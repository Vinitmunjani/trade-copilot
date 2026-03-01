"use client";

import React, { useState, useMemo } from "react";
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
import { Target, AlertCircle } from "lucide-react";

interface WinRateChartProps {
  data?: Array<{
    name: string;
    winRate: number;
    lossRate: number;
    totalTrades: number;
  }>;
  trades?: Array<any>;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-surface-muted border border-border/60 rounded-lg p-3 text-sm">
        <p className="font-semibold text-foreground">{label}</p>
        <p className="text-emerald-400">
          Win Rate: {payload[0].value}% ({payload[0].payload.totalTrades} trades)
        </p>
        <p className="text-red-400">Loss Rate: {payload[1].value}%</p>
      </div>
    );
  }
  return null;
};

export function WinRateChart({ data = [], trades = [] }: WinRateChartProps) {
  const [activeTab, setActiveTab] = useState("symbol");

  // Compute all analytics from real trades
  const computedData = useMemo(() => {
    if (!trades || trades.length === 0) {
      return {
        symbol: [],
        session: [],
        day: [],
        hasData: false,
      };
    }

    // 1. By Symbol
    const symbolStats: Record<string, { wins: number; losses: number; total: number }> = {};
    trades.forEach((trade: any) => {
      if (!symbolStats[trade.symbol]) {
        symbolStats[trade.symbol] = { wins: 0, losses: 0, total: 0 };
      }
      symbolStats[trade.symbol].total++;
      if ((trade.pnl || 0) > 0) {
        symbolStats[trade.symbol].wins++;
      } else {
        symbolStats[trade.symbol].losses++;
      }
    });

    const symbolData = Object.entries(symbolStats)
      .map(([symbol, stats]) => ({
        name: symbol,
        winRate: Math.round((stats.wins / stats.total) * 100),
        lossRate: Math.round((stats.losses / stats.total) * 100),
        totalTrades: stats.total,
      }))
      .sort((a, b) => b.totalTrades - a.totalTrades);

    // 2. By Session (London, NY, Tokyo, Sydney based on hour UTC)
    const sessionStats: Record<string, { wins: number; losses: number; total: number }> = {
      London: { wins: 0, losses: 0, total: 0 },
      "New York": { wins: 0, losses: 0, total: 0 },
      Tokyo: { wins: 0, losses: 0, total: 0 },
      Sydney: { wins: 0, losses: 0, total: 0 },
    };

    trades.forEach((trade: any) => {
      if (!trade.closed_at) return;
      const date = new Date(trade.closed_at);
      const hour = date.getHours();
      
      let session = "London";
      if (hour >= 0 && hour < 8) session = "Tokyo";
      else if (hour >= 8 && hour < 12) session = "London";
      else if (hour >= 12 && hour < 21) session = "New York";
      else session = "Sydney";

      sessionStats[session].total++;
      if ((trade.pnl || 0) > 0) {
        sessionStats[session].wins++;
      } else {
        sessionStats[session].losses++;
      }
    });

    const sessionData = Object.entries(sessionStats)
      .map(([session, stats]) => ({
        name: session,
        winRate: stats.total > 0 ? Math.round((stats.wins / stats.total) * 100) : 0,
        lossRate: stats.total > 0 ? Math.round((stats.losses / stats.total) * 100) : 0,
        totalTrades: stats.total,
      }))
      .filter(s => s.totalTrades > 0);

    // 3. By Day of Week (Mon-Fri)
    const dayStats: Record<string, { wins: number; losses: number; total: number }> = {
      Mon: { wins: 0, losses: 0, total: 0 },
      Tue: { wins: 0, losses: 0, total: 0 },
      Wed: { wins: 0, losses: 0, total: 0 },
      Thu: { wins: 0, losses: 0, total: 0 },
      Fri: { wins: 0, losses: 0, total: 0 },
    };

    const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    trades.forEach((trade: any) => {
      if (!trade.closed_at) return;
      const date = new Date(trade.closed_at);
      const dayName = dayNames[date.getDay()];
      
      if (dayName in dayStats) {
        dayStats[dayName].total++;
        if ((trade.pnl || 0) > 0) {
          dayStats[dayName].wins++;
        } else {
          dayStats[dayName].losses++;
        }
      }
    });

    const dayData = Object.entries(dayStats)
      .map(([day, stats]) => ({
        name: day,
        winRate: stats.total > 0 ? Math.round((stats.wins / stats.total) * 100) : 0,
        lossRate: stats.total > 0 ? Math.round((stats.losses / stats.total) * 100) : 0,
        totalTrades: stats.total,
      }))
      .filter(d => d.totalTrades > 0);

    return {
      symbol: symbolData,
      session: sessionData,
      day: dayData,
      hasData: symbolData.length > 0,
    };
  }, [trades]);

  const getData = () => {
    switch (activeTab) {
      case "session":
        return computedData.session;
      case "day":
        return computedData.day;
      default:
        return computedData.symbol;
    }
  };

  if (!computedData.hasData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Target className="h-4 w-4 text-emerald-400" />
            Win Rate Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex flex-col items-center justify-center text-slate-400">
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
          <Target className="h-4 w-4 text-emerald-400" />
          Win Rate Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-4">
            <TabsTrigger value="symbol">By Symbol</TabsTrigger>
            {computedData.session.length > 0 && <TabsTrigger value="session">By Session</TabsTrigger>}
            {computedData.day.length > 0 && <TabsTrigger value="day">By Day</TabsTrigger>}
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

