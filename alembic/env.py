from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 1) Logging from alembic.ini
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 2) Load .env and set sqlalchemy.url from DATABASE_URL
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # If python-dotenv isn't installed, ignore; but autogenerate will fail without URL
    pass

db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# 3) Import Base metadata and models so autogenerate sees tables
#    Base is defined in app\database.py; models live in app\models.py
from app.database import Base  # type: ignore
import app.models  # noqa: F401  # ensures model classes are imported and tables registered

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("sqlalchemy.url is not set. Ensure DATABASE_URL is in .env or alembic.ini.")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    if not configuration:
        raise RuntimeError("Alembic configuration section missing.")
    if not configuration.get("sqlalchemy.url"):
        raise RuntimeError("sqlalchemy.url is not set. Ensure DATABASE_URL is in .env or alembic.ini.")

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
