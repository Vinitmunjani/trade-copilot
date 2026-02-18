"use client";

import React from "react";
import { PatternStats } from "@/components/patterns/pattern-stats";
import { PatternTimeline } from "@/components/patterns/pattern-timeline";

export default function PatternsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-100">Behavioral Patterns</h1>
        <p className="text-slate-400 mt-1">
          Identify and track behavioral patterns affecting your trading
        </p>
      </div>

      {/* Pattern Statistics Cards */}
      <div>
        <h2 className="text-xl font-semibold text-slate-200 mb-4">Pattern Overview</h2>
        <PatternStats />
      </div>

      {/* Pattern Timeline */}
      <div>
        <h2 className="text-xl font-semibold text-slate-200 mb-4">Recent Activity</h2>
        <PatternTimeline />
      </div>

      {/* Insights Panel */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-3 flex items-center gap-2">
          💡 Key Insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="p-4 rounded-lg bg-slate-800/50">
            <h4 className="font-medium text-emerald-400 mb-2">Improvement Trend</h4>
            <p className="text-slate-300">
              Revenge trading incidents have decreased by 40% this month - great progress on emotional control!
            </p>
          </div>
          <div className="p-4 rounded-lg bg-slate-800/50">
            <h4 className="font-medium text-amber-400 mb-2">Watch Out</h4>
            <p className="text-slate-300">
              Early exit pattern is increasing. Consider using partial profit-taking instead of full exits.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
