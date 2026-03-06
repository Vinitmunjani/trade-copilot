"""Beta auto-adjust service.

Automatically applies protective actions for low-quality open trades based on
AI score and per-user settings.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import and_, select

from app.config import get_settings
from app.database import async_session_factory
from app.models.trade import Trade, TradeDirection, TradeStatus
from app.models.trade_log import TradeLog
from app.models.user import User

logger = logging.getLogger(__name__)


class AutoAdjustService:
    """Decision engine for beta auto-adjust interventions."""

    def _user_settings(self, user: User) -> dict[str, Any]:
        return dict(user.settings or {})

    def _is_enabled_for_user(self, user: User) -> bool:
        settings = self._user_settings(user)
        return bool(settings.get("beta_auto_adjust", False))

    def _threshold_for_user(self, user: User) -> int:
        app_settings = get_settings()
        default_threshold = int(getattr(app_settings, "AUTO_ADJUST_DEFAULT_THRESHOLD", 3) or 3)
        settings = self._user_settings(user)
        try:
            return int(settings.get("auto_adjust_score_threshold", default_threshold))
        except Exception:
            return default_threshold

    def _mode_for_user(self, user: User) -> str:
        app_settings = get_settings()
        default_mode = str(getattr(app_settings, "AUTO_ADJUST_DEFAULT_MODE", "hybrid") or "hybrid")
        settings = self._user_settings(user)
        mode = str(settings.get("auto_adjust_mode", default_mode)).lower().strip()
        if mode not in {"close", "modify", "hybrid"}:
            return default_mode
        return mode

    def _is_symbol_allowed(self, user: User, symbol: str) -> bool:
        settings = self._user_settings(user)
        symbols = settings.get("auto_adjust_symbols")
        if not symbols:
            return True
        try:
            allowed = {str(s).upper().strip() for s in symbols if str(s).strip()}
        except Exception:
            return True
        return symbol.upper() in allowed

    def _analysis_text(self, trade: Trade) -> str:
        """Flatten relevant AI fields to a single lower-cased text corpus."""
        analysis = trade.ai_analysis or {}
        if not isinstance(analysis, dict):
            return ""

        fields = [
            analysis.get("summary", ""),
            analysis.get("suggestion", ""),
            analysis.get("market_alignment", ""),
            analysis.get("risk_assessment", ""),
        ]

        open_thesis = analysis.get("open_thesis")
        if isinstance(open_thesis, dict):
            fields.extend(
                [
                    open_thesis.get("summary", ""),
                    open_thesis.get("suggestion", ""),
                    open_thesis.get("market_alignment", ""),
                    open_thesis.get("risk_assessment", ""),
                ]
            )

        return " ".join(str(x) for x in fields if x).lower()

    def _infer_bias_from_text(self, text: str) -> str | None:
        if not text:
            return None

        bullish_terms = (
            "bullish",
            "buy movement",
            "uptrend",
            "long setup",
            "upside",
            "demand",
        )
        bearish_terms = (
            "bearish",
            "sell movement",
            "downtrend",
            "short setup",
            "downside",
            "supply",
        )

        bullish_hits = sum(1 for term in bullish_terms if term in text)
        bearish_hits = sum(1 for term in bearish_terms if term in text)

        if bullish_hits and bearish_hits:
            return None
        if bullish_hits > 0:
            return "bullish"
        if bearish_hits > 0:
            return "bearish"
        return None

    async def _get_symbol_memory(self, user_id: uuid.UUID, symbol: str) -> dict[str, Any]:
        """Build a lightweight memory snapshot for recent behavior on a symbol."""
        bias_counts = {"bullish": 0, "bearish": 0}
        last_auto_adjust = None

        async with async_session_factory() as db:
            trade_rows = await db.execute(
                select(Trade)
                .where(
                    and_(
                        Trade.user_id == user_id,
                        Trade.symbol == symbol,
                    )
                )
                .order_by(Trade.open_time.desc())
                .limit(15)
            )
            recent_symbol_trades = trade_rows.scalars().all()

            for recent_trade in recent_symbol_trades:
                text = self._analysis_text(recent_trade)
                bias = self._infer_bias_from_text(text)
                if bias in bias_counts:
                    bias_counts[bias] += 1

            log_rows = await db.execute(
                select(TradeLog, Trade)
                .join(Trade, Trade.id == TradeLog.trade_id)
                .where(
                    and_(
                        TradeLog.user_id == user_id,
                        TradeLog.event_type == "auto_adjust",
                        Trade.symbol == symbol,
                    )
                )
                .order_by(TradeLog.created_at.desc())
                .limit(10)
            )
            recent_auto_adjust_logs = log_rows.all()

            if recent_auto_adjust_logs:
                latest_log, latest_trade = recent_auto_adjust_logs[0]
                payload = latest_log.payload or {}
                last_auto_adjust = {
                    "action": str(payload.get("action") or "").lower(),
                    "direction": latest_trade.direction.value,
                    "created_at": latest_log.created_at,
                }

        dominant_bias = None
        if bias_counts["bullish"] > bias_counts["bearish"] and bias_counts["bullish"] > 0:
            dominant_bias = "bullish"
        elif bias_counts["bearish"] > bias_counts["bullish"] and bias_counts["bearish"] > 0:
            dominant_bias = "bearish"

        return {
            "symbol": symbol,
            "dominant_bias": dominant_bias,
            "bias_counts": bias_counts,
            "last_auto_adjust": last_auto_adjust,
        }

    def _should_prefer_modify_from_memory(
        self,
        trade: Trade,
        decision_score: int,
        close_signals: dict[str, Any],
        symbol_memory: dict[str, Any],
    ) -> tuple[bool, str]:
        """Use prior analysis/actions to prevent flip-flop close behavior."""
        if decision_score <= 1:
            return False, "extreme_score_requires_close_consideration"

        dominant_bias = symbol_memory.get("dominant_bias")
        if dominant_bias == "bullish" and trade.direction == TradeDirection.BUY:
            return True, "memory_bias_supports_buy"
        if dominant_bias == "bearish" and trade.direction == TradeDirection.SELL:
            return True, "memory_bias_supports_sell"

        last_auto_adjust = symbol_memory.get("last_auto_adjust") or {}
        last_action = str(last_auto_adjust.get("action") or "").lower()
        last_direction = str(last_auto_adjust.get("direction") or "").upper()
        this_direction = str(trade.direction.value).upper()

        # Avoid back-to-back closes on opposite directions from conflicting narratives.
        if last_action == "close" and last_direction and last_direction != this_direction:
            return True, "recent_opposite_side_close_detected"

        if bool(close_signals.get("ambiguous_bias")):
            return True, "ambiguous_analysis_bias"

        return False, ""

    def _extract_levels_from_analysis(self, text: str) -> list[float]:
        """Extract candidate structure/liquidity levels from AI text."""
        if not text:
            return []

        matches = re.findall(r"(?<!\d)(\d{1,7}(?:\.\d{1,6})?)(?!\d)", text)
        levels: list[float] = []
        for m in matches:
            try:
                levels.append(float(m))
            except (TypeError, ValueError):
                continue
        return levels

    def _target_rr_from_behavior(self, analysis_text: str, score: int) -> float:
        """Select a dynamic RR target from AI-detected market behavior.

        We intentionally do NOT enforce 1:2 for all conditions. Ranging/choppy
        setups can use ~1:1 while trend/momentum setups can target higher RR.
        """
        range_terms = (
            "range",
            "ranging",
            "choppy",
            "mean reversion",
            "countertrend",
            "scalp",
            "low volatility",
            "inside day",
        )
        trend_terms = (
            "trend",
            "trend-aligned",
            "momentum",
            "displacement",
            "continuation",
            "breakout",
            "strong session",
        )

        if any(term in analysis_text for term in range_terms):
            return 1.0
        if any(term in analysis_text for term in trend_terms):
            return 1.8
        if score <= 2:
            return 1.0
        return 1.3

    def _risk_multiplier_from_liquidity(self, analysis_text: str) -> float:
        """Adjust stop distance when AI warns about nearby liquidity sweeps."""
        liquidity_terms = (
            "liquidity",
            "liquidity sweep",
            "stop hunt",
            "inducement",
            "untouched liquidity",
            "order block",
            "fvg",
        )
        if any(term in analysis_text for term in liquidity_terms):
            return 1.2
        return 1.0

    def _pick_directional_levels(self, levels: list[float], entry: float, direction: TradeDirection) -> tuple[list[float], list[float]]:
        below = sorted([lvl for lvl in levels if lvl < entry], reverse=True)
        above = sorted([lvl for lvl in levels if lvl > entry])
        if direction == TradeDirection.BUY:
            return below, above
        return above, below

    def _propose_levels(self, trade: Trade) -> tuple[Optional[float], Optional[float]]:
        """Build AI-guided SL/TP using market behavior and liquidity clues.

        Uses AI analysis text to infer market regime and liquidity zones, then
        applies a dynamic RR target (including 1:1 when conditions warrant it).
        """
        entry = float(trade.entry_price)
        direction = trade.direction
        score = int(trade.ai_score or 0)
        analysis_text = self._analysis_text(trade)
        raw_levels = self._extract_levels_from_analysis(analysis_text)
        directional_stop_levels, directional_target_levels = self._pick_directional_levels(raw_levels, entry, direction)

        # Reuse existing distance where possible to avoid surprising large jumps.
        if trade.sl is not None:
            base_risk = abs(entry - float(trade.sl))
        else:
            base_risk = max(abs(entry) * 0.002, 0.0005)

        risk = base_risk * self._risk_multiplier_from_liquidity(analysis_text)
        target_rr = self._target_rr_from_behavior(analysis_text, score)

        level_buffer = max(risk * 0.08, max(abs(entry) * 0.0001, 0.0001))

        # Stop: prefer nearest structural/liquidity level on invalidation side.
        if directional_stop_levels:
            structural_sl = directional_stop_levels[0]
            if direction == TradeDirection.BUY:
                new_sl = structural_sl - level_buffer
            else:
                new_sl = structural_sl + level_buffer
        else:
            new_sl = entry - risk if direction == TradeDirection.BUY else entry + risk

        actual_risk = abs(entry - new_sl)
        reward_distance = max(actual_risk * target_rr, max(abs(entry) * 0.0002, 0.0002))

        projected_tp = entry + reward_distance if direction == TradeDirection.BUY else entry - reward_distance

        # TP: prefer a directional structure/liquidity level near projected RR target.
        if directional_target_levels:
            if direction == TradeDirection.BUY:
                higher_or_equal = [lvl for lvl in directional_target_levels if lvl >= projected_tp]
                new_tp = higher_or_equal[0] if higher_or_equal else directional_target_levels[-1]
            else:
                lower_or_equal = [lvl for lvl in directional_target_levels if lvl <= projected_tp]
                new_tp = lower_or_equal[-1] if lower_or_equal else directional_target_levels[-1]
        else:
            new_tp = projected_tp

        # Preserve existing TP if it is already aligned with current market behavior.
        if trade.tp is not None and trade.sl is not None:
            current_reward = abs(float(trade.tp) - entry)
            current_risk = abs(entry - float(trade.sl))
            current_rr = (current_reward / current_risk) if current_risk > 0 else None
            if current_rr is not None and current_rr >= target_rr:
                new_tp = float(trade.tp)

        # Safety guardrails: ensure SL/TP are on correct sides.
        if direction == TradeDirection.BUY:
            if new_sl >= entry:
                new_sl = entry - max(base_risk, 0.0002)
            if new_tp <= entry:
                new_tp = entry + max(base_risk * target_rr, 0.0002)
        else:
            if new_sl <= entry:
                new_sl = entry + max(base_risk, 0.0002)
            if new_tp >= entry:
                new_tp = entry - max(base_risk * target_rr, 0.0002)

        return round(new_sl, 6), round(new_tp, 6)

    def _upsert_auto_adjust_note(self, existing: Optional[str], action: str) -> str:
        marker = f"[auto_adjust:{action}]"
        text = (existing or "").strip()
        if "[auto_adjust:" in text:
            import re

            return re.sub(r"\[auto_adjust:[^\]]+\]", marker, text)
        if not text:
            return marker
        return f"{text} {marker}"

    async def _recent_auto_adjust_exists(self, trade_id: uuid.UUID, cooldown_seconds: int) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max(0, cooldown_seconds))
        async with async_session_factory() as db:
            result = await db.execute(
                select(TradeLog)
                .where(
                    and_(
                        TradeLog.trade_id == trade_id,
                        TradeLog.event_type == "auto_adjust",
                        TradeLog.created_at >= cutoff,
                    )
                )
                .order_by(TradeLog.created_at.desc())
            )
            return result.scalar_one_or_none() is not None

    async def _auto_adjust_action_count(self, trade_id: uuid.UUID) -> int:
        async with async_session_factory() as db:
            result = await db.execute(
                select(TradeLog).where(
                    and_(
                        TradeLog.trade_id == trade_id,
                        TradeLog.event_type == "auto_adjust",
                    )
                )
            )
            return len(result.scalars().all())

    def _is_strong_misalignment(
        self,
        trade: Trade,
        decision_score: int,
        market_context: Optional[dict[str, Any]] = None,
    ) -> tuple[bool, dict[str, Any]]:
        text = self._analysis_text(trade)
        hard_misalignment_cues = (
            "misaligned",
            "against trend",
            "against operator flow",
            "retail trap",
            "avoid",
            "high probability of stop-out",
            "stop-hunt path",
        )

        has_hard_text_misalignment = any(cue in text for cue in hard_misalignment_cues)

        bullish_terms = ("bullish", "buy movement", "uptrend", "long setup")
        bearish_terms = ("bearish", "sell movement", "downtrend", "short setup")
        has_bullish_bias = any(term in text for term in bullish_terms)
        has_bearish_bias = any(term in text for term in bearish_terms)
        ambiguous_bias = has_bullish_bias and has_bearish_bias

        trend_conflict = False
        trend = ""
        direction = str(trade.direction.value).upper()

        if market_context:
            trend = str(market_context.get("overall_trend") or market_context.get("trend") or "").lower()
            trend_conflict = (direction == "BUY" and trend == "bearish") or (direction == "SELL" and trend == "bullish")

        # Treat score <= 1 as extreme quality failure; score 2-3 should prefer modify, not forced close.
        extreme_score = decision_score <= 1

        # Hybrid close-first now needs stronger confirmation to avoid contradictory closes.
        should_force_close = (
            (trend_conflict and extreme_score)
            or (has_hard_text_misalignment and extreme_score)
            or (has_hard_text_misalignment and trend_conflict and not ambiguous_bias)
        )

        return should_force_close, {
            "direction": direction,
            "trend": trend,
            "trend_conflict": trend_conflict,
            "hard_text_misalignment": has_hard_text_misalignment,
            "ambiguous_bias": ambiguous_bias,
            "extreme_score": extreme_score,
        }

    async def maybe_auto_adjust_trade(
        self,
        user_id: str,
        trade_id: str,
        trigger: str = "score_update",
        score_override: Optional[int] = None,
        market_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Apply auto-adjust policy to a single open trade if eligible."""
        app_settings = get_settings()
        if not getattr(app_settings, "AUTO_ADJUST_BETA_ENABLED", False):
            return {"applied": False, "reason": "beta_disabled"}

        user_uuid = uuid.UUID(user_id)
        trade_uuid = uuid.UUID(trade_id)

        async with async_session_factory() as db:
            user = (await db.execute(select(User).where(User.id == user_uuid))).scalar_one_or_none()
            trade = (await db.execute(select(Trade).where(Trade.id == trade_uuid))).scalar_one_or_none()
            if not user or not trade:
                return {"applied": False, "reason": "not_found"}

            if trade.status != TradeStatus.OPEN:
                return {"applied": False, "reason": "not_open"}
            if not trade.external_trade_id:
                return {"applied": False, "reason": "missing_external_trade_id"}
            if trade.ai_score is None and score_override is None:
                return {"applied": False, "reason": "missing_ai_score"}
            if not self._is_enabled_for_user(user):
                return {"applied": False, "reason": "user_disabled"}
            if not self._is_symbol_allowed(user, trade.symbol):
                return {"applied": False, "reason": "symbol_not_enabled"}

            threshold = self._threshold_for_user(user)
            decision_score = int(score_override if score_override is not None else trade.ai_score)
            if decision_score > threshold:
                return {"applied": False, "reason": "score_not_low_enough", "score": decision_score}

            max_actions_per_trade = max(
                1,
                int(getattr(app_settings, "AUTO_ADJUST_MAX_ACTIONS_PER_TRADE", 1) or 1),
            )
            action_count = await self._auto_adjust_action_count(trade.id)
            if action_count >= max_actions_per_trade:
                return {
                    "applied": False,
                    "reason": "max_actions_reached",
                    "max_actions": max_actions_per_trade,
                    "action_count": action_count,
                }

            cooldown = int(getattr(app_settings, "AUTO_ADJUST_COOLDOWN_SECONDS", 120) or 120)
            if await self._recent_auto_adjust_exists(trade.id, cooldown):
                return {"applied": False, "reason": "cooldown_active"}

            mode = self._mode_for_user(user)
            account_id = user.metaapi_account_id
            if not account_id:
                return {"applied": False, "reason": "missing_metaapi_account_id"}

            from app.services.metaapi_service import metaapi_service

            action_result: dict[str, Any] = {"ok": False, "error": "not_attempted"}
            action = "none"
            close_first, close_signals = self._is_strong_misalignment(
                trade,
                decision_score=decision_score,
                market_context=market_context,
            )
            symbol_memory = await self._get_symbol_memory(user.id, trade.symbol)

            if mode == "hybrid" and close_first:
                prefer_modify, memory_reason = self._should_prefer_modify_from_memory(
                    trade=trade,
                    decision_score=decision_score,
                    close_signals=close_signals,
                    symbol_memory=symbol_memory,
                )
                if prefer_modify:
                    close_first = False
                    close_signals["memory_override"] = memory_reason

            if mode in {"close", "hybrid"} and close_first:
                action = "close"
                action_result = await metaapi_service.close_position(
                    user_id=user_id,
                    account_id=account_id,
                    external_trade_id=str(trade.external_trade_id),
                    reason=f"{trigger}:score={decision_score}:close_first",
                )
                mode = "close"

            if mode in {"modify", "hybrid"} and action != "close":
                new_sl, new_tp = self._propose_levels(trade)
                action = "modify"
                action_result = await metaapi_service.modify_position(
                    user_id=user_id,
                    account_id=account_id,
                    external_trade_id=str(trade.external_trade_id),
                    new_sl=new_sl,
                    new_tp=new_tp,
                    reason=f"{trigger}:score={decision_score}",
                )
                if action_result.get("ok"):
                    # Reflect change in our DB + WS immediately while broker stream catches up.
                    from app.services.trade_processing_service import trade_processor

                    await trade_processor.process_trade_updated(
                        user_id,
                        {
                            "external_id": str(trade.external_trade_id),
                            "sl": new_sl,
                            "tp": new_tp,
                        },
                        live_pnl_only=False,
                    )

            if (mode == "close") or (mode == "hybrid" and not action_result.get("ok")):
                action = "close"
                action_result = await metaapi_service.close_position(
                    user_id=user_id,
                    account_id=account_id,
                    external_trade_id=str(trade.external_trade_id),
                    reason=f"{trigger}:score={decision_score}",
                )

            db.add(
                TradeLog(
                    trade_id=trade.id,
                    user_id=trade.user_id,
                    event_type="auto_adjust",
                    payload={
                        "trigger": trigger,
                        "score": decision_score,
                        "score_source": "override" if score_override is not None else "ai_score",
                        "threshold": threshold,
                        "mode": mode,
                        "close_signals": close_signals,
                        "symbol_memory": symbol_memory,
                        "action": action,
                        "result": action_result,
                    },
                )
            )

            if action_result.get("ok"):
                trade.notes = self._upsert_auto_adjust_note(trade.notes, action)
                await db.commit()
                logger.info(
                    "Auto-adjust applied: user=%s trade=%s action=%s score=%s",
                    user_id,
                    trade_id,
                    action,
                    decision_score,
                )
                return {"applied": True, "action": action, "result": action_result}

            await db.commit()

            return {"applied": False, "reason": action_result.get("error", "action_failed"), "action": action}

    async def run_periodic_pass(self) -> dict[str, int]:
        """Evaluate eligible open trades and apply auto-adjust policy as needed."""
        scanned = 0
        applied = 0

        async with async_session_factory() as db:
            result = await db.execute(
                select(Trade, User)
                .join(User, User.id == Trade.user_id)
                .where(
                    and_(
                        Trade.status == TradeStatus.OPEN,
                        Trade.ai_score.is_not(None),
                        User.is_active == True,
                    )
                )
                .order_by(Trade.open_time.desc())
                .limit(100)
            )
            rows = result.all()

        for trade, user in rows:
            scanned += 1
            try:
                outcome = await self.maybe_auto_adjust_trade(str(user.id), str(trade.id), trigger="periodic")
                if outcome.get("applied"):
                    applied += 1
            except Exception as e:
                logger.debug(f"Auto-adjust periodic trade check failed for {trade.id}: {e}")

        return {"scanned": scanned, "applied": applied}


auto_adjust_service = AutoAdjustService()
