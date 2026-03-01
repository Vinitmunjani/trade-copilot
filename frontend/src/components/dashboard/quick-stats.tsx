"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { BarChart3, Target, TrendingUp, Shield } from "lucide-react";
import { cn, formatPercent, formatR } from "@/lib/utils";

interface QuickStatsProps {
  tradesToday: number;
  winRate: number;
  avgR: number;
  ruleAdherence: number;
}

export function QuickStats({ tradesToday, winRate, avgR, ruleAdherence }: QuickStatsProps) {
  const stats = [
    {
      label: "Trades Today",
      value: tradesToday.toString(),
      icon: BarChart3,
      color: "text-foreground",
      accent: "from-accent/20 via-accent/5 to-transparent",
    },
    {
      label: "Win Rate",
      value: formatPercent(winRate),
      icon: Target,
      color: winRate >= 50 ? "text-accent" : "text-danger",
      accent: winRate >= 50 ? "from-accent/30 via-accent/10 to-transparent" : "from-danger/30 via-danger/10 to-transparent",
    },
    {
      label: "Avg R",
      value: formatR(avgR),
      icon: TrendingUp,
      color: avgR >= 0 ? "text-accent" : "text-danger",
      accent: avgR >= 0 ? "from-accent/30 via-accent/10 to-transparent" : "from-danger/30 via-danger/10 to-transparent",
    },
    {
      label: "Rule Adherence",
      value: formatPercent(ruleAdherence),
      icon: Shield,
      color:
        ruleAdherence >= 80 ? "text-accent" : ruleAdherence >= 60 ? "text-amber-300" : "text-danger",
      accent:
        ruleAdherence >= 80
          ? "from-accent/20 via-accent/5 to-transparent"
          : ruleAdherence >= 60
            ? "from-amber-400/20 via-amber-400/5 to-transparent"
            : "from-danger/25 via-danger/5 to-transparent",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="overflow-hidden border-white/5 bg-surface-muted/70 p-4">
          <div className="relative flex items-center gap-4">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
              <stat.icon className={cn("h-5 w-5", stat.color)} />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted">{stat.label}</p>
              <p className={cn("text-2xl font-semibold", stat.color)}>{stat.value}</p>
            </div>
            <div
              className={cn(
                "pointer-events-none absolute inset-0 -z-10 rounded-[20px] bg-gradient-to-r opacity-70",
                stat.accent
              )}
            />
          </div>
        </Card>
      ))}
    </div>
  );
}
