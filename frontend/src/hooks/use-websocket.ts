"use client";

import { useEffect, useRef } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useTradesStore } from "@/stores/trades-store";
import { useAlertsStore } from "@/stores/alerts-store";
import { useAiPanelStore } from "@/stores/ai-panel-store";
import { wsClient } from "@/lib/ws";
import type { WSEvent, Trade, WSScoreUpdate, WSAlertUpdate } from "@/types";

export function useWebSocket() {
  const { token } = useAuthStore();
  const unsubscribeRef = useRef<(() => void) | null>(null);
  const { addTrade, updateTrade, patchTrade, bumpStats } = useTradesStore();
  const { addAlert } = useAlertsStore();
  const { setAnalysis, open: openPanel } = useAiPanelStore();

  useEffect(() => {
    if (!token) return;

    wsClient.connect(token);

    const unsubscribe = wsClient.subscribe((event: WSEvent) => {
      console.log("[WS] Received event:", event.type);

      if (event.type === "trade_opened") {
        const tradeData = (event as any).trade as Trade;
        console.log("[WS] Adding new trade:", tradeData.symbol);
        addTrade(tradeData);
      } else if (event.type === "trade_closed") {
        const tradeData = (event as any).trade as Trade;
        console.log("[WS] Updating closed trade:", tradeData.symbol);
        updateTrade(tradeData);
        // Signal stats hooks to refetch so dashboard P&L updates immediately
        bumpStats();
      } else if (event.type === "trade_updated") {
        const tradeData = (event as any).trade as Trade;
        console.log("[WS] Trade modified:", tradeData.symbol);
        updateTrade(tradeData);
      } else if (event.type === "score_update") {
        const scoreEvent = event as WSScoreUpdate;
        console.log("[WS] Score update for trade:", scoreEvent.trade_id);
        patchTrade(scoreEvent.trade_id, {
          ai_score: scoreEvent.ai_score ?? undefined,
          ai_analysis: scoreEvent.ai_analysis ?? undefined,
          ai_review: scoreEvent.ai_review ?? undefined,
        });
        // Show AI analysis panel with new data
        setAnalysis(scoreEvent.trade_id, scoreEvent.ai_score, scoreEvent.ai_analysis, scoreEvent.ai_review);
        openPanel();
      } else if (event.type === "behavioral_alert") {
        const alertEvent = event as WSAlertUpdate;
        console.log("[WS] Behavioral alert:", alertEvent.alert?.pattern_type);
        if (alertEvent.alert) addAlert(alertEvent.alert);
      }
    });

    unsubscribeRef.current = unsubscribe;

    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, [token, addTrade, updateTrade, patchTrade, bumpStats, addAlert, setAnalysis, openPanel]);

  return { isConnected: wsClient.isConnected };
}
