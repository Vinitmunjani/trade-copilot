"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Activity, ArrowRight, BarChart3, Brain, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      router.push("/dashboard");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Nav */}
      <header className="border-b border-slate-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-emerald-500" />
            <span className="text-xl font-bold text-slate-100">Trade Co-Pilot</span>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" onClick={() => router.push("/login")}>
              Log In
            </Button>
            <Button onClick={() => router.push("/register")}>Get Started</Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm mb-6">
            <Activity className="h-3.5 w-3.5" />
            AI-Powered Trading Assistant
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-slate-100 mb-6 leading-tight">
            Trade Smarter with
            <br />
            <span className="text-emerald-400">AI-Driven Insights</span>
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-8">
            Real-time trade scoring, behavioral pattern detection, and personalized feedback
            to help you become a more disciplined and profitable trader.
          </p>
          <div className="flex items-center justify-center gap-4 mb-16">
            <Button size="lg" onClick={() => router.push("/register")}>
              Start Free Trial
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button variant="outline" size="lg" onClick={() => router.push("/login")}>
              Log In
            </Button>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors">
              <BarChart3 className="h-8 w-8 text-emerald-400 mb-4" />
              <h3 className="text-lg font-semibold text-slate-100 mb-2">Real-Time Scoring</h3>
              <p className="text-sm text-slate-400">
                Every trade scored 1-10 by AI based on setup quality, risk management, and rule adherence.
              </p>
            </div>
            <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors">
              <Brain className="h-8 w-8 text-emerald-400 mb-4" />
              <h3 className="text-lg font-semibold text-slate-100 mb-2">Behavioral Analysis</h3>
              <p className="text-sm text-slate-400">
                Detect revenge trading, FOMO entries, overtrading, and other destructive patterns automatically.
              </p>
            </div>
            <div className="p-6 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors">
              <Shield className="h-8 w-8 text-emerald-400 mb-4" />
              <h3 className="text-lg font-semibold text-slate-100 mb-2">Rule Enforcement</h3>
              <p className="text-sm text-slate-400">
                Define your trading rules and get instant alerts when you're about to break them.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
