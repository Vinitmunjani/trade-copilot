export interface User {
  id: string;
  email: string;
  name: string;
  timezone: string;
  currency: string;
  broker_connected: boolean;
  created_at: string;
}

export interface Trade {
  id: string;
  user_id: string;
  symbol: string;
  direction: "BUY" | "SELL";
  entry_price: number;
  exit_price: number | null;
  stop_loss: number;
  take_profit: number;
  lot_size: number;
  pnl: number | null;
  pnl_r: number | null;
  status: "open" | "closed" | "cancelled";
  opened_at: string;
  closed_at: string | null;
  duration_minutes: number | null;
  session: TradingSession;
  ai_score: TradeScore | null;
  flags: BehavioralFlag[];
}

export interface TradeScore {
  score: number;
  confidence: number;
  issues: string[];
  suggestion: string;
  rule_adherence: boolean;
  checklist_completed: boolean;
}

export interface TradeReview {
  id: string;
  trade_id: string;
  score: number;
  analysis: string;
  issues: string[];
  suggestion: string;
  patterns_detected: string[];
  created_at: string;
}

export interface BehavioralPattern {
  id: string;
  user_id: string;
  pattern_type: PatternType;
  description: string;
  occurrences: number;
  avg_pnl_impact: number;
  first_detected: string;
  last_detected: string;
  severity: "low" | "medium" | "high";
}

export interface BehavioralFlag {
  type: PatternType;
  message: string;
  severity: "low" | "medium" | "high";
  detected_at: string;
}

export interface BehavioralAlert {
  id: string;
  trade_id: string | null;
  pattern_type: PatternType;
  message: string;
  severity: "low" | "medium" | "high";
  created_at: string;
  acknowledged: boolean;
}

export interface TradingRules {
  max_risk_percent: number;
  min_risk_reward: number;
  max_trades_per_day: number;
  max_loss_per_day: number;
  blocked_sessions: TradingSession[];
  checklist: ChecklistItem[];
}

export interface ChecklistItem {
  id: string;
  label: string;
  required: boolean;
  order: number;
}

export interface DailyStats {
  date: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  total_pnl: number;
  total_pnl_r: number;
  win_rate: number;
  avg_r: number;
  rule_adherence: number;
  readiness_score: number;
}

export interface WeeklyReport {
  id: string;
  user_id: string;
  week_start: string;
  week_end: string;
  summary: string;
  total_trades: number;
  total_pnl: number;
  win_rate: number;
  avg_r: number;
  patterns_detected: string[];
  top_suggestion: string;
  strengths: string[];
  weaknesses: string[];
  created_at: string;
}

export type TradingSession = "london" | "new_york" | "tokyo" | "sydney";

export type PatternType =
  | "revenge_trading"
  | "overtrading"
  | "fomo_entry"
  | "early_exit"
  | "moved_stop_loss"
  | "ignored_rules"
  | "session_violation"
  | "size_violation"
  | "emotional_trading"
  | "chasing_losses";

export type TradeDirection = "BUY" | "SELL";
export type TradeStatus = "open" | "closed" | "cancelled";

export interface WSTradeUpdate {
  type: "trade_opened" | "trade_updated" | "trade_closed";
  trade: Trade;
}

export interface WSScoreUpdate {
  type: "score_update";
  trade_id: string;
  score: TradeScore;
}

export interface WSAlertUpdate {
  type: "behavioral_alert";
  alert: BehavioralAlert;
}

export interface WSReadinessUpdate {
  type: "readiness_update";
  score: number;
}

export type WSEvent =
  | WSTradeUpdate
  | WSScoreUpdate
  | WSAlertUpdate
  | WSReadinessUpdate;

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface TradeFilters {
  date_from?: string;
  date_to?: string;
  symbol?: string[];
  direction?: TradeDirection;
  score_min?: number;
  score_max?: number;
  status?: TradeStatus;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  per_page?: number;
}

export interface EquityCurvePoint {
  date: string;
  cumulative_pnl: number;
}

export interface WinRateByCategory {
  category: string;
  win_rate: number;
  total_trades: number;
}

export interface RDistributionBucket {
  range: string;
  count: number;
  min_r: number;
  max_r: number;
}

export interface HeatmapCell {
  session: TradingSession;
  day: string;
  pnl: number;
  trades: number;
}
