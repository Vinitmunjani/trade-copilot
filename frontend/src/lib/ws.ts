import { WS_URL } from "./constants";
import type { WSEvent } from "@/types";

type EventHandler = (event: WSEvent) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string | null = null;
  private handlers: Set<EventHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private isIntentionallyClosed = false;

  constructor(url: string = WS_URL) {
    this.url = url;
  }

  connect(token: string) {
    // Avoid creating duplicate sockets when already connected with the same token.
    if (
      this.token === token
      && this.ws
      && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.token = token;
    this.isIntentionallyClosed = false;
    this.reconnectAttempts = 0;
    this._connect();
  }

  private _connect() {
    if (!this.token) return;
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const wsUrl = `${this._normalizeUrl(this.url)}?token=${this.token}`;
      const socket = new WebSocket(wsUrl);
      this.ws = socket;

      socket.onopen = () => {
        console.log("[WS] Connected");
        this.reconnectAttempts = 0;
        this._startKeepAlive();
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSEvent;
          this.handlers.forEach((handler) => handler(data));
        } catch (err) {
          console.error("[WS] Failed to parse message:", err);
        }
      };

      socket.onclose = (event) => {
        this._stopKeepAlive();
        if (this.ws === socket) {
          this.ws = null;
        }
        console.log("[WS] Disconnected", event.code, event.reason);
        if (!this.isIntentionallyClosed) {
          this._reconnect();
        }
      };

      socket.onerror = (error) => {
        console.error("[WS] Error:", error);
      };
    } catch (err) {
      console.error("[WS] Connection failed:", err);
      this._reconnect();
    }
  }

  private _reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[WS] Max reconnection attempts reached");
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this._connect();
    }, delay);
  }

  disconnect() {
    this.isIntentionallyClosed = true;
    this._stopKeepAlive();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(handler: EventHandler): () => void {
    this.handlers.add(handler);
    return () => {
      this.handlers.delete(handler);
    };
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private _normalizeUrl(rawUrl: string): string {
    if (typeof window === "undefined") return rawUrl;
    if (window.location.protocol === "https:" && rawUrl.startsWith("ws://")) {
      return `wss://${rawUrl.slice("ws://".length)}`;
    }
    return rawUrl;
  }

  private _startKeepAlive() {
    this._stopKeepAlive();
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send("ping");
      }
    }, 20000);
  }

  private _stopKeepAlive() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}

// Singleton
export const wsClient = new WebSocketClient();
export default wsClient;
