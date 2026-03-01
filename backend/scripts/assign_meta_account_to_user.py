import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True, help="user email to assign to")
    parser.add_argument("--meta-id", required=True, help="meta_accounts.id to assign")
    parser.add_argument("--db", default=os.path.join(os.path.dirname(__file__), '..', 'dev.db'), help="path to sqlite db")
    parser.add_argument("--create", action='store_true', help="create the meta_accounts row if missing")
    parser.add_argument("--mt-login", help="MT login to set when creating the row")
    parser.add_argument("--mt-server", help="MT server to set when creating the row")
    parser.add_argument("--mt-platform", help="MT platform to set when creating the row")
    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        print(f"DB not found: {db_path}")
        sys.exit(2)

    bak_path = db_path + '.bak'
    shutil.copy2(db_path, bak_path)
    print(f"Backed up DB to {bak_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # find user id
    cur.execute("SELECT id, email FROM users WHERE email = ?", (args.email,))
    row = cur.fetchone()
    if not row:
        print(f"User with email {args.email} not found in users table")
        conn.close()
        sys.exit(3)
    user_id = row["id"]
    print(f"Found user id: {user_id}")

    # check meta_accounts table exists
    try:
        cur.execute("SELECT id, user_id, mt_login, mt_server, mt_platform FROM meta_accounts WHERE id = ?", (args.meta_id,))
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        conn.close()
        sys.exit(4)

    meta = cur.fetchone()
    if not meta:
        if '--create' in ' '.join(sys.argv):
            mt_login = None
            mt_server = None
            mt_platform = None
            # parse optional args from sys.argv
            for i, a in enumerate(sys.argv):
                if a == '--mt-login' and i + 1 < len(sys.argv):
                    mt_login = sys.argv[i+1]
                if a == '--mt-server' and i + 1 < len(sys.argv):
                    mt_server = sys.argv[i+1]
                if a == '--mt-platform' and i + 1 < len(sys.argv):
                    mt_platform = sys.argv[i+1]

            print(f"No row with id {args.meta_id} found in meta_accounts; inserting new row.")
            cur.execute(
                "INSERT INTO meta_accounts (id, user_id, metaapi_account_id, mt_login, mt_server, mt_platform, mt_last_heartbeat, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (args.meta_id, user_id, args.meta_id, mt_login, mt_server, mt_platform, None, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
            )
            conn.commit()
        else:
            print(f"No row with id {args.meta_id} found in meta_accounts")
            conn.close()
            sys.exit(5)

    print("Before:")
    print(dict(meta) if meta else {'id': args.meta_id, 'user_id': None})

    cur.execute("UPDATE meta_accounts SET user_id = ? WHERE id = ?", (user_id, args.meta_id))
    conn.commit()

    cur.execute("SELECT id, user_id, mt_login, mt_server, mt_platform FROM meta_accounts WHERE id = ?", (args.meta_id,))
    updated = cur.fetchone()
    print("After:")
    print(dict(updated) if updated else 'Not found after update')

    conn.close()


if __name__ == '__main__':
    main()
