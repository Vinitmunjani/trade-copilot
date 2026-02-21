import { create } from "zustand";
import api from "@/lib/api";
import type { User, AuthResponse } from "@/types";

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, confirm_password: string) => Promise<void>;
  logout: () => void;
  loadFromStorage: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: false,
  error: null,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<any>("/auth/login", null, {
        params: { email, password },
      });
      const data = response.data;
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user || { id: data.access_token, email }));
      set({
        user: data.user || { id: data.access_token, email },
        token: data.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err: any) {
      const message = err.response?.data?.detail || "Login failed";
      set({ error: message, isLoading: false });
      throw new Error(message);
    }
  },

  register: async (email: string, password: string, confirm_password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<any>("/auth/register", null, {
        params: { email, password, confirm_password },
      });
      const data = response.data;
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user || { id: data.access_token, email }));
      set({
        user: data.user || { id: data.access_token, email },
        token: data.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err: any) {
      const message = err.response?.data?.detail || "Registration failed";
      set({ error: message, isLoading: false });
      throw new Error(message);
    }
  },

  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
    window.location.href = "/login";
  },

  loadFromStorage: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("token");
    const userStr = localStorage.getItem("user");
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr) as User;
        set({ user, token, isAuthenticated: true });
      } catch {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
      }
    }
  },

  clearError: () => set({ error: null }),
}));
