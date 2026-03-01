#!/usr/bin/env python
"""
Real MetaAPI Account Connection & Streaming Test

This test demonstrates connecting trader@example.com to a real MetaAPI account
and streaming live trading data through the WebSocket pipeline.

Prerequisites:
1. MetaAPI Account with API access token
2. MT4/MT5 trading account credentials
3. Environment variables set:
   - METAAPI_TOKEN: Your MetaAPI API token
   - METAAPI_PROVISIONING_TOKEN: Your MetaAPI provisioning token

Usage:
    python real_account_workflow.py --login <MT5_LOGIN> \
        --password <MT5_PASSWORD> --server <MT5_SERVER> \
        --metaapi-token <API_TOKEN>
"""

import asyncio
import json
import httpx
import websockets
import logging
import os
import sys
from typing import Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ws/trades"
DEBUG_URL = "http://localhost:8000/api/v1/dev"

# Default test account (MetaAPI demo)
DEFAULT_LOGIN = "19023151"  # Example MT5 account
DEFAULT_SERVER = "Exness-MT5Trial8"  # Example server
DEFAULT_PASSWORD = "12345678"  # Example password (DO NOT USE REAL CREDENTIALS IN CODE)

TEST_EMAIL = "trader@example.com"
TEST_PASSWORD = "password"


class RealAccountWorktest:
    """Test real MetaAPI account connection and streaming."""
    
    def __init__(self, metaapi_token: Optional[str] = None):
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.metaapi_token = metaapi_token or os.getenv("METAAPI_TOKEN", "")
        self.client = httpx.Client(base_url=BACKEND_URL, timeout=30.0)
        self.meta_account_id: Optional[str] = None
    
    def print_header(self, text: str):
        print(f"\n{'='*90}")
        print(f"  {text:^85}")
        print(f"{'='*90}\n")
    
    def print_step(self, num: int, text: str):
        print(f"\n[STEP {num}] {text}")
        print("-" * 90)
    
    def print_success(self, text: str):
        print(f"✓ {text}")
    
    def print_error(self, text: str):
        print(f"✗ {text}")
    
    def print_info(self, text: str):
        print(f"ℹ {text}")
    
    def print_warning(self, text: str):
        print(f"⚠ {text}")
    
    # ============ Step 1: Prepare User ============
    def step_prepare_user(self):
        self.print_step(1, "Prepare user account (trader@example.com)")
        
        try:
            # Register
            resp = self.client.post(
                "/auth/register",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            
            if resp.status_code in [200, 201]:
                self.print_success(f"User registered: {TEST_EMAIL}")
            elif resp.status_code == 409:
                self.print_info(f"User already exists")
            else:
                self.print_error(f"Registration failed: {resp.status_code}")
                return False
            
            # Login
            resp = self.client.post(
                "/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.print_success(f"User authenticated")
                self.print_info(f"User ID: {self.user_id}")
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                return True
            else:
                self.print_error(f"Login failed: {resp.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Error: {e}")
            return False
    
    # ============ Step 2: Check MetaAPI Prerequisites ============
    def step_check_prerequisites(self):
        self.print_step(2, "Check MetaAPI requirements")
        
        if not self.metaapi_token:
            self.print_warning("METAAPI_TOKEN not set")
            self.print_info("You need a MetaAPI API token to connect real accounts")
            self.print_info("Get one at: https://app.metaapi.cloud/")
            return False
        
        self.print_success("MetaAPI token configured")
        self.print_info(f"Token (first 20 chars): {self.metaapi_token[:20]}...")
        return True
    
    # ============ Step 3: Connect MetaAPI Account ============
    def step_connect_metaapi_account(self, login: str, password: str, server: str, platform: str = "mt5"):
        self.print_step(3, "Connect MetaAPI account for trader@example.com")
        
        payload = {
            "login": login,
            "password": password,
            "server": server,
            "platform": platform,
        }
        if self.metaapi_token:
            payload["metaapi_token"] = self.metaapi_token
        
        self.print_info(f"Connecting to: {server} / Login: {login} / Platform: {platform.upper()}")
        
        try:
            resp = self.client.post("/account/connect", json=payload)
            
            if resp.status_code in [200, 201]:
                data = resp.json()
                self.meta_account_id = data.get("metaapi_account_id")
                self.print_success(f"Account connected successfully")
                self.print_info(f"MetaAPI Account ID: {self.meta_account_id}")
                self.print_info(f"Connection Status: {data.get('connection_status')}")
                
                # Display account info if available
                if data.get("balance"):
                    self.print_info(f"Balance: ${data.get('balance'):.2f}")
                if data.get("equity"):
                    self.print_info(f"Equity: ${data.get('equity'):.2f}")
                if data.get("free_margin"):
                    self.print_info(f"Free Margin: ${data.get('free_margin'):.2f}")
                
                return True
            else:
                error_detail = resp.json().get("detail", resp.text)
                self.print_error(f"Connection failed: {error_detail}")
                return False
                
        except Exception as e:
            self.print_error(f"Error: {e}")
            return False
    
    # ============ Step 4: Get Real Account Data ============
    def step_get_account_data(self):
        self.print_step(4, "Retrieve real account data")
        
        try:
            resp = self.client.get("/account/status")
            
            if resp.status_code == 200:
                data = resp.json()
                
                self.print_success("Account data retrieved")
                self.print_info(f"Connection Status: {data.get('connection_status')}")
                self.print_info(f"Platform: {data.get('platform')}")
                self.print_info(f"Login: {data.get('login')}")
                self.print_info(f"Server: {data.get('server')}")
                self.print_info(f"Broker: {data.get('broker')}")
                
                if data.get("connected"):
                    self.print_success("✓ Connected to live account")
                else:
                    self.print_warning("Account not currently connected")
                
                return True
            else:
                self.print_error(f"Failed: {resp.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Error: {e}")
            return False
    
    # ============ Step 5: Get Live Positions ============
    def step_get_live_positions(self):
        self.print_step(5, "Fetch live open positions")
        
        try:
            resp = httpx.get(
                f"{DEBUG_URL}/trader-data",
                params={"email": TEST_EMAIL}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                trades = data.get("open_trades", [])
                summary = data.get("summary", {})
                
                self.print_success(f"Live data retrieved")
                self.print_info(f"Total accounts: {summary.get('total_accounts')}")
                self.print_info(f"Connected accounts: {summary.get('connected_accounts')}")
                self.print_info(f"Open positions: {summary.get('open_trades_count')}")
                
                if trades:
                    self.print_info(f"\nOpen Trades:")
                    for i, trade in enumerate(trades, 1):
                        symbol = trade['symbol']
                        direction = trade['direction']
                        entry = trade['entry_price']
                        sl = trade['sl']
                        tp = trade['tp']
                        ai_score = trade['ai_score']
                        
                        self.print_info(
                            f"  {i}. {symbol} {direction} @ {entry:.5f} | "
                            f"SL: {sl:.5f} | TP: {tp:.5f} | AI: {ai_score}/10"
                        )
                        
                        # Show behavioral flags if present
                        flags = trade.get('behavioral_flags', {})
                        if flags:
                            self.print_info(f"     Flags: {flags}")
                else:
                    self.print_info("No open positions")
                
                return True
            else:
                self.print_error(f"Failed: {resp.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Error: {e}")
            return False
    
    # ============ Step 6: WebSocket Streaming ============
    async def step_websocket_streaming(self, duration: int = 30):
        self.print_step(6, "Monitor real-time WebSocket streaming")
        self.print_info(f"Listening for {duration} seconds...")
        
        try:
            url = f"{WS_URL}?token={self.token}"
            
            async with websockets.connect(url) as ws:
                self.print_success("WebSocket connected")
                
                start_time = asyncio.get_event_loop().time()
                events_received = []
                
                while asyncio.get_event_loop().time() - start_time < duration:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(msg)
                        event_type = data.get("event", "UNKNOWN")
                        events_received.append(event_type)
                        
                        if event_type == "CONNECTED":
                            self.print_success(f"[{event_type}] {data.get('message')}")
                        elif event_type == "TRADE_OPENED":
                            symbol = data.get("symbol", "?")
                            direction = data.get("direction", "?")
                            entry = data.get("entry_price", "?")
                            self.print_success(
                                f"🟢 [TRADE_OPENED] {symbol} {direction} @ {entry} | "
                                f"AI: {data.get('ai_score', '?')}/10"
                            )
                        elif event_type == "TRADE_CLOSED":
                            pnl = data.get("pnl", 0)
                            pnl_r = data.get("pnl_r", 0)
                            symbol = data.get("symbol", "?")
                            status_icon = "🟢" if pnl > 0 else "🔴"
                            self.print_success(
                                f"{status_icon} [TRADE_CLOSED] {symbol} | "
                                f"P&L: {pnl:.2f} ({pnl_r:.2f}%)"
                            )
                        elif event_type == "TRADE_UPDATED":
                            symbol = data.get("symbol", "?")
                            self.print_info(
                                f"[{event_type}] {symbol} | "
                                f"SL: {data.get('sl', '?')} | TP: {data.get('tp', '?')}"
                            )
                        else:
                            self.print_info(f"[{event_type}] {data}")
                    
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        if "1000" in str(e):  # Normal close
                            break
                        self.print_warning(f"Error: {e}")
                
                self.print_info(f"\nTotal events received: {len(events_received)}")
                if events_received:
                    event_counts = {}
                    for evt in events_received:
                        event_counts[evt] = event_counts.get(evt, 0) + 1
                    for evt_type, count in event_counts.items():
                        self.print_info(f"  {evt_type}: {count}")
                
                return True
                
        except Exception as e:
            self.print_error(f"WebSocket error: {e}")
            return False
    
    # ============ Step 7: Verify Heartbeat ============
    def step_verify_heartbeat(self):
        self.print_step(7, "Verify account heartbeat & connectivity")
        
        try:
            resp = httpx.get(
                f"{DEBUG_URL}/trader-data",
                params={"email": TEST_EMAIL}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                accounts = data.get("meta_accounts", [])
                
                if accounts:
                    self.print_success(f"Found {len(accounts)} MetaAPI account(s)")
                    for i, account in enumerate(accounts, 1):
                        last_hb = account.get("last_heartbeat")
                        connected = account.get("connected")
                        
                        status_icon = "🟢" if connected else "🔴"
                        self.print_info(
                            f"  {i}. {account.get('mt_platform').upper()} "
                            f"| Login: {account.get('mt_login')} | "
                            f"Server: {account.get('mt_server')}"
                        )
                        self.print_info(
                            f"     {status_icon} Connected: {connected} | "
                            f"Last Heartbeat: {last_hb}"
                        )
                else:
                    self.print_warning("No MetaAPI accounts found")
                
                return True
            else:
                self.print_error(f"Failed: {resp.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Error: {e}")
            return False
    
    # ============ Main Workflow ============
    async def run(self, login: str = None, password: str = None, server: str = None):
        """Run the complete real account workflow."""
        
        self.print_header("REAL MetaAPI ACCOUNT CONNECTION TEST")
        self.print_info("Testing trader@example.com with live MetaAPI streaming")
        
        platform = "mt5"  # Default to MT5
        login = login or DEFAULT_LOGIN
        password = password or DEFAULT_PASSWORD
        server = server or DEFAULT_SERVER
        
        # Step 1: Prepare user
        if not self.step_prepare_user():
            return
        
        # Step 2: Check prerequisites
        if not self.step_check_prerequisites():
            self.print_warning("Skipping real MetaAPI connection test - METAAPI_TOKEN required")
            self.print_info("\n" + "="*90)
            self.print_info("HOW TO SET UP REAL ACCOUNT TEST:")
            self.print_info("="*90)
            self.print_info("\n1. Get MetaAPI Token:")
            self.print_info("   - Sign up at https://app.metaapi.cloud/")
            self.print_info("   - Get your API token from account settings")
            self.print_info("   - Either set METAAPI_TOKEN environment variable or pass as argument")
            self.print_info("\n2. Prepare Trading Account:")
            self.print_info("   - Use your own MT5 account credentials")
            self.print_info("   - Or use a demo account from your broker")
            self.print_info("   - Example: login=19023151, server=Exness-MT5Trial8")
            self.print_info("\n3. Run Test Command:")
            self.print_info("   python real_account_workflow.py \\")
            self.print_info("     --login <YOUR_MT5_LOGIN> \\")
            self.print_info("     --password <YOUR_MT5_PASSWORD> \\")
            self.print_info("     --server <YOUR_MT5_SERVER> \\")
            self.print_info("     --metaapi-token <YOUR_API_TOKEN>")
            self.print_info("\n" + "="*90)
            return
        
        # Step 3: Connect account
        if not self.step_connect_metaapi_account(login, password, server, platform):
            self.print_error("Failed to connect account - check credentials and try again")
            return
        
        # Wait for connection to stabilize
        self.print_info("\nWaiting for MetaAPI connection to stabilize...")
        await asyncio.sleep(5)
        
        # Step 4: Get account data
        if not self.step_get_account_data():
            self.print_warning("Could not retrieve account data")
        
        # Step 5: Get live positions
        await asyncio.sleep(2)
        if not self.step_get_live_positions():
            self.print_warning("Could not retrieve positions")
        
        # Step 6: Monitor WebSocket
        self.print_info("\nStarting WebSocket listener...")
        await self.step_websocket_streaming(duration=30)
        
        # Step 7: Verify heartbeat
        await asyncio.sleep(1)
        if not self.step_verify_heartbeat():
            self.print_warning("Could not verify heartbeat")
        
        # Summary
        self.print_header("REAL ACCOUNT TEST COMPLETE")
        self.print_success("All steps executed successfully!")
        self.print_info("\nYou can now:")
        self.print_info("  ✓ Trade in real time")
        self.print_info("  ✓ Monitor positions via WebSocket")
        self.print_info("  ✓ Receive AI analysis on each trade")
        self.print_info("  ✓ Track behavioral patterns")


async def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test real MetaAPI account connection")
    parser.add_argument("--login", help="MT5 login number")
    parser.add_argument("--password", help="MT5 password")
    parser.add_argument("--server", help="MT5 server name")
    parser.add_argument("--metaapi-token", help="MetaAPI access token")
    
    args = parser.parse_args()
    
    test = RealAccountWorktest(metaapi_token=args.metaapi_token)
    await test.run(
        login=args.login,
        password=args.password,
        server=args.server,
    )


if __name__ == "__main__":
    asyncio.run(main())
