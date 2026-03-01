"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowUpRight, ArrowDownRight, AlertTriangle } from "lucide-react";
import { AiScoreBadge } from "@/components/trades/ai-score-badge";
import { formatCurrency, formatPrice, cn } from "@/lib/utils";
import type { Trade } from "@/types";

interface OpenTradesProps {
  trades: Trade[];
}

export function OpenTrades({ trades }: OpenTradesProps) {
  if (trades.length === 0) {
    return (
      <Card className="border-white/5">
        <CardHeader>
          <CardTitle className="text-base">Open Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-muted">
            <p className="text-sm">No open trades</p>
            <p className="mt-1 text-xs">Trades will appear here in real-time</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-white/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          Open Trades
          <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs font-normal text-muted">
            {trades.length}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {trades.map((trade) => (
          <div
            key={trade.id}
            className="flex items-center justify-between rounded-2xl border border-white/5 bg-white/5 px-3 py-3 transition hover:border-white/20"
          >
            <div className="flex items-center gap-3">
              {/* Direction Icon */}
              <div
                className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-2xl",
                  trade.direction === "BUY"
                    ? "border border-accent/30 bg-accent/10 text-accent"
                    : "border border-danger/30 bg-danger/10 text-danger"
                )}
              >
                {trade.direction === "BUY" ? (
                  <ArrowUpRight className="h-4 w-4" />
                ) : (
                  <ArrowDownRight className="h-4 w-4" />
                )}
              </div>

              {/* Symbol & Direction */}
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground">{trade.symbol}</span>
                  <span
                    className={cn(
                      "text-xs font-medium",
                      trade.direction === "BUY" ? "text-accent" : "text-danger"
                    )}
                  >
                    {trade.direction}
                  </span>
                </div>
                <p className="text-xs text-muted">
                  Entry: {formatPrice(trade.entry_price)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Flags */}
              {trade.flags.length > 0 && (
                <div className="flex items-center gap-1 text-amber-300">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  <span className="text-xs">{trade.flags.length}</span>
                </div>
              )}

              {/* AI Score */}
              {trade.ai_score && <AiScoreBadge score={trade.ai_score} />}

              {/* P&L */}
              <div className="text-right">
                <p
                  className={cn(
                    "text-sm font-semibold",
                    (trade.pnl || 0) >= 0 ? "text-accent" : "text-danger"
                  )}
                >
                  {formatCurrency(trade.pnl || 0)}
                </p>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
