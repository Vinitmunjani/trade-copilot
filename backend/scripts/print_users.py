import sqlite3
from pprint import pprint
DB = 'trade_copilot.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT id,email,metaapi_account_id,mt_login,mt_server,mt_last_heartbeat FROM users')
rows = cur.fetchall()
for r in rows:
    row = dict(r)
    print(row)
conn.close()
