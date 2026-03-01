import pytest

from app.database import init_db, async_session_factory
from app.models.user import User
from app.services.trade_processing_service import trade_processor


class MockWSManager:
    def __init__(self):
        self.messages = []

    async def broadcast_to_user(self, user_id: str, payload: dict):
        self.messages.append((user_id, payload))


@pytest.mark.asyncio
async def test_trade_open_broadcasts_to_ws_manager():
    await init_db()

    mock_ws = MockWSManager()
    trade_processor.set_ws_manager(mock_ws)

    async with async_session_factory() as db:
        user = User(email="ws-test@example.com", hashed_password="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    trade_data = {
        "external_id": "ws_ext_1",
        "symbol": "EURUSD",
        "type": "BUY",
        "entry_price": 1.1000,
        "sl": 1.0950,
        "tp": 1.1100,
        "lot_size": 0.1,
    }

    trade = await trade_processor.process_trade_opened(str(user.id), trade_data)
    assert trade is not None

    # Ensure the mock ws manager received at least one broadcast for this user
    assert len(mock_ws.messages) >= 1
    user_id, payload = mock_ws.messages[0]
    assert user_id == str(user.id)
    assert payload.get("event") == "TRADE_OPENED"
    assert payload.get("trade_id") == str(trade.id)
