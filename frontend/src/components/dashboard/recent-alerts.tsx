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
} from "lucide-react";
import { formatRelativeTime, cn } from "@/lib/utils";
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

const severityStyles: Record<string, string> = {
  low: "border-amber-300/30 bg-amber-300/10",
  medium: "border-orange-400/30 bg-orange-400/10",
  high: "border-danger/30 bg-danger/10",
};

const severityIcon: Record<string, string> = {
  low: "text-amber-200",
  medium: "text-orange-200",
  high: "text-danger",
};

interface RecentAlertsProps {
  alerts: BehavioralAlert[];
}

export function RecentAlerts({ alerts }: RecentAlertsProps) {
  const recentAlerts = alerts.slice(0, 5);

  if (recentAlerts.length === 0) {
    return (
      <Card className="border-white/5">
        <CardHeader>
          <CardTitle className="text-base">Recent Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-muted">
            <AlertTriangle className="mb-2 h-8 w-8 text-foreground/30" />
            <p className="text-sm">No alerts</p>
            <p className="text-xs mt-1">You&apos;re trading clean!</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-white/5">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          Recent Alerts
          <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs font-normal text-amber-200">
            {alerts.filter((a) => !a.acknowledged).length} new
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {recentAlerts.map((alert) => {
          const Icon = iconMap[alert.pattern_type] || AlertTriangle;
          return (
            <div
              key={alert.id}
              className={cn(
                "flex items-start gap-3 rounded-2xl border px-4 py-3 transition",
                severityStyles[alert.severity],
                alert.acknowledged && "opacity-60"
              )}
            >
              <div
                className={cn(
                  "flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/5",
                  severityIcon[alert.severity]
                )}
              >
                <Icon className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">
                  {PATTERN_LABELS[alert.pattern_type] || alert.pattern_type}
                </p>
                <p className="mt-0.5 text-xs text-muted line-clamp-2">{alert.message}</p>
                <p className="mt-1 text-xs text-muted">{formatRelativeTime(alert.created_at)}</p>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
