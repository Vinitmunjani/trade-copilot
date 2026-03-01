"use client";

import React, { useEffect, useState } from "react";
import { EquityCurve } from "@/components/analytics/equity-curve";
import { WinRateChart } from "@/components/analytics/win-rate-chart";
import { RDistribution } from "@/components/analytics/r-distribution";
import { SessionHeatmap } from "@/components/analytics/session-heatmap";
import { useTradesStore } from "@/stores/trades-store";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import type { EquityCurvePoint, RDistributionBucket } from "@/types";

export default function AnalyticsPage() {
  const { trades, fetchTrades } = useTradesStore();
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [hasEnoughData, setHasEnoughData] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      setIsLoading(true);
      await fetchTrades();

      // Read from store state directly to avoid stale closure over `trades`
      const currentTrades = useTradesStore.getState().trades;
      const closedTrades = currentTrades.filter((t: any) => t.status === 'closed');
      if (closedTrades.length < 10) {
        setHasEnoughData(false);
        setIsLoading(false);
        return;
      }

      setHasEnoughData(true);
      
      // Calculate analytics from real trades
      const computed = computeAnalytics(closedTrades);
      setAnalyticsData(computed);
      setIsLoading(false);
    };

    loadAnalytics();
  }, []);

  const computeAnalytics = (closedTrades: any[]) => {
    // 1. Equity Curve (Cumulative P&L over time)
    const sortedByTime = [...closedTrades].sort(
      (a, b) => new Date(a.opened_at).getTime() - new Date(b.opened_at).getTime()
    );
    
    let cumulativePnL = 0;
    const equityCurve: EquityCurvePoint[] = sortedByTime.map((trade) => {
      cumulativePnL += trade.pnl || 0;
      return {
        date: new Date(trade.closed_at || trade.opened_at).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric'
        }),
        cumulative_pnl: Math.round(cumulativePnL * 100) / 100,
      };
    });

    // 2. Win Rate by Symbol
    const symbolStats: Record<string, { wins: number; losses: number; total: number }> = {};
    closedTrades.forEach((trade) => {
      if (!symbolStats[trade.symbol]) {
        symbolStats[trade.symbol] = { wins: 0, losses: 0, total: 0 };
      }
      symbolStats[trade.symbol].total++;
      if ((trade.pnl || 0) > 0) {
        symbolStats[trade.symbol].wins++;
      } else {
        symbolStats[trade.symbol].losses++;
      }
    });

    const symbolData = Object.entries(symbolStats)
      .map(([symbol, stats]) => ({
        name: symbol,
        winRate: Math.round((stats.wins / stats.total) * 100),
        lossRate: Math.round((stats.losses / stats.total) * 100),
        totalTrades: stats.total,
      }))
      .sort((a, b) => b.totalTrades - a.totalTrades)
      .slice(0, 5); // Top 5 symbols

    // 3. R Distribution
    const rValues = closedTrades
      .map((trade) => trade.pnl_r || 0)
      .sort((a, b) => a - b);

    const rDistribution: RDistributionBucket[] = [
      { range: "<-2R", count: 0, min_r: -5, max_r: -2 },
      { range: "-2 to -1R", count: 0, min_r: -2, max_r: -1 },
      { range: "-1 to 0R", count: 0, min_r: -1, max_r: 0 },
      { range: "0 to 1R", count: 0, min_r: 0, max_r: 1 },
      { range: "1 to 2R", count: 0, min_r: 1, max_r: 2 },
      { range: "2 to 3R", count: 0, min_r: 2, max_r: 3 },
      { range: ">3R", count: 0, min_r: 3, max_r: 5 },
    ];

    rValues.forEach((r) => {
      if (r < -2) rDistribution[0].count++;
      else if (r < -1) rDistribution[1].count++;
      else if (r < 0) rDistribution[2].count++;
      else if (r < 1) rDistribution[3].count++;
      else if (r < 2) rDistribution[4].count++;
      else if (r < 3) rDistribution[5].count++;
      else rDistribution[6].count++;
    });

    // 4. Summary Stats
    const totalPnL = closedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
    const winCount = closedTrades.filter((t) => (t.pnl || 0) > 0).length;
    const winRate = Math.round((winCount / closedTrades.length) * 100);
    const avgR =
      closedTrades.length > 0
        ? closedTrades.reduce((sum, t) => sum + (t.pnl_r || 0), 0) / closedTrades.length
        : 0;

    return {
      equityCurve,
      symbolData,
      rDistribution,
      totalPnL: Math.round(totalPnL * 100) / 100,
      avgR: Math.round(avgR * 100) / 100,
      winRate,
      totalTrades: closedTrades.length,
    };
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-100">Analytics</h1>
          <p className="text-slate-400 mt-1">
            Loading your trading analytics...
          </p>
        </div>
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

  if (!hasEnoughData) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-100">Analytics</h1>
          <p className="text-slate-400 mt-1">
            Deep insights into your trading performance and patterns
          </p>
        </div>

        <Card className="border-yellow-900/50 bg-yellow-900/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-yellow-300">Not Enough Trade History</h3>
                <p className="text-sm text-yellow-200 mt-1">
                  You need at least 10 closed trades to unlock analytics. Keep trading and come back soon!
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-100">Analytics</h1>
        <p className="text-slate-400 mt-1">
          Deep insights into your trading performance and patterns
        </p>
      </div>

      {/* Equity Curve - Full Width */}
      <EquityCurve data={analyticsData?.equityCurve} />

      {/* Win Rate and R Distribution - Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WinRateChart trades={trades.filter(t => t.status === 'closed')} data={analyticsData?.symbolData} />
        <RDistribution data={analyticsData?.rDistribution} />
      </div>

      {/* Session Heatmap - Full Width */}
      <SessionHeatmap trades={trades} />

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 text-center">
          <div className={`text-3xl font-bold mb-2 ${analyticsData?.totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            ${analyticsData?.totalPnL || 0}
          </div>
          <div className="text-sm text-slate-400">Total P&L</div>
          <div className={`text-xs mt-1 ${analyticsData?.totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            From {analyticsData?.totalTrades || 0} trades
          </div>
        </div>
        
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 text-center">
          <div className="text-3xl font-bold text-slate-100 mb-2">{analyticsData?.avgR || 0}R</div>
          <div className="text-sm text-slate-400">Average R Multiple</div>
          <div className="text-xs text-slate-400 mt-1">Per closed trade</div>
        </div>
        
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 text-center">
          <div className={`text-3xl font-bold mb-2 ${analyticsData?.winRate && analyticsData.winRate > 50 ? 'text-emerald-400' : 'text-red-400'}`}>
            {analyticsData?.winRate || 0}%
          </div>
          <div className="text-sm text-slate-400">Overall Win Rate</div>
          <div className={`text-xs mt-1 ${analyticsData?.winRate && analyticsData.winRate > 50 ? 'text-emerald-400' : 'text-red-400'}`}>
            {analyticsData?.winRate && analyticsData.winRate > 50 ? '✓ Above 50%' : 'Below 50%'}
          </div>
        </div>
      </div>
    </div>
  );
}