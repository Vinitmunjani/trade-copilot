"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, TrendingUp, TrendingDown } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";

const mockData = {
  london: {
    Mon: { pnl: 245, trades: 3 },
    Tue: { pnl: 180, trades: 2 },
    Wed: { pnl: -120, trades: 4 },
    Thu: { pnl: 320, trades: 3 },
    Fri: { pnl: 95, trades: 2 },
  },
  new_york: {
    Mon: { pnl: 185, trades: 2 },
    Tue: { pnl: -85, trades: 3 },
    Wed: { pnl: 240, trades: 2 },
    Thu: { pnl: 160, trades: 2 },
    Fri: { pnl: -45, trades: 1 },
  },
  tokyo: {
    Mon: { pnl: -120, trades: 2 },
    Tue: { pnl: 0, trades: 0 },
    Wed: { pnl: -95, trades: 1 },
    Thu: { pnl: 0, trades: 0 },
    Fri: { pnl: 45, trades: 1 },
  },
  sydney: {
    Mon: { pnl: 0, trades: 0 },
    Tue: { pnl: 85, trades: 1 },
    Wed: { pnl: 0, trades: 0 },
    Thu: { pnl: -60, trades: 1 },
    Fri: { pnl: 0, trades: 0 },
  },
};

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

export function SessionHeatmap() {
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
                  const data = mockData[session.key as keyof typeof mockData][day as keyof typeof mockData.london];
                  const cellColor = getCellColor(data.pnl, data.trades);
                  
                  return (
                    <div
                      key={day}
                      className={cn(
                        "h-16 rounded-lg border flex flex-col items-center justify-center cursor-pointer transition-all hover:scale-105",
                        cellColor
                      )}
                      title={`${session.label} ${day}: ${formatCurrency(data.pnl)} (${data.trades} trades)`}
                    >
                      {data.trades > 0 ? (
                        <>
                          <div className="text-xs font-bold">
                            {formatCurrency(data.pnl)}
                          </div>
                          <div className="text-[10px] opacity-75">
                            {data.trades} trade{data.trades !== 1 ? 's' : ''}
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
