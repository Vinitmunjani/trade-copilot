// HTTP proxy endpoint (on OpenClaw server port 8080)
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://10.10.10.8:8080";
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://10.10.10.8:8080/ws/trades";

export const SESSIONS = [
  { value: "london", label: "London", hours: "08:00-16:00 GMT" },
  { value: "new_york", label: "New York", hours: "13:00-21:00 GMT" },
  { value: "tokyo", label: "Tokyo", hours: "00:00-08:00 GMT" },
  { value: "sydney", label: "Sydney", hours: "22:00-06:00 GMT" },
] as const;

export const SYMBOLS = [
  "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
  "EURGBP", "EURJPY", "GBPJPY", "XAUUSD", "XAGUSD", "US30", "NAS100", "SPX500",
] as const;

export const TIMEZONES = [
  "UTC", "America/New_York", "America/Chicago", "America/Los_Angeles",
  "Europe/London", "Europe/Berlin", "Europe/Paris", "Asia/Tokyo",
  "Asia/Shanghai", "Asia/Singapore", "Australia/Sydney",
] as const;

export const CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF"] as const;

export const PATTERN_LABELS: Record<string, string> = {
  revenge_trading: "Revenge Trading",
  overtrading: "Overtrading",
  fomo_entry: "FOMO Entry",
  early_exit: "Early Exit",
  moved_stop_loss: "Moved Stop Loss",
  ignored_rules: "Ignored Rules",
  session_violation: "Session Violation",
  size_violation: "Size Violation",
  emotional_trading: "Emotional Trading",
  chasing_losses: "Chasing Losses",
};

export const PATTERN_ICONS: Record<string, string> = {
  revenge_trading: "Swords",
  overtrading: "Repeat",
  fomo_entry: "Zap",
  early_exit: "LogOut",
  moved_stop_loss: "MoveHorizontal",
  ignored_rules: "ShieldOff",
  session_violation: "Clock",
  size_violation: "Scale",
  emotional_trading: "Heart",
  chasing_losses: "TrendingDown",
};
