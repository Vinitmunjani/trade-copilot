"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Shield, Save, Loader2 } from "lucide-react";
import { useSettingsStore } from "@/stores/settings-store";
import { SESSIONS } from "@/lib/constants";
import type { TradingSession } from "@/types";

export function RulesEditor() {
  const { rules, isSaving, updateRules } = useSettingsStore();
  const [localRules, setLocalRules] = useState(rules);
  
  useEffect(() => {
    setLocalRules(rules);
  }, [rules]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateRules(localRules);
    } catch (error) {
      console.error("Failed to update rules:", error);
    }
  };

  const toggleSession = (session: TradingSession) => {
    setLocalRules((prev) => ({
      ...prev,
      blocked_sessions: prev.blocked_sessions.includes(session)
        ? prev.blocked_sessions.filter((s) => s !== session)
        : [...prev.blocked_sessions, session],
    }));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Shield className="h-4 w-4 text-emerald-400" />
          Trading Rules
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Risk Management */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-200">Risk Management</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="max-risk">Max Risk per Trade (%)</Label>
                <div className="relative">
                  <Input
                    id="max-risk"
                    type="number"
                    min="0.1"
                    max="10"
                    step="0.1"
                    value={localRules.max_risk_percent}
                    onChange={(e) =>
                      setLocalRules((prev) => ({
                        ...prev,
                        max_risk_percent: parseFloat(e.target.value) || 0,
                      }))
                    }
                    className="pr-8"
                  />
                  <span className="absolute right-3 top-2 text-sm text-slate-400">%</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="min-rr">Min Risk:Reward Ratio</Label>
                <Input
                  id="min-rr"
                  type="number"
                  min="1"
                  max="10"
                  step="0.1"
                  value={localRules.min_risk_reward}
                  onChange={(e) =>
                    setLocalRules((prev) => ({
                      ...prev,
                      min_risk_reward: parseFloat(e.target.value) || 0,
                    }))
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="max-trades">Max Trades per Day</Label>
                <Input
                  id="max-trades"
                  type="number"
                  min="1"
                  max="20"
                  value={localRules.max_trades_per_day}
                  onChange={(e) =>
                    setLocalRules((prev) => ({
                      ...prev,
                      max_trades_per_day: parseInt(e.target.value, 10) || 0,
                    }))
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="max-loss">Max Loss per Day (%)</Label>
                <div className="relative">
                  <Input
                    id="max-loss"
                    type="number"
                    min="1"
                    max="20"
                    step="0.5"
                    value={localRules.max_loss_per_day}
                    onChange={(e) =>
                      setLocalRules((prev) => ({
                        ...prev,
                        max_loss_per_day: parseFloat(e.target.value) || 0,
                      }))
                    }
                    className="pr-8"
                  />
                  <span className="absolute right-3 top-2 text-sm text-slate-400">%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Session Restrictions */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-200">Session Restrictions</h3>
            <p className="text-xs text-slate-400">
              Block trading during specific sessions to maintain discipline
            </p>
            
            <div className="space-y-3">
              {SESSIONS.map((session) => (
                <div key={session.value} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 border border-slate-700">
                  <div>
                    <p className="text-sm font-medium text-slate-200">{session.label}</p>
                    <p className="text-xs text-slate-400">{session.hours}</p>
                  </div>
                  <Switch
                    checked={localRules.blocked_sessions.includes(session.value as TradingSession)}
                    onCheckedChange={() => toggleSession(session.value as TradingSession)}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end pt-4">
            <Button type="submit" disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Rules
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
