"use client";

import { useEffect, useRef } from "react";
import { useAuthStore } from "@/stores/auth-store";

export function useWebSocket() {
  // Disabled for MVP - WebSocket not critical for testing
  // Token persistence now works, so real-time updates can be added later
  return { isConnected: false };
}
