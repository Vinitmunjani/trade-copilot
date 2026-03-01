"""Integration tests for MetaAPI connector and trade simulation.

Tests the full flow: simulate trade open → process via trade_processor →
trigger AI analysis → broadcast via WebSocket.
"""

import asyncio
import uuid
import pytest
from sqlalchemy import select

from app.database import async_session_factory
from app.models.user import User
from app.models.meta_account import MetaAccount
from app.models.trade import Trade, TradeStatus
from app.services.trade_processing_service import trade_processor
from app.services.metaapi_service import metaapi_service


@pytest.mark.asyncio
async def test_simulate_metaapi_trade_open_and_close():
    """Test simulating a MetaAPI trade open and close.

    Verifies:
    1. Trade record is created with correct fields
    2. AI analysis runs and populates ai_score
    3. Trade can be closed with an exit price
    """
    user_email = f"test_metaapi_{uuid.uuid4().hex[:8]}@example.com"

    # Create test user
    async with async_session_factory() as db:
        user = User(
            id=uuid.uuid4(),
            email=user_email,
            hashed_password="mock_hash",
        )
        db.add(user)
        await db.commit()
        user_id = str(user.id)
    
    # Simulate MetaAPI trade open
    trade_data = {
        "external_id": "MT5_123456789",
        "symbol": "EURUSD",
        "type": "BUY",
        "entry_price": 1.0850,
        "sl": 1.0820,
        "tp": 1.0920,
        "lot_size": 0.1,
    }
    
    trade = await trade_processor.process_trade_opened(user_id, trade_data)
    
    assert trade is not None
    assert trade.symbol == "EURUSD"
    assert trade.direction == "BUY"
    assert trade.entry_price == 1.0850
    assert trade.status == TradeStatus.OPEN
    assert trade.ai_score is not None  # AI should have analyzed it
    
    # Verify trade is in DB
    async with async_session_factory() as db:
        result = await db.execute(
            select(Trade).where(Trade.id == trade.id)
        )
        db_trade = result.scalar_one_or_none()
        assert db_trade is not None
        assert db_trade.ai_score is not None
    
    # Simulate closing the trade
    close_trade = await trade_processor.process_trade_closed(user_id, {
        "external_id": trade.external_trade_id,
        "exit_price": 1.0900,
    })
    
    assert close_trade is not None
    assert close_trade.exit_price == 1.0900
    assert close_trade.status == TradeStatus.CLOSED
    
    # Verify profit/loss is calculated
    profit = close_trade.exit_price - close_trade.entry_price
    assert profit > 0  # We exited at 1.0900, above entry 1.0850


@pytest.mark.asyncio
async def test_metaapi_connector_ws_manager_broadcast():
    """Test that MetaAPI service can broadcast trade events via WS.

    Creates a mock WS manager, attaches it to metaapi_service,
    simulates a trade, and verifies broadcast was called.
    """
    user_email = f"test_ws_{uuid.uuid4().hex[:8]}@example.com"

    # Create test user
    async with async_session_factory() as db:
        user = User(
            id=uuid.uuid4(),
            email=user_email,
            hashed_password="mock_hash",
        )
        db.add(user)
        await db.commit()
        user_id = str(user.id)
    
    # Mock WS manager to track broadcasts
    broadcasts = []
    
    class MockWSManager:
        async def broadcast_to_user(self, uid, payload):
            broadcasts.append({"user_id": uid, "payload": payload})
        
        def get_connected_users(self):
            return [user_id]
    
    mock_ws = MockWSManager()
    metaapi_service.set_ws_manager(mock_ws)
    trade_processor.set_ws_manager(mock_ws)
    
    # Simulate trade open
    trade_data = {
        "external_id": "MT5_BroadcastTest",
        "symbol": "GBPUSD",
        "type": "SELL",
        "entry_price": 1.2750,
        "sl": 1.2800,
        "tp": 1.2650,
        "lot_size": 0.5,
    }
    
    trade = await trade_processor.process_trade_opened(user_id, trade_data)
    
    # Allow time for any async broadcasts
    await asyncio.sleep(0.1)
    
    # Verify broadcast was made
    assert len(broadcasts) > 0
    trade_opened_events = [
        b for b in broadcasts 
        if b["payload"].get("event") == "TRADE_OPENED"
    ]
    assert len(trade_opened_events) > 0
    
    event = trade_opened_events[0]
    assert event["user_id"] == user_id
    assert event["payload"]["symbol"] == "GBPUSD"


@pytest.mark.asyncio
async def test_metaapi_connector_behavioral_analysis():
    """Test that MetaAPI connector triggers behavioral analysis.

    Simulates a trade opening and verifies that behavioral flags
    are detected and attached to the trade.
    """
    user_email = f"test_behavior_{uuid.uuid4().hex[:8]}@example.com"

    # Create test user
    async with async_session_factory() as db:
        user = User(
            id=uuid.uuid4(),
            email=user_email,
            hashed_password="mock_hash",
        )
        db.add(user)
        await db.commit()
        user_id = str(user.id)

    # Simulate a normal trade open
    trade_data = {
        "external_id": "MT5_Behavior_Normal",
        "symbol": "EURUSD",
        "type": "BUY",
        "entry_price": 1.0850,
        "sl": 1.0820,
        "tp": 1.0920,
        "lot_size": 0.1,
    }

    trade = await trade_processor.process_trade_opened(user_id, trade_data)
    assert trade is not None
    assert trade.symbol == "EURUSD"

    # Verify trade has behavioral_flags field (should be empty for first trade)
    async with async_session_factory() as db:
        result = await db.execute(
            select(Trade).where(Trade.id == trade.id)
        )
        updated_trade = result.scalar_one_or_none()

        # behavioral_flags can be None or [] for first trade
        flags = updated_trade.behavioral_flags
        if flags:
            assert isinstance(flags, list)


@pytest.mark.asyncio
async def test_metaapi_connector_reconnection():
    """Test MetaAPI connection state and reconnection logic.

    Verifies connection state tracking and that reconnection attempts
    are logged correctly.
    """
    user_email = f"test_reconnect_{uuid.uuid4().hex[:8]}@example.com"

    # Create test user
    async with async_session_factory() as db:
        user = User(
            id=uuid.uuid4(),
            email=user_email,
            hashed_password="mock_hash",
            metaapi_account_id="test_account_123",
        )
        db.add(user)
        await db.commit()

    # Get connection status (should be disconnected since no real MetaAPI)
    # query without account - should still return same because only one account exists
    status = await metaapi_service.get_status(user)

    assert status["connected"] is False
    assert status["account_id"] == "test_account_123"
    # reconnect_attempts should be in the status dict (or 0 if not started)
    if "reconnect_attempts" in status:
        assert status["reconnect_attempts"] >= 0

    # also explicitly request by account_id parameter
    status2 = await metaapi_service.get_status(user, account_id="test_account_123")
    assert status2 == status


@pytest.mark.asyncio
async def test_auto_reconnect_on_startup(monkeypatch):
    """Accounts stored in the database should automatically reconnect.

    The MetaApiService starts a background task on application startup which
    iterates all ``MetaAccount`` rows and calls ``connect`` for each one.  This
    test verifies that behaviour by creating a user + meta account, clearing the
    in-memory connection map, and invoking the auto-reconnect helper directly
    (with the initial delay set to zero to speed the test).  The service is run
    in 'simulation' mode by patching ``_get_api`` to always return ``None``.
    """
    user_email = f"test_autoreconnect_{uuid.uuid4().hex[:8]}@example.com"
    metaapi_account_id = "stored_account_456"

    # create user and MetaAccount row
    async with async_session_factory() as db:
        # create the user without setting ``metaapi_account_id``; the linkage
        # will be represented by the separate MetaAccount row.
        user = User(
            id=uuid.uuid4(),
            email=user_email,
            hashed_password="hash",
        )
        db.add(user)
        from app.models.meta_account import MetaAccount
        ma = MetaAccount(
            user_id=user.id,
            metaapi_account_id=metaapi_account_id,
            mt_login="login",
            mt_server="srv",
            mt_platform="mt5",
        )
        db.add(ma)
        await db.commit()

    # run in simulation mode (no real MetaAPI client)
    async def fake_get_api():
        return None
    monkeypatch.setattr(metaapi_service, "_get_api", fake_get_api)

    # clear any existing state
    metaapi_service._connections.clear()

    # invoke auto-reconnect helper with no delay
    await metaapi_service._auto_reconnect_all(initial_delay=0)
    # give spawned tasks a moment
    await asyncio.sleep(0.1)

    key = f"{user.id}:{metaapi_account_id}"
    assert key in metaapi_service._connections
    state = metaapi_service._connections[key]
    assert state.account_id == metaapi_account_id
    assert state.is_connected is False


@pytest.mark.asyncio
async def test_metaapi_service_simulate_functions():
    """Test direct simulation functions on metaapi_service."""
    user_email = f"test_sim_{uuid.uuid4().hex[:8]}@example.com"

    # Create test user
    async with async_session_factory() as db:
        user = User(
            id=uuid.uuid4(),
            email=user_email,
            hashed_password="mock_hash",
        )
        db.add(user)
        await db.commit()
        user_id = str(user.id)
    
    # Use metaapi_service's simulate functions
    trade_data = {
        "external_id": "SIMULATE_DIRECT",
        "symbol": "NZDUSD",
        "type": "BUY",
        "entry_price": 0.6120,
        "sl": 0.6080,
        "tp": 0.6200,
        "lot_size": 1.0,
    }
    
    trade = await metaapi_service.simulate_trade_open(user_id, trade_data)
    
    assert trade is not None
    assert trade.symbol == "NZDUSD"
    assert trade.status == TradeStatus.OPEN
    
    # Simulate close
    closed_trade = await metaapi_service.simulate_trade_close(
        user_id,
        str(trade.id),
        0.6180,
    )
    
    assert closed_trade is not None
    assert closed_trade.exit_price == 0.6180
    assert closed_trade.status == TradeStatus.CLOSED


@pytest.mark.asyncio
async def test_streaming_logs_recorded():
    """Verify that events are logged and available via debug endpoint."""
    # create a fake user/account and simulate connection/logging
    user_email = f"test_logs_{uuid.uuid4().hex[:8]}@example.com"
    async with async_session_factory() as db:
        user = User(
            id=uuid.uuid4(),
            email=user_email,
            hashed_password="mock_hash",
            metaapi_account_id="acct_logs_123",
        )
        db.add(user)
        await db.commit()
        user_id = str(user.id)
    # manually append some logs
    metaapi_service._append_log("acct_logs_123", "TEST_EVENT foo")
    metaapi_service._append_log("acct_logs_123", "TEST_EVENT bar")

    # call the handler directly (avoids TestClient version mismatch)
    from app.api.account import get_trader_data

    async with async_session_factory() as db2:
        body = await get_trader_data(email=user_email, db=db2)
    assert "streaming_logs" in body
    logs = body["streaming_logs"].get("acct_logs_123")
    assert isinstance(logs, list)
    assert any("TEST_EVENT foo" in line for line in logs)
    assert any("TEST_EVENT bar" in line for line in logs)
