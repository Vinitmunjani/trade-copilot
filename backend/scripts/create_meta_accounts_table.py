import sqlite3

DB='trade_copilot.db'
SQL='''
CREATE TABLE IF NOT EXISTS meta_accounts (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  metaapi_account_id TEXT,
  mt_login TEXT,
  mt_server TEXT,
  mt_platform TEXT,
  mt_last_heartbeat TEXT,
  created_at TEXT,
  updated_at TEXT
);
'''

conn=sqlite3.connect(DB)
cur=conn.cursor()
cur.execute(SQL)
conn.commit()
print('meta_accounts table ensured')
conn.close()
