#!/usr/bin/env python3
"""Backfill trades.pnl_r using price-based R-multiple.

Formula:
  R = (price_move_in_trade_direction) / abs(entry_price - sl)

This script is dry-run by default. Use --apply to persist updates.
"""

import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _compute_price_based_r(trade) -> float | None:
    if trade.entry_price is None or trade.sl is None or trade.exit_price is None:
        return None

    risk = abs(trade.entry_price - trade.sl)
    if risk <= 0:
        return None

    direction = getattr(trade.direction, "value", trade.direction)
    if str(direction).upper() == "BUY":
        move = trade.exit_price - trade.entry_price
    else:
        move = trade.entry_price - trade.exit_price

    return round(move / risk, 3)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill trades.pnl_r with price-based R-multiple")
    parser.add_argument("--apply", action="store_true", help="Persist updates (default is dry-run)")
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Override DATABASE_URL for this run",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Use SQLite DB file path (builds sqlite+aiosqlite URL)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.01,
        help="Minimum absolute difference required to mark a row as changed (default: 0.01)",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="Optional user UUID to scope updates to one user",
    )
    args = parser.parse_args()

    if args.db_path and args.database_url:
        parser.error("Use only one of --db-path or --database-url")

    if args.db_path:
        db_file = Path(args.db_path).expanduser().resolve()
        if not db_file.exists():
            raise FileNotFoundError(f"SQLite DB not found: {db_file}")
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    elif args.database_url:
        os.environ["DATABASE_URL"] = args.database_url

    from app.database import async_session_factory
    from app.models.trade import Trade, TradeDirection, TradeStatus

    scoped_user_id = None
    if args.user_id:
        scoped_user_id = uuid.UUID(args.user_id)

    try:
        async with async_session_factory() as db:
            conditions = [
                Trade.status == TradeStatus.CLOSED,
                Trade.entry_price.is_not(None),
                Trade.sl.is_not(None),
                Trade.exit_price.is_not(None),
            ]
            if scoped_user_id:
                conditions.append(Trade.user_id == scoped_user_id)

            result = await db.execute(
                select(Trade)
                .where(and_(*conditions))
                .order_by(Trade.open_time.desc())
            )
            rows = result.scalars().all()

            evaluated = 0
            skipped = 0
            changed = 0
            examples: list[str] = []

            for trade in rows:
                evaluated += 1
                computed = _compute_price_based_r(trade)
                if computed is None:
                    skipped += 1
                    continue

                current = trade.pnl_r
                if current is None or abs(current - computed) > args.tolerance:
                    changed += 1
                    if len(examples) < 20:
                        examples.append(
                            f"trade_id={trade.id} symbol={trade.symbol} old={current} new={computed}"
                        )
                    if args.apply:
                        trade.pnl_r = computed

            mode = "APPLY" if args.apply else "DRY-RUN"
            print(f"Mode: {mode}")
            print(f"Evaluated closed trades: {evaluated}")
            print(f"Skipped (invalid risk data): {skipped}")
            print(f"Trades needing update: {changed}")

            if examples:
                print("\nExamples:")
                for line in examples:
                    print(" -", line)

            if args.apply:
                await db.commit()
                print("\nChanges committed.")
            else:
                await db.rollback()
                print("\nNo changes written (dry-run).")
    except SQLAlchemyError as e:
        print("Database connection/query failed.")
        print(f"Details: {e}")
        print("Hint: pass --db-path <sqlite_file> or --database-url <url> for this run.")
        raise


if __name__ == "__main__":
    asyncio.run(main())
