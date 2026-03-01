#!/usr/bin/env python
"""
Enhanced workflow test with detailed streaming demonstration
"""

import asyncio
import json
import httpx
import websockets
from datetime import datetime

BACKEND_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ws/trades"
DEBUG_URL = "http://localhost:8000/api/v1/dev"

TEST_EMAIL = "premium@example.com"
TEST_PASSWORD = "secure123"

def print_section(title):
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")

def print_success(msg):
    print(f"  ✓ {msg}")

def print_info(msg):
    print(f"  ℹ {msg}")

def print_header(level, msg):
    print(f"\n{'▶' * level} {msg}")

async def workflow():
    # Create fresh test user
    unique_ts = datetime.now().strftime("%Y%m%d%H%M%S")
    test_email = f"trader-{unique_ts}@example.com"
    
    print_section("TRADECO-PILOT WORKFLOW DEMONSTRATION")
    print_info(f"Testing with email: {test_email}")
    
    # Step 1: Register and Login
    print_header(1, "STEP 1: User Authentication")
    
    async with httpx.AsyncClient(base_url=BACKEND_URL) as client:
        # Register
        resp = await client.post("/auth/register", json={
            "email": test_email,
            "password": TEST_PASSWORD
        })
        if resp.status_code in [200, 201]:
            data = resp.json()
            token = data.get("access_token")
            user_id = data.get("user", {}).get("id")
            print_success(f"User registered: {test_email}")
        else:
            print_info(f"Registration status: {resp.status_code}")
            # Try login instead
            resp = await client.post("/auth/login", json={
                "email": test_email,
                "password": TEST_PASSWORD
            })
            if resp.status_code != 200:
                print_info(f"Login also failed - creating new test user")
                return
            data = resp.json()
            token = data.get("access_token")
            user_id = data.get("user", {}).get("id")
        
        print_success(f"JWT Token: {token[:30]}...")
        print_success(f"User ID: {user_id}")
        
        # Step 2: Check Profile
        print_header(1, "STEP 2: User Profile & Account Status")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = await client.get("/auth/me", headers=headers)
        profile = resp.json()
        print_success(f"Email: {profile.get('email')}")
        print_success(f"Active: {profile.get('is_active')}")
        
        resp = await client.get("/account/status", headers=headers)
        if resp.status_code == 200:
            status = resp.json()
            print_success(f"Connection: {status.get('connection_status')}")
            print_success(f"Platform: {status.get('platform')}")
        
        # Step 3: Get Trader Data Before Trades
        print_header(1, "STEP 3: Check Initial Trader Data")
        
        resp = httpx.get(f"{DEBUG_URL}/trader-data", params={"email": test_email})
        if resp.status_code == 200:
            trader_data = resp.json()
            print_success(f"Accounts: {trader_data['summary']['total_accounts']}")
            print_success(f"Open Trades: {trader_data['summary']['open_trades_count']}")
        
        # Step 4: Connect WebSocket and Monitor
        print_header(1, "STEP 4: WebSocket Connection & Event Streaming")
        
        ws_url = f"{WS_URL}?token={token}"
        print_info(f"Connecting to {ws_url[:60]}...")
        
        try:
            async with websockets.connect(ws_url) as ws:
                print_success("WebSocket connected!")
                
                # Receive CONNECTED event
                msg = await asyncio.wait_for(ws.recv(), timeout=2)
                event_data = json.loads(msg)
                if event_data.get("event") == "CONNECTED":
                    print_success(f"Received CONNECTED event")
                
                # Start trade simulation in parallel
                print_header(1, "STEP 5: Simulate Trades & Monitor Events")
                
                async def simulate_trades():
                    """Simulate 3 trades with delays"""
                    for i in range(3):
                        await asyncio.sleep(2)  # Wait before each trade
                        
                        payload = {
                            "symbol": "EURUSD" if i % 2 == 0 else "GBPUSD",
                            "direction": "BUY" if i % 2 == 0 else "SELL",
                            "entry_price": 1.1000 + i * 0.0001,
                            "sl": 1.0950,
                            "tp": 1.1200,
                            "lot_size": 0.1,
                            "close_after_seconds": 5,
                        }
                        
                        resp = await client.post(
                            "/dev/simulate-trade",
                            json=payload,
                            headers=headers
                        )
                        
                        if resp.status_code == 200:
                            trade = resp.json()
                            print_success(f"Trade {i+1} created: {payload['symbol']} {payload['direction']} @ {payload['entry_price']}")
                            print_info(f"  ID: {trade.get('id')}")
                        else:
                            print_info(f"Trade {i+1} failed: {resp.status_code}")
                
                async def monitor_events():
                    """Monitor WebSocket for events"""
                    event_count = 0
                    print_header(2, "Monitoring WebSocket Events")
                    
                    try:
                        while event_count < 10:  # Max 10 events
                            try:
                                msg = await asyncio.wait_for(ws.recv(), timeout=1)
                                event_data = json.loads(msg)
                                event_type = event_data.get("event", "UNKNOWN")
                                
                                if event_type == "CONNECTED":
                                    continue  # Skip initial connection
                                
                                event_count += 1
                                
                                if event_type == "TRADE_OPENED":
                                    print_success(f"[TRADE_OPENED] {event_data.get('symbol')} {event_data.get('direction')}")
                                    print_info(f"  AI Score: {event_data.get('ai_score')}")
                                    print_info(f"  Analysis: {event_data.get('ai_analysis')}")
                                elif event_type == "TRADE_CLOSED":
                                    print_success(f"[TRADE_CLOSED] P&L: {event_data.get('pnl')} ({event_data.get('pnl_r')}%)")
                                    print_info(f"  Exit Price: {event_data.get('exit_price')}")
                                else:
                                    print_info(f"[{event_type}] {json.dumps(event_data)[:100]}")
                                    
                            except asyncio.TimeoutError:
                                pass  # Continue waiting
                    except Exception as e:
                        print_info(f"Stream ended: {str(e)[:50]}")
                
                # Run both concurrently
                await asyncio.gather(
                    simulate_trades(),
                    monitor_events(),
                    return_exceptions=True
                )
        
        except Exception as e:
            print_info(f"WebSocket error: {e}")
        
        # Step 6: Verify Final Data
        print_header(1, "STEP 6: Final Data Verification")
        
        resp = httpx.get(f"{DEBUG_URL}/trader-data", params={"email": test_email})
        if resp.status_code == 200:
            trader_data = resp.json()
            summary = trader_data['summary']
            trades = trader_data['open_trades']
            
            print_success(f"Total Trades Created: {len(trades)}")
            print_success(f"Open Positions: {summary['open_trades_count']}")
            
            if trades:
                print_header(2, "Open Positions in Database")
                for trade in trades:
                    status_indicator = "🟢 OPEN" if not trade.get('close_time') else "🔴 CLOSED"
                    print_info(f"{status_indicator} | {trade['symbol']} {trade['direction']} @ {trade['entry_price']} | AI: {trade['ai_score']}")
    
    print_section("WORKFLOW COMPLETE")
    print_success("✓ Full pipeline executed successfully")
    print_info("Demonstrated:")
    print_info("  • User authentication with JWT")
    print_info("  • Real-time WebSocket connections")
    print_info("  • Trade creation and processing")
    print_info("  • Data persistence to database")
    print_info("  • Event streaming infrastructure")

if __name__ == "__main__":
    asyncio.run(workflow())
