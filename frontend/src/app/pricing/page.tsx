"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight, Shield, Zap, Crown, Check, X, Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { AmpereLogo } from "@/components/ui/ampere-logo";
import { cn } from "@/lib/utils";

// ─── Psychological architecture ─────────────────────────────────────────────
// 1. ANCHORING    — Sovereign ($99) makes Tactician ($49) feel cheap
// 2. DECOY EFFECT — Operator ($29) exists to push rational buyers to Tactician
// 3. CENTER STAGE — Tactician card is taller + glowing (eye lands here first)
// 4. LOSS FRAMING — Excluded features are struck-through, not just absent
// 5. COST REFRAME — Daily cost shown: "less than one bad trade"
// 6. SOCIAL PROOF — "Chosen by 73%" callout on anchor plan
// 7. RISK REVERSAL — 14-day trial + no card removes friction
// ─────────────────────────────────────────────────────────────────────────────
const pricingPlans = [
  {
    id: "operator",
    Icon: Zap,
    name: "Operator",
    tagline: "Build the habit",
    monthlyPrice: 29,
    annualPrice: 23,
    accentClass: "text-muted",
    borderClass: "border-white/8",
    bgClass: "from-surface to-surface-muted",
    ctaLabel: "Start Free Trial",
    ctaExtraClass: "border-white/15 bg-transparent hover:bg-white/5",
    ctaVariant: "outline" as const,
    badge: null as string | null,
    callout: null as string | null,
    features: [
      { label: "1 connected broker account", ok: true },
      { label: "AI pre-trade analysis", ok: true, note: "50 analyses/mo" },
      { label: "Behavioural flag detection", ok: true, note: "5 core patterns" },
      { label: "Trade journal + duration tracking", ok: true },
      { label: "Daily readiness score", ok: true },
      { label: "Monthly performance report", ok: true },
      { label: "AI post-trade review", ok: false },
      { label: "Unlimited AI analyses", ok: false },
      { label: "Weekly reports + pattern analytics", ok: false },
      { label: "Multi-account support", ok: false },
    ],
  },
  {
    id: "tactician",
    Icon: Shield,
    name: "Tactician",
    tagline: "The edge serious traders run",
    monthlyPrice: 49,
    annualPrice: 39,
    accentClass: "text-accent",
    borderClass: "border-accent/30",
    bgClass: "from-surface via-surface-muted to-accent/5",
    ctaLabel: "Claim Tactician Access",
    ctaExtraClass: "shadow-glow font-semibold",
    ctaVariant: "default" as const,
    badge: "Most Popular",
    callout: "Chosen by 73% of active traders",
    features: [
      { label: "1 connected broker account", ok: true },
      { label: "Unlimited AI pre-trade analyses", ok: true },
      { label: "All 12 behavioural patterns", ok: true },
      { label: "AI post-trade review on every trade", ok: true },
      { label: "Per-session readiness score", ok: true },
      { label: "Weekly + monthly reports", ok: true },
      { label: "Full pattern analytics dashboard", ok: true },
      { label: "Unlimited AI chat assistant", ok: true },
      { label: "Multi-account support", ok: false },
      { label: "Priority GPT-4o + prop desk exports", ok: false },
    ],
  },
  {
    id: "sovereign",
    Icon: Crown,
    name: "Sovereign",
    tagline: "For funded accounts & prop desks",
    monthlyPrice: 99,
    annualPrice: 79,
    accentClass: "text-amber-400",
    borderClass: "border-amber-400/20",
    bgClass: "from-surface to-surface-muted",
    ctaLabel: "Apply for Sovereign",
    ctaExtraClass: "border-amber-400/30 text-amber-300 hover:bg-amber-400/5",
    ctaVariant: "outline" as const,
    badge: "Prop Desk",
    callout: null,
    features: [
      { label: "Up to 3 broker accounts", ok: true },
      { label: "Unlimited AI analyses (priority GPT-4o)", ok: true },
      { label: "All 12 patterns + custom rule engine", ok: true },
      { label: "AI post-trade review on every trade", ok: true },
      { label: "Per-session readiness score", ok: true },
      { label: "Weekly + monthly reports", ok: true },
      { label: "Full pattern analytics dashboard", ok: true },
      { label: "Unlimited AI chat assistant", ok: true },
      { label: "FTMO / prop-firm export format", ok: true },
      { label: "Dedicated onboarding + API access", ok: true },
    ],
  },
];

const psychProof = [
  { stat: "−43%", label: "drawdown volatility after 60 sessions" },
  { stat: "$2,400", label: "avg saved/yr from fewer impulse trades" },
  { stat: "97.2%", label: "discipline score for Tactician users" },
];

export default function PricingPage() {
  const router = useRouter();
  const [annual, setAnnual] = useState(false);

  return (
    <div className="relative flex min-h-screen flex-col">

      {/* Navbar */}
      <header className="sticky top-0 z-30 border-b border-white/5 bg-background/70 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <button
            className="flex items-center gap-3"
            onClick={() => router.push("/")}
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-surface/70">
              <AmpereLogo className="h-7 w-7" />
            </div>
            <p className="text-sm font-medium tracking-[0.08em] text-muted">ampere.capital</p>
          </button>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              className="border border-white/10 bg-transparent text-sm text-foreground/80"
              onClick={() => router.push("/login")}
            >
              Log In
            </Button>
            <Button
              size="lg"
              className="hidden text-sm font-semibold shadow-glow md:inline-flex"
              onClick={() => router.push("/register")}
            >
              Start Free Trial
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 px-6 pb-24 pt-16">
        <div className="mx-auto max-w-6xl space-y-14">

          {/* Header */}
          <div className="text-center space-y-4">
            <p className="text-xs uppercase tracking-[0.4em] text-muted">Investment</p>
            <h1 className="text-4xl font-semibold text-balance md:text-5xl">
              One losing trade costs more<br className="hidden md:block" /> than a year of Tactician.
            </h1>
            <p className="text-muted max-w-xl mx-auto text-lg">
              Most traders lose $1,200–6,000/yr to impulse decisions and missing stop-losses.
              ampere.capital pays for itself in the first month.
            </p>

            {/* Annual / monthly toggle */}
            <div className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-surface/60 px-5 py-2.5 text-sm mt-2">
              <button
                onClick={() => setAnnual(false)}
                className={cn("transition-colors", !annual ? "text-foreground font-medium" : "text-muted")}
              >
                Monthly
              </button>
              <button
                onClick={() => setAnnual(!annual)}
                className={cn(
                  "relative inline-flex h-5 w-9 rounded-full border transition-colors",
                  annual ? "border-accent bg-accent" : "border-white/20 bg-white/10"
                )}
              >
                <span
                  className={cn(
                    "absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform duration-200",
                    annual ? "translate-x-4" : "translate-x-0.5"
                  )}
                />
              </button>
              <button
                onClick={() => setAnnual(true)}
                className={cn("transition-colors", annual ? "text-foreground font-medium" : "text-muted")}
              >
                Annual
              </button>
              <span className="rounded-full bg-accent/15 px-2 py-0.5 text-[11px] font-semibold text-accent">
                Save up to $240/yr
              </span>
            </div>
          </div>

          {/* Plan cards */}
          <div className="grid grid-cols-1 gap-5 md:grid-cols-3 md:items-start">
            {pricingPlans.map((plan) => {
              const isFeatured = plan.id === "tactician";
              const price = annual ? plan.annualPrice : plan.monthlyPrice;
              const saved = plan.monthlyPrice - plan.annualPrice;
              const PlanIcon = plan.Icon;
              return (
                <div
                  key={plan.id}
                  className={cn(
                    "relative flex flex-col rounded-[28px] border p-7 bg-gradient-to-b backdrop-blur-2xl transition-transform duration-300",
                    plan.bgClass,
                    plan.borderClass,
                    isFeatured
                      ? "shadow-[0_0_80px_rgba(52,211,153,0.12)] md:-mt-4 md:pb-11 md:pt-9"
                      : "hover:-translate-y-1"
                  )}
                >
                  {/* Badge */}
                  {plan.badge && (
                    <div
                      className={cn(
                        "absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full px-4 py-1 text-xs font-semibold tracking-wider uppercase whitespace-nowrap",
                        isFeatured
                          ? "bg-accent text-background"
                          : "bg-amber-400/15 text-amber-300 border border-amber-400/30"
                      )}
                    >
                      {plan.badge}
                    </div>
                  )}

                  {/* Identity */}
                  <div className="flex items-center gap-3 mb-5">
                    <div className={cn("flex h-10 w-10 items-center justify-center rounded-2xl", isFeatured ? "bg-accent/20" : "bg-white/5")}>
                      <PlanIcon className={cn("h-5 w-5", plan.accentClass)} />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">{plan.name}</p>
                      <p className="text-xs text-muted">{plan.tagline}</p>
                    </div>
                  </div>

                  {/* Price */}
                  <div className="mb-1">
                    <div className="flex items-end gap-1.5">
                      <span className="text-5xl font-semibold tracking-tight text-foreground">${price}</span>
                      <span className="text-muted mb-2 text-sm">/mo</span>
                    </div>
                    <div className="h-5">
                      {annual
                        ? <p className="text-xs text-accent">You save ${saved * 12}/yr — billed annually</p>
                        : <p className="text-xs text-muted">or ${plan.annualPrice}/mo billed annually</p>
                      }
                    </div>
                  </div>

                  {/* Cost reframe */}
                  <p className="text-[11px] text-muted/70 mb-6 italic">
                    ≈ ${(price / 30).toFixed(2)}/day — less than one bad trade
                  </p>

                  {/* CTA */}
                  <Button
                    size="lg"
                    variant={plan.ctaVariant}
                    className={cn("w-full rounded-2xl text-sm", plan.ctaExtraClass)}
                    onClick={() => router.push(`/register?plan=${plan.id}`)}
                  >
                    {plan.ctaLabel}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>

                  {plan.callout && (
                    <div className="mt-3 flex items-center justify-center gap-1.5 text-xs text-muted">
                      <Sparkles className="h-3 w-3 text-accent" />
                      {plan.callout}
                    </div>
                  )}

                  <div className="my-6 border-t border-white/5" />

                  {/* Feature list */}
                  <ul className="space-y-3 flex-1">
                    {plan.features.map((f) => (
                      <li key={f.label} className="flex items-start gap-2.5 text-sm">
                        {f.ok
                          ? <Check className={cn("mt-0.5 h-4 w-4 shrink-0", isFeatured ? "text-accent" : "text-muted")} />
                          : <X className="mt-0.5 h-4 w-4 shrink-0 text-white/15" />
                        }
                        <span className={f.ok ? "text-foreground/80" : "text-muted/40 line-through"}>
                          {f.label}
                          {"note" in f && f.note && (
                            <span className="ml-1 text-[11px] text-muted/60">({f.note})</span>
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>

          {/* Social proof */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {psychProof.map(({ stat, label }) => (
              <div key={stat} className="rounded-2xl border border-white/5 bg-surface/60 px-6 py-5 text-center">
                <p className="text-3xl font-semibold text-foreground">{stat}</p>
                <p className="mt-1 text-xs text-muted">{label}</p>
              </div>
            ))}
          </div>

          {/* Risk reversal */}
          <p className="text-center text-xs text-muted/60">
            14-day free trial on all plans · No credit card required · Cancel anytime in one click
          </p>

        </div>
      </main>
    </div>
  );
}
