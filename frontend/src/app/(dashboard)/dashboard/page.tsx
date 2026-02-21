"use client";

import React from "react";
import { PnlCard } from "@/components/dashboard/pnl-card";
import { QuickStats } from "@/components/dashboard/quick-stats";
import { OpenTrades } from "@/components/dashboard/open-trades";
import { ReadinessScore } from "@/components/dashboard/readiness-score";
import { RecentAlerts } from "@/components/dashboard/recent-alerts";
import { AccountStatus } from "@/components/dashboard/account-status";
import { useTradesStore } from "@/stores/trades-store";
import { useAlertsStore } from "@/stores/alerts-store";

export default function DashboardPage() {
  const { openTrades } = useTradesStore();
  const { alerts } = useAlertsStore();

  // Calculate today's P&L from open trades (mock data)
  const todayPnl = openTrades.reduce((sum, trade) => sum + (trade.pnl || 0), 0);
  const todayPnlR = openTrades.reduce((sum, trade) => sum + (trade.pnl_r || 0), 0);

  // Mock stats data - in real app, these would come from a dedicated stats store/API
  const mockStats = {
    tradesToday: 4,
    winRate: 72.5,
    avgR: 1.34,
    ruleAdherence: 85.2,
    readinessScore: 8,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-100">Dashboard</h1>
        <p className="text-slate-400 mt-1">Your trading performance overview</p>
      </div>

      {/* Account Status */}
      <AccountStatus />

      {/* Top Row - P&L and Readiness */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PnlCard pnl={todayPnl} pnlR={todayPnlR} />
        </div>
        <ReadinessScore score={mockStats.readinessScore} />
      </div>

      {/* Quick Stats */}
      <QuickStats
        tradesToday={mockStats.tradesToday}
        winRate={mockStats.winRate}
        avgR={mockStats.avgR}
        ruleAdherence={mockStats.ruleAdherence}
      />

      {/* Bottom Row - Open Trades and Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <OpenTrades trades={openTrades} />
        </div>
        <RecentAlerts alerts={alerts} />
      </div>
    </div>
  );
}
