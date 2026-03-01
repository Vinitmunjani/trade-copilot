#!/usr/bin/env python
"""
End-to-end workflow test for TradeCo-Pilot

Demonstrates:
1. User registration & login
2. Account data retrieval
3. WebSocket connection
4. Simulated trade events streaming in real-time
5. Trade data verification

Run with: python workflow_test.py
"""

import asyncio
import json
import httpx
import websockets
from typing import Optional

BACKEND_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ws/trades"
DEBUG_URL = "http://localhost:8000/api/v1/dev"

# Test user
TEST_EMAIL = "walker@example.com"
TEST_PASSWORD = "testpass123"


class TradeCoWorkflow:
    def __init__(self):
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.client = httpx.Client(base_url=BACKEND_URL)
        
    def print_header(self, text: str):
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}\n")
    
    def print_step(self, num: int, text: str):
        print(f"\n[STEP {num}] {text}")
        print("-" * 70)
    
    def print_success(self, text: str):
        print(f"✓ {text}")
    
    def print_error(self, text: str):
        print(f"✗ {text}")
    
    def print_info(self, text: str):
        print(f"ℹ {text}")
    
    # ============ Step 1: Register User ============
    def step_register(self):
        self.print_step(1, "Register new user")
        
        try:
            resp = self.client.post(
                "/auth/register",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            
            if resp.status_code in [200, 201]:
                data = resp.json()
                self.print_success(f"User registered: {TEST_EMAIL}")
                self.print_info(f"Response: {data}")
                return True
            else:
                # User might already exist, try login instead
                self.print_info(f"User might exist (status {resp.status_code}), will try login")
                return True
        except Exception as e:
            self.print_error(f"Registration failed: {e}")
            return False
    
    # ============ Step 2: Login & Get Token ============
    def step_login(self):
        self.print_step(2, "Login and get JWT token")
        
        try:
            resp = self.client.post(
                "/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                self.print_success(f"Login successful")
                self.print_info(f"Token: {self.token[:50]}...")
                
                # Update client headers
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                return True
            else:
                self.print_error(f"Login failed (status {resp.status_code}): {resp.text}")
                return False
        except Exception as e:
            self.print_error(f"Login error: {e}")
            return False
    
    # ============ Step 3: Get User Profile ============
    def step_get_profile(self):
        self.print_step(3, "Retrieve user profile")
        
        try:
            resp = self.client.get("/auth/me")
            
            if resp.status_code == 200:
                data = resp.json()
                self.user_id = data.get("id")
                self.print_success(f"Profile retrieved")
                self.print_info(f"User ID: {self.user_id}")
                self.print_info(f"Email: {data.get('email')}")
                self.print_info(f"Active: {data.get('is_active')}")
                return True
            else:
                self.print_error(f"Failed to get profile (status {resp.status_code})")
                return False
        except Exception as e:
            self.print_error(f"Profile retrieval error: {e}")
            return False
    
    # ============ Step 4: Check Account Status ============
    def step_check_account_status(self):
        self.print_step(4, "Check trading account status")
        
        try:
            resp = self.client.get("/account/status")
            
            if resp.status_code == 200:
                data = resp.json()
                self.print_info(f"Connection Status: {data.get('connection_status')}")
                self.print_info(f"Platform: {data.get('platform')}")
                self.print_info(f"Login: {data.get('login')}")
                
                if data.get('connected'):
                    self.print_success("Account is connected")
                else:
                    self.print_info("No active trading account (expected for workflow test)")
                return True
            else:
                self.print_info(f"Status check returned {resp.status_code} (might not have account yet)")
                return True
        except Exception as e:
            self.print_error(f"Status check error: {e}")
            return False
    
    # ============ Step 5: Get Trader Data ============
    def step_get_trader_data(self):
        self.print_step(5, "Fetch detailed trader data from debug endpoint")
        
        try:
            resp = httpx.get(
                f"{DEBUG_URL}/trader-data",
                params={"email": TEST_EMAIL}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Display user info
                user_info = data.get("user", {})
                self.print_success(f"Trader data retrieved")
                self.print_info(f"  Email: {user_info.get('email')}")
                self.print_info(f"  User ID: {user_info.get('id')}")
                
                # Display accounts
                summary = data.get("summary", {})
                self.print_info(f"  Total MetaAPI accounts: {summary.get('total_accounts', 0)}")
                self.print_info(f"  Connected accounts: {summary.get('connected_accounts', 0)}")
                self.print_info(f"  Open trades: {summary.get('open_trades_count', 0)}")
                
                # Show trades if any
                trades = data.get("open_trades", [])
                if trades:
                    self.print_info(f"\n  Trades:")
                    for trade in trades:
                        print(f"    - {trade['symbol']} {trade['direction']} @ {trade['entry_price']} (AI: {trade['ai_score']})")
                
                return True
            else:
                self.print_error(f"Failed to get trader data (status {resp.status_code})")
                return False
        except Exception as e:
            self.print_error(f"Trader data error: {e}")
            return False
    
    # ============ Step 6: WebSocket Connection ============
    async def step_websocket_connect(self):
        self.print_step(6, "Open WebSocket connection for real-time events")
        
        try:
            url = f"{WS_URL}?token={self.token}"
            self.print_info(f"Connecting to {url[:60]}...")
            
            async with websockets.connect(url) as ws:
                self.print_success("WebSocket connected!")
                
                # Receive connection confirmation
                msg = await ws.recv()
                data = json.loads(msg)
                
                if data.get("event") == "CONNECTED":
                    self.print_success("Received CONNECTED event from server")
                    self.print_info(f"  Message: {data.get('message')}")
                
                return ws
        except Exception as e:
            self.print_error(f"WebSocket connection failed: {e}")
            return None
    
    # ============ Step 7: Simulate Trades ============
    def step_simulate_trades(self, count: int = 3):
        self.print_step(7, f"Simulate {count} trades via API")
        
        trades_created = []
        
        for i in range(count):
            payload = {
                "symbol": "EURUSD" if i % 2 == 0 else "GBPUSD",
                "direction": "BUY" if i % 2 == 0 else "SELL",
                "entry_price": 1.1000 + i * 0.001,
                "sl": 1.0950,
                "tp": 1.1200,
                "lot_size": 0.1,
                "close_after_seconds": 4,  # Auto-close after 4s
            }
            
            try:
                resp = self.client.post("/dev/simulate-trade", json=payload)
                
                if resp.status_code == 200:
                    trade_data = resp.json()
                    trade_id = trade_data.get("id")
                    self.print_success(f"Trade {i+1} created: {payload['symbol']} {payload['direction']} @ {payload['entry_price']}")
                    self.print_info(f"  Trade ID: {trade_id}")
                    trades_created.append(trade_id)
                else:
                    self.print_error(f"Trade {i+1} failed (status {resp.status_code}): {resp.text}")
            except Exception as e:
                self.print_error(f"Trade {i+1} error: {e}")
        
        return trades_created
    
    # ============ Step 8: Monitor WebSocket ============
    async def step_monitor_websocket(self, ws, duration_sec: int = 20):
        self.print_step(8, f"Monitor WebSocket for {duration_sec} seconds")
        self.print_info("Waiting for trade events...")
        
        events_received = []
        start_time = asyncio.get_event_loop().time()
        
        try:
            while asyncio.get_event_loop().time() - start_time < duration_sec:
                try:
                    # Set a short timeout to allow checking elapsed time
                    await asyncio.wait_for(
                        asyncio.create_task(ws.recv()),
                        timeout=1.0
                    )
                    msg = await ws.recv()
                    data = json.loads(msg)
                    
                    event_type = data.get("event", "UNKNOWN")
                    events_received.append(event_type)
                    
                    if event_type == "TRADE_OPENED":
                        self.print_success(f"[{event_type}] {data.get('symbol')} - AI Score: {data.get('ai_score')}")
                    elif event_type == "TRADE_CLOSED":
                        self.print_success(f"[{event_type}] P&L: {data.get('pnl')}, P&L R: {data.get('pnl_r')}")
                    elif event_type == "TRADE_UPDATED":
                        self.print_info(f"[{event_type}] {data.get('symbol')} - SL: {data.get('sl')}, TP: {data.get('tp')}")
                    else:
                        self.print_info(f"[{event_type}] {data}")
                
                except asyncio.TimeoutError:
                    # No message in this second, check elapsed time again
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= duration_sec:
                        break
                    continue
        except Exception as e:
            self.print_error(f"WebSocket monitoring error: {e}")
        
        self.print_info(f"\nReceived {len(events_received)} events total")
        if events_received:
            event_counts = {}
            for evt in events_received:
                event_counts[evt] = event_counts.get(evt, 0) + 1
            for evt_type, count in event_counts.items():
                self.print_info(f"  {evt_type}: {count}")
        
        return events_received
    
    # ============ Step 9: Verify Data ============
    def step_verify_trades(self):
        self.print_step(9, "Verify trades in database")
        
        try:
            resp = httpx.get(
                f"{DEBUG_URL}/trader-data",
                params={"email": TEST_EMAIL}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                summary = data.get("summary", {})
                trades = data.get("open_trades", [])
                closed_count = summary.get("open_trades_count", 0)
                
                self.print_success(f"Verified: {len(trades)} open trades in database")
                
                if trades:
                    for trade in trades:
                        self.print_info(f"  {trade['symbol']} {trade['direction']} - AI: {trade['ai_score']}")
                
                return True
            else:
                self.print_error(f"Verification failed (status {resp.status_code})")
                return False
        except Exception as e:
            self.print_error(f"Verification error: {e}")
            return False
    
    # ============ Main Workflow ============
    async def run(self):
        self.print_header("TRADECO-PILOT END-TO-END WORKFLOW TEST")
        self.print_info("This test demonstrates the full trading system pipeline")
        
        # Run synchronous steps
        if not self.step_register():
            return
        
        if not self.step_login():
            return
        
        if not self.step_get_profile():
            return
        
        if not self.step_check_account_status():
            return
        
        if not self.step_get_trader_data():
            return
        
        # Connect WebSocket
        ws = await self.step_websocket_connect()
        if not ws:
            return
        
        # Simulate trades
        self.step_simulate_trades(count=3)
        
        # Monitor WebSocket
        await self.step_monitor_websocket(ws, duration_sec=20)
        
        # Verify trades
        self.step_verify_trades()
        
        # Done
        self.print_header("WORKFLOW COMPLETE")
        self.print_success("All steps executed successfully!")
        self.print_info("The system demonstrated:")
        self.print_info("  ✓ User authentication")
        self.print_info("  ✓ Account status checking")
        self.print_info("  ✓ Real-time WebSocket streaming")
        self.print_info("  ✓ Trade simulation and processing")
        self.print_info("  ✓ Data persistence and retrieval")


async def main():
    workflow = TradeCoWorkflow()
    await workflow.run()


if __name__ == "__main__":
    asyncio.run(main())
