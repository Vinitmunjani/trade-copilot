"use client";

import React from "react";
import { X, Brain, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Lightbulb, BarChart2 } from "lucide-react";
import { useAiPanelStore } from "@/stores/ai-panel-store";
import { cn } from "@/lib/utils";

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 8 ? "text-accent bg-accent/10 border-accent/30" :
    score >= 5 ? "text-yellow-400 bg-yellow-400/10 border-yellow-400/30" :
    "text-danger bg-danger/10 border-danger/30";
  return (
    <span className={cn("inline-flex items-center justify-center w-12 h-12 rounded-full border-2 text-xl font-bold", color)}>
      {score}
    </span>
  );
}

function Section({ icon: Icon, title, children }: { icon: React.ElementType; title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-muted">
        <Icon className="h-3.5 w-3.5" />
        {title}
      </div>
      <div className="text-sm text-foreground/90 leading-relaxed">{children}</div>
    </div>
  );
}

function TagList({ items, variant }: { items: string[]; variant: "success" | "danger" | "muted" }) {
  const cls =
    variant === "success" ? "bg-accent/10 text-accent border-accent/20" :
    variant === "danger" ? "bg-danger/10 text-danger border-danger/20" :
    "bg-surface-muted text-muted border-border";
  if (!items?.length) return <span className="text-muted text-sm">None detected</span>;
  return (
    <ul className="flex flex-wrap gap-1.5">
      {items.map((item, i) => (
        <li key={i} className={cn("rounded-md border px-2 py-1 text-xs leading-snug", cls)}>
          {item}
        </li>
      ))}
    </ul>
  );
}

export function AiAnalysisPanel() {
  const { isOpen, close, aiScore, aiAnalysis, aiReview } = useAiPanelStore();

  const isAnalyzing = isOpen && aiScore === null && !aiAnalysis;

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px]"
          onClick={close}
          aria-hidden="true"
        />
      )}

      {/* Drawer */}
      <aside
        className={cn(
          "fixed right-0 top-0 z-50 h-full w-full max-w-sm border-l border-border bg-surface/95 backdrop-blur-2xl shadow-2xl transition-transform duration-300 ease-out overflow-y-auto",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
        aria-label="AI Trade Analysis"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-2.5">
            <Brain className="h-5 w-5 text-accent" />
            <span className="font-semibold text-foreground">AI Analysis</span>
          </div>
          <button
            onClick={close}
            className="rounded-md p-1.5 text-muted hover:text-foreground hover:bg-surface-muted transition-colors"
            aria-label="Close panel"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-6">
          {isAnalyzing ? (
            /* Skeleton loading state */
            <div className="space-y-4 animate-pulse">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-surface-muted" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-surface-muted rounded w-2/3" />
                  <div className="h-2 bg-surface-muted rounded w-1/2" />
                </div>
              </div>
              <div className="h-2 bg-surface-muted rounded w-full" />
              <div className="h-2 bg-surface-muted rounded w-5/6" />
              <div className="h-2 bg-surface-muted rounded w-4/6" />
              <p className="text-center text-xs text-muted pt-2">Analyzing market context…</p>
            </div>
          ) : aiAnalysis ? (
            <>
              {/* Score + Confidence */}
              <div className="flex items-center gap-4">
                {aiScore != null && <ScoreBadge score={aiScore} />}
                <div>
                  <p className="text-xs text-muted">Trade Quality Score</p>
                  {aiAnalysis.confidence != null && (
                    <p className="text-xs text-muted mt-0.5">
                      Confidence: <span className="text-foreground font-medium">{Math.round(aiAnalysis.confidence * 100)}%</span>
                    </p>
                  )}
                  {aiAnalysis.market_alignment && (
                    <p className="text-xs text-muted mt-0.5">
                      Market alignment:{" "}
                      <span className={cn("font-medium", aiAnalysis.market_alignment === "aligned" ? "text-accent" : "text-danger")}>
                        {aiAnalysis.market_alignment}
                      </span>
                    </p>
                  )}
                </div>
              </div>

              {/* Summary */}
              {aiAnalysis.summary && (
                <Section icon={BarChart2} title="Summary">
                  {aiAnalysis.summary}
                </Section>
              )}

              {/* Risk Assessment */}
              {aiAnalysis.risk_assessment && (
                <Section icon={AlertTriangle} title="Risk Assessment">
                  {aiAnalysis.risk_assessment}
                </Section>
              )}

              {/* Strengths */}
              {aiAnalysis.strengths?.length > 0 && (
                <Section icon={CheckCircle} title="Strengths">
                  <TagList items={aiAnalysis.strengths} variant="success" />
                </Section>
              )}

              {/* Issues */}
              {aiAnalysis.issues?.length > 0 && (
                <Section icon={TrendingDown} title="Issues">
                  <TagList items={aiAnalysis.issues} variant="danger" />
                </Section>
              )}

              {/* Suggestion */}
              {aiAnalysis.suggestion && (
                <div className="rounded-xl border border-accent/20 bg-accent/5 p-4 space-y-1">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-accent">
                    <Lightbulb className="h-3.5 w-3.5" />
                    Suggestion
                  </div>
                  <p className="text-sm text-foreground/90 leading-relaxed">{aiAnalysis.suggestion}</p>
                </div>
              )}
            </>
          ) : null}

          {/* Post-trade review section */}
          {aiReview && (
            <div className="border-t border-border pt-5 space-y-4">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-muted">
                <TrendingUp className="h-3.5 w-3.5" />
                Post-Trade Review
              </div>
              {aiReview.summary && (
                <p className="text-sm text-foreground/90 leading-relaxed">{aiReview.summary}</p>
              )}
              {aiReview.lessons?.length > 0 && (
                <Section icon={Lightbulb} title="Key Lessons">
                  <TagList items={aiReview.lessons} variant="muted" />
                </Section>
              )}
              {aiReview.suggestion && (
                <div className="rounded-xl border border-border bg-surface-muted/60 p-4">
                  <p className="text-sm text-foreground/80 leading-relaxed">{aiReview.suggestion}</p>
                </div>
              )}
            </div>
          )}

          {!isAnalyzing && !aiAnalysis && !aiReview && (
            <div className="flex flex-col items-center justify-center py-12 text-center gap-3">
              <Brain className="h-10 w-10 text-muted/40" />
              <p className="text-sm text-muted">No analysis available yet.</p>
              <p className="text-xs text-muted/70">Analysis will appear here when a trade is placed.</p>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
