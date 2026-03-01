"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Brain,
  TrendingUp,
  ClipboardCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface PostTradeReviewCardProps {
  review: Record<string, any>;
  /** When true renders without outer Card wrapper (for embedding) */
  embedded?: boolean;
}

function ScoreRing({ value, label, color }: { value: number; label: string; color: string }) {
  const pct = Math.min(Math.max(value / 10, 0), 1);
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const strokeDash = pct * circumference;

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-14 h-14">
        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
          <circle
            cx="28"
            cy="28"
            r={radius}
            fill="none"
            stroke="rgb(51 65 85)"
            strokeWidth="4"
          />
          <circle
            cx="28"
            cy="28"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={`${strokeDash} ${circumference}`}
            className="transition-all duration-700"
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-slate-100">
          {value}
        </span>
      </div>
      <p className="text-[11px] text-slate-400 text-center leading-tight">{label}</p>
    </div>
  );
}

export function PostTradeReviewCard({ review, embedded = false }: PostTradeReviewCardProps) {
  const execution_score: number = review?.execution_score ?? 0;
  const plan_adherence: number = review?.plan_adherence ?? 0;
  const summary: string = review?.summary ?? "";
  const lessons: string[] = review?.lessons ?? [];
  const what_went_well: string[] = review?.what_went_well ?? [];
  const what_to_improve: string[] = review?.what_to_improve ?? [];
  const emotional_assessment: string = review?.emotional_assessment ?? "";

  const execColor =
    execution_score >= 7 ? "#34d399" : execution_score >= 5 ? "#fbbf24" : "#f87171";
  const planColor =
    plan_adherence >= 7 ? "#34d399" : plan_adherence >= 5 ? "#fbbf24" : "#f87171";

  const inner = (
    <div className="space-y-4">
      {/* Scores */}
      <div className="flex items-center gap-6">
        <ScoreRing value={execution_score} label="Execution" color={execColor} />
        <ScoreRing value={plan_adherence} label="Plan Adherence" color={planColor} />
        {summary && (
          <p className="flex-1 text-sm text-slate-300 leading-relaxed">{summary}</p>
        )}
      </div>

      {/* What went well */}
      {what_went_well.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            What Went Well
          </p>
          {what_went_well.map((item: string, i: number) => (
            <div key={i} className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <span className="text-sm text-slate-300">{item}</span>
            </div>
          ))}
        </div>
      )}

      {/* What to improve */}
      {what_to_improve.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            What to Improve
          </p>
          {what_to_improve.map((item: string, i: number) => (
            <div key={i} className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
              <span className="text-sm text-slate-300">{item}</span>
            </div>
          ))}
        </div>
      )}

      {/* Lessons */}
      {lessons.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Lessons Learned
          </p>
          {lessons.map((lesson: string, i: number) => (
            <div key={i} className="flex items-start gap-2">
              <Lightbulb className="h-4 w-4 text-yellow-400 shrink-0 mt-0.5" />
              <span className="text-sm text-slate-300">{lesson}</span>
            </div>
          ))}
        </div>
      )}

      {/* Emotional assessment */}
      {emotional_assessment && (
        <div className="p-3 rounded-lg bg-surface-muted/30 border border-border/50">
          <p className="text-xs font-medium text-muted uppercase tracking-wider mb-1 flex items-center gap-1">
            <Brain className="h-3 w-3" />
            Emotional Assessment
          </p>
          <p className="text-sm text-slate-300">{emotional_assessment}</p>
        </div>
      )}
    </div>
  );

  if (embedded) return inner;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <ClipboardCheck className="h-4 w-4 text-accent" />
          Post-Trade Review
        </CardTitle>
      </CardHeader>
      <CardContent>{inner}</CardContent>
    </Card>
  );
}
