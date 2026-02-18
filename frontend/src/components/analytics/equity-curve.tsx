"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { EquityCurvePoint } from "@/types";

const mockData: EquityCurvePoint[] = [
  { date: "Jan 01", cumulative_pnl: 0 },
  { date: "Jan 02", cumulative_pnl: 120 },
  { date: "Jan 03", cumulative_pnl: 85 },
  { date: "Jan 04", cumulative_pnl: 220 },
  { date: "Jan 05", cumulative_pnl: 180 },
  { date: "Jan 06", cumulative_pnl: 340 },
  { date: "Jan 07", cumulative_pnl: 290 },
  { date: "Jan 08", cumulative_pnl: 445 },
  { date: "Jan 09", cumulative_pnl: 520 },
  { date: "Jan 10", cumulative_pnl: 480 },
  { date: "Jan 11", cumulative_pnl: 610 },
  { date: "Jan 12", cumulative_pnl: 575 },
  { date: "Jan 13", cumulative_pnl: 720 },
  { date: "Jan 14", cumulative_pnl: 885 },
  { date: "Jan 15", cumulative_pnl: 849 },
];

interface EquityCurveProps {
  data?: EquityCurvePoint[];
}

export function EquityCurve({ data = mockData }: EquityCurveProps) {
  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Equity Curve</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
            No data available yet
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Equity Curve</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="date"
              stroke="#475569"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <YAxis
              stroke="#475569"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              tickFormatter={(val) => `$${val}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "8px",
                color: "#e2e8f0",
                fontSize: "12px",
              }}
              formatter={(value: any) => [`$${value.toFixed(2)}`, "Cumulative P&L"]}
            />
            <Area
              type="monotone"
              dataKey="cumulative_pnl"
              stroke="#10b981"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorPnl)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
