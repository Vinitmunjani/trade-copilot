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
  const [platformInput, setPlatformInput] = useState("mt5");
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
        <h1 className="text-3xl font-bold text-slate-100">Settings</h1>
        <p className="text-slate-400 mt-1">
          Manage your account preferences and broker connections
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Account Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <User className="h-4 w-4 text-emerald-400" />
              Account Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                value={user?.name || ""}
                placeholder="Your name"
                disabled
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={user?.email || ""}
                placeholder="your@email.com"
                disabled
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="timezone">Timezone</Label>
              <Select defaultValue="UTC">
                <SelectTrigger>
                  <SelectValue placeholder="Select timezone" />
                </SelectTrigger>
                <SelectContent>
                  {TIMEZONES.map((tz) => (
                    <SelectItem key={tz} value={tz}>
                      {tz}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="currency">Base Currency</Label>
              <Select defaultValue="USD">
                <SelectTrigger>
                  <SelectValue placeholder="Select currency" />
                </SelectTrigger>
                <SelectContent>
                  {CURRENCIES.map((curr) => (
                    <SelectItem key={curr} value={curr}>
                      {curr}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button className="w-full mt-6">
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </Button>
          </CardContent>
        </Card>

        {/* Broker Connection */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <LinkIcon className="h-4 w-4 text-emerald-400" />
              Connect Trading Account
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Connection Status */}
            <div className="flex items-center justify-between p-4 rounded-lg bg-slate-800/50 border border-slate-700">
              <div className="flex items-center gap-3">
                {brokerConnected ? (
                  <div className="h-8 w-8 rounded-full bg-emerald-500/10 flex items-center justify-center">
                    <Wifi className="h-4 w-4 text-emerald-400" />
                  </div>
                ) : (
                  <div className="h-8 w-8 rounded-full bg-red-500/10 flex items-center justify-center">
                    <WifiOff className="h-4 w-4 text-red-400" />
                  </div>
                )}
                <div>
                  <p className="font-medium text-slate-200">
                    {brokerConnected ? "Connected" : "Not Connected"}
                  </p>
                  <p className="text-xs text-slate-400">
                    {brokerConnected && tradingAccount
                      ? `${tradingAccount.login} @ ${tradingAccount.server} (${tradingAccount.platform?.toUpperCase()})`
                      : "No trading account connected"}
                  </p>
                </div>
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
                  <span className="text-slate-400">Platform:</span>
                  <span className="text-slate-200">{tradingAccount.platform?.toUpperCase()}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <KeyRound className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="text-slate-400">Account:</span>
                  <span className="text-slate-200">{tradingAccount.login}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Server className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="text-slate-400">Server:</span>
                  <span className="text-slate-200">{tradingAccount.server}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Wifi className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="text-slate-400">Status:</span>
                  <span className="text-emerald-400 capitalize">
                    {tradingAccount.connection_status || "connected"}
                  </span>
                </div>
              </div>
            )}

            {/* Connection Form */}
            {!brokerConnected && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="mt-login">Account Number</Label>
                  <Input
                    id="mt-login"
                    type="text"
                    placeholder="e.g., 12345678"
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
                    placeholder="e.g., ICMarketsSC-Demo"
                    value={serverInput}
                    onChange={(e) => setServerInput(e.target.value)}
                    disabled={isConnecting}
                  />
                  <p className="text-xs text-slate-500">
                    The server name from your broker (check MT4/MT5 login window)
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="mt-platform">Platform</Label>
                  <Select
                    value={platformInput}
                    onValueChange={setPlatformInput}
                    disabled={isConnecting}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select platform" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="mt5">MetaTrader 5 (MT5)</SelectItem>
                      <SelectItem value="mt4">MetaTrader 4 (MT4)</SelectItem>
                    </SelectContent>
                  </Select>
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
              </>
            )}

            {/* Info */}
            <div className="p-3 rounded-lg bg-slate-800/30 text-xs text-slate-400">
              <p className="mb-2">
                <CheckCircle className="inline h-3 w-3 mr-1 text-emerald-400" />
                Real-time trade synchronization
              </p>
              <p className="mb-2">
                <CheckCircle className="inline h-3 w-3 mr-1 text-emerald-400" />
                Read-only access — no trades executed from this app
              </p>
              <p className="mb-2">
                <CheckCircle className="inline h-3 w-3 mr-1 text-emerald-400" />
                Automated AI analysis on every trade
              </p>
              <p>
                <CheckCircle className="inline h-3 w-3 mr-1 text-emerald-400" />
                Behavioral pattern detection
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trading Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Settings className="h-4 w-4 text-emerald-400" />
            Trading Preferences
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="notifications">Email Notifications</Label>
              <Select defaultValue="important">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All alerts</SelectItem>
                  <SelectItem value="important">Important only</SelectItem>
                  <SelectItem value="none">None</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="analysis">AI Analysis Frequency</Label>
              <Select defaultValue="immediate">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="immediate">Immediate</SelectItem>
                  <SelectItem value="hourly">Hourly</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="reports">Weekly Reports</Label>
              <Select defaultValue="enabled">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="enabled">Enabled</SelectItem>
                  <SelectItem value="disabled">Disabled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button className="mt-6">
            <Save className="mr-2 h-4 w-4" />
            Save Preferences
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
