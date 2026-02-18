"use client";

import React, { useState } from "react";
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
  Link as LinkIcon
} from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuthStore();
  const { brokerConnected, brokerToken, isConnecting, connectBroker, disconnectBroker } = useSettingsStore();
  const [tokenInput, setTokenInput] = useState("");
  const [connectionError, setConnectionError] = useState("");

  const handleConnectBroker = async () => {
    if (!tokenInput.trim()) {
      setConnectionError("Please enter a valid MetaAPI token");
      return;
    }

    try {
      setConnectionError("");
      await connectBroker(tokenInput.trim());
      setTokenInput("");
    } catch (error) {
      setConnectionError("Failed to connect. Please check your token and try again.");
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
              Broker Connection
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
                    {brokerConnected ? "MetaAPI integration active" : "No broker connection"}
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

            {/* Connection Form */}
            {!brokerConnected && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="token">MetaAPI Token</Label>
                  <Input
                    id="token"
                    type="password"
                    placeholder="Enter your MetaAPI token"
                    value={tokenInput}
                    onChange={(e) => setTokenInput(e.target.value)}
                    disabled={isConnecting}
                  />
                  <p className="text-xs text-slate-500">
                    Get your token from{" "}
                    <a
                      href="https://app.metaapi.cloud/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-emerald-400 hover:text-emerald-300"
                    >
                      MetaAPI Dashboard
                    </a>
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
                  disabled={isConnecting || !tokenInput.trim()}
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
                      Connect Broker
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
                Automated AI analysis
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
