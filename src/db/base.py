# External imports -----------------------------------------------------------------------------------------------------
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase





# Necessary classes -----------------------------------------------------------------------------------------------------

# Predictable names for every constraint/index, so Alembic can reliably find, alter and drop them later
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}






# Define a base class for all SQLAlchemy models; AsyncAttrs adds safe async access to lazy-loaded attributes
class SqlalchemyBase(AsyncAttrs, DeclarativeBase):

    # Shared metadata object with the naming convention applied to all tables
    metadata = MetaData(naming_convention=NAMING_CONVENTION)





# ----------------------------------------------------------------------------------------------------------------------
