"use client";

import React from "react";
import { PnlCard } from "@/components/dashboard/pnl-card";
import { QuickStats } from "@/components/dashboard/quick-stats";
import { OpenTrades } from "@/components/dashboard/open-trades";
import { ReadinessScore } from "@/components/dashboard/readiness-score";
import { RecentAlerts } from "@/components/dashboard/recent-alerts";
import { AccountStatus } from "@/components/dashboard/account-status";
import { LossLockout } from "@/components/dashboard/loss-lockout";
import { PatternCost } from "@/components/dashboard/pattern-cost";
import { EdgeFinder } from "@/components/dashboard/edge-finder";
import { PositionSizer } from "@/components/dashboard/position-sizer";
import { useTradesStore } from "@/stores/trades-store";
import { useAlertsStore } from "@/stores/alerts-store";
import { useDailyStats } from "@/hooks/use-daily-stats";
import { useReadiness } from "@/hooks/use-readiness";

export default function DashboardPage() {
  const { openTrades, fetchOpenTrades, fetchTrades } = useTradesStore();
  const { alerts } = useAlertsStore();
  const { tradesToday, winRate, avgR, todayPnl: statsPnl, todayPnlR: statsPnlR, adherence, isLoading: statsLoading } = useDailyStats();
  const { readinessScore, isLoading: readinessLoading } = useReadiness();

  React.useEffect(() => {
    fetchOpenTrades();
    fetchTrades(); // needed for PatternCost, EdgeFinder, PositionSizer, LossLockout
  }, [fetchOpenTrades, fetchTrades]);

  // Realised P&L comes from the stats API (closed trades only).
  // We intentionally do NOT add open-trade pnl from the DB here because those
  // values are unreliable: MetaAPI stores the last-known floating unrealised P&L
  // in the trade record, which can contain stale or incorrect prices.
  const displayPnl = statsLoading ? 0 : statsPnl;
  const displayPnlR = statsLoading ? 0 : statsPnlR;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <p className="text-xs uppercase tracking-[0.4em] text-muted">Mission overview</p>
        <h1 className="mt-2 text-3xl font-semibold text-foreground">Dashboard</h1>
      </div>

      {/* Account Status */}
      <AccountStatus />

      {/* Loss Lockout — capital protection banner */}
      <LossLockout />

      {/* Top Row - P&L and Readiness */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PnlCard pnl={displayPnl} pnlR={displayPnlR} tradesCount={statsLoading ? undefined : tradesToday} />
        </div>
        <ReadinessScore score={readinessLoading ? 0 : readinessScore} />
      </div>

      {/* Quick Stats */}
      <QuickStats
        tradesToday={statsLoading ? 0 : tradesToday}
        winRate={statsLoading ? 0 : winRate}
        avgR={statsLoading ? 0 : avgR}
        ruleAdherence={statsLoading ? 0 : adherence}
      />

      {/* Bottom Row - Open Trades and Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <OpenTrades trades={openTrades} />
        </div>
        <RecentAlerts alerts={alerts} />
      </div>

      {/* Intelligence Row — Edge, Pattern Cost, Position Sizer */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <EdgeFinder />
        <PatternCost />
        <PositionSizer />
      </div>
    </div>
  );
}
