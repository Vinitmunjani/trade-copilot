#!/usr/bin/env python3
"""Assign an account row to a user by email.

Usage: run without args (values are set in the file) or pass via env vars:
  ACCOUNT_ID, USER_EMAIL, DB_PATH

This script will update `meta_accounts` and `accounts` tables (if present).
"""
import os
import sqlite3
import sys

DB = os.getenv("DB_PATH", r"d:\\TradeCo-Pilot\\backend\\dev.db")
ACCOUNT_ID = os.getenv("ACCOUNT_ID", "8656cfd8-5f14-40f2-9f4b-e69c5a968bbe")
USER_EMAIL = os.getenv("USER_EMAIL", "vinitmunjani11@gmail.com")


def main():
    if not os.path.exists(DB):
        print(f"Database not found: {DB}")
        sys.exit(2)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Ensure user exists
    cur.execute("SELECT id FROM users WHERE email = ?", (USER_EMAIL,))
    row = cur.fetchone()
    if not row:
        print(f"User with email {USER_EMAIL} not found in users table.")
        conn.close()
        sys.exit(3)

    user_id = row[0]
    print(f"Found user id: {user_id}")

    tables = ("meta_accounts", "accounts")
    updated_any = False
    for table in tables:
        try:
            cur.execute(f"UPDATE {table} SET user_id = ? WHERE id = ?", (user_id, ACCOUNT_ID))
            if cur.rowcount > 0:
                print(f"Updated {cur.rowcount} row(s) in {table}.")
                conn.commit()
                updated_any = True
                break
        except sqlite3.OperationalError as e:
            # table not present or invalid schema
            print(f"Skipping {table}: {e}")
            continue

    if not updated_any:
        # As fallback, show candidate account rows
        for table in tables:
            try:
                cur.execute(f"SELECT id, user_id, mt_login, mt_server FROM {table} WHERE id = ?", (ACCOUNT_ID,))
                r = cur.fetchone()
                if r:
                    print(f"Found row in {table}: {r}")
                else:
                    print(f"No row with id {ACCOUNT_ID} in {table}.")
            except sqlite3.OperationalError:
                pass

    conn.close()


if __name__ == "__main__":
    main()
