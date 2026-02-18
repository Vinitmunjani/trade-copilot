"use client";

import React, { useState } from "react";
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
  Download
} from "lucide-react";
import { formatDate, formatCurrency, formatPercent, cn } from "@/lib/utils";

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

const mockReports: WeeklyReport[] = [
  {
    id: "r1",
    week_start: "2024-01-15",
    week_end: "2024-01-21",
    summary: "Solid week with good trend-following discipline. Some late-session trading violated rules but overall performance was strong.",
    total_trades: 12,
    total_pnl: 485,
    win_rate: 75,
    avg_r: 1.8,
    patterns_detected: ["early_exit", "fomo_entry"],
    top_suggestion: "Consider using partial profit-taking instead of full early exits to maximize winners.",
    strengths: ["Good R:R ratios", "Consistent with trend", "Strong London session performance"],
    weaknesses: ["Late-session trading", "FOMO entries on news", "Exiting winners too early"],
    grade: "B",
  },
  {
    id: "r2",
    week_start: "2024-01-08",
    week_end: "2024-01-14",
    summary: "Excellent trading week with high discipline and strong risk management. Only minor violations of session rules.",
    total_trades: 8,
    total_pnl: 720,
    win_rate: 87.5,
    avg_r: 2.4,
    patterns_detected: ["session_violation"],
    top_suggestion: "Maintain current approach - you're in the zone! Watch out for overconfidence.",
    strengths: ["Exceptional win rate", "High R multiples", "Clean trend-following", "Good risk management"],
    weaknesses: ["Trading outside preferred sessions", "Slight overconfidence"],
    grade: "A",
  },
  {
    id: "r3",
    week_start: "2024-01-01",
    week_end: "2024-01-07",
    summary: "Challenging start to the year with some revenge trading after initial losses. Recovery showed good mental resilience.",
    total_trades: 15,
    total_pnl: -220,
    win_rate: 40,
    avg_r: -0.8,
    patterns_detected: ["revenge_trading", "overtrading", "moved_stop_loss"],
    top_suggestion: "Take a day break after 2 consecutive losses to reset emotional state.",
    strengths: ["Good recovery after losses", "Recognized mistakes quickly"],
    weaknesses: ["Revenge trading", "Moving stop losses", "Overtrading after losses", "Poor risk management"],
    grade: "D",
  },
];

const getGradeColor = (grade: string) => {
  switch (grade) {
    case "A": return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    case "B": return "text-blue-400 bg-blue-500/10 border-blue-500/20";
    case "C": return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    case "D": return "text-orange-400 bg-orange-500/10 border-orange-500/20";
    case "F": return "text-red-400 bg-red-500/10 border-red-500/20";
    default: return "text-slate-400 bg-slate-500/10 border-slate-500/20";
  }
};

export default function ReportsPage() {
  const [expandedReport, setExpandedReport] = useState<string | null>(null);

  const toggleReport = (id: string) => {
    setExpandedReport(expandedReport === id ? null : id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-100">Weekly Reports</h1>
          <p className="text-slate-400 mt-1">
            AI-generated insights and performance reviews
          </p>
        </div>
        <Button variant="outline" className="gap-2">
          <Download className="h-4 w-4" />
          Export All
        </Button>
      </div>

      {/* Reports List */}
      <div className="space-y-4">
        {mockReports.map((report) => (
          <Card key={report.id} className="overflow-hidden">
            <CardHeader 
              className="cursor-pointer hover:bg-slate-800/50 transition-colors"
              onClick={() => toggleReport(report.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-lg bg-slate-800 flex items-center justify-center">
                    <FileText className="h-5 w-5 text-emerald-400" />
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <CardTitle className="text-lg">
                        Week of {formatDate(report.week_start, "MMM dd")} - {formatDate(report.week_end, "MMM dd")}
                      </CardTitle>
                      <Badge className={cn("text-xs font-bold", getGradeColor(report.grade))}>
                        Grade {report.grade}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
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
                    <ChevronUp className="h-5 w-5 text-slate-400" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-slate-400" />
                  )}
                </div>
              </div>
            </CardHeader>

            {expandedReport === report.id && (
              <CardContent className="border-t border-slate-800">
                <div className="space-y-6 pt-6">
                  {/* Summary */}
                  <div>
                    <h4 className="font-semibold text-slate-200 mb-2">Summary</h4>
                    <p className="text-sm text-slate-300 leading-relaxed">{report.summary}</p>
                  </div>

                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 rounded-lg bg-slate-800/50">
                      <div className="text-lg font-bold text-slate-100">{report.total_trades}</div>
                      <div className="text-xs text-slate-400">Trades</div>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-slate-800/50">
                      <div className={cn("text-lg font-bold", report.total_pnl >= 0 ? "text-emerald-400" : "text-red-400")}>
                        {formatCurrency(report.total_pnl)}
                      </div>
                      <div className="text-xs text-slate-400">P&L</div>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-slate-800/50">
                      <div className="text-lg font-bold text-slate-100">{formatPercent(report.win_rate)}</div>
                      <div className="text-xs text-slate-400">Win Rate</div>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-slate-800/50">
                      <div className={cn("text-lg font-bold", report.avg_r >= 0 ? "text-emerald-400" : "text-red-400")}>
                        {report.avg_r >= 0 ? "+" : ""}{report.avg_r.toFixed(1)}R
                      </div>
                      <div className="text-xs text-slate-400">Avg R</div>
                    </div>
                  </div>

                  {/* AI Insights */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Strengths */}
                    <div>
                      <h4 className="font-semibold text-emerald-400 mb-3 flex items-center gap-2">
                        💪 Strengths
                      </h4>
                      <ul className="space-y-2">
                        {report.strengths.map((strength, i) => (
                          <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                            <span className="text-emerald-400 text-xs mt-1">✓</span>
                            {strength}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Areas for Improvement */}
                    <div>
                      <h4 className="font-semibold text-amber-400 mb-3 flex items-center gap-2">
                        🎯 Areas for Improvement
                      </h4>
                      <ul className="space-y-2">
                        {report.weaknesses.map((weakness, i) => (
                          <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                            <span className="text-amber-400 text-xs mt-1">!</span>
                            {weakness}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Top Suggestion */}
                  <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    <h4 className="font-semibold text-slate-200 mb-2 flex items-center gap-2">
                      <Brain className="h-4 w-4 text-emerald-400" />
                      AI Recommendation
                    </h4>
                    <p className="text-sm text-slate-300">{report.top_suggestion}</p>
                  </div>

                  {/* Patterns Detected */}
                  {report.patterns_detected.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-slate-200 mb-3">Behavioral Patterns</h4>
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
    </div>
  );
}
