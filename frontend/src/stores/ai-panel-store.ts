import { create } from "zustand";

interface AiPanelState {
  isOpen: boolean;
  tradeId: string | null;
  aiScore: number | null;
  aiAnalysis: Record<string, any> | null;
  aiReview: Record<string, any> | null;
  streamText: string;
  streamStatus: "idle" | "started" | "streaming" | "completed" | "failed";

  open: () => void;
  close: () => void;
  setStreamStarted: (tradeId: string) => void;
  appendStreamChunk: (tradeId: string, chunk: string) => void;
  setStreamCompleted: (tradeId: string, aiReview: Record<string, any> | null) => void;
  setStreamFailed: (tradeId: string) => void;
  setAnalysis: (
    tradeId: string,
    aiScore: number | null,
    aiAnalysis: Record<string, any> | null,
    aiReview: Record<string, any> | null
  ) => void;
}

export const useAiPanelStore = create<AiPanelState>((set) => ({
  isOpen: false,
  tradeId: null,
  aiScore: null,
  aiAnalysis: null,
  aiReview: null,
  streamText: "",
  streamStatus: "idle",

  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),

  setStreamStarted: (tradeId) =>
    set({
      tradeId,
      streamText: "",
      streamStatus: "started",
      aiReview: null,
      isOpen: true,
    }),

  appendStreamChunk: (tradeId, chunk) =>
    set((s) => {
      if (s.tradeId !== tradeId) return s;
      return {
        streamText: `${s.streamText}${chunk}`,
        streamStatus: "streaming",
      };
    }),

  setStreamCompleted: (tradeId, aiReview) =>
    set((s) => {
      if (s.tradeId !== tradeId) return s;
      return {
        aiReview: aiReview ?? s.aiReview,
        streamStatus: "completed",
      };
    }),

  setStreamFailed: (tradeId) =>
    set((s) => {
      if (s.tradeId !== tradeId) return s;
      return {
        streamStatus: "failed",
      };
    }),

  setAnalysis: (tradeId, aiScore, aiAnalysis, aiReview) =>
    set({
      tradeId,
      aiScore,
      aiAnalysis,
      aiReview,
      streamText: aiReview?.summary || "",
      streamStatus: aiReview ? "completed" : "idle",
    }),
}));
