"use client";

import React from "react";
import { RulesEditor } from "@/components/rules/rules-editor";
import { ChecklistBuilder } from "@/components/rules/checklist-builder";
import { AdherenceChart } from "@/components/rules/adherence-chart";

export default function RulesPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-100">Trading Rules</h1>
        <p className="text-slate-400 mt-1">
          Define and track your trading rules to maintain discipline
        </p>
      </div>

      {/* Rules and Checklist - Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RulesEditor />
        <ChecklistBuilder />
      </div>

      {/* Adherence Chart - Full Width */}
      <AdherenceChart />

      {/* Tips */}
      <div className="bg-gradient-to-r from-emerald-900/20 to-emerald-800/20 border border-emerald-500/20 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-emerald-400 mb-3 flex items-center gap-2">
          💡 Rule Management Tips
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-300">
          <div>
            <h4 className="font-medium text-slate-200 mb-2">Risk Management</h4>
            <ul className="space-y-1 text-xs">
              <li>• Keep risk per trade under 2% of account</li>
              <li>• Maintain minimum 2:1 risk-reward ratio</li>
              <li>• Set daily loss limits to protect capital</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-slate-200 mb-2">Pre-Trade Checklist</h4>
            <ul className="space-y-1 text-xs">
              <li>• Include both technical and fundamental checks</li>
              <li>• Mark critical items as "required"</li>
              <li>• Review and update checklist monthly</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
