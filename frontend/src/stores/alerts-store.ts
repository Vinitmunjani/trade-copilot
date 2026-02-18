import { create } from "zustand";
import api from "@/lib/api";
import type { BehavioralAlert } from "@/types";

interface AlertsState {
  alerts: BehavioralAlert[];
  unreadCount: number;
  isLoading: boolean;

  fetchAlerts: () => Promise<void>;
  addAlert: (alert: BehavioralAlert) => void;
  acknowledgeAlert: (id: string) => void;
  clearAll: () => void;
}

const mockAlerts: BehavioralAlert[] = [
  {
    id: "a1",
    trade_id: "t2",
    pattern_type: "fomo_entry",
    message: "Possible FOMO entry on GBPJPY — entered after 40-pip move without pullback",
    severity: "medium",
    created_at: new Date(Date.now() - 1800000).toISOString(),
    acknowledged: false,
  },
  {
    id: "a2",
    trade_id: null,
    pattern_type: "overtrading",
    message: "4 trades opened today — approaching daily limit of 5",
    severity: "low",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    acknowledged: false,
  },
  {
    id: "a3",
    trade_id: "t4",
    pattern_type: "revenge_trading",
    message: "Quick re-entry after USDJPY loss — possible revenge trade",
    severity: "high",
    created_at: new Date(Date.now() - 7200000).toISOString(),
    acknowledged: true,
  },
  {
    id: "a4",
    trade_id: "t6",
    pattern_type: "early_exit",
    message: "GBPUSD closed 25 pips before target — pattern detected 3 times this week",
    severity: "low",
    created_at: new Date(Date.now() - 86400000).toISOString(),
    acknowledged: true,
  },
  {
    id: "a5",
    trade_id: null,
    pattern_type: "session_violation",
    message: "Trade opened during Tokyo session — outside your preferred sessions",
    severity: "medium",
    created_at: new Date(Date.now() - 100000000).toISOString(),
    acknowledged: true,
  },
];

export const useAlertsStore = create<AlertsState>((set) => ({
  alerts: mockAlerts,
  unreadCount: mockAlerts.filter((a) => !a.acknowledged).length,
  isLoading: false,

  fetchAlerts: async () => {
    set({ isLoading: true });
    try {
      const { data } = await api.get("/alerts");
      set({ alerts: data, unreadCount: data.filter((a: BehavioralAlert) => !a.acknowledged).length, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  addAlert: (alert: BehavioralAlert) => {
    set((s) => ({
      alerts: [alert, ...s.alerts],
      unreadCount: s.unreadCount + (alert.acknowledged ? 0 : 1),
    }));
  },

  acknowledgeAlert: (id: string) => {
    set((s) => ({
      alerts: s.alerts.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)),
      unreadCount: Math.max(0, s.unreadCount - 1),
    }));
  },

  clearAll: () => {
    set((s) => ({
      alerts: s.alerts.map((a) => ({ ...a, acknowledged: true })),
      unreadCount: 0,
    }));
  },
}));
