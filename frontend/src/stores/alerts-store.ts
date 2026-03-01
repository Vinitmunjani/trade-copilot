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

export const useAlertsStore = create<AlertsState>((set) => ({
  alerts: [],
  unreadCount: 0,
  isLoading: false,

  fetchAlerts: async () => {
    set({ isLoading: true });
    try {
      const { data } = await api.get("/analysis/alerts");
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
