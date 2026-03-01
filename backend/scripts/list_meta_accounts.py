#!/usr/bin/env python3
"""List meta_accounts rows for inspection."""
import os, sqlite3, sys

DB = os.getenv("DB_PATH", r"d:\\TradeCo-Pilot\\backend\\dev.db")

if not os.path.exists(DB):
    print(f"Database not found: {DB}")
    sys.exit(2)

conn = sqlite3.connect(DB)
cur = conn.cursor()
try:
    cur.execute("SELECT id, user_id, mt_login, mt_server, mt_platform, mt_last_heartbeat, created_at FROM meta_accounts ORDER BY created_at DESC")
    rows = cur.fetchall()
    if not rows:
        print("No rows found in meta_accounts")
    else:
        print(f"Found {len(rows)} rows in meta_accounts:\n")
        for r in rows:
            print("id:", r[0])
            print(" user_id:", r[1])
            print(" mt_login:", r[2])
            print(" mt_server:", r[3])
            print(" mt_platform:", r[4])
            print(" mt_last_heartbeat:", r[5])
            print(" created_at:", r[6])
            print("-"*40)
except sqlite3.OperationalError as e:
    print("Error querying meta_accounts:", e)
finally:
    conn.close()
