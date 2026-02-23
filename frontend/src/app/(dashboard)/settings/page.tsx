"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
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
  KeyRound
} from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuthStore();
  const { 
    brokerConnected, 
    tradingAccount, 
    isConnecting, 
    connectBroker, 
    disconnectBroker, 
    fetchAccountInfo 
  } = useSettingsStore();

  const [loginInput, setLoginInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [serverInput, setServerInput] = useState("");
  const [platformInput, setPlatformInput] = useState("Exness");
  const [connectionError, setConnectionError] = useState("");

  // Fetch account info on mount
  useEffect(() => {
    fetchAccountInfo();
  }, [fetchAccountInfo]);

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
        platform: platformInput,
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
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wifi className="h-5 w-5" />
            Trading Account Connection
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Status */}
          <div className="flex items-center justify-between p-4 rounded-lg border border-slate-800 bg-slate-800/50">
            <div className="flex items-center gap-3">
              {brokerConnected ? (
                <>
                  <CheckCircle className="h-5 w-5 text-emerald-400" />
                  <div>
                    <p className="text-sm font-medium text-slate-200">Account Connected</p>
                    <p className="text-xs text-slate-400">Real-time sync enabled</p>
                  </div>
                </>
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
            {brokerConnected && (
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
          {brokerConnected && tradingAccount && (
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
                <span className="text-emerald-400 font-medium">
                  ✓ {tradingAccount.connection_status || "connected"}
                </span>
              </div>
            </div>
          )}

          {/* Connection Form */}
          {!brokerConnected && (
            <>
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
              <div className="p-3 rounded-lg bg-slate-800/30 text-xs text-slate-400 space-y-2">
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
    </div>
  );
}
