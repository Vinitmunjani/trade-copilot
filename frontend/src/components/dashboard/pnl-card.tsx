"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, TrendingDown } from "lucide-react";
import { formatCurrency, formatR, cn } from "@/lib/utils";

interface PnlCardProps {
  pnl: number;
  pnlR: number;
  label?: string;
}

export function PnlCard({ pnl, pnlR, label = "Today's P&L" }: PnlCardProps) {
  const isPositive = pnl >= 0;

  return (
    <Card className="relative overflow-hidden">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-400 mb-1">{label}</p>
            <p
              className={cn(
                "text-4xl font-bold tracking-tight",
                isPositive ? "text-emerald-400" : "text-red-400"
              )}
            >
              {formatCurrency(pnl)}
            </p>
            <p
              className={cn(
                "text-lg font-medium mt-1",
                isPositive ? "text-emerald-400/70" : "text-red-400/70"
              )}
            >
              {formatR(pnlR)}
            </p>
          </div>
          <div
            className={cn(
              "h-14 w-14 rounded-full flex items-center justify-center",
              isPositive ? "bg-emerald-500/10" : "bg-red-500/10"
            )}
          >
            {isPositive ? (
              <TrendingUp className="h-7 w-7 text-emerald-400" />
            ) : (
              <TrendingDown className="h-7 w-7 text-red-400" />
            )}
          </div>
        </div>
      </CardContent>
      {/* Decorative gradient */}
      <div
        className={cn(
          "absolute bottom-0 left-0 right-0 h-1",
          isPositive ? "bg-gradient-to-r from-emerald-500 to-emerald-600" : "bg-gradient-to-r from-red-500 to-red-600"
        )}
      />
    </Card>
  );
}
