"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import { useTradesStore } from "@/stores/trades-store";

export type EdgeGroupBy = "symbol" | "session";

export interface EdgeRow {
  key: string;
  trades: number;
  wins: number;
  winRate: number;
  avgPnl: number;
  totalPnl: number;
}

interface EdgeResponse {
  group_by: EdgeGroupBy;
  days: number;
  min_trades: number;
  rows: EdgeRow[];
}

interface UseEdgeStatsResult {
  rows: EdgeRow[];
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useEdgeStats(groupBy: EdgeGroupBy, days = 90, minTrades = 2, limit = 6): UseEdgeStatsResult {
  const statsVersion = useTradesStore((s) => s.statsVersion);
  const [rows, setRows] = useState<EdgeRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await api.get<EdgeResponse>("/stats/edge", {
        params: {
          group_by: groupBy,
          days,
          min_trades: minTrades,
          limit,
        },
      });
      setRows(data?.rows ?? []);
    } catch (e: any) {
      setRows([]);
      setError(e?.message ?? "Failed to load edge stats");
    } finally {
      setIsLoading(false);
    }
  }, [groupBy, days, minTrades, limit]);

  useEffect(() => {
    fetch();
  }, [fetch, statsVersion]);

  return { rows, isLoading, error, refetch: fetch };
}
