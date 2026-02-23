"""MT5 Terminal Connection Manager - validates and simulates MT5 accounts."""
import subprocess
import json
from typing import Optional, Dict, Any
from datetime import datetime

class MT5Connector:
    """Manages MT5 terminal initialization and login."""
    
    # Map brokers to MT5 container ports
    BROKER_PORTS = {
        "ICMarkets": 5001,
        "Exness": 5002,
        "XM": 5003,
        "ic_markets": 5001,
        "exness": 5002,
        "xm": 5003,
    }
    
    # Mock account data per broker (for MVP - real integration comes later)
    MOCK_ACCOUNTS = {
        "Exness": {
            "279495999": {
                "balance": 10000.00,
                "equity": 9950.25,
                "currency": "USD",
                "leverage": 500,
                "account_name": "Exness Trading Account",
                "company": "Exness",
                "margin_used": 49.75,
                "margin_free": 9900.25,
            }
        },
        "ICMarkets": {
            "123456789": {
                "balance": 5000.00,
                "equity": 4925.50,
                "currency": "USD",
                "leverage": 200,
                "account_name": "ICMarkets Demo",
                "company": "IC Markets",
                "margin_used": 74.50,
                "margin_free": 4850.50,
            }
        },
        "XM": {
            "987654321": {
                "balance": 8000.00,
                "equity": 7950.00,
                "currency": "USD",
                "leverage": 888,
                "account_name": "XM Trading Account",
                "company": "XM",
                "margin_used": 50.00,
                "margin_free": 7900.00,
            }
        }
    }
    
    @staticmethod
    def get_port_for_broker(broker: str) -> int:
        """Get MT5 container port for broker."""
        return MT5Connector.BROKER_PORTS.get(broker.lower(), 5001)
    
    @staticmethod
    def check_container_health(port: int, timeout: int = 5) -> bool:
        """Check if MT5 container is running and healthy."""
        try:
            import urllib.request
            url = f"http://localhost:{port}/health"
            response = urllib.request.urlopen(url, timeout=timeout)
            return response.status == 200
        except:
            return False
    
    @staticmethod
    def validate_credentials(broker: str, login: str, password: str) -> tuple[bool, str]:
        """
        Validate MT5 credentials.
        Returns (is_valid, message)
        """
        # Basic validation
        if not login or not password:
            return False, "Login and password are required"
        
        if not login.isdigit() or len(login) < 6:
            return False, "Invalid login format (must be numeric, 6+ digits)"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        # For MVP: mock validation - accept if broker exists
        if broker not in MT5Connector.BROKER_PORTS:
            return False, f"Broker '{broker}' not supported. Use: Exness, ICMarkets, or XM"
        
        # NOTE: Real MT5 validation would query the container here
        # For now, we accept valid formats and return mock data
        return True, "Credentials valid (mock)"
    
    @staticmethod
    def connect_account(broker: str, login: str, password: str, server: str = "Demo") -> Dict[str, Any]:
        """
        Connect to MT5 account.
        
        For MVP: Returns mock data. Real MT5 containers don't implement login yet.
        
        Returns:
            {
                "status": "connected|failed",
                "broker": "Exness",
                "login": "279495999",
                "server": "Exness-MT5Trial8",
                "account_info": {
                    "balance": 10000.0,
                    "equity": 9950.25,
                    "currency": "USD",
                    "leverage": 500,
                    "account_name": "Exness Account",
                    "company": "Exness",
                }
                "error": "reason"  # if failed
            }
        """
        # Validate credentials
        is_valid, message = MT5Connector.validate_credentials(broker, login, password)
        
        if not is_valid:
            return {
                "status": "failed",
                "broker": broker,
                "login": login,
                "server": server,
                "error": message
            }
        
        port = MT5Connector.get_port_for_broker(broker)
        
        # Check if container is running (even though it doesn't validate login)
        if not MT5Connector.check_container_health(port):
            return {
                "status": "failed",
                "broker": broker,
                "login": login,
                "server": server,
                "error": f"MT5 container for {broker} not available on port {port}"
            }
        
        # For MVP: Return mock account data (real MT5 integration comes in Phase 2)
        # Use the login number to look up mock data if available, otherwise generate
        mock_data = MT5Connector.MOCK_ACCOUNTS.get(broker, {}).get(login, {
            "balance": 10000.0,
            "equity": 9950.25,
            "currency": "USD",
            "leverage": 500,
            "account_name": f"{broker} Account ({login})",
            "company": broker,
            "margin_used": 49.75,
            "margin_free": 9900.25,
        })
        
        return {
            "status": "connected",
            "broker": broker,
            "login": login,
            "server": server,
            "account_info": mock_data
        }
    
    @staticmethod
    def get_account_trades(port: int, login: str) -> list:
        """Get trades from MT5 account (not implemented in MVP)."""
        return []
