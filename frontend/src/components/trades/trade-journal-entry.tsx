"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AiScoreBadge } from "./ai-score-badge";
import { AiAnalysisCard } from "./ai-analysis-card";
import { PostTradeReviewCard } from "./post-trade-review-card";
import {
  ArrowUpRight,
  ArrowDownRight,
  ChevronDown,
  ChevronUp,
  Clock,
  Shield,
  AlertTriangle,
  Brain,
  ClipboardCheck,
  ExternalLink,
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

interface TradeJournalEntryProps {
  trade: Trade;
  defaultOpen?: boolean;
}

export function TradeJournalEntry({ trade, defaultOpen = false }: TradeJournalEntryProps) {
  const [open, setOpen] = useState(defaultOpen);

  const isBuy = trade.direction === "BUY";
  const isClosed = trade.status === "closed" || trade.status === "CLOSED";
  const pnl = trade.pnl ?? null;
  const sessionLabel = SESSIONS.find((s) => s.value === trade.session)?.label ?? trade.session ?? "—";
  const flags = trade.flags ?? trade.behavioral_flags ?? [];

  return (
    <Card
      className={cn(
        "border transition-colors",
        open ? "border-border" : "border-white/5 hover:border-border"
      )}
    >
      {/* ── Clickable header row ── */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full text-left px-5 py-4 focus:outline-none"
      >
        <div className="flex flex-wrap items-center gap-3">
          {/* Direction icon */}
          <div
            className={cn(
              "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
              isBuy ? "bg-emerald-500/10" : "bg-red-500/10"
            )}
          >
            {isBuy ? (
              <ArrowUpRight className="h-4 w-4 text-emerald-400" />
            ) : (
              <ArrowDownRight className="h-4 w-4 text-red-400" />
            )}
          </div>

          {/* Symbol + direction */}
          <div className="min-w-[90px]">
            <p className="text-sm font-bold text-slate-100">{trade.symbol}</p>
            <p
              className={cn(
                "text-xs font-semibold",
                isBuy ? "text-emerald-400" : "text-red-400"
              )}
            >
              {trade.direction}
            </p>
          </div>

          {/* Date */}
          <div className="min-w-[130px] hidden sm:block">
            <p className="text-xs text-slate-400">Opened</p>
            <p className="text-sm text-slate-300">{formatDate(trade.opened_at)}</p>
          </div>

          {/* Duration */}
          <div className="min-w-[80px] hidden md:block">
            <p className="text-xs text-slate-400">Duration</p>
            <p className="text-sm text-slate-300 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDuration(trade.duration_seconds ?? (trade.duration_minutes !== null ? (trade.duration_minutes ?? 0) * 60 : null))}
            </p>
          </div>

          {/* P&L */}
          <div className="min-w-[80px]">
            <p className="text-xs text-slate-400">P&amp;L</p>
            <p
              className={cn(
                "text-sm font-bold",
                pnl === null ? "text-slate-400" : pnl >= 0 ? "text-emerald-400" : "text-red-400"
              )}
            >
              {pnl !== null ? formatCurrency(pnl) : "Open"}
            </p>
            {trade.pnl_r !== null && (
              <p
                className={cn(
                  "text-xs",
                  (trade.pnl_r ?? 0) >= 0 ? "text-emerald-400/70" : "text-red-400/70"
                )}
              >
                {formatR(trade.pnl_r)}
              </p>
            )}
          </div>

          {/* AI Score */}
          {trade.ai_score !== null && (
            <div className="flex flex-col items-start gap-1">
              <p className="text-xs text-slate-400">AI Score</p>
              <AiScoreBadge score={trade.ai_score} size="sm" />
            </div>
          )}

          {/* Flags count */}
          {flags.length > 0 && (
            <div className="flex items-center gap-1 text-amber-400">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span className="text-xs font-medium">{flags.length}</span>
            </div>
          )}

          {/* Status */}
          <Badge
            variant={
              isClosed ? "secondary" : "default"
            }
            className="text-[11px] ml-auto hidden sm:inline-flex"
          >
            {isClosed ? "CLOSED" : "OPEN"}
          </Badge>

          {/* Expand chevron */}
          <span className="ml-1 text-slate-500">
            {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </span>
        </div>
      </button>

      {/* ── Expanded body ── */}
      {open && (
        <CardContent className="border-t border-white/5 px-5 pb-5 pt-4 space-y-5">
          {/* Trade metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            {[
              { label: "Entry", value: formatPrice(trade.entry_price), mono: true },
              {
                label: "Exit",
                value: trade.exit_price ? formatPrice(trade.exit_price) : "—",
                mono: true,
              },
              {
                label: "Stop Loss",
                value: (trade.stop_loss ?? trade.sl) != null
                  ? formatPrice(trade.stop_loss ?? trade.sl as number)
                  : "—",
                mono: true,
                cls: "text-red-400",
              },
              {
                label: "Take Profit",
                value: (trade.take_profit ?? trade.tp) != null
                  ? formatPrice(trade.take_profit ?? trade.tp as number)
                  : "—",
                mono: true,
                cls: "text-emerald-400",
              },
              { label: "Lot Size", value: `${trade.lot_size}` },
              { label: "Session", value: sessionLabel },
              {
                label: "Opened",
                value: formatDate(trade.opened_at),
              },
              {
                label: "Closed",
                value: trade.closed_at ? formatDate(trade.closed_at) : "—",
              },
            ].map(({ label, value, mono, cls }) => (
              <div key={label}>
                <p className="text-xs text-slate-400">{label}</p>
                <p className={cn("font-medium text-slate-100", mono && "font-mono", cls)}>
                  {value}
                </p>
              </div>
            ))}
          </div>

          {/* AI sections side-by-side on lg */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Pre-trade AI */}
            {trade.ai_analysis ? (
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Brain className="h-3 w-3 text-emerald-400" />
                  Pre-Trade Analysis
                </p>
                <AiAnalysisCard analysis={trade.ai_analysis} score={trade.ai_score ?? 0} />
              </div>
            ) : (
              <div className="rounded-lg border border-white/5 bg-surface/40 flex items-center justify-center py-8 text-muted text-sm">
                Pre-trade analysis pending…
              </div>
            )}

            {/* Post-trade review */}
            {trade.ai_review ? (
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <ClipboardCheck className="h-3 w-3 text-accent" />
                  Post-Trade Review
                </p>
                <PostTradeReviewCard review={trade.ai_review} />
              </div>
            ) : isClosed ? (
              <div className="rounded-lg border border-white/5 bg-surface/40 flex items-center justify-center py-8 text-muted text-sm">
                Post-trade review generating…
              </div>
            ) : (
              <div className="rounded-lg border border-white/5 bg-surface/40 flex items-center justify-center py-8 text-muted text-sm">
                Post-trade review available after close
              </div>
            )}
          </div>

          {/* Behavioral flags */}
          {flags.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                <AlertTriangle className="h-3 w-3 text-amber-400" />
                Behavioral Flags ({flags.length})
              </p>
              <div className="space-y-2">
                {flags.map((flag: any, i: number) => (
                  <div
                    key={i}
                    className={cn(
                      "flex items-start gap-3 p-2.5 rounded-lg border text-sm",
                      getSeverityColor(flag.severity)
                    )}
                  >
                    <Shield className="h-4 w-4 mt-0.5 shrink-0" />
                    <div>
                      <p className="font-medium">
                        {PATTERN_LABELS[flag.type ?? flag.flag] ?? (flag.type ?? flag.flag)}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">{flag.message}</p>
                    </div>
                    <Badge
                      variant={
                        flag.severity === "critical" || flag.severity === "high"
                          ? "destructive"
                          : "secondary"
                      }
                      className="text-[10px] ml-auto shrink-0"
                    >
                      {flag.severity}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Link to full detail */}
          <div className="pt-1">
            <Link
              href={`/trades/${trade.id}`}
              className="inline-flex items-center gap-1.5 text-xs text-muted hover:text-foreground transition-colors"
            >
              <ExternalLink className="h-3 w-3" />
              View full detail
            </Link>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
