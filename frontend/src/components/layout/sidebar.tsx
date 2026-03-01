"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BarChart3,
  LineChart,
  Brain,
  Shield,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, meta: "Live" },
  { href: "/trades", label: "Trades", icon: BarChart3 },
  { href: "/analytics", label: "Analytics", icon: LineChart },
  { href: "/patterns", label: "Patterns", icon: Brain, meta: "Beta" },
  { href: "/rules", label: "Rules", icon: Shield },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-screen flex-col border-r border-white/5 bg-white/5 px-3 py-4 backdrop-blur-2xl transition-all duration-500 md:flex",
        collapsed ? "w-20" : "w-72"
      )}
    >
      <div className="flex items-center gap-3 rounded-3xl border border-white/5 bg-gradient-to-br from-surface to-surface-muted px-4 py-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-accent/20 text-accent">
          <Activity className="h-5 w-5" />
        </div>
        {!collapsed && (
          <div>
            <p className="text-xs font-medium tracking-[0.08em] text-muted">ampere.capital</p>
            <p className="text-base font-semibold text-foreground">Mission Deck</p>
          </div>
        )}
      </div>

      <nav className="mt-6 flex-1 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium",
                collapsed ? "justify-center" : "",
                isActive
                  ? "bg-white/10 text-foreground shadow-[0_0_30px_rgba(16,185,129,0.15)]"
                  : "text-muted hover:text-foreground hover:bg-white/5"
              )}
              title={collapsed ? item.label : undefined}
            >
              <span
                className={cn(
                  "absolute left-1 top-1/2 h-10 w-[1.5px] -translate-y-1/2 rounded-full bg-accent opacity-0 transition-opacity duration-300",
                  isActive && !collapsed ? "opacity-100" : ""
                )}
                aria-hidden="true"
              />
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && (
                <div className="flex w-full items-center justify-between">
                  <span>{item.label}</span>
                  {item.meta && (
                    <span className="text-[10px] uppercase tracking-[0.3em] text-accent">{item.meta}</span>
                  )}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-4 space-y-3">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 py-3 text-sm text-foreground/80 transition hover:text-foreground"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          {!collapsed && <span>Collapse rail</span>}
        </button>
      </div>
    </aside>
  );
}
