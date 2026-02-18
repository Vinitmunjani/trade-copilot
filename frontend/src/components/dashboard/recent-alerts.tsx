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
};

const severityStyles: Record<string, string> = {
  low: "border-amber-500/20 bg-amber-500/5",
  medium: "border-orange-500/20 bg-orange-500/5",
  high: "border-red-500/20 bg-red-500/5",
};

const severityIcon: Record<string, string> = {
  low: "text-amber-400",
  medium: "text-orange-400",
  high: "text-red-400",
};

interface RecentAlertsProps {
  alerts: BehavioralAlert[];
}

export function RecentAlerts({ alerts }: RecentAlertsProps) {
  const recentAlerts = alerts.slice(0, 5);

  if (recentAlerts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-slate-400">
            <AlertTriangle className="h-8 w-8 mb-2 text-slate-600" />
            <p className="text-sm">No alerts</p>
            <p className="text-xs mt-1">You&apos;re trading clean!</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          Recent Alerts
          <span className="text-xs font-normal text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full">
            {alerts.filter((a) => !a.acknowledged).length} new
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {recentAlerts.map((alert) => {
          const Icon = iconMap[alert.pattern_type] || AlertTriangle;
          return (
            <div
              key={alert.id}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg border transition-colors",
                severityStyles[alert.severity],
                alert.acknowledged && "opacity-60"
              )}
            >
              <div
                className={cn(
                  "h-8 w-8 rounded-full flex items-center justify-center shrink-0 bg-slate-800/50",
                  severityIcon[alert.severity]
                )}
              >
                <Icon className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-200">
                  {PATTERN_LABELS[alert.pattern_type] || alert.pattern_type}
                </p>
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">
                  {alert.message}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {formatRelativeTime(alert.created_at)}
                </p>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
