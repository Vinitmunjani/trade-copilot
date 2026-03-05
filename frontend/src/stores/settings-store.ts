import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "@/lib/api";
import type { TradingRules, ChecklistItem, TradingAccount } from "@/types";

interface BackendRulesResponse {
  max_risk_percent: number;
  min_risk_reward: number;
  max_trades_per_day: number;
  max_daily_loss_percent: number;
  blocked_sessions: string[];
  custom_checklist: string[];
}

interface ConnectBrokerParams {
  login: string;
  password: string;
  server: string;
  platform: string;
  broker: string;
}

interface SettingsState {
  rules: TradingRules;
  brokerConnected: boolean;
  tradingAccount: TradingAccount | null;
  isConnecting: boolean;
  isSaving: boolean;
  // debug information only used in development
  streamingLogs: Record<string, string[]>;

  fetchRules: () => Promise<void>;
  updateRules: (rules: Partial<TradingRules>) => Promise<void>;
  connectBroker: (params: ConnectBrokerParams) => Promise<void>;
  disconnectBroker: () => Promise<void>;
  fetchAccountInfo: () => Promise<void>;
  fetchAccounts?: () => Promise<any[]>;
  selectAccount?: (accountId: string) => Promise<any>;
  removeAccount?: (accountId: string) => Promise<void>;
  fetchStreamingLogs?: (userId: string) => Promise<void>;
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

function mapChecklistFromBackend(
  labels: string[] = [],
  existingChecklist: ChecklistItem[] = []
): ChecklistItem[] {
  return labels.map((label, index) => {
    const existing = existingChecklist.find((item) => item.label === label);
    const positional = existingChecklist[index];
    return {
      id: existing?.id || positional?.id || `c${Date.now()}-${index}`,
      label,
      required: existing?.required ?? positional?.required ?? true,
      order: index + 1,
    };
  });
}

function mapRulesFromBackend(
  data: BackendRulesResponse,
  existingChecklist: ChecklistItem[] = []
): TradingRules {
  return {
    max_risk_percent: data.max_risk_percent,
    min_risk_reward: data.min_risk_reward,
    max_trades_per_day: data.max_trades_per_day,
    max_loss_per_day: data.max_daily_loss_percent,
    blocked_sessions: (data.blocked_sessions || []) as TradingRules["blocked_sessions"],
    checklist: mapChecklistFromBackend(data.custom_checklist || [], existingChecklist),
  };
}

function mapRulesToBackend(rules: TradingRules) {
  return {
    max_risk_percent: rules.max_risk_percent,
    min_risk_reward: rules.min_risk_reward,
    max_trades_per_day: rules.max_trades_per_day,
    max_daily_loss_percent: rules.max_loss_per_day,
    blocked_sessions: rules.blocked_sessions,
    custom_checklist: (rules.checklist || [])
      .sort((a, b) => a.order - b.order)
      .map((item) => item.label)
      .filter((label) => label && label.trim().length > 0),
  };
}

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
          const { data } = await api.get<BackendRulesResponse>("/rules");
          set((state) => ({
            rules: mapRulesFromBackend(data, state.rules.checklist),
          }));
        } catch {
          // Use defaults
        }
      },

      updateRules: async (rules: Partial<TradingRules>) => {
        const mergedRules: TradingRules = {
          ...get().rules,
          ...rules,
        };

        set({ isSaving: true, rules: mergedRules });
        try {
          const payload = mapRulesToBackend(mergedRules);
          const { data } = await api.put<BackendRulesResponse>("/rules", payload);
          set((state) => ({
            rules: mapRulesFromBackend(data, state.rules.checklist),
            isSaving: false,
          }));
        } catch (err) {
          console.error("Failed to save rules", err);
          set({ isSaving: false });
          throw err;
        }
      },

      streamingLogs: {},
      fetchStreamingLogs: async (userId: string) => {
        try {
          const { data } = await api.get("/dev/trader-data", {
            params: { user_id: userId },
          });
          const connectedAccounts = Number(data?.summary?.connected_accounts || 0);
          const liveConnected = connectedAccounts > 0;

          set((state) => {
            const current = state.tradingAccount;
            return {
              streamingLogs: data.streaming_logs || {},
              brokerConnected: liveConnected,
              tradingAccount: current
                ? {
                    ...current,
                    connected: liveConnected,
                    connection_status: liveConnected ? "connected" : (current.connection_status || "linked"),
                    message: liveConnected
                      ? "Connected"
                      : (current.message || "Linked — waiting for terminal heartbeat"),
                  }
                : current,
            };
          });
        } catch (err) {
          console.error("Failed to fetch streaming logs", err);
          set({ streamingLogs: {} });
        }
      },

      connectBroker: async (params: ConnectBrokerParams) => {
        set({ isConnecting: true });
        try {
          console.log("🔌 Connecting to broker:", params.platform);

          const { data } = await api.post("/account/connect", {
            login: params.login,
            password: params.password,
            server: params.server,
            platform: params.platform.toLowerCase().includes("mt4") ? "mt4" : "mt5",
            broker: params.broker || params.platform,
          });

          console.log("📡 Backend response:", data);

          // Map backend TradingAccountResponse correctly
          const account: TradingAccount = {
            connected: data.connection_status === "connected" || data.status === "connected",
            account_id: data.id || null,
            login: data.login || params.login,
            server: data.server || params.server,
            platform: data.platform || params.platform,
            connection_status: data.connection_status || data.status || "disconnected",
            message: data.message || (data.connection_status === "connected" ? "Connected" : "Connection failed"),
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
            streamingLogs: {},
          });
          // Clear persisted state on disconnect
          localStorage.removeItem("settings-store");
        } catch {
          set({
            brokerConnected: false,
            tradingAccount: null,
            streamingLogs: {},
          });
          localStorage.removeItem("settings-store");
        }
      },

      removeAccount: async (accountId: string) => {
        try {
          await api.delete(`/account/disconnect?account_id=${encodeURIComponent(accountId)}`);
          // Refresh persisted state
          localStorage.removeItem("settings-store");
        } catch (err) {
          console.error('Failed to remove account', err);
          throw err;
        }
      },

      fetchAccountInfo: async () => {
        try {
          console.log("📥 Fetching account info from backend...");
          const { data } = await api.get("/account/info");
          console.log("📦 Account info response:", data);

          if (data && data.login) {
            // Account exists (either connected or just linked)
            const tradingAccount: TradingAccount = {
              connected: data.connected || data.connection_status === "connected",
              account_id: data.account_id || data.id || null,
              login: data.login,
              server: data.server || null,
              platform: data.platform || data.broker || null,
              connection_status: data.connection_status || "disconnected",
              message: data.message || (data.connected ? "Connected" : "Linked but not active"),
            };

            console.log("✅ Loaded account:", tradingAccount);

            // Show account if either connected OR linked
            set({
              brokerConnected: tradingAccount.connected,
              tradingAccount,
            });
          } else {
            console.log("⚠️ No account info found");
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

        fetchAccounts: async () => {
          try {
            const { data } = await api.get('/accounts');
            // data is array of MetaAccountResponse
            set({ isSaving: false });
            return data;
          } catch (err) {
            console.error('Failed to fetch accounts', err);
            return [];
          }
        },

        selectAccount: async (accountId: string) => {
          try {
            const { data } = await api.post('/account/select', { account_id: accountId });
            const account = {
              connected: data.connected,
              account_id: data.account_id,
              login: data.login,
              server: data.server,
              platform: data.platform,
              connection_status: data.connection_status,
              message: data.message,
            } as any;
            set({ tradingAccount: account, brokerConnected: account.connected });
            return account;
          } catch (err) {
            console.error('Failed to select/connect account', err);
            throw err;
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
      // persist only the basic user settings; logs are ephemeral
      partialize: (state) => ({
        rules: state.rules,
        brokerConnected: state.brokerConnected,
        tradingAccount: state.tradingAccount,
        isConnecting: state.isConnecting,
        isSaving: state.isSaving,
      }),
    }
  )
);
