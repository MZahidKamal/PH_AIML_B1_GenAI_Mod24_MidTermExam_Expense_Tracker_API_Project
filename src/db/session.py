# External imports -----------------------------------------------------------------------------------------------------
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from collections.abc import AsyncIterator
from sqlalchemy import text
import asyncio
import sys

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core.config import env_settings





# Necessary classes, objects and functions -----------------------------------------------------------------------------

# Create an asynchronous SQLAlchemy engine; pool_pre_ping checks a pooled connection is alive before using it
db_engine = create_async_engine(env_settings.sb_connection_string, pool_pre_ping=True)

# Create a session factory; expire_on_commit=False keeps object attributes readable after commit (recommended for async)
DB_SessionLocal = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

# Define a dependency function to provide one database session per request and close it afterwards
async def get_db() -> AsyncIterator[AsyncSession]:
    async with DB_SessionLocal() as db_session:
        yield db_session





# Checking PostgreSQL cloud database accessibility ---------------------------------------------------------------------

# Verify the database connection; raise the error so the application does NOT start with a broken database
async def check_db_connection() -> None:
    print("\nChecking if database connection is established correctly...")

    try:
        # Open a connection and fetch the PostgreSQL server version in one step
        async with db_engine.connect() as connection:
            db_version = await connection.scalar(text("SELECT version();"))

    except Exception as error:
        # Print only the error type here (the full traceback will appear in the terminal), then re-raise
        print(f"    ❌ Failed to connect to the database.")
        print(f"    ❌ Error type: {type(error).__name__}")
        raise

    print(f"    ✅ Database connection established successfully.")
    print(f"    ✅ Connected to: {db_engine.url.database} @ {db_engine.url.host}")
    print(f"    ✅ PostgreSQL version: {db_version}")


# Run the check standalone and always dispose the engine afterwards (recommended by SQLAlchemy docs)
async def _run_standalone_check() -> None:
    try:
        await check_db_connection()
    finally:
        await db_engine.dispose()



# Execute the check when this file is run directly: python -m src.db.session
# if __name__ == "__main__":
#     asyncio.run(_run_standalone_check())

# On Windows, psycopg's async mode needs a SelectorEventLoop (loop_factory replaces the deprecated event loop policy)
if __name__ == "__main__":
    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    asyncio.run(_run_standalone_check(), loop_factory=loop_factory)





# ----------------------------------------------------------------------------------------------------------------------
