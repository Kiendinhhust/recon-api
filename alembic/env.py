from logging.config import fileConfig
import os
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Load .env file if it exists (for local development)
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✓ Loaded .env file from {env_path}")
else:
    print(f"⚠ WARNING: .env file not found at {env_path}")

# Import your models here
from app.deps import Base
from app.storage.models import ScanJob, Subdomain, Screenshot, WafDetection, LeakDetection, Technology
from app.auth.models import User

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with DATABASE_URL from environment if available
# This ensures Alembic uses the same database credentials as the application
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Mask password for security when printing
    if '@' in database_url:
        parts = database_url.split('@')
        user_pass = parts[0].split(':')
        if len(user_pass) >= 3:  # postgresql://user:pass
            masked_url = ':'.join(user_pass[:-1]) + ':***@' + parts[1]
        else:
            masked_url = database_url
    else:
        masked_url = database_url
    print(f"✓ Using DATABASE_URL from environment: {masked_url}")
    config.set_main_option("sqlalchemy.url", database_url)
else:
    print("⚠ WARNING: DATABASE_URL not found in environment, using alembic.ini default")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
