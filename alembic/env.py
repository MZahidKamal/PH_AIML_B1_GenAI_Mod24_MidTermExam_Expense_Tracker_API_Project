# External imports -----------------------------------------------------------------------------------------------------
from alembic import context
from logging.config import fileConfig
import sys
import asyncio
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core.config import env_settings
from src.db.base import SqlalchemyBase

# Import every feature's models here so SqlalchemyBase.metadata knows about all tables ---------------------------------
from src.features.users import models as user_models                      # noqa: F401
from src.features.auth import models as auth_models                       # noqa: F401
from src.features.transactions import models as transaction_models        # noqa: F401





# ----------------------------------------------------------------------------------------------------------------------

# Access the Alembic configuration object from the migration context
config = context.config

# Load logging configuration from the alembic.ini file if available;
# disable_existing_loggers=False keeps the application's (and pytest's) loggers working
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Assign the SQLAlchemy models' metadata object to target metadata for migration tracking
target_metadata = SqlalchemyBase.metadata

# Dynamically override the Alembic configuration database URL with the environment settings string
config.set_main_option("sqlalchemy.url", env_settings.sb_connection_string)





# ----------------------------------------------------------------------------------------------------------------------

# Check if the operating system platform is Windows
# if sys.platform == "win32":

    # Set the event loop policy to WindowsSelectorEventLoopPolicy to prevent compatibility issues on Windows
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())





# ----------------------------------------------------------------------------------------------------------------------

# Run migrations in 'offline' mode without connecting to a live database engine
def run_migrations_offline() -> None:

    # Retrieve the database connection URL from the Alembic configuration
    url = config.get_main_option("sqlalchemy.url")

    # Configure the migration context with the database URL, model metadata, and SQL generation options
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    # Open a migration transaction and generate/execute the migration scripts as raw SQL
    with context.begin_transaction():
        context.run_migrations()





# ----------------------------------------------------------------------------------------------------------------------

# Define a helper function to execute migrations using an active database connection
def do_run_migrations(connection: Connection) -> None:

    # Configure the Alembic migration context with the live database connection and model metadata
    context.configure(connection=connection, target_metadata=target_metadata)

    # Begin a database transaction and run the migrations on the live database
    with context.begin_transaction():
        context.run_migrations()





# ----------------------------------------------------------------------------------------------------------------------

# Define an asynchronous function to handle database migrations in online mode using an async engine
async def run_async_migrations() -> None:

    # Create an asynchronous SQLAlchemy engine from the Alembic configuration settings
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Establish an asynchronous database connection and run sync-based migrations safely inside it
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    # Close and dispose of the asynchronous engine connection pool after migrations complete
    await connectable.dispose()





# ----------------------------------------------------------------------------------------------------------------------

# Entry point for online migrations
def run_migrations_online() -> None:

    # If a connection was handed over programmatically (e.g. by the pytest suite for the TEST database), use it
    connection = config.attributes.get("connection", None)

    if connection is None:
        # Normal CLI usage ('alembic upgrade head'): create our own async engine for the main database.
        # psycopg's async mode needs a SelectorEventLoop on Windows; loop_factory is the modern replacement
        # for the deprecated asyncio.set_event_loop_policy(...)
        loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
        asyncio.run(run_async_migrations(), loop_factory=loop_factory)
    else:
        # Programmatic usage: the caller already opened the connection (inside its own event loop)
        do_run_migrations(connection)





# ----------------------------------------------------------------------------------------------------------------------

# Check whether Alembic is running in offline mode or online mode and execute the respective migration function
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()





# ----------------------------------------------------------------------------------------------------------------------
