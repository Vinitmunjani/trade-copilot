"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { useTradesStore } from "@/stores/trades-store";

export interface DailyOverview {
  tradesToday: number;
  winRate: number;
  avgR: number;
  todayPnl: number;
  todayPnlR: number;
  adherence: number;
  winningTrades: number;
  losingTrades: number;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useDailyStats(): DailyOverview {
  const statsVersion = useTradesStore((s) => s.statsVersion);
  const [data, setData] = useState<Omit<DailyOverview, "isLoading" | "error" | "refetch">>({
    tradesToday: 0,
    winRate: 0,
    avgR: 0,
    todayPnl: 0,
    todayPnlR: 0,
    adherence: 0,
    winningTrades: 0,
    losingTrades: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data: res } = await api.get("/stats/overview");
      setData({
        tradesToday: res.total_trades ?? 0,
        winRate: res.win_rate ?? 0,
        avgR: res.avg_r ?? 0,
        todayPnl: res.total_pnl ?? 0,
        todayPnlR: res.total_pnl_r ?? 0,
        adherence: res.adherence ?? 100,
        winningTrades: res.winning_trades ?? 0,
        losingTrades: res.losing_trades ?? 0,
      });
    } catch (e: any) {
      setError(e?.message ?? "Failed to load stats");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch, statsVersion]);

  return { ...data, isLoading, error, refetch: fetch };
}
