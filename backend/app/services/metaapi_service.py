"""MetaAPI integration service.

Manages connections to MT4/MT5 broker accounts via MetaAPI Cloud SDK.
Listens for trade events (open, update, close), normalizes data,
triggers AI analysis, and broadcasts via WebSocket.
"""

import asyncio
import logging
import uuid
import os
from datetime import datetime, timezone
from typing import Dict,  Optional, Any

from sqlalchemy import select, and_

from app.config import get_settings
from app.database import async_session_factory
from app.services.trade_processing_service import trade_processor
from app.models.trade import Trade, TradeStatus
from app.models.user import User

logger = logging.getLogger(__name__)
# settings are loaded on demand inside methods to allow dynamic updates


class ConnectionState:
    """Track a user's MetaAPI connection state."""

    def __init__(self, user_id: str, account_id: str):
        self.user_id = user_id
        self.account_id = account_id
        self.connection = None
        self.account = None
        self.listener_task: Optional[asyncio.Task] = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5


class MetaApiService:
    """Manages MetaAPI connections for all users.

    Handles connecting to user broker accounts, subscribing to trade events,
    normalizing trade data, and coordinating with AI analysis and WebSocket broadcasting.
    """

    def __init__(self):
        # connections keyed by "{user_id}:{account_id}" to allow multiple accounts per user
        self._connections: Dict[str, ConnectionState] = {}
        self._ws_manager = None  # Set externally
        self._api = None
        # keep streaming/event logs per MetaAPI account for debugging/testing
        # keyed by "account_id"; we store only the most recent 200 entries per account
        self._logs: Dict[str, list] = {}

    def _append_log(self, account_id: str, message: str) -> None:
        """Internal helper: append a line to the in-memory log buffer.

        Limits the stored entries to avoid unbounded growth.
        """
        if account_id not in self._logs:
            self._logs[account_id] = []
        log_list = self._logs[account_id]
        log_list.append(f"[{datetime.now(timezone.utc).isoformat()}] {message}")
        # keep last 200 lines
        if len(log_list) > 200:
            del log_list[: len(log_list) - 200]

    def get_logs(self, account_id: Optional[str] = None):
        """Return stored logs.

        If ``account_id`` is provided returns only that account's logs;
        otherwise returns the full mapping.
        """
        if account_id:
            return list(self._logs.get(account_id, []))
        return {k: list(v) for k, v in self._logs.items()}

    def is_account_connected(self, user_id: str, account_id: str) -> bool:
        """Check whether a specific user/account streaming connection is live."""
        conn_key = f"{user_id}:{account_id}"
        state = self._connections.get(conn_key)
        return bool(state and state.is_connected)

    async def _touch_heartbeat(self, user_id: str, account_id: str) -> None:
        """Persist a heartbeat timestamp for an account and legacy user fields."""
        now_utc = datetime.now(timezone.utc)
        try:
            async with async_session_factory() as db:
                from app.models.meta_account import MetaAccount

                result = await db.execute(
                    select(MetaAccount).where(
                        and_(
                            MetaAccount.user_id == uuid.UUID(user_id),
                            MetaAccount.metaapi_account_id == account_id,
                        )
                    )
                )
                ma = result.scalar_one_or_none()
                if ma:
                    ma.mt_last_heartbeat = now_utc

                user_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
                user = user_result.scalar_one_or_none()
                if user and user.metaapi_account_id == account_id:
                    user.mt_last_heartbeat = now_utc

                await db.commit()
        except Exception as e:
            logger.debug(f"Failed to persist heartbeat for account {account_id}: {e}")

    async def _get_api(self):
        """Lazily create and return the MetaApi client instance.

        The token is fetched from settings on every call so that changes made
        to the environment (or by tests) are respected.  Callers may also
        inject a temporary settings object by assigning ``metaapi_service.settings``
        (see ``app/api/account.py``).

        Returns None when MetaAPI token is not configured or client creation fails.
        """
        if getattr(self, "_api", None):
            return self._api

        # prefer override set on instance for testing/injection
        settings = getattr(self, "settings", None) or get_settings()
        token = settings.METAAPI_TOKEN
        if not token:
            logger.warning("METAAPI_TOKEN not configured; MetaAPI client disabled")
            return None

        try:
            # Import lazily to avoid hard dependency at import time
            from metaapi_cloud_sdk import MetaApi

            api = MetaApi(token)
            # The SDK may expose async connect; attempt to await if present
            connect = getattr(api, "connect", None)
            if callable(connect):
                maybe_coro = connect()
                if hasattr(maybe_coro, "__await__"):
                    await maybe_coro

            self._api = api
            return api

        except Exception as e:
            logger.error(f"Failed to initialize MetaAPI client: {e}")
            return None

    def set_ws_manager(self, ws_manager: Any) -> None:
        """Set the WebSocket manager for broadcasting events.

        Args:
            ws_manager: WebSocket connection manager instance.
        """
        self._ws_manager = ws_manager

    async def lifespan(self):
        """Setup dependencies on startup.

        The service configures the trade processor and starts a background
        task to automatically reconnect any previously linked MetaAPI
        accounts.  This ensures that once a user has connected their broker
        account the backend will re-establish the streaming connection after
        a restart without requiring additional action from the user.
        """
        trade_processor.set_ws_manager(self._ws_manager)
        logger.info("✅ TradeProcessor configured with WS manager")
        # Start background reconnects for any users who already have a MetaAPI account ID
        # (runs separately so startup isn't blocked)
        asyncio.create_task(self._auto_reconnect_all())

    async def shutdown(self) -> None:
        """Gracefully shutdown all MetaAPI connections and client.

        Closes streaming connections, cancels listener tasks, and calls
        the SDK `close()` to ensure aiohttp sessions are cleaned up.
        """
        logger.info("MetaApiService shutting down: closing connections and SDK client")
        # Cancel and close per-user connections
        for user_id, state in list(self._connections.items()):
            try:
                if state.listener_task and not state.listener_task.done():
                    state.listener_task.cancel()
                    try:
                        await state.listener_task
                    except asyncio.CancelledError:
                        pass

                if state.connection:
                    try:
                        await state.connection.close()
                    except Exception as e:
                        logger.debug(f"Error closing streaming connection for user {user_id}: {e}")

            except Exception as e:
                logger.debug(f"Error during shutdown for user {user_id}: {e}")

        # Close global MetaAPI client if present
        try:
            api = getattr(self, '_api', None)
            if api:
                # Prefer awaiting the websocket client's close coroutine if available
                ws_client = getattr(api, '_metaapi_websocket_client', None)
                if ws_client and hasattr(ws_client, 'close'):
                    try:
                        close_coro = getattr(ws_client, 'close')
                        if asyncio.iscoroutinefunction(close_coro):
                            await close_coro()
                        else:
                            # If close is a coroutine method bound to instance, call and await
                            res = close_coro()
                            if asyncio.iscoroutine(res):
                                await res
                    except Exception as e:
                        logger.debug(f"Error awaiting websocket client close(): {e}")

                # Call public API close() to perform remaining cleanup (non-blocking)
                close_fn = getattr(api, 'close', None)
                if callable(close_fn):
                    try:
                        close_fn()
                    except Exception as e:
                        logger.debug(f"Error calling MetaAPI.close(): {e}")
        except Exception as e:
            logger.debug(f"Error shutting down MetaApiService: {e}")

    async def _auto_reconnect_all(self, initial_delay: float = 2.0) -> None:
        """Attempt to connect all users with a stored MetaAPI account ID on startup.

        Args:
            initial_delay: time to sleep before beginning reconnection attempts;
                default 2 seconds to allow other startup tasks to complete.  Tests
                may override this by calling directly with 0 or by monkeypatching
                ``asyncio.sleep``.

        This avoids requiring users to press "Connect" again (which would provision)
        and prevents accidental repeated provisioning/charges.  Each account is
        handled in its own task so that a slow or failing account does not block
        the others.
        """
        try:
            await asyncio.sleep(initial_delay)  # give app a moment to settle
            async with async_session_factory() as session:
                # Reconnect for every MetaAccount row (supports many accounts per user)
                from app.models.meta_account import MetaAccount
                result = await session.execute(
                    select(MetaAccount).where(MetaAccount.metaapi_account_id != None)
                )
                accounts = result.scalars().all()

            for ma in accounts:
                # Kick off separate tasks so a slow connect doesn't block others
                asyncio.create_task(self._safe_connect_account(ma))
        except Exception as e:
            logger.error(f"Failed to start auto-reconnect tasks: {e}")

    async def _safe_connect_user(self, user: User) -> None:
        try:
            logger.info(f"Auto-reconnect: attempting MetaAPI connect for user {user.id}")
            res = await self.connect(user)
            logger.info(f"Auto-reconnect result for user {user.id}: {res}")
        except Exception as e:
            logger.error(f"Auto-reconnect failed for user {user.id}: {e}")

    async def _safe_connect_account(self, meta_account) -> None:
        try:
            logger.info(f"Auto-reconnect: attempting MetaAPI connect for account {meta_account.metaapi_account_id}")
            # Load owning user
            async with async_session_factory() as session:
                result = await session.execute(select(User).where(User.id == meta_account.user_id))
                user = result.scalar_one_or_none()
            if user:
                res = await self.connect(user, account_id=meta_account.metaapi_account_id)
                logger.info(f"Auto-reconnect result for account {meta_account.metaapi_account_id}: {res}")
        except Exception as e:
            logger.error(f"Auto-reconnect failed for account {meta_account.metaapi_account_id}: {e}")

    async def connect(self, user: User, account_id: Optional[str] = None) -> dict:
        """Connect to a user's MT4/MT5 account via MetaAPI.

        Args:
            user: User model with metaapi_token and metaapi_account_id set.

        Returns:
            Dict with connection status info.
        """
        user_id = str(user.id)
        if account_id is None:
            account_id = user.metaapi_account_id

        if not account_id:
            return {"connected": False, "error": "No MetaAPI account ID configured"}

        conn_key = f"{user_id}:{account_id}"
        if conn_key in self._connections and self._connections[conn_key].is_connected:
            return {"connected": True, "account_id": account_id, "status": "already_connected"}

        state = ConnectionState(user_id, account_id)
        self._connections[conn_key] = state

        api = await self._get_api()
        if api is None:
            logger.info(f"MetaAPI unavailable — user {user_id} in simulation mode")
            state.is_connected = False
            return {"connected": False, "status": "simulation_mode", "account_id": account_id}

        try:
            # Get the MetaAPI account
            account = await api.metatrader_account_api.get_account(account_id)
            state.account = account
            
            # Log connection start
            self._append_log(account_id, f"🔌 Connecting to account {account_id[:12]}...")

            # Deploy if needed (with retries)
            if account.state not in ("DEPLOYED", "DEPLOYING"):
                self._append_log(account_id, "⏳ Deploying account...")
                try:
                    await account.deploy()
                    self._append_log(account_id, "✓ Account deployment initiated")
                except Exception as e:
                    logger.warning(f"Account deploy failed/timeout: {e}")
                    self._append_log(account_id, f"⚠️ Deploy warning: {str(e)[:80]}")
                    # log detailed exception
                    try:
                        os.makedirs('logs', exist_ok=True)
                        with open('logs/metaapi_connect_error.log', 'a', encoding='utf-8') as f:
                            f.write(f"[{datetime.now().isoformat()}] Deploy error for account {account_id}: {repr(e)}\n")
                    except Exception:
                        pass
            else:
                self._append_log(account_id, f"✓ Account already deployed (state: {account.state})")

            # Timeouts and retries configurable via env
            base_timeout = int(os.getenv('METAAPI_CONNECT_TIMEOUT', '90'))
            max_retries = int(os.getenv('METAAPI_CONNECT_RETRIES', '3'))

            # Wait for connection (with retries/backoff)
            connected_ok = False
            timeout = base_timeout
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        self._append_log(account_id, f"🔄 Connection attempt {attempt}/{max_retries}...")
                    logger.info(f"Waiting for account.wait_connected() attempt {attempt}/{max_retries} timeout={timeout}s")
                    await asyncio.wait_for(account.wait_connected(), timeout=timeout)
                    connected_ok = True
                    self._append_log(account_id, "✓ Account connected")
                    break
                except Exception as e:
                    logger.warning(f"Account wait_connected attempt {attempt} failed: {e}")
                    self._append_log(account_id, f"⚠️ Connection attempt {attempt} failed: {str(e)[:60]}")
                    if attempt < max_retries:
                        await asyncio.sleep(min(5 * attempt, 30))
                        timeout = min(timeout * 2, 300)

            if not connected_ok:
                logger.warning("Account wait_connected timed out or failed after retries")
                self._append_log(account_id, "❌ Connection failed after all retries")
                state.is_connected = False
                return {"connected": False, "status": "connecting", "account_id": account_id}

            # Create streaming connection
            self._append_log(account_id, "⏳ Creating streaming connection...")
            connection = account.get_streaming_connection()

            # Connect streaming with retries
            stream_ok = False
            timeout = base_timeout
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        self._append_log(account_id, f"🔄 Stream connect attempt {attempt}/{max_retries}...")
                    logger.info(f"Connecting streaming attempt {attempt}/{max_retries} timeout={timeout}s")
                    await asyncio.wait_for(connection.connect(), timeout=timeout)
                    stream_ok = True
                    self._append_log(account_id, "✓ Streaming connected")
                    break
                except Exception as e:
                    logger.warning(f"Streaming connect attempt {attempt} failed: {e}")
                    self._append_log(account_id, f"⚠️ Stream connect attempt {attempt} failed: {str(e)[:60]}")
                    if attempt < max_retries:
                        await asyncio.sleep(min(5 * attempt, 30))
                        timeout = min(timeout * 2, 300)

            if not stream_ok:
                logger.warning("Streaming connect failed after retries")
                self._append_log(account_id, "❌ Streaming connection failed after all retries")
                state.is_connected = False
                return {"connected": False, "status": "connecting", "account_id": account_id}

            # Wait for synchronization with retries
            self._append_log(account_id, "⏳ Synchronizing terminal state...")
            sync_ok = False
            timeout = base_timeout
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        self._append_log(account_id, f"🔄 Sync attempt {attempt}/{max_retries}...")
                    logger.info(f"Waiting for synchronization attempt {attempt}/{max_retries} timeout={timeout}s")
                    await asyncio.wait_for(connection.wait_synchronized(), timeout=timeout)
                    sync_ok = True
                    self._append_log(account_id, "✓ Terminal state synchronized")
                    break
                except Exception as e:
                    logger.warning(f"Synchronization attempt {attempt} failed: {e}")
                    self._append_log(account_id, f"⚠️ Sync attempt {attempt} failed: {str(e)[:60]}")
                    if attempt < max_retries:
                        await asyncio.sleep(min(5 * attempt, 30))
                        timeout = min(timeout * 2, 300)

            if not sync_ok:
                logger.warning("Streaming synchronization failed after retries")
                self._append_log(account_id, "❌ Synchronization failed after all retries")
                state.is_connected = False
                return {"connected": False, "status": "connecting", "account_id": account_id}

            state.connection = connection
            state.is_connected = True
            state.reconnect_attempts = 0

            # record connection in logs with more details
            self._append_log(account_id, "✅ CONNECTED to MetaAPI")
            
            # Get account info (balance, equity, etc.) early for logging
            try:
                terminal_state = connection.terminal_state
                if terminal_state:
                    balance = getattr(terminal_state, 'balance', None)
                    equity = getattr(terminal_state, 'equity', None)
                    if balance is not None:
                        self._append_log(account_id, f"💰 Account Balance: ${balance:.2f}")
                    if equity is not None and equity != balance:
                        self._append_log(account_id, f"📈 Current Equity: ${equity:.2f}")
            except Exception as e:
                logger.debug(f"Could not fetch initial account balance: {e}")

            # Start listening for trade events
            state.listener_task = asyncio.create_task(
                self._listen_for_events(user_id, connection, account_id)
            )

            logger.info(f"Connected to MetaAPI for user {user_id}, account {account_id}")

            # Get account info (balance, equity, etc.)
            account_info = {}
            try:
                terminal_state = connection.terminal_state
                if terminal_state:
                    account_info = {
                        "connected": True,
                        "account_id": account_id,
                        "status": "connected",
                        "broker": getattr(account, 'broker', 'Unknown'),
                        "server": getattr(account, 'server', 'Unknown'),
                        "balance": getattr(terminal_state, 'balance', None),
                        "equity": getattr(terminal_state, 'equity', None),
                        "currency": getattr(terminal_state, 'currency', 'USD'),
                    }
            except Exception as e:
                logger.debug(f"Could not retrieve account info: {e}")
                account_info = {
                    "connected": True,
                    "account_id": account_id,
                    "status": "connected",
                    "broker": getattr(account, 'broker', 'Unknown'),
                    "server": getattr(account, 'server', 'Unknown'),
                }

            await self._touch_heartbeat(user_id, account_id)

            return account_info

        except Exception as e:
            logger.error(f"MetaAPI connection failed for user {user_id}: {e}")
            state.is_connected = False
            return {"connected": False, "error": str(e), "account_id": account_id}

    async def disconnect(self, user: User, account_id: Optional[str] = None) -> dict:
        """Disconnect a user's MetaAPI connection.

        Args:
            user: User model.

        Returns:
            Dict with disconnection status.
        """
        user_id = str(user.id)
        if account_id is None:
            account_id = user.metaapi_account_id
        conn_key = f"{user_id}:{account_id}"
        state = self._connections.get(conn_key)

        if not state:
            return {"disconnected": True, "status": "was_not_connected"}

        # Log disconnection start
        if account_id:
            self._append_log(account_id, "🔌 Disconnecting...")

        try:
            if state.listener_task and not state.listener_task.done():
                state.listener_task.cancel()
                try:
                    await state.listener_task
                except asyncio.CancelledError:
                    pass

            if state.connection:
                try:
                    await state.connection.close()
                    if account_id:
                        self._append_log(account_id, "✓ Streaming connection closed")
                except Exception:
                    logger.debug("Error closing streaming connection")

            # Respect setting to avoid undeploy on user-initiated disconnects.
            settings = get_settings()
            if state.account and getattr(settings, "METAAPI_UNDEPLOY_ON_DISCONNECT", False):
                try:
                    await state.account.undeploy()
                    if account_id:
                        self._append_log(account_id, "✓ Account undeployed")
                except Exception as e:
                    logger.debug(f"Failed to undeploy account {account_id}: {e}")

        except Exception as e:
            logger.error(f"Error disconnecting MetaAPI for user {user_id}: {e}")
            if account_id:
                self._append_log(account_id, f"⚠️ Disconnect error: {str(e)[:80]}")

        state.is_connected = False
        if conn_key in self._connections:
            del self._connections[conn_key]
        
        if account_id:
            self._append_log(account_id, "❌ DISCONNECTED from MetaAPI")

        return {"disconnected": True, "status": "disconnected"}

    async def get_status(self, user: User, account_id: Optional[str] = None) -> dict:
        """Get the connection status for a user (optionally filtered by account).

        Args:
            user: User model.
            account_id: Specific MetaAPI account ID to query.  If omitted, the
                first connection state belonging to the user is returned.

        Returns:
            Dict with connection status details.  Keys mirror those returned by
            :meth:`connect`.
        """
        user_id = str(user.id)
        state = None
        if account_id:
            conn_key = f"{user_id}:{account_id}"
            state = self._connections.get(conn_key)
        else:
            # pick any state for this user
            for key, st in self._connections.items():
                if key.startswith(f"{user_id}:"):
                    state = st
                    break

        if not state:
            return {
                "connected": False,
                "account_id": account_id or user.metaapi_account_id,
                "status": "not_connected",
            }

        return {
            "connected": state.is_connected,
            "account_id": state.account_id,
            "status": "connected" if state.is_connected else "disconnected",
            "reconnect_attempts": state.reconnect_attempts,
        }

    async def _listen_for_events(self, user_id: str, connection: Any, account_id: str) -> None:
        """Listen for trade events from MetaAPI streaming connection.

        Runs as a background task. Handles order opened, updated, and closed events.

        Args:
            user_id: User UUID string.
            connection: MetaAPI streaming connection.
            account_id: MetaAPI account ID for logging.
        """
        try:
            # The MetaAPI SDK uses synchronization listeners
            # We poll for position changes as a robust fallback
            known_positions: Dict[str, dict] = {}
            has_logged_initialized = False
            heartbeat_counter = 0
            heartbeat_interval = 30  # Log heartbeat every 30 seconds
            reconcile_counter = 0
            reconcile_interval = 3  # Reconcile DB open trades every 3 seconds

            while True:
                try:
                    terminal_state = connection.terminal_state
                    if not terminal_state:
                        logger.debug(f"No terminal state for account {account_id}, waiting...")
                        await asyncio.sleep(1)
                        heartbeat_counter += 1
                        continue

                    current_positions = {
                        p.get("id", ""): p
                        for p in (terminal_state.positions or [])
                    }

                    # Log initial state once
                    if not has_logged_initialized:
                        self._append_log(account_id, f"📊 Position listener initialized, {len(current_positions)} current positions")
                        if current_positions:
                            for pos_id, pos in current_positions.items():
                                self._append_log(account_id, f"  - {pos.get('symbol')} vol={pos.get('volume')} id={pos_id}")
                        # Run an immediate reconciliation once terminal state is available.
                        try:
                            closed_count = await self._reconcile_open_trades_with_terminal(
                                user_id, account_id, current_positions
                            )
                            if closed_count > 0:
                                self._append_log(
                                    account_id,
                                    f"🔁 Reconciled {closed_count} stale open trade(s) from DB",
                                )
                        except Exception as reconcile_err:
                            logger.debug(
                                f"Initial reconciliation error for user {user_id}, account {account_id}: {reconcile_err}"
                            )
                        has_logged_initialized = True
                    
                    # Periodic heartbeat to show connection is alive
                    heartbeat_counter += 1
                    if heartbeat_counter >= heartbeat_interval:
                        pos_count = len(current_positions)
                        equity = getattr(terminal_state, 'equity', None)
                        balance = getattr(terminal_state, 'balance', None)
                        status_parts = [f"{pos_count} position(s)"]
                        if balance is not None:
                            status_parts.append(f"balance=${balance:.2f}")
                        if equity is not None and equity != balance:
                            status_parts.append(f"equity=${equity:.2f}")
                        self._append_log(account_id, f"💓 Heartbeat: {', '.join(status_parts)}")
                        await self._touch_heartbeat(user_id, account_id)
                        heartbeat_counter = 0

                    # Periodic reconciliation: close stale DB-open trades missing from broker positions
                    reconcile_counter += 1
                    if reconcile_counter >= reconcile_interval:
                        try:
                            closed_count = await self._reconcile_open_trades_with_terminal(
                                user_id, account_id, current_positions
                            )
                            if closed_count > 0:
                                self._append_log(
                                    account_id,
                                    f"🔁 Reconciled {closed_count} stale open trade(s) from DB",
                                )
                        except Exception as reconcile_err:
                            logger.debug(
                                f"Reconciliation error for user {user_id}, account {account_id}: {reconcile_err}"
                            )
                        finally:
                            reconcile_counter = 0

                    # Detect new positions (opened)
                    _acct_balance = getattr(terminal_state, 'balance', None) or 10000.0
                    for pos_id, pos in current_positions.items():
                        if pos_id not in known_positions:
                            symbol = pos.get('symbol', 'UNKNOWN')
                            volume = pos.get('volume', 0)
                            price = pos.get('openPrice', 0)
                            log_msg = f"📈 NEW TRADE OPENED: {symbol} vol={volume} @ {price}"
                            logger.info(f"[{account_id}] {log_msg}")
                            self._append_log(account_id, log_msg)
                            await self._on_trade_opened(user_id, pos, account_id, account_balance=_acct_balance)

                    # Detect closed positions
                    for pos_id, pos in known_positions.items():
                        if pos_id not in current_positions:
                            symbol = pos.get('symbol', 'UNKNOWN')
                            close_price = pos.get('closePrice') or pos.get('currentPrice', 0)
                            log_msg = f"📉 TRADE CLOSED: {symbol} @ {close_price}"
                            logger.info(f"[{account_id}] {log_msg}")
                            self._append_log(account_id, log_msg)
                            await self._on_trade_closed(user_id, pos, account_id)

                    # Detect updated positions (SL/TP changes)
                    for pos_id, pos in current_positions.items():
                        if pos_id in known_positions:
                            old = known_positions[pos_id]
                            sl_changed = pos.get("stopLoss") != old.get("stopLoss")
                            tp_changed = pos.get("takeProfit") != old.get("takeProfit")
                            if sl_changed or tp_changed:
                                symbol = pos.get('symbol', 'UNKNOWN')
                                changes = []
                                if sl_changed:
                                    changes.append(f"SL: {old.get('stopLoss')}→{pos.get('stopLoss')}")
                                if tp_changed:
                                    changes.append(f"TP: {old.get('takeProfit')}→{pos.get('takeProfit')}")
                                log_msg = f"🔧 TRADE UPDATED: {symbol} ({', '.join(changes)})"
                                logger.info(f"[{account_id}] {log_msg}")
                                self._append_log(account_id, log_msg)
                                await self._on_trade_updated(user_id, pos, account_id)

                    known_positions = current_positions

                except Exception as e:
                    logger.error(f"Error in event listener for user {user_id}: {e}", exc_info=True)
                    self._append_log(account_id, f"EVENT LISTENER ERROR: {str(e)[:100]}")

                await asyncio.sleep(1)  # Poll every second

        except asyncio.CancelledError:
            logger.info(f"Event listener cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Event listener crashed for user {user_id}: {e}")
            # log crash
            # figure out account id from state if available
            state = self._connections.get(f"{user_id}:" + (getattr(connection, 'account_id', '') or ''))
            if state and state.account_id:
                self._append_log(state.account_id, f"EVENT LISTENER CRASH: {e}")
            # Attempt reconnection
            await self._handle_reconnection(user_id, account_id)

    async def _on_trade_opened(self, user_id: str, position: dict, account_id: str = "", account_balance: float = 10000.0) -> None:
        """Handle a new trade being opened."""
        if not account_id:
            account_id = position.get("accountId") or ""
        if account_id:
            self._append_log(account_id, f"TRADE_OPENED {position.get('symbol')} id={position.get('id')}")
        trade_data = {
            "external_id": position.get("id", ""),
            "symbol": position.get("symbol", ""),
            "type": "BUY" if position.get("type") == "POSITION_TYPE_BUY" else "SELL",
            "entry_price": position.get("openPrice", 0),
            "sl": position.get("stopLoss"),
            "tp": position.get("takeProfit"),
            "lot_size": position.get("volume", 0),
            "account_balance": account_balance,
        }
        await trade_processor.process_trade_opened(user_id, trade_data)

    async def _reconcile_open_trades_with_terminal(
        self,
        user_id: str,
        account_id: str,
        current_positions: Dict[str, dict],
    ) -> int:
        """Close DB OPEN trades that are no longer present in broker terminal positions.

        This heals missed close events (e.g., during temporary disconnects/restarts)
        so UI does not keep showing trades as OPEN after they are closed at broker.
        """
        current_external_ids = {str(pos_id) for pos_id in current_positions.keys() if pos_id}

        async with async_session_factory() as db:
            result = await db.execute(
                select(Trade).where(
                    and_(
                        Trade.user_id == uuid.UUID(user_id),
                        Trade.status == TradeStatus.OPEN,
                    )
                )
            )
            open_trades = result.scalars().all()

        stale_external_ids = []
        for trade in open_trades:
            ext_id = (trade.external_trade_id or "").strip()
            if ext_id and ext_id not in current_external_ids:
                stale_external_ids.append(ext_id)

        closed_count = 0
        for ext_id in stale_external_ids:
            try:
                # Try to get the close price from history_storage for this position
                close_price = None
                try:
                    conn_key = f"{user_id}:{account_id}"
                    state = self._connections.get(conn_key)
                    if state and state.connection:
                        hs = getattr(state.connection, "history_storage", None)
                        if hs is not None:
                            close_entry_types = {"DEAL_ENTRY_OUT", "DEAL_ENTRY_INOUT", "DEAL_ENTRY_OUT_BY"}
                            close_deals = [
                                d for d in (hs.get_deals_by_position(ext_id) or [])
                                if d.get("entryType") in close_entry_types and d.get("price") is not None
                            ]
                            if close_deals:
                                latest = max(close_deals, key=lambda d: d.get("time") or 0)
                                close_price = float(latest["price"])
                except Exception:
                    pass

                trade_data: dict = {"external_id": ext_id}
                if close_price is not None:
                    trade_data["exit_price"] = close_price

                await trade_processor.process_trade_closed(user_id, trade_data)
                closed_count += 1
            except Exception as close_err:
                logger.debug(
                    f"Failed reconciling stale trade {ext_id} for user {user_id}: {close_err}"
                )

        return closed_count

    async def _on_trade_closed(self, user_id: str, position: dict, account_id: str = "") -> None:
        """Handle a trade being closed."""
        if not account_id:
            account_id = position.get("accountId") or ""
        if account_id:
            self._append_log(account_id, f"TRADE_CLOSED {position.get('symbol')} id={position.get('id')}")
        # MetaAPI provides profit in account currency — use it directly when available.
        # Use explicit None-checks instead of `or` so that a legitimate profit of 0.0
        # is not falsely treated as missing and replaced by a wrong fallback value.
        broker_profit = position.get("profit")
        if broker_profit is None:
            broker_profit = position.get("currentProfit")
        if broker_profit is None:
            broker_profit = position.get("unrealizedProfit")

        # Include commission and swap so stored pnl is the real net P&L the trader sees.
        # MetaAPI stores commission/swap as negative numbers (costs), so we add them.
        # Note: this snapshot-based value is only used when history_storage has no
        # closing deal — see the deal-based override further below.
        if broker_profit is not None:
            # For a fully-closed position, `unrealizedCommission` / `unrealizedSwap` are
            # 0 because everything has been realized — using them would silently drop the
            # commission/swap cost entirely.  Prefer the total `commission`/`swap` fields
            # and fall back to the unrealized sub-fields only when the totals are absent.
            commission = (
                position.get("commission")
                if position.get("commission") is not None
                else position.get("unrealizedCommission") or 0.0
            )
            swap = (
                position.get("swap")
                if position.get("swap") is not None
                else position.get("unrealizedSwap") or 0.0
            )
            net_pnl = float(broker_profit) + float(commission) + float(swap)
            self._append_log(
                account_id,
                f"  profit={broker_profit} commission={commission} swap={swap} net={net_pnl:.4f} (snapshot fallback)",
            )
        else:
            net_pnl = None

        # --- Determine the actual close price AND authoritative P&L ---
        # The position snapshot we have is from the last time it appeared in
        # terminal_state.positions (i.e. while it was still OPEN).  Therefore
        # `closePrice` is absent and `currentPrice` / `profit` may reflect the
        # floating value at the last polling cycle — NOT the actual close values.
        # Example: floating P&L was $3 when last polled, real exit P&L is $35.
        #
        # The AUTHORITATIVE source is history_storage: MetaAPI fires on_deal_added
        # before removing the position from positions, so the closing deal
        # (entryType DEAL_ENTRY_OUT / DEAL_ENTRY_INOUT) should already be
        # present by the time we get here.  We read price, profit, commission,
        # and swap from the deal rather than the stale position snapshot.
        exit_price = None
        position_id = str(position.get("id", ""))
        try:
            conn_key = f"{user_id}:{account_id}"
            state = self._connections.get(conn_key)
            if state and state.connection:
                hs = getattr(state.connection, "history_storage", None)
                if hs is not None:
                    close_entry_types = {"DEAL_ENTRY_OUT", "DEAL_ENTRY_INOUT", "DEAL_ENTRY_OUT_BY"}
                    close_deals = [
                        d for d in (hs.get_deals_by_position(position_id) or [])
                        if d.get("entryType") in close_entry_types and d.get("price") is not None
                    ]
                    if close_deals:
                        # Take the most recent closing deal
                        latest = max(close_deals, key=lambda d: d.get("time") or 0)
                        exit_price = float(latest["price"])
                        self._append_log(
                            account_id,
                            f"  close_price from history deal: {exit_price}",
                        )

                        # Override net_pnl with the deal's authoritative profit/commission/swap
                        # fields so we are never relying on the stale floating P&L from the
                        # position snapshot (which may differ significantly from the final P&L).
                        deal_profit = latest.get("profit")
                        if deal_profit is not None:
                            deal_commission = latest.get("commission") or 0.0
                            deal_swap = latest.get("swap") or 0.0
                            net_pnl = float(deal_profit) + float(deal_commission) + float(deal_swap)
                            self._append_log(
                                account_id,
                                f"  pnl from history deal: profit={deal_profit} "
                                f"commission={deal_commission} swap={deal_swap} net={net_pnl:.4f}",
                            )
        except Exception as _hs_err:
            logger.debug(f"history_storage close-price lookup failed for pos {position_id}: {_hs_err}")

        # Fall back to the position snapshot price fields when history is unavailable
        if not exit_price:
            exit_price = position.get("closePrice") or position.get("currentPrice") or position.get("openPrice", 0)
            self._append_log(account_id, f"  close_price fallback (snapshot): {exit_price}")

        trade_data = {
            "external_id": position.get("id", ""),
            "exit_price": exit_price,
            "pnl": net_pnl,
        }
        await trade_processor.process_trade_closed(user_id, trade_data)

    async def _on_trade_updated(self, user_id: str, position: dict, account_id: str = "") -> None:
        """Handle a trade being modified (SL/TP update).

        Args:
            user_id: User UUID string.
            position: Updated MetaAPI position data dict.
            account_id: MetaAPI account ID for logging.
        """
        logger.info(f"Trade updated for user {user_id}: {position.get('symbol')}")
        if not account_id:
            account_id = position.get("accountId") or ""
        if account_id:
            self._append_log(account_id, f"TRADE_UPDATED {position.get('symbol')} id={position.get('id')}")

        # Delegate update handling (DB update, WS broadcast, notifications)
        trade_data = {
            "external_id": position.get("id", ""),
            "sl": position.get("stopLoss"),
            "tp": position.get("takeProfit"),
        }
        try:
            await trade_processor.process_trade_updated(user_id, trade_data)
        except Exception as e:
            logger.error(f"Error delegating trade update for user {user_id}: {e}")

    async def _handle_reconnection(self, user_id: str, account_id: str) -> None:
        """Handle reconnection after a connection failure.

        Args:
            user_id: User UUID string.
        """
        conn_key = f"{user_id}:{account_id}"
        state = self._connections.get(conn_key)
        if not state:
            return

        state.reconnect_attempts += 1
        if state.account_id:
            self._append_log(state.account_id, f"🔄 RECONNECT ATTEMPT {state.reconnect_attempts}/{state.max_reconnect_attempts}")
        
        if state.reconnect_attempts > state.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts reached for user {user_id}")
            if state.account_id:
                self._append_log(state.account_id, f"❌ Max reconnection attempts ({state.max_reconnect_attempts}) reached - giving up")
            state.is_connected = False
            return

        delay = min(30, 2 ** state.reconnect_attempts)
        logger.info(f"Reconnecting user {user_id} in {delay}s (attempt {state.reconnect_attempts})")
        if state.account_id:
            self._append_log(state.account_id, f"⏳ Waiting {delay}s before reconnection...")
        await asyncio.sleep(delay)

        async with async_session_factory() as db:
            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user = result.scalar_one_or_none()
            if user:
                if state.account_id:
                    self._append_log(state.account_id, "🔄 Attempting to reconnect...")
                await self.connect(user, account_id=account_id)

    async def simulate_trade_open(self, user_id: str, trade_data: dict) -> Trade:
        """Simulate a trade opening for testing."""
        return await trade_processor.process_trade_opened(user_id, trade_data)

    async def simulate_trade_close(self, user_id: str, trade_id: str, exit_price: float) -> Optional[Trade]:
        """Simulate closing a trade for testing."""
        # Note: trade_processor expects external_id in trade_data
        # We need to find the external_id associated with this internal trade_id
        async with async_session_factory() as db:
            result = await db.execute(select(Trade).where(Trade.id == uuid.UUID(trade_id)))
            trade = result.scalar_one_or_none()
            if not trade:
                return None
            ext_id = trade.external_trade_id
            
        return await trade_processor.process_trade_closed(user_id, {
            "external_id": ext_id,
            "exit_price": exit_price
        })

    async def fetch_trade_history(self, user_id: str, account_id: str, lookback_days: int = 180) -> dict:
        """Fetch trade history from MetaAPI and store closed trades in DB.
        
        Args:
            user_id: User UUID
            account_id: MetaAPI account ID
            lookback_days: Number of days to fetch history for (default 180)
            
        Returns:
            Dict with summary of fetched trades and any errors
        """
        api = await self._get_api()
        if api is None:
            logger.info(f"MetaAPI unavailable; skipping history fetch for account {account_id}")
            return {"fetched": 0, "skipped": True, "reason": "MetaAPI unavailable"}
        
        try:
            account = await api.metatrader_account_api.get_account(account_id)
            if not account:
                return {"fetched": 0, "error": "Account not found"}
            
            conn = account.get_streaming_connection()
            if not conn or not await conn.is_connected():
                logger.warning(f"Account {account_id} not connected; cannot fetch history yet")
                return {"fetched": 0, "error": "Account not yet connected"}
            
            # Fetch closed deals/history orders from MetaAPI
            # Use getHistoryOrders to get closed trades
            from_date = datetime.now(timezone.utc).timestamp() - (lookback_days * 86400)
            to_date = datetime.now(timezone.utc).timestamp()
            
            logger.info(f"Fetching trade history for account {account_id} from last {lookback_days} days")
            
            try:
                # getHistoryOrders returns closed orders/deals
                history = await asyncio.wait_for(
                    conn.terminal_state.history,
                    timeout=30
                )
                
                if not history:
                    logger.info(f"No history available for account {account_id}")
                    return {"fetched": 0, "status": "no_history"}
                
                # Process history trades through trade processor
                async with async_session_factory() as db:
                    fetched_count = 0
                    skipped_count = 0
                    
                    for deal in history:
                        try:
                            # Check if this deal already exists in DB
                            ext_id = str(deal.get("id", ""))
                            if not ext_id:
                                continue
                            
                            result = await db.execute(
                                select(Trade).where(
                                    and_(
                                        Trade.user_id == uuid.UUID(user_id),
                                        Trade.external_trade_id == ext_id,
                                    )
                                )
                            )
                            existing = result.scalar_one_or_none()
                            
                            if existing:
                                skipped_count += 1
                                continue
                            
                            # Only process closed trades
                            deal_type = deal.get("type", "").upper()
                            if deal_type not in ("BUY", "SELL"):
                                continue
                            
                            # Convert deal to uniform trade format
                            trade_data = {
                                "external_id": ext_id,
                                "symbol": deal.get("symbol", "").upper(),
                                "type": deal_type,
                                "entry_price": float(deal.get("entryPrice", 0)),
                                "exit_price": float(deal.get("dealPrice", deal.get("entryPrice", 0))),
                                "lot_size": float(deal.get("volume", 0)),
                                "open_time": datetime.fromtimestamp(
                                    deal.get("openTime", 0) / 1000, 
                                    tz=timezone.utc
                                ),
                                "close_time": datetime.fromtimestamp(
                                    deal.get("closeTime", deal.get("openTime", 0)) / 1000,
                                    tz=timezone.utc
                                ),
                                "pnl": float(deal.get("profit", 0)),
                                "is_history": True,  # Mark as historical
                            }
                            
                            # Process as closed trade
                            await trade_processor.process_trade_closed(user_id, trade_data)
                            fetched_count += 1
                            
                        except Exception as e:
                            logger.warning(f"Error processing history deal: {e}")
                            skipped_count += 1
                            continue
                    
                    self._append_log(account_id, f"✓ Fetched {fetched_count} trade(s) from history")
                    logger.info(f"Fetched {fetched_count} historical trades for account {account_id}")
                    
                    return {
                        "fetched": fetched_count,
                        "skipped": skipped_count,
                        "status": "success"
                    }
                    
            except asyncio.TimeoutError:
                logger.warning(f"History fetch timeout for account {account_id}")
                return {"fetched": 0, "error": "Fetch timeout"}
            except Exception as e:
                logger.error(f"Error fetching trade history: {e}")
                return {"fetched": 0, "error": str(e)}
                
        except Exception as e:
            logger.error(f"Error in fetch_trade_history: {e}")
            return {"fetched": 0, "error": str(e)}


# Global singleton
metaapi_service = MetaApiService()
