#!/usr/bin/env python
"""Check data for trader@example.com account."""

import asyncio
from sqlalchemy import select
from app.database import async_session_factory, init_db
from app.models.user import User
from app.models.meta_account import MetaAccount
from app.models.trade import Trade, TradeStatus


async def main():
    """Get trader@example.com account data."""
    # Initialize database
    await init_db()
    
    async with async_session_factory() as db:
        # Find user
        print("\n" + "="*60)
        print("🔍 LOOKING UP: trader@example.com")
        print("="*60 + "\n")
        
        result = await db.execute(select(User).where(User.email == "trader@example.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User trader@example.com NOT FOUND in database\n")
            return
        
        print(f"✅ User Found:")
        print(f"   📧 Email: {user.email}")
        print(f"   🆔 User ID: {user.id}")
        print(f"   ✔️  Verified: {user.is_verified}")
        print()
        
        # Find MetaAPI accounts
        print("-" * 60)
        print("📈 METAAPI ACCOUNTS")
        print("-" * 60 + "\n")
        
        result = await db.execute(select(MetaAccount).where(MetaAccount.user_id == user.id))
        accounts = result.scalars().all()
        
        if not accounts:
            print("❌ No MetaAPI accounts connected\n")
            return
        
        print(f"✅ Found {len(accounts)} MetaAPI Account(s):\n")
        for i, acc in enumerate(accounts, 1):
            print(f"Account #{i}:")
            print(f"   Account ID: {acc.metaapi_account_id}")
            print(f"   MT Login: {acc.mt_login}")
            print(f"   MT Server: {acc.mt_server}")
            print(f"   MT Platform: {acc.mt_platform.upper()}")
            print(f"   Last Heartbeat: {acc.mt_last_heartbeat}")
            print()
        
        # Find open trades
        print("-" * 60)
        print("📊 OPEN POSITIONS")
        print("-" * 60 + "\n")
        
        result = await db.execute(
            select(Trade).where(
                (Trade.user_id == user.id) & 
                (Trade.status == TradeStatus.OPEN)
            )
        )
        trades = result.scalars().all()
        
        if not trades:
            print("❌ No open trades in database\n")
            return
        
        print(f"✅ Found {len(trades)} Open Trade(s):\n")
        for i, trade in enumerate(trades, 1):
            direction_emoji = "📈" if trade.direction.value == "BUY" else "📉"
            print(f"{direction_emoji} Trade #{i}:")
            print(f"   Trade ID: {trade.id}")
            print(f"   Symbol: {trade.symbol}")
            print(f"   Direction: {trade.direction.value}")
            print(f"   Entry Price: {trade.entry_price}")
            print(f"   Lot Size: {trade.lot_size}")
            print(f"   Stop Loss: {trade.sl}")
            print(f"   Take Profit: {trade.tp}")
            print(f"   Open Time: {trade.open_time}")
            print(f"   AI Score: {trade.ai_score}")
            print()
        
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
