//+------------------------------------------------------------------+
//| TradeMonitor.mq5 - Expert Advisor for Trade Capture             |
//+------------------------------------------------------------------+
#property copyright "Trade Connect"
#property description "Captures trades and sends webhook"
#property strict

string WEBHOOK_URL = "http://backend:8000/api/trade_webhook";
string EA_VERSION = "1.0.0";

int OnInit() {
    Print("[TradeMonitor] Starting Trade Capture EA v" + EA_VERSION);
    EventSetTimer(5);
    return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) {
    EventKillTimer();
    Print("[TradeMonitor] EA deactivated");
}

void OnTick() {
    CheckPositions();
}

void OnTimer() {
    CheckPositions();
}

void CheckPositions() {
    int total_positions = PositionsTotal();
    
    for(int i = 0; i < total_positions; i++) {
        if(!PositionGetTicket(i)) continue;
        
        long ticket = PositionGetTicket(i);
        string symbol = PositionGetString(POSITION_SYMBOL);
        int type = PositionGetInteger(POSITION_TYPE);
        double volume = PositionGetDouble(POSITION_VOLUME);
        double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
        double current_price = PositionGetDouble(POSITION_PRICE_CURRENT);
        long open_time = PositionGetInteger(POSITION_TIME);
        double profit = PositionGetDouble(POSITION_PROFIT);
        double sl = PositionGetDouble(POSITION_SL);
        double tp = PositionGetDouble(POSITION_TP);
        
        SendWebhook(ticket, symbol, type, volume, open_price, current_price, 
                   open_time, profit, sl, tp);
    }
}

void SendWebhook(long ticket, string symbol, int type, double volume, 
                 double open_price, double current_price, long open_time, 
                 double profit, double sl, double tp) {
    
    string type_str = (type == POSITION_TYPE_BUY) ? "BUY" : "SELL";
    Print("[TradeMonitor] Trade: " + symbol + " " + type_str + " Vol:" + volume);
}

void OnStart() {
    Print("[TradeMonitor] Initial scan started");
    CheckPositions();
}
