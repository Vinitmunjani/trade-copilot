"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Target } from "lucide-react";

const symbolData = [
  { name: "EURUSD", winRate: 72, lossRate: 28, totalTrades: 18 },
  { name: "GBPUSD", winRate: 65, lossRate: 35, totalTrades: 12 },
  { name: "USDJPY", winRate: 58, lossRate: 42, totalTrades: 8 },
  { name: "XAUUSD", winRate: 78, lossRate: 22, totalTrades: 15 },
  { name: "NAS100", winRate: 55, lossRate: 45, totalTrades: 6 },
];

const sessionData = [
  { name: "London", winRate: 75, lossRate: 25, totalTrades: 32 },
  { name: "NY", winRate: 63, lossRate: 37, totalTrades: 28 },
  { name: "Tokyo", winRate: 45, lossRate: 55, totalTrades: 9 },
  { name: "Sydney", winRate: 60, lossRate: 40, totalTrades: 5 },
];

const dayData = [
  { name: "Mon", winRate: 68, lossRate: 32, totalTrades: 15 },
  { name: "Tue", winRate: 71, lossRate: 29, totalTrades: 17 },
  { name: "Wed", winRate: 65, lossRate: 35, totalTrades: 12 },
  { name: "Thu", winRate: 73, lossRate: 27, totalTrades: 14 },
  { name: "Fri", winRate: 58, lossRate: 42, totalTrades: 16 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm">
        <p className="font-semibold text-slate-200">{label}</p>
        <p className="text-emerald-400">
          Win Rate: {payload[0].value}% ({payload[0].payload.totalTrades} trades)
        </p>
        <p className="text-red-400">Loss Rate: {payload[1].value}%</p>
      </div>
    );
  }
  return null;
};

export function WinRateChart() {
  const [activeTab, setActiveTab] = useState("symbol");

  const getData = () => {
    switch (activeTab) {
      case "session":
        return sessionData;
      case "day":
        return dayData;
      default:
        return symbolData;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Target className="h-4 w-4 text-emerald-400" />
          Win Rate Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-4">
            <TabsTrigger value="symbol">By Symbol</TabsTrigger>
            <TabsTrigger value="session">By Session</TabsTrigger>
            <TabsTrigger value="day">By Day</TabsTrigger>
          </TabsList>

          <TabsContent value={activeTab}>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={getData()} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: "#94a3b8", fontSize: 12 }}
                    axisLine={{ stroke: "#334155" }}
                    tickLine={{ stroke: "#334155" }}
                  />
                  <YAxis
                    tick={{ fill: "#94a3b8", fontSize: 12 }}
                    axisLine={{ stroke: "#334155" }}
                    tickLine={{ stroke: "#334155" }}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar
                    dataKey="winRate"
                    name="Win Rate"
                    fill="#10b981"
                    radius={[2, 2, 0, 0]}
                  />
                  <Bar
                    dataKey="lossRate"
                    name="Loss Rate"
                    fill="#ef4444"
                    radius={[2, 2, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
