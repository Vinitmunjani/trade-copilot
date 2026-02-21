"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/stores/auth-store";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Load persisted auth state from localStorage on mount
    useAuthStore.getState().loadFromStorage();
  }, []);

  return <>{children}</>;
}
