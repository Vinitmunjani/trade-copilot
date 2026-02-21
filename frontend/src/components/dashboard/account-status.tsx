"use client";

import React, { useEffect } from "react";
import { useSettingsStore } from "@/stores/settings-store";
import { Card } from "@/components/ui/card";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

export function AccountStatus() {
  const { tradingAccount, brokerConnected, fetchAccountInfo } = useSettingsStore();

  useEffect(() => {
    fetchAccountInfo();
  }, [fetchAccountInfo]);

  if (!brokerConnected || !tradingAccount) {
    return (
      <Card className="p-6 border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-amber-500" />
          <div>
            <p className="text-sm font-medium text-slate-300">No Account Connected</p>
            <p className="text-xs text-slate-500">Go to Settings to connect a broker account</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 border-slate-800 bg-slate-900/50">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            <h3 className="text-sm font-semibold text-slate-100">Trading Account</h3>
          </div>
          <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Connected
          </span>
        </div>

        {/* Account Details */}
        <div className="grid grid-cols-2 gap-4">
          {/* Broker */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wide">Broker</p>
            <p className="text-sm font-medium text-slate-100 mt-1">
              {tradingAccount.platform || "Unknown"}
            </p>
          </div>

          {/* Login */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wide">Account Login</p>
            <p className="text-sm font-medium text-slate-100 mt-1 font-mono">
              {tradingAccount.login || "N/A"}
            </p>
          </div>

          {/* Server */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wide">Server</p>
            <p className="text-sm font-medium text-slate-100 mt-1">
              {tradingAccount.server || "N/A"}
            </p>
          </div>

          {/* Status */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wide">Status</p>
            <p className="text-sm font-medium text-emerald-400 mt-1">
              {tradingAccount.connection_status || "Connected"}
            </p>
          </div>
        </div>

        {/* Message */}
        {tradingAccount.message && (
          <div className="pt-2 border-t border-slate-800">
            <p className="text-xs text-slate-400">{tradingAccount.message}</p>
          </div>
        )}
      </div>
    </Card>
  );
}
