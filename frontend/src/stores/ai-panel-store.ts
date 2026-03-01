import { create } from "zustand";

interface AiPanelState {
  isOpen: boolean;
  tradeId: string | null;
  aiScore: number | null;
  aiAnalysis: Record<string, any> | null;
  aiReview: Record<string, any> | null;

  open: () => void;
  close: () => void;
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

  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),

  setAnalysis: (tradeId, aiScore, aiAnalysis, aiReview) =>
    set({ tradeId, aiScore, aiAnalysis, aiReview }),
}));
