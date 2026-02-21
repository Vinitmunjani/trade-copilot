"""MetaAPI integration service.

Manages connections to MT4/MT5 broker accounts via MetaAPI Cloud SDK.
Listens for trade events (open, update, close), normalizes data,
triggers AI analysis, and broadcasts via WebSocket.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import async_session_factory
from app.models.trade import Trade, TradeDirection, TradeStatus
from app.models.trading_rules import TradingRules
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


class ConnectionState:
    """Track a user's MetaAPI connection state."""

    def __init__(self, user_id: str, account_id: str):
        self.user_id = user_id
        self.account_id = account_id
        self.connection = None
        self.account = None
        self.listener_task: Optional[asyncio.Task] = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5


class MetaApiService:
    """Manages MetaAPI connections for all users.

    Handles connecting to user broker accounts, subscribing to trade events,
    normalizing trade data, and coordinating with AI analysis and WebSocket broadcasting.
    """

    def __init__(self):
        self._connections: dict[str, ConnectionState] = {}
        self._ws_manager = None  # Set externally
        self._api = None

    def set_ws_manager(self, ws_manager: Any) -> None:
        """Set the WebSocket manager for broadcasting events.

        Args:
            ws_manager: WebSocket connection manager instance.
        """
        self._ws_manager = ws_manager

    async def _get_api(self):
        """Get or create the MetaApi SDK instance.

        Returns:
            MetaApi instance.
        """
        if self._api is None:
            try:
                from metaapi_cloud_sdk import MetaApi
                self._api = MetaApi(settings.METAAPI_TOKEN)
            except ImportError:
                logger.warning("MetaAPI SDK not installed. Using simulation mode.")
                self._api = None
            except Exception as e:
                logger.error(f"Failed to initialize MetaAPI: {e}")
                self._api = None
        return self._api

    async def connect(self, user: User) -> dict:
        """Connect to a user's MT4/MT5 account via MetaAPI.

        Args:
            user: User model with metaapi_token and metaapi_account_id set.

        Returns:
            Dict with connection status info.
        """
        user_id = str(user.id)
        account_id = user.metaapi_account_id

        if not account_id:
            return {"connected": False, "error": "No MetaAPI account ID configured"}

        if user_id in self._connections and self._connections[user_id].is_connected:
            return {"connected": True, "account_id": account_id, "status": "already_connected"}

        state = ConnectionState(user_id, account_id)
        self._connections[user_id] = state

        api = await self._get_api()
        if api is None:
            logger.info(f"MetaAPI unavailable — user {user_id} in simulation mode")
            state.is_connected = False
            return {"connected": False, "status": "simulation_mode", "account_id": account_id}

        try:
            # Get the MetaAPI account
            account = await api.metatrader_account_api.get_account(account_id)
            state.account = account

            # Deploy if needed
            if account.state not in ("DEPLOYED", "DEPLOYING"):
                await account.deploy()

            # Wait for connection
            await account.wait_connected()

            # Create streaming connection
            connection = account.get_streaming_connection()
            await connection.connect()
            await connection.wait_synchronized()

            state.connection = connection
            state.is_connected = True
            state.reconnect_attempts = 0

            # Start listening for trade events
            state.listener_task = asyncio.create_task(
                self._listen_for_events(user_id, connection)
            )

            logger.info(f"Connected to MetaAPI for user {user_id}, account {account_id}")

            return {
                "connected": True,
                "account_id": account_id,
                "status": "connected",
                "broker": getattr(account, 'broker', 'Unknown'),
                "server": getattr(account, 'server', 'Unknown'),
            }

        except Exception as e:
            logger.error(f"MetaAPI connection failed for user {user_id}: {e}")
            state.is_connected = False
            return {"connected": False, "error": str(e), "account_id": account_id}

    async def disconnect(self, user: User) -> dict:
        """Disconnect a user's MetaAPI connection.

        Args:
            user: User model.

        Returns:
            Dict with disconnection status.
        """
        user_id = str(user.id)
        state = self._connections.get(user_id)

        if not state:
            return {"disconnected": True, "status": "was_not_connected"}

        try:
            if state.listener_task and not state.listener_task.done():
                state.listener_task.cancel()
                try:
                    await state.listener_task
                except asyncio.CancelledError:
                    pass

            if state.connection:
                await state.connection.close()

            if state.account:
                await state.account.undeploy()

        except Exception as e:
            logger.error(f"Error disconnecting MetaAPI for user {user_id}: {e}")

        state.is_connected = False
        del self._connections[user_id]

        return {"disconnected": True, "status": "disconnected"}

    async def get_status(self, user: User) -> dict:
        """Get the connection status for a user.

        Args:
            user: User model.

        Returns:
            Dict with connection status details.
        """
        user_id = str(user.id)
        state = self._connections.get(user_id)

        if not state:
            return {
                "connected": False,
                "account_id": user.metaapi_account_id,
                "status": "not_connected",
            }

        return {
            "connected": state.is_connected,
            "account_id": state.account_id,
            "status": "connected" if state.is_connected else "disconnected",
            "reconnect_attempts": state.reconnect_attempts,
        }

    async def _listen_for_events(self, user_id: str, connection: Any) -> None:
        """Listen for trade events from MetaAPI streaming connection.

        Runs as a background task. Handles order opened, updated, and closed events.

        Args:
            user_id: User UUID string.
            connection: MetaAPI streaming connection.
        """
        try:
            # The MetaAPI SDK uses synchronization listeners
            # We poll for position changes as a robust fallback
            known_positions: dict[str, dict] = {}

            while True:
                try:
                    terminal_state = connection.terminal_state
                    current_positions = {
                        p.get("id", ""): p
                        for p in (terminal_state.positions or [])
                    }

                    # Detect new positions (opened)
                    for pos_id, pos in current_positions.items():
                        if pos_id not in known_positions:
                            await self._on_trade_opened(user_id, pos)

                    # Detect closed positions
                    for pos_id, pos in known_positions.items():
                        if pos_id not in current_positions:
                            await self._on_trade_closed(user_id, pos)

                    # Detect updated positions
                    for pos_id, pos in current_positions.items():
                        if pos_id in known_positions:
                            old = known_positions[pos_id]
                            if (pos.get("stopLoss") != old.get("stopLoss") or
                                    pos.get("takeProfit") != old.get("takeProfit")):
                                await self._on_trade_updated(user_id, pos)

                    known_positions = current_positions

                except Exception as e:
                    logger.error(f"Error in event listener for user {user_id}: {e}")

                await asyncio.sleep(1)  # Poll every second

        except asyncio.CancelledError:
            logger.info(f"Event listener cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Event listener crashed for user {user_id}: {e}")
            # Attempt reconnection
            await self._handle_reconnection(user_id)

    async def _on_trade_opened(self, user_id: str, position: dict) -> None:
        """Handle a new trade being opened.

        Normalizes the trade data, saves to DB, runs behavioral checks
        and pre-trade AI analysis, then broadcasts via WebSocket.

        Args:
            user_id: User UUID string.
            position: MetaAPI position data dict.
        """
        logger.info(f"Trade opened for user {user_id}: {position.get('symbol')} {position.get('type')}")

        async with async_session_factory() as db:
            try:
                trade = Trade(
                    user_id=uuid.UUID(user_id),
                    external_trade_id=position.get("id", ""),
                    symbol=position.get("symbol", ""),
                    direction=TradeDirection.BUY if position.get("type") == "POSITION_TYPE_BUY" else TradeDirection.SELL,
                    entry_price=position.get("openPrice", 0),
                    sl=position.get("stopLoss"),
                    tp=position.get("takeProfit"),
                    lot_size=position.get("volume", 0),
                    open_time=datetime.now(timezone.utc),
                    status=TradeStatus.OPEN,
                )
                db.add(trade)
                await db.flush()

                # Run behavioral checks
                from app.services.behavioral_service import run_all_checks
                result = await db.execute(
                    select(TradingRules).where(TradingRules.user_id == user_id)
                )
                rules = result.scalar_one_or_none()

                alerts = await run_all_checks(db, user_id, trade, rules)
                trade.behavioral_flags = [a.dict() for a in alerts]

                # Run pre-trade AI analysis
                from app.services.ai_service import analyze_pre_trade
                from app.services.stats_service import get_user_history_summary
                from app.services.market_service import get_market_context

                history = await get_user_history_summary(db, user_id)
                market = await get_market_context(trade.symbol)

                trade_dict = {
                    "symbol": trade.symbol,
                    "direction": trade.direction.value,
                    "entry_price": trade.entry_price,
                    "sl": trade.sl,
                    "tp": trade.tp,
                    "lot_size": trade.lot_size,
                    "rr_ratio": None,
                }
                if trade.sl and trade.tp and trade.entry_price:
                    risk = abs(trade.entry_price - trade.sl)
                    reward = abs(trade.tp - trade.entry_price)
                    trade_dict["rr_ratio"] = round(reward / risk, 2) if risk > 0 else None

                score = await analyze_pre_trade(
                    trade_dict, market, history,
                    [a.dict() for a in alerts]
                )
                trade.ai_score = score.score
                trade.ai_analysis = score.dict()

                await db.commit()

                # Broadcast via WebSocket
                if self._ws_manager:
                    await self._ws_manager.broadcast_to_user(
                        user_id,
                        {
                            "event": "TRADE_OPENED",
                            "trade_id": str(trade.id),
                            "symbol": trade.symbol,
                            "direction": trade.direction.value,
                            "entry_price": trade.entry_price,
                            "ai_score": trade.ai_score,
                            "ai_analysis": trade.ai_analysis,
                            "behavioral_flags": trade.behavioral_flags,
                        },
                    )

                    # Send behavioral alerts separately for immediate notification
                    for alert in alerts:
                        await self._ws_manager.broadcast_to_user(
                            user_id,
                            {
                                "event": "BEHAVIORAL_ALERT",
                                "alert": alert.dict(),
                            },
                        )

            except Exception as e:
                logger.error(f"Error processing trade opened for user {user_id}: {e}")
                await db.rollback()

    async def _on_trade_closed(self, user_id: str, position: dict) -> None:
        """Handle a trade being closed.

        Calculates P&L, runs post-trade AI review, updates daily stats,
        and broadcasts via WebSocket.

        Args:
            user_id: User UUID string.
            position: MetaAPI position data dict (last known state).
        """
        logger.info(f"Trade closed for user {user_id}: {position.get('symbol')}")

        async with async_session_factory() as db:
            try:
                ext_id = position.get("id", "")
                result = await db.execute(
                    select(Trade).where(
                        and_(
                            Trade.user_id == user_id,
                            Trade.external_trade_id == ext_id,
                            Trade.status == TradeStatus.OPEN,
                        )
                    )
                )
                trade = result.scalar_one_or_none()

                if not trade:
                    logger.warning(f"No open trade found for external ID {ext_id}")
                    return

                now = datetime.now(timezone.utc)
                trade.status = TradeStatus.CLOSED
                trade.close_time = now
                trade.exit_price = position.get("closePrice") or position.get("currentPrice", trade.entry_price)

                # Calculate P&L
                if trade.direction == TradeDirection.BUY:
                    trade.pnl = (trade.exit_price - trade.entry_price) * trade.lot_size * 100000
                else:
                    trade.pnl = (trade.entry_price - trade.exit_price) * trade.lot_size * 100000

                # Calculate P&L in R-multiples
                if trade.sl and trade.entry_price:
                    risk = abs(trade.entry_price - trade.sl)
                    if risk > 0:
                        if trade.direction == TradeDirection.BUY:
                            trade.pnl_r = (trade.exit_price - trade.entry_price) / risk
                        else:
                            trade.pnl_r = (trade.entry_price - trade.exit_price) / risk
                        trade.pnl_r = round(trade.pnl_r, 3)

                # Duration
                if trade.open_time:
                    open_time = trade.open_time
                    if open_time.tzinfo is None:
                        open_time = open_time.replace(tzinfo=timezone.utc)
                    trade.duration_seconds = int((now - open_time).total_seconds())

                # Run post-trade AI review
                from app.services.ai_service import analyze_post_trade

                trade_dict = {
                    "symbol": trade.symbol,
                    "direction": trade.direction.value,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "sl": trade.sl,
                    "tp": trade.tp,
                    "pnl": round(trade.pnl, 2) if trade.pnl else 0,
                    "pnl_r": trade.pnl_r,
                    "duration_seconds": trade.duration_seconds,
                    "behavioral_flags": [
                        f.get("flag", "") if isinstance(f, dict) else str(f)
                        for f in (trade.behavioral_flags or [])
                    ],
                }
                pre_score = trade.ai_analysis

                review = await analyze_post_trade(trade_dict, pre_score)
                trade.ai_review = review.dict()

                await db.commit()

                # Update daily stats
                from app.services.stats_service import save_daily_stats
                await save_daily_stats(db, user_id)
                await db.commit()

                # Broadcast via WebSocket
                if self._ws_manager:
                    await self._ws_manager.broadcast_to_user(
                        user_id,
                        {
                            "event": "TRADE_CLOSED",
                            "trade_id": str(trade.id),
                            "symbol": trade.symbol,
                            "direction": trade.direction.value,
                            "pnl": round(trade.pnl, 2) if trade.pnl else 0,
                            "pnl_r": trade.pnl_r,
                            "ai_review": trade.ai_review,
                            "duration_seconds": trade.duration_seconds,
                        },
                    )

            except Exception as e:
                logger.error(f"Error processing trade closed for user {user_id}: {e}")
                await db.rollback()

    async def _on_trade_updated(self, user_id: str, position: dict) -> None:
        """Handle a trade being modified (SL/TP update).

        Args:
            user_id: User UUID string.
            position: Updated MetaAPI position data dict.
        """
        logger.info(f"Trade updated for user {user_id}: {position.get('symbol')}")

        async with async_session_factory() as db:
            try:
                ext_id = position.get("id", "")
                result = await db.execute(
                    select(Trade).where(
                        and_(
                            Trade.user_id == user_id,
                            Trade.external_trade_id == ext_id,
                            Trade.status == TradeStatus.OPEN,
                        )
                    )
                )
                trade = result.scalar_one_or_none()

                if not trade:
                    return

                trade.sl = position.get("stopLoss", trade.sl)
                trade.tp = position.get("takeProfit", trade.tp)

                await db.commit()

                if self._ws_manager:
                    await self._ws_manager.broadcast_to_user(
                        user_id,
                        {
                            "event": "TRADE_UPDATED",
                            "trade_id": str(trade.id),
                            "symbol": trade.symbol,
                            "sl": trade.sl,
                            "tp": trade.tp,
                        },
                    )

            except Exception as e:
                logger.error(f"Error processing trade update for user {user_id}: {e}")
                await db.rollback()

    async def _handle_reconnection(self, user_id: str) -> None:
        """Handle reconnection after a connection failure.

        Args:
            user_id: User UUID string.
        """
        state = self._connections.get(user_id)
        if not state:
            return

        state.reconnect_attempts += 1
        if state.reconnect_attempts > state.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts reached for user {user_id}")
            state.is_connected = False
            return

        delay = min(30, 2 ** state.reconnect_attempts)
        logger.info(f"Reconnecting user {user_id} in {delay}s (attempt {state.reconnect_attempts})")
        await asyncio.sleep(delay)

        async with async_session_factory() as db:
            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user = result.scalar_one_or_none()
            if user:
                await self.connect(user)

    async def simulate_trade_open(self, user_id: str, trade_data: dict) -> Trade:
        """Simulate a trade opening for testing without a real broker.

        Creates a trade record, runs behavioral checks and AI analysis,
        and broadcasts via WebSocket — same as a real trade open.

        Args:
            user_id: User UUID string.
            trade_data: Dict with symbol, direction, entry_price, sl, tp, lot_size.

        Returns:
            The created Trade model instance.
        """
        async with async_session_factory() as db:
            trade = Trade(
                user_id=uuid.UUID(user_id),
                external_trade_id=f"SIM-{uuid.uuid4().hex[:8]}",
                symbol=trade_data.get("symbol", "EURUSD"),
                direction=TradeDirection(trade_data.get("direction", "BUY")),
                entry_price=trade_data.get("entry_price", 1.0850),
                sl=trade_data.get("sl"),
                tp=trade_data.get("tp"),
                lot_size=trade_data.get("lot_size", 0.1),
                open_time=datetime.now(timezone.utc),
                status=TradeStatus.OPEN,
            )
            db.add(trade)
            await db.flush()

            # Run behavioral checks
            from app.services.behavioral_service import run_all_checks
            result = await db.execute(
                select(TradingRules).where(TradingRules.user_id == user_id)
            )
            rules = result.scalar_one_or_none()
            alerts = await run_all_checks(db, user_id, trade, rules)
            trade.behavioral_flags = [a.dict() for a in alerts]

            # Run AI analysis
            from app.services.ai_service import analyze_pre_trade
            from app.services.stats_service import get_user_history_summary
            from app.services.market_service import get_market_context

            history = await get_user_history_summary(db, user_id)
            market = await get_market_context(trade.symbol)

            trade_dict = {
                "symbol": trade.symbol,
                "direction": trade.direction.value,
                "entry_price": trade.entry_price,
                "sl": trade.sl,
                "tp": trade.tp,
                "lot_size": trade.lot_size,
                "rr_ratio": None,
            }
            if trade.sl and trade.tp and trade.entry_price:
                risk = abs(trade.entry_price - trade.sl)
                reward = abs(trade.tp - trade.entry_price)
                trade_dict["rr_ratio"] = round(reward / risk, 2) if risk > 0 else None

            score = await analyze_pre_trade(
                trade_dict, market, history,
                [a.dict() for a in alerts]
            )
            trade.ai_score = score.score
            trade.ai_analysis = score.dict()

            await db.commit()

            # Broadcast
            if self._ws_manager:
                await self._ws_manager.broadcast_to_user(
                    user_id,
                    {
                        "event": "TRADE_OPENED",
                        "trade_id": str(trade.id),
                        "symbol": trade.symbol,
                        "direction": trade.direction.value,
                        "entry_price": trade.entry_price,
                        "ai_score": trade.ai_score,
                        "ai_analysis": trade.ai_analysis,
                        "behavioral_flags": trade.behavioral_flags,
                        "simulated": True,
                    },
                )

                for alert in alerts:
                    await self._ws_manager.broadcast_to_user(
                        user_id,
                        {"event": "BEHAVIORAL_ALERT", "alert": alert.dict()},
                    )

            # Refresh to get all fields
            await db.refresh(trade)
            return trade

    async def simulate_trade_close(self, user_id: str, trade_id: str, exit_price: float) -> Optional[Trade]:
        """Simulate closing a trade for testing.

        Args:
            user_id: User UUID string.
            trade_id: Trade UUID string.
            exit_price: Simulated exit price.

        Returns:
            Updated Trade model, or None if not found.
        """
        async with async_session_factory() as db:
            result = await db.execute(
                select(Trade).where(
                    and_(
                        Trade.id == uuid.UUID(trade_id),
                        Trade.user_id == user_id,
                        Trade.status == TradeStatus.OPEN,
                    )
                )
            )
            trade = result.scalar_one_or_none()

            if not trade:
                return None

            now = datetime.now(timezone.utc)
            trade.status = TradeStatus.CLOSED
            trade.close_time = now
            trade.exit_price = exit_price

            # Calculate P&L
            if trade.direction == TradeDirection.BUY:
                trade.pnl = round((exit_price - trade.entry_price) * trade.lot_size * 100000, 2)
            else:
                trade.pnl = round((trade.entry_price - exit_price) * trade.lot_size * 100000, 2)

            # R-multiples
            if trade.sl:
                risk = abs(trade.entry_price - trade.sl)
                if risk > 0:
                    if trade.direction == TradeDirection.BUY:
                        trade.pnl_r = round((exit_price - trade.entry_price) / risk, 3)
                    else:
                        trade.pnl_r = round((trade.entry_price - exit_price) / risk, 3)

            # Duration
            open_time = trade.open_time
            if open_time.tzinfo is None:
                open_time = open_time.replace(tzinfo=timezone.utc)
            trade.duration_seconds = int((now - open_time).total_seconds())

            # Post-trade AI review
            from app.services.ai_service import analyze_post_trade

            trade_dict = {
                "symbol": trade.symbol,
                "direction": trade.direction.value,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "sl": trade.sl,
                "tp": trade.tp,
                "pnl": trade.pnl,
                "pnl_r": trade.pnl_r,
                "duration_seconds": trade.duration_seconds,
                "behavioral_flags": [
                    f.get("flag", "") if isinstance(f, dict) else str(f)
                    for f in (trade.behavioral_flags or [])
                ],
            }

            review = await analyze_post_trade(trade_dict, trade.ai_analysis)
            trade.ai_review = review.dict()

            await db.commit()

            # Update daily stats
            from app.services.stats_service import save_daily_stats
            await save_daily_stats(db, user_id)
            await db.commit()

            # Broadcast
            if self._ws_manager:
                await self._ws_manager.broadcast_to_user(
                    user_id,
                    {
                        "event": "TRADE_CLOSED",
                        "trade_id": str(trade.id),
                        "symbol": trade.symbol,
                        "direction": trade.direction.value,
                        "pnl": trade.pnl,
                        "pnl_r": trade.pnl_r,
                        "ai_review": trade.ai_review,
                        "duration_seconds": trade.duration_seconds,
                        "simulated": True,
                    },
                )

            await db.refresh(trade)
            return trade


# Global singleton
metaapi_service = MetaApiService()
