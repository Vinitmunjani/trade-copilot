"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Menu,
  X,
  LayoutDashboard,
  BarChart3,
  LineChart,
  Brain,
  Shield,
  FileText,
  Settings,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/trades", label: "Trades", icon: BarChart3 },
  { href: "/analytics", label: "Analytics", icon: LineChart },
  { href: "/patterns", label: "Patterns", icon: Brain },
  { href: "/rules", label: "Rules", icon: Shield },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="md:hidden">
      <button
        onClick={() => setOpen(!open)}
        className="rounded-full border border-white/10 p-2 text-foreground/70 hover:bg-white/5"
      >
        {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" onClick={() => setOpen(false)} />
          <div className="fixed left-0 top-0 bottom-0 z-50 flex w-72 flex-col border-r border-white/10 bg-surface/95 backdrop-blur-2xl">
            <div className="flex items-center gap-3 border-b border-white/10 px-5 py-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-accent/20 text-accent">
                <Activity className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-medium tracking-[0.08em] text-muted">ampere.capital</p>
                <p className="text-base font-semibold text-foreground">Mission Deck</p>
              </div>
            </div>
            <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-4">
              {navItems.map((item) => {
                const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className={cn(
                      "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium",
                      isActive
                        ? "bg-white/10 text-foreground"
                        : "text-muted hover:text-foreground hover:bg-white/5"
                    )}
                  >
                    <item.icon className="h-5 w-5" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </>
      )}
    </div>
  );
}
