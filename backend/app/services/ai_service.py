"""AI analysis service.
from typing import List, Dict,  Optional, Union

Provides pre-trade scoring, post-trade review, and weekly report generation
using the configured OpenAI model for all analyses.
"""

import json
import logging
import re
from typing import List, Dict,  Optional, Any, Callable, Awaitable

import openai

from app.config import get_settings
from app.schemas.analysis import TradeScore, TradeReview, WeeklyReport

logger = logging.getLogger(__name__)
settings = get_settings()
AI_MODEL = settings.OPENAI_MODEL or "gpt-5.2"

# ---------------------------------------------------------------------------
# Institutional operator persona — used as the system role for all AI calls.
# The AI acts as a senior market maker / liquidity analyst on a prop desk,
# evaluating whether the retail trader is aligned with smart-money positioning
# or walking into a liquidity trap.
# ---------------------------------------------------------------------------
OPERATOR_SYSTEM_PROMPT = (
    "You are a senior institutional operator and liquidity analyst on a proprietary trading desk. "
    "You think exclusively in terms of:\n"
    "- Buy-side and sell-side liquidity pools (where retail stops are clustered above swing highs / below swing lows)\n"
    "- Order blocks: the last up/down candle before a displacement move — where institutional orders were placed\n"
    "- Inducement, stop hunts, and liquidity sweeps that precede real directional moves\n"
    "- Fair Value Gaps (FVGs) and imbalance zones that price is drawn back into to rebalance\n"
    "- DXY / dollar-index correlation for forex pairs and intermarket alignment\n"
    "- Smart money accumulation / distribution vs retail trap setups\n"
    "- Session liquidity windows: London open, NY open, and the London/NY overlap as peak institutional activity periods\n\n"
    "You speak directly and clinically — like a senior desk trader reviewing a junior's setup. "
    "Your analysis names WHERE smart money is positioned, identifies whether the retail entry is WITH or AGAINST operator flow, "
    "and pinpoints any liquidity pools that price is likely to sweep before honouring or invalidating the move.\n"
    "Respond only with valid JSON."
)


def _to_float(value: Any) -> Optional[float]:
    """Best-effort conversion to float for numeric prompt math."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_rr(entry: Optional[float], sl: Optional[float], tp: Optional[float]) -> Optional[float]:
    """Compute R:R from absolute price distances."""
    if entry is None or sl is None or tp is None:
        return None
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    reward = abs(tp - entry)
    return round(reward / risk, 2)


def _compute_modified_trade_metrics(trade: dict, new_sl: Any, new_tp: Any) -> Dict[str, Any]:
    """Compute objective before/after risk and R:R metrics for SL/TP modifications."""
    entry = _to_float(trade.get("entry_price"))
    old_sl = _to_float(trade.get("sl"))
    old_tp = _to_float(trade.get("tp"))
    next_sl = _to_float(new_sl)
    next_tp = _to_float(new_tp)

    old_risk = abs(entry - old_sl) if entry is not None and old_sl is not None else None
    new_risk = abs(entry - next_sl) if entry is not None and next_sl is not None else None

    old_rr = _compute_rr(entry, old_sl, old_tp)
    new_rr = _compute_rr(entry, next_sl, next_tp)

    tighter_sl = (
        old_risk is not None and
        new_risk is not None and
        new_risk < old_risk
    )
    wider_sl = (
        old_risk is not None and
        new_risk is not None and
        new_risk > old_risk
    )
    rr_improved = (
        old_rr is not None and
        new_rr is not None and
        new_rr >= old_rr
    )
    objective_improvement = tighter_sl and rr_improved

    return {
        "entry": entry,
        "old_sl": old_sl,
        "old_tp": old_tp,
        "new_sl": next_sl,
        "new_tp": next_tp,
        "old_risk": round(old_risk, 5) if old_risk is not None else None,
        "new_risk": round(new_risk, 5) if new_risk is not None else None,
        "old_rr": old_rr,
        "new_rr": new_rr,
        "tighter_sl": tighter_sl,
        "wider_sl": wider_sl,
        "rr_improved": rr_improved,
        "objective_improvement": objective_improvement,
    }


def _extract_open_thesis(original_analysis: Optional[dict]) -> dict:
    if not isinstance(original_analysis, dict):
        return {}
    thesis = original_analysis.get("open_thesis")
    if isinstance(thesis, dict):
        return thesis
    return original_analysis


def _extract_candidate_prices(text: str) -> List[float]:
    if not text:
        return []
    matches = re.findall(r"(?<!\d)(\d{1,7}(?:\.\d{1,6})?)(?!\d)", text)
    values: List[float] = []
    for match in matches:
        try:
            values.append(float(match))
        except (TypeError, ValueError):
            continue
    return values


def _is_wider_sl_supported_by_original_analysis(metrics: Dict[str, Any], original_analysis: Optional[dict]) -> bool:
    if not metrics.get("wider_sl"):
        return False

    thesis = _extract_open_thesis(original_analysis)
    if not thesis:
        return False

    suggestion_text = str(thesis.get("suggestion", ""))
    summary_text = str(thesis.get("summary", ""))
    risk_text = str(thesis.get("risk_assessment", ""))
    combined = f"{suggestion_text} {summary_text} {risk_text}".lower()

    widening_intent_terms = (
        "liquidity",
        "liquidity sweep",
        "stop hunt",
        "avoid sweep",
        "move stop",
        "move sl",
        "wider stop",
        "give room",
        "above cluster",
        "below cluster",
    )
    if not any(term in combined for term in widening_intent_terms):
        return False

    # Strong signal: suggested level is numerically close to applied SL.
    new_sl = metrics.get("new_sl")
    old_risk = metrics.get("old_risk")
    if new_sl is None:
        return True

    candidate_prices = _extract_candidate_prices(combined)
    if not candidate_prices:
        return True

    # Dynamic tolerance: around 20% of prior risk distance (fallback 0.001).
    tolerance = max((old_risk or 0) * 0.2, 0.001)
    closest = min(abs(new_sl - level) for level in candidate_prices)
    return closest <= tolerance


def _apply_modified_trade_consistency_guard(
    result: Dict[str, Any],
    metrics: Dict[str, Any],
    original_analysis: Optional[dict] = None,
) -> Dict[str, Any]:
    """Prevent contradictory modified-trade output when objective math shows improvement."""
    score = result.get("score", 5)
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 5

    old_rr = metrics.get("old_rr")
    new_rr = metrics.get("new_rr")
    rr_drop_ratio = None
    if old_rr and new_rr is not None and old_rr > 0:
        rr_drop_ratio = max(0.0, (old_rr - new_rr) / old_rr)

    objective_improvement = metrics.get("objective_improvement")
    supported_wider_sl = _is_wider_sl_supported_by_original_analysis(metrics, original_analysis)

    if not objective_improvement and not supported_wider_sl:
        return result

    if objective_improvement:
        result["score"] = max(score, 7)
    else:
        # If trader followed prior AI guidance to widen SL for liquidity protection,
        # do not downgrade as a poor change solely due larger risk distance.
        acceptable_tradeoff = rr_drop_ratio is None or rr_drop_ratio <= 0.35
        result["score"] = max(score, 7 if acceptable_tradeoff else 6)

    contradiction_terms = (
        "increasing risk",
        "increased risk",
        "higher risk",
        "reducing r:r",
        "reduced r:r",
        "widening sl",
        "wider stop",
    )

    summary_text = str(result.get("summary", ""))
    risk_text = str(result.get("risk_assessment", ""))
    combined = f"{summary_text} {risk_text}".lower()
    if any(term in combined for term in contradiction_terms):
        if objective_improvement:
            result["summary"] = "The SL adjustment tightens risk and preserves/improves the setup's R:R profile."
            result["risk_assessment"] = (
                f"Risk distance tightened from {metrics.get('old_risk')} to {metrics.get('new_risk')} "
                f"and R:R moved from {metrics.get('old_rr')} to {metrics.get('new_rr')}."
            )
        elif supported_wider_sl:
            result["summary"] = "SL was widened in line with the earlier liquidity-protection suggestion; this is a planned risk trade-off."
            result["risk_assessment"] = (
                f"Risk distance changed from {metrics.get('old_risk')} to {metrics.get('new_risk')} and "
                f"R:R moved from {metrics.get('old_rr')} to {metrics.get('new_rr')}. "
                "Treat this as acceptable only if it preserves the original structural thesis."
            )

    issues = result.get("issues")
    if not isinstance(issues, list):
        issues = []
    if supported_wider_sl:
        issues = [
            issue for issue in issues
            if "widen" not in str(issue).lower() and "increasing" not in str(issue).lower()
        ]
    result["issues"] = issues[:4]

    strengths = result.get("strengths")
    if not isinstance(strengths, list):
        strengths = []
    if objective_improvement:
        strengths.append(
            f"SL was tightened ({metrics.get('old_risk')} → {metrics.get('new_risk')} risk distance), improving trade protection."
        )
    elif supported_wider_sl:
        strengths.append(
            "SL adjustment follows the prior AI liquidity-sweep guidance rather than emotional stop movement."
        )
    result["strengths"] = strengths[:4]

    return result


def _build_pre_trade_prompt(
    trade: dict,
    market_context: Optional[dict],
    user_history: Optional[dict],
    behavioral_flags: Optional[List[dict]],
    open_positions: Optional[List[dict]] = None,
) -> str:
    """Build a comprehensive prompt for pre-trade AI analysis.

    Args:
        trade: Trade data dict.
        market_context: Current market conditions (trend, ATR, key levels).
        user_history: Recent trading performance summary.
        behavioral_flags: Any behavioral alerts triggered.
        open_positions: List of other currently open trades for this user.

    Returns:
        Formatted prompt string.
    """
    flags_text = ""
    if behavioral_flags:
        flags_text = "\n".join(
            f"  - [{f.get('severity', 'unknown').upper()}] {f.get('flag', 'unknown')}: {f.get('message', '')}"
            for f in behavioral_flags
        )
    else:
        flags_text = "  None detected"

    market_text = ""
    if market_context:
        fib = market_context.get('fibonacci_pivots')
        if fib:
            fib_text = (
                f"Pivot: {fib.get('pivot', 'N/A')} | "
                f"R1: {fib.get('r1', 'N/A')} R2: {fib.get('r2', 'N/A')} R3: {fib.get('r3', 'N/A')} | "
                f"S1: {fib.get('s1', 'N/A')} S2: {fib.get('s2', 'N/A')} S3: {fib.get('s3', 'N/A')}"
            )
        else:
            fib_text = "N/A"

        bb_pct = market_context.get('bb_percent_b')
        bb_pct_str = f"{bb_pct:.2f}" if bb_pct is not None else "N/A"
        bb_squeeze = market_context.get('bb_squeeze')
        bb_squeeze_str = "YES (tight consolidation)" if bb_squeeze else ("no" if bb_squeeze is not None else "N/A")

        news_event = market_context.get('nearest_news_event') or "None"
        m15 = market_context.get("m15_context") or {}
        m15_text = "N/A"
        if m15:
            m15_text = (
                f"M15 Trend: {m15.get('trend', 'N/A')} (EMA20: {m15.get('ema20_trend', 'N/A')}, EMA50: {m15.get('ema50_trend', 'N/A')})\n"
                f"M15 ATR(14): {m15.get('atr', 'N/A')}  Breakout: {m15.get('breakout_state', 'N/A')}\n"
                f"M15 Last Pattern: {m15.get('candle_pattern', 'N/A')}  BodyRatio: {m15.get('body_ratio', 'N/A')}  "
                f"UpperWick: {m15.get('upper_wick_ratio', 'N/A')}  LowerWick: {m15.get('lower_wick_ratio', 'N/A')}\n"
                f"Distance to nearest H1 support/resistance (M15 ATR): "
                f"{m15.get('distance_to_h1_support_atr', 'N/A')} / {m15.get('distance_to_h1_resistance_atr', 'N/A')}"
            )

        market_text = f"""
Current Price: {market_context.get('current_price', 'N/A')}

[TREND]
H1 Trend: {market_context.get('overall_trend', 'N/A')} (EMA20: {market_context.get('ema20_trend', 'N/A')}, EMA50: {market_context.get('ema50_trend', 'N/A')}, EMA200: {market_context.get('ema200_trend', 'N/A')})
HTF Daily Trend: {market_context.get('htf_trend', 'N/A')}

[MOMENTUM]
RSI(14): {market_context.get('rsi', 'N/A')} — {market_context.get('rsi_state', 'N/A')}
MACD: line={market_context.get('macd_line', 'N/A')}  signal={market_context.get('signal_line', 'N/A')}  hist={market_context.get('histogram', 'N/A')}  cross={market_context.get('macd_cross', 'N/A')}
Bollinger Bands: upper={market_context.get('bb_upper', 'N/A')}  lower={market_context.get('bb_lower', 'N/A')}  %B={bb_pct_str}  squeeze={bb_squeeze_str}

[VOLATILITY]
ATR(14): {market_context.get('atr', 'N/A')}
ATR Percentile: {market_context.get('atr_percentile', 'N/A')}  Regime: {market_context.get('volatility_regime', 'N/A')}
Daily Range Used: {market_context.get('daily_range_percent', 'N/A')}%

[KEY LEVELS]
Prev Day High: {market_context.get('prev_day_high', 'N/A')}  Low: {market_context.get('prev_day_low', 'N/A')}  Close: {market_context.get('prev_day_close', 'N/A')}
Key Support: {market_context.get('support_levels', 'N/A')}  (distance: {market_context.get('distance_to_support_atr', 'N/A')} ATR)
Key Resistance: {market_context.get('resistance_levels', 'N/A')}  (distance: {market_context.get('distance_to_resistance_atr', 'N/A')} ATR)
Fibonacci Pivots: {fib_text}

[CANDLE & SESSION]
Last Candle Pattern: {market_context.get('candle_pattern', 'N/A')}
Session: {market_context.get('session', 'N/A')}

[NEWS RISK]
Risk Level: {market_context.get('news_risk_level', 'N/A')}  High-impact events in 1h: {market_context.get('news_events_1h', 0)}
High-impact events in 15m: {market_context.get('news_events_15m', 0)}
Nearest Event: {news_event}

[EXECUTION (M15)]
{m15_text}"""
    else:
        market_text = "  Market context unavailable"

    history_text = ""
    if user_history:
        history_text = f"""
Recent Win Rate: {user_history.get('win_rate', 'N/A')}%
Last 10 Trades P&L: {user_history.get('last_10_pnl', 'N/A')}
R-Expectancy: {user_history.get('r_expectancy', 'N/A')}
Today's Trades: {user_history.get('today_trades', 0)}
Today's P&L: {user_history.get('today_pnl', 'N/A')}
Winning Streak: {user_history.get('streak', 'N/A')}"""
    else:
        history_text = "  No history available"

    if open_positions:
        pos_lines = [
            f"  {i+1}. {p.get('symbol')} {p.get('direction')} @ {p.get('entry_price')} "
            f"| SL: {p.get('sl', 'none')} | TP: {p.get('tp', 'none')} | Lot: {p.get('lot_size')}"
            for i, p in enumerate(open_positions)
        ]
        positions_text = f"Total open: {len(open_positions)}\n" + "\n".join(pos_lines)
    else:
        positions_text = "  None"

    # --- INSTITUTIONAL CONTEXT block (derived from existing market_context data) ---
    inst_context_text = ""
    if market_context:
        current_price = _to_float(market_context.get('current_price'))
        prev_day_high = _to_float(market_context.get('prev_day_high'))
        prev_day_low  = _to_float(market_context.get('prev_day_low'))
        atr_pct = market_context.get('atr_percentile')
        vol_regime = market_context.get('volatility_regime', 'N/A')
        session = market_context.get('session', 'N/A')
        bb_squeeze = market_context.get('bb_squeeze')
        resistance = market_context.get('resistance_levels', 'N/A')
        support = market_context.get('support_levels', 'N/A')

        # Determine if prev-day high/low was just swept (potential liquidity grab)
        sweep_note = "N/A"
        if current_price is not None and prev_day_high is not None and prev_day_low is not None:
            atr_val = _to_float(market_context.get('atr')) or 0
            if abs(current_price - prev_day_high) <= max(atr_val * 0.3, 0.0005):
                sweep_note = f"Price is AT/NEAR prev-day high ({prev_day_high}) — potential buy-side liquidity sweep in progress"
            elif abs(current_price - prev_day_low) <= max(atr_val * 0.3, 0.0005):
                sweep_note = f"Price is AT/NEAR prev-day low ({prev_day_low}) — potential sell-side liquidity sweep in progress"
            elif current_price > prev_day_high:
                sweep_note = f"Price ABOVE prev-day high ({prev_day_high}) — buy-side liquidity already swept, watch for reversal"
            elif current_price < prev_day_low:
                sweep_note = f"Price BELOW prev-day low ({prev_day_low}) — sell-side liquidity already swept, watch for reversal"
            else:
                sweep_note = f"Price between prev-day range ({prev_day_low} – {prev_day_high}) — no external liquidity sweep yet"

        # Session activity label
        session_activity = "standard activity"
        if session:
            s_lower = session.lower()
            if "london" in s_lower and "ny" in s_lower:
                session_activity = "PEAK — London/NY overlap (highest institutional order flow)"
            elif "london" in s_lower:
                session_activity = "HIGH — London open (institutional desk active)"
            elif "new york" in s_lower or "ny" in s_lower:
                session_activity = "HIGH — NY open (institutional desk active)"
            elif "asian" in s_lower:
                session_activity = "LOW — Asian session (liquidity accumulation / ranging more likely)"

        # Volatility regime interpretation
        squeeze_note = ""
        if bb_squeeze:
            squeeze_note = " | BB SQUEEZE active — consolidation phase, potential displacement/FVG imminent"

        inst_context_text = f"""
## INSTITUTIONAL CONTEXT
Buy-Side Liquidity Pool (above): {resistance} — retail BUY stops cluster here; smart money may sweep this before reversing
Sell-Side Liquidity Pool (below): {support} — retail SELL stops cluster here; smart money may sweep this before reversing
Prev-Day Liquidity Sweep Status: {sweep_note}
Volatility Regime: ATR percentile={atr_pct} | {vol_regime}{squeeze_note}
Session Activity: {session} — {session_activity}
Operator Note: identify whether this entry is AFTER a liquidity sweep (ideal) or INTO an untouched liquidity pool (trap risk)."""

    return f"""You are a senior operator on an institutional trading desk reviewing a retail trade setup submitted by a junior trader.
Your mandate: determine whether this entry is WITH smart-money / institutional order flow or is walking into a liquidity trap.

Assess the following in your analysis:
1. Is price being DRAWN TOWARD a liquidity pool (buy-side above, sell-side below) — meaning it may sweep stops before the real move?
2. Has a liquidity sweep ALREADY occurred before this entry — validating the setup?
3. Does the entry align with a high-probability order block or Fair Value Gap?
4. Is the session timing aligned with institutional desk activity (London/NY open)?
5. Is the retail trader entering WHERE smart money is EXITING (a distribution/inducement zone)?

Provide a trade quality score 1–10 from the operator's perspective.

## TRADE SETUP
Symbol: {trade.get('symbol', 'N/A')}
Direction: {trade.get('direction', 'N/A')}
Entry Price: {trade.get('entry_price', 'N/A')}
Stop Loss: {trade.get('sl', 'Not set')}
Take Profit: {trade.get('tp', 'Not set')}
Lot Size: {trade.get('lot_size', 'N/A')}
R:R Ratio: {trade.get('rr_ratio', 'N/A')}

## MARKET CONTEXT
{market_text}
{inst_context_text}

## TRADER HISTORY
{history_text}

## BEHAVIORAL FLAGS
{flags_text}

## OTHER OPEN POSITIONS (PORTFOLIO CONTEXT)
{positions_text}

## SCORING CRITERIA (OPERATOR PERSPECTIVE)
- 9-10: Setup mirrors institutional positioning — entry after confirmed liquidity sweep, clean order block or FVG, strong session alignment, R:R ≥ 2.5, no structural traps ahead
- 7-8: Structurally sound — decent OB proximity or post-sweep entry, trend-aligned, manageable liquidity risk in the path
- 5-6: Mixed signals — entry near an untouched liquidity pool price hasn't swept yet, or weak session timing, or marginal R:R
- 3-4: Retail trap setup — entering without prior liquidity sweep, chasing a breakout directly into a buy/sell-side stop cluster, or counter to DXY alignment
- 1-2: Operator bait — price is in pure inducement territory, three or more structural red flags, high probability of a stop hunt before any move in the intended direction

## RESPONSE FORMAT
Respond ONLY with valid JSON (no markdown, no code fences):
{{
    "score": <1-10>,
    "confidence": <0.0-1.0>,
    "summary": "<one-line operator verdict on the setup>",
    "issues": ["<issue1>", "<issue2>"],
    "strengths": ["<strength1>", "<strength2>"],
    "suggestion": "<specific actionable instruction from the operator's desk>",
    "market_alignment": "<how this entry aligns or conflicts with smart-money / institutional order flow>",
    "risk_assessment": "<risk assessment: liquidity pools in path, R:R, position sizing relative to desk limits>"
}}

Be clinical and direct — like a senior desk trader. Call out liquidity traps by name. Praise setups that follow the money."""


def _build_post_trade_prompt(trade: dict, pre_score: Optional[dict]) -> str:
    """Build prompt for post-trade AI review.

    Args:
        trade: Completed trade data.
        pre_score: Pre-trade analysis if available.

    Returns:
        Formatted prompt string.
    """
    pre_score_text = ""
    if pre_score:
        pre_score_text = f"""
Pre-Trade Score: {pre_score.get('score', 'N/A')}/10
Pre-Trade Issues: {', '.join(pre_score.get('issues', []))}
Pre-Trade Suggestion: {pre_score.get('suggestion', 'N/A')}"""
    else:
        pre_score_text = "  No pre-trade analysis available"

    duration_min = (trade.get('duration_seconds', 0) or 0) / 60

    return f"""You are an expert trading analyst AI co-pilot. Review this completed trade and provide a post-trade analysis.

## COMPLETED TRADE
Symbol: {trade.get('symbol', 'N/A')}
Direction: {trade.get('direction', 'N/A')}
Entry: {trade.get('entry_price', 'N/A')}
Exit: {trade.get('exit_price', 'N/A')}
Stop Loss: {trade.get('sl', 'Not set')}
Take Profit: {trade.get('tp', 'Not set')}
P&L: {trade.get('pnl', 'N/A')}
P&L (R): {trade.get('pnl_r', 'N/A')}R
Duration: {duration_min:.1f} minutes
Behavioral Flags: {', '.join(trade.get('behavioral_flags', [])) or 'None'}

## PRE-TRADE ANALYSIS
{pre_score_text}

## RESPONSE FORMAT
Respond ONLY with valid JSON (no markdown, no code fences):
{{
    "execution_score": <1-10>,
    "plan_adherence": <1-10>,
    "summary": "<post-trade summary>",
    "lessons": ["<lesson1>", "<lesson2>"],
    "what_went_well": ["<point1>"],
    "what_to_improve": ["<point1>"],
    "emotional_assessment": "<assessment of likely emotional state and its impact>"
}}

Focus on process over outcome. A losing trade with good process should score higher than a winning trade with poor process."""


def _build_weekly_report_prompt(
    trades: List[dict],
    stats: dict,
) -> str:
    """Build prompt for weekly AI performance report.

    Args:
        trades: List of trade dicts for the week.
        stats: Aggregated statistics for the week.

    Returns:
        Formatted prompt string.
    """
    trades_summary = "\n".join(
        f"  {t.get('symbol')} {t.get('direction')} | Entry: {t.get('entry_price')} "
        f"Exit: {t.get('exit_price', 'N/A')} | P&L: {t.get('pnl', 'N/A')} | "
        f"Score: {t.get('ai_score', 'N/A')}/10 | Flags: {', '.join(t.get('behavioral_flags', []) or [])}"
        for t in trades[:50]  # Cap at 50 trades for context window
    )

    return f"""You are an expert trading performance coach. Generate a comprehensive weekly trading report.

## WEEKLY STATISTICS
Period: {stats.get('period', 'N/A')}
Total Trades: {stats.get('total_trades', 0)}
Win Rate: {stats.get('win_rate', 0):.1f}%
Total P&L: ${stats.get('total_pnl', 0):.2f}
Total R: {stats.get('total_r', 0):.2f}R
Best Trade: {stats.get('best_trade', 'N/A')}
Worst Trade: {stats.get('worst_trade', 'N/A')}
Avg AI Score: {stats.get('avg_ai_score', 'N/A')}/10
Total Behavioral Flags: {stats.get('total_flags', 0)}

## TRADE LOG
{trades_summary}

## RESPONSE FORMAT
Respond ONLY with valid JSON (no markdown, no code fences):
{{
    "period": "{stats.get('period', 'N/A')}",
    "overall_grade": "<A+ to F>",
    "summary": "<2-3 sentence performance summary>",
    "total_trades": {stats.get('total_trades', 0)},
    "win_rate": {stats.get('win_rate', 0)},
    "total_pnl": {stats.get('total_pnl', 0)},
    "total_r": {stats.get('total_r', 0)},
    "best_trade_summary": "<description of best trade and why>",
    "worst_trade_summary": "<description of worst trade and lessons>",
    "recurring_patterns": ["<pattern1>", "<pattern2>"],
    "strengths": ["<strength1>", "<strength2>"],
    "areas_for_improvement": ["<area1>", "<area2>"],
    "action_items": ["<specific action1>", "<specific action2>"],
    "emotional_profile": "<assessment of emotional patterns throughout the week>"
}}

Be a direct, honest coach. Praise genuinely good performance but don't shy away from calling out problems."""


def _parse_json_response(text: str) -> dict:
    """Parse a JSON response from an LLM, handling common formatting issues.

    Args:
        text: Raw text response from the LLM.

    Returns:
        Parsed dictionary.
    """
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}\nResponse: {text[:500]}")
        return {}


def _extract_token_usage(usage_obj: Any) -> Optional[Dict[str, int]]:
    """Normalize provider usage fields into input/output/total token counts."""
    if usage_obj is None:
        return None

    def _get(name: str) -> Optional[int]:
        value = getattr(usage_obj, name, None)
        if value is None and isinstance(usage_obj, dict):
            value = usage_obj.get(name)
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    input_tokens = _get("prompt_tokens") or _get("input_tokens")
    output_tokens = _get("completion_tokens") or _get("output_tokens")
    total_tokens = _get("total_tokens")

    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens

    if input_tokens is None and output_tokens is None and total_tokens is None:
        return None

    return {
        "input_tokens": input_tokens or 0,
        "output_tokens": output_tokens or 0,
        "total_tokens": total_tokens or ((input_tokens or 0) + (output_tokens or 0)),
    }


async def analyze_pre_trade(
    trade: dict,
    market_context: Optional[dict] = None,
    user_history: Optional[dict] = None,
    behavioral_flags: Optional[List[dict]] = None,
    open_positions: Optional[List[dict]] = None,
) -> TradeScore:
    """Run pre-trade AI analysis and return a quality score.

    Uses the configured OpenAI model for quick scoring on trade open.

    Args:
        trade: Normalized trade data dict.
        market_context: Current market conditions.
        user_history: Recent trading performance.
        behavioral_flags: Any behavioral alerts.
        open_positions: Other currently open trades for this user.

    Returns:
        TradeScore with score, issues, and suggestions.
    """
    # Check if API key is configured
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        logger.warning("⚠️ OpenAI API key not configured — using mock score")
        flag_count = len(behavioral_flags or [])
        score = max(1, min(10, 6 - (flag_count // 2)))  # Reduce score for each behavioral flag
        return TradeScore(
            score=score,
            confidence=0.6,
            summary="Mock analysis (API key not configured)",
            issues=[f.get("message", "") for f in (behavioral_flags or [])],
            strengths=["Trade has defined risk/reward"],
            suggestion="Configure OpenAI API key for full AI analysis",
            market_alignment="Unable to assess",
            risk_assessment=f"Risk = {trade.get('sl', 'N/A')}, Reward = {trade.get('tp', 'N/A')}",
        )
    
    prompt = _build_pre_trade_prompt(trade, market_context, user_history, behavioral_flags, open_positions)

    token_usage: Optional[Dict[str, int]] = None
    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": OPERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_completion_tokens=1000,
        )
        token_usage = _extract_token_usage(getattr(response, "usage", None))
        result = _parse_json_response(response.choices[0].message.content or "{}")
    except Exception as e:
        logger.error(f"OpenAI API error in pre-trade analysis: {e}")
        # Fallback score based on behavioral flags
        flag_count = len(behavioral_flags or [])
        fallback_score = max(1, 5 - flag_count)
        result = {
            "score": fallback_score,
            "confidence": 0.3,
            "summary": "AI analysis unavailable — scored based on behavioral flags only.",
            "issues": [f.get("message", "") for f in (behavioral_flags or [])],
            "strengths": [],
            "suggestion": "AI service is temporarily unavailable. Exercise extra caution.",
            "market_alignment": "Unable to assess — AI unavailable",
            "risk_assessment": "Unable to assess — AI unavailable",
        }

    return TradeScore(
        score=result.get("score", 5),
        confidence=result.get("confidence", 0.5),
        summary=result.get("summary", "Analysis unavailable"),
        issues=result.get("issues", []),
        strengths=result.get("strengths", []),
        suggestion=result.get("suggestion", "No suggestion available"),
        market_alignment=result.get("market_alignment", "Unknown"),
        risk_assessment=result.get("risk_assessment", "Unknown"),
        token_usage=token_usage,
    )


def _build_modified_trade_prompt(trade: dict, new_sl: Any, new_tp: Any, original_analysis: Optional[dict], market_context: Optional[dict] = None) -> str:
    """Build a prompt for analyzing a modified (SL/TP updated) open trade.

    Args:
        trade: Current trade data.
        new_sl: Updated stop loss value.
        new_tp: Updated take profit value.
        original_analysis: The AI analysis from when the trade was opened.
        market_context: Current live market conditions.

    Returns:
        Formatted prompt string.
    """
    orig_text = ""
    if original_analysis:
        # If original_analysis itself contains an open_thesis, use that as the entry thesis
        thesis = original_analysis.get("open_thesis") or original_analysis
        orig_text = f"""
Original Score: {thesis.get('score', 'N/A')}/10
Original Thesis: {thesis.get('summary', 'N/A')}
Original Strengths: {', '.join(thesis.get('strengths', []))}
Original Issues: {', '.join(thesis.get('issues', []))}
Original Suggestion: {thesis.get('suggestion', 'N/A')}
Market Alignment at Entry: {thesis.get('market_alignment', 'N/A')}
Risk Assessment at Entry: {thesis.get('risk_assessment', 'N/A')}"""
    else:
        orig_text = "  No original analysis available"

    market_text = ""
    if market_context and market_context.get("current_price"):
        fib = market_context.get('fibonacci_pivots')
        fib_text = (
            f"Pivot: {fib.get('pivot', 'N/A')} | "
            f"R1: {fib.get('r1', 'N/A')} R2: {fib.get('r2', 'N/A')} R3: {fib.get('r3', 'N/A')} | "
            f"S1: {fib.get('s1', 'N/A')} S2: {fib.get('s2', 'N/A')} S3: {fib.get('s3', 'N/A')}"
        ) if fib else "N/A"

        bb_pct = market_context.get('bb_percent_b')
        bb_pct_str = f"{bb_pct:.2f}" if bb_pct is not None else "N/A"
        bb_squeeze_str = "YES" if market_context.get('bb_squeeze') else "no"
        news_event = market_context.get('nearest_news_event') or "None"
        m15 = market_context.get("m15_context") or {}
        m15_text = "N/A"
        if m15:
            m15_text = (
                f"M15 Trend: {m15.get('trend', 'N/A')} (EMA20: {m15.get('ema20_trend', 'N/A')}, EMA50: {m15.get('ema50_trend', 'N/A')}) | "
                f"ATR: {m15.get('atr', 'N/A')} | Breakout: {m15.get('breakout_state', 'N/A')} | "
                f"Pattern: {m15.get('candle_pattern', 'N/A')} | "
                f"H1 distance (support/resistance, ATR): {m15.get('distance_to_h1_support_atr', 'N/A')} / {m15.get('distance_to_h1_resistance_atr', 'N/A')}"
            )

        market_text = f"""
Current Price: {market_context.get('current_price', 'N/A')}
H1 Trend: {market_context.get('overall_trend', 'N/A')} (EMA20: {market_context.get('ema20_trend', 'N/A')}, EMA50: {market_context.get('ema50_trend', 'N/A')}, EMA200: {market_context.get('ema200_trend', 'N/A')})
HTF Daily Trend: {market_context.get('htf_trend', 'N/A')}
RSI(14): {market_context.get('rsi', 'N/A')} ({market_context.get('rsi_state', 'N/A')})
MACD cross: {market_context.get('macd_cross', 'N/A')}  histogram: {market_context.get('histogram', 'N/A')}
Bollinger %B: {bb_pct_str}  squeeze: {bb_squeeze_str}
ATR(14): {market_context.get('atr', 'N/A')}  Regime: {market_context.get('volatility_regime', 'N/A')}
Prev Day High/Low/Close: {market_context.get('prev_day_high', 'N/A')} / {market_context.get('prev_day_low', 'N/A')} / {market_context.get('prev_day_close', 'N/A')}
Key Support: {market_context.get('support_levels', 'N/A')}  (distance: {market_context.get('distance_to_support_atr', 'N/A')} ATR)
Key Resistance: {market_context.get('resistance_levels', 'N/A')}  (distance: {market_context.get('distance_to_resistance_atr', 'N/A')} ATR)
Fibonacci Pivots: {fib_text}
Last Candle Pattern: {market_context.get('candle_pattern', 'N/A')}
Session: {market_context.get('session', 'N/A')}  Daily Range Used: {market_context.get('daily_range_percent', 'N/A')}%
News Risk: {market_context.get('news_risk_level', 'N/A')}  Events in 1h: {market_context.get('news_events_1h', 0)}  Events in 15m: {market_context.get('news_events_15m', 0)}  Nearest: {news_event}
M15 Execution: {m15_text}"""
    else:
        market_text = "  Market context unavailable — evaluate based on original thesis"

    metrics = _compute_modified_trade_metrics(trade, new_sl, new_tp)
    old_sl = metrics.get("old_sl")
    old_tp = metrics.get("old_tp")
    entry = metrics.get("entry")
    old_rr = metrics.get("old_rr", "N/A")
    new_rr = metrics.get("new_rr", "N/A")
    old_risk = metrics.get("old_risk", "N/A")
    new_risk = metrics.get("new_risk", "N/A")

    return f"""You are a senior operator reviewing a mid-trade position modification submitted by a junior trader on your desk.
Your mandate: assess whether this modification reflects DISCIPLINED institutional trade management or emotional retail behaviour.

Operator rules:
- Modifications that move SL BEHIND a structural order block or liquidity sweep level are sound — they protect the thesis.
- Modifications that WIDEN the SL into an untouched liquidity pool (inviting a sweep) without a structural reason are not.
- Moving TP closer to the current price without a valid resistance/distribution level nearby is premature — it reduces R:R for no structural gain.
- If the original desk suggestion explicitly advised placing SL at a specific liquidity level to avoid a sweep, that widening is PLANNED and should be treated as disciplined execution.

## OPEN TRADE
Symbol: {trade.get('symbol', 'N/A')}
Direction: {trade.get('direction', 'N/A')}
Entry Price: {entry}

## MODIFICATION
Previous Stop Loss: {old_sl} → New Stop Loss: {new_sl}
Previous Take Profit: {old_tp} → New Take Profit: {new_tp}
Previous Risk Distance: {old_risk} → New Risk Distance: {new_risk}
Previous R:R: {old_rr} → New R:R: {new_rr}

## OBJECTIVE CHECKS (MUST RESPECT)
- A tighter SL means lower risk distance and should NOT be described as increasing risk.
- If risk distance decreased and R:R stayed flat or improved, do not label it as a negative change.
- If the original desk suggestion explicitly advised widening SL (e.g., to avoid a liquidity sweep), do not penalize solely because risk distance increased.
- Only penalize the change when there is a clear structural reason that outweighs improved protection.

## CURRENT MARKET CONTEXT
{market_text}

## ORIGINAL TRADE THESIS (at open)
{orig_text}

## SCORING CRITERIA (OPERATOR PERSPECTIVE)
Score the UPDATED setup — re-evaluate the whole trade given the modification:
- 9-10: Textbook institutional trade management — SL tightened behind structure, BE-stop set, or profit locked in at a valid distribution level
- 7-8: Disciplined modification — structurally neutral or slight improvement, thesis intact, no new liquidity pools created in the path
- 5-6: Questionable — SL widened toward an untouched liquidity pool, R:R reduced without a structural reason, or TP moved without a valid target
- 3-4: Reactive retail behaviour — SL widened under drawdown pressure, chasing a distribution move, or modification contradicts the original thesis
- 1-2: Trapped-retail behaviour — stop removed, position sized up mid-trade, or SL placed directly inside a high-probability liquidity sweep zone

## RESPONSE FORMAT
Respond ONLY with valid JSON (no markdown, no code fences):
{{
    "score": <1-10>,
    "confidence": <0.0-1.0>,
    "summary": "<one-line operator verdict on the modification>",
    "issues": ["<issue1>", "<issue2>"],
    "strengths": ["<strength1>", "<strength2>"],
    "suggestion": "<specific operator instruction for managing this trade from here>",
    "market_alignment": "<how the modified setup aligns with current smart-money flow and original thesis>",
    "risk_assessment": "<updated risk: liquidity pools in path, R:R, SL placement relative to structure>"
}}

Call out reactive stops by name. Validate disciplined structural modifications. Stay grounded in the original thesis."""


async def analyze_trade_modified(
    trade: dict,
    new_sl: Any,
    new_tp: Any,
    original_analysis: Optional[dict] = None,
    market_context: Optional[dict] = None,
) -> TradeScore:
    """Run AI analysis on a modified (SL/TP changed) open trade.

    Preserves and references the original open-trade thesis to evaluate
    whether the modification is sound.

    Args:
        trade: Current trade data dict.
        new_sl: The updated stop loss.
        new_tp: The updated take profit.
        original_analysis: The ai_analysis dict stored when the trade was opened.
        market_context: Current live market conditions.

    Returns:
        TradeScore reflecting the updated trade setup.
    """
    metrics = _compute_modified_trade_metrics(trade, new_sl, new_tp)

    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        logger.warning("⚠️ OpenAI API key not configured — using rule-based modified-trade score")
        base_score = 5
        if metrics.get("objective_improvement"):
            base_score = 7
        elif metrics.get("wider_sl"):
            base_score = 4

        result = {
            "score": base_score,
            "confidence": 0.55,
            "summary": "Rule-based analysis for modified trade (API key not configured)",
            "issues": [] if not metrics.get("wider_sl") else ["SL widened versus entry, increasing absolute risk distance."],
            "strengths": ["Trade still has defined levels"],
            "suggestion": "Configure OpenAI API key for full AI analysis",
            "market_alignment": "Unable to assess",
            "risk_assessment": (
                f"Risk distance: {metrics.get('old_risk')} → {metrics.get('new_risk')}; "
                f"R:R: {metrics.get('old_rr')} → {metrics.get('new_rr')}"
            ),
        }
        result = _apply_modified_trade_consistency_guard(result, metrics, original_analysis)
        return TradeScore(
            score=result.get("score", base_score),
            confidence=result.get("confidence", 0.55),
            summary=result.get("summary", "Analysis unavailable"),
            issues=result.get("issues", []),
            strengths=result.get("strengths", []),
            suggestion=result.get("suggestion", "No suggestion available"),
            market_alignment=result.get("market_alignment", "Unknown"),
            risk_assessment=result.get("risk_assessment", "Unknown"),
        )

    prompt = _build_modified_trade_prompt(trade, new_sl, new_tp, original_analysis, market_context)

    token_usage: Optional[Dict[str, int]] = None
    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": OPERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_completion_tokens=1000,
        )
        token_usage = _extract_token_usage(getattr(response, "usage", None))
        result = _parse_json_response(response.choices[0].message.content or "{}")
    except Exception as e:
        logger.error(f"OpenAI API error in modified-trade analysis: {e}")
        result = {
            "score": 5,
            "confidence": 0.3,
            "summary": "AI analysis unavailable for modification — review manually.",
            "issues": [],
            "strengths": [],
            "suggestion": "AI service temporarily unavailable. Verify modification aligns with your original plan.",
            "market_alignment": "Unable to assess — AI unavailable",
            "risk_assessment": f"Updated SL={new_sl}, TP={new_tp}",
        }

    result = _apply_modified_trade_consistency_guard(result, metrics, original_analysis)

    return TradeScore(
        score=result.get("score", 5),
        confidence=result.get("confidence", 0.5),
        summary=result.get("summary", "Analysis unavailable"),
        issues=result.get("issues", []),
        strengths=result.get("strengths", []),
        suggestion=result.get("suggestion", "No suggestion available"),
        market_alignment=result.get("market_alignment", "Unknown"),
        risk_assessment=result.get("risk_assessment", "Unknown"),
        token_usage=token_usage,
    )


async def analyze_post_trade(
    trade: dict,
    pre_score: Optional[dict] = None,
) -> TradeReview:
    """Run post-trade AI review using OpenAI for deeper analysis.

    Args:
        trade: Completed trade data.
        pre_score: Pre-trade analysis result if available.

    Returns:
        TradeReview with execution score, lessons, and emotional assessment.
    """
    # Check if API key is configured
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        logger.warning("⚠️ OpenAI API key not configured — using mock review")
        is_winner = (trade.get("pnl") or 0) > 0
        return TradeReview(
            execution_score=7 if is_winner else 4,
            plan_adherence=6,
            summary=f"Mock review: {'Winning' if is_winner else 'Losing'} trade (API key not configured)",
            lessons=["Configure OpenAI API key for full AI analysis"],
            what_went_well=["Trade was closed"] if is_winner else [],
            what_to_improve=["Set up OpenAI API key"],
            emotional_assessment="Unable to assess — API key not configured",
        )
    
    prompt = _build_post_trade_prompt(trade, pre_score)

    token_usage: Optional[Dict[str, int]] = None
    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional trading analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_completion_tokens=1500,
        )
        token_usage = _extract_token_usage(getattr(response, "usage", None))
        result = _parse_json_response(response.choices[0].message.content or "{}")
    except Exception as e:
        logger.error(f"OpenAI API error in post-trade review: {e}")
        is_winner = (trade.get("pnl") or 0) > 0
        result = {
            "execution_score": 5,
            "plan_adherence": 5,
            "summary": f"{'Winning' if is_winner else 'Losing'} trade — AI review unavailable.",
            "lessons": ["AI service temporarily unavailable for detailed review."],
            "what_went_well": ["Trade was closed"] if is_winner else [],
            "what_to_improve": ["Review trade manually"],
            "emotional_assessment": "Unable to assess — AI unavailable",
        }

    return TradeReview(
        execution_score=result.get("execution_score", 5),
        plan_adherence=result.get("plan_adherence", 5),
        summary=result.get("summary", "Review unavailable"),
        lessons=result.get("lessons", []),
        what_went_well=result.get("what_went_well", []),
        what_to_improve=result.get("what_to_improve", []),
        emotional_assessment=result.get("emotional_assessment", "Unknown"),
        token_usage=token_usage,
    )


async def analyze_post_trade_streaming(
    trade: dict,
    pre_score: Optional[dict] = None,
    on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
) -> TradeReview:
    """Run post-trade AI review and optionally stream partial text chunks.

    Args:
        trade: Completed trade data.
        pre_score: Pre-trade analysis result if available.
        on_chunk: Optional async callback receiving partial model text.

    Returns:
        TradeReview with execution score, lessons, and emotional assessment.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        logger.warning("⚠️ OpenAI API key not configured — using mock review")
        is_winner = (trade.get("pnl") or 0) > 0
        mock_review = TradeReview(
            execution_score=7 if is_winner else 4,
            plan_adherence=6,
            summary=f"Mock review: {'Winning' if is_winner else 'Losing'} trade (API key not configured)",
            lessons=["Configure OpenAI API key for full AI analysis"],
            what_went_well=["Trade was closed"] if is_winner else [],
            what_to_improve=["Set up OpenAI API key"],
            emotional_assessment="Unable to assess — API key not configured",
        )
        if on_chunk:
            await on_chunk(mock_review.summary)
        return mock_review

    prompt = _build_post_trade_prompt(trade, pre_score)
    collected_text = ""

    token_usage: Optional[Dict[str, int]] = None
    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        stream = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional trading analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_completion_tokens=1500,
            stream=True,
            stream_options={"include_usage": True},
        )

        async for event in stream:
            maybe_usage = _extract_token_usage(getattr(event, "usage", None))
            if maybe_usage:
                token_usage = maybe_usage
            choice = (event.choices or [None])[0]
            if not choice:
                continue
            delta = getattr(choice, "delta", None)
            chunk_text = getattr(delta, "content", None) if delta else None
            if chunk_text:
                collected_text += chunk_text
                if on_chunk:
                    await on_chunk(chunk_text)

        result = _parse_json_response(collected_text or "{}")
    except Exception as e:
        logger.error(f"OpenAI API error in post-trade streaming review: {e}")
        is_winner = (trade.get("pnl") or 0) > 0
        result = {
            "execution_score": 5,
            "plan_adherence": 5,
            "summary": f"{'Winning' if is_winner else 'Losing'} trade — AI review unavailable.",
            "lessons": ["AI service temporarily unavailable for detailed review."],
            "what_went_well": ["Trade was closed"] if is_winner else [],
            "what_to_improve": ["Review trade manually"],
            "emotional_assessment": "Unable to assess — AI unavailable",
        }

    return TradeReview(
        execution_score=result.get("execution_score", 5),
        plan_adherence=result.get("plan_adherence", 5),
        summary=result.get("summary", "Review unavailable"),
        lessons=result.get("lessons", []),
        what_went_well=result.get("what_went_well", []),
        what_to_improve=result.get("what_to_improve", []),
        emotional_assessment=result.get("emotional_assessment", "Unknown"),
        token_usage=token_usage,
    )


async def generate_weekly_report(
    user_id: str,
    trades: List[dict],
    stats: dict,
) -> WeeklyReport:
    """Generate a comprehensive weekly performance report using OpenAI.

    Args:
        user_id: User UUID string.
        trades: List of trade dicts for the week.
        stats: Aggregated weekly statistics.

    Returns:
        WeeklyReport with grades, patterns, and action items.
    """
    # Check if API key is configured
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        logger.warning("⚠️ OpenAI API key not configured — using mock weekly report")
        return WeeklyReport(
            period=stats.get("period", "N/A"),
            overall_grade="N/A",
            summary="Configure OpenAI API key for full AI analysis",
            total_trades=stats.get("total_trades", 0),
            win_rate=stats.get("win_rate", 0),
            total_pnl=stats.get("total_pnl", 0),
            total_r=stats.get("total_r", 0),
            best_trade_summary="N/A",
            worst_trade_summary="N/A",
            recurring_patterns=[],
            strengths=[],
            areas_for_improvement=[],
            action_items=["Set up OpenAI API key for weekly reports"],
            emotional_profile="Unable to assess — API key not configured",
        )
    
    prompt = _build_weekly_report_prompt(trades, stats)

    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional trading performance coach. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_completion_tokens=2000,
        )
        result = _parse_json_response(response.choices[0].message.content or "{}")
    except Exception as e:
        logger.error(f"OpenAI API error in weekly report: {e}")
        result = {
            "period": stats.get("period", "N/A"),
            "overall_grade": "N/A",
            "summary": "Weekly report generation failed — AI service unavailable.",
            "total_trades": stats.get("total_trades", 0),
            "win_rate": stats.get("win_rate", 0),
            "total_pnl": stats.get("total_pnl", 0),
            "total_r": stats.get("total_r", 0),
            "best_trade_summary": "Unavailable",
            "worst_trade_summary": "Unavailable",
            "recurring_patterns": [],
            "strengths": [],
            "areas_for_improvement": [],
            "action_items": ["Manually review your trades this week"],
            "emotional_profile": "Unable to assess",
        }

    return WeeklyReport(
        period=result.get("period", stats.get("period", "N/A")),
        overall_grade=result.get("overall_grade", "N/A"),
        summary=result.get("summary", "Report unavailable"),
        total_trades=result.get("total_trades", 0),
        win_rate=result.get("win_rate", 0),
        total_pnl=result.get("total_pnl", 0),
        total_r=result.get("total_r", 0),
        best_trade_summary=result.get("best_trade_summary", "N/A"),
        worst_trade_summary=result.get("worst_trade_summary", "N/A"),
        recurring_patterns=result.get("recurring_patterns", []),
        strengths=result.get("strengths", []),
        areas_for_improvement=result.get("areas_for_improvement", []),
        action_items=result.get("action_items", []),
        emotional_profile=result.get("emotional_profile", "N/A"),
    )
