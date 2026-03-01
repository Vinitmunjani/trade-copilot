import { create } from "zustand";
import api from "@/lib/api";
import type { Trade, TradeFilters, TradeScore, TradingSession } from "@/types";

function deriveSession(openTime: string | undefined | null): TradingSession {
  if (!openTime) return "london";
  const hour = new Date(openTime).getUTCHours();
  if (hour >= 0 && hour < 8) return "tokyo";
  if (hour >= 8 && hour < 13) return "london";
  if (hour >= 13 && hour < 22) return "new_york";
  return "sydney";
}

interface TradesState {
  trades: Trade[];
  openTrades: Trade[];
  selectedTrade: Trade | null;
  isLoading: boolean;
  error: string | null;
  totalTrades: number;
  currentPage: number;
  /** Incremented every time a trade closes — allows stats hooks to react. */
  statsVersion: number;

  fetchTrades: (filters?: TradeFilters) => Promise<void>;
  fetchOpenTrades: () => Promise<void>;
  fetchTradeById: (id: string) => Promise<void>;
  addTrade: (trade: Trade) => void;
  updateTrade: (trade: Trade) => void;
  patchTrade: (tradeId: string, patch: Partial<Trade>) => void;
  removeTrade: (tradeId: string) => void;
  updateTradeScore: (tradeId: string, score: TradeScore) => void;
  bumpStats: () => void;
}

export const useTradesStore = create<TradesState>((set, get) => ({
  trades: [],
  openTrades: [],
  selectedTrade: null,
  isLoading: false,
  error: null,
  totalTrades: 0,
  currentPage: 1,
  statsVersion: 0,

  fetchTrades: async (filters?: TradeFilters) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get("/trades", { params: filters });
      // Map backend response to frontend Trade format
      const mappedTrades = (data.trades || data.items || []).map((trade: any) => ({
        id: trade.id,
        user_id: trade.user_id,
        symbol: trade.symbol,
        direction: trade.direction,
        entry_price: trade.entry_price,
        exit_price: trade.exit_price,
        sl: trade.sl,
        tp: trade.tp,
        stop_loss: trade.sl,
        take_profit: trade.tp,
        lot_size: trade.lot_size,
        pnl: trade.pnl,
        pnl_r: trade.pnl_r,
        status: trade.status?.toLowerCase() || "closed",
        opened_at: trade.open_time || trade.opened_at,
        closed_at: trade.close_time || trade.closed_at,
        open_time: trade.open_time,
        close_time: trade.close_time,
        duration_minutes: trade.duration_seconds ? Math.floor(trade.duration_seconds / 60) : null,
        duration_seconds: trade.duration_seconds,
        session: deriveSession(trade.open_time || trade.opened_at),
        ai_score: trade.ai_score || null,
        ai_analysis: trade.ai_analysis || null,
        ai_review: trade.ai_review || null,
        behavioral_flags: (trade.behavioral_flags || []).map((flag: any) => ({
          type: flag.flag || flag.type || "unknown",
          message: flag.message || "",
          severity: flag.severity || "low",
          detected_at: new Date().toISOString(),
        })),
        flags: (trade.behavioral_flags || []).map((flag: any) => ({
          type: flag.flag || flag.type || "unknown",
          message: flag.message || "",
          severity: flag.severity || "low",
          detected_at: new Date().toISOString(),
        })),
      }));
      set({ trades: mappedTrades, totalTrades: data.total || mappedTrades.length, currentPage: data.page || 1, isLoading: false });
    } catch {
      // Fallback to mock data in dev
      set({ isLoading: false });
    }
  },

  fetchOpenTrades: async () => {
    try {
      const { data } = await api.get("/trades", { params: { status: "open" } });
      const mappedTrades = (data.trades || data.items || []).map((trade: any) => ({
        id: trade.id,
        user_id: trade.user_id,
        symbol: trade.symbol,
        direction: trade.direction,
        entry_price: trade.entry_price,
        exit_price: trade.exit_price,
        sl: trade.sl,
        tp: trade.tp,
        stop_loss: trade.sl,
        take_profit: trade.tp,
        lot_size: trade.lot_size,
        pnl: trade.pnl,
        pnl_r: trade.pnl_r,
        status: trade.status?.toLowerCase() || "open",
        opened_at: trade.open_time || trade.opened_at,
        closed_at: trade.close_time || trade.closed_at,
        open_time: trade.open_time,
        close_time: trade.close_time,
        duration_minutes: trade.duration_seconds ? Math.floor(trade.duration_seconds / 60) : null,
        duration_seconds: trade.duration_seconds,
        session: deriveSession(trade.open_time || trade.opened_at),
        ai_score: trade.ai_score || null,
        ai_analysis: trade.ai_analysis || null,
        ai_review: trade.ai_review || null,
        behavioral_flags: (trade.behavioral_flags || []).map((flag: any) => ({
          type: flag.flag || flag.type || "unknown",
          message: flag.message || "",
          severity: flag.severity || "low",
          detected_at: new Date().toISOString(),
        })),
        flags: (trade.behavioral_flags || []).map((flag: any) => ({
          type: flag.flag || flag.type || "unknown",
          message: flag.message || "",
          severity: flag.severity || "low",
          detected_at: new Date().toISOString(),
        })),
      }));
      set({ openTrades: mappedTrades });
    } catch {
      // Keep mock data
    }
  },

  fetchTradeById: async (id: string) => {
    set({ isLoading: true });
    try {
      const { data } = await api.get(`/trades/${id}`);
      const trade = data;
      const mappedTrade: Trade = {
        id: trade.id,
        user_id: trade.user_id,
        symbol: trade.symbol,
        direction: trade.direction,
        entry_price: trade.entry_price,
        exit_price: trade.exit_price,
        sl: trade.sl,
        tp: trade.tp,
        stop_loss: trade.sl,
        take_profit: trade.tp,
        lot_size: trade.lot_size,
        pnl: trade.pnl,
        pnl_r: trade.pnl_r,
        status: trade.status?.toLowerCase() || "closed",
        opened_at: trade.open_time || trade.opened_at,
        closed_at: trade.close_time || trade.closed_at,
        open_time: trade.open_time,
        close_time: trade.close_time,
        duration_minutes: trade.duration_seconds ? Math.floor(trade.duration_seconds / 60) : null,
        duration_seconds: trade.duration_seconds,
        session: deriveSession(trade.open_time || trade.opened_at),
        ai_score: trade.ai_score || null,
        ai_analysis: trade.ai_analysis || null,
        ai_review: trade.ai_review || null,
        behavioral_flags: (trade.behavioral_flags || []).map((flag: any) => ({
          type: flag.flag || flag.type || "unknown",
          message: flag.message || "",
          severity: flag.severity || "low",
          detected_at: new Date().toISOString(),
        })),
        flags: (trade.behavioral_flags || []).map((flag: any) => ({
          type: flag.flag || flag.type || "unknown",
          message: flag.message || "",
          severity: flag.severity || "low",
          detected_at: new Date().toISOString(),
        })),
      };
      set({ selectedTrade: mappedTrade, isLoading: false });
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

  patchTrade: (tradeId: string, patch: Partial<Trade>) => {
    set((s) => ({
      openTrades: s.openTrades.map((t) => (t.id === tradeId ? { ...t, ...patch } : t)),
      trades: s.trades.map((t) => (t.id === tradeId ? { ...t, ...patch } : t)),
      selectedTrade: s.selectedTrade?.id === tradeId ? { ...s.selectedTrade, ...patch } : s.selectedTrade,
    }));
  },

  bumpStats: () => set((s) => ({ statsVersion: s.statsVersion + 1 })),
}));
