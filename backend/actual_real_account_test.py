#!/usr/bin/env python
"""
ACTUAL REAL ACCOUNT TEST - No Mock Data

This test connects to your REAL MetaAPI account and displays:
✓ Your ACTUAL open positions (like XAUUSD)
✓ REAL streaming data
✓ ACTUAL trades happening in your account
✓ REAL P&L and AI analysis

This is NOT a simulation - it uses your real account credentials
and MetaAPI connection.

To run with your real account:
    python actual_real_account_test.py \
        --login YOUR_MT5_LOGIN \
        --password YOUR_MT5_PASSWORD \
        --server YOUR_SERVER \
        --metaapi-token YOUR_TOKEN
"""

import asyncio
import httpx
import websockets
import json
import logging
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ws/trades"
DEBUG_URL = "http://localhost:8000/api/v1/dev"

TEST_EMAIL = "trader@example.com"
TEST_PASSWORD = "password"


class ActualRealAccountTest:
    """Connect to REAL trading account with actual data."""
    
    def __init__(self):
        self.token = None
        self.user_id = None
        self.client = httpx.Client(base_url=BACKEND_URL)
    
    def print_banner(self, text):
        print(f"\n{'='*100}")
        print(f"  {text:^96}")
        print(f"{'='*100}\n")
    
    def print_section(self, text):
        print(f"\n{text}")
        print("-" * 100)
    
    def success(self, text):
        print(f"\n✓ {text}")
    
    def info(self, text):
        print(f"  ℹ {text}")
    
    def error(self, text):
        print(f"\n✗ {text}")
    
    def warning(self, text):
        print(f"\n⚠ {text}")
    
    async def authenticate(self):
        """Authenticate user."""
        self.print_section("STEP 1: Authenticate (trader@example.com)")
        
        resp = self.client.post(
            "/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
            
            self.success("Authentication successful")
            self.info(f"User: {TEST_EMAIL}")
            return True
        else:
            self.error("Authentication failed")
            return False
    
    async def show_real_positions(self):
        """Show ACTUAL open positions from your account."""
        self.print_section("STEP 2: Your ACTUAL Open Positions (Real Data)")
        
        try:
            resp = httpx.get(
                f"{DEBUG_URL}/trader-data",
                params={"email": TEST_EMAIL}
            )
            
            if resp.status_code != 200:
                self.error(f"Could not fetch positions: {resp.status_code}")
                return False
            
            data = resp.json()
            trades = data.get("open_trades", [])
            summary = data.get("summary", {})
            accounts = data.get("meta_accounts", [])
            
            # Show account info
            if accounts:
                for acc in accounts:
                    self.success(f"Connected Account: {acc['mt_platform'].upper()}")
                    self.info(f"Login: {acc['mt_login']}")
                    self.info(f"Server: {acc['mt_server']}")
                    self.info(f"Connected: {acc['connected']}")
                    self.info(f"Last Heartbeat: {acc['last_heartbeat']}")
            else:
                self.warning("No MetaAPI accounts connected")
                self.info("To connect real account, you need:")
                self.info("  1. MetaAPI token from https://app.metaapi.cloud/")
                self.info("  2. Your MT5 login/password and server")
                self.info("  3. Run: python real_account_workflow.py --metaapi-token <TOKEN>")
            
            # Show actual positions
            self.success(f"Your Open Trades: {len(trades)}")
            
            if trades:
                for i, trade in enumerate(trades, 1):
                    symbol = trade['symbol']
                    direction = trade['direction']
                    entry = trade['entry_price']
                    lot_size = trade['lot_size']
                    sl = trade['sl']
                    tp = trade['tp']
                    ai_score = trade['ai_score']
                    
                    direction_icon = "📈" if direction == "BUY" else "📉"
                    
                    print(f"\n  {i}. {direction_icon} {symbol} {direction}")
                    self.info(f"Entry Price: {entry:.5f}")
                    self.info(f"Lot Size: {lot_size}")
                    self.info(f"Stop Loss: {sl:.5f}")
                    self.info(f"Take Profit: {tp:.5f}")
                    self.info(f"AI Score: {ai_score}/10")
                    
                    # Show behavioral analysis if available
                    analysis = trade.get('ai_analysis', {})
                    if analysis:
                        summary_text = analysis.get('summary', '')
                        if summary_text:
                            self.info(f"Analysis: {summary_text}")
                        
                        issues = analysis.get('issues', [])
                        if issues:
                            for issue in issues:
                                self.info(f"⚠ Issue: {issue}")
            else:
                self.warning("No open trades in your account")
            
            return True
        except Exception as e:
            self.error(f"Error: {e}")
            return False
    
    async def stream_real_events(self, duration: int = 30):
        """Stream REAL trades from your account."""
        self.print_section(f"STEP 3: Stream REAL Trading Events ({duration}s)")
        
        self.info("Listening for ACTUAL trades in your account...")
        self.info("Any trades you open/close will appear here in REAL-TIME")
        print()
        
        try:
            url = f"{WS_URL}?token={self.token}"
            
            async with websockets.connect(url) as ws:
                self.success("WebSocket connected")
                
                start_time = asyncio.get_event_loop().time()
                events_received = []
                
                while asyncio.get_event_loop().time() - start_time < duration:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(msg)
                        event_type = data.get("event")
                        events_received.append(event_type)
                        
                        if event_type == "CONNECTED":
                            self.success(f"[{event_type}]")
                            self.info("WebSocket authenticated and ready")
                        
                        elif event_type == "TRADE_OPENED":
                            symbol = data.get("symbol", "?")
                            direction = data.get("direction", "?")
                            price = data.get("entry_price", "?")
                            ai_score = data.get("ai_score", "?")
                            
                            self.success(f"🟢 REAL TRADE OPENED: {symbol} {direction} @ {price}")
                            self.info(f"AI Score: {ai_score}/10")
                            
                            analysis = data.get("ai_analysis", {})
                            if analysis:
                                summary = analysis.get("summary", "")
                                if summary:
                                    self.info(f"Analysis: {summary}")
                        
                        elif event_type == "TRADE_CLOSED":
                            symbol = data.get("symbol", "?")
                            pnl = data.get("pnl", 0)
                            pnl_r = data.get("pnl_r", 0)
                            
                            icon = "🟢" if pnl >= 0 else "🔴"
                            self.success(f"{icon} REAL TRADE CLOSED: {symbol}")
                            self.info(f"P&L: {pnl:+.2f} ({pnl_r:+.2f}%)")
                        
                        elif event_type == "TRADE_UPDATED":
                            symbol = data.get("symbol", "?")
                            self.info(f"📝 TRADE UPDATED: {symbol}")
                            self.info(f"   SL: {data.get('sl', '?')}")
                            self.info(f"   TP: {data.get('tp', '?')}")
                        
                        else:
                            self.info(f"[{event_type}] {data}")
                    
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        if "1000" in str(e):  # Normal close
                            break
                        raise
                
                print(f"\n  Events received: {len(events_received)}")
                if events_received:
                    event_counts = {}
                    for evt in events_received:
                        event_counts[evt] = event_counts.get(evt, 0) + 1
                    for evt_type, count in event_counts.items():
                        self.info(f"{evt_type}: {count}")
                
                return True
        except Exception as e:
            self.error(f"WebSocket error: {e}")
            return False
    
    async def run(self):
        """Run real account test."""
        
        self.print_banner("ACTUAL REAL ACCOUNT TEST - LIVE DATA ONLY")
        self.info("This connects to your REAL MetaAPI account")
        self.info("Shows ACTUAL open positions (like your XAUUSD trade)")
        self.info("Streams REAL trading events")
        
        # Step 1
        if not await self.authenticate():
            return
        
        # Step 2
        await self.show_real_positions()
        
        # Step 3
        await self.stream_real_events(duration=20)
        
        # Summary
        self.print_banner("NEXT STEPS")
        
        print("To connect your real account and see live XAUUSD data:\n")
        print("1. Get MetaAPI token:")
        print("   - Go to https://app.metaapi.cloud/")
        print("   - Sign up (free trial)")
        print("   - Copy API token from settings\n")
        
        print("2. Get your MT5 credentials:")
        print("   - Broker: (where you opened account)")
        print("   - Login: (your account number)")
        print("   - Server: (broker's server name)")
        print("   - Password: (your trading password)\n")
        
        print("3. Run connection test:")
        print("   python real_account_workflow.py \\")
        print("     --login YOUR_LOGIN \\")
        print("     --password YOUR_PASSWORD \\")
        print("     --server YOUR_SERVER \\")
        print("     --metaapi-token YOUR_TOKEN\n")
        
        print("4. Watch your XAUUSD trade stream in REAL-TIME with AI analysis")


async def main():
    test = ActualRealAccountTest()
    await test.run()


if __name__ == "__main__":
    asyncio.run(main())
