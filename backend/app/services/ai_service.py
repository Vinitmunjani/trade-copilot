"""AI analysis service.
from typing import List, Dict,  Optional, Union

Provides pre-trade scoring, post-trade review, and weekly report generation
using GPT-4o-mini for all analyses.
"""

import json
import logging
from typing import List, Dict,  Optional, Any

import openai

from app.config import get_settings
from app.schemas.analysis import TradeScore, TradeReview, WeeklyReport

logger = logging.getLogger(__name__)
settings = get_settings()


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
        market_text = f"""
Current Price: {market_context.get('current_price', 'N/A')}
Trend (EMA20): {market_context.get('ema20_trend', 'N/A')}
Trend (EMA50): {market_context.get('ema50_trend', 'N/A')}
Trend (EMA200): {market_context.get('ema200_trend', 'N/A')}
ATR(14): {market_context.get('atr', 'N/A')}
Key Support: {market_context.get('support_levels', 'N/A')}
Key Resistance: {market_context.get('resistance_levels', 'N/A')}
Session: {market_context.get('session', 'N/A')}
Daily Range Used: {market_context.get('daily_range_percent', 'N/A')}%"""
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

    return f"""You are an expert trading analyst AI co-pilot. Analyze this trade setup and provide a quality score from 1-10.

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

## TRADER HISTORY
{history_text}

## BEHAVIORAL FLAGS
{flags_text}

## OTHER OPEN POSITIONS (PORTFOLIO CONTEXT)
{positions_text}

## SCORING CRITERIA
- 9-10: Excellent setup — strong trend alignment, good R:R, clean levels, no flags
- 7-8: Good setup — mostly aligned, minor concerns
- 5-6: Mediocre — some alignment issues or missing context
- 3-4: Poor — trading against trend, bad R:R, behavioral flags, or adding to already over-exposed positions
- 1-2: Terrible — multiple red flags, high probability of loss (e.g. 3+ correlated same-direction trades with no hedging)

## RESPONSE FORMAT
Respond ONLY with valid JSON (no markdown, no code fences):
{{
    "score": <1-10>,
    "confidence": <0.0-1.0>,
    "summary": "<one-line summary>",
    "issues": ["<issue1>", "<issue2>"],
    "strengths": ["<strength1>", "<strength2>"],
    "suggestion": "<specific actionable suggestion>",
    "market_alignment": "<how trade aligns with current market structure>",
    "risk_assessment": "<risk assessment including position sizing>"
}}

Be honest and direct. A mediocre trade should get a mediocre score. Don't sugarcoat."""


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


async def analyze_pre_trade(
    trade: dict,
    market_context: Optional[dict] = None,
    user_history: Optional[dict] = None,
    behavioral_flags: Optional[List[dict]] = None,
    open_positions: Optional[List[dict]] = None,
) -> TradeScore:
    """Run pre-trade AI analysis and return a quality score.

    Uses GPT-4o-mini for quick scoring to minimize latency on trade open.

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

    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional trading analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
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
        market_text = f"""
Current Price: {market_context.get('current_price', 'N/A')}
Trend (EMA20): {market_context.get('ema20_trend', 'N/A')}
Trend (EMA50): {market_context.get('ema50_trend', 'N/A')}
Trend (EMA200): {market_context.get('ema200_trend', 'N/A')}
ATR(14): {market_context.get('atr', 'N/A')}
Key Support: {market_context.get('support_levels', 'N/A')}
Key Resistance: {market_context.get('resistance_levels', 'N/A')}
Session: {market_context.get('session', 'N/A')}
Daily Range Used: {market_context.get('daily_range_percent', 'N/A')}%"""
    else:
        market_text = "  Market context unavailable — evaluate based on original thesis"

    old_sl = trade.get('sl')
    old_tp = trade.get('tp')
    entry = trade.get('entry_price', 0)

    old_rr = "N/A"
    new_rr = "N/A"
    if old_sl and old_tp and entry:
        risk = abs(entry - old_sl)
        reward = abs(old_tp - entry)
        if risk > 0:
            old_rr = round(reward / risk, 2)
    if new_sl and new_tp and entry:
        risk = abs(entry - new_sl)
        reward = abs(new_tp - entry)
        if risk > 0:
            new_rr = round(reward / risk, 2)

    return f"""You are an expert trading analyst AI co-pilot. A trader has MODIFIED an open trade. \
Evaluate whether this modification is sound, using the original trade thesis and current market context.

## OPEN TRADE
Symbol: {trade.get('symbol', 'N/A')}
Direction: {trade.get('direction', 'N/A')}
Entry Price: {entry}

## MODIFICATION
Previous Stop Loss: {old_sl} → New Stop Loss: {new_sl}
Previous Take Profit: {old_tp} → New Take Profit: {new_tp}
Previous R:R: {old_rr} → New R:R: {new_rr}

## CURRENT MARKET CONTEXT
{market_text}

## ORIGINAL TRADE THESIS (at open)
{orig_text}

## SCORING CRITERIA
Score the UPDATED setup (re-evaluate the whole trade given the change):
- 9-10: Modification improves the setup — tighter SL, better R:R, or locking in profit
- 7-8: Good modification — neutral to slightly better
- 5-6: Questionable change — widening SL, reducing R:R without clear reason
- 3-4: Poor modification — moving SL against trade logic, chasing loss
- 1-2: Dangerous modification — removing SL, gambling behaviour

## RESPONSE FORMAT
Respond ONLY with valid JSON (no markdown, no code fences):
{{
    "score": <1-10>,
    "confidence": <0.0-1.0>,
    "summary": "<one-line summary of the modification quality>",
    "issues": ["<issue1>", "<issue2>"],
    "strengths": ["<strength1>", "<strength2>"],
    "suggestion": "<specific actionable suggestion>",
    "market_alignment": "<how the modified setup aligns with current market structure and original thesis>",
    "risk_assessment": "<updated risk assessment after modification>"
}}

Stay grounded in the original thesis. If market context is unavailable, rely on the entry thesis. Praise modifications that honour the original plan and flag those that deviate."""


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
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        logger.warning("⚠️ OpenAI API key not configured — using mock modified-trade score")
        return TradeScore(
            score=5,
            confidence=0.5,
            summary="Mock analysis for modified trade (API key not configured)",
            issues=[],
            strengths=["Trade still has defined levels"],
            suggestion="Configure OpenAI API key for full AI analysis",
            market_alignment="Unable to assess",
            risk_assessment=f"Updated SL={new_sl}, TP={new_tp}",
        )

    prompt = _build_modified_trade_prompt(trade, new_sl, new_tp, original_analysis, market_context)

    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional trading analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
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

    return TradeScore(
        score=result.get("score", 5),
        confidence=result.get("confidence", 0.5),
        summary=result.get("summary", "Analysis unavailable"),
        issues=result.get("issues", []),
        strengths=result.get("strengths", []),
        suggestion=result.get("suggestion", "No suggestion available"),
        market_alignment=result.get("market_alignment", "Unknown"),
        risk_assessment=result.get("risk_assessment", "Unknown"),
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

    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional trading analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
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
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional trading performance coach. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
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
