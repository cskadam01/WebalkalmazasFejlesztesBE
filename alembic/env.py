from logging.config import fileConfig
import os
from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# .env betöltése (hogy a DATABASE_URL elérhető legyen)
load_dotenv()

# Alembic config
config = context.config

# DATABASE_URL az .env-ből (felülírja az alembic.ini sqlalchemy.url-t)
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Modellek és MetaData bekötése ---
from database.db import Base          # itt van a declarative_base()
from models import models             # fontos: import, hogy a táblák tényleg betöltődjenek

target_metadata = Base.metadata
# --------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,               # típusváltozások észlelése
        compare_server_default=True,     # szerver oldali defaultok észlelése
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,               # típusváltozások észlelése
            compare_server_default=True,     # szerver oldali defaultok észlelése
            # render_as_batch=True,          # csak SQLite-hoz kell(het)
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
