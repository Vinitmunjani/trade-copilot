//+------------------------------------------------------------------+
//| TradeMonitor.mq5 - Real-time Trade Capture and API Integration  |
//+------------------------------------------------------------------+
#property copyright "Trade Co-Pilot"
#property link      "https://tradecopilot.ai"
#property version   "1.00"
#property strict

input string API_URL = "http://localhost:5000";
input int CHECK_INTERVAL = 1000; // milliseconds
input bool SEND_TRADE_UPDATES = true;
input bool SEND_ACCOUNT_UPDATES = true;

int last_check_time = 0;
int last_trade_count = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit() {
    Print("[TradeMonitor] EA initialized");
    
    // Send initial account info
    if (SEND_ACCOUNT_UPDATES) {
        SendAccountUpdate();
    }
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
    Print("[TradeMonitor] EA deinitialized, reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() {
    int current_time = GetTickCount();
    
    // Check for trade updates periodically
    if (current_time - last_check_time > CHECK_INTERVAL) {
        int current_trade_count = PositionsTotal();
        
        // Send account update
        if (SEND_ACCOUNT_UPDATES) {
            SendAccountUpdate();
        }
        
        // Check for new trades
        if (SEND_TRADE_UPDATES && current_trade_count != last_trade_count) {
            SendTradeUpdates();
        }
        
        last_trade_count = current_trade_count;
        last_check_time = current_time;
    }
}

//+------------------------------------------------------------------+
//| Send all open trades to API                                      |
//+------------------------------------------------------------------+
void SendTradeUpdates() {
    int total = PositionsTotal();
    Print("[TradeMonitor] Found ", total, " open trades");
    
    for (int i = 0; i < total; i++) {
        if (!PositionSelectByTicket(PositionGetTicket(i))) {
            continue;
        }
        
        string symbol = PositionGetString(POSITION_SYMBOL);
        double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
        double current_price = PositionGetDouble(POSITION_PRICE_CURRENT);
        double volume = PositionGetDouble(POSITION_VOLUME);
        long ticket = PositionGetTicket(i);
        long open_time = PositionGetInteger(POSITION_TIME);
        string comment = PositionGetString(POSITION_COMMENT);
        
        ENUM_POSITION_TYPE pos_type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
        string type_str = (pos_type == POSITION_TYPE_BUY) ? "BUY" : "SELL";
        
        // Build JSON payload
        string json = "";
        json += "{";
        json += "\"ticket\":" + IntegerToString(ticket) + ",";
        json += "\"symbol\":\"" + symbol + "\",";
        json += "\"type\":\"" + type_str + "\",";
        json += "\"open_price\":" + DoubleToString(open_price, 5) + ",";
        json += "\"current_price\":" + DoubleToString(current_price, 5) + ",";
        json += "\"volume\":" + DoubleToString(volume, 2) + ",";
        json += "\"open_time\":" + IntegerToString(open_time) + ",";
        json += "\"comment\":\"" + comment + "\"";
        json += "}";
        
        SendToAPI(API_URL + "/trades/new", json);
    }
}

//+------------------------------------------------------------------+
//| Send account information to API                                  |
//+------------------------------------------------------------------+
void SendAccountUpdate() {
    string account_json = "";
    account_json += "{";
    account_json += "\"login\":" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + ",";
    account_json += "\"balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + ",";
    account_json += "\"equity\":" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + ",";
    account_json += "\"margin\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN), 2) + ",";
    account_json += "\"margin_free\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2) + ",";
    account_json += "\"margin_level\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_LEVEL), 2) + ",";
    account_json += "\"currency\":\"" + AccountInfoString(ACCOUNT_CURRENCY) + "\",";
    account_json += "\"leverage\":" + IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)) + ",";
    account_json += "\"company\":\"" + AccountInfoString(ACCOUNT_COMPANY) + "\",";
    account_json += "\"name\":\"" + AccountInfoString(ACCOUNT_NAME) + "\"";
    account_json += "}";
    
    SendToAPI(API_URL + "/account/update", account_json);
}

//+------------------------------------------------------------------+
//| Generic HTTP POST function                                       |
//+------------------------------------------------------------------+
void SendToAPI(string url, string json_data) {
    // Note: WebRequest requires proper setup in MT5
    // This would require handling in the EA properly
    Print("[TradeMonitor] Would send to API: ", url);
    Print("[TradeMonitor] Data: ", json_data);
    
    // In a real setup with WebRequest enabled:
    // char post_data[];
    // ArrayResize(post_data, StringLen(json_data));
    // StringToCharArray(json_data, post_data, 0, StringLen(json_data));
    // char result[];
    // WebRequest("POST", url, "Content-Type: application/json\r\n", 5000, post_data, result, 0);
}

//+------------------------------------------------------------------+
