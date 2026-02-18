import { create } from "zustand";
import api from "@/lib/api";
import type { TradingRules, ChecklistItem, TradingAccount } from "@/types";

interface ConnectBrokerParams {
  login: string;
  password: string;
  server: string;
  platform: string;
}

interface SettingsState {
  rules: TradingRules;
  brokerConnected: boolean;
  tradingAccount: TradingAccount | null;
  isConnecting: boolean;
  isSaving: boolean;

  fetchRules: () => Promise<void>;
  updateRules: (rules: Partial<TradingRules>) => Promise<void>;
  connectBroker: (params: ConnectBrokerParams) => Promise<void>;
  disconnectBroker: () => Promise<void>;
  fetchAccountInfo: () => Promise<void>;
  addChecklistItem: (label: string) => void;
  removeChecklistItem: (id: string) => void;
  reorderChecklist: (items: ChecklistItem[]) => void;
}

const defaultRules: TradingRules = {
  max_risk_percent: 1.0,
  min_risk_reward: 2.0,
  max_trades_per_day: 5,
  max_loss_per_day: 3.0,
  blocked_sessions: [],
  checklist: [
    { id: "c1", label: "Identified key support/resistance levels", required: true, order: 1 },
    { id: "c2", label: "Confirmed trend direction on HTF", required: true, order: 2 },
    { id: "c3", label: "Risk:Reward minimum 2:1", required: true, order: 3 },
    { id: "c4", label: "Stop loss placed at logical level", required: true, order: 4 },
    { id: "c5", label: "No major news events in next 30 min", required: false, order: 5 },
    { id: "c6", label: "Trading within preferred session", required: false, order: 6 },
  ],
};

export const useSettingsStore = create<SettingsState>((set, get) => ({
  rules: defaultRules,
  brokerConnected: false,
  tradingAccount: null,
  isConnecting: false,
  isSaving: false,

  fetchRules: async () => {
    try {
      const { data } = await api.get("/settings/rules");
      set({ rules: data });
    } catch {
      // Use defaults
    }
  },

  updateRules: async (updates: Partial<TradingRules>) => {
    set({ isSaving: true });
    const newRules = { ...get().rules, ...updates };
    try {
      await api.put("/settings/rules", newRules);
      set({ rules: newRules, isSaving: false });
    } catch {
      set({ rules: newRules, isSaving: false });
    }
  },

  connectBroker: async (params: ConnectBrokerParams) => {
    set({ isConnecting: true });
    try {
      const { data } = await api.post("/account/connect", {
        login: params.login,
        password: params.password,
        server: params.server,
        platform: params.platform,
      });
      const account: TradingAccount = data;
      set({
        brokerConnected: account.connected,
        tradingAccount: account,
        isConnecting: false,
      });
      if (!account.connected) {
        throw new Error(account.message || "Connection failed");
      }
    } catch (err: any) {
      set({ isConnecting: false });
      const message =
        err?.response?.data?.detail ||
        err?.message ||
        "Failed to connect trading account";
      throw new Error(message);
    }
  },

  disconnectBroker: async () => {
    try {
      await api.delete("/account/disconnect");
    } catch {
      // Continue with disconnect locally
    }
    set({ brokerConnected: false, tradingAccount: null });
  },

  fetchAccountInfo: async () => {
    try {
      const { data } = await api.get("/account/info");
      const account: TradingAccount = data;
      set({
        brokerConnected: account.connected,
        tradingAccount: account,
      });
    } catch {
      set({ brokerConnected: false, tradingAccount: null });
    }
  },

  addChecklistItem: (label: string) => {
    const { rules } = get();
    const newItem: ChecklistItem = {
      id: `c${Date.now()}`,
      label,
      required: false,
      order: rules.checklist.length + 1,
    };
    set({ rules: { ...rules, checklist: [...rules.checklist, newItem] } });
  },

  removeChecklistItem: (id: string) => {
    const { rules } = get();
    set({ rules: { ...rules, checklist: rules.checklist.filter((c) => c.id !== id) } });
  },

  reorderChecklist: (items: ChecklistItem[]) => {
    const { rules } = get();
    set({ rules: { ...rules, checklist: items.map((item, i) => ({ ...item, order: i + 1 })) } });
  },
}));
