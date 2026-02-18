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
};

// Mock pattern stats
const mockStats = [
  {
    pattern_type: "early_exit",
    occurrences: 8,
    avg_pnl_impact: -45.5,
    trend: "increasing",
  },
  {
    pattern_type: "fomo_entry",
    occurrences: 5,
    avg_pnl_impact: -92.3,
    trend: "stable",
  },
  {
    pattern_type: "revenge_trading",
    occurrences: 3,
    avg_pnl_impact: -156.7,
    trend: "decreasing",
  },
  {
    pattern_type: "overtrading",
    occurrences: 4,
    avg_pnl_impact: -78.2,
    trend: "stable",
  },
  {
    pattern_type: "session_violation",
    occurrences: 6,
    avg_pnl_impact: -34.8,
    trend: "decreasing",
  },
  {
    pattern_type: "ignored_rules",
    occurrences: 2,
    avg_pnl_impact: -112.5,
    trend: "stable",
  },
];

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

export function PatternStats() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {mockStats.map((stat) => {
        const Icon = iconMap[stat.pattern_type] || AlertTriangle;
        const trendData = getTrendIcon(stat.trend);
        const TrendIcon = trendData.icon;

        return (
          <Card key={stat.pattern_type} className="hover:border-slate-700 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                    <Icon className="h-4 w-4 text-amber-400" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-semibold text-slate-200 text-sm leading-tight">
                      {PATTERN_LABELS[stat.pattern_type] || stat.pattern_type}
                    </h3>
                    <p className="text-xs text-slate-400">
                      {stat.occurrences} occurrence{stat.occurrences !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
                <div className={cn("h-6 w-6 rounded-full flex items-center justify-center", trendData.bg)}>
                  <TrendIcon className={cn("h-3 w-3", trendData.color)} />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Avg Impact</span>
                  <span className="text-sm font-semibold text-red-400">
                    {formatCurrency(stat.avg_pnl_impact)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Trend</span>
                  <span className={cn("text-xs font-medium capitalize", trendData.color)}>
                    {stat.trend}
                  </span>
                </div>
              </div>

              {/* Impact severity bar */}
              <div className="mt-3">
                <div className="w-full bg-slate-800 rounded-full h-1">
                  <div
                    className="h-1 rounded-full bg-red-500"
                    style={{
                      width: `${Math.min(100, (Math.abs(stat.avg_pnl_impact) / 200) * 100)}%`,
                    }}
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {Math.abs(stat.avg_pnl_impact) > 100 ? "High" : Math.abs(stat.avg_pnl_impact) > 50 ? "Medium" : "Low"} impact
                </p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
