# External imports -----------------------------------------------------------------------------------------------------
import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncConnection

# Internal imports -----------------------------------------------------------------------------------------------------
from src.db.base import SqlalchemyBase
from tests.conftest import alembic_config

pytestmark = pytest.mark.migrations





# Helpers --------------------------------------------------------------------------------------------------------------

# Compare the live database schema with the SQLAlchemy models and return every difference
def _schema_differences(connection: Connection) -> list:
    migration_context = MigrationContext.configure(connection)
    return compare_metadata(migration_context, SqlalchemyBase.metadata)


# Full round trip: remove every table, then build them again from the migration files
def _downgrade_then_upgrade(connection: Connection) -> None:
    config = alembic_config()
    config.attributes["connection"] = connection
    command.downgrade(config, "base")
    command.upgrade(config, "head")





# Tests ----------------------------------------------------------------------------------------------------------------

# Catches "I changed a model but forgot to create a migration"
async def test_models_and_migrations_are_in_sync(db_connection: AsyncConnection) -> None:
    differences = await db_connection.run_sync(_schema_differences)
    assert differences == [], f"Models differ from the migrated database: {differences}"


# Catches broken downgrade() functions; PostgreSQL DDL is transactional, so this is rolled back afterwards
async def test_migrations_can_be_reverted_and_reapplied(db_connection: AsyncConnection) -> None:
    await db_connection.run_sync(_downgrade_then_upgrade)
    differences = await db_connection.run_sync(_schema_differences)
    assert differences == []
