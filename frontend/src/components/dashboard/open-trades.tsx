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
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Open Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-slate-400">
            <p className="text-sm">No open trades</p>
            <p className="text-xs mt-1">Trades will appear here in real-time</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          Open Trades
          <span className="text-xs font-normal text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
            {trades.length}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {trades.map((trade) => (
          <div
            key={trade.id}
            className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 border border-slate-800 hover:border-slate-700 transition-colors"
          >
            <div className="flex items-center gap-3">
              {/* Direction Icon */}
              <div
                className={cn(
                  "h-8 w-8 rounded-full flex items-center justify-center",
                  trade.direction === "BUY" ? "bg-emerald-500/10" : "bg-red-500/10"
                )}
              >
                {trade.direction === "BUY" ? (
                  <ArrowUpRight className="h-4 w-4 text-emerald-400" />
                ) : (
                  <ArrowDownRight className="h-4 w-4 text-red-400" />
                )}
              </div>

              {/* Symbol & Direction */}
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-100">{trade.symbol}</span>
                  <span
                    className={cn(
                      "text-xs font-medium",
                      trade.direction === "BUY" ? "text-emerald-400" : "text-red-400"
                    )}
                  >
                    {trade.direction}
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  Entry: {formatPrice(trade.entry_price)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Flags */}
              {trade.flags.length > 0 && (
                <div className="flex items-center gap-1">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                  <span className="text-xs text-amber-400">{trade.flags.length}</span>
                </div>
              )}

              {/* AI Score */}
              {trade.ai_score && <AiScoreBadge score={trade.ai_score.score} />}

              {/* P&L */}
              <div className="text-right">
                <p
                  className={cn(
                    "font-semibold text-sm animate-pulse",
                    (trade.pnl || 0) >= 0 ? "text-emerald-400" : "text-red-400"
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
