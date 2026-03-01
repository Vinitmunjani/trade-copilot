import sqlite3, os
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dev.db'))
if not os.path.exists(p):
    print('DB not found', p)
    raise SystemExit(1)
conn = sqlite3.connect(p)
cur = conn.cursor()
print('PRAGMA table_info(meta_accounts):')
for r in cur.execute('PRAGMA table_info(meta_accounts)'):
    print(r)
conn.close()
