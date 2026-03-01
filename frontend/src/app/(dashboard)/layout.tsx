"use client";

import React, { useEffect } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { useAuth } from "@/hooks/use-auth";
import { useWebSocket } from "@/hooks/use-websocket";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { AiAnalysisPanel } from "@/components/dashboard/ai-analysis-panel";
import { TradeNotificationsProvider } from "@/hooks/use-trade-notifications";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated } = useAuth(true);
  const { isConnected } = useWebSocket();
  const [mounted, setMounted] = React.useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);
  const statusLabel = isConnected ? "Calibrating workspace" : "Reconnecting feed";

  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 opacity-80" aria-hidden="true">
        <div className="absolute -top-32 left-1/2 h-[520px] w-[520px] -translate-x-1/2 rounded-full bg-accent/25 blur-[140px]" />
        <div className="absolute bottom-0 right-0 h-[460px] w-[460px] translate-x-1/2 translate-y-1/3 rounded-full bg-accent-soft/40 blur-[180px]" />
        <div className="absolute inset-0 bg-grid-lines opacity-[0.04]" />
      </div>

      {!mounted || !isAuthenticated ? (
        <div className="relative z-10 flex min-h-screen flex-col items-center justify-center gap-4 text-muted">
          <LoadingSpinner size="lg" />
          <p className="text-xs uppercase tracking-[0.4em] text-foreground/60">{statusLabel}</p>
        </div>
      ) : (
        <div className="relative z-10 flex min-h-screen">
          <Sidebar />
          <div className="relative flex flex-1 flex-col">
            <Topbar isConnected={isConnected} />
            <main className="relative flex-1 overflow-auto px-6 pb-8 pt-6 lg:px-10">
              <div className="mx-auto w-full max-w-6xl space-y-6">{children}</div>
            </main>
          </div>
          <AiAnalysisPanel />
          <TradeNotificationsProvider />
        </div>
      )}
    </div>
  );
}
