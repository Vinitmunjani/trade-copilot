"use client";

import React, { useMemo } from "react";
import { DollarSign, TrendingDown } from "lucide-react";
import { useTradesStore } from "@/stores/trades-store";

const LABEL: Record<string, string> = {
  revenge_trading: "Revenge Trading",
  overtrading: "Overtrading",
  fomo_entry: "FOMO Entry",
  early_exit: "Early Exit",
  late_entry: "Late Entry",
  missing_sl: "Missing Stop Loss",
  missing_tp: "Missing Take Profit",
  bad_rr: "Bad Risk/Reward",
  excessive_risk: "Excessive Risk",
  tilt_trading: "Tilt Trading",
  session_drift: "Session Drift",
  unknown: "Unclassified",
};

export function PatternCost() {
  const { trades } = useTradesStore();

  const rows = useMemo(() => {
    const map: Record<string, { cost: number; count: number }> = {};

    for (const trade of trades) {
      if (trade.status !== "closed" && trade.status !== "CLOSED") continue;
      if (!trade.pnl) continue;

      const flags = trade.behavioral_flags ?? trade.flags ?? [];
      if (flags.length === 0) continue;

      for (const flag of flags) {
        const key = (flag.flag ?? flag.type ?? "unknown").toLowerCase();
        if (!map[key]) map[key] = { cost: 0, count: 0 };
        // Only count cost if the trade was a loss; flag caused/coincided with the loss
        if (trade.pnl < 0) {
          map[key].cost += Math.abs(trade.pnl);
        }
        map[key].count += 1;
      }
    }

    return Object.entries(map)
      .map(([key, { cost, count }]) => ({
        key,
        label: LABEL[key] ?? key.replace(/_/g, " "),
        cost,
        count,
      }))
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 6);
  }, [trades]);

  const maxCost = rows[0]?.cost ?? 1;
  const totalCost = rows.reduce((s, r) => s + r.cost, 0);

  return (
    <div className="rounded-2xl border border-white/8 bg-surface/60 p-5">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-400/10">
            <TrendingDown className="h-4 w-4 text-red-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Pattern Cost</p>
            <p className="text-xs text-muted">Dollar cost per behavioural flag</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-muted">Total identified</p>
          <p className="text-lg font-semibold text-red-300">${totalCost.toFixed(0)}</p>
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <DollarSign className="h-8 w-8 text-accent/30" />
          <p className="text-sm text-muted">No flagged trade losses yet</p>
          <p className="text-xs text-muted/60">Patterns will appear as trades are analysed</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rows.map(({ key, label, cost, count }) => (
            <div key={key}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-foreground">{label}</span>
                  <span className="rounded-full bg-surface-muted px-1.5 py-0.5 text-[10px] text-muted">
                    ×{count}
                  </span>
                </div>
                <span className="text-sm font-medium text-red-300">
                  {cost > 0 ? `-$${cost.toFixed(0)}` : "—"}
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-surface">
                <div
                  className="h-full rounded-full bg-red-400/70 transition-all duration-700"
                  style={{ width: `${(cost / maxCost) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="mt-4 border-t border-white/5 pt-3 text-[11px] text-muted/60">
        Cost is the total PnL loss on trades where each pattern was detected.
      </p>
    </div>
  );
}
