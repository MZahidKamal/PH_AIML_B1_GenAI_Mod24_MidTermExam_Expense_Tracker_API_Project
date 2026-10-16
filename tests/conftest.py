# External imports -----------------------------------------------------------------------------------------------------
import asyncio
import json
import sys
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

import allure
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core.config import env_settings
from src.db.session import get_db
from src.main import app





# Constants ------------------------------------------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORD = "StrongPass123"


# Report grouping for every test file: (epic, feature, layer tag)
REPORT_LABELS: dict[str, tuple[str, str, str]] = {
    "test_security.py": ("Core", "Password hashing & JWT", "unit"),
    "test_user_schemas.py": ("Users", "Validation rules", "unit"),
    "test_auth_schemas.py": ("Auth", "Validation rules", "unit"),
    "test_current_user.py": ("Auth", "Route protection", "api"),
    "test_register_api.py": ("Auth", "Register", "api"),
    "test_login_api.py": ("Auth", "Login", "api"),
    "test_token_lifecycle_api.py": ("Auth", "Refresh & logout", "api"),
    "test_transaction_schemas.py": ("Transactions", "Validation rules", "unit"),
    "test_transaction_models.py": ("Transactions", "Model & relationship", "database"),
    "test_create_transaction_api.py": ("Transactions", "Create", "api"),
    "test_read_transaction_api.py": ("Transactions", "Read", "api"),
    "test_filter_transaction_api.py": ("Transactions", "Filter", "api"),
    "test_update_transaction_api.py": ("Transactions", "Update", "api"),
    "test_delete_transaction_api.py": ("Transactions", "Delete", "api"),
    "test_migrations.py": ("Database", "Migrations", "database"),
}


# The five tests the exam asks for; they are marked as critical in the Allure report
EXAM_TESTS = {
    "test_get_transactions",
    "test_get_transaction_by_id",
    "test_create_transaction",
    "test_update_transaction",
    "test_delete_transaction",
}





# Event loop (Windows support) -----------------------------------------------------------------------------------------

# psycopg's async mode does not work with Windows' default ProactorEventLoop; this pytest-asyncio hook
# tells pytest-asyncio which loop to create (the modern replacement for overriding the event loop policy)
def pytest_asyncio_loop_factories(config: pytest.Config, item: pytest.Item) -> dict[str, Callable[[], asyncio.AbstractEventLoop]]:
    if sys.platform == "win32":
        return {"selector": asyncio.SelectorEventLoop}
    return {"default": asyncio.new_event_loop}





# Test reports (pytest-html + Allure) ----------------------------------------------------------------------------------

# pytest-html: title shown at the top of the HTML report
def pytest_html_report_title(report) -> None:
    report.title = "Expense Tracker API - Test Report"


# pytest-html: extra rows in the "Environment" table (never put secrets or connection strings here)
def pytest_metadata(metadata: dict) -> None:
    metadata["Project"] = "Expense Tracker API (FastAPI)"
    metadata["Database"] = "PostgreSQL test database (Supabase), rolled back after every test"


# Allure: give every test an epic, feature, layer tag, severity and a readable title, based on its file and name
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        epic, feature, layer = REPORT_LABELS.get(Path(str(item.path)).name, ("Other", "Other", "other"))
        test_name = item.originalname if isinstance(item, pytest.Function) else item.name

        item.add_marker(allure.epic(epic))
        item.add_marker(allure.feature(feature))
        item.add_marker(allure.tag(layer))

        if test_name in EXAM_TESTS:
            item.add_marker(allure.severity(allure.severity_level.CRITICAL))
            item.add_marker(allure.tag("exam"))
        else:
            item.add_marker(allure.severity(allure.severity_level.NORMAL))

        # "test_create_transaction" -> "Create transaction" (only if no @allure.title was set by hand)
        function = getattr(item, "function", None)
        if function is not None and not hasattr(function, "__allure_display_name__"):
            function.__allure_display_name__ = test_name.removeprefix("test_").replace("_", " ").capitalize()


# Allure: hide pytest-asyncio's internal "_asyncio_loop_factory" parameter (it would clutter every test title)
@pytest.fixture(autouse=True)
def _hide_internal_allure_parameters(request: pytest.FixtureRequest) -> None:
    callspec = getattr(request.node, "callspec", None)
    if callspec is not None and "_asyncio_loop_factory" in callspec.params:
        allure.dynamic.parameter(
            "_asyncio_loop_factory", "hidden", excluded=True, mode=allure.parameter_mode.HIDDEN
        )


# Keys whose values must never appear in a report (test data or not, reports get shared)
SENSITIVE_KEYS = {"password", "access_token", "refresh_token"}


# Replace sensitive values with "***" anywhere inside a JSON structure
def _redact(data: object) -> object:
    if isinstance(data, dict):
        return {key: "***" if key in SENSITIVE_KEYS else _redact(value) for key, value in data.items()}
    if isinstance(data, list):
        return [_redact(value) for value in data]
    return data


# Turn bytes into pretty, redacted JSON when possible, otherwise plain text
def _readable(content: bytes) -> object:
    if not content:
        return None
    try:
        return _redact(json.loads(content))
    except ValueError:
        return content.decode(errors="replace")


# httpx response hook: attach every request/response pair to the Allure report (Authorization header is masked)
async def attach_http_exchange_to_allure(response: Response) -> None:
    await response.aread()
    request = response.request
    exchange = {
        "request": {
            "method": request.method,
            "url": str(request.url),
            "authorization": "Bearer ***" if "authorization" in request.headers else None,
            "body": _readable(request.content),
        },
        "response": {"status_code": response.status_code, "body": _readable(response.content)},
    }
    allure.attach(
        json.dumps(exchange, indent=2, ensure_ascii=False, default=str),
        name=f"{request.method} {request.url.path} -> {response.status_code}",
        attachment_type=allure.attachment_type.JSON,
    )





# Alembic helpers ------------------------------------------------------------------------------------------------------

# Build an Alembic config that points to the project's alembic.ini (works from any working directory)
def alembic_config() -> Config:
    return Config(str(PROJECT_ROOT / "alembic.ini"))


# Run 'alembic upgrade head' on an already-open (sync-adapted) connection
def run_upgrade(connection: Connection, config: Config) -> None:
    config.attributes["connection"] = connection
    command.upgrade(config, "head")





# Database fixtures ----------------------------------------------------------------------------------------------------

# ONE engine for the whole test session, connected to the TEST database; the schema is brought up to date once
@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncIterator[AsyncEngine]:
    # Safety guard: never run destructive tests against the real database
    if env_settings.sb_testdb_connection_string == env_settings.sb_connection_string:
        pytest.exit("The test database URL equals the main database URL. Refusing to run tests.", returncode=1)

    engine = create_async_engine(env_settings.sb_testdb_connection_string, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.run_sync(run_upgrade, alembic_config())

    yield engine
    await engine.dispose()


# One connection + one OUTER transaction per test; it is rolled back at the end, so every test starts clean
@pytest_asyncio.fixture
async def db_connection(test_engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        yield connection
        await transaction.rollback()


# Session factory bound to the test connection; "create_savepoint" turns every commit()/rollback()
# made by the application into a SAVEPOINT, so the outer transaction stays open and can be rolled back
@pytest.fixture
def session_factory(db_connection: AsyncConnection) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=db_connection,
        expire_on_commit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )


# A session for tests that need to look into (or change) the database directly
@pytest_asyncio.fixture
async def db_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session





# HTTP client fixture --------------------------------------------------------------------------------------------------

# In-process HTTP client: requests go straight into the FastAPI app (no real server, no network)
@pytest_asyncio.fixture
async def client(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncClient]:

    # Every request gets its own session, all bound to this test's connection
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        event_hooks={"response": [attach_http_exchange_to_allure]},
    ) as async_client:
        yield async_client
    app.dependency_overrides.clear()





# User factories -------------------------------------------------------------------------------------------------------

# Everything a test needs to act as a logged-in user; secrets are hidden from repr(), so they never leak into reports
@dataclass(frozen=True)
class AuthUser:
    id: int
    username: str
    email: str
    password: str = field(repr=False)
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}


# Unique, valid credentials for a new user
def make_user_payload(**overrides: Any) -> dict[str, Any]:
    suffix = uuid4().hex[:10]
    payload = {"username": f"user_{suffix}", "email": f"user_{suffix}@example.com", "password": DEFAULT_PASSWORD}
    payload.update(overrides)
    return payload


# Factory fixture: register (and log in) a brand-new user; call it as many times as a test needs
@pytest.fixture
def create_user(client: AsyncClient) -> Callable[..., Awaitable[AuthUser]]:
    @allure.step("Register and log in a new user")
    async def _create_user(**overrides: Any) -> AuthUser:
        payload = make_user_payload(**overrides)

        register_response = await client.post("/auth/register", json=payload)
        assert register_response.status_code == 201, register_response.text

        login_response = await client.post(
            "/auth/login", json={"username": payload["username"], "password": payload["password"]}
        )
        assert login_response.status_code == 200, login_response.text
        tokens = login_response.json()

        return AuthUser(
            id=register_response.json()["id"],
            username=payload["username"],
            email=register_response.json()["email"],
            password=payload["password"],
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
        )

    return _create_user


# The main logged-in user of a test
@pytest_asyncio.fixture
async def user(create_user: Callable[..., Awaitable[AuthUser]]) -> AuthUser:
    return await create_user()


# A second logged-in user, used to prove that users cannot see or change each other's data
@pytest_asyncio.fixture
async def other_user(create_user: Callable[..., Awaitable[AuthUser]]) -> AuthUser:
    return await create_user()





# Transaction factory --------------------------------------------------------------------------------------------------

# Factory fixture: create a transaction for a user through the API; any field can be overridden
@pytest.fixture
def create_transaction(client: AsyncClient) -> Callable[..., Awaitable[dict[str, Any]]]:
    @allure.step("Create a transaction through the API")
    async def _create_transaction(owner: AuthUser, **overrides: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": "Groceries",
            "amount": 150.75,
            "type": "expense",
            "category": "Food",
            "date": "2026-10-01",
        }
        payload.update(overrides)

        response = await client.post("/transactions", json=payload, headers=owner.headers)
        assert response.status_code == 201, response.text
        return response.json()

    return _create_transaction





# ----------------------------------------------------------------------------------------------------------------------
