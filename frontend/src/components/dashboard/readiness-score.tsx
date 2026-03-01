"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface ReadinessScoreProps {
  score: number;
}

export function ReadinessScore({ score }: ReadinessScoreProps) {
  const clampedScore = Math.max(1, Math.min(10, score));
  const percentage = clampedScore / 10;

  const getColor = (s: number) => {
    if (s <= 3) return { stroke: "hsl(var(--danger))", text: "text-danger", label: "Stressed" };
    if (s <= 6) return { stroke: "hsl(38 92% 55%)", text: "text-amber-300", label: "Warming up" };
    return { stroke: "hsl(var(--accent))", text: "text-accent", label: "Locked in" };
  };

  const { stroke, text, label } = getColor(clampedScore);

  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - percentage);

  const glowColor =
    clampedScore > 6 ? "bg-accent/20" : clampedScore > 3 ? "bg-amber-400/15" : "bg-danger/20";

  return (
    <Card className="relative overflow-hidden border-white/5 bg-gradient-to-br from-surface via-surface-muted to-surface-contrast text-center">
      <div className="pointer-events-none absolute inset-0 opacity-70">
        <div className={cn("absolute inset-y-0 left-0 w-2/3 blur-[80px]", glowColor)} />
      </div>
      <CardHeader className="relative pb-2">
        <CardTitle className="text-base">Readiness Score</CardTitle>
      </CardHeader>
      <CardContent className="relative flex flex-col items-center justify-center pb-6">
        <div className="relative w-40 h-40">
          <svg
            className="w-40 h-40 transform -rotate-90"
            viewBox="0 0 140 140"
          >
            {/* Background circle */}
            <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
            {/* Progress circle */}
            <circle
              cx="70"
              cy="70"
              r={radius}
              fill="none"
              stroke={stroke}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-700 ease-out"
            />
          </svg>
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-4xl font-bold ${text}`}>{clampedScore}</span>
            <span className="text-xs text-muted">/10</span>
          </div>
        </div>
        <p className={`mt-3 text-sm font-medium ${text}`}>{label}</p>
        <p className="mt-1 text-xs text-muted">Based on recent behavior</p>
      </CardContent>
    </Card>
  );
}

