"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Shield } from "lucide-react";

// Mock data for the last 30 days
const mockData = [
  { date: "Jan 1", followed: 85, broken: 45, followedWinRate: 80, brokenWinRate: 30 },
  { date: "Jan 2", followed: 90, broken: 35, followedWinRate: 85, brokenWinRate: 25 },
  { date: "Jan 3", followed: 75, broken: 50, followedWinRate: 75, brokenWinRate: 40 },
  { date: "Jan 4", followed: 95, broken: 25, followedWinRate: 90, brokenWinRate: 20 },
  { date: "Jan 5", followed: 80, broken: 45, followedWinRate: 70, brokenWinRate: 35 },
  { date: "Jan 6", followed: 85, broken: 40, followedWinRate: 82, brokenWinRate: 28 },
  { date: "Jan 7", followed: 70, broken: 55, followedWinRate: 65, brokenWinRate: 45 },
  { date: "Jan 8", followed: 90, broken: 30, followedWinRate: 88, brokenWinRate: 22 },
  { date: "Jan 9", followed: 85, broken: 40, followedWinRate: 80, brokenWinRate: 30 },
  { date: "Jan 10", followed: 92, broken: 28, followedWinRate: 85, brokenWinRate: 25 },
  { date: "Jan 11", followed: 78, broken: 48, followedWinRate: 72, brokenWinRate: 38 },
  { date: "Jan 12", followed: 88, broken: 35, followedWinRate: 84, brokenWinRate: 28 },
  { date: "Jan 13", followed: 82, broken: 42, followedWinRate: 78, brokenWinRate: 32 },
  { date: "Jan 14", followed: 94, broken: 26, followedWinRate: 90, brokenWinRate: 20 },
  { date: "Jan 15", followed: 86, broken: 38, followedWinRate: 82, brokenWinRate: 30 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm">
        <p className="font-semibold text-slate-200 mb-2">{label}</p>
        <div className="space-y-1">
          <p className="text-emerald-400">
            Rules Followed: {data.followed}% (Win Rate: {data.followedWinRate}%)
          </p>
          <p className="text-red-400">
            Rules Broken: {data.broken}% (Win Rate: {data.brokenWinRate}%)
          </p>
        </div>
      </div>
    );
  }
  return null;
};

export function AdherenceChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Shield className="h-4 w-4 text-emerald-400" />
          Rule Adherence Performance
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={mockData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="date"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
                axisLine={{ stroke: "#334155" }}
                tickLine={{ stroke: "#334155" }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                axisLine={{ stroke: "#334155" }}
                tickLine={{ stroke: "#334155" }}
                tickFormatter={(v) => `${v}%`}
                label={{
                  value: "Win Rate (%)",
                  angle: -90,
                  position: "insideLeft",
                  style: { textAnchor: "middle", fill: "#94a3b8", fontSize: "12px" },
                }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{
                  paddingTop: "20px",
                  fontSize: "12px",
                  color: "#94a3b8",
                }}
              />
              <Bar
                dataKey="followedWinRate"
                name="Win Rate (Rules Followed)"
                fill="#10b981"
                radius={[2, 2, 0, 0]}
                opacity={0.8}
              />
              <Bar
                dataKey="brokenWinRate"
                name="Win Rate (Rules Broken)"
                fill="#ef4444"
                radius={[2, 2, 0, 0]}
                opacity={0.8}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Summary */}
        <div className="mt-4 grid grid-cols-2 gap-4 text-center">
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <p className="text-2xl font-bold text-emerald-400">83%</p>
            <p className="text-xs text-emerald-400/70">Avg Win Rate (Rules Followed)</p>
          </div>
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
            <p className="text-2xl font-bold text-red-400">31%</p>
            <p className="text-xs text-red-400/70">Avg Win Rate (Rules Broken)</p>
          </div>
        </div>

        <p className="text-xs text-slate-400 text-center mt-3">
          Following your trading rules improves win rate by an average of 52%
        </p>
      </CardContent>
    </Card>
  );
}
