"use client";

import React, { useEffect, useState } from "react";
import { useSettingsStore } from "@/stores/settings-store";
import { Card } from "@/components/ui/card";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

/** Map raw broker/MetaAPI status strings to human-readable copy. */
function sanitizeMessage(msg: string | null | undefined): string | null {
  if (!msg) return null;
  const map: Record<string, string> = {
    already_connected: "Session active",
    connected: "Connected",
    connecting: "Connecting…",
    disconnected: "Disconnected",
    reconnecting: "Reconnecting…",
    synchronizing: "Synchronising…",
  };
  return map[msg.toLowerCase()] ?? (msg.toLowerCase() === msg ? null : msg);
}

export function AccountStatus() {
  const { tradingAccount, brokerConnected, fetchAccountInfo } = useSettingsStore();
  const [loading, setLoading] = useState(false);
  const [hasInitialized, setHasInitialized] = useState(false);

  useEffect(() => {
    // Only fetch if we don't have account data yet
    if (!hasInitialized && !tradingAccount) {
      console.log("📲 AccountStatus: No cached account data, fetching...");
      setLoading(true);
      fetchAccountInfo()
        .then(() => {
          console.log("✅ Account info fetched");
          setHasInitialized(true);
          setLoading(false);
        })
        .catch((err) => {
          console.error("❌ Failed to fetch account info:", err);
          setHasInitialized(true);
          setLoading(false);
        });
    } else if (tradingAccount) {
      console.log("✅ AccountStatus: Using cached account data");
      setHasInitialized(true);
      setLoading(false);
    }
  }, []);

  if (loading) {
    return (
      <Card className="border-white/5">
        <div className="flex items-center gap-3 p-6">
          <Loader2 className="h-5 w-5 animate-spin text-accent" />
          <p className="text-sm font-medium text-foreground">Loading account...</p>
        </div>
      </Card>
    );
  }

  if (!tradingAccount || !tradingAccount.login) {
    return (
      <Card className="border-white/5">
        <div className="flex items-center gap-3 p-6">
          <AlertCircle className="h-5 w-5 text-amber-300" />
          <div>
            <p className="text-sm font-medium text-foreground">No Account Connected</p>
            <p className="text-xs text-muted">Go to Settings to connect a broker account</p>
          </div>
        </div>
      </Card>
    );
  }

  const humanMessage = sanitizeMessage(tradingAccount.message);

  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 rounded-2xl border border-white/5 bg-white/[0.03] px-5 py-3">
      {/* Label */}
      <div className="flex items-center gap-2 shrink-0">
        <CheckCircle2 className="h-4 w-4 text-accent" />
        <span className="text-xs font-semibold uppercase tracking-[0.25em] text-foreground/90">Trading Account</span>
      </div>

      <div className="h-4 w-px bg-white/10 shrink-0 hidden sm:block" />

      {/* Broker */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] uppercase tracking-[0.3em] text-muted">Broker</span>
        <span className="text-xs font-medium text-foreground">{tradingAccount.platform || "—"}</span>
      </div>

      {/* Server */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] uppercase tracking-[0.3em] text-muted">Server</span>
        <span className="text-xs font-medium text-foreground">{tradingAccount.server || "—"}</span>
      </div>

      {/* Login */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] uppercase tracking-[0.3em] text-muted">Login</span>
        <span className="font-mono text-xs font-medium text-foreground">{tradingAccount.login || "—"}</span>
      </div>

      {/* Optional sanitized message */}
      {humanMessage && (
        <span className="text-[11px] text-muted hidden md:inline">{humanMessage}</span>
      )}

      {/* Status badge — pushed to the right */}
      <div className="ml-auto shrink-0">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium",
            tradingAccount.connected
              ? "border-accent/30 bg-accent/10 text-accent"
              : "border-amber-400/30 bg-amber-500/10 text-amber-300"
          )}
        >
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              tradingAccount.connected ? "bg-accent" : "bg-amber-400"
            )}
          />
          {tradingAccount.connected ? "Connected" : "Linked"}
        </span>
      </div>
    </div>
  );
}
