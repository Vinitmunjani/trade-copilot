"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { RDistributionBucket } from "@/types";

const mockData: RDistributionBucket[] = [
  { range: "<-2R", count: 3, min_r: -5, max_r: -2 },
  { range: "-2 to -1R", count: 8, min_r: -2, max_r: -1 },
  { range: "-1 to 0R", count: 12, min_r: -1, max_r: 0 },
  { range: "0 to 1R", count: 15, min_r: 0, max_r: 1 },
  { range: "1 to 2R", count: 20, min_r: 1, max_r: 2 },
  { range: "2 to 3R", count: 10, min_r: 2, max_r: 3 },
  { range: ">3R", count: 5, min_r: 3, max_r: 5 },
];

interface RDistributionProps {
  data?: RDistributionBucket[];
}

export function RDistribution({ data = mockData }: RDistributionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">R Distribution</CardTitle>
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
