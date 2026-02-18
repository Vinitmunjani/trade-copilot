"use client";

import { useEffect } from "react";
import { useTradesStore } from "@/stores/trades-store";
import type { TradeFilters } from "@/types";

export function useTrades(filters?: TradeFilters) {
  const { trades, openTrades, isLoading, fetchTrades, fetchOpenTrades } = useTradesStore();

  useEffect(() => {
    fetchTrades(filters);
    fetchOpenTrades();
  }, [fetchTrades, fetchOpenTrades, filters]);

  return { trades, openTrades, isLoading };
}

export function useTradeDetail(id: string) {
  const { selectedTrade, isLoading, fetchTradeById } = useTradesStore();

  useEffect(() => {
    fetchTradeById(id);
  }, [id, fetchTradeById]);

  return { trade: selectedTrade, isLoading };
}
