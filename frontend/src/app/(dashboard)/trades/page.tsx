"use client";

import React, { useState, useEffect } from "react";
import { TradeFilters } from "@/components/trades/trade-filters";
import { TradeTable } from "@/components/trades/trade-table";
import { TradeJournal } from "@/components/trades/trade-journal";
import { EmptyState } from "@/components/common/empty-state";
import { useTradesStore } from "@/stores/trades-store";
import { BarChart3, AlertCircle, BookOpen, History } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import type { TradeFilters as TradeFiltersType } from "@/types";
import api from "@/lib/api";

export default function TradesPage() {
  const { trades, fetchTrades } = useTradesStore();
  const [filteredTrades, setFilteredTrades] = useState(trades);
  const [analyticsReadiness, setAnalyticsReadiness] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch trades and analytics readiness on page load
  React.useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        await fetchTrades();
        // Fetch analytics readiness
        try {
          const { data } = await api.get("/analysis/readiness");
          setAnalyticsReadiness(data);
        } catch (error) {
          console.warn("Analytics readiness unavailable", error);
        }
      } catch (err) {
        console.error("Error fetching data:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [fetchTrades]);

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
        (trade) => (trade.ai_score || 0) >= filters.score_min!
      );
    }
    if (filters.score_max !== undefined) {
      filtered = filtered.filter(
        (trade) => (trade.ai_score || 0) <= filters.score_max!
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

      {/* Analytics Readiness Alert */}
      {analyticsReadiness && !analyticsReadiness.has_enough_history && (
        <Card className="border-yellow-900/50 bg-yellow-900/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-yellow-300">Not Enough History for Analytics</h3>
                <p className="text-sm text-yellow-200 mt-1">
                  {analyticsReadiness.message}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analytics Ready Alert */}
      {analyticsReadiness && analyticsReadiness.has_enough_history && trades.length > 0 && (
        <Card className="border-emerald-900/50 bg-emerald-900/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-emerald-500 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-emerald-300">✓ Analytics Available</h3>
                <p className="text-sm text-emerald-200 mt-1">
                  You have {analyticsReadiness.total_closed_trades} closed trades. Analytics is now available with full insights and pattern analysis.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs: History / Journal */}
      <Tabs defaultValue="history" className="space-y-4">
        <TabsList>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            History
          </TabsTrigger>
          <TabsTrigger value="journal" className="flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            Journal
          </TabsTrigger>
        </TabsList>

        {/* ── History tab ── */}
        <TabsContent value="history" className="space-y-4 mt-0">
          {/* Filters */}
          <TradeFilters onFilterChange={handleFilterChange} />

          {/* Trade Table */}
          {filteredTrades.length > 0 ? (
            <div className="bg-surface rounded-lg border border-white/5 overflow-hidden">
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
              <div className="p-4 rounded-lg bg-surface border border-white/5">
                <p className="text-2xl font-bold text-foreground">{filteredTrades.length}</p>
                <p className="text-xs text-muted">Total Trades</p>
              </div>
              <div className="p-4 rounded-lg bg-surface border border-white/5">
                <p className="text-2xl font-bold text-emerald-400">
                  {filteredTrades.filter((t) => (t.pnl || 0) > 0).length}
                </p>
                <p className="text-xs text-muted">Winners</p>
              </div>
              <div className="p-4 rounded-lg bg-surface border border-white/5">
                <p className="text-2xl font-bold text-red-400">
                  {filteredTrades.filter((t) => (t.pnl || 0) < 0).length}
                </p>
                <p className="text-xs text-muted">Losers</p>
              </div>
              <div className="p-4 rounded-lg bg-surface border border-white/5">
                <p className="text-2xl font-bold text-foreground">
                  {filteredTrades.length > 0
                    ? (
                        (filteredTrades.filter((t) => (t.pnl || 0) > 0).length /
                          filteredTrades.length) *
                        100
                      ).toFixed(1)
                    : "0.0"}%
                </p>
                <p className="text-xs text-muted">Win Rate</p>
              </div>
            </div>
          )}
        </TabsContent>

        {/* ── Journal tab ── */}
        <TabsContent value="journal" className="mt-0">
          <TradeJournal trades={trades} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
