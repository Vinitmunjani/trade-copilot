"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import { useTradesStore } from "@/stores/trades-store";

export interface LossResult {
  symbol: string;
  pnl: number;
  closed_at: string | null;
}

interface LossProtectionResponse {
  consecutive_losses: number;
  dollar_lost: number;
  level: "clear" | "warn" | "lockout";
  suggested_modifier: number;
  last_results: LossResult[];
}

interface UseLossProtectionResult {
  consecutiveLosses: number;
  dollarLost: number;
  level: "clear" | "warn" | "lockout";
  suggestedModifier: number;
  lastResults: LossResult[];
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useLossProtection(recentLimit = 10, lookbackDays = 90): UseLossProtectionResult {
  const statsVersion = useTradesStore((s) => s.statsVersion);

  const [consecutiveLosses, setConsecutiveLosses] = useState(0);
  const [dollarLost, setDollarLost] = useState(0);
  const [level, setLevel] = useState<"clear" | "warn" | "lockout">("clear");
  const [suggestedModifier, setSuggestedModifier] = useState(1);
  const [lastResults, setLastResults] = useState<LossResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await api.get<LossProtectionResponse>("/stats/loss-protection", {
        params: {
          recent_limit: recentLimit,
          lookback_days: lookbackDays,
        },
      });
      setConsecutiveLosses(data?.consecutive_losses ?? 0);
      setDollarLost(data?.dollar_lost ?? 0);
      setLevel(data?.level ?? "clear");
      setSuggestedModifier(data?.suggested_modifier ?? 1);
      setLastResults(data?.last_results ?? []);
    } catch (e: any) {
      setConsecutiveLosses(0);
      setDollarLost(0);
      setLevel("clear");
      setSuggestedModifier(1);
      setLastResults([]);
      setError(e?.message ?? "Failed to load loss protection stats");
    } finally {
      setIsLoading(false);
    }
  }, [lookbackDays, recentLimit]);

  useEffect(() => {
    fetch();
  }, [fetch, statsVersion]);

  return {
    consecutiveLosses,
    dollarLost,
    level,
    suggestedModifier,
    lastResults,
    isLoading,
    error,
    refetch: fetch,
  };
}
