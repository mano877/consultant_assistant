"""Alembic uses the same environment-based database URL as the backend."""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import DATABASE_URL
from app.database import Base
from app import models  # Register ORM metadata without importing main/startup.

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)
target_metadata = Base.metadata


def migrate(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("These adoption migrations require an online connection to inspect existing columns. Run alembic upgrade head without --sql.")
elif config.attributes.get("connection") is not None:
    migrate(config.attributes["connection"])
else:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be configured before running migrations")
    engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with engine.connect() as connection:
        migrate(connection)
    engine.dispose()
