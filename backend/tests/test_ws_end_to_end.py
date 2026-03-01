import pytest
from starlette.testclient import TestClient

from app.database import init_db, async_session_factory
from app.models.user import User
from app.core.security import create_access_token
from app.services.trade_processing_service import trade_processor
from app.main import app


@pytest.mark.asyncio
async def test_ws_receives_trade_open_event():
    # Prepare DB and user
    await init_db()
    import uuid
    unique_email = f"e2e-ws-{uuid.uuid4().hex[:8]}@example.com"
    async with async_session_factory() as db:
        user = User(email=unique_email, hashed_password="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})

    trade_data = {
        "external_id": "e2e_ext_1",
        "symbol": "EURUSD",
        "type": "BUY",
        "entry_price": 1.1000,
        "sl": 1.0950,
        "tp": 1.1100,
        "lot_size": 0.1,
    }

    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/trades?token={token}") as websocket:
            # initial CONNECTED message
            msg = websocket.receive_json()
            assert msg.get("event") == "CONNECTED"

            # Trigger trade processing (AI analysis + broadcast)
            trade = pytest.raises(Exception)
            # Call the async processor
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                trade_processor.process_trade_opened(str(user.id), trade_data)
            )

            # Receive broadcast
            broadcast = websocket.receive_json()
            assert broadcast.get("event") == "TRADE_OPENED"
            assert broadcast.get("symbol") == "EURUSD"
            assert "ai_score" in broadcast
