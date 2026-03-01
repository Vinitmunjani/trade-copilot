"""Shared trade processing service.

Handles trade events from both MetaAPI and local MT5 engines.
Coordinates DB updates, behavioral checks, AI analysis, and WS broadcasts.
"""

import asyncio
import logging
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy import select, and_
from app.database import async_session_factory
from app.models.trade import Trade, TradeDirection, TradeStatus
from app.models.trade_log import TradeLog
from app.models.trading_rules import TradingRules
from app.services.behavioral_service import run_all_checks
from app.services.ai_service import analyze_pre_trade, analyze_post_trade, analyze_trade_modified
from app.services.stats_service import get_user_history_summary, save_daily_stats
from app.services.market_service import get_market_context, fetch_live_market_context
from app.services.notification_service import notification_service


def _derive_session(open_time: datetime) -> str:
    """Derive trading session from UTC open time."""
    hour = open_time.hour
    if 0 <= hour < 8:
        return "tokyo"
    elif 8 <= hour < 13:
        return "london"
    elif 13 <= hour < 22:
        return "new_york"
    else:
        return "sydney"


def _build_trade_payload(trade: Trade) -> dict:
    """Serialize a Trade to WS-broadcast dict."""
    return {
        "id": str(trade.id),
        "user_id": str(trade.user_id),
        "symbol": trade.symbol,
        "direction": trade.direction.value,
        "entry_price": trade.entry_price,
        "exit_price": trade.exit_price,
        "stop_loss": trade.sl,
        "take_profit": trade.tp,
        "sl": trade.sl,
        "tp": trade.tp,
        "lot_size": trade.lot_size,
        "pnl": round(trade.pnl, 2) if trade.pnl is not None else None,
        "pnl_r": trade.pnl_r,
        "status": trade.status.value,
        "opened_at": trade.open_time.isoformat() if trade.open_time else None,
        "closed_at": trade.close_time.isoformat() if trade.close_time else None,
        "open_time": trade.open_time.isoformat() if trade.open_time else None,
        "close_time": trade.close_time.isoformat() if trade.close_time else None,
        "duration_seconds": trade.duration_seconds
            if trade.duration_seconds is not None
            else (
                max(0, int((
                    (trade.close_time.replace(tzinfo=timezone.utc) if trade.close_time.tzinfo is None else trade.close_time)
                    - (trade.open_time.replace(tzinfo=timezone.utc) if trade.open_time.tzinfo is None else trade.open_time)
                ).total_seconds()))
                if trade.open_time and trade.close_time else None
            ),
        "duration_minutes": None,  # computed on frontend from duration_seconds
        "session": _derive_session(trade.open_time) if trade.open_time else "london",
        "ai_score": trade.ai_score,
        "ai_analysis": trade.ai_analysis,
        "ai_review": trade.ai_review,
        "flags": trade.behavioral_flags or [],
        "behavioral_flags": trade.behavioral_flags or [],
    }

logger = logging.getLogger(__name__)

class TradeProcessingService:
    def __init__(self):
        self._ws_manager = None
        self._open_trade_locks: Dict[str, Any] = {}
        # Hold strong references to background tasks so they aren't GC'd before completion
        self._background_tasks: set = set()

    def set_ws_manager(self, ws_manager: Any) -> None:
        self._ws_manager = ws_manager

    async def process_trade_opened(self, user_id: str, trade_data: Dict[str, Any]) -> Optional[Trade]:
        """Process a new trade being opened."""
        logger.info(f"Processing trade opened for user {user_id}: {trade_data.get('symbol')}")

        external_id = str(trade_data.get("external_id", ""))
        if not external_id:
            logger.warning(f"Skipping trade_opened with missing external_id for user {user_id}")
            return None

        lock_key = f"{user_id}:{external_id}"
        if lock_key not in self._open_trade_locks:
            self._open_trade_locks[lock_key] = asyncio.Lock()
        lock = self._open_trade_locks[lock_key]

        async with lock:
            return await self._process_trade_opened_locked(user_id, trade_data, external_id)

    async def _process_trade_opened_locked(
        self, user_id: str, trade_data: Dict[str, Any], external_id: str
    ) -> Optional[Trade]:
        """Internal locked implementation for process_trade_opened."""
        user_uuid = uuid.UUID(user_id)
        
        async with async_session_factory() as db:
            try:
                existing_result = await db.execute(
                    select(Trade).where(
                        and_(
                            Trade.user_id == user_uuid,
                            Trade.external_trade_id == external_id,
                            Trade.status == TradeStatus.OPEN,
                        )
                    )
                )
                existing_trade = existing_result.scalar_one_or_none()
                if existing_trade:
                    logger.info(
                        f"Skipping duplicate open trade for user {user_id}, external_id {external_id}"
                    )
                    return existing_trade

                # 1. Create trade record
                trade = Trade(
                    user_id=user_uuid,
                    external_trade_id=external_id,
                    symbol=trade_data.get("symbol", ""),
                    direction=TradeDirection.BUY if trade_data.get("type", "").upper() == "BUY" else TradeDirection.SELL,
                    entry_price=float(trade_data.get("entry_price", 0)),
                    sl=trade_data.get("sl"),
                    tp=trade_data.get("tp"),
                    lot_size=float(trade_data.get("lot_size", 0)),
                    open_time=datetime.now(timezone.utc),
                    status=TradeStatus.OPEN,
                )
                db.add(trade)
                await db.flush()

                # 2. Run behavioral checks
                result = await db.execute(
                    select(TradingRules).where(TradingRules.user_id == user_id)
                )
                rules = result.scalar_one_or_none()
                account_balance = float(trade_data.get("account_balance") or 10000.0)
                alerts = await run_all_checks(db, user_id, trade, rules, account_balance=account_balance)
                trade.behavioral_flags = [a.model_dump() for a in alerts]

                # 3. Write opened log entry (before commit)
                db.add(TradeLog(
                    trade_id=trade.id,
                    user_id=user_uuid,
                    event_type="opened",
                    payload={
                        "symbol": trade.symbol,
                        "direction": trade.direction.value,
                        "entry_price": trade.entry_price,
                        "sl": trade.sl,
                        "tp": trade.tp,
                        "lot_size": trade.lot_size,
                        "behavioral_flags": trade.behavioral_flags or [],
                    },
                ))

                await db.commit()
                trade_id_str = str(trade.id)

                # 4. Broadcast via WebSocket immediately (AI score filled later)
                if self._ws_manager:
                    await self._ws_manager.broadcast_to_user(
                        user_id,
                        {
                            "type": "trade_opened",
                            "trade": _build_trade_payload(trade),
                        },
                    )

                # 5. Schedule AI analysis as background task (non-blocking)
                task = asyncio.create_task(
                    self._run_pre_trade_ai(user_id, trade_id_str, trade.symbol, trade.direction.value,
                                           trade.entry_price, trade.sl, trade.tp, trade.lot_size,
                                           [a.model_dump() for a in alerts])
                )
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

                # 6. External notifications (webhook/email)
                try:
                    await notification_service.notify_trade_event(
                        user_id,
                        "TRADE_OPENED",
                        {
                            "id": str(trade.id),
                            "symbol": trade.symbol,
                            "direction": trade.direction.value,
                            "entry_price": trade.entry_price,
                            "sl": trade.sl,
                            "tp": trade.tp,
                            "lot_size": trade.lot_size,
                        },
                    )
                except Exception:
                    logger.exception("Failed to send trade opened notification")

                return trade
            except Exception as e:
                logger.error(f"Error processing trade opened: {e}")
                await db.rollback()
                return None

    async def _run_pre_trade_ai(
        self, user_id: str, trade_id: str, symbol: str, direction: str,
        entry_price: float, sl: float | None, tp: float | None, lot_size: float,
        alert_dicts: list,
    ) -> None:
        """Background task: run pre-trade AI, save score, broadcast score_update."""
        user_uuid = uuid.UUID(user_id)
        trade_uuid = uuid.UUID(trade_id)

        # --- Step 1: load context (isolated session, no long-lived hold) ---
        history: dict = {}
        market: dict = {}
        open_positions: list = []
        try:
            async with async_session_factory() as db:
                history = await get_user_history_summary(db, user_uuid)
        except Exception:
            logger.warning(f"Could not fetch user history for pre-trade AI (trade {trade_id}) — using empty history")

        # Fetch all OTHER currently open trades so GPT can assess portfolio exposure
        try:
            async with async_session_factory() as db:
                pos_result = await db.execute(
                    select(Trade).where(
                        and_(
                            Trade.user_id == user_uuid,
                            Trade.status == TradeStatus.OPEN,
                            Trade.id != trade_uuid,
                        )
                    )
                )
                open_positions = [
                    {
                        "symbol": t.symbol,
                        "direction": t.direction.value,
                        "entry_price": t.entry_price,
                        "sl": t.sl,
                        "tp": t.tp,
                        "lot_size": t.lot_size,
                    }
                    for t in pos_result.scalars().all()
                ]
        except Exception:
            logger.warning(f"Could not fetch open positions for pre-trade AI (trade {trade_id}) — using empty list")

        try:
            market = await fetch_live_market_context(symbol, user_id)
        except Exception:
            logger.warning(f"Could not fetch market context for pre-trade AI (trade {trade_id}) — using empty context")

        # --- Step 2: build normalised trade and run AI (no DB session open) ---
        normalized_trade = {
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "sl": sl,
            "tp": tp,
            "lot_size": lot_size,
            "rr_ratio": None,
        }
        if sl and tp and entry_price:
            risk = abs(entry_price - sl)
            reward = abs(tp - entry_price)
            normalized_trade["rr_ratio"] = round(reward / risk, 2) if risk > 0 else None

        try:
            score = await analyze_pre_trade(normalized_trade, market, history, alert_dicts, open_positions)
        except Exception:
            logger.exception(f"analyze_pre_trade raised for trade {trade_id}")
            return

        # --- Step 3: save + broadcast (fresh session) ---
        try:
            async with async_session_factory() as db:
                result = await db.execute(select(Trade).where(Trade.id == trade_uuid))
                trade = result.scalar_one_or_none()
                if not trade:
                    logger.warning(f"Pre-trade AI: trade {trade_id} not found when saving score")
                    return

                # If a modification analysis already ran (open_thesis key present), don't overwrite.
                if trade.ai_analysis and "open_thesis" in trade.ai_analysis:
                    logger.info(
                        f"Pre-trade AI skipped save for {trade_id}: modification analysis already present"
                    )
                    return

                analysis_dict = score.model_dump()
                trade.ai_score = score.score
                trade.ai_analysis = analysis_dict

                db.add(TradeLog(
                    trade_id=trade.id,
                    user_id=trade.user_id,
                    event_type="score_update",
                    payload={"ai_score": score.score, "ai_analysis": analysis_dict},
                ))

                await db.commit()
                logger.info(f"Pre-trade AI saved score {score.score} for trade {trade_id}")

                if self._ws_manager:
                    await self._ws_manager.broadcast_to_user(
                        user_id,
                        {
                            "type": "score_update",
                            "trade_id": trade_id,
                            "ai_score": score.score,
                            "ai_analysis": analysis_dict,
                            "ai_review": None,
                        },
                    )
        except Exception:
            logger.exception(f"Background pre-trade AI failed saving/broadcasting for trade {trade_id}")

    async def _run_modified_trade_ai(
        self, user_id: str, trade_id: str,
        old_sl: float | None, old_tp: float | None,
        new_sl: float | None, new_tp: float | None,
        original_analysis: dict | None,
    ) -> None:
        """Background task: run AI analysis on a modified open trade, preserving original thesis."""
        # --- Step 1: load trade + market context ---
        symbol = None
        trade_dict: dict = {}
        market: dict = {}
        try:
            async with async_session_factory() as db:
                result = await db.execute(select(Trade).where(Trade.id == uuid.UUID(trade_id)))
                trade = result.scalar_one_or_none()
                if not trade:
                    return
                symbol = trade.symbol
                trade_dict = {
                    "symbol": trade.symbol,
                    "direction": trade.direction.value,
                    "entry_price": trade.entry_price,
                    # Use pre-commit snapshots so the prompt shows the real before→after diff
                    "sl": old_sl if old_sl is not None else trade.sl,
                    "tp": old_tp if old_tp is not None else trade.tp,
                    "lot_size": trade.lot_size,
                }
        except Exception:
            logger.exception(f"Background modified-trade AI failed loading trade {trade_id}")
            return

        if symbol:
            try:
                market = await fetch_live_market_context(symbol, user_id)
            except Exception:
                logger.warning(f"Could not fetch market context for modified-trade AI (trade {trade_id}) — using empty context")

        # --- Step 2: run AI (no DB session open) ---
        try:
            score = await analyze_trade_modified(trade_dict, new_sl, new_tp, original_analysis, market)
        except Exception:
            logger.exception(f"analyze_trade_modified raised for trade {trade_id}")
            return

        # --- Step 3: save + broadcast (fresh session) ---
        try:
            async with async_session_factory() as db:
                result = await db.execute(select(Trade).where(Trade.id == uuid.UUID(trade_id)))
                trade = result.scalar_one_or_none()
                if not trade:
                    return

                # Update ai_analysis — keep original_analysis nested as open_thesis
                updated_analysis = score.model_dump()
                if original_analysis:
                    updated_analysis["open_thesis"] = original_analysis

                trade.ai_score = score.score
                trade.ai_analysis = updated_analysis

                db.add(TradeLog(
                    trade_id=trade.id,
                    user_id=trade.user_id,
                    event_type="score_update",
                    payload={"ai_score": score.score, "ai_analysis": updated_analysis, "trigger": "modified"},
                ))

                await db.commit()

                if self._ws_manager:
                    await self._ws_manager.broadcast_to_user(
                        user_id,
                        {
                            "type": "score_update",
                            "trade_id": trade_id,
                            "ai_score": score.score,
                            "ai_analysis": updated_analysis,
                            "ai_review": None,
                            "trigger": "modified",
                        },
                    )
        except Exception:
            logger.exception(f"Background modified-trade AI failed saving/broadcasting for trade {trade_id}")

    async def _run_post_trade_ai(
        self, user_id: str, trade_id: str, review_input: dict, pre_analysis: dict | None
    ) -> None:
        """Background task: run post-trade AI review, save, broadcast score_update."""
        try:
            async with async_session_factory() as db:
                result = await db.execute(select(Trade).where(Trade.id == uuid.UUID(trade_id)))
                trade = result.scalar_one_or_none()
                if not trade:
                    return

                review = await analyze_post_trade(review_input, pre_analysis)
                review_dict = review.model_dump()
                trade.ai_review = review_dict

                db.add(TradeLog(
                    trade_id=trade.id,
                    user_id=trade.user_id,
                    event_type="score_update",
                    payload={"ai_review": review_dict},
                ))

                await db.commit()

                if self._ws_manager:
                    await self._ws_manager.broadcast_to_user(
                        user_id,
                        {
                            "type": "score_update",
                            "trade_id": trade_id,
                            "ai_score": trade.ai_score,
                            "ai_analysis": trade.ai_analysis,
                            "ai_review": review_dict,
                        },
                    )
        except Exception:
            logger.exception(f"Background post-trade AI failed for trade {trade_id}")

    async def process_trade_closed(self, user_id: str, trade_data: Dict[str, Any]) -> Optional[Trade]:
        """Process a trade being closed."""
        ext_id = str(trade_data.get("external_id", ""))
        logger.info(f"Processing trade closed for user {user_id}: {ext_id}")

        if not ext_id:
            logger.warning(f"Skipping trade_closed with missing external_id for user {user_id}")
            return None
        
        async with async_session_factory() as db:
            try:
                # Find all open trades for this external id (handles legacy duplicates)
                result = await db.execute(
                    select(Trade).where(
                        and_(
                            Trade.user_id == uuid.UUID(user_id),
                            Trade.external_trade_id == ext_id,
                            Trade.status == TradeStatus.OPEN,
                        )
                    ).order_by(Trade.open_time.desc())
                )
                open_trades = result.scalars().all()
                if not open_trades:
                    logger.warning(f"No open trade found for external ID {ext_id}")
                    return None

                trade = open_trades[0]

                now = datetime.now(timezone.utc)

                # Close all matching open rows so duplicates don't remain open
                broker_pnl = trade_data.get("pnl")  # Broker-provided profit in account currency
                for row in open_trades:
                    row.status = TradeStatus.CLOSED
                    row.close_time = now
                    # Compute duration from the stored open_time to now.
                    # open_time may be tz-naive (stored as UTC); normalise before diff.
                    if row.open_time:
                        open_ts = row.open_time
                        if open_ts.tzinfo is None:
                            open_ts = open_ts.replace(tzinfo=timezone.utc)
                        row.duration_seconds = max(0, int((now - open_ts).total_seconds()))
                    raw_exit = trade_data.get("exit_price")
                    # Only accept exit_price when it is a real non-zero value.
                    # A 0 or missing value means the close price was not captured
                    # (e.g. fast scalp, reconnect reconciliation) — fall back to
                    # entry_price so the row is at least consistent; the broker
                    # pnl field still gives the correct profit in account currency.
                    row.exit_price = float(raw_exit) if raw_exit else row.entry_price

                    if broker_pnl is not None:
                        # Use broker-provided P&L (already in account currency — correct for all instruments)
                        row.pnl = float(broker_pnl)
                    else:
                        # Fallback: estimate P&L from price movement when broker value is unavailable.
                        # Instrument categories (by entry price range):
                        #   > 1000  — crypto CFDs (BTCUSD, ETHUSD …): 1 lot = 1 coin, pnl = Δprice * lots
                        #   > 20    — indices / metals / oil: pip_size=0.01, pip_value=$10/std lot
                        #   ≤ 20    — standard forex: pip_size=0.0001, pip_value=$10/std lot
                        price_diff = (row.exit_price - row.entry_price) if row.direction == TradeDirection.BUY \
                            else (row.entry_price - row.exit_price)
                        if row.entry_price > 1000:
                            # Crypto CFD — contract size is 1 coin, priced directly in USD
                            row.pnl = round(price_diff * row.lot_size, 2)
                        elif row.entry_price > 20:
                            pip_size = 0.01
                            pip_value = 10.0
                            row.pnl = round((price_diff / pip_size) * pip_value * row.lot_size, 2)
                        else:
                            pip_size = 0.0001
                            pip_value = 10.0
                            row.pnl = round((price_diff / pip_size) * pip_value * row.lot_size, 2)

                    if row.sl and row.entry_price:
                        risk = abs(row.entry_price - row.sl)
                        if risk > 0 and row.lot_size > 0:
                            if row.entry_price > 1000:
                                risk_in_money = risk * row.lot_size
                            elif row.entry_price > 20:
                                risk_in_money = (risk / 0.01) * 10.0 * row.lot_size
                            else:
                                risk_in_money = (risk / 0.0001) * 10.0 * row.lot_size
                            row.pnl_r = round(row.pnl / risk_in_money, 3) if risk_in_money != 0 else 0

                # keep reference to newest row for notification/broadcast payload
                trade = open_trades[0]

                # Write closed log
                db.add(TradeLog(
                    trade_id=trade.id,
                    user_id=trade.user_id,
                    event_type="closed",
                    payload={
                        "exit_price": trade.exit_price,
                        "pnl": round(trade.pnl, 2) if trade.pnl is not None else None,
                        "pnl_r": trade.pnl_r,
                        "close_time": now.isoformat(),
                    },
                ))

                await db.commit()
                await save_daily_stats(db, user_id)
                await db.commit()

                # Broadcast trade_closed immediately (ai_review filled by background task)
                if self._ws_manager:
                    await self._ws_manager.broadcast_to_user(
                        user_id,
                        {
                            "type": "trade_closed",
                            "trade": _build_trade_payload(trade),
                        },
                    )

                # Schedule post-trade AI in background
                review_input = {
                    "symbol": trade.symbol,
                    "direction": trade.direction.value,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "sl": trade.sl,
                    "tp": trade.tp,
                    "pnl": round(trade.pnl, 2) if trade.pnl is not None else None,
                    "pnl_r": trade.pnl_r,
                    "behavioral_flags": [f.get("flag", "") for f in (trade.behavioral_flags or [])],
                }
                task = asyncio.create_task(
                    self._run_post_trade_ai(user_id, str(trade.id), review_input, trade.ai_analysis)
                )
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

                # External notifications
                try:
                    await notification_service.notify_trade_event(
                        user_id,
                        "TRADE_CLOSED",
                        {
                            "id": str(trade.id),
                            "symbol": trade.symbol,
                            "direction": trade.direction.value,
                            "entry_price": trade.entry_price,
                            "exit_price": trade.exit_price,
                            "pnl": round(trade.pnl, 2) if trade.pnl is not None else None,
                            "pnl_r": trade.pnl_r,
                        },
                    )
                except Exception:
                    logger.exception("Failed to send trade closed notification")

                return trade
            except Exception as e:
                logger.error(f"Error processing trade closed: {e}")
                await db.rollback()
                return None

    async def process_trade_updated(self, user_id: str, trade_data: Dict[str, Any]) -> Optional[Trade]:
        """Process updates to an open trade (SL/TP changes)."""
        ext_id = str(trade_data.get("external_id", ""))
        logger.info(f"Processing trade update for user {user_id}: {ext_id}")

        async with async_session_factory() as db:
            try:
                result = await db.execute(
                    select(Trade).where(
                        and_(
                            Trade.user_id == uuid.UUID(user_id),
                            Trade.external_trade_id == ext_id,
                            Trade.status == TradeStatus.OPEN,
                        )
                    )
                )
                trade = result.scalar_one_or_none()
                if not trade:
                    logger.debug(f"No open trade found for update external ID {ext_id}")
                    return None

                # Snapshot OLD levels before overwriting — the AI needs the before→after diff
                old_sl_snap = trade.sl
                old_tp_snap = trade.tp

                new_sl = trade_data.get("sl", trade.sl)
                new_tp = trade_data.get("tp", trade.tp)
                # Snapshot original analysis before overwriting so AI can reference the open thesis
                original_analysis = trade.ai_analysis

                trade.sl = new_sl
                trade.tp = new_tp
                await db.commit()

                # Write modified log
                db.add(TradeLog(
                    trade_id=trade.id,
                    user_id=trade.user_id,
                    event_type="modified",
                    payload={"sl": trade.sl, "tp": trade.tp},
                ))
                await db.commit()

                if self._ws_manager:
                    await self._ws_manager.broadcast_to_user(
                        user_id,
                        {
                            "type": "trade_updated",
                            "trade": _build_trade_payload(trade),
                        },
                    )

                # Schedule AI analysis for the modification (non-blocking)
                task = asyncio.create_task(
                    self._run_modified_trade_ai(
                        user_id, str(trade.id),
                        old_sl_snap, old_tp_snap,
                        new_sl, new_tp,
                        original_analysis,
                    )
                )
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

                try:
                    await notification_service.notify_trade_event(
                        user_id,
                        "TRADE_UPDATED",
                        {
                            "id": str(trade.id),
                            "symbol": trade.symbol,
                            "sl": trade.sl,
                            "tp": trade.tp,
                        },
                    )
                except Exception:
                    logger.exception("Failed to send trade updated notification")

                return trade
            except Exception as e:
                logger.error(f"Error processing trade updated: {e}")
                await db.rollback()
                return None

# Global instance
trade_processor = TradeProcessingService()
