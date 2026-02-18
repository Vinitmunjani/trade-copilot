"use client";

import { useEffect, useRef } from "react";
import { wsClient } from "@/lib/ws";
import { useAuthStore } from "@/stores/auth-store";
import { useTradesStore } from "@/stores/trades-store";
import { useAlertsStore } from "@/stores/alerts-store";
import type { WSEvent } from "@/types";

export function useWebSocket() {
  const { token } = useAuthStore();
  const { addTrade, updateTrade, updateTradeScore } = useTradesStore();
  const { addAlert } = useAlertsStore();
  const connectedRef = useRef(false);

  useEffect(() => {
    if (!token || connectedRef.current) return;

    const handleEvent = (event: WSEvent) => {
      switch (event.type) {
        case "trade_opened":
          addTrade(event.trade);
          break;
        case "trade_updated":
          updateTrade(event.trade);
          break;
        case "trade_closed":
          updateTrade(event.trade);
          break;
        case "score_update":
          updateTradeScore(event.trade_id, event.score);
          break;
        case "behavioral_alert":
          addAlert(event.alert);
          break;
        case "readiness_update":
          // Could update a readiness store
          break;
      }
    };

    wsClient.connect(token);
    const unsubscribe = wsClient.subscribe(handleEvent);
    connectedRef.current = true;

    return () => {
      unsubscribe();
      wsClient.disconnect();
      connectedRef.current = false;
    };
  }, [token, addTrade, updateTrade, updateTradeScore, addAlert]);

  return { isConnected: wsClient.isConnected };
}
