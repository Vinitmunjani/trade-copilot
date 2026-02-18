"""MetaAPI account provisioning service.

Handles creating MetaAPI cloud accounts from MT4/MT5 broker credentials
using the MetaAPI REST API directly.
"""

import asyncio
import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# MetaAPI REST API endpoints
METAAPI_PROVISIONING_BASE = "https://mt-provisioning-api-v1.agiliumtrade.agiliumtrade.ai"


class MetaApiProvisioningError(Exception):
    """Raised when MetaAPI provisioning fails."""

    def __init__(self, message: str, status_code: int | None = None, details: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class MetaApiProvisioning:
    """Provisions MetaAPI cloud accounts from MT4/MT5 broker credentials."""

    def __init__(self):
        self._token = settings.METAAPI_TOKEN

    def _get_headers(self) -> dict:
        """Get authorization headers for MetaAPI REST API."""
        return {
            "auth-token": self._token,
            "Content-Type": "application/json",
        }

    async def create_account(
        self,
        login: str,
        password: str,
        server: str,
        platform: str = "mt5",
    ) -> str:
        """Create a MetaAPI cloud account from MT broker credentials.

        This creates a read-only cloud account that connects to the user's
        MT4/MT5 broker account for live trade data streaming.

        Args:
            login: MT4/MT5 account number.
            password: MT4/MT5 account password.
            server: Broker server name (e.g. "ICMarketsSC-Demo").
            platform: Trading platform - "mt4" or "mt5".

        Returns:
            The MetaAPI account ID string.

        Raises:
            MetaApiProvisioningError: If account creation fails.
        """
        if not self._token:
            raise MetaApiProvisioningError(
                "METAAPI_TOKEN not configured. Please set it in environment variables."
            )

        # Validate platform
        platform = platform.lower()
        if platform not in ("mt4", "mt5"):
            raise MetaApiProvisioningError(f"Invalid platform: {platform}. Must be 'mt4' or 'mt5'.")

        # Check if an account with this login+server already exists
        existing_id = await self._find_existing_account(login, server, platform)
        if existing_id:
            logger.info(f"Found existing MetaAPI account {existing_id} for login {login}@{server}")
            # Update password on existing account (in case it changed)
            await self._update_account_password(existing_id, password)
            return existing_id

        # Create new account
        account_payload = {
            "name": f"Trade Co-Pilot - {login}",
            "type": "cloud-g2",
            "login": login,
            "password": password,
            "server": server,
            "platform": platform,
            "magic": 0,
            "quoteStreamingIntervalInSeconds": 2.5,
            "reliability": "regular",
            "resourceSlots": 1,
            "copyFactoryRoles": [],
            "manualTrades": False,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{METAAPI_PROVISIONING_BASE}/users/current/accounts",
                    json=account_payload,
                    headers=self._get_headers(),
                )

                if response.status_code == 201:
                    data = response.json()
                    account_id = data.get("id")
                    logger.info(f"Created MetaAPI account {account_id} for login {login}@{server}")
                    return account_id

                elif response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get("message", "Bad request")
                    raise MetaApiProvisioningError(
                        f"Invalid account details: {error_msg}",
                        status_code=400,
                        details=error_data,
                    )

                elif response.status_code == 401:
                    raise MetaApiProvisioningError(
                        "MetaAPI authentication failed. Check METAAPI_TOKEN.",
                        status_code=401,
                    )

                elif response.status_code == 429:
                    raise MetaApiProvisioningError(
                        "MetaAPI rate limit exceeded. Please try again later.",
                        status_code=429,
                    )

                else:
                    error_text = response.text
                    raise MetaApiProvisioningError(
                        f"MetaAPI returned status {response.status_code}: {error_text}",
                        status_code=response.status_code,
                    )

            except httpx.RequestError as e:
                raise MetaApiProvisioningError(
                    f"Network error connecting to MetaAPI: {str(e)}"
                )

    async def _find_existing_account(
        self, login: str, server: str, platform: str
    ) -> Optional[str]:
        """Check if a MetaAPI account already exists for this login+server.

        Args:
            login: MT account number.
            server: Broker server name.
            platform: mt4 or mt5.

        Returns:
            Account ID if found, None otherwise.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(
                    f"{METAAPI_PROVISIONING_BASE}/users/current/accounts",
                    headers=self._get_headers(),
                )

                if response.status_code == 200:
                    accounts = response.json()
                    for account in accounts:
                        if (
                            str(account.get("login")) == str(login)
                            and account.get("server") == server
                            and account.get("platform") == platform
                        ):
                            return account.get("id")

            except Exception as e:
                logger.warning(f"Failed to check existing accounts: {e}")

        return None

    async def _update_account_password(self, account_id: str, password: str) -> None:
        """Update the password on an existing MetaAPI account.

        Args:
            account_id: MetaAPI account ID.
            password: New MT4/MT5 password.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.put(
                    f"{METAAPI_PROVISIONING_BASE}/users/current/accounts/{account_id}",
                    json={"password": password},
                    headers=self._get_headers(),
                )
                if response.status_code in (200, 204):
                    logger.info(f"Updated password for MetaAPI account {account_id}")
                else:
                    logger.warning(
                        f"Failed to update password for account {account_id}: "
                        f"status {response.status_code}"
                    )
            except Exception as e:
                logger.warning(f"Failed to update account password: {e}")

    async def wait_for_deployment(self, account_id: str, timeout: int = 120) -> bool:
        """Wait for a MetaAPI account to be deployed and connected.

        Polls the account status until it reaches DEPLOYED state or times out.

        Args:
            account_id: MetaAPI account ID.
            timeout: Max seconds to wait.

        Returns:
            True if deployed successfully, False if timed out.
        """
        elapsed = 0
        poll_interval = 3

        async with httpx.AsyncClient(timeout=15.0) as client:
            while elapsed < timeout:
                try:
                    response = await client.get(
                        f"{METAAPI_PROVISIONING_BASE}/users/current/accounts/{account_id}",
                        headers=self._get_headers(),
                    )

                    if response.status_code == 200:
                        data = response.json()
                        state = data.get("state", "")
                        connection_status = data.get("connectionStatus", "")

                        logger.debug(
                            f"Account {account_id} state={state}, "
                            f"connectionStatus={connection_status}"
                        )

                        if state == "DEPLOYED":
                            return True

                        if state == "DEPLOY_FAILED":
                            raise MetaApiProvisioningError(
                                "Account deployment failed. Check your credentials and server name.",
                                details=data,
                            )

                except MetaApiProvisioningError:
                    raise
                except Exception as e:
                    logger.warning(f"Error polling account status: {e}")

                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

        return False

    async def delete_account(self, account_id: str) -> bool:
        """Delete a MetaAPI account.

        Args:
            account_id: MetaAPI account ID.

        Returns:
            True if deleted successfully.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.delete(
                    f"{METAAPI_PROVISIONING_BASE}/users/current/accounts/{account_id}",
                    headers=self._get_headers(),
                )
                return response.status_code in (200, 204, 404)
            except Exception as e:
                logger.error(f"Failed to delete MetaAPI account {account_id}: {e}")
                return False


# Global singleton
metaapi_provisioning = MetaApiProvisioning()
