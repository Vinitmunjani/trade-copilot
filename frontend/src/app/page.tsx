"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Shield,
  Brain,
  BarChart3,
  Sparkles,
  Signal,
  Radar,
  Waves,
  BookOpen,
  Clock,
  TrendingUp,
  AlertTriangle,
  FileText,
  MessageSquare,
  Activity,
  CheckSquare,
  Target,
  LineChart,
  Zap,
  ShieldAlert,
  ScanLine,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { AmpereLogo } from "@/components/ui/ampere-logo";

const navLinks = [
  { label: "Product", href: "#product" },
  { label: "Method", href: "#method" },
  { label: "Features", href: "#features" },
  { label: "Security", href: "#security" },
  { label: "Pricing", href: "/pricing" },
];

const featureCategories = [
  {
    icon: Brain,
    label: "AI Intelligence",
    color: "text-accent",
    bg: "bg-accent/10",
    dot: "bg-accent",
    description: "GPT-4o analysis woven into every stage of your trade lifecycle.",
    items: [
      "Pre-trade score (1–10) with strengths & issues",
      "Post-trade review with execution + plan adherence scores",
      "Per-session readiness score before market open",
      "Unlimited AI chat assistant for trade debriefs",
      "Confidence rating + market alignment assessment",
    ],
  },
  {
    icon: ShieldAlert,
    label: "Behavioural Science",
    color: "text-amber-400",
    bg: "bg-amber-400/10",
    dot: "bg-amber-400",
    description: "12 pattern detectors that catch what your emotions hide.",
    items: [
      "Revenge trading & overtrading detection",
      "FOMO entries, late entries, early exits",
      "Bad risk-reward & excessive risk flags",
      "Missing SL/TP guard — intercepts before entry",
      "Real-time alerts with severity (INFO → CRITICAL)",
    ],
  },
  {
    icon: LineChart,
    label: "Analytics & Reporting",
    color: "text-emerald-300",
    bg: "bg-emerald-400/10",
    dot: "bg-emerald-400",
    description: "Your full trading history, scored, charted, and audited.",
    items: [
      "Trade journal with collapsible AI analysis per trade",
      "Win rate charts by symbol, session & time-of-day",
      "P&L tracking with R-multiple calculation",
      "Weekly + monthly AI-graded performance reports",
      "Pattern timeline — behavioural trends over time",
    ],
  },
];

const featureCards = [
  {
    icon: Activity,
    title: "Live Trade Monitoring",
    description: "MetaAPI streams your MT4/MT5 positions in real time. Every open, update and close is captured instantly.",
  },
  {
    icon: Target,
    title: "Pre-Trade AI Score",
    description: "Before you commit capital, GPT-4o rates the trade 1–10 across risk, setup quality and market alignment.",
  },
  {
    icon: BookOpen,
    title: "Trade Journal",
    description: "Every trade becomes a journal entry — pre-trade reasoning, post-trade review, behavioural flags and metrics in one card.",
  },
  {
    icon: Clock,
    title: "Duration Tracking",
    description: "Measures exactly how long each trade was open. Spot overholding, premature exits and session drift patterns.",
  },
  {
    icon: AlertTriangle,
    title: "Behavioural Alerts",
    description: "Nudged the moment a pattern fires — revenge trade, overexposure, missing stop-loss. Severity-graded in real time.",
  },
  {
    icon: TrendingUp,
    title: "Pattern Analytics",
    description: "Aggregate view of all 12 behavioural patterns across your history. See which are increasing, decreasing or resolved.",
  },
  {
    icon: FileText,
    title: "Weekly Reports",
    description: "AI-graded weekly summary (A–F) with strengths, weaknesses, pattern recap and one actionable recommendation.",
  },
  {
    icon: CheckSquare,
    title: "Trading Rules Engine",
    description: "Encode your personal risk doctrine — max daily loss, lot size limits, session restrictions. ampere enforces them.",
  },
  {
    icon: MessageSquare,
    title: "AI Chat Assistant",
    description: "Debrief any trade, ask about your week, or stress-test a setup — your AI coach knows your full history.",
  },
  {
    icon: ScanLine,
    title: "Readiness Score",
    description: "A pre-session discipline index built from your last 10 trades and rule compliance rate.",
  },
  {
    icon: Zap,
    title: "Real-Time WebSocket Feed",
    description: "Trades, alerts, P&L and scores stream live to your dashboard the moment they update — zero polling lag.",
  },
  {
    icon: BarChart3,
    title: "Win Rate & R Analytics",
    description: "Symbol-by-symbol and session-by-session breakdown of win rate, average R, expectancy and drawdown contribution.",
  },
];

const featureHighlights = [
  {
    icon: BarChart3,
    title: "Live Alpha Score",
    copy: "Every trade receives a trust score calculated from 42 behavioral and structural signals.",
  },
  {
    icon: Brain,
    title: "Cognition Graph",
    copy: "Surface revenge impulses, FOMO entries, and fatigue loops before they cost capital.",
  },
  {
    icon: Shield,
    title: "Protocol Guardrails",
    copy: "Encode your risk doctrine once, then let ampere.capital intercept violations in real time.",
  },
];

const ritualPillars = [
  { label: "Pre-market ritual", detail: "+12% discipline delta" },
  { label: "Live execution", detail: "sub-second nudges" },
  { label: "Post-trade audit", detail: "context-aware journaling" },
];

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      router.push("/dashboard");
    }
  }, [router]);

  return (
    <div className="relative flex min-h-screen flex-col">

      <header className="sticky top-0 z-30 border-b border-white/5 bg-background/70 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-surface/70">
              <AmpereLogo className="h-7 w-7" />
            </div>
            <div>
              <p className="text-sm font-medium tracking-[0.08em] text-muted">ampere.capital</p>
            </div>
          </div>

          <nav className="hidden items-center gap-6 text-sm text-muted md:flex">
            {navLinks.map((link) => (
              <button
                key={link.href}
                onClick={() => {
                  if (link.href.startsWith("#")) {
                    document.querySelector(link.href)?.scrollIntoView({ behavior: "smooth" });
                  } else {
                    router.push(link.href);
                  }
                }}
                className="transition-colors hover:text-foreground"
              >
                {link.label}
              </button>
            ))}
          </nav>
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
              Launch Terminal
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero / Product */}
        <section className="px-6 py-20" id="product">
          <div className="mx-auto max-w-6xl">
            <div className="relative overflow-hidden rounded-[48px] border border-white/10 bg-surface/70 px-6 py-12 shadow-[0_40px_120px_rgba(0,0,0,0.65)] md:px-10 md:py-14">
              <div className="relative z-10 grid gap-12 lg:grid-cols-[1.15fr_0.85fr]">
                <div className="space-y-10">
              <div className="stat-pill w-fit border-accent/30 bg-accent/10 text-accent">
                <Sparkles className="h-3.5 w-3.5" />
                Now orchestrating $12B in annual order flow
              </div>
              <div className="space-y-6">
                <p className="text-sm uppercase tracking-[0.4em] text-muted">Adaptive Execution Layer</p>
                <h1 className="text-balance text-4xl font-semibold leading-tight text-foreground md:text-6xl">
                  Precision coaching for traders who treat discipline as an edge.
                </h1>
                <p className="text-lg text-muted">
                  ampere.capital captures every impulse, reframes risk in real time, and unlocks the ritual that elite desks run to stay in control. There’s no generic dashboard—only adaptive guidance tuned to your playbook.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button
                  size="lg"
                  className="rounded-full px-8 text-base font-semibold shadow-glow"
                  onClick={() => router.push("/register")}
                >
                  Start Free Trial
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="lg"
                  className="rounded-full border border-white/10 px-8 text-base"
                  onClick={() => router.push("/login")}
                >
                  Enter Console
                </Button>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                {["Rule Check", "State of Mind", "Execution Hygiene"].map((label) => (
                  <div key={label} className="rounded-2xl border border-white/5 bg-white/5 px-4 py-5">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted">{label}</p>
                    <p className="mt-3 text-3xl font-semibold text-glow">97.2%</p>
                    <p className="text-xs text-muted">rolling 30-day discipline score</p>
                  </div>
                ))}
              </div>
                </div>

                <div className="beam-border relative rounded-[32px] border border-white/10 bg-gradient-to-b from-surface to-surface-muted p-6 backdrop-blur-2xl">
                  <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted">
                    <span>Mission Control</span>
                    <span>live feed</span>
                  </div>
                  <div className="mt-6 space-y-4">
                    {ritualPillars.map((pillar) => (
                      <div key={pillar.label} className="rounded-2xl border border-white/5 bg-surface-contrast/40 p-4">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted">{pillar.label}</span>
                          <span className="text-foreground">{pillar.detail}</span>
                        </div>
                        <div className="mt-3 h-1.5 rounded-full bg-surface">
                          <div className="h-full rounded-full bg-accent" style={{ width: "82%" }} />
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-8 rounded-[28px] border border-white/5 bg-black/30 p-6 text-center">
                    <p className="text-sm uppercase tracking-[0.4em] text-muted">Live nudges</p>
                    <p className="mt-4 text-4xl font-semibold text-glow">-43% drawdown volatility</p>
                    <p className="mt-3 text-sm text-muted">after 60 sessions on ampere.capital</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Method */}
        <section id="method" className="border-y border-white/5 bg-surface/60 py-16">
          <div className="mx-auto grid max-w-6xl gap-8 px-6 md:grid-cols-3">
            {featureHighlights.map(({ icon: Icon, title, copy }) => (
              <article key={title} className="card-surface p-6 transition-transform duration-300 hover:-translate-y-1">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/15 text-accent">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-6 text-xl font-semibold">{title}</h3>
                <p className="mt-3 text-sm text-muted">{copy}</p>
              </article>
            ))}
          </div>
        </section>

        {/* Features */}
        <section id="features" className="px-6 py-24">
          <div className="mx-auto max-w-6xl space-y-24">

            {/* Header */}
            <div className="text-center space-y-3">
              <p className="text-xs uppercase tracking-[0.4em] text-muted">Full Platform</p>
              <h2 className="text-4xl font-semibold text-balance">
                Everything you need to trade with discipline.
              </h2>
              <p className="text-muted max-w-xl mx-auto">
                The only platform that combines live broker data, GPT-4o intelligence
                and behavioural science into a single adaptive terminal.
              </p>
            </div>

            {/* Feature spotlight 1 — AI Intelligence */}
            <div className="relative overflow-hidden rounded-[48px] border border-white/10 bg-surface/70 px-6 py-12 shadow-[0_40px_120px_rgba(0,0,0,0.65)] md:px-10 md:py-14">
              <div className="relative z-10 grid gap-12 lg:grid-cols-2 items-center">
                <div className="space-y-8">
                  <div className="stat-pill w-fit border-accent/30 bg-accent/10 text-accent">
                    <Brain className="h-3.5 w-3.5" />
                    GPT-4o Powered
                  </div>
                  <div className="space-y-4">
                    <p className="text-xs uppercase tracking-[0.4em] text-muted">AI Intelligence</p>
                    <h3 className="text-3xl font-semibold text-balance">
                      Analysis at every stage of your trade lifecycle.
                    </h3>
                    <p className="text-muted">
                      Before entry, during execution, and after close — GPT-4o grades your decision-making and surfaces what your instincts miss.
                    </p>
                  </div>
                  <ul className="space-y-3">
                    {featureCategories[0].items.map((item) => (
                      <li key={item} className="flex items-start gap-3 text-sm text-muted">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="beam-border relative rounded-[32px] border border-white/10 bg-gradient-to-b from-surface to-surface-muted p-6 backdrop-blur-2xl">
                  <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted">
                    <span>Pre-Trade Score</span>
                    <span className="text-accent">Live</span>
                  </div>
                  <div className="mt-6 space-y-3">
                    {[
                      { label: "Setup Quality", pct: 88 },
                      { label: "Risk Alignment", pct: 72 },
                      { label: "Market Confluence", pct: 91 },
                      { label: "Plan Adherence", pct: 95 },
                    ].map(({ label, pct }) => (
                      <div key={label} className="rounded-2xl border border-white/5 bg-surface-contrast/40 p-4">
                        <div className="flex items-center justify-between text-sm mb-2">
                          <span className="text-muted">{label}</span>
                          <span className="text-foreground font-medium">{pct}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-surface">
                          <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 rounded-[24px] border border-white/5 bg-black/30 p-5 text-center">
                    <p className="text-xs uppercase tracking-[0.3em] text-muted">Trade Score</p>
                    <p className="mt-2 text-5xl font-semibold text-glow">8.6</p>
                    <p className="mt-1 text-xs text-muted">Strong setup — proceed with defined risk</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Feature spotlight 2 — Behavioural Science (reversed) */}
            <div className="relative overflow-hidden rounded-[48px] border border-white/10 bg-surface/70 px-6 py-12 shadow-[0_40px_120px_rgba(0,0,0,0.65)] md:px-10 md:py-14">
              <div className="relative z-10 grid gap-12 lg:grid-cols-2 items-center">
                <div className="beam-border relative rounded-[32px] border border-white/10 bg-gradient-to-b from-surface to-surface-muted p-6 backdrop-blur-2xl order-last lg:order-first">
                  <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted">
                    <span>Behaviour Monitor</span>
                    <span className="text-amber-400">3 active</span>
                  </div>
                  <div className="mt-6 space-y-3">
                    {[
                      { flag: "Revenge Trading", severity: "CRITICAL", color: "text-red-400", bg: "bg-red-400/10" },
                      { flag: "Missing Stop Loss", severity: "HIGH", color: "text-amber-400", bg: "bg-amber-400/10" },
                      { flag: "Early Exit Pattern", severity: "MEDIUM", color: "text-yellow-400", bg: "bg-yellow-400/10" },
                      { flag: "FOMO Entry", severity: "INFO", color: "text-accent", bg: "bg-accent/10" },
                    ].map(({ flag, severity, color, bg }) => (
                      <div key={flag} className="flex items-center justify-between rounded-2xl border border-white/5 bg-surface-contrast/40 px-4 py-3">
                        <div className="flex items-center gap-3">
                          <AlertTriangle className={`h-4 w-4 ${color}`} />
                          <span className="text-sm text-foreground">{flag}</span>
                        </div>
                        <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${bg} ${color}`}>{severity}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 rounded-[24px] border border-white/5 bg-black/30 p-5 text-center">
                    <p className="text-xs uppercase tracking-[0.3em] text-muted">Patterns intercepted</p>
                    <p className="mt-2 text-4xl font-semibold text-glow">312</p>
                    <p className="mt-1 text-xs text-muted">before capital was committed</p>
                  </div>
                </div>
                <div className="space-y-8">
                  <div className="stat-pill w-fit border-amber-400/30 bg-amber-400/10 text-amber-400">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    12 Live Detectors
                  </div>
                  <div className="space-y-4">
                    <p className="text-xs uppercase tracking-[0.4em] text-muted">Behavioural Science</p>
                    <h3 className="text-3xl font-semibold text-balance">
                      Catch the patterns your emotions work hard to hide.
                    </h3>
                    <p className="text-muted">
                      ampere.capital runs 12 behavioural detectors in real time, intercepting revenge trades, FOMO entries and overexposure before they become losses.
                    </p>
                  </div>
                  <ul className="space-y-3">
                    {featureCategories[1].items.map((item) => (
                      <li key={item} className="flex items-start gap-3 text-sm text-muted">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Feature spotlight 3 — Analytics */}
            <div className="relative overflow-hidden rounded-[48px] border border-white/10 bg-surface/70 px-6 py-12 shadow-[0_40px_120px_rgba(0,0,0,0.65)] md:px-10 md:py-14">
              <div className="relative z-10 grid gap-12 lg:grid-cols-2 items-center">
                <div className="space-y-8">
                  <div className="stat-pill w-fit border-emerald-400/30 bg-emerald-400/10 text-emerald-300">
                    <LineChart className="h-3.5 w-3.5" />
                    Full History
                  </div>
                  <div className="space-y-4">
                    <p className="text-xs uppercase tracking-[0.4em] text-muted">Analytics & Reporting</p>
                    <h3 className="text-3xl font-semibold text-balance">
                      Your full trading history, scored, charted, and audited.
                    </h3>
                    <p className="text-muted">
                      Every trade graded, every week summarised, every pattern tracked over time. Know exactly where your edge degrades and where it compounds.
                    </p>
                  </div>
                  <ul className="space-y-3">
                    {featureCategories[2].items.map((item) => (
                      <li key={item} className="flex items-start gap-3 text-sm text-muted">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="beam-border relative rounded-[32px] border border-white/10 bg-gradient-to-b from-surface to-surface-muted p-6 backdrop-blur-2xl">
                  <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted">
                    <span>Weekly Report</span>
                    <span className="text-emerald-300">Feb 24</span>
                  </div>
                  <div className="mt-6 space-y-3">
                    {[
                      { label: "Win Rate", value: "68%", delta: "+4%" },
                      { label: "Avg R-Multiple", value: "1.8R", delta: "+0.3R" },
                      { label: "Expectancy", value: "$312", delta: "+$48" },
                      { label: "Drawdown", value: "3.2%", delta: "−1.1%" },
                    ].map(({ label, value, delta }) => (
                      <div key={label} className="flex items-center justify-between rounded-2xl border border-white/5 bg-surface-contrast/40 px-4 py-3">
                        <span className="text-sm text-muted">{label}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-foreground">{value}</span>
                          <span className="text-xs text-emerald-400">{delta}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 rounded-[24px] border border-white/5 bg-black/30 p-5 text-center">
                    <p className="text-xs uppercase tracking-[0.3em] text-muted">Weekly Grade</p>
                    <p className="mt-2 text-5xl font-semibold text-glow">A−</p>
                    <p className="mt-1 text-xs text-muted">Discipline consistent — tighten entries on EURUSD</p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </section>

        {/* Security */}
        <section id="security" className="px-6 py-20">
          <div className="mx-auto max-w-6xl rounded-[36px] border border-white/10 bg-gradient-to-br from-surface to-surface-contrast p-10 backdrop-blur-2xl">
            <div className="grid gap-8 lg:grid-cols-2">
              <div className="space-y-4">
                <p className="stat-pill border-white/10 text-xs text-muted">Trust Architecture</p>
                <h2 className="text-3xl font-semibold text-balance">
                  Enterprise-grade controls for single-seat traders.
                </h2>
                <p className="text-muted">
                  SOC2-ready infrastructure, fully encrypted broker connections, and air-gapped AI model training ensure that your edge is never material for anyone else.
                </p>
                <div className="grid gap-3 text-sm text-muted">
                  {["Broker-neutral connectivity", "Audit trails for every nudge", "Role-aware workspace access"].map((item) => (
                    <div key={item} className="flex items-center gap-2 text-foreground">
                      <Signal className="h-4 w-4 text-accent" />
                      {item}
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-[28px] border border-white/10 bg-black/30 p-6">
                <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted">
                  <span>Watchlist</span>
                  <span>Realtime</span>
                </div>
                <div className="mt-6 space-y-4">
                  {[
                    { label: "Latency budget", value: "42 ms", icon: Radar },
                    { label: "Broker uptime", value: "99.98%", icon: Waves },
                    { label: "Anomaly intercepts", value: "+312", icon: Shield },
                  ].map(({ label, value, icon: Icon }) => (
                    <div
                      key={label}
                      className="flex items-center justify-between rounded-2xl border border-white/5 bg-surface-muted/80 px-4 py-4"
                    >
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-muted">{label}</p>
                        <p className="mt-1 text-2xl font-semibold">{value}</p>
                      </div>
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-accent/15 text-accent">
                        <Icon className="h-5 w-5" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="px-6 pb-24 pt-4">
          <div className="mx-auto max-w-5xl rounded-[40px] border border-white/10 bg-accent-soft/20 p-10 text-center backdrop-blur-2xl">
            <p className="text-sm uppercase tracking-[0.4em] text-foreground/70">Investment</p>
            <h2 className="mt-4 text-4xl font-semibold text-balance">
              One losing trade costs more than a year of Tactician.
            </h2>
            <p className="mt-4 text-muted">
              Plans from $29/mo. 14-day free trial on all plans — no credit card required.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-4">
              <Button
                size="lg"
                className="rounded-full px-10 text-base font-semibold shadow-glow"
                onClick={() => router.push("/pricing")}
              >
                See Plans &amp; Pricing
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="lg"
                className="rounded-full border border-white/20 px-10 text-base"
                onClick={() => router.push("/register")}
              >
                Start Free Trial
              </Button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 bg-surface/40 px-6 pt-16 pb-10">
        <div className="mx-auto max-w-6xl">

          {/* Top grid */}
          <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-[2fr_1fr_1fr_1fr]">

            {/* Brand */}
            <div className="space-y-5">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-surface/70">
                  <AmpereLogo className="h-6 w-6" />
                </div>
                <span className="text-sm font-medium tracking-[0.08em] text-muted">ampere.capital</span>
              </div>
              <p className="max-w-xs text-sm text-muted leading-relaxed">
                Precision coaching for traders who treat discipline as an edge. Live broker data, GPT-4o intelligence and behavioural science — unified.
              </p>
              <div className="flex items-center gap-3">
                {[
                  { label: "X / Twitter", href: "https://x.com" },
                  { label: "LinkedIn", href: "https://linkedin.com" },
                  { label: "Discord", href: "https://discord.com" },
                ].map(({ label, href }) => (
                  <a
                    key={label}
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-lg border border-white/8 bg-surface/60 px-3 py-1.5 text-xs text-muted transition-colors hover:border-white/15 hover:text-foreground"
                  >
                    {label}
                  </a>
                ))}
              </div>
            </div>

            {/* Product */}
            <div className="space-y-4">
              <p className="text-xs uppercase tracking-[0.3em] text-muted/60">Product</p>
              <ul className="space-y-3">
                {[
                  { label: "Features", href: "#features" },
                  { label: "Method", href: "#method" },
                  { label: "Security", href: "#security" },
                  { label: "Pricing", href: "/pricing" },
                  { label: "Dashboard", href: "/dashboard" },
                  { label: "Changelog", href: "#" },
                ].map(({ label, href }) => (
                  <li key={label}>
                    <button
                      onClick={() => {
                        if (href.startsWith("#")) {
                          document.querySelector(href)?.scrollIntoView({ behavior: "smooth" });
                        } else {
                          router.push(href);
                        }
                      }}
                      className="text-sm text-muted transition-colors hover:text-foreground"
                    >
                      {label}
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            {/* Company */}
            <div className="space-y-4">
              <p className="text-xs uppercase tracking-[0.3em] text-muted/60">Company</p>
              <ul className="space-y-3">
                {["About", "Blog", "Careers", "Press", "Contact", "Partners"].map((item) => (
                  <li key={item}>
                    <a href="#" className="text-sm text-muted transition-colors hover:text-foreground">{item}</a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Legal */}
            <div className="space-y-4">
              <p className="text-xs uppercase tracking-[0.3em] text-muted/60">Legal</p>
              <ul className="space-y-3">
                {["Privacy Policy", "Terms of Service", "Cookie Policy", "Security", "Data Processing", "Compliance"].map((item) => (
                  <li key={item}>
                    <a href="#" className="text-sm text-muted transition-colors hover:text-foreground">{item}</a>
                  </li>
                ))}
              </ul>
            </div>

          </div>

          {/* Divider */}
          <div className="my-10 border-t border-white/5" />

          {/* Bottom bar */}
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-xs text-muted">
              © {new Date().getFullYear()} ampere.capital. All rights reserved.
            </p>
            <div className="flex items-center gap-6 text-xs text-muted">
              <span className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
                Systems operational
              </span>
              <a href="#" className="transition-colors hover:text-foreground">Privacy</a>
              <a href="#" className="transition-colors hover:text-foreground">Terms</a>
              <a href="#" className="transition-colors hover:text-foreground">Cookies</a>
            </div>
          </div>

        </div>
      </footer>
    </div>
  );
}
