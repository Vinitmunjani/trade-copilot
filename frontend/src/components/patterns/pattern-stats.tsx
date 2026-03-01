"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AlertTriangle,
  Zap,
  Repeat,
  Clock,
  LogOut,
  ShieldOff,
  TrendingDown,
  Heart,
  Scale,
  MoveHorizontal,
  TrendingUp,
  Minus,
} from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { PATTERN_LABELS } from "@/lib/constants";

const iconMap: Record<string, React.ElementType> = {
  revenge_trading: AlertTriangle,
  overtrading: Repeat,
  fomo_entry: Zap,
  early_exit: LogOut,
  moved_stop_loss: MoveHorizontal,
  ignored_rules: ShieldOff,
  session_violation: Clock,
  size_violation: Scale,
  emotional_trading: Heart,
  chasing_losses: TrendingDown,
  missing_sl_tp: ShieldOff,
};


const getTrendIcon = (trend: string) => {
  switch (trend) {
    case "increasing":
      return { icon: TrendingUp, color: "text-red-400", bg: "bg-red-500/10" };
    case "decreasing":
      return { icon: TrendingDown, color: "text-emerald-400", bg: "bg-emerald-500/10" };
    default:
      return { icon: Minus, color: "text-slate-400", bg: "bg-slate-500/10" };
  }
};

interface PatternStatsProps {
  patterns?: Array<{
    pattern: string;
    frequency: number;
    description: string;
    impact: string;
    recommendation: string;
  }>;
}

export function PatternStats({ patterns = [] }: PatternStatsProps) {
  if (!patterns || patterns.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <AlertTriangle className="h-12 w-12 mx-auto mb-4" />
        <p className="text-lg">No behavioral patterns detected yet</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {patterns.map((stat) => {
        const Icon = iconMap[stat.pattern] || AlertTriangle;
        const impactColor = stat.impact === "negative" ? "text-red-400" : stat.impact === "positive" ? "text-emerald-400" : "text-slate-400";
        const bgColor = stat.impact === "negative" ? "bg-red-500/10" : stat.impact === "positive" ? "bg-emerald-500/10" : "bg-slate-500/10";

        return (
          <Card key={stat.pattern} className="hover:border-slate-700 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                    <Icon className="h-4 w-4 text-amber-400" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-semibold text-slate-200 text-sm leading-tight">
                      {stat.pattern}
                    </h3>
                    <p className="text-xs text-slate-400">
                      {stat.frequency} occurrence{stat.frequency !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
                <div className={cn("h-6 w-6 rounded-full flex items-center justify-center", bgColor)}>
                  <Minus className={cn("h-3 w-3", impactColor)} />
                </div>
              </div>

              <p className="text-xs text-slate-400 mb-2">{stat.description}</p>
              <p className="text-xs italic text-slate-300">{stat.recommendation}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
