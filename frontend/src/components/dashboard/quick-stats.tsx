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
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    },
    {
      label: "Win Rate",
      value: formatPercent(winRate),
      icon: Target,
      color: winRate >= 50 ? "text-emerald-400" : "text-red-400",
      bg: winRate >= 50 ? "bg-emerald-500/10" : "bg-red-500/10",
    },
    {
      label: "Avg R",
      value: formatR(avgR),
      icon: TrendingUp,
      color: avgR >= 0 ? "text-emerald-400" : "text-red-400",
      bg: avgR >= 0 ? "bg-emerald-500/10" : "bg-red-500/10",
    },
    {
      label: "Rule Adherence",
      value: formatPercent(ruleAdherence),
      icon: Shield,
      color: ruleAdherence >= 80 ? "text-emerald-400" : ruleAdherence >= 60 ? "text-amber-400" : "text-red-400",
      bg: ruleAdherence >= 80 ? "bg-emerald-500/10" : ruleAdherence >= 60 ? "bg-amber-500/10" : "bg-red-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="hover:border-slate-700 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", stat.bg)}>
                <stat.icon className={cn("h-5 w-5", stat.color)} />
              </div>
              <div>
                <p className="text-xs text-slate-400">{stat.label}</p>
                <p className={cn("text-xl font-bold", stat.color)}>{stat.value}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
