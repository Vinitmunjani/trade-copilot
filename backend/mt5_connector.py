"""MT5 Terminal Connection Manager - now using real broker APIs."""
from broker_api import BrokerAPIClient
from typing import Dict, Any

class MT5Connector:
    """Manages MT5 terminal initialization and login via broker APIs."""
    
    # Map brokers to ports (for reference)
    BROKER_PORTS = {
        "Exness": 5002,
        "ICMarkets": 5001,
        "XM": 5003,
    }
    
    @staticmethod
    def get_port_for_broker(broker: str) -> int:
        """Get MT5 container port for broker."""
        return MT5Connector.BROKER_PORTS.get(broker, 5001)
    
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
    def connect_account(broker: str, login: str, password: str, server: str = "Demo") -> Dict[str, Any]:
        """
        Connect to real broker account via their REST API.
        
        Returns:
            {
                "status": "connected|failed",
                "broker": "Exness",
                "login": "279495999",
                "server": "Exness-MT5Trial8",
                "account_info": {
                    "balance": 10000.0,
                    "equity": 9950.25,
                    "free_margin": 9900.25,
                    "used_margin": 49.75,
                    "margin_level": 19900,
                    "currency": "USD",
                    "leverage": 500,
                    "account_name": "Live Account",
                    "company": "Exness",
                    "trading_allowed": True,
                }
                "error": "reason"  # if failed
            }
        """
        # Use real broker API to connect
        result = BrokerAPIClient.connect(broker, login, password, server)
        return result
    
    @staticmethod
    def get_account_trades(broker: str, login: str, password: str) -> list:
        """Get trades from real broker account (Phase 2)."""
        return []
