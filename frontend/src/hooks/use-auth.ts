"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export function useAuth(requireAuth = true) {
  const router = useRouter();
  const { user, token, isAuthenticated, loadFromStorage } = useAuthStore();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  useEffect(() => {
    if (requireAuth && !isAuthenticated && typeof window !== "undefined") {
      const storedToken = localStorage.getItem("token");
      if (!storedToken) {
        router.push("/login");
      }
    }
  }, [isAuthenticated, requireAuth, router]);

  return { user, token, isAuthenticated };
}
