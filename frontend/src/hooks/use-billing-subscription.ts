"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";

export interface BillingSubscription {
  has_subscription: boolean;
  plan: string;
  status: string;
  is_paid?: boolean;
  is_trial?: boolean;
  trial_expired?: boolean;
  current_period_end: string | null;
  stripe_customer_id: string | null;
}

interface UseBillingSubscriptionResult {
  subscription: BillingSubscription | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useBillingSubscription(): UseBillingSubscriptionResult {
  const [subscription, setSubscription] = useState<BillingSubscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSubscription = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await api.get<BillingSubscription>("/billing/subscription");
      setSubscription(data);
    } catch (e: any) {
      setSubscription(null);
      setError(e?.message ?? "Failed to load subscription");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  return {
    subscription,
    isLoading,
    error,
    refetch: fetchSubscription,
  };
}
