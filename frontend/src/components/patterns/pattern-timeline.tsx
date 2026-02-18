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
};

// Mock pattern timeline data
const mockPatterns: BehavioralAlert[] = [
  {
    id: "p1",
    trade_id: "t2",
    pattern_type: "fomo_entry",
    message: "Entered GBPJPY after 40-pip move without waiting for pullback",
    severity: "medium",
    created_at: new Date(Date.now() - 1800000).toISOString(),
    acknowledged: false,
  },
  {
    id: "p2",
    trade_id: null,
    pattern_type: "overtrading",
    message: "4th trade opened today - approaching daily limit",
    severity: "low",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    acknowledged: false,
  },
  {
    id: "p3",
    trade_id: "t4",
    pattern_type: "revenge_trading",
    message: "Quick re-entry after USDJPY loss - possible revenge trade",
    severity: "high",
    created_at: new Date(Date.now() - 7200000).toISOString(),
    acknowledged: true,
  },
  {
    id: "p4",
    trade_id: "t6",
    pattern_type: "early_exit",
    message: "GBPUSD closed 25 pips before target - 3rd time this week",
    severity: "low",
    created_at: new Date(Date.now() - 86400000).toISOString(),
    acknowledged: true,
  },
  {
    id: "p5",
    trade_id: "t8",
    pattern_type: "session_violation",
    message: "Trade opened during Tokyo session - outside preferred sessions",
    severity: "medium",
    created_at: new Date(Date.now() - 172800000).toISOString(),
    acknowledged: true,
  },
  {
    id: "p6",
    trade_id: "t10",
    pattern_type: "moved_stop_loss",
    message: "Stop loss moved further from entry on XAUUSD",
    severity: "high",
    created_at: new Date(Date.now() - 259200000).toISOString(),
    acknowledged: true,
  },
  {
    id: "p7",
    trade_id: "t12",
    pattern_type: "ignored_rules",
    message: "Checklist not completed before EURUSD entry",
    severity: "medium",
    created_at: new Date(Date.now() - 345600000).toISOString(),
    acknowledged: true,
  },
];

interface PatternTimelineProps {
  patterns?: BehavioralAlert[];
}

export function PatternTimeline({ patterns = mockPatterns }: PatternTimelineProps) {
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
