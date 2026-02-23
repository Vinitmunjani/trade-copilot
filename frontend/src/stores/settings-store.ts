import { create } from "zustand";
import { persist } from "zustand/middleware";
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
  setTradingAccount: (account: TradingAccount | null) => void;
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

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
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
          console.log("🔌 Connecting to broker:", params.platform);
          
          const { data } = await api.post("/account/connect", null, {
            params: {
              broker: params.platform,
              login: params.login,
              password: params.password,
              server: params.server,
            },
          });
          
          console.log("📡 Backend response:", data);
          
          // Map broker field correctly - use data.broker (the original broker name from backend)
          const account: TradingAccount = {
            connected: data.status === "connected",
            account_id: data.id || null,
            login: data.login || params.login,
            server: data.server || params.server,
            platform: data.broker || params.platform,  // Use broker field from response
            connection_status: data.status || "disconnected",
            message: data.status === "connected" ? "Connected" : data.error || "Connection failed",
          };
          
          console.log("💾 Saving account:", account);
          
          set({
            brokerConnected: account.connected,
            tradingAccount: account,
            isConnecting: false,
          });
          
          if (!account.connected) {
            throw new Error(account.message || "Connection failed");
          }
        } catch (err: any) {
          console.error("❌ Connection error:", err);
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
          set({
            brokerConnected: false,
            tradingAccount: null,
          });
          // Clear persisted state on disconnect
          localStorage.removeItem("settings-store");
        } catch {
          set({
            brokerConnected: false,
            tradingAccount: null,
          });
          localStorage.removeItem("settings-store");
        }
      },

      fetchAccountInfo: async () => {
        try {
          console.log("📥 Fetching account info from backend...");
          const { data } = await api.get("/account/list");
          console.log("📦 Account list response:", data);
          
          if (data && data.length > 0) {
            const account = data[0];
            const tradingAccount: TradingAccount = {
              connected: account.status === "connected",
              account_id: account.id || null,
              login: account.login || null,
              server: account.server || null,
              platform: account.broker || null,  // Use broker field from backend
              connection_status: account.status || "disconnected",
              message: "Connected",
            };
            
            console.log("✅ Loaded account:", tradingAccount);
            
            set({
              brokerConnected: true,
              tradingAccount,
            });
          } else {
            console.log("⚠️ No accounts found in backend");
            set({
              brokerConnected: false,
              tradingAccount: null,
            });
          }
        } catch (err) {
          console.error("❌ Fetch account error:", err);
          set({
            brokerConnected: false,
            tradingAccount: null,
          });
        }
      },

      setTradingAccount: (account: TradingAccount | null) => {
        set({
          tradingAccount: account,
          brokerConnected: account?.connected || false,
        });
      },

      addChecklistItem: (label: string) => {
        const newItem: ChecklistItem = {
          id: Math.random().toString(36).substr(2, 9),
          label,
          required: false,
          order: (get().rules.checklist?.length || 0) + 1,
        };
        set((state) => ({
          rules: {
            ...state.rules,
            checklist: [...(state.rules.checklist || []), newItem],
          },
        }));
      },

      removeChecklistItem: (id: string) => {
        set((state) => ({
          rules: {
            ...state.rules,
            checklist: state.rules.checklist?.filter((item) => item.id !== id) || [],
          },
        }));
      },

      reorderChecklist: (items: ChecklistItem[]) => {
        set((state) => ({
          rules: {
            ...state.rules,
            checklist: items,
          },
        }));
      },
    }),
    {
      name: "settings-store",
    }
  )
);
