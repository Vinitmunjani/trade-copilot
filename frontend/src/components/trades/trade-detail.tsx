"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AiAnalysisCard } from "./ai-analysis-card";
import { AiScoreBadge } from "./ai-score-badge";
import {
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Target,
  Shield,
  AlertTriangle,
  Calendar,
} from "lucide-react";
import {
  formatDate,
  formatPrice,
  formatCurrency,
  formatR,
  formatDuration,
  cn,
  getSeverityColor,
} from "@/lib/utils";
import { PATTERN_LABELS, SESSIONS } from "@/lib/constants";
import type { Trade } from "@/types";

interface TradeDetailProps {
  trade: Trade;
}

export function TradeDetail({ trade }: TradeDetailProps) {
  const sessionLabel =
    SESSIONS.find((s) => s.value === trade.session)?.label || trade.session;

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div
                className={cn(
                  "h-12 w-12 rounded-full flex items-center justify-center",
                  trade.direction === "BUY"
                    ? "bg-emerald-500/10"
                    : "bg-red-500/10"
                )}
              >
                {trade.direction === "BUY" ? (
                  <ArrowUpRight className="h-6 w-6 text-emerald-400" />
                ) : (
                  <ArrowDownRight className="h-6 w-6 text-red-400" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-bold text-slate-100">
                    {trade.symbol}
                  </h2>
                  <span
                    className={cn(
                      "text-sm font-semibold px-2 py-0.5 rounded",
                      trade.direction === "BUY"
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "bg-red-500/10 text-red-400"
                    )}
                  >
                    {trade.direction}
                  </span>
                  <Badge
                    variant={
                      trade.status === "open"
                        ? "default"
                        : trade.status === "closed"
                        ? "secondary"
                        : "destructive"
                    }
                  >
                    {trade.status.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-sm text-slate-400 mt-1">
                  {formatDate(trade.opened_at)} · {sessionLabel} Session ·{" "}
                  {trade.lot_size} lots
                </p>
              </div>
            </div>
            <div className="text-right">
              <p
                className={cn(
                  "text-3xl font-bold",
                  (trade.pnl ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                )}
              >
                {trade.pnl !== null ? formatCurrency(trade.pnl) : "Open"}
              </p>
              <p
                className={cn(
                  "text-lg",
                  (trade.pnl_r ?? 0) >= 0 ? "text-emerald-400/70" : "text-red-400/70"
                )}
              >
                {formatR(trade.pnl_r)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trade Metadata */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Calendar className="h-4 w-4 text-slate-400" />
              Trade Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-slate-400">Entry Price</p>
                  <p className="text-sm font-mono text-slate-100">
                    {formatPrice(trade.entry_price)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Stop Loss</p>
                  <p className="text-sm font-mono text-red-400">
                    {formatPrice(trade.stop_loss)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Opened</p>
                  <p className="text-sm text-slate-300">
                    {formatDate(trade.opened_at)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Session</p>
                  <p className="text-sm text-slate-300">{sessionLabel}</p>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-slate-400">Exit Price</p>
                  <p className="text-sm font-mono text-slate-100">
                    {trade.exit_price
                      ? formatPrice(trade.exit_price)
                      : "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Take Profit</p>
                  <p className="text-sm font-mono text-emerald-400">
                    {formatPrice(trade.take_profit)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Closed</p>
                  <p className="text-sm text-slate-300">
                    {trade.closed_at
                      ? formatDate(trade.closed_at)
                      : "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Duration</p>
                  <p className="text-sm text-slate-300 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDuration(trade.duration_minutes)}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Analysis */}
        {trade.ai_score ? (
          <AiAnalysisCard score={trade.ai_score} />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">AI Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-8 text-slate-400">
                <Target className="h-8 w-8 mb-2 text-slate-600" />
                <p className="text-sm">Analysis pending</p>
                <p className="text-xs mt-1">
                  AI review will be available after trade closes
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Behavioral Flags */}
      {trade.flags.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              Behavioral Flags ({trade.flags.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {trade.flags.map((flag, i) => (
              <div
                key={i}
                className={cn(
                  "flex items-start gap-3 p-3 rounded-lg border",
                  getSeverityColor(flag.severity)
                )}
              >
                <Shield className="h-4 w-4 mt-0.5 shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium">
                      {PATTERN_LABELS[flag.type] || flag.type}
                    </p>
                    <Badge
                      variant={
                        flag.severity === "high"
                          ? "destructive"
                          : flag.severity === "medium"
                          ? "warning"
                          : "secondary"
                      }
                      className="text-[10px]"
                    >
                      {flag.severity}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{flag.message}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Detected: {formatDate(flag.detected_at)}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
