# Flask API Design — Best Practices

These instructions define how to design, implement, and maintain production-quality REST APIs with Flask. Every section is actionable and applies to new projects and existing codebases alike.

**One command runs the app:**

```bash
flask run           # or: python -m flask run
```

---

## 1. Project Structure

### Recommended Layout

```
my_api/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration classes
│   ├── extensions.py        # Flask extensions (db, cache, etc.)
│   ├── exceptions.py        # Custom exceptions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── product.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py          # Request/response schemas
│   │   └── product.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py  # v1 Blueprint registration
│   │   │   ├── users.py     # /api/v1/users routes
│   │   │   └── products.py
│   │   └── v2/
│   │       ├── __init__.py
│   │       └── users.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py  # Business logic layer
│   │   └── email_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user_repository.py  # Data access layer
│   └── utils/
│       ├── __init__.py
│       ├── auth.py
│       └── pagination.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_services.py
│   │   └── test_models.py
│   └── integration/
│       ├── test_users.py
│       └── test_products.py
├── migrations/              # Flask-Migrate migrations
├── .env.example
├── .env
├── pyproject.toml
├── requirements.txt
└── wsgi.py                  # Production entry point
```

### Application Factory Pattern

```python
# app/__init__.py
from flask import Flask

from app.config import config_by_name
from app.extensions import db, migrate, cache, limiter
from app.api.v1 import api_v1_blueprint
from app.api.v2 import api_v2_blueprint


def create_app(config_name: str = "development") -> Flask:
    """
    Application factory. Creates and configures the Flask app.

    Args:
        config_name: One of 'development', 'testing', or 'production'.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    _register_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_shell_context(app)

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    limiter.init_app(app)


def _register_blueprints(app: Flask) -> None:
    app.register_blueprint(api_v1_blueprint, url_prefix="/api/v1")
    app.register_blueprint(api_v2_blueprint, url_prefix="/api/v2")


def _register_error_handlers(app: Flask) -> None:
    from app.exceptions import register_error_handlers
    register_error_handlers(app)


def _register_shell_context(app: Flask) -> None:
    from app.models.user import User
    from app.extensions import db

    @app.shell_context_processor
    def make_shell_context() -> dict:
        return {"db": db, "User": User}
```

---

## 2. Configuration

### Config Classes

```python
# app/config.py
import os
from datetime import timedelta


class BaseConfig:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    JSON_SORT_KEYS: bool = False
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=30)

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Rate Limiting
    RATELIMIT_DEFAULT: str = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI: str = os.getenv("REDIS_URL", "memory://")


class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", "sqlite:///dev.db"
    )
    SQLALCHEMY_ECHO: bool = True


class TestingConfig(BaseConfig):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=5)
    RATELIMIT_ENABLED: bool = False
    WTF_CSRF_ENABLED: bool = False


class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.environ["DATABASE_URL"]
    SQLALCHEMY_POOL_SIZE: int = 10
    SQLALCHEMY_MAX_OVERFLOW: int = 20


config_by_name: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
```

### Environment Variables

```bash
# .env.example
SECRET_KEY=change-me-in-production
DATABASE_URL=postgresql://user:password@localhost:5432/myapp
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=development
FLASK_APP=wsgi:app

# JWT
JWT_SECRET_KEY=another-secret-key

# Mail
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=noreply@example.com
MAIL_PASSWORD=secret
```

---

## 3. Extensions

### Centralized Extension Initialization

```python
# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
ma = Marshmallow()
jwt = JWTManager()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
)
```

---

## 4. Models

### SQLAlchemy Models

```python
# app/models/base.py
from datetime import datetime, timezone

from app.extensions import db


class TimestampMixin:
    """Adds created_at and updated_at timestamps to any model."""

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class BaseModel(TimestampMixin, db.Model):
    """Abstract base model with id and timestamps."""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    def save(self) -> "BaseModel":
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self) -> None:
        db.session.delete(self)
        db.session.commit()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"
```

```python
# app/models/user.py
import bcrypt

from app.extensions import db
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    posts = db.relationship("Post", backref="author", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """Hash and store password. Never store plaintext."""
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8"),
        )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

---

## 5. Schemas and Validation

### Marshmallow Schemas

```python
# app/schemas/user.py
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load

from app.models.user import User


class UserSchema(Schema):
    """Schema for serializing user responses."""

    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=80),
    )
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    full_name = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format="iso")
    updated_at = fields.DateTime(dump_only=True, format="iso")

    class Meta:
        # Never expose sensitive fields
        dump_only = ("id", "is_active", "created_at", "updated_at")


class CreateUserSchema(Schema):
    """Schema for creating a new user."""

    email = fields.Email(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    password = fields.Str(
        required=True,
        load_only=True,
        validate=[
            validate.Length(min=8),
            validate.Regexp(
                r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)",
                error="Password must contain uppercase, lowercase, and digit.",
            ),
        ],
    )
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))

    @validates("email")
    def validate_unique_email(self, email: str) -> None:
        if User.query.filter_by(email=email.lower()).first():
            raise ValidationError("Email is already registered.", field_name="email")

    @validates("username")
    def validate_unique_username(self, username: str) -> None:
        if User.query.filter_by(username=username.lower()).first():
            raise ValidationError("Username is already taken.", field_name="username")

    @post_load
    def normalize(self, data: dict, **kwargs) -> dict:
        data["email"] = data["email"].lower()
        data["username"] = data["username"].lower()
        return data


class UpdateUserSchema(Schema):
    """Schema for partial user updates (PATCH)."""

    first_name = fields.Str(validate=validate.Length(min=1, max=100))
    last_name = fields.Str(validate=validate.Length(min=1, max=100))


class ChangePasswordSchema(Schema):
    current_password = fields.Str(required=True, load_only=True)
    new_password = fields.Str(
        required=True,
        load_only=True,
        validate=[
            validate.Length(min=8),
            validate.Regexp(
                r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)",
                error="Password must contain uppercase, lowercase, and digit.",
            ),
        ],
    )


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


# Instantiated schema singletons (reuse to avoid re-allocation)
user_schema = UserSchema()
users_schema = UserSchema(many=True)
create_user_schema = CreateUserSchema()
update_user_schema = UpdateUserSchema()
```

---

## 6. Blueprints and Routing

### Blueprint Registration

```python
# app/api/v1/__init__.py
from flask import Blueprint

api_v1_blueprint = Blueprint("api_v1", __name__)

from app.api.v1 import users, products, auth  # noqa: E402, F401
```

### Route Definition

```python
# app/api/v1/users.py
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.api.v1 import api_v1_blueprint
from app.schemas.user import (
    user_schema,
    users_schema,
    create_user_schema,
    update_user_schema,
)
from app.services.user_service import UserService
from app.utils.pagination import paginate
from app.utils.responses import success_response, created_response, no_content_response
from app.decorators import admin_required


@api_v1_blueprint.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    """
    List all users with pagination and optional filtering.

    Query params:
        page (int): Page number, default 1.
        per_page (int): Items per page, default 20, max 100.
        search (str): Optional search term for name/email.
        is_active (bool): Filter by active status.

    Returns:
        JSON list of users with pagination metadata.
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    search = request.args.get("search", "").strip()
    is_active = request.args.get("is_active", type=lambda v: v.lower() == "true")

    query = UserService.build_query(search=search, is_active=is_active)
    return paginate(query, users_schema, page=page, per_page=per_page)


@api_v1_blueprint.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id: int):
    """
    Get a single user by ID.

    Returns:
        JSON user object or 404.
    """
    user = UserService.get_by_id_or_404(user_id)
    return success_response(user_schema.dump(user))


@api_v1_blueprint.route("/users", methods=["POST"])
def create_user():
    """
    Create a new user account.

    Body:
        email, username, password, first_name, last_name (all required).

    Returns:
        201 with created user or 422 with validation errors.
    """
    data = create_user_schema.load(request.get_json() or {})
    user = UserService.create(data)
    return created_response(user_schema.dump(user))


@api_v1_blueprint.route("/users/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id: int):
    """
    Partially update a user. Only the authenticated user can update themselves.
    """
    current_user_id = int(get_jwt_identity())

    if current_user_id != user_id:
        from app.exceptions import ForbiddenError
        raise ForbiddenError("You can only update your own profile.")

    user = UserService.get_by_id_or_404(user_id)
    data = update_user_schema.load(request.get_json() or {}, partial=True)
    updated_user = UserService.update(user, data)
    return success_response(user_schema.dump(updated_user))


@api_v1_blueprint.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_user(user_id: int):
    """
    Delete a user. Requires admin role.
    """
    user = UserService.get_by_id_or_404(user_id)
    UserService.delete(user)
    return no_content_response()
```

---

## 7. Service Layer

### Business Logic Separation

```python
# app/services/user_service.py
from datetime import datetime, timezone
from typing import Any

from flask import abort
from sqlalchemy import or_

from app.extensions import db
from app.models.user import User


class UserService:
    """
    Handles all business logic for user operations.
    Never call db.session directly from routes — use this layer.
    """

    @staticmethod
    def get_by_id_or_404(user_id: int) -> User:
        """Fetch user by ID or raise 404."""
        return db.get_or_404(User, user_id, description="User not found.")

    @staticmethod
    def get_by_email(email: str) -> User | None:
        return User.query.filter_by(email=email.lower()).first()

    @staticmethod
    def build_query(search: str = "", is_active: bool | None = None):
        """Build a filterable query for user listing."""
        query = User.query

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        return query.order_by(User.created_at.desc())

    @staticmethod
    def create(data: dict) -> User:
        """Create and persist a new user."""
        user = User(
            email=data["email"],
            username=data["username"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        user.set_password(data["password"])

        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update(user: User, data: dict) -> User:
        """Apply partial updates to a user."""
        for key, value in data.items():
            setattr(user, key, value)

        db.session.commit()
        return user

    @staticmethod
    def delete(user: User) -> None:
        """Soft delete by deactivation, rather than hard delete."""
        user.is_active = False
        db.session.commit()

    @staticmethod
    def record_login(user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
```

---

## 8. Authentication and Authorization

### JWT Authentication

```python
# app/api/v1/auth.py
from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)

from app.api.v1 import api_v1_blueprint
from app.extensions import limiter
from app.schemas.user import LoginSchema, user_schema
from app.services.user_service import UserService
from app.utils.responses import success_response
from app.exceptions import UnauthorizedError


login_schema = LoginSchema()


@api_v1_blueprint.route("/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    """
    Authenticate and return access + refresh tokens.
    Rate limited to prevent brute-force attacks.
    """
    data = login_schema.load(request.get_json() or {})

    user = UserService.get_by_email(data["email"])

    if not user or not user.check_password(data["password"]):
        raise UnauthorizedError("Invalid email or password.")

    if not user.is_active:
        raise UnauthorizedError("Account is disabled.", details={"code": "ACCOUNT_DISABLED"})

    UserService.record_login(user)

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_schema.dump(user),
    })


@api_v1_blueprint.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Issue a new access + refresh token pair using a valid refresh token."""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    refresh_token = create_refresh_token(identity=identity)
    return success_response({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    })


@api_v1_blueprint.route("/auth/logout", methods=["DELETE"])
@jwt_required()
def logout():
    """
    Invalidate the current token.
    Requires a token blocklist implementation (Redis recommended).
    """
    from app.utils.auth import blocklist_token
    blocklist_token(get_jwt()["jti"])
    return no_content_response()
```

### Token Blocklist (Redis)

```python
# app/utils/auth.py
from datetime import timezone

from flask_jwt_extended import decode_token

from app.extensions import cache


BLOCKLIST_PREFIX = "jwt_blocklist:"


def blocklist_token(jti: str) -> None:
    """Add a JWT ID to the blocklist."""
    token = decode_token(jti, allow_expired=True)
    expires = token["exp"] - token["iat"]
    cache.set(f"{BLOCKLIST_PREFIX}{jti}", "true", timeout=expires)


def is_token_revoked(jwt_payload: dict) -> bool:
    """Check if a token has been revoked."""
    return cache.get(f"{BLOCKLIST_PREFIX}{jwt_payload['jti']}") is not None
```

```python
# Wire up in create_app
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    from app.utils.auth import is_token_revoked
    return is_token_revoked(jwt_payload)
```

### Role-Based Access Control

```python
# app/decorators.py
from functools import wraps

from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.exceptions import ForbiddenError
from app.models.user import User


def admin_required(fn):
    """Decorator that requires the current user to be an admin."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            raise ForbiddenError("Admin access required.")

        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles: str):
    """Decorator factory that requires one of the specified roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)

            if not user or user.role not in roles:
                raise ForbiddenError(f"One of these roles required: {', '.join(roles)}")

            return fn(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 9. Error Handling

### Custom Exceptions

```python
# app/exceptions.py
from flask import Flask, jsonify


class ApiError(Exception):
    """Base class for all API errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        payload = {
            "error": {
                "code": self.error_code,
                "message": self.message,
            }
        }
        if self.details:
            payload["error"]["details"] = self.details
        return payload


class BadRequestError(ApiError):
    status_code = 400
    error_code = "BAD_REQUEST"


class UnauthorizedError(ApiError):
    status_code = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(ApiError):
    status_code = 403
    error_code = "FORBIDDEN"


class NotFoundError(ApiError):
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(ApiError):
    status_code = 409
    error_code = "CONFLICT"


class UnprocessableError(ApiError):
    status_code = 422
    error_code = "UNPROCESSABLE_ENTITY"


class TooManyRequestsError(ApiError):
    status_code = 429
    error_code = "TOO_MANY_REQUESTS"


def register_error_handlers(app: Flask) -> None:
    """Register all error handlers on the app."""

    from marshmallow import ValidationError
    from flask_jwt_extended.exceptions import (
        NoAuthorizationError,
        InvalidHeaderError,
        ExpiredSignatureError,
    )
    from werkzeug.exceptions import HTTPException
    from sqlalchemy.exc import IntegrityError

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        # Return 409 for uniqueness violations, 422 for other validation errors
        is_conflict = any(
            "already" in str(msg).lower()
            for msgs in error.messages.values()
            for msg in (msgs if isinstance(msgs, list) else [msgs])
        )
        status_code = 409 if is_conflict else 422
        error_code = "CONFLICT" if is_conflict else "VALIDATION_ERROR"
        message = "A resource with that value already exists." if is_conflict else "Input validation failed."
        return jsonify({
            "error": {
                "code": error_code,
                "message": message,
                "details": error.messages,
            }
        }), status_code

    @app.errorhandler(NoAuthorizationError)
    @app.errorhandler(InvalidHeaderError)
    def handle_auth_error(error):
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": str(error),
            }
        }), 401

    @app.errorhandler(ExpiredSignatureError)
    def handle_expired_token(error):
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Access token has expired.",
            }
        }), 401

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        from app.extensions import db
        db.session.rollback()
        return jsonify({
            "error": {
                "code": "CONFLICT",
                "message": "A resource with that value already exists.",
            }
        }), 409

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return jsonify({
            "error": {
                "code": error.name.upper().replace(" ", "_"),
                "message": error.description,
            }
        }), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled exception: %s", error)
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            }
        }), 500
```

---

## 10. Response Helpers

### Consistent Response Format

```python
# app/utils/responses.py
from flask import jsonify, Response


def success_response(data: dict | list, status_code: int = 200) -> tuple[Response, int]:
    """Standard 200 OK response."""
    return jsonify({"data": data}), status_code


def created_response(data: dict) -> tuple[Response, int]:
    """Standard 201 Created response."""
    return jsonify({"data": data}), 201


def no_content_response() -> tuple[Response, int]:
    """Standard 204 No Content response."""
    return Response(status=204)


def paginated_response(
    items: list,
    total: int,
    page: int,
    per_page: int,
) -> tuple[Response, int]:
    """Paginated response with metadata."""
    return jsonify({
        "data": items,
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }
    }), 200
```

---

## 11. Pagination

### Reusable Pagination Utility

```python
# app/utils/pagination.py
from flask import request
from marshmallow import Schema

from app.utils.responses import paginated_response


def paginate(query, schema: Schema, page: int = 1, per_page: int = 20):
    """
    Apply pagination to a SQLAlchemy query and serialize the result.

    Args:
        query: SQLAlchemy query object.
        schema: Marshmallow schema for serialization.
        page: Current page number.
        per_page: Number of items per page.

    Returns:
        JSON paginated response.
    """
    per_page = min(per_page, 100)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return paginated_response(
        items=schema.dump(pagination.items),
        total=pagination.total,
        page=pagination.page,
        per_page=pagination.per_page,
    )
```

---

## 12. Request Validation

### Validating All Input Surfaces

```python
# Route-level validation pattern
@api_v1_blueprint.route("/products", methods=["POST"])
@jwt_required()
def create_product():
    # ✓ Always validate JSON body
    json_data = request.get_json()
    if not json_data:
        raise BadRequestError("Request body must be JSON.")

    data = create_product_schema.load(json_data)
    product = ProductService.create(data)
    return created_response(product_schema.dump(product))


# ✓ Validate query parameters as a schema
class ProductFilterSchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    category = fields.Str(validate=validate.Length(max=100))
    min_price = fields.Float(validate=validate.Range(min=0))
    max_price = fields.Float(validate=validate.Range(min=0))
    sort_by = fields.Str(
        validate=validate.OneOf(["price", "created_at", "name"]),
        load_default="created_at",
    )


product_filter_schema = ProductFilterSchema()


@api_v1_blueprint.route("/products", methods=["GET"])
def list_products():
    # ✓ Validate query params
    filters = product_filter_schema.load(request.args)
    ...
```

---

## 13. Caching

### Response and Query Caching

```python
# app/extensions.py - Cache config
cache = Cache(config={
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": os.getenv("REDIS_URL"),
    "CACHE_DEFAULT_TIMEOUT": 300,  # 5 minutes
})

# Route caching
@api_v1_blueprint.route("/products/<int:product_id>", methods=["GET"])
@cache.cached(timeout=300, key_prefix="product_%s")
def get_product(product_id: int):
    product = ProductService.get_by_id_or_404(product_id)
    return success_response(product_schema.dump(product))


# Manual cache control
class ProductService:
    CACHE_KEY = "products:all"

    @staticmethod
    def get_all() -> list:
        cached = cache.get(ProductService.CACHE_KEY)
        if cached:
            return cached

        products = Product.query.filter_by(is_active=True).all()
        result = products_schema.dump(products)
        cache.set(ProductService.CACHE_KEY, result, timeout=300)
        return result

    @staticmethod
    def invalidate_cache() -> None:
        """Call after any product write operation."""
        cache.delete(ProductService.CACHE_KEY)
        cache.delete_memoized(get_product)
```

---

## 14. Rate Limiting

### Granular Rate Limits

```python
# app/api/v1/auth.py
from app.extensions import limiter


# Tight limits on sensitive endpoints
@api_v1_blueprint.route("/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    ...


@api_v1_blueprint.route("/auth/register", methods=["POST"])
@limiter.limit("3 per hour")
def register():
    ...


# Custom limit by authenticated user identity
@api_v1_blueprint.route("/upload", methods=["POST"])
@jwt_required()
@limiter.limit("10 per hour", key_func=get_jwt_identity)
def upload_file():
    ...


# Exempt health check routes
@api_v1_blueprint.route("/health")
@limiter.exempt
def health_check():
    return success_response({"status": "ok"})
```

---

## 15. File Uploads

### Secure File Upload Handling

```python
import os
import uuid

from flask import request
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename: str, allowed: set[str]) -> bool:
    """Check if the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def save_upload(file, upload_folder: str, allowed: set[str]) -> str:
    """
    Securely save an uploaded file and return its filename.

    - Validates extension
    - Sanitizes filename
    - Generates unique name to prevent overwrite attacks
    """
    if not file or file.filename == "":
        raise BadRequestError("No file selected.")

    if not allowed_file(file.filename, allowed):
        raise BadRequestError(
            f"File type not allowed. Permitted: {', '.join(allowed)}"
        )

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(upload_folder, unique_filename)
    file.save(save_path)
    return unique_filename


@api_v1_blueprint.route("/users/<int:user_id>/avatar", methods=["POST"])
@jwt_required()
def upload_avatar(user_id: int):
    if "file" not in request.files:
        raise BadRequestError("No file part in request.")

    file = request.files["file"]
    filename = save_upload(
        file,
        upload_folder=current_app.config["UPLOAD_FOLDER"],
        allowed=ALLOWED_IMAGE_EXTENSIONS,
    )
    UserService.set_avatar(user_id, filename)
    return success_response({"filename": filename})
```

---

## 16. Background Tasks

### Celery Integration

```python
# app/extensions.py
from celery import Celery

celery = Celery()


def init_celery(app):
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# app/tasks/email_tasks.py
from app.extensions import celery
from app.services.email_service import EmailService


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id: int) -> None:
    """Send welcome email. Retries up to 3 times on failure."""
    try:
        from app.models.user import User
        user = User.query.get(user_id)
        if user:
            EmailService.send_welcome(user)
    except Exception as exc:
        raise self.retry(exc=exc)


# Usage in routes
from app.tasks.email_tasks import send_welcome_email

def create_user(data: dict) -> User:
    user = UserService.create(data)
    send_welcome_email.delay(user.id)  # Async, non-blocking
    return user
```

---

## 17. Database Migrations

### Flask-Migrate Best Practices

```bash
# Initialize migrations
flask db init

# Generate migration after model change
flask db migrate -m "Add last_login_at to users"

# Review generated migration before applying
# Always review auto-generated scripts — they are not always correct

# Apply migration
flask db upgrade

# Rollback one step
flask db downgrade
```

```python
# migrations/versions/001_add_last_login.py
def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    # Add an index for common lookup
    op.create_index("ix_users_last_login_at", "users", ["last_login_at"])


def downgrade():
    op.drop_index("ix_users_last_login_at", table_name="users")
    op.drop_column("users", "last_login_at")
```

---

## 18. API Versioning

### URL-based Versioning (Recommended)

```python
# app/api/v1/__init__.py
from flask import Blueprint

api_v1_blueprint = Blueprint("api_v1", __name__)
from app.api.v1 import users  # noqa


# app/api/v2/__init__.py
from flask import Blueprint

api_v2_blueprint = Blueprint("api_v2", __name__)
from app.api.v2 import users  # noqa


# app/__init__.py
app.register_blueprint(api_v1_blueprint, url_prefix="/api/v1")
app.register_blueprint(api_v2_blueprint, url_prefix="/api/v2")


# v2 route can reuse v1 service/schema but with a new response shape
# app/api/v2/users.py
@api_v2_blueprint.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id: int):
    user = UserService.get_by_id_or_404(user_id)
    return success_response(user_v2_schema.dump(user))  # New schema with extra fields
```

---

## 19. Logging

### Structured Logging

```python
# app/__init__.py
import logging
import json
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Outputs log records as JSON for log aggregation tools."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def configure_logging(app) -> None:
    if not app.debug:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
```

### Request Logging Middleware

```python
# app/middleware.py
import time
import uuid

from flask import Flask, g, request


def register_request_logging(app: Flask) -> None:
    @app.before_request
    def start_timer():
        g.start_time = time.perf_counter()
        g.request_id = str(uuid.uuid4())

    @app.after_request
    def log_request(response):
        duration_ms = (time.perf_counter() - g.start_time) * 1000

        app.logger.info(
            "HTTP Request",
            extra={
                "request_id": g.request_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "ip": request.remote_addr,
            }
        )
        response.headers["X-Request-ID"] = g.request_id
        return response
```

---

## 20. Security

### CORS Configuration

```python
from flask_cors import CORS

def _register_extensions(app: Flask) -> None:
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config["ALLOWED_ORIGINS"],
            "methods": ["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Authorization", "Content-Type"],
            "expose_headers": ["X-Request-ID"],
            "max_age": 600,
        }
    })
```

### Security Headers

```python
# app/middleware.py
from flask import Flask


def register_security_headers(app: Flask) -> None:
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "frame-ancestors 'none';"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        return response
```

### Input Sanitization

```python
import bleach


def sanitize_html(content: str) -> str:
    """Strip all HTML tags. Use for user-submitted text content."""
    return bleach.clean(content, tags=[], strip=True)


def sanitize_rich_content(content: str) -> str:
    """Allowlist safe HTML tags for rich text fields."""
    allowed_tags = ["b", "i", "u", "em", "strong", "p", "br", "ul", "ol", "li"]
    allowed_attrs = {}
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attrs, strip=True)
```

### SQL Injection Prevention

```python
# ✓ Always use SQLAlchemy ORM or parameterized queries
user = User.query.filter_by(email=email).first()

# ✓ For complex queries, use text() with bound parameters
from sqlalchemy import text

result = db.session.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)

# ✗ Never interpolate user input into raw SQL
# db.session.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

---

## 21. Health and Readiness Checks

```python
# app/api/v1/health.py
from flask import jsonify

from app.api.v1 import api_v1_blueprint
from app.extensions import db, cache


@api_v1_blueprint.route("/health", methods=["GET"])
def health_check():
    """
    Liveness probe. Returns 200 if app is running.
    Used by load balancers and container orchestrators.
    """
    return jsonify({"status": "ok"}), 200


@api_v1_blueprint.route("/health/ready", methods=["GET"])
def readiness_check():
    """
    Readiness probe. Returns 200 only if all dependencies are reachable.
    Used by Kubernetes to determine if a pod should receive traffic.
    """
    checks = {}

    try:
        db.session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    try:
        cache.get("__probe__")
        checks["cache"] = "ok"
    except Exception:
        checks["cache"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return jsonify({"status": "ok" if all_ok else "degraded", "checks": checks}), 200 if all_ok else 503
```

---

## 22. API Documentation

### OpenAPI / Swagger with Flask-Smorest

```python
# app/config.py
class BaseConfig:
    API_TITLE = "My API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"


# app/api/v1/users.py
from flask_smorest import Blueprint

blp = Blueprint("users", __name__, url_prefix="/users", description="User operations")


@blp.route("/<int:user_id>")
class UserResource:
    @blp.arguments(UserQuerySchema, location="query")
    @blp.response(200, UserSchema)
    @blp.doc(summary="Get a user", description="Retrieve a user by their ID.")
    @jwt_required()
    def get(self, query_args, user_id: int):
        return UserService.get_by_id_or_404(user_id)

    @blp.arguments(UpdateUserSchema)
    @blp.response(200, UserSchema)
    @jwt_required()
    def patch(self, update_data, user_id: int):
        user = UserService.get_by_id_or_404(user_id)
        return UserService.update(user, update_data)
```

---

## 23. Testing

### Test Setup

```python
# tests/conftest.py
import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Reset DB to clean state between tests."""
    with app.app_context():
        yield _db
        _db.session.remove()
        _db.drop_all()
        _db.create_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client, db):
    """Return JWT Authorization headers for an authenticated user."""
    from app.models.user import User
    from app.extensions import db as database

    user = User(
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
    )
    user.set_password("Password1!")
    database.session.add(user)
    database.session.commit()

    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "Password1!",
    })

    token = response.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### Integration Tests

```python
# tests/integration/test_users.py
import pytest


class TestCreateUser:
    def test_creates_user_with_valid_data(self, client, db):
        response = client.post("/api/v1/users", json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "Password1!",
            "first_name": "Alice",
            "last_name": "Smith",
        })

        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["email"] == "alice@example.com"
        assert "password" not in data
        assert "password_hash" not in data

    def test_rejects_duplicate_email(self, client, db):
        payload = {
            "email": "dup@example.com",
            "username": "unique",
            "password": "Password1!",
            "first_name": "Alice",
            "last_name": "Smith",
        }
        client.post("/api/v1/users", json=payload)
        response = client.post("/api/v1/users", json={**payload, "username": "other"})

        assert response.status_code == 409

    def test_rejects_weak_password(self, client, db):
        response = client.post("/api/v1/users", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "weakpassword",
            "first_name": "Test",
            "last_name": "User",
        })

        assert response.status_code == 422


class TestGetUser:
    def test_returns_user(self, client, db, auth_headers):
        # Create user first
        create_response = client.post("/api/v1/users", json={
            "email": "get@example.com",
            "username": "getuser",
            "password": "Password1!",
            "first_name": "Get",
            "last_name": "User",
        })
        user_id = create_response.get_json()["data"]["id"]

        response = client.get(f"/api/v1/users/{user_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.get_json()["data"]["id"] == user_id

    def test_returns_404_for_missing_user(self, client, db, auth_headers):
        response = client.get("/api/v1/users/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_requires_authentication(self, client, db):
        response = client.get("/api/v1/users/1")

        assert response.status_code == 401
```

### Unit Tests

```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import patch, MagicMock


class TestUserService:
    def test_creates_user(self, db):
        from app.services.user_service import UserService

        user = UserService.create({
            "email": "unit@example.com",
            "username": "unituser",
            "password": "Password1!",
            "first_name": "Unit",
            "last_name": "Test",
        })

        assert user.id is not None
        assert user.email == "unit@example.com"
        assert user.password_hash != "Password1!"

    def test_password_check(self, db):
        from app.services.user_service import UserService

        user = UserService.create({
            "email": "pw@example.com",
            "username": "pwuser",
            "password": "Password1!",
            "first_name": "Pw",
            "last_name": "User",
        })

        assert user.check_password("Password1!") is True
        assert user.check_password("wrongpassword") is False
```

---

## 24. Deployment

### Production Entry Point

```python
# wsgi.py
import os
from app import create_app

app = create_app(os.getenv("FLASK_ENV", "production"))

if __name__ == "__main__":
    app.run()
```

### Gunicorn Configuration

```python
# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
```

---

## 25. Repository Layer

### Data Access Abstraction

```python
# app/repositories/base.py
from typing import Generic, TypeVar

from sqlalchemy.orm import Query

from app.extensions import db

T = TypeVar("T", bound=db.Model)


class BaseRepository(Generic[T]):
    """
    Generic repository providing standard CRUD operations.
    All database access goes through repositories — never call db.session
    from services directly.
    """

    model: type[T]

    def get_by_id(self, entity_id: int) -> T | None:
        return db.session.get(self.model, entity_id)

    def get_all(self) -> list[T]:
        return self.model.query.all()

    def save(self, entity: T) -> T:
        db.session.add(entity)
        db.session.commit()
        return entity

    def delete(self, entity: T) -> None:
        db.session.delete(entity)
        db.session.commit()

    def count(self, query: Query | None = None) -> int:
        if query is not None:
            return query.count()
        return self.model.query.count()
```

```python
# app/repositories/user_repository.py
from sqlalchemy import or_

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return User.query.filter_by(email=email.lower()).first()

    def get_by_username(self, username: str) -> User | None:
        return User.query.filter_by(username=username.lower()).first()

    def search(self, term: str, is_active: bool | None = None):
        query = User.query

        if term:
            pattern = f"%{term}%"
            query = query.filter(
                or_(
                    User.email.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        return query.order_by(User.created_at.desc())
```

---

## 26. Filtering & Sorting

### Query Parameter Validation for Filters

```python
# app/schemas/filters.py
from marshmallow import Schema, fields, validate


class BaseFilterSchema(Schema):
    """Base schema for list endpoint query parameters."""

    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    sort_by = fields.Str(load_default="created_at")
    sort_order = fields.Str(
        load_default="desc",
        validate=validate.OneOf(["asc", "desc"]),
    )


class UserFilterSchema(BaseFilterSchema):
    search = fields.Str(load_default="", validate=validate.Length(max=100))
    is_active = fields.Bool(load_default=None)
    created_after = fields.DateTime(load_default=None)
    created_before = fields.DateTime(load_default=None)

    ALLOWED_SORT_FIELDS = {"created_at", "email", "first_name", "last_name"}


class ProductFilterSchema(BaseFilterSchema):
    category = fields.Str(validate=validate.Length(max=100))
    min_price = fields.Float(validate=validate.Range(min=0))
    max_price = fields.Float(validate=validate.Range(min=0))

    ALLOWED_SORT_FIELDS = {"created_at", "price", "name"}


user_filter_schema = UserFilterSchema()
product_filter_schema = ProductFilterSchema()
```

### Applying Filters in Services

```python
# app/services/user_service.py
from sqlalchemy import asc, desc


class UserService:
    SORT_FIELDS = {
        "created_at": User.created_at,
        "email": User.email,
        "first_name": User.first_name,
        "last_name": User.last_name,
    }

    @staticmethod
    def build_filtered_query(filters: dict):
        """Build a filterable, sortable query from validated filter params."""
        query = User.query

        if filters.get("search"):
            pattern = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    User.email.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )

        if filters.get("is_active") is not None:
            query = query.filter_by(is_active=filters["is_active"])

        if filters.get("created_after"):
            query = query.filter(User.created_at >= filters["created_after"])

        if filters.get("created_before"):
            query = query.filter(User.created_at <= filters["created_before"])

        sort_field = UserService.SORT_FIELDS.get(
            filters.get("sort_by", "created_at"), User.created_at
        )
        direction = desc if filters.get("sort_order", "desc") == "desc" else asc
        query = query.order_by(direction(sort_field))

        return query
```

### Usage in Routes

```python
@api_v1_blueprint.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    filters = user_filter_schema.load(request.args)
    query = UserService.build_filtered_query(filters)
    return paginate(query, users_schema, page=filters["page"], per_page=filters["per_page"])
```

---

## 27. Database Transactions & Concurrency

### Explicit Transaction Management

```python
# app/services/order_service.py
from app.extensions import db
from app.exceptions import ConflictError


class OrderService:
    @staticmethod
    def place_order(user_id: int, items: list[dict]) -> "Order":
        """
        Place an order inside a single transaction.
        Either all items are reserved and the order is created, or nothing changes.
        Uses SELECT ... FOR UPDATE to lock inventory rows.
        """
        try:
            order = Order(user_id=user_id, status="pending")
            db.session.add(order)

            for item in items:
                product = Product.query.with_for_update().get(item["product_id"])
                if not product or product.stock < item["quantity"]:
                    db.session.rollback()
                    raise ConflictError(
                        f"Insufficient stock for product {item['product_id']}."
                    )

                product.stock -= item["quantity"]
                order_item = OrderItem(
                    order=order,
                    product=product,
                    quantity=item["quantity"],
                    unit_price=product.price,
                )
                db.session.add(order_item)

            db.session.commit()
            return order
        except ConflictError:
            raise
        except Exception:
            db.session.rollback()
            raise
```

### Optimistic Concurrency Control

```python
# app/models/base.py
class VersionedMixin:
    """Add a version column for optimistic concurrency control."""

    version = db.Column(db.Integer, nullable=False, default=1)


# app/models/product.py
class Product(BaseModel, VersionedMixin):
    __tablename__ = "products"

    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)


# app/services/product_service.py
class ProductService:
    @staticmethod
    def update_with_version(product_id: int, data: dict, expected_version: int) -> Product:
        """
        Update a product only if the version matches.
        Returns 409 Conflict if another client modified it first.
        """
        rows_updated = (
            Product.query
            .filter_by(id=product_id, version=expected_version)
            .update({**data, "version": expected_version + 1})
        )
        db.session.commit()

        if rows_updated == 0:
            raise ConflictError(
                "Resource was modified by another request. Reload and try again."
            )

        return Product.query.get(product_id)
```

### Route with ETag / If-Match

```python
@api_v1_blueprint.route("/products/<int:product_id>", methods=["PATCH"])
@jwt_required()
def update_product(product_id: int):
    data = update_product_schema.load(request.get_json() or {})
    expected_version = request.headers.get("If-Match", type=int)

    if expected_version is None:
        raise BadRequestError("If-Match header with resource version is required.")

    product = ProductService.update_with_version(product_id, data, expected_version)
    response, status_code = success_response(product_schema.dump(product))
    response.headers["ETag"] = str(product.version)
    return response, status_code
```

---

## 28. Idempotency Keys

### Decorator for Idempotent POST Requests

```python
# app/utils/idempotency.py
import hashlib
import json
from functools import wraps

from flask import jsonify, request

from app.extensions import cache
from app.exceptions import ConflictError

IDEMPOTENCY_TTL = 86400  # 24 hours


def idempotent(fn):
    """
    Decorator for POST endpoints that should be idempotent.
    Clients send an Idempotency-Key header. If the same key is reused,
    the stored response is replayed instead of re-executing the handler.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        key = request.headers.get("Idempotency-Key")
        if not key:
            return fn(*args, **kwargs)

        cache_key = f"idempotency:{key}"
        cached = cache.get(cache_key)
        body_hash = hashlib.sha256(
            json.dumps(request.get_json() or {}, sort_keys=True).encode()
        ).hexdigest()

        if cached is not None:
            if cached["body_hash"] != body_hash:
                raise ConflictError(
                    "Idempotency-Key was already used with a different request body."
                )
            return jsonify(cached["response_body"]), cached["status_code"]

        result = fn(*args, **kwargs)
        response_body = result[0].get_json() if isinstance(result, tuple) else result.get_json()
        status_code = result[1] if isinstance(result, tuple) else 200

        cache.set(cache_key, {
            "response_body": response_body,
            "status_code": status_code,
            "body_hash": body_hash,
        }, timeout=IDEMPOTENCY_TTL)

        return result
    return wrapper
```

### Usage

```python
@api_v1_blueprint.route("/orders", methods=["POST"])
@jwt_required()
@idempotent
def create_order():
    """Idempotent order creation — safe to retry with the same Idempotency-Key."""
    data = create_order_schema.load(request.get_json() or {})
    order = OrderService.place_order(
        user_id=int(get_jwt_identity()),
        items=data["items"],
    )
    return created_response(order_schema.dump(order))
```

---

## 29. External Service Resilience

### HTTP Client with Timeouts and Retries

```python
# app/utils/http_client.py
import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10  # seconds
MAX_RETRIES = 3


def create_http_client(
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> requests.Session:
    """
    Create a requests session with timeout enforcement and retry logic.
    Uses exponential backoff for transient failures (429, 500, 502, 503, 504).
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.timeout = timeout
    return session


# Singleton — reuse across the application
http_client = create_http_client()
```

### Circuit Breaker Pattern

```python
# pip install pybreaker
# app/utils/circuit_breaker.py
import logging

import pybreaker

logger = logging.getLogger(__name__)


class LoggingListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        logger.warning(
            "Circuit breaker '%s' state changed: %s → %s",
            cb.name, old_state.name, new_state.name,
        )


payment_circuit = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    listeners=[LoggingListener()],
    name="payment_gateway",
)


# app/services/payment_service.py
from app.utils.circuit_breaker import payment_circuit
from app.utils.http_client import http_client


class PaymentService:
    @staticmethod
    @payment_circuit
    def charge(amount: int, currency: str, token: str) -> dict:
        """
        Call external payment gateway with circuit breaker protection.
        If the gateway fails 5 consecutive times, the circuit opens and calls
        fail fast for 30 seconds before retrying.
        """
        response = http_client.post(
            "https://api.payment-provider.com/v1/charges",
            json={"amount": amount, "currency": currency, "source": token},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
```

### Graceful Degradation in Routes

```python
import pybreaker
import requests as req_lib

from app.exceptions import ApiError


@api_v1_blueprint.route("/checkout", methods=["POST"])
@jwt_required()
def checkout():
    try:
        payment = PaymentService.charge(
            amount=order.total,
            currency="usd",
            token=data["payment_token"],
        )
    except pybreaker.CircuitBreakerError:
        raise ApiError(
            "Payment service is temporarily unavailable. Please try again later.",
        )
    except req_lib.Timeout:
        raise ApiError("Payment service timed out. Please try again.")
    ...
```

---

## 30. Bulk Operations & Streaming

### Batch Create Endpoint

```python
# app/schemas/product.py
class BulkCreateProductSchema(Schema):
    items = fields.List(
        fields.Nested(CreateProductSchema),
        required=True,
        validate=validate.Length(min=1, max=100),
    )


bulk_create_product_schema = BulkCreateProductSchema()


# app/api/v1/products.py
@api_v1_blueprint.route("/products/bulk", methods=["POST"])
@jwt_required()
@admin_required
def bulk_create_products():
    """
    Create up to 100 products in a single request.
    All succeed or all fail (transactional).
    """
    data = bulk_create_product_schema.load(request.get_json() or {})
    try:
        products = ProductService.bulk_create(data["items"])
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return created_response(products_schema.dump(products))
```

### Streaming Large Responses (CSV Export)

```python
import csv
import io

from flask import Response, stream_with_context


@api_v1_blueprint.route("/users/export", methods=["GET"])
@jwt_required()
@admin_required
def export_users():
    """Stream users as CSV. Handles large datasets without loading all into memory."""

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "email", "first_name", "last_name", "created_at"])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        page = 1
        per_page = 500
        while True:
            users = User.query.order_by(User.id).paginate(
                page=page, per_page=per_page, error_out=False
            )
            if not users.items:
                break

            for user in users.items:
                writer.writerow([
                    user.id, user.email, user.first_name,
                    user.last_name, user.created_at.isoformat(),
                ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            page += 1

    return Response(
        stream_with_context(generate()),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )
```

### Cursor-Based Pagination (for Large Datasets)

```python
# app/utils/pagination.py
import json
from base64 import b64decode, b64encode


def encode_cursor(payload: dict) -> str:
    return b64encode(json.dumps(payload).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    return json.loads(b64decode(cursor.encode()).decode())


@api_v1_blueprint.route("/events", methods=["GET"])
@jwt_required()
def list_events():
    """
    Cursor-based pagination for large or real-time datasets.
    More efficient than offset pagination for large tables.
    """
    cursor = request.args.get("cursor")
    limit = min(request.args.get("limit", 20, type=int), 100)

    query = Event.query.order_by(Event.created_at.desc(), Event.id.desc())

    if cursor:
        pos = decode_cursor(cursor)
        query = query.filter(
            db.or_(
                Event.created_at < pos["created_at"],
                db.and_(
                    Event.created_at == pos["created_at"],
                    Event.id < pos["id"],
                ),
            )
        )

    items = query.limit(limit + 1).all()

    next_cursor = None
    if len(items) > limit:
        items = items[:limit]
        last = items[-1]
        next_cursor = encode_cursor({
            "created_at": last.created_at.isoformat(),
            "id": last.id,
        })

    return jsonify({
        "data": events_schema.dump(items),
        "meta": {"next_cursor": next_cursor, "limit": limit},
    }), 200
```

---

## 31. Anti-Patterns — Never Do These

- **Never put business logic in routes**: Routes coordinate, services decide
- **Never call `db.session` in routes directly**: Always go through the service layer
- **Never return raw model objects**: Always serialize through a schema
- **Never expose sensitive fields**: Passwords, tokens, internal IDs on responses
- **Never trust user input without validation**: Validate every input surface (body, query, headers, path params)
- **Never swallow exceptions silently**: Log and surface meaningful errors
- **Never pass `debug=True` to production**: Exposes internals and disables security
- **Never use `app.run()` in production**: Use Gunicorn/uWSGI behind a reverse proxy
- **Never store secrets in code**: Use environment variables and secrets managers
- **Never use `SELECT *`**: Only query what you need
- **Never disable CSRF without compensating controls**: Use JWT or same-site cookies properly
- **Never return 200 for errors**: Use proper HTTP status codes always
- **Never log passwords or tokens**: Scrub sensitive data from logs
- **Never return stack traces to clients**: Only in debug mode
- **Never build SQL strings with f-strings**: Use ORM or parameterized queries always
- **Never create database connections per-request manually**: Let SQLAlchemy pool manage it
- **Never skip migration review**: Always review auto-generated migration scripts
- **Never mix query logic into schemas or models**: Keep queries in repositories/services
- **Never use `app.config["KEY"]` without a default in critical config**: Fail fast on startup
- **Never set `CORS(app)` to wildcard `*` in production**: Restrict to known origins
- **Never store uploads in the container filesystem**: Use object storage (S3, GCS)
- **Never call external services without a timeout**: Set explicit timeouts on every HTTP call
- **Never retry failed requests without exponential backoff**: Prevents thundering herd on recovery
- **Never allow unbounded bulk operations**: Cap batch size and validate
- **Never overwrite concurrent changes silently**: Use optimistic concurrency control with version fields
- **Never allow arbitrary sort or filter fields from user input**: Validate against an explicit allowlist

---

## 32. Best Practices Summary

**Structure:**
- ✓ Use the application factory pattern
- ✓ Separate routing, services, repositories, and schemas
- ✓ Version all APIs from day one
- ✓ Use Blueprints for every domain area

**Data Access:**
- ✓ Use repository pattern for all database queries
- ✓ Keep query logic in repositories — not in services, schemas, or routes
- ✓ Use transactions for multi-step mutations
- ✓ Use optimistic concurrency control for conflict-prone resources

**Validation:**
- ✓ Validate all input with Marshmallow schemas
- ✓ Validate query params as well as body
- ✓ Normalize input (lowercase email, trim strings) at schema level
- ✓ Validate and whitelist all filter and sort parameters

**Security:**
- ✓ Use JWT with short-lived access tokens + refresh token rotation
- ✓ Rate limit authentication endpoints aggressively
- ✓ Add security headers to every response
- ✓ Hash passwords with bcrypt — never store plaintext

**Error Handling:**
- ✓ Use custom exception hierarchy
- ✓ Register centralized error handlers
- ✓ Return consistent error shapes everywhere
- ✓ Never expose internals in production errors

**Resilience:**
- ✓ Set timeouts on all external HTTP calls
- ✓ Use circuit breakers for critical external dependencies
- ✓ Use idempotency keys for mutation endpoints
- ✓ Design for graceful degradation when non-critical services fail

**Performance:**
- ✓ Index all foreign keys and frequently queried columns
- ✓ Use caching for expensive or frequently read data
- ✓ Paginate all list endpoints (offset for standard, cursor for large datasets)
- ✓ Send slow tasks to Celery — never block a request
- ✓ Stream large exports instead of loading into memory

**Testing:**
- ✓ Use an in-memory SQLite DB for tests
- ✓ Reset DB state between tests
- ✓ Test the full HTTP layer, not just functions
- ✓ Test auth boundaries — always assert on 401/403 behavior
