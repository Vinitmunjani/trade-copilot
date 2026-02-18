"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AiScoreBadge } from "./ai-score-badge";
import { Badge } from "@/components/ui/badge";
import { ArrowUpRight, ArrowDownRight, ArrowUpDown, AlertTriangle } from "lucide-react";
import {
  formatDate,
  formatPrice,
  formatCurrency,
  formatR,
  formatDuration,
  cn,
} from "@/lib/utils";
import { PATTERN_LABELS } from "@/lib/constants";
import type { Trade } from "@/types";

interface TradeTableProps {
  trades: Trade[];
}

type SortKey =
  | "opened_at"
  | "symbol"
  | "direction"
  | "entry_price"
  | "exit_price"
  | "pnl"
  | "pnl_r"
  | "duration_minutes"
  | "ai_score";

export function TradeTable({ trades }: TradeTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("opened_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortOrder("desc");
    }
  };

  const sortedTrades = useMemo(() => {
    return [...trades].sort((a, b) => {
      let aVal: number | string = 0;
      let bVal: number | string = 0;

      switch (sortKey) {
        case "opened_at":
          aVal = new Date(a.opened_at).getTime();
          bVal = new Date(b.opened_at).getTime();
          break;
        case "symbol":
          aVal = a.symbol;
          bVal = b.symbol;
          break;
        case "direction":
          aVal = a.direction;
          bVal = b.direction;
          break;
        case "entry_price":
          aVal = a.entry_price;
          bVal = b.entry_price;
          break;
        case "exit_price":
          aVal = a.exit_price ?? 0;
          bVal = b.exit_price ?? 0;
          break;
        case "pnl":
          aVal = a.pnl ?? 0;
          bVal = b.pnl ?? 0;
          break;
        case "pnl_r":
          aVal = a.pnl_r ?? 0;
          bVal = b.pnl_r ?? 0;
          break;
        case "duration_minutes":
          aVal = a.duration_minutes ?? 0;
          bVal = b.duration_minutes ?? 0;
          break;
        case "ai_score":
          aVal = a.ai_score?.score ?? 0;
          bVal = b.ai_score?.score ?? 0;
          break;
      }

      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortOrder === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return sortOrder === "asc"
        ? (aVal as number) - (bVal as number)
        : (bVal as number) - (aVal as number);
    });
  }, [trades, sortKey, sortOrder]);

  const SortHeader = ({
    label,
    field,
  }: {
    label: string;
    field: SortKey;
  }) => (
    <TableHead
      className="cursor-pointer hover:text-slate-200 select-none"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {label}
        <ArrowUpDown
          className={cn(
            "h-3 w-3",
            sortKey === field ? "text-emerald-400" : "text-slate-600"
          )}
        />
      </div>
    </TableHead>
  );

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <SortHeader label="Date" field="opened_at" />
          <SortHeader label="Symbol" field="symbol" />
          <SortHeader label="Direction" field="direction" />
          <SortHeader label="Entry" field="entry_price" />
          <SortHeader label="Exit" field="exit_price" />
          <SortHeader label="P&L ($)" field="pnl" />
          <SortHeader label="P&L (R)" field="pnl_r" />
          <SortHeader label="Duration" field="duration_minutes" />
          <SortHeader label="AI Score" field="ai_score" />
          <TableHead>Flags</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedTrades.map((trade) => (
          <TableRow key={trade.id} className="group">
            <TableCell className="text-slate-300 text-xs">
              <Link
                href={`/trades/${trade.id}`}
                className="hover:text-emerald-400 transition-colors"
              >
                {formatDate(trade.opened_at, "MMM dd HH:mm")}
              </Link>
            </TableCell>
            <TableCell className="font-semibold text-slate-100">
              {trade.symbol}
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-1">
                {trade.direction === "BUY" ? (
                  <ArrowUpRight className="h-3.5 w-3.5 text-emerald-400" />
                ) : (
                  <ArrowDownRight className="h-3.5 w-3.5 text-red-400" />
                )}
                <span
                  className={
                    trade.direction === "BUY"
                      ? "text-emerald-400 text-xs font-medium"
                      : "text-red-400 text-xs font-medium"
                  }
                >
                  {trade.direction}
                </span>
              </div>
            </TableCell>
            <TableCell className="text-slate-300 font-mono text-xs">
              {formatPrice(trade.entry_price)}
            </TableCell>
            <TableCell className="text-slate-300 font-mono text-xs">
              {trade.exit_price ? formatPrice(trade.exit_price) : "—"}
            </TableCell>
            <TableCell
              className={cn(
                "font-semibold",
                (trade.pnl ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
              )}
            >
              {trade.pnl !== null ? formatCurrency(trade.pnl) : "—"}
            </TableCell>
            <TableCell
              className={cn(
                "font-mono text-xs",
                (trade.pnl_r ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
              )}
            >
              {formatR(trade.pnl_r)}
            </TableCell>
            <TableCell className="text-slate-400 text-xs">
              {formatDuration(trade.duration_minutes)}
            </TableCell>
            <TableCell>
              {trade.ai_score ? (
                <AiScoreBadge score={trade.ai_score.score} />
              ) : (
                <span className="text-slate-600 text-xs">—</span>
              )}
            </TableCell>
            <TableCell>
              {trade.flags.length > 0 ? (
                <div className="flex items-center gap-1">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                  <div className="flex gap-1">
                    {trade.flags.slice(0, 2).map((flag, i) => (
                      <Badge key={i} variant="warning" className="text-[10px] px-1.5 py-0">
                        {PATTERN_LABELS[flag.type] || flag.type}
                      </Badge>
                    ))}
                    {trade.flags.length > 2 && (
                      <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                        +{trade.flags.length - 2}
                      </Badge>
                    )}
                  </div>
                </div>
              ) : (
                <span className="text-slate-600 text-xs">Clean</span>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
