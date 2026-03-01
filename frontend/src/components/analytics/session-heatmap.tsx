"use client";

import React, { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, AlertCircle } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";

const days = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const sessions = [
  { key: "london", label: "London" },
  { key: "new_york", label: "New York" },
  { key: "tokyo", label: "Tokyo" },
  { key: "sydney", label: "Sydney" },
];

const getIntensity = (pnl: number) => {
  const maxPnl = 320;
  const minPnl = -120;
  
  if (pnl === 0) return 0;
  
  if (pnl > 0) {
    return Math.min(pnl / maxPnl, 1);
  } else {
    return Math.min(Math.abs(pnl) / Math.abs(minPnl), 1);
  }
};

const getCellColor = (pnl: number, trades: number) => {
  if (trades === 0) {
    return "bg-slate-800 border-slate-700";
  }
  
  const intensity = getIntensity(pnl);
  
  if (pnl > 0) {
    return `bg-emerald-500/${Math.max(10, Math.floor(intensity * 50))} border-emerald-500/30 text-emerald-100`;
  } else if (pnl < 0) {
    return `bg-red-500/${Math.max(10, Math.floor(intensity * 50))} border-red-500/30 text-red-100`;
  }
  
  return "bg-slate-800 border-slate-700";
};

interface SessionHeatmapProps {
  trades?: Array<any>;
}

export function SessionHeatmap({ trades = [] }: SessionHeatmapProps) {
  // Compute heatmap data from real trades
  const heatmapData = useMemo(() => {
    const data: Record<string, Record<string, { pnl: number; trades: number }>> = {
      london: { Mon: { pnl: 0, trades: 0 }, Tue: { pnl: 0, trades: 0 }, Wed: { pnl: 0, trades: 0 }, Thu: { pnl: 0, trades: 0 }, Fri: { pnl: 0, trades: 0 } },
      new_york: { Mon: { pnl: 0, trades: 0 }, Tue: { pnl: 0, trades: 0 }, Wed: { pnl: 0, trades: 0 }, Thu: { pnl: 0, trades: 0 }, Fri: { pnl: 0, trades: 0 } },
      tokyo: { Mon: { pnl: 0, trades: 0 }, Tue: { pnl: 0, trades: 0 }, Wed: { pnl: 0, trades: 0 }, Thu: { pnl: 0, trades: 0 }, Fri: { pnl: 0, trades: 0 } },
      sydney: { Mon: { pnl: 0, trades: 0 }, Tue: { pnl: 0, trades: 0 }, Wed: { pnl: 0, trades: 0 }, Thu: { pnl: 0, trades: 0 }, Fri: { pnl: 0, trades: 0 } },
    };

    // Map trades to sessions and days
    if (trades && trades.length > 0) {
      trades.forEach((trade: any) => {
        if (!trade.closed_at) return;
        
        const date = new Date(trade.closed_at);
        const day = date.toLocaleDateString('en-US', { weekday: 'short' });
        const hour = date.getHours();
        
        // Determine session based on hour (UTC)
        let session = 'london';
        if (hour >= 0 && hour < 8) session = 'tokyo';
        else if (hour >= 8 && hour < 12) session = 'london';
        else if (hour >= 12 && hour < 21) session = 'new_york';
        else session = 'sydney';
        
        if (!data[session][day as any]) {
          data[session][day as any] = { pnl: 0, trades: 0 };
        }
        
        data[session][day as any].pnl += trade.pnl || 0;
        data[session][day as any].trades += 1;
      });
    }

    return data;
  }, [trades]);

  // Check if there's any data
  const hasData = useMemo(() => {
    return trades && trades.length > 0 && Object.values(heatmapData).some(session =>
      Object.values(session).some(day => day.trades > 0)
    );
  }, [trades, heatmapData]);

  if (!hasData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Calendar className="h-4 w-4 text-emerald-400" />
            Session Performance Heatmap
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex flex-col items-center justify-center text-slate-400">
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
          <Calendar className="h-4 w-4 text-emerald-400" />
          Session Performance Heatmap
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div className="min-w-[600px]">
            {/* Header */}
            <div className="grid grid-cols-6 gap-2 mb-2">
              <div></div>
              {days.map((day) => (
                <div
                  key={day}
                  className="text-center text-xs font-medium text-slate-400 p-2"
                >
                  {day}
                </div>
              ))}
            </div>
            
            {/* Rows */}
            {sessions.map((session) => (
              <div key={session.key} className="grid grid-cols-6 gap-2 mb-2">
                <div className="flex items-center text-sm font-medium text-slate-300 p-2">
                  {session.label}
                </div>
                {days.map((day) => {
                  const cellData = heatmapData[session.key as keyof typeof heatmapData][day as keyof typeof heatmapData.london];
                  const cellColor = getCellColor(cellData.pnl, cellData.trades);
                  
                  return (
                    <div
                      key={day}
                      className={cn(
                        "h-16 rounded-lg border flex flex-col items-center justify-center cursor-pointer transition-all hover:scale-105",
                        cellColor
                      )}
                      title={`${session.label} ${day}: ${formatCurrency(cellData.pnl)} (${cellData.trades} trades)`}
                    >
                      {cellData.trades > 0 ? (
                        <>
                          <div className="text-xs font-bold">
                            {formatCurrency(cellData.pnl)}
                          </div>
                          <div className="text-[10px] opacity-75">
                            {cellData.trades} trade{cellData.trades !== 1 ? 's' : ''}
                          </div>
                        </>
                      ) : (
                        <div className="text-xs text-slate-500">—</div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
        
        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-6 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-emerald-500/30 border border-emerald-500/50"></div>
            <span className="text-slate-400">Profitable</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-red-500/30 border border-red-500/50"></div>
            <span className="text-slate-400">Loss</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-slate-800 border border-slate-700"></div>
            <span className="text-slate-400">No trades</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

