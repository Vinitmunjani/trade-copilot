"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";

export interface ReadinessData {
  readinessScore: number;   // 0-10 normalised
  rawCount: number;         // total_closed_trades from API
  hasEnoughHistory: boolean;
  tradesNeeded: number;
  message: string;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

/** Maps total closed trades → 0-10 readiness score. */
function scoreFromCount(count: number, minRequired: number): number {
  if (minRequired <= 0) return 10;
  return Math.min(10, Math.round((count / minRequired) * 10));
}

export function useReadiness(): ReadinessData {
  const [state, setState] = useState<Omit<ReadinessData, "isLoading" | "error" | "refetch">>({
    readinessScore: 0,
    rawCount: 0,
    hasEnoughHistory: false,
    tradesNeeded: 0,
    message: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await api.get("/analysis/readiness");
      const minRequired: number = data.min_required ?? 10;
      const count: number = data.total_closed_trades ?? 0;
      setState({
        readinessScore: scoreFromCount(count, minRequired),
        rawCount: count,
        hasEnoughHistory: !!data.has_enough_history,
        tradesNeeded: data.trades_needed ?? Math.max(0, minRequired - count),
        message: data.status ?? "",
      });
    } catch (e: any) {
      setError(e?.message ?? "Failed to load readiness");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  return { ...state, isLoading, error, refetch: fetch };
}
