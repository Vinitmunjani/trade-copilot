/**
 * Imperative toast hook backed by a Zustand store.
 * Usage: const { toast } = useToast();
 *        toast({ title: "Trade opened", description: "EURUSD BUY", variant: "success" });
 */

import { create } from "zustand";

export type ToastVariant = "default" | "success" | "destructive" | "info";

export interface ToastItem {
  id: string;
  title?: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
}

interface ToastStore {
  toasts: ToastItem[];
  addToast: (item: Omit<ToastItem, "id">) => void;
  removeToast: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (item) =>
    set((s) => ({
      toasts: [
        ...s.toasts,
        { ...item, id: Math.random().toString(36).slice(2) },
      ],
    })),
  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export function useToast() {
  const { addToast } = useToastStore();

  const toast = (item: Omit<ToastItem, "id">) => {
    addToast(item);
  };

  return { toast };
}
