import uuid
import pytest
from datetime import datetime, timezone
import httpx

from app.database import async_session_factory
from app.models.user import User
from app.models.trade import Trade, TradeStatus
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_patterns_and_alerts_endpoints():
    # create a user and some trades with behavioral flags
    async with async_session_factory() as db:
        user = User(
            id=uuid.uuid4(),
            email=f"pattern_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="mock_hash",
        )
        db.add(user)
        await db.commit()

        user_id = str(user.id)
        # create two closed trades with flags
        trade1 = Trade(
            id=uuid.uuid4(),
            user_id=user.id,
            symbol="EURUSD",
            direction="BUY",
            entry_price=1.0,
            exit_price=1.1,
            pnl=100,
            pnl_r=1,
            status=TradeStatus.CLOSED,
            open_time=datetime.now(timezone.utc),
            close_time=datetime.now(timezone.utc),
            behavioral_flags=[{"flag": "revenge_trading", "message": "test", "severity": "high"}],
        )
        trade2 = Trade(
            id=uuid.uuid4(),
            user_id=user.id,
            symbol="GBPUSD",
            direction="SELL",
            entry_price=1.5,
            exit_price=1.4,
            pnl=-50,
            pnl_r=-0.5,
            status=TradeStatus.CLOSED,
            open_time=datetime.now(timezone.utc),
            close_time=datetime.now(timezone.utc),
            behavioral_flags=[{"flag": "overtrading", "message": "test", "severity": "low"}],
        )
        db.add_all([trade1, trade2])
        await db.commit()

    # generate JWT for user
    token = create_access_token({"sub": user_id})
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", headers=headers) as client:
        res = await client.get("/api/v1/analysis/patterns")
        assert res.status_code == 200
        data = res.json()
        assert data["total_trades_analyzed"] >= 2
        assert isinstance(data["patterns"], list)

        res2 = await client.get("/api/v1/analysis/alerts")
        assert res2.status_code == 200
        alerts = res2.json()
        assert isinstance(alerts, list)
        assert len(alerts) >= 2
        assert "pattern_type" in alerts[0]
