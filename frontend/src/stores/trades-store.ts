import { create } from "zustand";
import api from "@/lib/api";
import type { Trade, TradeFilters, TradeScore } from "@/types";

interface TradesState {
  trades: Trade[];
  openTrades: Trade[];
  selectedTrade: Trade | null;
  isLoading: boolean;
  error: string | null;
  totalTrades: number;
  currentPage: number;

  fetchTrades: (filters?: TradeFilters) => Promise<void>;
  fetchOpenTrades: () => Promise<void>;
  fetchTradeById: (id: string) => Promise<void>;
  addTrade: (trade: Trade) => void;
  updateTrade: (trade: Trade) => void;
  removeTrade: (tradeId: string) => void;
  updateTradeScore: (tradeId: string, score: TradeScore) => void;
}

// Mock data for development
const mockOpenTrades: Trade[] = [
  {
    id: "t1",
    user_id: "u1",
    symbol: "EURUSD",
    direction: "BUY",
    entry_price: 1.0892,
    exit_price: null,
    stop_loss: 1.0862,
    take_profit: 1.0952,
    lot_size: 0.5,
    pnl: 45.0,
    pnl_r: 1.5,
    status: "open",
    opened_at: new Date().toISOString(),
    closed_at: null,
    duration_minutes: null,
    session: "london",
    ai_score: { score: 8, confidence: 0.85, issues: [], suggestion: "Good setup, aligned with trend", rule_adherence: true, checklist_completed: true },
    flags: [],
  },
  {
    id: "t2",
    user_id: "u1",
    symbol: "GBPJPY",
    direction: "SELL",
    entry_price: 188.45,
    exit_price: null,
    stop_loss: 188.95,
    take_profit: 187.45,
    lot_size: 0.3,
    pnl: -12.3,
    pnl_r: -0.25,
    status: "open",
    opened_at: new Date(Date.now() - 3600000).toISOString(),
    closed_at: null,
    duration_minutes: null,
    session: "london",
    ai_score: { score: 5, confidence: 0.72, issues: ["Counter-trend entry", "Near resistance"], suggestion: "Consider tighter stop loss", rule_adherence: true, checklist_completed: false },
    flags: [{ type: "fomo_entry", message: "Entry after rapid price movement", severity: "medium", detected_at: new Date().toISOString() }],
  },
];

const mockClosedTrades: Trade[] = [
  {
    id: "t3", user_id: "u1", symbol: "XAUUSD", direction: "BUY", entry_price: 2024.5, exit_price: 2038.2, stop_loss: 2018.0, take_profit: 2040.0, lot_size: 0.2,
    pnl: 274.0, pnl_r: 2.11, status: "closed", opened_at: "2024-01-15T09:30:00Z", closed_at: "2024-01-15T14:22:00Z", duration_minutes: 292, session: "london",
    ai_score: { score: 9, confidence: 0.92, issues: [], suggestion: "Excellent trend-following trade", rule_adherence: true, checklist_completed: true }, flags: [],
  },
  {
    id: "t4", user_id: "u1", symbol: "USDJPY", direction: "SELL", entry_price: 148.32, exit_price: 148.65, stop_loss: 148.62, take_profit: 147.72, lot_size: 0.5,
    pnl: -110.0, pnl_r: -1.1, status: "closed", opened_at: "2024-01-15T06:15:00Z", closed_at: "2024-01-15T07:45:00Z", duration_minutes: 90, session: "tokyo",
    ai_score: { score: 3, confidence: 0.88, issues: ["Traded against trend", "Session violation", "Stop hit quickly"], suggestion: "Avoid counter-trend trades in Tokyo session", rule_adherence: false, checklist_completed: false },
    flags: [
      { type: "session_violation", message: "Trading outside preferred sessions", severity: "medium", detected_at: "2024-01-15T06:15:00Z" },
      { type: "revenge_trading", message: "Quick re-entry after loss", severity: "high", detected_at: "2024-01-15T06:15:00Z" },
    ],
  },
  {
    id: "t5", user_id: "u1", symbol: "EURUSD", direction: "BUY", entry_price: 1.0845, exit_price: 1.0878, stop_loss: 1.0825, take_profit: 1.0895, lot_size: 0.5,
    pnl: 165.0, pnl_r: 1.65, status: "closed", opened_at: "2024-01-14T13:00:00Z", closed_at: "2024-01-14T16:30:00Z", duration_minutes: 210, session: "new_york",
    ai_score: { score: 7, confidence: 0.8, issues: ["Slightly early entry"], suggestion: "Wait for confirmation candle close", rule_adherence: true, checklist_completed: true }, flags: [],
  },
  {
    id: "t6", user_id: "u1", symbol: "GBPUSD", direction: "SELL", entry_price: 1.2710, exit_price: 1.2685, stop_loss: 1.2740, take_profit: 1.2660, lot_size: 0.4,
    pnl: 100.0, pnl_r: 0.83, status: "closed", opened_at: "2024-01-14T08:45:00Z", closed_at: "2024-01-14T11:20:00Z", duration_minutes: 155, session: "london",
    ai_score: { score: 6, confidence: 0.75, issues: ["Early exit before TP"], suggestion: "Consider partial take profit strategy", rule_adherence: true, checklist_completed: true },
    flags: [{ type: "early_exit", message: "Closed before reaching target", severity: "low", detected_at: "2024-01-14T11:20:00Z" }],
  },
  {
    id: "t7", user_id: "u1", symbol: "NAS100", direction: "BUY", entry_price: 16820.0, exit_price: 16905.0, stop_loss: 16780.0, take_profit: 16920.0, lot_size: 0.1,
    pnl: 85.0, pnl_r: 2.13, status: "closed", opened_at: "2024-01-13T14:30:00Z", closed_at: "2024-01-13T19:00:00Z", duration_minutes: 270, session: "new_york",
    ai_score: { score: 8, confidence: 0.87, issues: [], suggestion: "Clean breakout trade", rule_adherence: true, checklist_completed: true }, flags: [],
  },
  {
    id: "t8", user_id: "u1", symbol: "XAUUSD", direction: "SELL", entry_price: 2030.0, exit_price: 2035.5, stop_loss: 2036.0, take_profit: 2020.0, lot_size: 0.3,
    pnl: -165.0, pnl_r: -0.92, status: "closed", opened_at: "2024-01-13T10:00:00Z", closed_at: "2024-01-13T10:45:00Z", duration_minutes: 45, session: "london",
    ai_score: { score: 4, confidence: 0.7, issues: ["Counter-trend", "Tight stop"], suggestion: "Give gold trades more room in London session", rule_adherence: true, checklist_completed: false },
    flags: [{ type: "overtrading", message: "5th trade of the day", severity: "medium", detected_at: "2024-01-13T10:00:00Z" }],
  },
];

export const useTradesStore = create<TradesState>((set, get) => ({
  trades: [...mockClosedTrades],
  openTrades: [...mockOpenTrades],
  selectedTrade: null,
  isLoading: false,
  error: null,
  totalTrades: mockClosedTrades.length,
  currentPage: 1,

  fetchTrades: async (filters?: TradeFilters) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get("/trades", { params: filters });
      set({ trades: data.items, totalTrades: data.total, currentPage: data.page, isLoading: false });
    } catch {
      // Fallback to mock data in dev
      set({ isLoading: false });
    }
  },

  fetchOpenTrades: async () => {
    try {
      const { data } = await api.get("/trades", { params: { status: "open" } });
      set({ openTrades: data.items });
    } catch {
      // Keep mock data
    }
  },

  fetchTradeById: async (id: string) => {
    set({ isLoading: true });
    try {
      const { data } = await api.get(`/trades/${id}`);
      set({ selectedTrade: data, isLoading: false });
    } catch {
      // Try finding in local state
      const all = [...get().trades, ...get().openTrades];
      const found = all.find((t) => t.id === id) || null;
      set({ selectedTrade: found, isLoading: false });
    }
  },

  addTrade: (trade: Trade) => {
    if (trade.status === "open") {
      set((s) => ({ openTrades: [trade, ...s.openTrades] }));
    } else {
      set((s) => ({ trades: [trade, ...s.trades] }));
    }
  },

  updateTrade: (trade: Trade) => {
    set((s) => {
      if (trade.status === "open") {
        return { openTrades: s.openTrades.map((t) => (t.id === trade.id ? trade : t)) };
      }
      // Trade closed — remove from open, add to closed
      return {
        openTrades: s.openTrades.filter((t) => t.id !== trade.id),
        trades: [trade, ...s.trades.filter((t) => t.id !== trade.id)],
      };
    });
  },

  removeTrade: (tradeId: string) => {
    set((s) => ({
      openTrades: s.openTrades.filter((t) => t.id !== tradeId),
      trades: s.trades.filter((t) => t.id !== tradeId),
    }));
  },

  updateTradeScore: (tradeId: string, score: TradeScore) => {
    set((s) => ({
      openTrades: s.openTrades.map((t) => (t.id === tradeId ? { ...t, ai_score: score } : t)),
      trades: s.trades.map((t) => (t.id === tradeId ? { ...t, ai_score: score } : t)),
    }));
  },
}));
