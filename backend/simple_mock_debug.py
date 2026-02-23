"""Debug version - test account_info in response."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
import os
from mt5_connector import MT5Connector

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent storage files
ACCOUNTS_FILE = "/tmp/accounts_debug.json"

accounts = {}

def save_to_file(filepath: str, data: dict):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving to {filepath}: {e}")

@app.post("/api/v1/account/connect")
async def connect_account(broker: str = None, login: str = None, password: str = None, server: str = None, authorization: str = None):
    """Connect broker account via real broker APIs."""
    print(f"[DEBUG] Received broker={broker}, login={login}")
    
    # Connect via real broker API
    result = MT5Connector.connect_account(broker, login, password, server or "Demo")
    
    print(f"[DEBUG] MT5Connector result: {result}")
    
    if result["status"] == "failed":
        return {"detail": result.get("error", "Failed to connect")}, 400
    
    # Create response
    account_id = str(uuid.uuid4())
    response = {
        "id": account_id,
        "broker": broker,
        "login": login,
        "server": server or "Demo",
        "status": "connected",
        "account_info": result.get("account_info", {})
    }
    
    print(f"[DEBUG] Response being returned: {response}")
    print(f"[DEBUG] Response JSON: {json.dumps(response)}")
    
    return response

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
