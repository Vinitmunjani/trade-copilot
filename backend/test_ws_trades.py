#!/usr/bin/env python3
"""Test WebSocket connection to stream real trades from MetaAPI account."""

import asyncio
import websockets
import json
import pytest
from app.core.security import create_access_token
from app.database import async_session_factory, init_db
from app.models.user import User
from app.models.meta_account import MetaAccount
from sqlalchemy import select

pytestmark = pytest.mark.skip(reason="Manual integration script; not part of automated pytest suite")

async def test_ws_trades():
    """Connect to WebSocket and listen for trades."""
    
    # Get test user JWT
    print("📝 Setting up test user for WebSocket...")
    await init_db()
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == 'metaapi_test@example.com'))
        user = result.scalar_one_or_none()
        if not user:
            print("❌ User not found (need to run test_correct_login.py first)")
            return
    
    user_id = str(user.id)
    token = create_access_token({"sub": user_id})
    
    print(f"✅ User ready: {user_id}")
    print(f"🔑 Token: {token[:50]}...")
    
    # Connect to WebSocket
    ws_url = f"ws://localhost:8000/api/v1/ws/trades?token={token}"
    print(f"\n🔗 Connecting to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as websocket:
            print("✅ WebSocket connected!")
            print("⏳ Listening for trade events (60 seconds)...\n")
            
            start_time = asyncio.get_event_loop().time()
            event_count = 0
            
            try:
                while asyncio.get_event_loop().time() - start_time < 60:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        event_count += 1
                        data = json.loads(message)
                        
                        print(f"\n📊 Event #{event_count}:")
                        print(f"  Type: {data.get('type', 'unknown')}")
                        
                        if data.get('type') == 'TRADE_OPENED':
                            trade = data.get('trade', {})
                            print(f"  Symbol: {trade.get('symbol', 'N/A')}")
                            print(f"  Direction: {trade.get('direction', 'N/A')}")
                            print(f"  Entry: {trade.get('entryPrice', 'N/A')}")
                            print(f"  Volume: {trade.get('volume', 'N/A')}")
                            print(f"  Time: {trade.get('openTime', 'N/A')}")
                        
                        elif data.get('type') == 'TRADE_CLOSED':
                            trade = data.get('trade', {})
                            print(f"  Symbol: {trade.get('symbol', 'N/A')}")
                            print(f"  Profit: {trade.get('profit', 'N/A')}")
                            print(f"  Profit %: {trade.get('profitPercent', 'N/A')}")
                            print(f"  Close Time: {trade.get('closeTime', 'N/A')}")
                        
                        else:
                            print(f"  Data: {json.dumps(data, indent=2)}")
                            
                    except asyncio.TimeoutError:
                        elapsed = int(asyncio.get_event_loop().time() - start_time)
                        print(f"⏳ {elapsed}s - waiting for events...")
                        continue
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Failed to parse message: {e}")
                        continue
                
            except KeyboardInterrupt:
                print("\n\n⚙️  Interrupted by user")
            except websockets.exceptions.ConnectionClosed:
                print("\n⚠️  Connection closed by server")
            
            print(f"\n{'='*60}")
            print(f"📈 Summary:")
            print(f"  Total events received: {event_count}")
            print(f"  Duration: {int(asyncio.get_event_loop().time() - start_time)}s")
            
            if event_count == 0:
                print("\n⚠️  No trade events received in 60 seconds.")
                print("   This could mean:")
                print("   - No active trades on the MT5 account")
                print("   - MetaAPI account not connected yet")
                print("   - Streaming not initialized")
            else:
                print(f"\n✅ SUCCESS! Received {event_count} trade events from MetaAPI!")
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ws_trades())
