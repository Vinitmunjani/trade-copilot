"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import { useTradesStore } from "@/stores/trades-store";

export interface PatternCostRow {
  key: string;
  cost: number;
  count: number;
}

interface PatternCostResponse {
  days: number;
  total_patterns: number;
  total_cost: number;
  rows: PatternCostRow[];
}

interface UsePatternCostResult {
  rows: PatternCostRow[];
  totalCost: number;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function usePatternCost(days = 90, limit = 6): UsePatternCostResult {
  const statsVersion = useTradesStore((s) => s.statsVersion);
  const [rows, setRows] = useState<PatternCostRow[]>([]);
  const [totalCost, setTotalCost] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await api.get<PatternCostResponse>("/stats/pattern-cost", {
        params: { days, limit },
      });
      setRows(data?.rows ?? []);
      setTotalCost(data?.total_cost ?? 0);
    } catch (e: any) {
      setRows([]);
      setTotalCost(0);
      setError(e?.message ?? "Failed to load pattern cost");
    } finally {
      setIsLoading(false);
    }
  }, [days, limit]);

  useEffect(() => {
    fetch();
  }, [fetch, statsVersion]);

  return { rows, totalCost, isLoading, error, refetch: fetch };
}
