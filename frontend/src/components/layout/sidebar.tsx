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
  CreditCard,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { AmpereLogo } from "@/components/ui/ampere-logo";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, meta: "Live" },
  { href: "/trades", label: "Trades", icon: BarChart3 },
  { href: "/analytics", label: "Analytics", icon: LineChart },
  { href: "/patterns", label: "Patterns", icon: Brain, meta: "Beta" },
  { href: "/rules", label: "Rules", icon: Shield },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/billing", label: "Billing", icon: CreditCard },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const railWidth = collapsed ? "w-20" : "w-72";

  return (
    <div className={cn("hidden shrink-0 md:block", railWidth)}>
      <aside
        className={cn(
          "fixed left-0 top-0 z-30 hidden h-screen flex-col border-r border-border bg-surface px-3 py-4 transition-all duration-500 md:flex",
          railWidth
        )}
      >
        <div className="flex items-center gap-3 rounded-3xl border border-border bg-surface-muted px-4 py-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-surface-contrast">
            <AmpereLogo className="h-6 w-6" />
          </div>
          {!collapsed && (
            <div>
              <p className="text-xs font-medium tracking-[0.08em] text-muted">ampere.capital</p>
            </div>
          )}
        </div>

        <nav className="mt-6 flex-1 space-y-1 overflow-y-auto">
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
                    ? "border border-border bg-surface-muted text-foreground"
                    : "text-muted hover:text-foreground hover:bg-surface-muted/70"
                )}
                title={collapsed ? item.label : undefined}
              >
                <span
                  className={cn(
                    "absolute left-2 top-1/2 h-7 w-px -translate-y-1/2 rounded-full bg-accent/65 opacity-0 transition-opacity duration-300",
                    isActive && !collapsed ? "opacity-100" : ""
                  )}
                  aria-hidden="true"
                />
                <item.icon className="h-5 w-5 shrink-0" />
                {!collapsed && (
                  <div className="flex w-full items-center justify-between">
                    <span>{item.label}</span>
                    {item.meta && (
                      <span className="text-[10px] uppercase tracking-[0.3em] text-accent/90">{item.meta}</span>
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
            className="flex w-full items-center justify-center gap-2 rounded-2xl border border-border bg-surface-muted py-3 text-sm text-muted transition hover:bg-surface-contrast hover:text-foreground"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            {!collapsed && <span>Collapse rail</span>}
          </button>
        </div>
      </aside>
    </div>
  );
}
