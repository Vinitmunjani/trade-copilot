#!/usr/bin/env python
"""
Real Account Health Check & Validation

This script validates that a real MetaAPI account is properly connected,
streaming data, and the full system is operational.

Usage:
    python validate_real_account.py --email trader@example.com
"""

import asyncio
import httpx
import websockets
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000/api/v1"
DEBUG_URL = "http://localhost:8000/api/v1/dev"
WS_URL = "ws://localhost:8000/api/v1/ws/trades"


class RealAccountValidator:
    """Validate real account integration."""
    
    def __init__(self, email: str, password: str = "password"):
        self.email = email
        self.password = password
        self.token = None
        self.user_id = None
        self.checks_passed = 0
        self.checks_failed = 0
    
    def print_test(self, name: str):
        print(f"\n┌─ {name}")
    
    def pass_check(self, message: str):
        print(f"├─ ✓ {message}")
        self.checks_passed += 1
    
    def fail_check(self, message: str):
        print(f"├─ ✗ {message}")
        self.checks_failed += 1
    
    def info(self, message: str):
        print(f"├─ ℹ {message}")
    
    def end_test(self):
        print(f"└─")
    
    async def check_backend_health(self):
        """Check if backend is running."""
        self.print_test("Backend Health Check")
        
        try:
            resp = httpx.get(f"{BACKEND_URL.replace('/api/v1', '')}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.pass_check("Backend is running")
                self.info(f"Redis: {data.get('redis')}")
                self.info(f"WebSocket Clients: {data.get('websocket_connections')}")
                self.end_test()
                return True
        except Exception as e:
            self.fail_check(f"Backend unreachable: {e}")
            self.end_test()
            return False
    
    async def check_authentication(self):
        """Check user authentication."""
        self.print_test("User Authentication")
        
        try:
            client = httpx.Client(base_url=BACKEND_URL)
            resp = client.post(
                "/auth/login",
                json={"email": self.email, "password": self.password}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.pass_check(f"User authenticated: {self.email}")
                self.info(f"User ID: {self.user_id}")
                self.end_test()
                return True
            else:
                self.fail_check(f"Authentication failed: {resp.status_code}")
                self.end_test()
                return False
        except Exception as e:
            self.fail_check(f"Auth error: {e}")
            self.end_test()
            return False
    
    async def check_account_connection(self):
        """Check if account is connected via MetaAPI."""
        self.print_test("MetaAPI Account Connection")
        
        try:
            client = httpx.Client(
                base_url=BACKEND_URL,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            resp = client.get("/account/status")
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get("connected"):
                    self.pass_check(f"Account connected")
                    self.info(f"Status: {data.get('connection_status')}")
                    self.info(f"Platform: {data.get('platform')}")
                    self.info(f"Login: {data.get('login')}")
                    self.info(f"Server: {data.get('server')}")
                    
                    if data.get("balance"):
                        self.info(f"Balance: ${data.get('balance'):,.2f}")
                    if data.get("equity"):
                        self.info(f"Equity: ${data.get('equity'):,.2f}")
                else:
                    self.fail_check("Account not connected - no MetaAPI connection")
                    self.info("This is OK if MetaAPI token is not configured")
                
                self.end_test()
                return data.get("connected", False)
            else:
                self.fail_check(f"Could not get account status: {resp.status_code}")
                self.end_test()
                return False
        except Exception as e:
            self.fail_check(f"Error: {e}")
            self.end_test()
            return False
    
    async def check_trader_data(self):
        """Check trader data endpoint."""
        self.print_test("Trader Data Retrieval")
        
        try:
            resp = httpx.get(
                f"{DEBUG_URL}/trader-data",
                params={"email": self.email}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                summary = data.get("summary", {})
                
                self.pass_check("Trader data retrieved")
                self.info(f"Accounts: {summary.get('total_accounts')}")
                self.info(f"Connected: {summary.get('connected_accounts')}")
                self.info(f"Open Trades: {summary.get('open_trades_count')}")
                
                trades = data.get("open_trades", [])
                if trades:
                    self.pass_check(f"Found {len(trades)} open trade(s)")
                    for trade in trades[:3]:  # Show first 3
                        self.info(
                            f"  {trade['symbol']} {trade['direction']} "
                            f"@ {trade['entry_price']:.5f} (AI: {trade['ai_score']}/10)"
                        )
                else:
                    self.info("No open trades currently")
                
                self.end_test()
                return True
            else:
                self.fail_check(f"Failed: {resp.status_code}")
                self.end_test()
                return False
        except Exception as e:
            self.fail_check(f"Error: {e}")
            self.end_test()
            return False
    
    async def check_websocket_streaming(self):
        """Check WebSocket streaming capability."""
        self.print_test("WebSocket Streaming Connection")
        
        try:
            url = f"{WS_URL}?token={self.token}"
            
            try:
                async with websockets.connect(url, ping_interval=None) as ws:
                    # Receive CONNECTED event
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    data = json.loads(msg)
                    
                    if data.get("event") == "CONNECTED":
                        self.pass_check("WebSocket connected and authenticated")
                        self.info(f"Message: {data.get('message')}")
                        
                        # Try to receive one more message (with timeout)
                        try:
                            next_msg = await asyncio.wait_for(ws.recv(), timeout=2)
                            event_data = json.loads(next_msg)
                            self.info(f"Live event received: {event_data.get('event')}")
                        except asyncio.TimeoutError:
                            self.info("No live events (normal if no trades happening)")
                        
                        self.end_test()
                        return True
                    else:
                        self.fail_check(f"Unexpected event: {data.get('event')}")
                        self.end_test()
                        return False
            except asyncio.TimeoutError:
                self.fail_check("WebSocket connection timeout")
                self.end_test()
                return False
        except Exception as e:
            self.fail_check(f"Error: {e}")
            self.end_test()
            return False
    
    async def check_heartbeat(self):
        """Check account heartbeat status."""
        self.print_test("Account Heartbeat Monitoring")
        
        try:
            resp = httpx.get(
                f"{DEBUG_URL}/trader-data",
                params={"email": self.email}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                accounts = data.get("meta_accounts", [])
                
                if accounts:
                    for account in accounts:
                        if account.get("connected"):
                            self.pass_check(f"Heartbeat active: {account.get('mt_platform').upper()}")
                            last_hb = account.get("last_heartbeat")
                            self.info(f"Last heartbeat: {last_hb}")
                        else:
                            self.fail_check(f"No heartbeat: {account.get('mt_platform').upper()}")
                else:
                    self.info("No MetaAPI accounts connected")
                
                self.end_test()
                return True
            else:
                self.fail_check(f"Could not verify heartbeat: {resp.status_code}")
                self.end_test()
                return False
        except Exception as e:
            self.fail_check(f"Error: {e}")
            self.end_test()
            return False
    
    async def run_all_checks(self):
        """Run all validation checks."""
        print("\n" + "="*100)
        print("  REAL ACCOUNT VALIDATION CHECK")
        print("="*100)
        print(f"\nValidating account for: {self.email}\n")
        
        # Run checks
        if not await self.check_backend_health():
            print("\n❌ FAILED: Backend is not running!")
            print("   Start backend with: python -m uvicorn app.main:app")
            return False
        
        if not await self.check_authentication():
            print("\n❌ FAILED: Authentication failed!")
            return False
        
        await self.check_account_connection()
        await self.check_trader_data()
        await self.check_websocket_streaming()
        await self.check_heartbeat()
        
        # Summary
        print("\n" + "="*100)
        print("  VALIDATION SUMMARY")
        print("="*100)
        print(f"\n✓ Checks Passed: {self.checks_passed}")
        print(f"✗ Checks Failed: {self.checks_failed}")
        
        if self.checks_failed == 0:
            print("\n🟢 SYSTEM OPERATIONAL - Ready for trading!")
            print("\nNext steps:")
            print("  1. Open trades in your MT5 terminal")
            print("  2. Watch WebSocket for TRADE_OPENED events")
            print("  3. Monitor AI analysis and P&L in real-time")
        else:
            print("\n🟡 Some checks failed - review above for details")
        
        print("\n" + "="*100 + "\n")
        
        return self.checks_failed == 0


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate real account setup")
    parser.add_argument("--email", default="trader@example.com", help="Trader email")
    parser.add_argument("--password", default="password", help="Trader password")
    
    args = parser.parse_args()
    
    validator = RealAccountValidator(args.email, args.password)
    success = await validator.run_all_checks()
    
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
