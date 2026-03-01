"use client";

import React, { useMemo, useState } from "react";
import { Target, Trophy, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTradesStore } from "@/stores/trades-store";

type GroupBy = "symbol" | "session";

interface EdgeRow {
  key: string;
  trades: number;
  wins: number;
  winRate: number;
  avgPnl: number;
  totalPnl: number;
}

export function EdgeFinder() {
  const { trades } = useTradesStore();
  const [groupBy, setGroupBy] = useState<GroupBy>("symbol");

  const rows: EdgeRow[] = useMemo(() => {
    const closed = trades.filter(
      (t) => (t.status === "closed" || t.status === "CLOSED") && t.pnl !== null
    );

    const map: Record<string, { wins: number; total: number; pnl: number }> = {};

    for (const t of closed) {
      const key =
        groupBy === "symbol"
          ? t.symbol.toUpperCase()
          : (t.session ?? "unknown").replace(/_/g, " ");

      if (!map[key]) map[key] = { wins: 0, total: 0, pnl: 0 };
      map[key].total++;
      map[key].pnl += t.pnl!;
      if ((t.pnl ?? 0) > 0) map[key].wins++;
    }

    return Object.entries(map)
      .map(([key, { wins, total, pnl }]) => ({
        key,
        trades: total,
        wins,
        winRate: total > 0 ? (wins / total) * 100 : 0,
        avgPnl: total > 0 ? pnl / total : 0,
        totalPnl: pnl,
      }))
      .filter((r) => r.trades >= 2) // need at least 2 trades to be meaningful
      .sort((a, b) => b.winRate - a.winRate || b.totalPnl - a.totalPnl);
  }, [trades, groupBy]);

  const top = rows[0];
  const bottom = rows[rows.length - 1];

  return (
    <div className="rounded-2xl border border-white/8 bg-surface/60 p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/10">
            <Target className="h-4 w-4 text-accent" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Edge Finder</p>
            <p className="text-xs text-muted">Where you actually win</p>
          </div>
        </div>
        <div className="flex rounded-lg border border-white/10 overflow-hidden text-xs">
          {(["symbol", "session"] as GroupBy[]).map((g) => (
            <button
              key={g}
              onClick={() => setGroupBy(g)}
              className={cn(
                "px-3 py-1.5 capitalize transition-colors",
                groupBy === g ? "bg-accent/20 text-accent" : "text-muted hover:text-foreground"
              )}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <Clock className="h-8 w-8 text-accent/30" />
          <p className="text-sm text-muted">Need more closed trades</p>
          <p className="text-xs text-muted/60">At least 2 trades per group to calculate edge</p>
        </div>
      ) : (
        <>
          {/* Best edge callout */}
          {top && top.winRate >= 50 && (
            <div className="mb-4 flex items-center gap-3 rounded-xl border border-accent/20 bg-accent/5 px-4 py-3">
              <Trophy className="h-4 w-4 shrink-0 text-accent" />
              <p className="text-xs text-muted">
                Your best edge:{" "}
                <span className="font-semibold text-foreground capitalize">{top.key}</span>
                {" "}— {top.winRate.toFixed(0)}% win rate over {top.trades} trades (
                <span className={top.totalPnl >= 0 ? "text-accent" : "text-red-400"}>
                  {top.totalPnl >= 0 ? "+" : ""}${top.totalPnl.toFixed(0)}
                </span>
                )
              </p>
            </div>
          )}

          {/* Table */}
          <div className="space-y-2">
            {rows.slice(0, 6).map((row, i) => (
              <div
                key={row.key}
                className={cn(
                  "flex items-center gap-3 rounded-xl border px-4 py-3",
                  i === 0 && "border-accent/20 bg-accent/5",
                  i !== 0 && "border-white/5 bg-surface/40"
                )}
              >
                <span className="w-5 text-xs text-muted">{i + 1}</span>
                <span className="flex-1 text-sm font-medium capitalize text-foreground">{row.key}</span>
                <div className="flex items-center gap-4 text-xs">
                  <div className="text-right">
                    <p className="text-muted">Win rate</p>
                    <p className={cn("font-semibold", row.winRate >= 50 ? "text-accent" : "text-red-300")}>
                      {row.winRate.toFixed(0)}%
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-muted">Avg P&amp;L</p>
                    <p className={cn("font-semibold", row.avgPnl >= 0 ? "text-accent" : "text-red-300")}>
                      {row.avgPnl >= 0 ? "+" : ""}${row.avgPnl.toFixed(0)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-muted">Trades</p>
                    <p className="font-semibold text-foreground">{row.trades}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Worst edge warning */}
          {bottom && rows.length > 1 && bottom.winRate < 45 && bottom.totalPnl < 0 && (
            <p className="mt-3 text-[11px] text-muted/70">
              Worst edge:{" "}
              <span className="text-red-300 capitalize">{bottom.key}</span>
              {" "}({bottom.winRate.toFixed(0)}% win rate, ${bottom.totalPnl.toFixed(0)} total). Consider avoiding.
            </p>
          )}
        </>
      )}
    </div>
  );
}
