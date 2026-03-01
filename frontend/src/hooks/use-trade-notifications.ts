"use client";

/**
 * useTradeNotifications
 * Subscribes to WS events and fires:
 *   1. In-app themed toast via useToastStore
 *   2. Browser Notification API (if permission granted)
 *
 * Mount once inside the dashboard layout via <TradeNotificationsProvider />.
 */

import { useEffect, useRef } from "react";
import { wsClient } from "@/lib/ws";
import { useAuthStore } from "@/stores/auth-store";
import { useToast } from "@/hooks/use-toast";
import type { WSEvent, Trade, WSScoreUpdate, WSAlertUpdate } from "@/types";

function browserNotify(title: string, body: string, tag?: string) {
  if (typeof window === "undefined") return;
  if (Notification.permission === "granted") {
    new Notification(title, {
      body,
      tag,
      icon: "/favicon.ico",
      silent: false,
    });
  }
}

async function requestNotificationPermission() {
  if (typeof window === "undefined") return;
  if (Notification.permission === "default") {
    await Notification.requestPermission();
  }
}

export function useTradeNotifications() {
  const { token } = useAuthStore();
  const { toast } = useToast();
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    requestNotificationPermission();
  }, []);

  useEffect(() => {
    if (!token) return;

    const unsubscribe = wsClient.subscribe((event: WSEvent) => {
      if (event.type === "trade_opened") {
        const trade = (event as any).trade as Trade;
        const desc = `${trade.direction} ${trade.symbol} @ ${trade.entry_price}`;
        toast({
          title: "Trade Opened",
          description: desc,
          variant: "success",
        });
        browserNotify("Trade Opened", desc, `open-${trade.id}`);
      } else if (event.type === "trade_closed") {
        const trade = (event as any).trade as Trade;
        const pnl = trade.pnl != null ? ` · PnL: ${trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)}` : "";
        const desc = `${trade.direction} ${trade.symbol}${pnl}`;
        toast({
          title: "Trade Closed",
          description: desc,
          variant: trade.pnl != null && trade.pnl >= 0 ? "success" : "destructive",
        });
        browserNotify("Trade Closed", desc, `close-${trade.id}`);
      } else if (event.type === "trade_updated") {
        const trade = (event as any).trade as Trade;
        const desc = `${trade.symbol} — SL: ${trade.sl ?? "—"} | TP: ${trade.tp ?? "—"}`;
        toast({
          title: "Trade Modified",
          description: desc,
          variant: "info",
        });
        browserNotify("Trade Modified", desc, `mod-${trade.id}`);
      } else if (event.type === "score_update") {
        const ev = event as WSScoreUpdate;
        const score = ev.ai_score;
        if (score != null) {
          const desc = `AI score: ${score}/10`;
          toast({ title: "Analysis Ready", description: desc, variant: "info" });
        }
      } else if (event.type === "behavioral_alert") {
        const ev = event as WSAlertUpdate;
        if (ev.alert) {
          toast({
            title: "Behavioral Alert",
            description: ev.alert.message,
            variant: "destructive",
          });
          browserNotify("Behavioral Alert", ev.alert.message, `alert-${ev.alert.id}`);
        }
      }
    });

    unsubscribeRef.current = unsubscribe;
    return () => {
      if (unsubscribeRef.current) unsubscribeRef.current();
    };
  }, [token, toast]);
}

/** Drop-in component — mount once in layout to activate notifications. */
export function TradeNotificationsProvider() {
  useTradeNotifications();
  return null;
}
