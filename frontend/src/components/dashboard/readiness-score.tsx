"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ReadinessScoreProps {
  score: number;
}

export function ReadinessScore({ score }: ReadinessScoreProps) {
  const clampedScore = Math.max(1, Math.min(10, score));
  const percentage = clampedScore / 10;

  const getColor = (s: number) => {
    if (s <= 3) return { stroke: "#ef4444", text: "text-red-400", label: "Poor" };
    if (s <= 6) return { stroke: "#f59e0b", text: "text-amber-400", label: "Fair" };
    return { stroke: "#10b981", text: "text-emerald-400", label: "Good" };
  };

  const { stroke, text, label } = getColor(clampedScore);

  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - percentage);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Readiness Score</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center pb-6">
        <div className="relative w-40 h-40">
          <svg
            className="w-40 h-40 transform -rotate-90"
            viewBox="0 0 140 140"
          >
            {/* Background circle */}
            <circle
              cx="70"
              cy="70"
              r={radius}
              fill="none"
              stroke="#1e293b"
              strokeWidth="10"
            />
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
            <span className="text-xs text-slate-400">/10</span>
          </div>
        </div>
        <p className={`text-sm font-medium mt-2 ${text}`}>{label}</p>
        <p className="text-xs text-slate-500 mt-1">Based on recent behavior</p>
      </CardContent>
    </Card>
  );
}
