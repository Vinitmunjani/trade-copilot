"use client";

import React, { useMemo, useState } from "react";
import { ShieldAlert, ShieldCheck, AlertTriangle, ChevronDown, ChevronUp, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTradesStore } from "@/stores/trades-store";

const LOCKOUT_THRESHOLD = 3; // consecutive losses → lockout
const WARN_THRESHOLD = 2;    // consecutive losses → warning

export function LossLockout() {
  const { trades } = useTradesStore();
  const [expanded, setExpanded] = useState(false);

  const { consecutiveLosses, lastResults, dollarLost, level } = useMemo(() => {
    const closed = trades
      .filter((t) => t.status === "closed" || t.status === "CLOSED")
      .filter((t) => t.pnl !== null && t.pnl !== undefined)
      .sort((a, b) => new Date(b.closed_at ?? b.close_time ?? 0).getTime() - new Date(a.closed_at ?? a.close_time ?? 0).getTime());

    // Count streak of losses from most recent trade backwards
    let streak = 0;
    let dollarLost = 0;
    const lastResults: Array<{ pnl: number; symbol: string }> = [];

    for (const t of closed.slice(0, 10)) {
      lastResults.push({ pnl: t.pnl!, symbol: t.symbol });
      if ((t.pnl ?? 0) < 0 && streak === lastResults.length - 1) {
        streak++;
        dollarLost += Math.abs(t.pnl!);
      }
    }

    const level: "clear" | "warn" | "lockout" =
      streak >= LOCKOUT_THRESHOLD ? "lockout" : streak >= WARN_THRESHOLD ? "warn" : "clear";

    return { consecutiveLosses: streak, lastResults, dollarLost, level };
  }, [trades]);

  const config = {
    clear: {
      bg: "bg-accent/5 border-accent/20",
      icon: ShieldCheck,
      iconColor: "text-accent",
      iconBg: "bg-accent/15",
      label: "Capital Protection",
      headline: "You're in the clear",
      sub: "No consecutive loss streak detected.",
      bar: "bg-accent",
    },
    warn: {
      bg: "bg-amber-500/5 border-amber-500/25",
      icon: AlertTriangle,
      iconColor: "text-amber-400",
      iconBg: "bg-amber-400/15",
      label: "Capital Protection",
      headline: `${consecutiveLosses} consecutive losses — slow down`,
      sub: `You've lost $${dollarLost.toFixed(2)} across the last ${consecutiveLosses} trades. Consider reducing size or pausing.`,
      bar: "bg-amber-400",
    },
    lockout: {
      bg: "bg-red-500/8 border-red-500/30",
      icon: Lock,
      iconColor: "text-red-400",
      iconBg: "bg-red-400/15",
      label: "Capital Protection — LOCKOUT",
      headline: `${consecutiveLosses} losses in a row — step away`,
      sub: `$${dollarLost.toFixed(2)} lost in the last ${consecutiveLosses} trades. This is the spiral. Your rule says stop here.`,
      bar: "bg-red-500",
    },
  }[level];

  const Icon = config.icon;
  const fillPct = Math.min((consecutiveLosses / LOCKOUT_THRESHOLD) * 100, 100);

  return (
    <div className={cn("rounded-2xl border p-5 transition-all duration-300", config.bg)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-xl", config.iconBg)}>
            <Icon className={cn("h-5 w-5", config.iconColor)} />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.35em] text-muted">{config.label}</p>
            <p className={cn("text-sm font-semibold", level === "clear" ? "text-foreground" : level === "warn" ? "text-amber-300" : "text-red-300")}>
              {config.headline}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Streak bar */}
          <div className="hidden sm:flex flex-col items-end gap-1.5">
            <p className="text-[10px] text-muted">
              {consecutiveLosses} / {LOCKOUT_THRESHOLD} loss limit
            </p>
            <div className="h-1.5 w-32 rounded-full bg-surface">
              <div
                className={cn("h-full rounded-full transition-all duration-700", config.bar)}
                style={{ width: `${fillPct}%` }}
              />
            </div>
          </div>

          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/10 text-muted hover:text-foreground transition-colors"
          >
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="mt-4 space-y-3 border-t border-white/5 pt-4">
          <p className="text-sm text-muted">{config.sub}</p>

          {/* Last 5 trade P&L dots */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">Last {Math.min(lastResults.length, 5)} trades:</span>
            <div className="flex gap-1.5">
              {lastResults.slice(0, 5).map((r, i) => (
                <div
                  key={i}
                  className={cn(
                    "flex h-7 items-center rounded-lg px-2.5 text-xs font-medium",
                    r.pnl >= 0 ? "bg-accent/15 text-accent" : "bg-red-400/15 text-red-300"
                  )}
                >
                  {r.pnl >= 0 ? "+" : ""}${r.pnl.toFixed(0)}
                </div>
              ))}
            </div>
          </div>

          {level === "lockout" && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3">
              <p className="text-sm font-medium text-red-300">Recommended actions:</p>
              <ul className="mt-2 space-y-1.5 text-xs text-muted">
                <li className="flex gap-2"><span className="text-red-400">→</span> Close your trading platform for at least 2 hours</li>
                <li className="flex gap-2"><span className="text-red-400">→</span> Do not open any new positions</li>
                <li className="flex gap-2"><span className="text-red-400">→</span> Review your last 3 trades in the journal before returning</li>
                <li className="flex gap-2"><span className="text-red-400">→</span> Ask: was each loss from the market, or from you?</li>
              </ul>
            </div>
          )}

          {level === "warn" && (
            <div className="rounded-xl border border-amber-400/20 bg-amber-400/10 px-4 py-3">
              <p className="text-xs text-amber-300">
                One more loss = lockout threshold. Consider halving your position size on the next trade.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
