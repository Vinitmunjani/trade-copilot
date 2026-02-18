"use client";

import React, { useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, X } from "lucide-react";
import { SYMBOLS } from "@/lib/constants";
import type { TradeFilters as TradeFiltersType } from "@/types";

interface TradeFiltersProps {
  onFilterChange: (filters: TradeFiltersType) => void;
}

export function TradeFilters({ onFilterChange }: TradeFiltersProps) {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [symbol, setSymbol] = useState<string>("all");
  const [direction, setDirection] = useState<string>("all");
  const [scoreMin, setScoreMin] = useState("");
  const [scoreMax, setScoreMax] = useState("");

  const applyFilters = useCallback(() => {
    const filters: TradeFiltersType = {};
    if (dateFrom) filters.date_from = dateFrom;
    if (dateTo) filters.date_to = dateTo;
    if (symbol && symbol !== "all") filters.symbol = [symbol];
    if (direction && direction !== "all")
      filters.direction = direction as "BUY" | "SELL";
    if (scoreMin) filters.score_min = parseInt(scoreMin, 10);
    if (scoreMax) filters.score_max = parseInt(scoreMax, 10);
    onFilterChange(filters);
  }, [dateFrom, dateTo, symbol, direction, scoreMin, scoreMax, onFilterChange]);

  const clearFilters = () => {
    setDateFrom("");
    setDateTo("");
    setSymbol("all");
    setDirection("all");
    setScoreMin("");
    setScoreMax("");
    onFilterChange({});
  };

  return (
    <div className="flex flex-wrap items-end gap-3 p-4 rounded-lg bg-slate-900 border border-slate-800">
      {/* Date Range */}
      <div className="space-y-1">
        <label className="text-xs text-slate-400">From</label>
        <Input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="w-36"
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs text-slate-400">To</label>
        <Input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="w-36"
        />
      </div>

      {/* Symbol */}
      <div className="space-y-1">
        <label className="text-xs text-slate-400">Symbol</label>
        <Select value={symbol} onValueChange={setSymbol}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="All Symbols" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Symbols</SelectItem>
            {SYMBOLS.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Direction */}
      <div className="space-y-1">
        <label className="text-xs text-slate-400">Direction</label>
        <Select value={direction} onValueChange={setDirection}>
          <SelectTrigger className="w-28">
            <SelectValue placeholder="All" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="BUY">Buy</SelectItem>
            <SelectItem value="SELL">Sell</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Score Range */}
      <div className="space-y-1">
        <label className="text-xs text-slate-400">Score Min</label>
        <Input
          type="number"
          min={1}
          max={10}
          value={scoreMin}
          onChange={(e) => setScoreMin(e.target.value)}
          placeholder="1"
          className="w-20"
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs text-slate-400">Score Max</label>
        <Input
          type="number"
          min={1}
          max={10}
          value={scoreMax}
          onChange={(e) => setScoreMax(e.target.value)}
          placeholder="10"
          className="w-20"
        />
      </div>

      {/* Action Buttons */}
      <Button onClick={applyFilters} size="sm" className="gap-1">
        <Search className="h-3.5 w-3.5" />
        Filter
      </Button>
      <Button onClick={clearFilters} variant="ghost" size="sm" className="gap-1">
        <X className="h-3.5 w-3.5" />
        Clear
      </Button>
    </div>
  );
}
