import os
import sqlite3
import sys

def search(db_path, meta_id, mt_login):
    db_path = os.path.abspath(db_path)
    if not os.path.exists(db_path):
        print(f"DB not found: {db_path}")
        return 2

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("Searching tables for meta id or mt_login...")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]

    found = False
    for t in tables:
        try:
            q = f"SELECT * FROM {t} WHERE id = ? OR mt_login = ? LIMIT 5"
            cur.execute(q, (meta_id, mt_login))
            rows = cur.fetchall()
            if rows:
                print(f"\nTable: {t}")
                for r in rows:
                    print(dict(r))
                found = True
        except Exception:
            # table may not have those columns
            continue

    if not found:
        print("No matches found for meta id or mt_login in any table.")

    conn.close()
    return 0


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--meta-id', required=True)
    p.add_argument('--mt-login', required=False)
    p.add_argument('--db', default=os.path.join(os.path.dirname(__file__), '..', 'dev.db'))
    args = p.parse_args()
    sys.exit(search(args.db, args.meta_id, args.mt_login))
