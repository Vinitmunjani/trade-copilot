"use client";

import React, { useMemo, useState } from "react";
import { Calculator, TrendingDown, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTradesStore } from "@/stores/trades-store";

const STREAK_MODIFIERS: Array<{ losses: number; label: string; modifier: number; color: string }> = [
  { losses: 0, label: "Full size", modifier: 1.0, color: "text-accent" },
  { losses: 1, label: "Slight caution", modifier: 0.75, color: "text-accent" },
  { losses: 2, label: "Reduce size", modifier: 0.5, color: "text-amber-400" },
  { losses: 3, label: "Minimal size", modifier: 0.25, color: "text-red-400" },
];

// Rough lot-size calculator for forex: 1 lot = 100,000 units
// Risk $ = lotSize × 100,000 × pipValue × stopPips  (simplified: risk = lotSize × 10 × stopPips for USD pairs)
function calcLotSize(balance: number, riskPct: number, stopPips: number): number {
  if (!balance || !riskPct || !stopPips) return 0;
  const riskAmount = (balance * riskPct) / 100;
  // $10/pip per standard lot for most USD pairs
  const pipValuePerLot = 10;
  return riskAmount / (stopPips * pipValuePerLot);
}

export function PositionSizer() {
  const { trades } = useTradesStore();
  const [balance, setBalance] = useState("");
  const [riskPct, setRiskPct] = useState("1");
  const [stopPips, setStopPips] = useState("20");

  const { consecutiveLosses, streakMod } = useMemo(() => {
    const closed = trades
      .filter((t) => t.status === "closed" || t.status === "CLOSED")
      .filter((t) => t.pnl !== null)
      .sort((a, b) => new Date(b.closed_at ?? b.close_time ?? 0).getTime() - new Date(a.closed_at ?? a.close_time ?? 0).getTime());

    let streak = 0;
    for (const t of closed) {
      if ((t.pnl ?? 0) < 0) streak++;
      else break;
    }

    const streakMod = streak >= 3 ? STREAK_MODIFIERS[3] : (STREAK_MODIFIERS[streak] ?? STREAK_MODIFIERS[0]);
    return { consecutiveLosses: streak, streakMod };
  }, [trades]);

  const baseLot = calcLotSize(
    parseFloat(balance) || 0,
    parseFloat(riskPct) || 1,
    parseFloat(stopPips) || 20
  );

  const adjustedLot = baseLot * streakMod.modifier;
  const riskAmount = ((parseFloat(balance) || 0) * (parseFloat(riskPct) || 1)) / 100 * streakMod.modifier;

  return (
    <div className="rounded-2xl border border-white/8 bg-surface/60 p-5">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/10">
          <Calculator className="h-4 w-4 text-accent" />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">Position Sizer</p>
          <p className="text-xs text-muted">Streak-adjusted lot size</p>
        </div>
      </div>

      {/* Streak indicator */}
      <div className={cn(
        "mb-4 flex items-center gap-2 rounded-xl border px-3 py-2.5 text-xs",
        consecutiveLosses === 0 ? "border-accent/20 bg-accent/5 text-accent"
        : consecutiveLosses < 2 ? "border-accent/20 bg-accent/5 text-accent"
        : consecutiveLosses < 3 ? "border-amber-400/20 bg-amber-400/5 text-amber-400"
        : "border-red-400/20 bg-red-400/5 text-red-400"
      )}>
        {consecutiveLosses >= 2 ? <TrendingDown className="h-3.5 w-3.5 shrink-0" /> : <ShieldAlert className="h-3.5 w-3.5 shrink-0" />}
        <span>
          {consecutiveLosses === 0
            ? "No loss streak — full size permitted"
            : `${consecutiveLosses} consecutive ${consecutiveLosses === 1 ? "loss" : "losses"} — size modifier: ${(streakMod.modifier * 100).toFixed(0)}% (${streakMod.label})`}
        </span>
      </div>

      {/* Inputs */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          { label: "Account ($)", value: balance, set: setBalance, placeholder: "10000" },
          { label: "Risk (%)", value: riskPct, set: setRiskPct, placeholder: "1" },
          { label: "Stop (pips)", value: stopPips, set: setStopPips, placeholder: "20" },
        ].map(({ label, value, set, placeholder }) => (
          <div key={label}>
            <label className="mb-1 block text-[10px] uppercase tracking-widest text-muted">{label}</label>
            <input
              type="number"
              value={value}
              onChange={(e) => set(e.target.value)}
              placeholder={placeholder}
              className="w-full rounded-xl border border-white/10 bg-surface px-3 py-2 text-sm text-foreground placeholder-muted/40 focus:border-accent/40 focus:outline-none"
            />
          </div>
        ))}
      </div>

      {/* Result */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-white/5 bg-surface-contrast/40 p-3 text-center">
          <p className="text-[10px] uppercase tracking-widest text-muted">Adjusted Lots</p>
          <p className={cn("mt-1 text-3xl font-semibold", streakMod.color)}>
            {adjustedLot > 0 ? adjustedLot.toFixed(2) : "—"}
          </p>
          {baseLot > 0 && consecutiveLosses > 0 && (
            <p className="mt-0.5 text-[10px] text-muted line-through">{baseLot.toFixed(2)} base</p>
          )}
        </div>
        <div className="rounded-xl border border-white/5 bg-surface-contrast/40 p-3 text-center">
          <p className="text-[10px] uppercase tracking-widest text-muted">Risk Amount</p>
          <p className={cn("mt-1 text-3xl font-semibold", streakMod.color)}>
            {riskAmount > 0 ? `$${riskAmount.toFixed(0)}` : "—"}
          </p>
          <p className="mt-0.5 text-[10px] text-muted">
            {parseFloat(riskPct) * streakMod.modifier}% of balance
          </p>
        </div>
      </div>

      {/* Modifier ladder */}
      <div className="mt-4 grid grid-cols-4 gap-1.5">
        {STREAK_MODIFIERS.map((m) => (
          <div
            key={m.losses}
            className={cn(
              "rounded-lg border px-2 py-1.5 text-center text-[10px]",
              consecutiveLosses >= m.losses && (m.losses === 3 || consecutiveLosses < (STREAK_MODIFIERS[STREAK_MODIFIERS.indexOf(m) + 1]?.losses ?? 99))
                ? "border-white/15 bg-white/5 text-foreground"
                : "border-white/5 text-muted/50"
            )}
          >
            <p>{m.losses === 0 ? "0" : `${m.losses}L`}</p>
            <p className={cn("font-semibold", m.color)}>{(m.modifier * 100).toFixed(0)}%</p>
          </div>
        ))}
      </div>
    </div>
  );
}
