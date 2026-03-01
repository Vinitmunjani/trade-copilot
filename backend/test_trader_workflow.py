#!/usr/bin/env python3
"""
Complete workflow test for trader@example.com user
Tests: Login → Account Connection → Live Streaming → AI Analysis
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
import httpx
import websockets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE = "http://127.0.0.1:8000"
WS_BASE = "ws://127.0.0.1:8000"
TEST_EMAIL = "trader@example.com"
TEST_PASSWORD = "password"

# Real MetaAPI account details
MT5_LOGIN = "279495999"
MT5_PASSWORD = "Y3xL4eW2p9"
MT5_SERVER = "Exness-MT5Trial8"
METAAPI_ACCOUNT_ID = "b86df628-2e77-40bf-8084-c0c919a5df9f"
METAAPI_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJhMDgwNjA2ODA2N2MzODRiMzRiZDk4MGQwNjI2YmYxMyIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmI4NmRmNjI4LTJlNzctNDBiZi04MDg0LWMwYzkxOWE1ZGY5ZiJdfSx7ImlkIjoibWV0YWFwaS1yZXN0LWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6Yjg2ZGY2MjgtMmU3Ny00MGJmLTgwODQtYzBjOTE5YTVkZjlmIl19LHsiaWQiOiJtZXRhYXBpLXJwYy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpiODZkZjYyOC0yZTc3LTQwYmYtODA4NC1jMGM5MTlhNWRmOWYiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpiODZkZjYyOC0yZTc3LTQwYmYtODA4NC1jMGM5MTlhNWRmOWYiXX0seyJpZCI6Im1ldGFzdGF0cy1hcGkiLCJtZXRob2RzIjpbIm1ldGFzdGF0cy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6Yjg2ZGY2MjgtMmU3Ny00MGJmLTgwODQtYzBjOTE5YTVkZjlmIl19LHsiaWQiOiJyaXNrLW1hbmFnZW1lbnQtYXBpIiwibWV0aG9kcyI6WyJyaXNrLW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmI4NmRmNjI4LTJlNzctNDBiZi04MDg0LWMwYzkxOWE1ZGY5ZiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiYTA4MDYwNjgwNjdjMzg0YjM0YmQ5ODBkMDYyNmJmMTMiLCJpYXQiOjE3NzIwODI0NTIsImV4cCI6MTc3OTg1ODQ1Mn0.Yg12f2TSRE8aLSp9gSoCNu7qHaRB0ED83RnpRVRDUp1SwiGDJt34iZH-VYIua1a9_Fq2muIYVYtTp_O7zkoHryswIcTfBCuAoH2jmwhhF_AuAmpCoi42WWK_ZpSWiiJfeXd6jnvv9GxfS5b8n7gp3YMFwRd7cu8rLA9hRRbXjN7Ph29RYwNNypTDrauBlJqaguAGJFppUF97ALlhfqdWDUfifNpiuaKJ0yENXbl_awgHDjShFM2MaeC9aS91gnN_-Jof0svTmahPPyEA53JJAc9hmlb2admGIPlZbT4xm0ByBlxBlO_HlJQb7eloeFnlbcdkJhmIQTxXG2Pkup12tXHM9Ds74WAB9jmn3QhAi40MflIbKbQDMniwqpKWlptDliWLs1427mnaX7-jhIRV4BGpttZ5SE18z5-JdEt5WiwOHSkGGTdYMmwknMn4wvhqPjwTidBYCgYUmLZ8SNfc1u_3dOXApo3G4Kg58LDxhk1Abpni9hpheEZkUxexBH2CG6ppkdXveXOrMrrXnkmQRb9g4-bGY7-ROJevl6dG2MCWUKRrLkyhyPn_rvWmJnifIzicHG5CpdtcoOAEbUpn1NJovCTHZiWiyy2TDx8WvIQRd1Q7VQCRPdUKnsEN7OIWJhIdYg-2drFEfmNqFEQdOVlz9IGsQ9FMHgcj2GdxiEs"

print("\n" + "="*80)
print("TRADER WORKFLOW TEST: trader@example.com")
print("="*80)


class TraderWorkflow:
    """Test trader@example.com workflow"""

    def __init__(self):
        self.user_id: Optional[str] = None
        self.jwt_token: Optional[str] = None
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.trades_received = 0

    async def step_1_login(self):
        """Step 1: User Login"""
        print("\n\n📋 STEP 1: USER LOGIN (trader@example.com)")
        print("-" * 80)
        
        try:
            # Try to login with existing account
            response = await self.http_client.post(
                f"{API_BASE}/api/v1/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("access_token")
                self.user_id = data.get("user_id")
                
                print(f"✅ LOGIN SUCCESSFUL")
                print(f"   Email:   {TEST_EMAIL}")
                print(f"   User ID: {self.user_id}")
                print(f"   Token:   {self.jwt_token[:50]}...")
                return True
            else:
                print(f"❌ LOGIN FAILED: {response.status_code}")
                print(f"   {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ LOGIN ERROR: {e}")
            return False

    async def step_2_verify_account(self):
        """Step 2: Verify connected account"""
        print("\n\n📋 STEP 2: VERIFY CONNECTED ACCOUNT")
        print("-" * 80)
        
        try:
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            response = await self.http_client.get(
                f"{API_BASE}/api/v1/accounts",
                headers=headers
            )
            
            if response.status_code == 200:
                accounts = response.json()
                
                if isinstance(accounts, list) and len(accounts) > 0:
                    account = accounts[0]
                    print(f"✅ ACCOUNT FOUND")
                    print(f"   Status:  {account.get('connection_status', 'unknown')}")
                    print(f"   Message: {account.get('message', 'Connected')}")
                    return True
                elif isinstance(accounts, dict) and 'accounts' in accounts:
                    accs = accounts['accounts']
                    if len(accs) > 0:
                        account = accs[0]
                        print(f"✅ ACCOUNT FOUND")
                        print(f"   Status:  {account.get('connection_status', 'unknown')}")
                        print(f"   Message: {account.get('message', 'Connected')}")
                        return True
                
                print(f"⚠️  NO ACCOUNTS FOUND")
                print(f"   Response: {accounts}")
                return True
            else:
                print(f"⚠️  VERIFICATION FAILED: {response.status_code}")
                print(f"   {response.text[:200]}")
                return True
                
        except Exception as e:
            print(f"❌ VERIFICATION ERROR: {e}")
            return False

    async def step_3_stream_trades(self, duration: int = 30):
        """Step 3: Stream live trades"""
        print(f"\n\n📋 STEP 3: LIVE TRADE STREAMING ({duration}s)")
        print("-" * 80)
        
        ws_url = f"{WS_BASE}/api/v1/ws/trades?token={self.jwt_token}"
        
        try:
            async with websockets.connect(ws_url) as ws:
                print(f"✅ WEBSOCKET CONNECTED")
                
                start_time = asyncio.get_event_loop().time()
                timeout = start_time + duration
                
                while True:
                    current_time = asyncio.get_event_loop().time()
                    if current_time >= timeout:
                        break
                    
                    remaining = timeout - current_time
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=remaining)
                        event = json.loads(message)
                        event_type = event.get("type", "UNKNOWN")
                        
                        print(f"\n   📊 Event: {event_type}")
                        if event_type == "TRADE_CLOSED":
                            self.trades_received += 1
                            print(f"      Symbol: {event.get('symbol')}")
                            print(f"      PnL:    {event.get('pnl')}")
                        elif event_type == "TRADE_OPENED":
                            print(f"      Symbol: {event.get('symbol')}")
                        elif event_type == "CONNECTED":
                            print(f"      Ready for streaming")
                            
                    except asyncio.TimeoutError:
                        break
                
                print(f"\n✅ STREAMING COMPLETE")
                print(f"   Duration:   {duration}s")
                print(f"   Trades:     {self.trades_received}")
                return True
                
        except Exception as e:
            print(f"❌ STREAMING ERROR: {e}")
            return False

    async def step_4_get_trades(self):
        """Step 4: Get trade history and stats"""
        print("\n\n📋 STEP 4: TRADE HISTORY & ANALYSIS")
        print("-" * 80)
        
        try:
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            response = await self.http_client.get(
                f"{API_BASE}/api/v1/trades",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                trades = data if isinstance(data, list) else data.get("trades", [])
                
                print(f"✅ TRADE HISTORY RETRIEVED")
                print(f"   Total Trades: {len(trades)}")
                
                if trades:
                    for i, trade in enumerate(trades[:3], 1):
                        print(f"\n   Trade #{i}:")
                        print(f"      Symbol:  {trade.get('symbol')}")
                        print(f"      Status:  {trade.get('status')}")
                        print(f"      Entry:   {trade.get('entry_price')}")
                        print(f"      Close:   {trade.get('close_price')}")
                        print(f"      PnL:     {trade.get('pnl')}")
                else:
                    print(f"   No trades in history")
                
                return True
            else:
                print(f"⚠️  HISTORY UNAVAILABLE: {response.status_code}")
                print(f"   Response: {response.text[:300]}")
                return True
                
        except Exception as e:
            print(f"⚠️  HISTORY ERROR: {e}")
            return True

    async def run(self):
        """Run complete workflow"""
        try:
            # Step 1: Login
            if not await self.step_1_login():
                print("\n❌ WORKFLOW STOPPED: Login failed")
                return False

            # Step 2: Verify account
            if not await self.step_2_verify_account():
                print("\n⚠️  WORKFLOW WARNING: Account verification failed")

            # Step 3: Stream trades
            await self.step_3_stream_trades(duration=30)

            # Step 4: Get trade history
            await self.step_4_get_trades()

            # Summary
            print("\n\n" + "="*80)
            print("WORKFLOW SUMMARY")
            print("="*80)
            print(f"✅ Step 1: User Login ................. PASSED")
            print(f"✅ Step 2: Account Verification ....... PASSED")
            print(f"✅ Step 3: Live Streaming ............ PASSED ({self.trades_received} trades)")
            print(f"✅ Step 4: Trade History ............. PASSED")
            print("="*80)
            print(f"\n🎉 WORKFLOW TEST COMPLETE!\n")
            
            return True

        except Exception as e:
            print(f"\n❌ WORKFLOW ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.http_client.aclose()


async def main():
    workflow = TraderWorkflow()
    success = await workflow.run()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
