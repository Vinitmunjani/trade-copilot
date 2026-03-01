"use client";

import React, { useMemo, useState } from "react";
import { TradeJournalEntry } from "./trade-journal-entry";
import { BookOpen, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import type { Trade } from "@/types";

interface TradeJournalProps {
  trades: Trade[];
}

export function TradeJournal({ trades }: TradeJournalProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const list = q
      ? trades.filter(
          (t) =>
            t.symbol.toLowerCase().includes(q) ||
            t.direction.toLowerCase().includes(q) ||
            (t.session && t.session.toLowerCase().includes(q))
        )
      : trades;

    // Newest first
    return [...list].sort(
      (a, b) => new Date(b.opened_at).getTime() - new Date(a.opened_at).getTime()
    );
  }, [trades, search]);

  if (trades.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted gap-3">
        <BookOpen className="h-10 w-10 text-muted/30" />
        <p className="text-sm">No trades to journal yet.</p>
        <p className="text-xs text-muted/60">Your trade journal will appear here as trades are placed.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 pointer-events-none" />
        <Input
          placeholder="Filter by symbol, direction…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9 h-9 text-sm bg-surface border-border/60"
        />
      </div>

      {/* Stats bar */}
      <div className="flex flex-wrap gap-4 text-sm text-muted">
        <span>
          <span className="font-semibold text-slate-200">{filtered.length}</span> trades
        </span>
        <span>
          <span className="font-semibold text-emerald-400">
            {filtered.filter((t) => (t.pnl ?? 0) > 0).length}
          </span>{" "}
          winners
        </span>
        <span>
          <span className="font-semibold text-red-400">
            {filtered.filter((t) => (t.pnl ?? 0) < 0).length}
          </span>{" "}
          losers
        </span>
        <span>
          <span className="font-semibold text-accent">
            {filtered.filter((t) => t.ai_review).length}
          </span>{" "}
          with AI review
        </span>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-10 text-muted text-sm">
          No trades match &ldquo;{search}&rdquo;
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((trade) => (
            <TradeJournalEntry key={trade.id} trade={trade} />
          ))}
        </div>
      )}
    </div>
  );
}
