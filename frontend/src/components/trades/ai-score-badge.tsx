"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface AiScoreBadgeProps {
  score: number;
  size?: "sm" | "lg";
  className?: string;
}

export function AiScoreBadge({ score, size = "sm", className }: AiScoreBadgeProps) {
  const bgColor =
    score <= 3
      ? "bg-red-500/20 text-red-400 border-red-500/30"
      : score <= 6
      ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
      : "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";

  return (
    <div
      className={cn(
        "inline-flex items-center justify-center rounded-md border font-bold",
        bgColor,
        size === "sm" ? "h-6 w-6 text-xs" : "h-12 w-12 text-xl",
        className
      )}
    >
      {score}
    </div>
  );
}
