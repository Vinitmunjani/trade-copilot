"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  FileText, 
  ChevronDown, 
  ChevronUp, 
  TrendingUp, 
  TrendingDown,
  Brain,
  Calendar,
  Download,
  AlertCircle,
} from "lucide-react";
import { formatDate, formatCurrency, formatPercent, cn } from "@/lib/utils";
import api from "@/lib/api";

interface WeeklyReport {
  id: string;
  week_start: string;
  week_end: string;
  summary: string;
  total_trades: number;
  total_pnl: number;
  win_rate: number;
  avg_r: number;
  patterns_detected: string[];
  top_suggestion: string;
  strengths: string[];
  weaknesses: string[];
  grade: "A" | "B" | "C" | "D" | "F";
}

const getGradeColor = (grade: string) => {
  switch (grade) {
    case "A": return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    case "B": return "text-teal-400 bg-teal-500/10 border-teal-500/20";
    case "C": return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    case "D": return "text-orange-400 bg-orange-500/10 border-orange-500/20";
    case "F": return "text-red-400 bg-red-500/10 border-red-500/20";
    default: return "text-muted bg-surface-muted border-border";
  }
};

export default function ReportsPage() {
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [expandedReport, setExpandedReport] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        const { data } = await api.get("/stats/weekly-reports", { params: { weeks: 4 } });
        setReports(data);
        if (data.length > 0) setExpandedReport(data[0].id);
      } catch {
        setReports([]);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  const toggleReport = (id: string) => {
    setExpandedReport(expandedReport === id ? null : id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Weekly Reports</h1>
          <p className="text-muted mt-1">
            Performance reviews generated from your real trade data
          </p>
        </div>
        <Button variant="outline" className="gap-2" disabled>
          <Download className="h-4 w-4" />
          Export All
        </Button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="text-center py-16 text-slate-400 animate-pulse">
          Loading your weekly reports…
        </div>
      )}

      {/* No data */}
      {!isLoading && reports.length === 0 && (
        <Card className="border-yellow-900/50 bg-yellow-900/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-yellow-300">No Reports Yet</h3>
                <p className="text-sm text-yellow-200 mt-1">
                  Close some trades this week and reports will appear here automatically.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Reports List */}
      {!isLoading && reports.length > 0 && (
        <div className="space-y-4">
          {reports.map((report) => (
            <Card key={report.id} className="overflow-hidden">
              <CardHeader 
                className="cursor-pointer hover:bg-surface-muted/60 transition-colors"
                onClick={() => toggleReport(report.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-[18px] bg-surface-muted border border-border flex items-center justify-center">
                      <FileText className="h-5 w-5 text-emerald-400" />
                    </div>
                    <div>
                      <div className="flex items-center gap-3">
                        <CardTitle className="text-lg">
                          Week of {formatDate(report.week_start, "MMM dd")} – {formatDate(report.week_end, "MMM dd")}
                        </CardTitle>
                        <Badge className={cn("text-xs font-bold", getGradeColor(report.grade))}>
                          Grade {report.grade}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-sm text-muted">
                        <span>{report.total_trades} trades</span>
                        <span>•</span>
                        <span className={report.total_pnl >= 0 ? "text-emerald-400" : "text-red-400"}>
                          {formatCurrency(report.total_pnl)}
                        </span>
                        <span>•</span>
                        <span>{formatPercent(report.win_rate)} win rate</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(report.week_end, "MMM dd, yyyy")}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {report.total_pnl >= 0 ? (
                      <TrendingUp className="h-5 w-5 text-emerald-400" />
                    ) : (
                      <TrendingDown className="h-5 w-5 text-red-400" />
                    )}
                    {expandedReport === report.id ? (
                      <ChevronUp className="h-5 w-5 text-muted" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-muted" />
                    )}
                  </div>
                </div>
              </CardHeader>

              {expandedReport === report.id && (
                <CardContent className="border-t border-border">
                  <div className="space-y-6 pt-6">
                    {/* Summary */}
                    <div>
                      <h4 className="font-semibold text-foreground mb-2">Summary</h4>
                      <p className="text-sm text-muted leading-relaxed">{report.summary}</p>
                    </div>

                    {/* Key Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-3 rounded-[18px] bg-surface-muted border border-border">
                        <div className="text-lg font-bold text-foreground">{report.total_trades}</div>
                        <div className="text-xs text-muted">Trades</div>
                      </div>
                      <div className="text-center p-3 rounded-[18px] bg-surface-muted border border-border">
                        <div className={cn("text-lg font-bold", report.total_pnl >= 0 ? "text-emerald-400" : "text-red-400")}>
                          {formatCurrency(report.total_pnl)}
                        </div>
                        <div className="text-xs text-muted">P&L</div>
                      </div>
                      <div className="text-center p-3 rounded-[18px] bg-surface-muted border border-border">
                        <div className="text-lg font-bold text-foreground">{formatPercent(report.win_rate)}</div>
                        <div className="text-xs text-muted">Win Rate</div>
                      </div>
                      <div className="text-center p-3 rounded-[18px] bg-surface-muted border border-border">
                        <div className={cn("text-lg font-bold", report.avg_r >= 0 ? "text-emerald-400" : "text-red-400")}>
                          {report.avg_r >= 0 ? "+" : ""}{report.avg_r.toFixed(1)}R
                        </div>
                        <div className="text-xs text-muted">Avg R</div>
                      </div>
                    </div>

                    {/* Strengths & Weaknesses */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold text-emerald-400 mb-3">💪 Strengths</h4>
                        <ul className="space-y-2">
                          {report.strengths.map((s, i) => (
                            <li key={i} className="text-sm text-muted flex items-start gap-2">
                              <span className="text-emerald-400 text-xs mt-1">✓</span>
                              {s}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-semibold text-amber-400 mb-3">🎯 Areas for Improvement</h4>
                        <ul className="space-y-2">
                          {report.weaknesses.map((w, i) => (
                            <li key={i} className="text-sm text-muted flex items-start gap-2">
                              <span className="text-amber-400 text-xs mt-1">!</span>
                              {w}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Top Suggestion */}
                    <div className="p-4 rounded-[18px] bg-surface-muted border border-border">
                      <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                        <Brain className="h-4 w-4 text-emerald-400" />
                        Recommendation
                      </h4>
                      <p className="text-sm text-muted">{report.top_suggestion}</p>
                    </div>

                    {/* Patterns Detected */}
                    {report.patterns_detected.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-foreground mb-3">Behavioral Patterns Flagged</h4>
                        <div className="flex flex-wrap gap-2">
                          {report.patterns_detected.map((pattern, i) => (
                            <Badge key={i} variant="warning" className="text-xs">
                              {pattern.replace(/_/g, " ").toUpperCase()}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}



