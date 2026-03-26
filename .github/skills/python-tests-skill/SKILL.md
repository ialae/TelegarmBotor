---
name: python-tests-skill
description: Instructions for writing consistent, coherent, and effective Python unit and integration tests using pytest. Covers test structure, naming, fixtures, mocking, parametrize, assertions, error testing, integration patterns (database, API, external services), coverage, running all tests with one command, and anti-patterns. Use this skill whenever writing, reviewing, or refactoring Python tests.
---

# Python Testing with pytest — Unit and Integration

These instructions define how to write, organize, and maintain Python tests using pytest. This covers both unit tests and integration tests. Every test written in this project must follow these rules.

**One command runs everything:**

```bash
pytest
```

Unit tests, integration tests, all in one suite, all from the same `tests/` tree, all configured in `pyproject.toml`. No separate scripts, no separate runners.

---

## 1. Project Test Structure

### Directory Layout

Tests live in a top-level `tests/` directory that mirrors the source structure. Unit and integration tests coexist in the same tree, distinguished by markers — not by separate directories.

```
project/
  src/
    auth/
      service.py
      repository.py
    billing/
      invoice.py
      payment_gateway.py
    utils/
      validators.py
  tests/
    auth/
      test_service.py
      test_repository.py
    billing/
      test_invoice.py
      test_payment_gateway.py
    utils/
      test_validators.py
    conftest.py
```

- Every source directory has a matching directory under `tests/`.
- Every source file `module.py` has a matching test file `test_module.py`.
- A test file may contain both unit tests and integration tests for the same module. Use markers to distinguish them.
- Shared fixtures go in `conftest.py` at the appropriate directory level.
- Never put tests inside the source package. Tests and production code are separate trees.

### conftest.py Hierarchy

pytest discovers `conftest.py` files at every directory level. Use this for fixture scoping:

- `tests/conftest.py` — project-wide fixtures (database connections, app factory, test client, test database setup/teardown)
- `tests/auth/conftest.py` — auth-specific fixtures (fake users, tokens, auth headers)
- `tests/billing/conftest.py` — billing-specific fixtures (sample invoices, mock payment gateway)

Rules for `conftest.py`:

- Only define fixtures. No test functions, no helper classes, no constants.
- Keep each `conftest.py` focused on its directory's domain.
- Never import from one `conftest.py` into another. Let pytest's discovery handle inheritance.
- If a fixture is used across more than one subdirectory, move it up to the nearest common `conftest.py`.

---

## 2. Unit vs. Integration — Definitions and Boundaries

### Unit Tests

A unit test verifies a single function, method, or class in isolation. All external dependencies are mocked or stubbed out.

Characteristics:
- Fast — runs in under 100ms.
- No I/O — no network, no database, no file system (except `tmp_path`).
- Deterministic — same result every time, no matter the environment.
- Isolated — mocking boundaries: patch services, repositories, clients, clocks.

### Integration Tests

An integration test verifies that multiple components work together correctly through real interactions. External systems may be real (local database, test containers) or high-fidelity fakes.

Characteristics:
- Slower — may take seconds per test.
- Real I/O — hits a database, makes HTTP calls to a running test server, reads/writes files.
- Requires setup — database migrations, test data seeding, service startup.
- Still deterministic — uses transactions, cleanup, and isolated test data to avoid flakiness.

### Marking

Every integration test must be explicitly marked:

```python
import pytest

@pytest.mark.integration
def test_create_user_persists_to_database(db_session):
    ...
```

Unit tests do not need a marker — they are the default.

### Running Selectively

```bash
pytest                          # everything — unit + integration
pytest -m "not integration"     # unit tests only (fast feedback)
pytest -m integration           # integration tests only
```

---

## 3. Naming Conventions

### Test Files

- File name: `test_<module_name>.py`
- One test file per source module. Never test multiple modules in one file.

### Test Functions

- Pattern: `test_<function_or_method>_<scenario>_<expected_result>`
- Name reads as a sentence describing behavior.

Good names:

```python
# Unit tests
def test_calculate_total_with_discount_returns_reduced_price():
def test_validate_email_with_empty_string_raises_validation_error():

# Integration tests
def test_create_user_persists_and_retrieves_from_database():
def test_payment_endpoint_charges_card_and_returns_receipt():
```

Bad names:

```python
def test_1():                    # meaningless number
def test_calculate():            # no scenario, no expectation
def test_it_works():             # vague
def test_create_user_test():     # redundant "test" suffix
```

### Test Classes

Use classes only to group related tests for the same unit. Never use classes for shared state.

- Pattern: `Test<ClassName>` or `Test<FunctionName>`
- No `__init__` method. Ever. pytest ignores classes with `__init__`.
- No instance state. Every test method must be independent.

### Fixtures

- Pattern: `<noun>` or `<adjective>_<noun>` describing what the fixture provides.
- Never prefix fixtures with `get_`, `make_`, or `create_` — they are declarations, not actions.

---

## 4. Test Structure — Arrange, Act, Assert

Every test function follows the AAA pattern. Separate the three sections with a blank line.

```python
def test_calculate_total_with_tax_returns_correct_amount():
    # Arrange
    cart = Cart(items=[Item(price=100), Item(price=200)])
    tax_rate = Decimal("0.10")

    # Act
    total = calculate_total(cart, tax_rate=tax_rate)

    # Assert
    assert total == Decimal("330.00")
```

- **Arrange**: Set up inputs, dependencies, and preconditions. Use fixtures for complex setup.
- **Act**: Call the function under test. Exactly one action per test.
- **Assert**: Verify the result. One logical assertion per test (multiple `assert` lines are fine if they verify the same outcome).
- Blank lines between sections are mandatory.
- The `# Arrange / Act / Assert` comments are optional for complex tests, noise for trivial ones.

### One Action Per Test

Each test calls the function under test exactly once:

```python
# BAD — two actions in one test
def test_user_creation_and_retrieval():
    user = create_user(name="Alice")
    retrieved = get_user(user.id)
    assert retrieved.name == "Alice"

# GOOD — split into two tests
def test_create_user_with_valid_name_returns_user():
    user = create_user(name="Alice")
    assert user.name == "Alice"

def test_get_user_with_valid_id_returns_matching_user(saved_user):
    retrieved = get_user(saved_user.id)
    assert retrieved.name == saved_user.name
```

**Exception for integration tests:** An integration test may perform a sequence of steps (create → read → verify) because the integration itself — the full round-trip — is the behavior under test. Keep it to one logical workflow.

```python
@pytest.mark.integration
def test_user_registration_flow_persists_and_retrieves(db_session):
    # Arrange
    user_data = {"name": "Alice", "email": "alice@example.com"}

    # Act
    created = user_service.register(user_data, session=db_session)
    retrieved = user_service.get_by_id(created.id, session=db_session)

    # Assert
    assert retrieved.email == "alice@example.com"
    assert retrieved.id == created.id
```

---

## 5. Fixtures

### When to Use

- Shared setup needed by multiple tests in the same file or directory.
- Complex object construction that would clutter the test body.
- Resources that need teardown (database connections, temporary files, server processes).

### When Not to Use

- Simple values that fit on one line. Inline them directly.
- Setup used by exactly one test. Put it in the arrange section of that test.

### Fixture Scope

```python
@pytest.fixture(scope="function")   # default — runs before each test
@pytest.fixture(scope="class")      # once per test class
@pytest.fixture(scope="module")     # once per test file
@pytest.fixture(scope="session")    # once per entire test run
```

- Default to `function` scope. Each test gets a clean fixture.
- Use `session` scope only for expensive, read-only resources (database engine, app factory).
- Never use `session` or `module` scope for mutable fixtures.

### Teardown with yield

```python
@pytest.fixture
def temp_directory():
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)
```

Code before `yield` is setup. Code after is teardown — runs even if the test fails.

### Factory Fixtures

When tests need variations of the same object:

```python
@pytest.fixture
def make_user():
    created_users = []

    def _make_user(name="Alice", email="alice@example.com", is_active=True):
        user = User(name=name, email=email, is_active=is_active)
        created_users.append(user)
        return user

    yield _make_user

    for user in created_users:
        user.delete()
```

### Fixture Dependencies

Fixtures can depend on other fixtures by declaring them as parameters:

```python
@pytest.fixture
def auth_headers(active_user, valid_token):
    return {"Authorization": f"Bearer {valid_token.value}"}
```

- Keep fixture chains short — no more than 3 levels deep.
- Never create circular dependencies.

---

## 6. Parametrize

Use `@pytest.mark.parametrize` to test multiple inputs through the same logic.

```python
@pytest.mark.parametrize("input_value, expected", [
    ("alice@example.com", True),
    ("bob@domain.co.uk", True),
    ("not-an-email", False),
    ("", False),
    ("@missing-local.com", False),
])
def test_validate_email_returns_expected_result(input_value, expected):
    assert validate_email(input_value) == expected
```

### Rules

- Use descriptive parameter names, not `a`, `b`, `x`, `y`.
- Add `ids` when parameters are not self-explanatory:

```python
@pytest.mark.parametrize("amount, currency, expected", [
    (100, "USD", "$1.00"),
    (100, "EUR", "€1.00"),
    (0, "USD", "$0.00"),
    (-500, "USD", "-$5.00"),
], ids=["positive-usd", "positive-eur", "zero", "negative-usd"])
def test_format_currency_returns_formatted_string(amount, currency, expected):
    assert format_currency(amount, currency) == expected
```

- Never parametrize more than 6 parameters wide.
- Keep parameter lists under 15 cases. Split into grouped tests beyond that.
- Every parametrize must include at least one edge case and one error case.

### Stacking Parametrize

Combine decorators for a cross-product:

```python
@pytest.mark.parametrize("role", ["admin", "editor", "viewer"])
@pytest.mark.parametrize("resource", ["document", "image", "video"])
def test_access_control_checks_role_against_resource(role, resource):
    ...
```

This produces 9 test cases. Use sparingly — cross-products grow fast.

---

## 7. Mocking

Mock external dependencies at the boundary. Never mock the thing you are testing.

### What to Mock

- Network calls (HTTP requests, API clients)
- Database queries (when testing business logic, not repository code)
- File system operations, time/dates, environment variables
- Third-party service SDKs, random number generators

### What Not to Mock

- The function or class under test
- Pure functions with no side effects
- Data structures and value objects — construct real ones
- Deterministic standard library functions

### Patch as a Decorator

```python
@patch("myapp.billing.service.payment_gateway.charge")
def test_process_payment_calls_gateway(mock_charge):
    mock_charge.return_value = PaymentResult(success=True)

    result = process_payment(amount=500, currency="USD")

    mock_charge.assert_called_once_with(amount=500, currency="USD")
    assert result.success is True
```

### Patch as Context Manager

```python
def test_fetch_user_handles_api_timeout():
    with patch("myapp.users.client.http_get") as mock_get:
        mock_get.side_effect = TimeoutError("Connection timed out")
        result = fetch_user(user_id=42)
    assert result is None
```

### monkeypatch for Environment

```python
def test_config_reads_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    config = load_config()
    assert config.database_url == "sqlite:///test.db"
```

### Mocking Rules

- **Patch where used, not where defined.** Patch `myapp.billing.service.gateway`, not `myapp.integrations.gateway`.
- **Always specify return values or side effects.** A bare `Mock()` hides bugs.
- **Use `autospec=True`** to enforce the original's interface:

```python
@patch("myapp.service.repository", autospec=True)
def test_service_calls_repository_save(mock_repo):
    mock_repo.save.return_value = None
    ...
```

- **Never mock more than 3 things per test.** More means the unit has too many collaborators.
- **Assert mock interactions only when the interaction IS the behavior.** Do not verify internal helpers were called — check the return value.
- **Integration tests should mock as little as possible.** The point is to test real interactions. Only mock truly external systems you cannot run locally (third-party payment APIs, email providers).

---

## 8. Testing Exceptions

Use `pytest.raises` as a context manager. Always verify type and message.

```python
def test_withdraw_with_insufficient_funds_raises_error():
    account = Account(balance=100)

    with pytest.raises(InsufficientFundsError) as exc_info:
        account.withdraw(200)

    assert "insufficient funds" in str(exc_info.value).lower()
    assert exc_info.value.balance == 100
```

- Always capture `exc_info` and verify the message or attributes.
- The `with` block must contain only the single call that triggers the exception.
- Use `match` for simple checks: `pytest.raises(ValueError, match="must be positive")`
- To test no exception is raised, just call the function — if it raises, the test fails naturally.

### Testing Warnings

```python
def test_deprecated_function_emits_warning():
    with pytest.warns(DeprecationWarning, match="use new_function instead"):
        old_function()
```

---

## 9. Integration Tests — Database

### Transactional Isolation

Every integration test that touches the database runs inside a transaction that is rolled back after the test. This keeps the database clean without expensive setup/teardown.

```python
# tests/conftest.py

@pytest.fixture(scope="session")
def db_engine():
    """Create the test database engine once per session."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Provide a transactional database session that rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

### Rules for Database Integration Tests

- Never commit inside a test. The fixture manages the transaction.
- Never depend on data from another test. Each test creates its own data.
- Use factory fixtures to build test data:

```python
@pytest.fixture
def make_invoice(db_session):
    def _make_invoice(amount=1000, status="pending"):
        invoice = Invoice(amount=amount, status=status)
        db_session.add(invoice)
        db_session.flush()  # assigns ID without committing
        return invoice
    return _make_invoice

@pytest.mark.integration
def test_get_pending_invoices_returns_only_pending(db_session, make_invoice):
    make_invoice(status="pending")
    make_invoice(status="pending")
    make_invoice(status="paid")

    result = invoice_repo.get_pending(session=db_session)

    assert len(result) == 2
    assert all(inv.status == "pending" for inv in result)
```

- Use `session.flush()` instead of `session.commit()` to assign IDs and enforce constraints without persisting.
- Use an in-memory SQLite database for speed when the schema is compatible. Use a containerized PostgreSQL/MySQL when you need dialect-specific behavior.
- Run migrations in the `db_engine` session fixture, not in each test.

---

## 10. Integration Tests — HTTP APIs

### Testing with a Test Client

For web frameworks (FastAPI, Flask, Django), use the framework's test client. The client makes real HTTP requests to the application but without starting a network server.

```python
# tests/conftest.py (FastAPI example)

@pytest.fixture(scope="session")
def app():
    """Create the application instance."""
    from myapp.main import create_app
    return create_app(settings=test_settings)

@pytest.fixture
def client(app, db_session):
    """Provide a test client with a transactional database session."""
    def override_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
```

### Testing Endpoints

```python
@pytest.mark.integration
def test_create_item_returns_201_with_item_data(client, auth_headers):
    response = client.post(
        "/api/items",
        json={"name": "Widget", "price": 9.99},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Widget"
    assert body["price"] == 9.99
    assert "id" in body
```

### Rules for API Integration Tests

- Always assert the status code first.
- Verify the response body structure and key values, not the exact JSON string.
- Test authentication: missing token → 401, wrong role → 403, valid token → 2xx.
- Test validation: missing fields → 422, bad types → 422, valid → 2xx.
- Test not-found cases: nonexistent ID → 404.
- Use the `auth_headers` pattern to avoid duplicating token logic in every test.
- Never hardcode IDs. Create resources in the test and use the returned IDs.

---

## 11. Integration Tests — External Services

### Services You Cannot Run Locally

Some external dependencies cannot be spun up locally (payment processors, email providers, third-party APIs). For these, use recorded responses or high-fidelity fakes.

### Responses (VCR Pattern)

Use `pytest-recording` or `responses` to record and replay HTTP interactions:

```python
import responses

@responses.activate
@pytest.mark.integration
def test_fetch_weather_returns_temperature():
    responses.add(
        responses.GET,
        "https://api.weather.com/v1/current",
        json={"temperature": 22.5, "unit": "celsius"},
        status=200,
    )

    result = weather_service.get_current_temperature(city="Paris")

    assert result == 22.5
```

### Services You Can Run Locally

Use containers for databases, message brokers, caches, and other infrastructure:

```python
# tests/conftest.py — using testcontainers

@pytest.fixture(scope="session")
def postgres_url():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres.get_connection_url()
```

### Rules for External Service Tests

- Never hit real production APIs in tests.
- Recorded responses must be checked into version control and kept up to date.
- If a service offers a sandbox/test mode (Stripe test keys, SendGrid sandbox), use it.
- Container-based fixtures use `session` scope — starting a container per test is too slow.
- All container setup belongs in `conftest.py`, never in individual test files.

---

## 12. Assertion Patterns

### Comparing Values

```python
assert result == expected
assert result is None
assert result is not None
assert result is True
assert isinstance(result, ExpectedType)
```

### Comparing Collections

```python
assert sorted(result) == sorted(expected)    # order-independent
assert set(result) == set(expected)          # unique elements
assert len(result) == 5
assert item in result
assert all(x > 0 for x in result)
```

### Comparing Floats

```python
assert result == pytest.approx(expected, rel=1e-6)
assert result == pytest.approx(3.14159, abs=1e-4)
```

### Comparing API Responses

```python
body = response.json()
assert body["id"] is not None               # exists but don't hardcode
assert body["name"] == "Widget"
assert body["created_at"]                    # truthy, don't match exact time
assert len(body["items"]) == 3
```

### Rules

- Never use `assertEqual`, `assertTrue`, `assertIn`, or other unittest assertions. Use plain `assert`.
- Add custom messages only when failure output is ambiguous:

```python
assert user.is_active, f"Expected user {user.id} to be active after registration"
```

---

## 13. Markers and Test Selection

### Built-in Markers

```python
@pytest.mark.skip(reason="Waiting for upstream fix #1234")
def test_broken_feature(): ...

@pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific paths")
def test_unix_paths(): ...

@pytest.mark.xfail(reason="Known bug #5678, fix in progress")
def test_known_bug(): ...
```

### Custom Markers

Register in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests that hit real infrastructure (database, HTTP, files)",
    "slow: marks tests that take more than 5 seconds",
    "e2e: marks end-to-end tests spanning the full stack",
]
```

### Running by Category

```bash
pytest                         # all tests — unit + integration
pytest -m "not integration"    # unit only (fast feedback loop)
pytest -m integration          # integration only
pytest -m "not slow"           # skip slow tests
pytest -m "integration and not slow"  # fast integration tests
```

### Rules

- Every `skip` must have a `reason` with a ticket number.
- Use `xfail` for known bugs, not `skip`. It still runs the test and alerts when fixed.
- Never use markers to hide flaky tests. Fix the flakiness.
- Every integration test must carry `@pytest.mark.integration`.

---

## 14. Test Configuration — One Command

All configuration lives in `pyproject.toml`. Running `pytest` with no arguments executes the full suite — unit and integration together.

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
python_classes = ["Test*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-branch",
]
filterwarnings = ["error", "ignore::DeprecationWarning:third_party_lib.*"]
markers = [
    "integration: marks tests that hit real infrastructure (database, HTTP, files)",
    "slow: marks tests that take more than 5 seconds",
    "e2e: marks end-to-end tests spanning the full stack",
]
asyncio_mode = "auto"
```

- `--strict-markers` — typos in marker names become errors.
- `--strict-config` — invalid config keys become errors.
- `-ra` — show summary of all non-passing tests.
- `filterwarnings = ["error"]` — warnings become errors. Ignore specific third-party ones explicitly.
- Never use `--disable-warnings`.
- `--cov=src` and `--cov-branch` — coverage runs with every test invocation.

### CI Pipeline

The CI pipeline runs the exact same command:

```bash
pytest
```

No special scripts, no different configuration. Local and CI must behave identically. If integration tests require infrastructure (database container), the CI pipeline provisions it before running `pytest`.

---

## 15. Coverage

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/migrations/*", "*/__main__.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```

- 80% minimum coverage. Branch coverage is mandatory.
- Never use `# pragma: no cover` to inflate numbers. Only for genuinely untestable code (abstract methods, type-checking blocks).
- Coverage measures execution, not verification. A line that runs but is never asserted on is not tested.
- Integration tests contribute to coverage. A database round-trip that exercises the repository code counts.

---

## 16. Testing Async Code

```python
@pytest.mark.asyncio
async def test_fetch_user_returns_user_data():
    user = await fetch_user(user_id=1)
    assert user.name == "Alice"
```

With `asyncio_mode = "auto"` in the config, `async def test_*` functions run as async tests automatically.

### Async Fixtures

```python
@pytest.fixture
async def async_client(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

### Async Integration Tests

```python
@pytest.mark.integration
async def test_create_and_retrieve_user(async_client):
    create_response = await async_client.post(
        "/api/users",
        json={"name": "Alice", "email": "alice@example.com"},
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    get_response = await async_client.get(f"/api/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Alice"
```

- Never call `asyncio.run()` inside a test. Let pytest-asyncio handle the loop.
- Never create your own event loop.

---

## 17. Anti-Patterns

### Testing Implementation Instead of Behavior

```python
# BAD — asserts internal calls, not observable behavior
def test_save_user_calls_validate_then_persist(mock_validate, mock_persist):
    save_user(user)
    mock_validate.assert_called_once()
    mock_persist.assert_called_once()
```

### Shared Mutable State Between Tests

```python
# BAD — test order dependency
users_list = []

def test_add_user():
    users_list.append(User(name="Alice"))
    assert len(users_list) == 1

def test_remove_user():
    users_list.pop()
    assert len(users_list) == 0
```

### Mocking Everything in Integration Tests

```python
# BAD — this is a unit test pretending to be an integration test
@pytest.mark.integration
@patch("myapp.repo.save")
@patch("myapp.repo.get_all")
@patch("myapp.service.validate")
def test_workflow(mock_validate, mock_get_all, mock_save):
    ...
```

If you are mocking the database and the service layer, you are writing a unit test. Mark it accordingly.

### Hitting Real External APIs in Tests

```python
# BAD — flaky, slow, costs money, exposes credentials
@pytest.mark.integration
def test_charge_customer():
    stripe.api_key = "sk_live_REAL_KEY"
    result = stripe.Charge.create(amount=1000, currency="usd")
    ...
```

Use sandbox keys, recorded responses, or fakes instead.

### Other Anti-Patterns

- **Catching all exceptions**: `except Exception: pass` hides real failures.
- **Giant test functions**: Over 20 lines means it tests too much — split it.
- **Testing third-party code**: Trust `json.loads` works. Test your code that uses it.
- **Asserting on mocks without behavior**: Only assert mock calls when the call IS the behavior.
- **Using `time.sleep`**: Use polling with timeout, mock time, or async patterns instead.
- **Database tests without rollback**: Every test that writes to a database must clean up after itself. Transactional rollback is the standard pattern.
- **Hardcoded ports or URLs**: Use fixtures and configuration. Hardcoded `localhost:5432` will break in CI.

---

## 18. Test Performance

- Full unit suite must run in under 60 seconds. Individual unit tests under 100ms.
- Integration suite may take longer, but individual tests should stay under 5 seconds.
- `pytest --durations=10` finds the slowest tests.
- Real DB operations → use in-memory databases or transactional rollback, not full DB recreate per test.
- Real HTTP calls to external services → mock or record them.
- `time.sleep` → never in tests. Use polling with timeout or mock time.

### Parallelization

```bash
pytest -n auto  # all CPU cores
pytest -n 4     # 4 workers
```

For parallel safety:
- No shared mutable state.
- No hardcoded ports — use dynamic port allocation or framework test clients.
- Use UUIDs and `tmp_path` for file-based tests.
- Database tests need per-worker databases or transaction isolation.

---

## 19. Fixture Patterns Reference

```python
# Temporary file
@pytest.fixture
def config_file(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("database:\n  host: localhost\n  port: 5432\n")
    return config

# Database session with rollback
@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# Freezing time
from freezegun import freeze_time

@freeze_time("2025-01-15 12:00:00")
def test_invoice_due_date_is_30_days_from_creation():
    invoice = create_invoice()
    assert invoice.due_date == date(2025, 2, 14)

# Capturing logs
def test_retry_logs_warning_on_failure(caplog):
    with caplog.at_level(logging.WARNING):
        retry_operation(failing_function, max_retries=3)
    assert "Retry attempt 3 failed" in caplog.text

# Capturing stdout
def test_cli_prints_help(capsys):
    run_cli(["--help"])
    captured = capsys.readouterr()
    assert "Usage:" in captured.out

# Authenticated test client
@pytest.fixture
def auth_headers(make_user, client):
    user = make_user(email="test@example.com")
    response = client.post("/api/auth/login", json={
        "email": user.email,
        "password": "TestPassword1!",
    })
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}

# Testcontainers database
@pytest.fixture(scope="session")
def postgres_url():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres.get_connection_url()
```

---

## 20. Checklist — Before Committing Tests

- Every test has a descriptive name that reads as a sentence.
- Every test follows Arrange-Act-Assert with blank line separators.
- Every test is independent — passes in isolation and in any order.
- Every integration test is marked with `@pytest.mark.integration`.
- `pytest` with no arguments runs the full suite (unit + integration) and passes.
- `pytest -m "not integration"` runs fast and passes (unit-only feedback loop).
- No `time.sleep`, no hardcoded delays, no flaky timing.
- No file-existence checks instead of behavior checks.
- No commented-out code or TODO comments.
- Mocks use `autospec=True` or `spec=True`.
- No more than 3 mocks per test.
- Integration tests mock as little as possible — only truly external services.
- `pytest.raises` blocks contain exactly one statement.
- Database integration tests use transactional rollback.
- Coverage at or above 80% with branch coverage enabled.
- `pytest --strict-markers` passes with no warnings.
- Full test suite runs with one command: `pytest`.
