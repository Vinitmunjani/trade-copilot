"""Alembic migration environment configuration.

Uses async SQLAlchemy engine from the application's database module.
Supports both online (connected) and offline (SQL script) migrations.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine

# Import application models and config so Alembic can detect schema changes
from app.config import get_settings
from app.database import Base
from app.models import User, Trade, DailyStats, TradingRules, TradeLog  # noqa: F401 — ensure models are registered

settings = get_settings()

# Alembic Config object — provides access to alembic.ini values
config = context.config

# Override sqlalchemy.url from application settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for generating migration SQL to run manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations using a synchronous connection.

    Called by both online and async migration runners.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' async mode.

    Creates an async engine and runs migrations within a connection.
    """
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Delegates to the async runner since we use asyncpg.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
