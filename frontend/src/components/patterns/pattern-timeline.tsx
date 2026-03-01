"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
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
} from "lucide-react";
import { formatRelativeTime, formatDate, getSeverityColor } from "@/lib/utils";
import { PATTERN_LABELS } from "@/lib/constants";
import type { BehavioralAlert } from "@/types";

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


interface PatternTimelineProps {
  patterns?: BehavioralAlert[];
}

export function PatternTimeline({ patterns = [] }: PatternTimelineProps) {
  if (!patterns || patterns.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            Pattern Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-12 text-center text-slate-400">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4" />
            <p className="text-lg">No pattern alerts yet</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
          Pattern Timeline
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {patterns.map((pattern, index) => {
            const Icon = iconMap[pattern.pattern_type] || AlertTriangle;
            const isLast = index === patterns.length - 1;

            return (
              <div key={pattern.id} className="relative">
                {/* Vertical line */}
                {!isLast && (
                  <div className="absolute left-6 top-12 bottom-0 w-px bg-slate-700" />
                )}

                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div
                    className={`h-12 w-12 rounded-full border-2 bg-slate-900 flex items-center justify-center shrink-0 ${
                      pattern.severity === "high"
                        ? "border-red-500/50 text-red-400"
                        : pattern.severity === "medium"
                        ? "border-amber-500/50 text-amber-400"
                        : "border-slate-600 text-slate-400"
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 pb-4">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-slate-200">
                            {PATTERN_LABELS[pattern.pattern_type] || pattern.pattern_type}
                          </h4>
                          <Badge
                            variant={
                              pattern.severity === "high"
                                ? "destructive"
                                : pattern.severity === "medium"
                                ? "warning"
                                : "secondary"
                            }
                            className="text-[10px]"
                          >
                            {pattern.severity}
                          </Badge>
                          {!pattern.acknowledged && (
                            <Badge variant="default" className="text-[10px]">
                              New
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-slate-400 mb-2">
                          {pattern.message}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          <span>{formatRelativeTime(pattern.created_at)}</span>
                          <span>•</span>
                          <span>{formatDate(pattern.created_at, "MMM dd, HH:mm")}</span>
                          {pattern.trade_id && (
                            <>
                              <span>•</span>
                              <Link
                                href={`/trades/${pattern.trade_id}`}
                                className="text-emerald-400 hover:text-emerald-300 transition-colors"
                              >
                                View Trade
                              </Link>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {patterns.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-slate-400">
            <AlertTriangle className="h-12 w-12 mb-4 text-slate-600" />
            <p className="text-lg font-semibold">No Patterns Detected</p>
            <p className="text-sm mt-1">Keep up the good trading habits!</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
