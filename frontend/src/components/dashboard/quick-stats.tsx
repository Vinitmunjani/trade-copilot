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
    },
    {
      label: "Win Rate",
      value: formatPercent(winRate),
      icon: Target,
      color: winRate >= 50 ? "text-accent" : "text-danger",
    },
    {
      label: "Avg R",
      value: formatR(avgR),
      icon: TrendingUp,
      color: avgR >= 0 ? "text-accent" : "text-danger",
    },
    {
      label: "Rule Adherence",
      value: formatPercent(ruleAdherence),
      icon: Shield,
      color:
        ruleAdherence >= 80 ? "text-accent" : ruleAdherence >= 60 ? "text-amber-300" : "text-danger",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="overflow-hidden border-white/5 bg-surface p-4">
          <div className="relative flex items-center gap-4">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
              <stat.icon className={cn("h-5 w-5", stat.color)} />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted">{stat.label}</p>
              <p className={cn("text-2xl font-semibold", stat.color)}>{stat.value}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
