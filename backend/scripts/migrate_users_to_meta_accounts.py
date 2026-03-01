import sqlite3
from datetime import datetime
DB='trade_copilot.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()
cur.execute("SELECT id,email,metaapi_account_id,mt_login,mt_server,mt_platform,mt_last_heartbeat FROM users WHERE metaapi_account_id IS NOT NULL")
rows=cur.fetchall()
for r in rows:
    uid, email, metaid, login, server, platform, heartbeat = r
    # check if already exists
    cur.execute('SELECT 1 FROM meta_accounts WHERE metaapi_account_id = ?', (metaid,))
    if cur.fetchone():
        print('Already migrated:', email)
        continue
    cur.execute('INSERT INTO meta_accounts (id,user_id,metaapi_account_id,mt_login,mt_server,mt_platform,mt_last_heartbeat,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)', (
        uid, uid, metaid, login, server, platform, heartbeat, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()
    ))
    print('Migrated user', email, '-> account', metaid)
conn.commit()
conn.close()
