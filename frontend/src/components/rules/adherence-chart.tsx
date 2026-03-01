"use client";

import React, { useEffect, useState, useCallback } from "react";
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
import api from "@/lib/api";

interface DayEntry {
  date: string;
  winRate: number;
  adherence: number;
  behavioralFlags: number;
  totalTrades: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as DayEntry;
    return (
      <div className="bg-surface border border-border rounded-lg p-3 text-sm shadow-lg">
        <p className="font-semibold text-foreground mb-2">{label}</p>
        <div className="space-y-1">
          <p className="text-accent">
            Win Rate: {data.winRate.toFixed(1)}%
          </p>
          <p className="text-muted">
            Rule Adherence: {data.adherence.toFixed(1)}%
          </p>
          {data.behavioralFlags > 0 && (
            <p className="text-[hsl(var(--danger))]">
              Behavioral Flags: {data.behavioralFlags}
            </p>
          )}
          <p className="text-muted">
            Trades: {data.totalTrades}
          </p>
        </div>
      </div>
    );
  }
  return null;
};

export function AdherenceChart() {
  const [chartData, setChartData] = useState<DayEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [avgWinRate, setAvgWinRate] = useState(0);
  const [avgAdherence, setAvgAdherence] = useState(0);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get("/stats/daily");
      const days: DayEntry[] = (data.days ?? [])
        .filter((d: any) => d.total_trades > 0)
        .map((d: any) => {
          const flags: number = d.behavioral_flags_count ?? 0;
          const total: number = d.total_trades ?? 0;
          const adherence = total > 0 ? Math.max(0, Math.round(((total - flags) / total) * 100)) : 100;
          return {
            date: new Date(d.date).toLocaleDateString("en-GB", { day: "2-digit", month: "short" }),
            winRate: Number((d.win_rate ?? 0).toFixed(1)),
            adherence,
            behavioralFlags: flags,
            totalTrades: total,
          };
        });
      setChartData(days);
      if (days.length > 0) {
        setAvgWinRate(days.reduce((s, d) => s + d.winRate, 0) / days.length);
        setAvgAdherence(days.reduce((s, d) => s + d.adherence, 0) / days.length);
      }
    } catch {
      setChartData([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Shield className="h-4 w-4 text-accent" />
          Rule Adherence Performance
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[400px] flex items-center justify-center">
            <div className="text-muted text-sm animate-pulse">Loading chart data…</div>
          </div>
        ) : chartData.length === 0 ? (
          <div className="h-[400px] flex flex-col items-center justify-center gap-3">
            <Shield className="h-10 w-10 text-muted/40" />
            <p className="text-muted text-sm">No trading data yet — close some trades to see adherence stats.</p>
          </div>
        ) : (
          <>
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: "hsl(var(--muted))", fontSize: 11 }}
                    axisLine={{ stroke: "hsl(var(--border))" }}
                    tickLine={{ stroke: "hsl(var(--border))" }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis
                    tick={{ fill: "hsl(var(--muted))", fontSize: 12 }}
                    axisLine={{ stroke: "hsl(var(--border))" }}
                    tickLine={{ stroke: "hsl(var(--border))" }}
                    tickFormatter={(v) => `${v}%`}
                    label={{
                      value: "Percentage (%)",
                      angle: -90,
                      position: "insideLeft",
                      style: { textAnchor: "middle", fill: "hsl(var(--muted))", fontSize: "12px" },
                    }}
                    domain={[0, 100]}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    wrapperStyle={{ paddingTop: "20px", fontSize: "12px", color: "hsl(var(--muted))" }}
                  />
                  <Bar
                    dataKey="winRate"
                    name="Win Rate"
                    fill="hsl(var(--accent))"
                    radius={[2, 2, 0, 0]}
                    opacity={0.85}
                  />
                  <Bar
                    dataKey="adherence"
                    name="Rule Adherence"
                    fill="hsl(var(--accent-soft))"
                    radius={[2, 2, 0, 0]}
                    opacity={0.6}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Summary */}
            <div className="mt-4 grid grid-cols-2 gap-4 text-center">
              <div className="p-3 rounded-lg bg-accent/10 border border-accent/20">
                <p className="text-2xl font-bold text-accent">{avgWinRate.toFixed(1)}%</p>
                <p className="text-xs text-muted">Avg Win Rate</p>
              </div>
              <div className="p-3 rounded-lg bg-accent/5 border border-border">
                <p className="text-2xl font-bold text-foreground">{avgAdherence.toFixed(1)}%</p>
                <p className="text-xs text-muted">Avg Rule Adherence</p>
              </div>
            </div>

            <p className="text-xs text-muted text-center mt-3">
              Based on your last {chartData.length} trading day{chartData.length !== 1 ? "s" : ""}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

