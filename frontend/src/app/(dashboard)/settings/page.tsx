"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { useSettingsStore } from "@/stores/settings-store";
import { TIMEZONES, CURRENCIES } from "@/lib/constants";
import {
  Settings,
  User,
  Wifi,
  WifiOff,
  Save,
  Loader2,
  CheckCircle,
  AlertCircle,
  Link as LinkIcon,
  Monitor,
  Server,
  KeyRound,
  Sparkles,
  ShieldCheck
} from "lucide-react";

interface AutoAdjustSettingsResponse {
  enabled: boolean;
  score_threshold: number;
  mode: "close" | "modify" | "hybrid";
  symbols: string[];
}

export default function SettingsPage() {
  const { user } = useAuthStore();
  const {
    brokerConnected,
    tradingAccount,
    isConnecting,
    connectBroker,
    disconnectBroker,
    fetchAccountInfo,
    fetchAccounts,
    selectAccount,
    removeAccount,
    streamingLogs,
    fetchStreamingLogs,
  } = useSettingsStore();

  const [loginInput, setLoginInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [serverInput, setServerInput] = useState("");
  const [platformInput, setPlatformInput] = useState("Exness");
  const [mtPlatform, setMtPlatform] = useState("mt5");
  const [connectionError, setConnectionError] = useState("");
  const [hasInitialized, setHasInitialized] = useState(false);
  const [autoAdjustEnabled, setAutoAdjustEnabled] = useState(false);
  const [autoAdjustThreshold, setAutoAdjustThreshold] = useState(3);
  const [autoAdjustMode, setAutoAdjustMode] = useState<"close" | "modify" | "hybrid">("hybrid");
  const [autoAdjustSymbolsInput, setAutoAdjustSymbolsInput] = useState("");
  const [isAutoAdjustLoading, setIsAutoAdjustLoading] = useState(false);
  const [isAutoAdjustSaving, setIsAutoAdjustSaving] = useState(false);
  const [autoAdjustStatus, setAutoAdjustStatus] = useState<string | null>(null);

  // Always fetch fresh account info on page load (persisted store can be stale)
  useEffect(() => {
    if (!hasInitialized) {
      console.log("⚙️ Settings: Refreshing account data...");
      fetchAccountInfo()
        .finally(() => {
          setHasInitialized(true);
        });
    }

    // Load accounts list and streaming logs
    (async () => {
      try {
        const list = await fetchAccounts?.();
        if (list && list.length > 0 && !tradingAccount) {
          // nothing automatic for now
        }
      } catch (e) {
        // ignore
      }
    })();
    // try load streaming logs for debug when user has id
    if (user?.id) {
      fetchStreamingLogs?.(user.id);
    }
  }, [hasInitialized, fetchAccountInfo, fetchAccounts, fetchStreamingLogs, tradingAccount, user?.id]);

  // Auto-refresh streaming logs every 2 seconds when user is on this page
  useEffect(() => {
    if (!user?.id || !fetchStreamingLogs) return;

    const interval = setInterval(() => {
      fetchStreamingLogs(user.id);
    }, 2000); // Refresh every 2 seconds

    return () => clearInterval(interval);
  }, [user?.id, fetchStreamingLogs]);

  const [accounts, setAccounts] = useState<any[]>([]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const list = await fetchAccounts?.();
        if (mounted && list) setAccounts(list);
      } catch (e) {
        console.error('Failed to load accounts', e);
      }
    })();
    return () => { mounted = false; };
  }, [fetchAccounts]);

  useEffect(() => {
    let mounted = true;
    const loadAutoAdjust = async () => {
      try {
        setIsAutoAdjustLoading(true);
        const { data } = await api.get<AutoAdjustSettingsResponse>("/account/auto-adjust-settings");
        if (!mounted) return;
        setAutoAdjustEnabled(Boolean(data.enabled));
        setAutoAdjustThreshold(Number(data.score_threshold || 3));
        setAutoAdjustMode((data.mode || "hybrid") as "close" | "modify" | "hybrid");
        setAutoAdjustSymbolsInput((data.symbols || []).join(", "));
      } catch (err) {
        console.error("Failed to load auto-adjust settings", err);
      } finally {
        if (mounted) setIsAutoAdjustLoading(false);
      }
    };

    loadAutoAdjust();
    return () => {
      mounted = false;
    };
  }, []);

  const handleConnectBroker = async () => {
    if (!loginInput.trim()) {
      setConnectionError("Please enter your MT4/MT5 account number");
      return;
    }
    if (!passwordInput.trim()) {
      setConnectionError("Please enter your MT4/MT5 password");
      return;
    }
    if (!serverInput.trim()) {
      setConnectionError("Please enter your broker server name");
      return;
    }

    try {
      setConnectionError("");
      await connectBroker({
        login: loginInput.trim(),
        password: passwordInput.trim(),
        server: serverInput.trim(),
        platform: mtPlatform,
        broker: platformInput,
      });
      // Clear form on success (especially password)
      setLoginInput("");
      setPasswordInput("");
      setServerInput("");
    } catch (error: any) {
      setConnectionError(error?.message || "Failed to connect. Please check your credentials and try again.");
    }
  };

  const handleDisconnectBroker = async () => {
    try {
      await disconnectBroker();
    } catch (error) {
      console.error("Failed to disconnect:", error);
    }
  };

  const handleSaveAutoAdjust = async () => {
    try {
      setIsAutoAdjustSaving(true);
      setAutoAdjustStatus(null);
      const symbols = autoAdjustSymbolsInput
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean);

      const { data } = await api.put<AutoAdjustSettingsResponse>("/account/auto-adjust-settings", {
        enabled: autoAdjustEnabled,
        score_threshold: Math.max(1, Math.min(10, Number(autoAdjustThreshold) || 3)),
        mode: autoAdjustMode,
        symbols,
      });

      setAutoAdjustEnabled(Boolean(data.enabled));
      setAutoAdjustThreshold(Number(data.score_threshold || 3));
      setAutoAdjustMode((data.mode || "hybrid") as "close" | "modify" | "hybrid");
      setAutoAdjustSymbolsInput((data.symbols || []).join(", "));
      setAutoAdjustStatus("Saved");
    } catch (err) {
      console.error("Failed to save auto-adjust settings", err);
      setAutoAdjustStatus("Failed to save");
    } finally {
      setIsAutoAdjustSaving(false);
      setTimeout(() => setAutoAdjustStatus(null), 2500);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-100 flex items-center gap-2">
          <Settings className="h-8 w-8" />
          Settings
        </h1>
        <p className="text-slate-400 mt-1">Configure your trading preferences and connect your broker account</p>
      </div>

      {/* Broker Connection */}
      <Card className="border-white/5 bg-surface/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wifi className="h-5 w-5" />
            Trading Account Connection
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Status */}
          <div className="flex items-center justify-between p-4 rounded-lg border border-white/5 bg-surface-muted/50">
            <div className="flex items-center gap-3">
              {tradingAccount ? (
                tradingAccount.connected ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-emerald-400" />
                    <div>
                      <p className="text-sm font-medium text-slate-200">Account Connected</p>
                      <p className="text-xs text-slate-400">Real-time sync enabled</p>
                    </div>
                  </>
                ) : (
                  <>
                    <WifiOff className="h-5 w-5 text-amber-400" />
                    <div>
                      <p className="text-sm font-medium text-slate-200">Account Linked</p>
                      <p className="text-xs text-slate-400">Linked — waiting for terminal heartbeat</p>
                    </div>
                  </>
                )
              ) : (
                <>
                  <WifiOff className="h-5 w-5 text-slate-400" />
                  <div>
                    <p className="text-sm font-medium text-slate-200">No Account Connected</p>
                    <p className="text-xs text-slate-400">Connect your MT4/MT5 account to get started</p>
                  </div>
                </>
              )}
            </div>
            {tradingAccount && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleDisconnectBroker}
              >
                Disconnect
              </Button>
            )}
          </div>

          {/* Connected Account Details */}
          {tradingAccount && (
            <div className="space-y-2 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
              <div className="flex items-center gap-2 text-sm">
                <Monitor className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-slate-400">Broker:</span>
                <span className="text-slate-200 font-medium">{tradingAccount.platform}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <KeyRound className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-slate-400">Account:</span>
                <span className="text-slate-200 font-mono">{tradingAccount.login}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Server className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-slate-400">Server:</span>
                <span className="text-slate-200">{tradingAccount.server}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Wifi className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-slate-400">Status:</span>
                <span className={`${tradingAccount.connected ? 'text-emerald-400' : 'text-amber-400'} font-medium`}>
                  {tradingAccount.connected ? `✓ ${tradingAccount.connection_status || 'connected'}` : `${tradingAccount.connection_status || 'linked'}`}
                </span>
              </div>
            </div>
          )}

          {/* Multi-account list */}
          {accounts && accounts.length > 0 && (
            <div className="space-y-2">
              <Label>Linked Accounts</Label>
              <div className="grid gap-2">
                {accounts.map((a: any) => (
                  <div key={a.account_id} className="flex items-center justify-between p-3 rounded border border-white/5 bg-surface-muted/40">
                    <div>
                      <div className="text-sm text-slate-200 font-medium">{a.login} <span className="text-xs text-slate-400">{a.server}</span></div>
                      <div className="text-xs text-slate-400">{a.connection_status} {a.last_heartbeat ? `• ${new Date(a.last_heartbeat).toLocaleString()}` : ''}</div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="ghost" onClick={async () => {
                        try {
                          await selectAccount?.(a.account_id);
                          const list = await fetchAccounts?.();
                          setAccounts(list || []);
                        } catch (err) {
                          console.error('Select failed', err);
                        }
                      }}>{a.connection_status === 'connected' ? 'Active' : 'Connect'}</Button>
                      <Button size="sm" variant="outline" onClick={async () => {
                        try {
                          await removeAccount?.(a.account_id);
                          const list = await fetchAccounts?.();
                          setAccounts(list || []);
                        } catch (err) { console.error(err); }
                      }}>Remove</Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Connection Form */}
          {!brokerConnected && (
            <>
              <div className="space-y-2">
                <Label>Platform</Label>
                <div className="flex gap-4">
                  <Button
                    variant={mtPlatform === "mt4" ? "default" : "outline"}
                    className="flex-1"
                    onClick={() => setMtPlatform("mt4")}
                    type="button"
                  >
                    MT4
                  </Button>
                  <Button
                    variant={mtPlatform === "mt5" ? "default" : "outline"}
                    className="flex-1"
                    onClick={() => setMtPlatform("mt5")}
                    type="button"
                  >
                    MT5
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="broker-select">Broker</Label>
                <Select
                  value={platformInput}
                  onValueChange={setPlatformInput}
                  disabled={isConnecting}
                >
                  <SelectTrigger id="broker-select">
                    <SelectValue placeholder="Select broker" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Exness">Exness</SelectItem>
                    <SelectItem value="ICMarkets">IC Markets</SelectItem>
                    <SelectItem value="XM">XM</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-slate-500">
                  Select your broker from the list above
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="mt-login">Account Number</Label>
                <Input
                  id="mt-login"
                  type="text"
                  placeholder="e.g., 279495999"
                  value={loginInput}
                  onChange={(e) => setLoginInput(e.target.value)}
                  disabled={isConnecting}
                />
                <p className="text-xs text-slate-500">
                  Your MT4/MT5 trading account number
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="mt-password">Password</Label>
                <Input
                  id="mt-password"
                  type="password"
                  placeholder="Enter your MT4/MT5 password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  disabled={isConnecting}
                />
                <p className="text-xs text-slate-500">
                  Your password is used only to establish the connection and is not stored
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="mt-server">Broker Server</Label>
                <Input
                  id="mt-server"
                  type="text"
                  placeholder="e.g., Exness-MT5Trial8"
                  value={serverInput}
                  onChange={(e) => setServerInput(e.target.value)}
                  disabled={isConnecting}
                />
                <p className="text-xs text-slate-500">
                  The server name from your broker (check MT4/MT5 login window)
                </p>
              </div>

              {connectionError && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {connectionError}
                </div>
              )}

              <Button
                onClick={handleConnectBroker}
                disabled={isConnecting || !loginInput.trim() || !passwordInput.trim() || !serverInput.trim()}
                className="w-full"
              >
                {isConnecting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <LinkIcon className="mr-2 h-4 w-4" />
                    Connect Trading Account
                  </>
                )}
              </Button>

              {/* Info */}
              <div className="p-3 rounded-lg bg-surface-muted/30 text-xs text-muted space-y-2">
                <div className="flex gap-2">
                  <CheckCircle className="h-3 w-3 text-emerald-400 shrink-0 mt-0.5" />
                  <p>Real-time trade synchronization</p>
                </div>
                <div className="flex gap-2">
                  <CheckCircle className="h-3 w-3 text-emerald-400 shrink-0 mt-0.5" />
                  <p>Read-only access — no trades executed from this app</p>
                </div>
                <div className="flex gap-2">
                  <CheckCircle className="h-3 w-3 text-emerald-400 shrink-0 mt-0.5" />
                  <p>Automated AI analysis on every trade</p>
                </div>
                <div className="flex gap-2">
                  <CheckCircle className="h-3 w-3 text-emerald-400 shrink-0 mt-0.5" />
                  <p>Behavioral pattern detection</p>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Debug: streaming logs panel */}
      <Card className="border-white/5 bg-surface/40 mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            MetaAPI Streaming Logs
          </CardTitle>
        </CardHeader>
        <CardContent>
          {Object.keys(streamingLogs || {}).length > 0 ? (
            <>
              {Object.entries(streamingLogs).map(([acct, lines]) => (
                <div key={acct} className="mb-4">
                  <div className="text-sm font-medium text-slate-300 mb-1">
                    Account: {acct}
                  </div>
                  <pre className="text-xs font-mono bg-surface-muted p-2 rounded max-h-40 overflow-y-auto">
{(lines as string[]).length > 0
  ? (lines as string[]).join("\n")
  : "No logs yet for this account. Keep this page open while connected to capture stream events."}
                  </pre>
                </div>
              ))}
            </>
          ) : (
            <div className="text-sm text-slate-400 py-4">
              No logs available. Logs will appear here once your MetaAPI account connects.
            </div>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => user?.id && fetchStreamingLogs?.(user.id)}
          >
            Refresh Logs
          </Button>
        </CardContent>
      </Card>

      {/* Beta auto-adjust controls */}
      <Card className="border-white/5 bg-surface/40 mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Auto Adjust
            <Badge variant="warning" className="ml-2">Beta</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-start justify-between rounded-lg border border-white/5 bg-surface-muted/40 p-4">
            <div>
              <p className="text-sm font-medium text-slate-200">Enable AI Auto Adjust</p>
              <p className="mt-1 text-xs text-slate-400">
                If your setup quality is too low, AI can auto-adjust protection or close the trade.
              </p>
            </div>
            <Switch
              checked={autoAdjustEnabled}
              onCheckedChange={setAutoAdjustEnabled}
              disabled={isAutoAdjustLoading || isAutoAdjustSaving}
              aria-label="Enable auto adjust"
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="auto-adjust-threshold">Trigger Score (1-10)</Label>
              <Input
                id="auto-adjust-threshold"
                type="number"
                min={1}
                max={10}
                value={autoAdjustThreshold}
                onChange={(e) => setAutoAdjustThreshold(Number(e.target.value || 3))}
                disabled={!autoAdjustEnabled || isAutoAdjustLoading || isAutoAdjustSaving}
              />
              <p className="text-xs text-slate-500">Auto-adjust triggers when AI score is at or below this value.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="auto-adjust-mode">Action Mode</Label>
              <Select
                value={autoAdjustMode}
                onValueChange={(v) => setAutoAdjustMode(v as "close" | "modify" | "hybrid")}
                disabled={!autoAdjustEnabled || isAutoAdjustLoading || isAutoAdjustSaving}
              >
                <SelectTrigger id="auto-adjust-mode">
                  <SelectValue placeholder="Select mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hybrid">Hybrid (modify then close if needed)</SelectItem>
                  <SelectItem value="modify">Modify SL/TP only</SelectItem>
                  <SelectItem value="close">Close only</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="auto-adjust-symbols">Symbols (optional)</Label>
            <Input
              id="auto-adjust-symbols"
              type="text"
              placeholder="XAUUSD, EURUSD"
              value={autoAdjustSymbolsInput}
              onChange={(e) => setAutoAdjustSymbolsInput(e.target.value)}
              disabled={!autoAdjustEnabled || isAutoAdjustLoading || isAutoAdjustSaving}
            />
            <p className="text-xs text-slate-500">Leave empty to allow all symbols. Comma-separated list.</p>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <ShieldCheck className="h-3.5 w-3.5" />
              Auto-adjust only works when your trade account is connected and streaming.
            </div>
            <Button onClick={handleSaveAutoAdjust} disabled={isAutoAdjustLoading || isAutoAdjustSaving}>
              {isAutoAdjustSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Auto Adjust
                </>
              )}
            </Button>
          </div>

          {autoAdjustStatus && (
            <p className={`text-xs ${autoAdjustStatus === "Saved" ? "text-emerald-400" : "text-red-400"}`}>
              {autoAdjustStatus}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
