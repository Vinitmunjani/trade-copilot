"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { AlertCircle, Zap } from "lucide-react";
import type { RDistributionBucket } from "@/types";

interface RDistributionProps {
  data?: RDistributionBucket[];
}

export function RDistribution({ data = [] }: RDistributionProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Zap className="h-4 w-4 text-emerald-400" />
            R Distribution
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px] flex flex-col items-center justify-center text-slate-400">
            <AlertCircle className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No data available yet</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Zap className="h-4 w-4 text-emerald-400" />
          R Distribution
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="range" stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <YAxis stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "8px",
                color: "#e2e8f0",
                fontSize: "12px",
              }}
              formatter={(value: any) => [`${value} trades`, "Count"]}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.min_r >= 0 ? "#10b981" : "#ef4444"}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

