"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AiScoreBadge } from "./ai-score-badge";
import { CheckCircle2, AlertTriangle, Lightbulb, Brain } from "lucide-react";
import type { TradeScore } from "@/types";

interface AiAnalysisCardProps {
  score: TradeScore;
}

export function AiAnalysisCard({ score }: AiAnalysisCardProps) {
  const strengths = [
    ...(score.rule_adherence ? ["Rules followed"] : []),
    ...(score.checklist_completed ? ["Checklist completed"] : []),
    ...(score.score >= 7 ? ["High-quality setup"] : []),
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Brain className="h-4 w-4 text-emerald-400" />
          AI Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Score */}
        <div className="flex items-center gap-4">
          <AiScoreBadge score={score.score} size="lg" />
          <div>
            <p className="text-sm font-medium text-slate-200">
              Trade Score: {score.score}/10
            </p>
            <p className="text-xs text-slate-400">
              Confidence: {(score.confidence * 100).toFixed(0)}%
            </p>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="w-full bg-slate-800 rounded-full h-1.5">
          <div
            className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${score.confidence * 100}%` }}
          />
        </div>

        {/* Strengths */}
        {strengths.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Strengths
            </p>
            {strengths.map((s, i) => (
              <div key={i} className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                <span className="text-sm text-slate-300">{s}</span>
              </div>
            ))}
          </div>
        )}

        {/* Issues */}
        {score.issues.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Issues
            </p>
            {score.issues.map((issue, i) => (
              <div key={i} className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
                <span className="text-sm text-slate-300">{issue}</span>
              </div>
            ))}
          </div>
        )}

        {/* Suggestion */}
        {score.suggestion && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-slate-800/50 border border-slate-700">
            <Lightbulb className="h-4 w-4 text-amber-400 mt-0.5 shrink-0" />
            <p className="text-sm text-slate-300">{score.suggestion}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
