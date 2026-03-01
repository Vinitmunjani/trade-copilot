"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AiScoreBadge } from "./ai-score-badge";
import { CheckCircle2, AlertTriangle, Lightbulb, Brain } from "lucide-react";

interface AiAnalysisCardProps {
  analysis: Record<string, any>;
  score: number;
}

export function AiAnalysisCard({ analysis, score }: AiAnalysisCardProps) {
  const confidence = analysis?.confidence || 0;
  const issues = analysis?.issues || [];
  const strengths = analysis?.strengths || [];
  const suggestion = analysis?.suggestion || "";
  const market_alignment = analysis?.market_alignment || "";
  const risk_assessment = analysis?.risk_assessment || "";

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
          <AiScoreBadge score={score} size="lg" />
          <div>
            <p className="text-sm font-medium text-slate-200">
              Trade Score: {score}/10
            </p>
            <p className="text-xs text-slate-400">
              Confidence: {(confidence * 100).toFixed(0)}%
            </p>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="w-full bg-surface-contrast rounded-full h-1.5">
          <div
            className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(confidence * 100, 100)}%` }}
          />
        </div>

        {/* Strengths */}
        {strengths.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Strengths
            </p>
            {strengths.map((s: string, i: number) => (
              <div key={i} className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                <span className="text-sm text-slate-300">{s}</span>
              </div>
            ))}
          </div>
        )}

        {/* Issues */}
        {issues.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Issues
            </p>
            {issues.map((issue: string, i: number) => (
              <div key={i} className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
                <span className="text-sm text-slate-300">{issue}</span>
              </div>
            ))}
          </div>
        )}

        {/* Suggestion */}
        {suggestion && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-surface-muted/50 border border-border/60">
            <Lightbulb className="h-4 w-4 text-amber-400 mt-0.5 shrink-0" />
            <p className="text-sm text-slate-300">{suggestion}</p>
          </div>
        )}

        {/* Market Alignment */}
        {market_alignment && (
          <div className="p-3 rounded-lg bg-surface-muted/30 border border-border/60">
            <p className="text-xs font-medium text-muted uppercase tracking-wider mb-1">
              Market Alignment
            </p>
            <p className="text-sm text-slate-300">{market_alignment}</p>
          </div>
        )}

        {/* Risk Assessment */}
        {risk_assessment && (
          <div className="p-3 rounded-lg bg-surface-muted/30 border border-border/60">
            <p className="text-xs font-medium text-muted uppercase tracking-wider mb-1">
              Risk Assessment
            </p>
            <p className="text-sm text-slate-300">{risk_assessment}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
