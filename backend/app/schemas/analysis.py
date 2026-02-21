from typing import List, Dict,  Optional, Union
"""Pydantic schemas for AI analysis responses."""

from pydantic import BaseModel, Field


class TradeScore(BaseModel):
    """Pre-trade AI analysis score."""
    score: int = Field(..., ge=1, le=10, description="Trade quality score 1-10")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the score")
    summary: str = Field(..., description="One-line summary")
    issues: List[str] = Field(default_factory=list, description="List of identified issues")
    strengths: List[str] = Field(default_factory=list, description="List of trade strengths")
    suggestion: str = Field(..., description="Actionable suggestion for the trader")
    market_alignment: str = Field(..., description="How trade aligns with market context")
    risk_assessment: str = Field(..., description="Risk assessment summary")


class TradeReview(BaseModel):
    """Post-trade AI review."""
    execution_score: int = Field(..., ge=1, le=10, description="How well the trade was executed")
    plan_adherence: int = Field(..., ge=1, le=10, description="How well trader followed their plan")
    summary: str = Field(..., description="Post-trade summary")
    lessons: List[str] = Field(default_factory=list, description="Lessons from this trade")
    what_went_well: List[str] = Field(default_factory=list)
    what_to_improve: List[str] = Field(default_factory=list)
    emotional_assessment: str = Field(..., description="Assessment of emotional state during trade")


class BehavioralAlert(BaseModel):
    """Behavioral pattern alert."""
    flag: str = Field(..., description="Flag identifier")
    severity: str = Field(..., description="low, medium, high, critical")
    message: str = Field(..., description="Human-readable alert message")
    details: Optional[dict] = None


class WeeklyReport(BaseModel):
    """Weekly AI-generated performance report."""
    period: str
    overall_grade: str = Field(..., description="A+ to F grade")
    summary: str
    total_trades: int
    win_rate: float
    total_pnl: float
    total_r: float
    best_trade_summary: str
    worst_trade_summary: str
    recurring_patterns: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]
    action_items: List[str]
    emotional_profile: str


class PatternAnalysis(BaseModel):
    """Trading pattern analysis."""
    pattern: str
    frequency: int
    description: str
    impact: str  # positive, negative, neutral
    recommendation: str


class PatternsResponse(BaseModel):
    """Response for pattern analysis endpoint."""
    patterns: List[PatternAnalysis]
    analysis_period_days: int
    total_trades_analyzed: int
