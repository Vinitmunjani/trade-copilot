"""Real MT5 connection using MetaTrader5 Python library."""
import MetaTrader5 as mt5
from typing import Dict, Any, Optional

class RealMT5Connection:
    """Connect to real MT5 accounts via MT5 Python library."""
    
    # Broker connection details
    BROKER_PATHS = {
        "Exness": "C:\\Program Files\\Exness\\Terminal\\terminal.exe",
        "ICMarkets": "C:\\Program Files\\IC Markets\\terminal.exe", 
        "XM": "C:\\Program Files\\XM\\terminal.exe",
    }
    
    @staticmethod
    def connect(broker: str, login: int, password: str, server: str) -> Dict[str, Any]:
        """
        Connect to real MT5 account.
        
        Returns:
            {
                "status": "connected|failed",
                "account_info": {...},
                "error": "message" (if failed)
            }
        """
        try:
            # Initialize MT5
            if not mt5.initialize(login=login, password=password, server=server):
                return {
                    "status": "failed",
                    "error": f"MT5 initialization failed: {mt5.last_error()}"
                }
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                mt5.shutdown()
                return {
                    "status": "failed",
                    "error": "Failed to get account info"
                }
            
            # Convert to dict
            result = {
                "status": "connected",
                "account_info": {
                    "login": account_info.login,
                    "server": account_info.server,
                    "balance": account_info.balance,
                    "equity": account_info.equity,
                    "credit": account_info.credit,
                    "margin": account_info.margin,
                    "margin_free": account_info.margin_free,
                    "margin_level": account_info.margin_level,
                    "margin_used": account_info.margin_used,
                    "currency_digits": account_info.currency_digits,
                    "fifo_close": account_info.fifo_close,
                    "trade_allowed": account_info.trade_allowed,
                    "buy_only": account_info.buy_only,
                    "company": account_info.company,
                    "name": account_info.name,
                    "leverage": account_info.leverage,
                    "currency": account_info.currency,
                    "phone": account_info.phone,
                    "email": account_info.email,
                }
            }
            
            mt5.shutdown()
            return result
            
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Connection error: {str(e)}"
            }
    
    @staticmethod
    def get_trades(login: int, password: str, server: str) -> list:
        """Get all open trades from account."""
        try:
            if not mt5.initialize(login=login, password=password, server=server):
                return []
            
            trades = mt5.positions_get()
            if trades is None:
                mt5.shutdown()
                return []
            
            result = []
            for trade in trades:
                result.append({
                    "ticket": trade.ticket,
                    "symbol": trade.symbol,
                    "type": "BUY" if trade.type == mt5.ORDER_TYPE_BUY else "SELL",
                    "open_price": trade.price_open,
                    "current_price": trade.price_current,
                    "volume": trade.volume,
                    "profit": trade.profit,
                    "open_time": trade.time,
                    "comment": trade.comment,
                })
            
            mt5.shutdown()
            return result
            
        except:
            return []
