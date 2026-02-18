"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { TradeDetail } from "@/components/trades/trade-detail";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { ArrowLeft } from "lucide-react";
import { useTradeDetail } from "@/hooks/use-trades";

export default function TradeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { trade, isLoading } = useTradeDetail(params.id as string);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!trade) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="text-center py-12">
          <p className="text-slate-400">Trade not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={() => router.back()}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Trades
      </Button>
      <TradeDetail trade={trade} />
    </div>
  );
}
