---
name: python-pep8-skill
description: PEP 8 style guide enforcement for Python code. Covers formatting, naming, imports, whitespace, comments, docstrings, type hints, and tooling configuration. Use this skill whenever writing, reviewing, or refactoring Python code to ensure consistent style across the project.
---

# Python Style Guide — PEP 8

These instructions define the code style for all Python code in this project. Every Python file must follow these rules. They are based on PEP 8, extended with project-specific conventions where PEP 8 is silent or ambiguous.

**Tooling enforces most of this automatically:**

```bash
ruff check .          # lint
ruff format .         # format
mypy .                # type check
```

Do not rely on memory — configure the tools, run them, and let them catch violations.

---

## 1. Formatting — The Non-Negotiables

### Line Length

- Maximum 88 characters per line (Black/Ruff default).
- URLs in comments and docstrings may exceed the limit rather than being broken mid-URL.
- Never break a line just to stay under the limit if the result is less readable than the original.

### Indentation

- 4 spaces per level. No tabs. Ever.
- Continuation lines align with the opening delimiter or use a hanging indent with 4 extra spaces:

```python
# Aligned with opening delimiter
result = some_function(first_argument, second_argument,
                       third_argument, fourth_argument)

# Hanging indent — preferred for long signatures
result = some_function(
    first_argument,
    second_argument,
    third_argument,
    fourth_argument,
)
```

- Always use trailing commas in multi-line collections, function arguments, and function parameters. This produces cleaner diffs:

```python
# Good — trailing comma
config = {
    "host": "localhost",
    "port": 5432,
    "database": "myapp",
}

# Bad — no trailing comma
config = {
    "host": "localhost",
    "port": 5432,
    "database": "myapp"
}
```

### Blank Lines

- **2 blank lines** before and after top-level definitions (functions, classes).
- **1 blank line** between methods inside a class.
- **1 blank line** to separate logical sections within a function (sparingly).
- No blank line after a function's docstring.
- No blank line after `if`, `for`, `while`, `with`, `try` headers.
- No trailing blank lines at the end of a file. End with exactly one newline.

### Whitespace

**Spaces around operators:**

```python
# Good
x = 1
y = x + 2
result = value * (base + offset)
is_valid = name != "" and age >= 18

# Bad
x=1
y = x +2
result = value *( base + offset)
```

**No spaces inside brackets:**

```python
# Good
items[0]
data["key"]
func(arg1, arg2)

# Bad
items[ 0 ]
data[ "key" ]
func( arg1, arg2 )
```

**No spaces around `=` in keyword arguments or default values:**

```python
# Good
def connect(host="localhost", port=5432, timeout=30):
    client.send(data=payload, retry=True)

# Bad
def connect(host = "localhost", port = 5432, timeout = 30):
    client.send(data = payload, retry = True)
```

**Spaces around `=` in annotated assignments:**

```python
# Good — space around = when annotation is present
count: int = 0
name: str = "default"

# Good — no annotation, no space needed beyond normal
count = 0
```

**No spaces before colons in slices:**

```python
# Good
items[1:3]
items[::2]
items[1:10:2]

# Bad
items[1 : 3]
items[ :: 2]
```

---

## 2. Imports

### Order

Imports are grouped in this exact order, separated by a blank line:

1. Standard library (`os`, `sys`, `pathlib`, `typing`)
2. Third-party packages (`fastapi`, `sqlalchemy`, `pydantic`)
3. Local/project imports (`from myapp.models import User`)

```python
import os
import sys
from pathlib import Path

import httpx
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from myapp.config import settings
from myapp.models import User, Invoice
```

### Rules

- One `import` per line for module imports:

```python
# Good
import os
import sys

# Bad
import os, sys
```

- `from` imports may have multiple names on one line if they fit:

```python
from typing import Any, Optional, Union
```

- If a `from` import exceeds the line length, use parentheses with one name per line:

```python
from myapp.services.billing import (
    calculate_total,
    generate_invoice,
    process_refund,
    validate_payment,
)
```

- Never use wildcard imports: `from module import *`
- Never use relative imports in application code. Relative imports are acceptable only inside packages that are designed to be redistributable.
- Remove unused imports. The linter will catch them — never ignore the warning.
- Import modules, not individual objects, when the module name adds clarity:

```python
# Good — json.loads is clearer than a bare loads
import json
data = json.loads(payload)

# Good — no ambiguity, direct import is fine
from pathlib import Path
config_path = Path("config.yaml")
```

### Conditional Imports

Use `TYPE_CHECKING` for imports needed only by type checkers:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myapp.models import User
```

This avoids circular imports and runtime overhead for type-only dependencies.

---

## 3. Naming Conventions

### Summary Table

- **Modules and packages**: `lowercase` or `lower_case` (`utils.py`, `payment_gateway.py`)
- **Functions and variables**: `snake_case` (`calculate_total`, `user_count`)
- **Constants**: `UPPER_SNAKE_CASE` (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Classes**: `PascalCase` (`UserService`, `InvoiceRepository`)
- **Type variables**: `PascalCase`, short (`T`, `K`, `V`, `ItemT`)
- **Private members**: prefix with single underscore (`_validate_input`, `_cache`)
- **Name-mangling (rare)**: prefix with double underscore (`__secret`) — only to avoid subclass conflicts
- **Dunder methods**: `__init__`, `__repr__`, `__eq__` — never invent your own

### Detailed Rules

**Functions start with a verb:**

```python
# Good
def calculate_tax(amount: Decimal, rate: Decimal) -> Decimal: ...
def validate_email(email: str) -> bool: ...
def fetch_user_by_id(user_id: int) -> User: ...
def send_notification(user: User, message: str) -> None: ...

# Bad
def tax(amount, rate): ...        # noun, not a verb
def email_check(email): ...       # ambiguous
def user(user_id): ...            # noun
```

**Booleans read as yes/no questions:**

```python
# Good
is_active = True
has_permission = user.role == "admin"
can_edit = document.owner_id == current_user.id
should_retry = attempt < MAX_RETRIES

# Bad
active = True           # ambiguous — is it a noun or adjective?
permission = True       # noun, not a question
retry = True            # verb, not a question
```

**Collections use plural nouns:**

```python
# Good
users = get_all_users()
invoices: list[Invoice] = []
pending_items = queue.get_pending()

# Bad
user_list = get_all_users()      # redundant "list"
invoice = []                     # singular for a collection
```

**Avoid abbreviations unless universally understood:**

```python
# Good — universally understood
user_id = 42
http_client = httpx.Client()
url = "https://example.com"
config = load_config()

# Bad — cryptic abbreviations
usr_id = 42
clnt = httpx.Client()
cfg = load_config()
req = build_request()
```

**Avoid generic names:**

```python
# Bad
data = fetch_something()
result = process(data)
info = get_info()
temp = calculate()
items = load()

# Good
user_profile = fetch_user_profile(user_id)
monthly_total = calculate_monthly_revenue(transactions)
server_config = load_server_config()
```

**Single-character variables only in narrow scopes:**

```python
# Acceptable — list comprehension, lambda, short loop
squares = [x ** 2 for x in range(10)]
points = sorted(points, key=lambda p: p.distance)

# Not acceptable — function body
def process(d):    # what is d?
    r = calculate(d)
    return r
```

---

## 4. Functions and Methods

### Length

- Maximum 40 lines per function (including docstring).
- If a function exceeds 40 lines, it is doing too much. Extract helpers.

### Parameters

- Maximum 3 positional parameters. Use keyword-only arguments or a data class for more:

```python
# Good — 3 or fewer positional params
def create_user(name: str, email: str, role: str = "viewer") -> User: ...

# Good — keyword-only for many params (note the * separator)
def send_email(
    *,
    to: str,
    subject: str,
    body: str,
    cc: list[str] | None = None,
    reply_to: str | None = None,
) -> None: ...

# Good — data class for complex input
@dataclass
class ConnectionConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 5

def connect(config: ConnectionConfig) -> Connection: ...
```

### Return Early

Use guard clauses to avoid deep nesting:

```python
# Good — guard clauses
def process_order(order: Order) -> Receipt:
    if order.is_cancelled:
        raise OrderCancelledError(order.id)
    if not order.items:
        raise EmptyOrderError(order.id)
    if order.total <= 0:
        raise InvalidTotalError(order.total)

    return _charge_and_generate_receipt(order)

# Bad — deeply nested
def process_order(order: Order) -> Receipt:
    if not order.is_cancelled:
        if order.items:
            if order.total > 0:
                return _charge_and_generate_receipt(order)
            else:
                raise InvalidTotalError(order.total)
        else:
            raise EmptyOrderError(order.id)
    else:
        raise OrderCancelledError(order.id)
```

### No Boolean Flags

Never use a boolean parameter to toggle behavior:

```python
# Bad
def get_users(include_inactive: bool = False) -> list[User]: ...

# Good — two functions with clear intent
def get_active_users() -> list[User]: ...
def get_all_users() -> list[User]: ...
```

### Nesting Limit

Maximum 3 levels of indentation inside a function. Flatten with early returns, comprehensions, or extracted helpers.

---

## 5. Classes

### Structure

Order members consistently within a class:

1. Class-level constants
2. `__init__`
3. `__repr__`, `__str__`, `__eq__`, and other dunder methods
4. Properties (`@property`)
5. Public methods
6. Private methods (prefixed with `_`)

```python
class Invoice:
    MAX_LINE_ITEMS = 100

    def __init__(self, customer_id: int, currency: str = "USD") -> None:
        self.customer_id = customer_id
        self.currency = currency
        self._line_items: list[LineItem] = []

    def __repr__(self) -> str:
        return f"Invoice(customer_id={self.customer_id}, items={len(self._line_items)})"

    @property
    def total(self) -> Decimal:
        return sum(item.amount for item in self._line_items)

    def add_item(self, description: str, amount: Decimal) -> None:
        if len(self._line_items) >= self.MAX_LINE_ITEMS:
            raise InvoiceLimitError(self.MAX_LINE_ITEMS)
        self._line_items.append(LineItem(description=description, amount=amount))

    def _validate_currency(self) -> None:
        if self.currency not in SUPPORTED_CURRENCIES:
            raise UnsupportedCurrencyError(self.currency)
```

### Rules

- Prefer `dataclass` or `NamedTuple` for data-holding classes with no behavior.
- Never use a class when a function will do. A class with only `__init__` and one other method should be a function.
- Keep inheritance shallow — prefer composition.
- Always define `__repr__` for classes that will be logged or debugged.

---

## 6. Type Hints

### Every Public Function Must Be Annotated

```python
def calculate_total(items: list[Item], tax_rate: Decimal) -> Decimal: ...
def fetch_user(user_id: int) -> User | None: ...
def send_email(to: str, subject: str, body: str) -> None: ...
```

### Modern Syntax (Python 3.10+)

Use the modern union syntax and built-in generics:

```python
# Good — modern
def process(value: int | str) -> list[str]: ...
def find_user(user_id: int) -> User | None: ...
config: dict[str, Any] = {}

# Avoid — legacy
def process(value: Union[int, str]) -> List[str]: ...
def find_user(user_id: int) -> Optional[User]: ...
config: Dict[str, Any] = {}
```

If supporting Python < 3.10, add `from __future__ import annotations` at the top of the file.

### Type Alias for Complex Types

```python
# Good — named alias for clarity
type UserId = int
type Headers = dict[str, str]
type Middleware = Callable[[Request], Awaitable[Response]]

# Bad — inline complex types repeated everywhere
def fetch(user_id: int, headers: dict[str, str]) -> ...: ...
def send(user_id: int, headers: dict[str, str]) -> ...: ...
```

### Rules

- Annotate all function parameters and return types.
- Annotate class attributes in `__init__` or as class-level annotations.
- Private helpers and local variables do not need annotations unless the type is non-obvious.
- Never use `Any` as a default. Use it only when genuinely any type is valid.
- Use `TypeVar` for generic functions. Use `Protocol` for structural subtyping instead of ABCs when the only purpose is type checking.
- Return `None` explicitly in the annotation: `-> None`, not omitting the return type.

---

## 7. Strings

### Prefer f-strings

```python
# Good
message = f"User {user.name} has {len(items)} items"
log.info(f"Processing order {order_id}")

# Avoid
message = "User {} has {} items".format(user.name, len(items))
message = "User %s has %d items" % (user.name, len(items))
```

### Quote Style

- Use double quotes `"` for strings. Be consistent project-wide.
- Use single quotes `'` only inside f-strings to avoid escaping: `f"User '{name}' not found"`
- Use triple double quotes `"""` for docstrings and multi-line strings.

### Raw Strings for Regex

```python
pattern = r"\d{3}-\d{4}"
```

### Long Strings

Use implicit concatenation for long strings:

```python
message = (
    f"The operation failed because the user {user.name} "
    f"does not have permission to access resource {resource.id} "
    f"in workspace {workspace.name}."
)
```

Never use backslash continuation `\` for strings. Use parentheses.

---

## 8. Comments and Docstrings

### Comments

- Comments explain **why**, never **what**. The code tells you what.
- If a comment restates the code, delete it.
- Place comments on their own line above the code, not inline:

```python
# Good — explains a non-obvious decision
# Rate limit is 100/min per Stripe docs, use 90 to leave headroom
RATE_LIMIT = 90

# Bad — restates the code
x = x + 1  # increment x
```

### Docstrings

Every public module, class, function, and method must have a docstring.

Use Google-style docstrings:

```python
def calculate_shipping(
    weight: Decimal,
    destination: str,
    express: bool = False,
) -> Decimal:
    """Calculate shipping cost based on weight and destination.

    Applies express surcharge if requested. Rates are pulled from
    the shipping_rates configuration.

    Args:
        weight: Package weight in kilograms. Must be positive.
        destination: ISO 3166-1 alpha-2 country code.
        express: Whether to use express shipping. Defaults to False.

    Returns:
        Shipping cost in USD as a Decimal.

    Raises:
        InvalidWeightError: If weight is zero or negative.
        UnsupportedDestinationError: If the country code is not in the rate table.
    """
```

### Docstring Rules

- First line is a concise summary ending with a period.
- Blank line between the summary and the body (if there is a body).
- Document all parameters, return values, and raised exceptions.
- Use Google style (`Args:`, `Returns:`, `Raises:`), not Sphinx `:param:` style.
- Class docstrings describe the class purpose, not `__init__` parameters. Document `__init__` separately if it is complex.
- One-liner docstrings stay on one line: `"""Return the user's full name."""`

---

## 9. Error Handling

### Use Specific Exceptions

```python
# Good
except FileNotFoundError:
    log.warning(f"Config file {path} not found, using defaults")
    return default_config

except httpx.TimeoutException:
    log.error(f"Request to {url} timed out after {timeout}s")
    raise ServiceUnavailableError(url) from None

# Bad
except Exception:
    pass
```

### Rules

- Never use bare `except:`. Always specify the exception type.
- Never use `except Exception: pass`. Handle the error or let it propagate.
- Use `raise ... from original` to chain exceptions and preserve context:

```python
try:
    data = json.loads(raw_input)
except json.JSONDecodeError as exc:
    raise InvalidPayloadError(f"Malformed JSON: {raw_input[:100]}") from exc
```

- Use `raise ... from None` to suppress the chain when the original is noise.
- Define custom exception classes for domain-specific errors. Inherit from `Exception`, not `BaseException`.
- Custom exceptions live in an `exceptions.py` module within the relevant package.

### Try/Except Scope

Keep the `try` block as narrow as possible:

```python
# Good — only the risky call is inside try
try:
    response = client.get(url)
except httpx.ConnectError:
    raise ServiceUnavailableError(url)

data = response.json()
validate(data)

# Bad — too much inside try
try:
    response = client.get(url)
    data = response.json()
    validate(data)
    process(data)
except Exception:
    log.error("Something failed")
```

---

## 10. Collections and Comprehensions

### Prefer Comprehensions Over map/filter

```python
# Good
names = [user.name for user in users if user.is_active]
lookup = {item.id: item for item in items}
unique_tags = {tag for article in articles for tag in article.tags}

# Avoid
names = list(map(lambda u: u.name, filter(lambda u: u.is_active, users)))
```

### Rules

- Keep comprehensions to one line when possible. Two lines (with a line break after `for` or `if`) is acceptable.
- If a comprehension exceeds two lines or has nested logic, use a regular `for` loop.
- Never nest more than two levels of comprehension.
- Use `dict.get(key, default)` instead of checking `if key in dict`.
- Use `collections.defaultdict` instead of manually checking and initializing keys.

### Unpacking

```python
# Good
first, *rest = items
name, email = user_tuple
for key, value in config.items():
    ...

# Good — ignore values with _
_, _, third = coordinates
```

---

## 11. Comparisons and Booleans

### Identity vs. Equality

```python
# Good — identity check for singletons
if value is None:
if value is not None:
if value is True:

# Bad — equality check for singletons
if value == None:
if value != None:
```

### Truthiness

Use implicit truthiness for collections and strings:

```python
# Good
if items:              # non-empty
if not items:          # empty
if name:               # non-empty string
if not errors:         # no errors

# Bad
if len(items) > 0:
if len(items) == 0:
if name != "":
if len(errors) == 0:
```

### Chained Comparisons

```python
# Good
if 0 < age < 120:
if start <= value <= end:

# Bad
if age > 0 and age < 120:
```

### Negation

Avoid double negatives:

```python
# Good
if is_enabled:
if not is_empty:

# Bad
if not is_disabled:
if not is_not_empty:
```

---

## 12. Context Managers

Use `with` for all resource management:

```python
# Good
with open(path) as f:
    data = f.read()

with db.session() as session:
    session.add(user)
    session.commit()

# Bad — manual resource management
f = open(path)
data = f.read()
f.close()
```

### Multiple Context Managers

```python
# Good — parenthesized (Python 3.10+)
with (
    open(input_path) as source,
    open(output_path, "w") as dest,
):
    dest.write(source.read())
```

---

## 13. Pathlib Over os.path

Always use `pathlib.Path` instead of `os.path`:

```python
# Good
from pathlib import Path

config_path = Path("config") / "settings.yaml"
if config_path.exists():
    content = config_path.read_text()

# Bad
import os
config_path = os.path.join("config", "settings.yaml")
if os.path.exists(config_path):
    with open(config_path) as f:
        content = f.read()
```

---

## 14. Constants

- Define at module level in `UPPER_SNAKE_CASE`.
- Group related constants in a dedicated module (`constants.py`) or at the top of the module that uses them.
- Never use magic numbers or strings inline:

```python
# Good
MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 30
SUPPORTED_CURRENCIES = frozenset({"USD", "EUR", "GBP"})

retry(max_attempts=MAX_RETRIES, timeout=DEFAULT_TIMEOUT_SECONDS)

# Bad
retry(max_attempts=3, timeout=30)
```

- Use `Enum` for related constants that represent choices:

```python
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
```

---

## 15. Tooling Configuration

All tools are configured in `pyproject.toml`. No separate config files.

### Ruff (Linter and Formatter)

```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort (import sorting)
    "N",     # pep8-naming
    "UP",    # pyupgrade (modern syntax)
    "B",     # bugbear (common bugs)
    "SIM",   # simplify
    "RUF",   # ruff-specific rules
    "S",     # bandit (security)
    "A",     # builtins shadowing
    "C4",    # comprehension improvements
    "DTZ",   # datetime timezone
    "T20",   # print statements
    "PT",    # pytest style
    "RET",   # return statements
    "ARG",   # unused arguments
]
ignore = []

[tool.ruff.lint.isort]
known-first-party = ["myapp"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Mypy (Type Checker)

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = ["third_party_lib.*"]
ignore_missing_imports = true
```

### Running

```bash
ruff check .                  # lint (find issues)
ruff check . --fix            # lint and auto-fix
ruff format .                 # format
ruff format . --check         # check formatting without changing files
mypy .                        # type check
```

- Run all three before every commit.
- CI runs the same commands. No difference between local and CI.
- Never use `# noqa` without specifying the exact rule: `# noqa: E501` is acceptable, `# noqa` alone is not.
- Never use `# type: ignore` without specifying the error code: `# type: ignore[arg-type]` is acceptable.

---

## 16. Project Layout

```
project/
  src/
    myapp/
      __init__.py
      config.py
      exceptions.py
      models/
        __init__.py
        user.py
        invoice.py
      services/
        __init__.py
        auth.py
        billing.py
      repositories/
        __init__.py
        user_repo.py
        invoice_repo.py
      api/
        __init__.py
        routes/
          __init__.py
          auth.py
          billing.py
      utils/
        __init__.py
        validators.py
        formatters.py
  tests/
    ...
  pyproject.toml
```

- `src/` layout with a single top-level package.
- One module = one responsibility. The file name says what it contains.
- `__init__.py` files are empty or contain only public API re-exports.
- Group by domain (auth, billing) not by type (models, views, serializers).
- `exceptions.py` in each package for domain-specific errors.
- `config.py` at the package root for settings and environment parsing.

---

## 17. Checklist — Before Committing Python Code

- `ruff check .` passes with no errors or warnings.
- `ruff format . --check` passes (code is formatted).
- `mypy .` passes with no errors.
- All public functions, classes, and modules have docstrings.
- All function signatures have complete type annotations.
- No bare `except:` or `except Exception: pass`.
- No unused imports, variables, or arguments.
- No magic numbers or strings — all are named constants.
- No functions longer than 40 lines.
- No nesting deeper than 3 levels.
- Names follow conventions: `snake_case` functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants.
- Imports are ordered: stdlib → third-party → local, with blank line separators.
- f-strings used for all string formatting.
- `pathlib.Path` used instead of `os.path`.
- `with` statements used for all resource management.