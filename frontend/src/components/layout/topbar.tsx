"use client";

import React from "react";
import { Bell, User, LogOut, Settings, Wifi, WifiOff } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";
import { useAlertsStore } from "@/stores/alerts-store";
import { useSettingsStore } from "@/stores/settings-store";
import { MobileNav } from "./mobile-nav";

export function Topbar() {
  const { user, logout } = useAuthStore();
  const { unreadCount } = useAlertsStore();
  const { brokerConnected } = useSettingsStore();

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between h-14 px-4 border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm">
      {/* Mobile nav + page title area */}
      <div className="flex items-center gap-3">
        <MobileNav />
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Broker Status */}
        <div
          className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${
            brokerConnected
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : "bg-red-500/10 text-red-400 border border-red-500/20"
          }`}
        >
          {brokerConnected ? (
            <Wifi className="h-3 w-3" />
          ) : (
            <WifiOff className="h-3 w-3" />
          )}
          {brokerConnected ? "Connected" : "Disconnected"}
        </div>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4 text-slate-400" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="rounded-full">
              <div className="h-7 w-7 rounded-full bg-emerald-600 flex items-center justify-center text-white text-xs font-bold">
                {user?.name?.charAt(0).toUpperCase() || "U"}
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="flex flex-col">
                <span className="text-sm font-medium">{user?.name || "Trader"}</span>
                <span className="text-xs text-slate-400">{user?.email || "trader@example.com"}</span>
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
            <DropdownMenuItem onClick={logout} className="text-red-400">
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
