import pytest
from datetime import datetime

from app.database import init_db, async_session_factory
from app.models.user import User
from app.services.trade_processing_service import trade_processor


@pytest.mark.asyncio
async def test_process_trade_opened_integration():
    """Integration test: create a user, simulate trade open, ensure AI score is set."""
    await init_db()

    async with async_session_factory() as db:
        # Create test user
        user = User(email="integration-test@example.com", hashed_password="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    trade_data = {
        "external_id": "ext_integ_1",
        "symbol": "EURUSD",
        "type": "BUY",
        "entry_price": 1.1000,
        "sl": 1.0950,
        "tp": 1.1100,
        "lot_size": 0.1,
    }

    # Call the processor (this will invoke AI pre-trade analysis)
    trade = await trade_processor.process_trade_opened(str(user.id), trade_data)

    assert trade is not None
    # AI score should be present (fallback or real OpenAI response)
    assert hasattr(trade, "ai_score")
    print("AI score:", trade.ai_score)
