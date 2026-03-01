"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, TrendingDown } from "lucide-react";
import { formatCurrency, formatR, cn } from "@/lib/utils";

interface PnlCardProps {
  pnl: number;
  pnlR: number;
  label?: string;
  tradesCount?: number;
}

export function PnlCard({ pnl, pnlR, label = "Today's P&L", tradesCount }: PnlCardProps) {
  const isPositive = pnl >= 0;

  return (
    <Card className="relative overflow-hidden border-white/10 bg-gradient-to-br from-surface via-surface-muted to-surface-contrast">
      <div className="pointer-events-none absolute inset-0 opacity-60">
        <div
          className={cn(
            "absolute inset-y-0 right-0 w-1/3 blur-[90px]",
            isPositive ? "bg-accent/40" : "bg-danger/25"
          )}
        />
      </div>
      <CardContent className="relative p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-muted">{label}</p>
            <p
              className={cn(
                "mt-4 text-4xl font-semibold tracking-tight",
                isPositive ? "text-glow" : "text-danger"
              )}
            >
              {formatCurrency(pnl)}
            </p>
            <p
              className={cn(
                "text-lg font-medium",
                isPositive ? "text-accent" : "text-danger"
              )}
            >
              {formatR(pnlR)}
            </p>
            {tradesCount !== undefined && (
              <p className="mt-3 text-xs text-muted">
                {tradesCount === 0
                  ? "No trades closed today"
                  : `${tradesCount} trade${tradesCount !== 1 ? "s" : ""} closed today`}
              </p>
            )}
          </div>
          <div
            className={cn(
              "flex h-16 w-16 items-center justify-center rounded-2xl border",
              isPositive ? "border-accent/30 bg-accent/10 text-accent" : "border-danger/30 bg-danger/10 text-danger"
            )}
          >
            {isPositive ? <TrendingUp className="h-7 w-7" /> : <TrendingDown className="h-7 w-7" />}
          </div>
        </div>
      </CardContent>
      <div
        className={cn(
          "absolute inset-x-6 bottom-4 h-px bg-gradient-to-r",
          isPositive
            ? "from-transparent via-accent/40 to-transparent"
            : "from-transparent via-danger/40 to-transparent"
        )}
      />
    </Card>
  );
}
