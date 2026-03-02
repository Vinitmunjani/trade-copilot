"use client";

import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useBillingSubscription } from "@/hooks/use-billing-subscription";
import { useToast } from "@/hooks/use-toast";
import api from "@/lib/api";
import { CreditCard, Loader2, Shield, Zap, Crown, Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

const PLANS = [
  {
    id: "operator",
    name: "Operator",
    monthlyPrice: 29,
    annualPrice: 23,
    Icon: Zap,
    accentClass: "text-muted",
    borderClass: "border-white/8",
    bgClass: "from-surface to-surface-muted",
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
    name: "Tactician",
    monthlyPrice: 49,
    annualPrice: 39,
    Icon: Shield,
    accentClass: "text-accent",
    borderClass: "border-accent/30",
    bgClass: "from-surface via-surface-muted to-accent/5",
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
      { label: "Priority GPT-5.2 + prop desk exports", ok: false },
    ],
  },
  {
    id: "sovereign",
    name: "Sovereign",
    monthlyPrice: 99,
    annualPrice: 79,
    Icon: Crown,
    accentClass: "text-amber-400",
    borderClass: "border-amber-400/20",
    bgClass: "from-surface to-surface-muted",
    features: [
      { label: "Up to 3 broker accounts", ok: true },
      { label: "Unlimited AI analyses (priority GPT-5.2)", ok: true },
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
] as const;

export default function BillingPage() {
  const { subscription, isLoading, error, refetch } = useBillingSubscription();
  const { toast } = useToast();

  const [selectedPlan, setSelectedPlan] = useState<(typeof PLANS)[number]["id"]>("operator");
  const [interval, setInterval] = useState<"monthly" | "annual">("monthly");
  const [isCheckoutLoading, setIsCheckoutLoading] = useState(false);
  const [isPortalLoading, setIsPortalLoading] = useState(false);

  const currentPlanId = useMemo(() => {
    const p = (subscription?.plan || "free").toLowerCase();
    if (p === "operator" || p === "tactician" || p === "sovereign") {
      return p as (typeof PLANS)[number]["id"];
    }
    return "operator" as const;
  }, [subscription?.plan]);

  const currentPlanLabel = useMemo(() => {
    const p = (subscription?.plan || "free").toLowerCase();
    if (p === "operator" || p === "tactician" || p === "sovereign") {
      return p.charAt(0).toUpperCase() + p.slice(1);
    }
    if (p === "unknown") return "Active";
    return "Free";
  }, [subscription?.plan]);

  const planRank: Record<(typeof PLANS)[number]["id"], number> = {
    operator: 1,
    tactician: 2,
    sovereign: 3,
  };

  const isUpgrade = planRank[selectedPlan] > planRank[currentPlanId];
  const ctaLabel = selectedPlan === currentPlanId ? "Current Plan" : isUpgrade ? "Upgrade Plan" : "Change Plan";

  const handleCheckout = async () => {
    if (selectedPlan === currentPlanId) {
      return;
    }

    setIsCheckoutLoading(true);
    try {
      const origin = window.location.origin;
      const { data } = await api.post("/billing/checkout", {
        plan: selectedPlan,
        interval,
        success_url: `${origin}/billing?checkout=success`,
        cancel_url: `${origin}/billing?checkout=cancel`,
      });

      if (data?.url) {
        window.location.href = data.url;
        return;
      }

      toast({
        title: "Checkout session created",
        description: "Open Stripe checkout from your latest response URL.",
        variant: "info",
      });
    } catch (e: any) {
      toast({
        title: "Checkout failed",
        description: e?.response?.data?.detail || e?.message || "Unable to start checkout",
        variant: "destructive",
      });
    } finally {
      setIsCheckoutLoading(false);
    }
  };

  const handlePortal = async () => {
    setIsPortalLoading(true);
    try {
      const origin = window.location.origin;
      const { data } = await api.post("/billing/portal", {
        return_url: `${origin}/billing`,
      });
      if (!data?.url) throw new Error("No portal URL returned");
      window.location.href = data.url;
    } catch (e: any) {
      toast({
        title: "Portal unavailable",
        description: e?.response?.data?.detail || e?.message || "Unable to open billing portal",
        variant: "destructive",
      });
    } finally {
      setIsPortalLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.4em] text-muted">Account</p>
        <h1 className="mt-2 text-3xl font-semibold text-foreground">Billing</h1>
      </div>

      <Card className="border-white/5 bg-surface/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Current plan
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {isLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading subscription...
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between rounded-lg border border-white/5 bg-surface-muted/50 p-4">
                <div>
                  <p className="text-sm text-muted">Plan</p>
                  <p className="text-lg font-semibold text-foreground">{currentPlanLabel}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted">Status</p>
                  <p className="text-sm font-medium text-foreground capitalize">{subscription?.status || "inactive"}</p>
                </div>
              </div>

              {subscription?.current_period_end && (
                <p className="text-sm text-muted">
                  Renews on {new Date(subscription.current_period_end).toLocaleDateString()}
                </p>
              )}

              {error && <p className="text-sm text-red-300">{error}</p>}

              <div className="flex flex-wrap gap-3">
                <Button variant="outline" onClick={refetch}>Refresh</Button>
                <Button onClick={handlePortal} disabled={isPortalLoading || !subscription?.stripe_customer_id}>
                  {isPortalLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Manage billing
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="space-y-4 rounded-3xl border border-white/5 bg-surface/50 p-6">
        <h2 className="text-3xl font-semibold text-foreground">Upgrade or change plan</h2>
          <div className="inline-flex rounded-full border border-white/10 bg-surface-muted/40 p-1">
            <button
              onClick={() => setInterval("monthly")}
              className={`rounded-full px-3 py-1 text-sm ${interval === "monthly" ? "bg-white/10 text-foreground" : "text-muted"}`}
            >
              Monthly
            </button>
            <button
              onClick={() => setInterval("annual")}
              className={`rounded-full px-3 py-1 text-sm ${interval === "annual" ? "bg-white/10 text-foreground" : "text-muted"}`}
            >
              Annual
            </button>
          </div>

          <div className="grid grid-cols-1 gap-5 md:grid-cols-3 md:items-start">
            {PLANS.map((plan) => {
              const active = selectedPlan === plan.id;
              const isCurrent = currentPlanId === plan.id;
              const isFeatured = plan.id === "tactician";
              const PlanIcon = plan.Icon;
              const price = interval === "monthly" ? plan.monthlyPrice : plan.annualPrice;
              const saved = plan.monthlyPrice - plan.annualPrice;
              return (
                <button
                  key={plan.id}
                  onClick={() => setSelectedPlan(plan.id)}
                  className={cn(
                    "relative flex flex-col rounded-[28px] border p-7 text-left bg-gradient-to-b backdrop-blur-2xl transition-transform duration-300",
                    plan.bgClass,
                    active ? "border-accent/50" : plan.borderClass,
                    isFeatured ? "shadow-[0_0_80px_rgba(52,211,153,0.12)] md:-mt-4 md:pb-11 md:pt-9" : "hover:-translate-y-1"
                  )}
                >
                  {isCurrent && (
                    <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-accent px-4 py-1 text-xs font-semibold uppercase tracking-wider whitespace-nowrap text-background">
                      Current Plan
                    </span>
                  )}

                  {!isCurrent && isFeatured && (
                    <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-accent px-4 py-1 text-xs font-semibold tracking-wider uppercase whitespace-nowrap text-background">
                      Popular
                    </span>
                  )}

                  <div className="mb-5 flex items-center gap-3">
                    <div className={cn("flex h-10 w-10 items-center justify-center rounded-2xl", isFeatured ? "bg-accent/20" : "bg-white/5")}>
                      <PlanIcon className={cn("h-5 w-5", plan.accentClass)} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="font-semibold text-foreground">{plan.name}</p>
                        {active && <Check className="h-4 w-4 text-accent" />}
                      </div>
                    </div>
                  </div>

                  <div className="mb-1">
                    <div className="flex items-end gap-1.5">
                      <span className="text-5xl font-semibold tracking-tight text-foreground">${price}</span>
                      <span className="mb-2 text-sm text-muted">/mo</span>
                    </div>
                    <div className="h-5">
                      {interval === "monthly" ? (
                        <p className="text-xs text-muted">or ${plan.annualPrice}/mo billed annually</p>
                      ) : (
                        <p className="text-xs text-accent">You save ${saved * 12}/yr — billed annually</p>
                      )}
                    </div>
                  </div>

                  <p className="text-[11px] text-muted/70 italic">
                    ≈ ${(price / 30).toFixed(2)}/day — less than one bad trade
                  </p>

                  <div className="my-6 border-t border-white/5" />

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
                </button>
              );
            })}
          </div>

          <Button onClick={handleCheckout} disabled={isCheckoutLoading || selectedPlan === currentPlanId}>
            {isCheckoutLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {ctaLabel}
          </Button>
      </div>
    </div>
  );
}
