"use client";

import React from "react";
import { EquityCurve } from "@/components/analytics/equity-curve";
import { WinRateChart } from "@/components/analytics/win-rate-chart";
import { RDistribution } from "@/components/analytics/r-distribution";
import { SessionHeatmap } from "@/components/analytics/session-heatmap";

export default function AnalyticsPage() {
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
      <EquityCurve />

      {/* Win Rate and R Distribution - Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WinRateChart />
        <RDistribution />
      </div>

      {/* Session Heatmap - Full Width */}
      <SessionHeatmap />

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 text-center">
          <div className="text-3xl font-bold text-emerald-400 mb-2">$1,350</div>
          <div className="text-sm text-slate-400">Total P&L</div>
          <div className="text-xs text-emerald-400 mt-1">+18.7% this month</div>
        </div>
        
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 text-center">
          <div className="text-3xl font-bold text-slate-100 mb-2">1.52R</div>
          <div className="text-sm text-slate-400">Average R Multiple</div>
          <div className="text-xs text-slate-400 mt-1">Across 74 trades</div>
        </div>
        
        <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 text-center">
          <div className="text-3xl font-bold text-slate-100 mb-2">67.6%</div>
          <div className="text-sm text-slate-400">Overall Win Rate</div>
          <div className="text-xs text-emerald-400 mt-1">Above 65% target</div>
        </div>
      </div>
    </div>
  );
}
