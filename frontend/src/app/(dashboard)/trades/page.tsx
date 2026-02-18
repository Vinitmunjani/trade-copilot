"use client";

import React, { useState } from "react";
import { TradeFilters } from "@/components/trades/trade-filters";
import { TradeTable } from "@/components/trades/trade-table";
import { EmptyState } from "@/components/common/empty-state";
import { useTradesStore } from "@/stores/trades-store";
import { BarChart3 } from "lucide-react";
import type { TradeFilters as TradeFiltersType } from "@/types";

export default function TradesPage() {
  const { trades } = useTradesStore();
  const [filteredTrades, setFilteredTrades] = useState(trades);

  const handleFilterChange = (filters: TradeFiltersType) => {
    let filtered = [...trades];

    // Apply filters
    if (filters.date_from) {
      filtered = filtered.filter(
        (trade) => new Date(trade.opened_at) >= new Date(filters.date_from!)
      );
    }
    if (filters.date_to) {
      filtered = filtered.filter(
        (trade) => new Date(trade.opened_at) <= new Date(filters.date_to!)
      );
    }
    if (filters.symbol && filters.symbol.length > 0) {
      filtered = filtered.filter((trade) => filters.symbol!.includes(trade.symbol));
    }
    if (filters.direction) {
      filtered = filtered.filter((trade) => trade.direction === filters.direction);
    }
    if (filters.score_min !== undefined) {
      filtered = filtered.filter(
        (trade) => (trade.ai_score?.score || 0) >= filters.score_min!
      );
    }
    if (filters.score_max !== undefined) {
      filtered = filtered.filter(
        (trade) => (trade.ai_score?.score || 0) <= filters.score_max!
      );
    }

    setFilteredTrades(filtered);
  };

  React.useEffect(() => {
    setFilteredTrades(trades);
  }, [trades]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-100">Trade History</h1>
        <p className="text-slate-400 mt-1">
          Review and analyze your trading performance
        </p>
      </div>

      {/* Filters */}
      <TradeFilters onFilterChange={handleFilterChange} />

      {/* Trade Table */}
      {filteredTrades.length > 0 ? (
        <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
          <TradeTable trades={filteredTrades} />
        </div>
      ) : (
        <EmptyState
          icon={BarChart3}
          title="No trades found"
          description="Try adjusting your filters or start trading to see your history here."
        />
      )}

      {/* Summary */}
      {filteredTrades.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
            <p className="text-2xl font-bold text-slate-100">{filteredTrades.length}</p>
            <p className="text-xs text-slate-400">Total Trades</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
            <p className="text-2xl font-bold text-emerald-400">
              {filteredTrades.filter((t) => (t.pnl || 0) > 0).length}
            </p>
            <p className="text-xs text-slate-400">Winners</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
            <p className="text-2xl font-bold text-red-400">
              {filteredTrades.filter((t) => (t.pnl || 0) < 0).length}
            </p>
            <p className="text-xs text-slate-400">Losers</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
            <p className="text-2xl font-bold text-slate-100">
              {(
                (filteredTrades.filter((t) => (t.pnl || 0) > 0).length /
                  filteredTrades.length) *
                100
              ).toFixed(1)}%
            </p>
            <p className="text-xs text-slate-400">Win Rate</p>
          </div>
        </div>
      )}
    </div>
  );
}
