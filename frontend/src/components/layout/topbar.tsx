"use client";

import React from "react";
import { Bell, User, LogOut, Settings, Wifi, WifiOff, Activity, AlertTriangle, CheckCircle, Info, X } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { useAlertsStore } from "@/stores/alerts-store";
import { useSettingsStore } from "@/stores/settings-store";
import { MobileNav } from "./mobile-nav";

interface TopbarProps {
  isConnected: boolean;
}

export function Topbar({ isConnected }: TopbarProps) {
  const { user, logout } = useAuthStore();
  const { alerts, unreadCount, acknowledgeAlert, clearAll } = useAlertsStore();
  const { brokerConnected } = useSettingsStore();

  const severityIcon = (severity: string) => {
    if (severity === "high") return <AlertTriangle className="h-3.5 w-3.5 text-red-400" />;
    if (severity === "medium") return <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />;
    return <Info className="h-3.5 w-3.5 text-accent" />;
  };

  const severityBg = (severity: string) => {
    if (severity === "high") return "bg-red-400/10";
    if (severity === "medium") return "bg-amber-400/10";
    return "bg-accent/10";
  };

  return (
    <header className="sticky top-0 z-40 border-b border-white/5 bg-background/80 backdrop-blur-2xl">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 lg:px-8">
        <div className="flex items-center gap-3">
          <MobileNav />
          <div className="hidden flex-col md:flex">
            <span className="text-xs uppercase tracking-[0.4em] text-foreground/50">Live environment</span>
            <span className="text-sm text-foreground/80">Alpha board — {isConnected ? "synced" : "syncing"}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${
              brokerConnected
                ? "border-white/15 bg-accent/10 text-accent"
                : "border-red-400/30 bg-red-500/10 text-red-300"
            }`}
          >
            {brokerConnected ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
            {brokerConnected ? "Broker synced" : "Broker offline"}
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="relative border border-white/10">
                <Bell className="h-4 w-4 text-foreground/70" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold leading-none text-white ring-2 ring-background">
                    {unreadCount > 9 ? "9+" : unreadCount}
                  </span>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80 border-white/10 bg-surface p-0">
              {/* Header */}
              <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
                <p className="text-sm font-medium text-foreground">Notifications</p>
                {unreadCount > 0 && (
                  <button
                    onClick={clearAll}
                    className="flex items-center gap-1 text-xs text-muted transition-colors hover:text-accent"
                  >
                    <X className="h-3 w-3" />
                    Clear all
                  </button>
                )}
              </div>

              {/* Alert list */}
              <div className="max-h-[340px] overflow-y-auto">
                {alerts.length === 0 ? (
                  <div className="flex flex-col items-center gap-2 px-4 py-10 text-center">
                    <CheckCircle className="h-8 w-8 text-accent/40" />
                    <p className="text-sm text-muted">No notifications</p>
                  </div>
                ) : (
                  alerts.map((alert) => (
                    <div
                      key={alert.id}
                      onClick={() => acknowledgeAlert(alert.id)}
                      className={cn(
                        "flex cursor-pointer gap-3 border-b border-white/5 px-4 py-3 last:border-0 transition-colors hover:bg-white/5",
                        !alert.acknowledged && "bg-accent/5"
                      )}
                    >
                      <div className={cn("mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full", severityBg(alert.severity))}>
                        {severityIcon(alert.severity)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={cn("text-sm font-medium capitalize leading-tight", !alert.acknowledged ? "text-foreground" : "text-muted")}>
                          {alert.pattern_type.replace(/_/g, " ")}
                        </p>
                        <p className="mt-0.5 text-xs text-muted leading-relaxed line-clamp-2">{alert.message}</p>
                        <p className="mt-1 text-[11px] text-muted/50">
                          {new Date(alert.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </p>
                      </div>
                      {!alert.acknowledged && (
                        <div className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                      )}
                    </div>
                  ))
                )}
              </div>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="secondary" size="sm" className="rounded-full border border-white/10 px-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/20 text-accent">
                    {user?.name?.charAt(0).toUpperCase() || <Activity className="h-4 w-4" />}
                  </div>
                  <div className="hidden text-left lg:block">
                    <p className="text-xs text-muted">Operator</p>
                    <p className="text-sm text-foreground">{user?.name || "Trader"}</p>
                  </div>
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 border-white/10 bg-surface">
              <DropdownMenuLabel>
                <div className="flex flex-col">
                  <span className="text-sm font-medium">{user?.name || "Trader"}</span>
                  <span className="text-xs text-muted">{user?.email || "trader@example.com"}</span>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="text-danger">
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
