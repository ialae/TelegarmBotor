# FastAPI — Complete Implementation Guide

These instructions define a complete implementation guide for building scalable, secure, and production-ready REST APIs with FastAPI. Covers project structure, routing, Pydantic models, dependency injection, authentication, error handling, database integration, background tasks, caching, testing, and deployment. Use this skill whenever writing, reviewing, or refactoring FastAPI code.

**One command runs the app:**

```bash
uvicorn app.main:app --reload
```

---

## 1. Project Structure

### Recommended Layout

```
my_api/
├── app/
│   ├── main.py              # App factory and startup
│   ├── config.py            # Settings via pydantic-settings
│   ├── dependencies.py      # Shared FastAPI dependencies
│   ├── exceptions.py        # Custom exceptions and handlers
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # SQLAlchemy ORM models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py          # Pydantic request/response schemas
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py  # APIRouter for v1
│   │       ├── users.py
│   │       ├── products.py
│   │       └── auth.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── user_service.py  # Business logic layer
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user_repository.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py       # Async SQLAlchemy engine + session
│   │   └── base.py          # DeclarativeBase
│   └── utils/
│       ├── __init__.py
│       ├── security.py      # JWT helpers
│       └── pagination.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── alembic/                 # Alembic migrations
├── alembic.ini
├── .env.example
├── .env
├── pyproject.toml
└── Dockerfile
```

### Application Entry Point

```python
# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1 import api_v1_router
from app.config import settings
from app.db.session import engine
from app.db.base import Base
from app.exceptions import register_exception_handlers
from app.middleware import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    _register_middleware(app)
    _register_routers(app)
    register_exception_handlers(app)

    return app


def _register_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(RequestLoggingMiddleware)


def _register_routers(app: FastAPI) -> None:
    app.include_router(api_v1_router, prefix="/api/v1")


app = create_app()
```

---

## 2. Configuration

### Pydantic Settings

```python
# app/config.py
from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_TITLE: str = "My API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = ""
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: PostgresDsn

    # Redis
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"

    # CORS
    ALLOWED_ORIGINS: list[AnyHttpUrl] = []

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

---

## 3. Database

### Async SQLAlchemy Setup

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
```

```python
# app/db/base.py
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

---

## 4. Models

### SQLAlchemy ORM Models

```python
# app/models/user.py
from typing import TYPE_CHECKING

import bcrypt
from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.post import Post


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_username", "username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    posts: Mapped[list["Post"]] = relationship("Post", back_populates="author")

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
```

---

## 5. Pydantic Schemas

### Request and Response Schemas

```python
# app/schemas/user.py
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=80)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., max_length=100)


class CreateUserRequest(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        return v.lower().strip()


class UpdateUserRequest(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)


class UserResponse(UserBase):
    id: int
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedUsersResponse(BaseModel):
    data: list[UserResponse]
    meta: dict


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_must_differ(self) -> "ChangePasswordRequest":
        if self.current_password == self.new_password:
            raise ValueError("New password must differ from current password.")
        return self
```

---

## 6. Dependencies

### Dependency Injection

```python
# app/dependencies.py
from typing import Annotated, AsyncGenerator

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.repositories.user_repository import UserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Decode JWT and return the authenticated user."""
    from app.exceptions import UnauthorizedError

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("Invalid or expired token.")
    except JWTError:
        raise UnauthorizedError("Invalid or expired token.")

    repo = UserRepository(db)
    user = await repo.get_by_id(int(user_id))

    if user is None:
        raise UnauthorizedError("Invalid or expired token.")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled.", details={"code": "ACCOUNT_DISABLED"})
    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require admin role."""
    from app.exceptions import ForbiddenError

    if not current_user.is_admin:
        raise ForbiddenError("Admin access required.")
    return current_user


# Type aliases for cleaner route signatures
DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_current_admin)]
```

---

## 7. Routing

### APIRouter and Routes

```python
# app/api/v1/__init__.py
from fastapi import APIRouter

from app.api.v1 import auth, users, products

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(products.router, prefix="/products", tags=["Products"])
```

```python
# app/api/v1/users.py
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.dependencies import AdminUser, CurrentUser, DBSession
from app.exceptions import ForbiddenError
from app.schemas.user import (
    CreateUserRequest,
    PaginatedUsersResponse,
    UpdateUserRequest,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedUsersResponse,
    summary="List users",
    description="Returns a paginated list of users. Requires authentication.",
)
async def list_users(
    db: DBSession,
    _: CurrentUser,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    search: Annotated[str, Query(max_length=100)] = "",
):
    service = UserService(db)
    items, total = await service.list_users(page=page, per_page=per_page, search=search)
    pages = (total + per_page - 1) // per_page
    return {
        "data": items,
        "meta": {"total": total, "page": page, "per_page": per_page, "pages": pages},
    }


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user",
    responses={404: {"description": "User not found"}},
)
async def get_user(user_id: int, db: DBSession, _: CurrentUser):
    service = UserService(db)
    user = await service.get_by_id_or_404(user_id)
    return {"data": UserResponse.model_validate(user)}


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
async def create_user(payload: CreateUserRequest, db: DBSession):
    service = UserService(db)
    user = await service.create(payload)
    return {"data": UserResponse.model_validate(user)}


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
)
async def update_user(
    user_id: int,
    payload: UpdateUserRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    if current_user.id != user_id:
        raise ForbiddenError("You can only update your own profile.")
    service = UserService(db)
    user = await service.get_by_id_or_404(user_id)
    updated = await service.update(user, payload)
    return {"data": UserResponse.model_validate(updated)}


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
)
async def delete_user(user_id: int, db: DBSession, _: AdminUser):
    service = UserService(db)
    user = await service.get_by_id_or_404(user_id)
    await service.delete(user)
```

---

## 8. Authentication

### JWT Auth Routes

```python
# app/api/v1/auth.py
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.dependencies import CurrentUser, DBSession
from app.exceptions import UnauthorizedError
from app.schemas.user import LoginRequest, TokenResponse, UserResponse
from app.services.user_service import UserService
from app.utils.security import blocklist_token, is_token_revoked

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def create_token(subject: str, expires_delta: timedelta, token_type: str = "access") -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": subject,
        "exp": expire,
        "type": token_type,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Returns access and refresh tokens on valid credentials.",
)
async def login(credentials: LoginRequest, db: DBSession):
    service = UserService(db)
    user = await service.get_by_email(credentials.email)

    if not user or not user.check_password(credentials.password):
        raise UnauthorizedError("Invalid email or password.")

    if not user.is_active:
        raise UnauthorizedError("Account is disabled.", details={"code": "ACCOUNT_DISABLED"})

    await service.record_login(user)

    return {"data": {
        "access_token": create_token(
            str(user.id),
            timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        "refresh_token": create_token(
            str(user.id),
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            token_type="refresh",
        ),
        "token_type": "bearer",
        "user": UserResponse.model_validate(user).model_dump(mode="json"),
    }}


@router.post("/refresh", response_model=None, summary="Refresh access token")
async def refresh_token(current_user: CurrentUser):
    return {"data": {
        "access_token": create_token(
            str(current_user.id),
            timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        "refresh_token": create_token(
            str(current_user.id),
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            token_type="refresh",
        ),
        "token_type": "bearer",
    }}


@router.delete("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Logout")
async def logout(current_user: CurrentUser, token: Annotated[str, Depends(...)]):
    from app.dependencies import oauth2_scheme
    # Token blocklist via Redis
    blocklist_token(token)
```

---

## 9. Service Layer

```python
# app/services/user_service.py
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import CreateUserRequest, UpdateUserRequest


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)

    async def get_by_id_or_404(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self.repo.get_by_email(email)

    async def list_users(
        self, page: int, per_page: int, search: str = ""
    ) -> tuple[list[User], int]:
        return await self.repo.list_paginated(page=page, per_page=per_page, search=search)

    async def create(self, payload: CreateUserRequest) -> User:
        if await self.repo.get_by_email(payload.email):
            raise ConflictError("Email already registered.")
        if await self.repo.get_by_username(payload.username):
            raise ConflictError("Username already taken.")

        user = User(
            email=payload.email,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        user.set_password(payload.password)
        return await self.repo.save(user)

    async def update(self, user: User, payload: UpdateUserRequest) -> User:
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        return await self.repo.save(user)

    async def delete(self, user: User) -> None:
        user.is_active = False
        await self.repo.save(user)

    async def record_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        await self.repo.save(user)
```

---

## 10. Repository Layer

```python
# app/repositories/user_repository.py
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def list_paginated(
        self, page: int, per_page: int, search: str = ""
    ) -> tuple[list[User], int]:
        query = select(User)

        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def save(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.commit()
```

---

## 11. Error Handling

```python
# app/exceptions.py
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


class ApiError(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}


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


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        payload = {"error": {"code": exc.error_code, "message": exc.message}}
        if exc.details:
            payload["error"]["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        formatted = {}
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            formatted.setdefault(field, []).append(error["msg"])

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed.",
                    "details": formatted,
                }
            },
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "CONFLICT",
                    "message": "A resource with that value already exists.",
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        import logging
        logging.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                }
            },
        )
```

---

## 12. Middleware

```python
# app/middleware.py
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        import logging
        logging.info(
            "HTTP %s %s %s %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "frame-ancestors 'none';"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response
```

---

## 13. Rate Limiting

```python
# Using slowapi (Starlette-compatible limiter)
# pip install slowapi

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# app/main.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# On routes
from slowapi import Limiter
from fastapi import Request

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest, db: DBSession):
    ...

# Per-user rate limiting after auth
@router.post("/upload")
@limiter.limit("10/hour", key_func=lambda request: str(request.state.user_id))
async def upload(request: Request, current_user: CurrentUser):
    ...
```

---

## 14. Caching

```python
# Using fastapi-cache2 with Redis
# pip install fastapi-cache2[redis]

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis.asyncio import from_url

# app/main.py lifespan startup
redis = from_url(str(settings.REDIS_URL), encoding="utf8", decode_responses=True)
FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

# On routes — caches full response
@router.get("/{product_id}", response_model=ProductResponse)
@cache(expire=300)
async def get_product(product_id: int, db: DBSession) -> Product:
    service = ProductService(db)
    return await service.get_by_id_or_404(product_id)


# Manual cache control in service
from fastapi_cache import FastAPICache

async def invalidate_product_cache(product_id: int) -> None:
    await FastAPICache.clear(namespace=f"product:{product_id}")
```

---

## 15. Background Tasks

```python
# app/api/v1/users.py
from fastapi import BackgroundTasks

@router.post("", status_code=201)
async def create_user(
    payload: CreateUserRequest,
    db: DBSession,
    background_tasks: BackgroundTasks,
):
    service = UserService(db)
    user = await service.create(payload)
    # Fire-and-forget — does not block the response
    background_tasks.add_task(send_welcome_email, user.email, user.first_name)
    return {"data": UserResponse.model_validate(user)}


async def send_welcome_email(email: str, first_name: str) -> None:
    """Runs after the response is sent. Use for lightweight async work."""
    # Use aiosmtplib or similar async email library
    ...


# For heavier workloads, use Celery or ARQ
# app/tasks.py
import arq

async def send_welcome_email_task(ctx, user_id: int) -> None:
    # ctx provides db session, settings etc.
    ...

class WorkerSettings:
    functions = [send_welcome_email_task]
    redis_settings = arq.connections.RedisSettings.from_dsn(settings.REDIS_URL)
```

---

## 16. File Uploads

```python
import os
import uuid

from fastapi import APIRouter, File, UploadFile, status

from app.exceptions import BadRequestError, ForbiddenError

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/users/{user_id}/avatar", response_model=dict)
async def upload_avatar(
    user_id: int,
    file: UploadFile = File(...),
    current_user: CurrentUser = ...,
):
    if current_user.id != user_id:
        raise ForbiddenError("You can only upload your own avatar.")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise BadRequestError("File type not allowed.")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise BadRequestError("File exceeds 5MB limit.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    # Save to object storage (S3, GCS) in production, not local filesystem
    save_path = os.path.join("uploads", unique_name)
    with open(save_path, "wb") as f:
        f.write(content)

    return {"data": {"filename": unique_name}}
```

---

## 17. Database Migrations (Alembic)

```bash
# Initialize
alembic init -t async alembic

# Generate migration after model change
alembic revision --autogenerate -m "add last_login_at to users"

# Always review generated migration before applying

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

```python
# alembic/env.py (async setup)
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.config import settings
from app.db.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

target_metadata = Base.metadata


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
```

---

## 18. Health Checks

```python
# app/api/v1/health.py
from fastapi import APIRouter
from sqlalchemy import text

from app.dependencies import DBSession

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Liveness probe")
async def health():
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness probe")
async def readiness(db: DBSession):
    checks: dict[str, str] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    try:
        from fastapi_cache import FastAPICache
        await FastAPICache.get_backend().get("__probe__")
        checks["cache"] = "ok"
    except Exception:
        checks["cache"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
```

---

## 19. Testing

### Test Configuration

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.dependencies import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, db: AsyncSession):
    await client.post("/api/v1/users", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "Test1234!",
        "first_name": "Test",
        "last_name": "User",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "Test1234!",
    })
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### Integration Tests

```python
# tests/integration/test_users.py
import pytest


@pytest.mark.asyncio
class TestCreateUser:
    async def test_creates_user_with_valid_data(self, client):
        response = await client.post("/api/v1/users", json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "Password1!",
            "first_name": "Alice",
            "last_name": "Smith",
        })

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["email"] == "alice@example.com"
        assert "password" not in data
        assert "password_hash" not in data

    async def test_rejects_duplicate_email(self, client):
        payload = {
            "email": "dup@example.com",
            "username": "unique",
            "password": "Password1!",
            "first_name": "Alice",
            "last_name": "Smith",
        }
        await client.post("/api/v1/users", json=payload)
        response = await client.post("/api/v1/users", json={**payload, "username": "other"})
        assert response.status_code == 409

    async def test_rejects_weak_password(self, client):
        response = await client.post("/api/v1/users", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "weakpassword",
            "first_name": "Test",
            "last_name": "User",
        })
        assert response.status_code == 422

    async def test_get_user_requires_auth(self, client):
        response = await client.get("/api/v1/users/1")
        assert response.status_code == 401

    async def test_get_user_returns_404(self, client, auth_headers):
        response = await client.get("/api/v1/users/99999", headers=auth_headers)
        assert response.status_code == 404
```

---

## 20. Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
```

### Production Settings

```bash
# For multi-worker production deployment
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools \
  --proxy-headers \
  --forwarded-allow-ips "*" \
  --log-level info

# Or via gunicorn with uvicorn workers
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --timeout 30 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50
```

---

## 21. Pagination

### Generic Paginated Response Model

```python
# app/utils/pagination.py
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PaginationMeta
```

### Pagination in Routes

```python
# app/api/v1/users.py
from app.utils.pagination import PaginatedResponse, PaginationMeta
from app.schemas.user import UserResponse


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List users",
)
async def list_users(
    db: DBSession,
    _: CurrentUser,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    search: Annotated[str, Query(max_length=100)] = "",
):
    service = UserService(db)
    items, total = await service.list_users(page=page, per_page=per_page, search=search)
    pages = (total + per_page - 1) // per_page
    return PaginatedResponse(
        data=items,
        meta=PaginationMeta(total=total, page=page, per_page=per_page, pages=pages),
    )
```

### Repository Pagination Pattern

```python
# app/repositories/user_repository.py
async def list_paginated(
    self, page: int, per_page: int, search: str = ""
) -> tuple[list[User], int]:
    query = select(User).where(User.is_active == True)

    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
            )
        )

    count_result = await self.db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await self.db.execute(query)
    return list(result.scalars().all()), total
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


# In a route — stateless, stable ordering required
@router.get("/events", response_model=dict, summary="List events (cursor)")
async def list_events(
    db: DBSession,
    _: CurrentUser,
    cursor: str | None = Query(None, description="Opaque cursor from previous response"),
    limit: int = Query(20, ge=1, le=100),
):
    from sqlalchemy import and_

    query = select(Event).order_by(Event.created_at.desc(), Event.id.desc())

    if cursor:
        pos = decode_cursor(cursor)
        query = query.where(
            or_(
                Event.created_at < pos["created_at"],
                and_(
                    Event.created_at == pos["created_at"],
                    Event.id < pos["id"],
                ),
            )
        )

    query = query.limit(limit + 1)
    result = await db.execute(query)
    items = list(result.scalars().all())

    next_cursor = None
    if len(items) > limit:
        items = items[:limit]
        last = items[-1]
        next_cursor = encode_cursor({"created_at": str(last.created_at), "id": last.id})

    return {"data": items, "meta": {"next_cursor": next_cursor, "limit": limit}}
```

---

## 22. API Versioning

### URL-Based Versioning (Recommended)

```python
# app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1 import auth, users, products

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(products.router, prefix="/products", tags=["Products"])
```

```python
# app/api/v2/__init__.py — new version adds/changes endpoints
from fastapi import APIRouter
from app.api.v2 import users as users_v2

api_v2_router = APIRouter()
api_v2_router.include_router(users_v2.router, prefix="/users", tags=["Users"])
```

```python
# app/main.py — register both versions
from app.api.v1 import api_v1_router
from app.api.v2 import api_v2_router

app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(api_v2_router, prefix="/api/v2")
```

### Versioned Schemas

```python
# app/schemas/user.py — extend v1 schema for v2 without breaking v1
class UserResponseV1(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserResponseV2(UserResponseV1):
    """V2 adds optional fields — backward compatible."""
    username: str
    avatar_url: str | None = None
    post_count: int = 0
```

```python
# app/api/v2/users.py — reuse same service, different response schema
from app.schemas.user import UserResponseV2

router = APIRouter()


@router.get("/{user_id}", response_model=UserResponseV2, summary="Get user (v2)")
async def get_user_v2(user_id: int, db: DBSession, _: CurrentUser):
    service = UserService(db)
    return await service.get_by_id_or_404(user_id)
```

### Header-Based Versioning (Alternative)

```python
# Useful when you cannot change URLs (client SDKs)
from fastapi import Header


async def require_api_version(
    x_api_version: str = Header(default="1.0"),
) -> str:
    supported = {"1.0", "2.0"}
    if x_api_version not in supported:
        raise BadRequestError(
            f"Supported versions: {sorted(supported)}",
        )
    return x_api_version


# Inject into route
@router.get("/users", dependencies=[Depends(require_api_version)])
async def list_users(...):
    ...
```

---

## 23. Security and CORS

### CORS

```python
# app/main.py — full CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,      # ["https://app.example.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)

# app/config.py
ALLOWED_ORIGINS: list[AnyHttpUrl] = []           # filled from env — never "*" in production
```

### Security Headers

```python
# app/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
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
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


# Register in app/main.py
app.add_middleware(SecurityHeadersMiddleware)
```

### Input Sanitization

```python
# pip install bleach
import bleach


def sanitize_html(value: str) -> str:
    """Strip all HTML tags. Use on every user-submitted text field."""
    return bleach.clean(value, tags=[], strip=True)


def sanitize_rich_content(value: str) -> str:
    """Allow a safe subset of HTML (for rich text editor input)."""
    return bleach.clean(
        value,
        tags=["b", "i", "em", "strong", "a", "ul", "ol", "li", "p", "br"],
        attributes={"a": ["href", "title"]},
        strip=True,
    )


# Use in Pydantic validators
class CreatePostRequest(BaseModel):
    title: str
    body: str

    @field_validator("title", "body", mode="before")
    @classmethod
    def strip_html(cls, v: str) -> str:
        return sanitize_html(v)
```

### JWT Security

```python
# Always specify the algorithm — never let the token header decide
from jose import JWTError, jwt

payload = jwt.decode(
    token,
    settings.SECRET_KEY,
    algorithms=[settings.ALGORITHM],  # explicit list — prevents algorithm confusion attacks
)

# Token revocation via Redis
import redis.asyncio as aioredis
from datetime import timedelta

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(str(settings.REDIS_URL))
    return _redis


async def blocklist_token(jti: str, expires_in: timedelta) -> None:
    r = await get_redis()
    await r.setex(f"jwt:blocklist:{jti}", int(expires_in.total_seconds()), "1")


async def is_token_revoked(jti: str) -> bool:
    r = await get_redis()
    return await r.exists(f"jwt:blocklist:{jti}") == 1
```

---

## 24. Logging

### Structured Logging Configuration

```python
# app/logging_config.py
import logging
import sys

try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False


def configure_logging(debug: bool = False) -> None:
    """Configure structured JSON logging for production, plain for development."""
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)

    if not debug and HAS_JSON_LOGGER:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)

    logging.basicConfig(level=level, handlers=[handler])

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if debug else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

```python
# app/main.py — call during lifespan startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.logging_config import configure_logging
    configure_logging(debug=settings.DEBUG)
    yield
```

### Request Logging Middleware

```python
# app/middleware.py
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "HTTP request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
        )

        return response
```

### Logging in Application Code

```python
# Always use module-level __name__ loggers — never the root logger
import logging

logger = logging.getLogger(__name__)


class UserService:
    async def create(self, payload: CreateUserRequest) -> User:
        logger.info("Creating user", extra={"email": payload.email})
        user = await self.repo.save(...)
        logger.info("User created", extra={"user_id": user.id})
        return user

    async def delete(self, user: User) -> None:
        logger.warning(
            "Deactivating user account",
            extra={"user_id": user.id, "email": user.email},
        )
        user.is_active = False
        await self.repo.save(user)
```

---

## 25. OpenAPI Documentation

### App-Level Metadata

```python
# app/main.py
app = FastAPI(
    title="My API",
    version="1.0.0",
    description="""
## My API

Complete API for managing users and products.

### Authentication
All endpoints except `POST /api/v1/users` and `POST /api/v1/auth/login` require a `Bearer` token.
""",
    contact={"name": "API Support", "email": "api@example.com"},
    license_info={"name": "Private"},
    openapi_tags=[
        {"name": "Authentication", "description": "Login, logout, token refresh"},
        {"name": "Users", "description": "User CRUD and profile management"},
        {"name": "Products", "description": "Product catalogue endpoints"},
        {"name": "Health", "description": "Liveness and readiness probes"},
    ],
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)
```

### Route-Level Metadata

```python
@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description="Registers a new user. Email and username must be unique.",
    responses={
        201: {"description": "User created successfully"},
        409: {
            "description": "Email or username already taken",
            "content": {
                "application/json": {
                    "example": {
                        "error": {"code": "CONFLICT", "message": "Email already registered."}
                    }
                }
            },
        },
        422: {"description": "Validation error"},
    },
    tags=["Users"],
)
async def create_user(payload: CreateUserRequest, db: DBSession):
    ...
```

### Global Security Scheme

```python
# app/main.py — inject Bearer auth into every operation
from fastapi.openapi.utils import get_openapi


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in schema["paths"].values():
        for operation in path.values():
            operation.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
```

### Hiding Internal Endpoints

```python
# Exclude from /docs and /openapi.json
@router.get("/internal/probe", include_in_schema=False)
async def internal_probe():
    return {"ok": True}
```

---

## 26. Filtering & Sorting

### Typed Query Parameters with Dependencies

```python
# app/schemas/filters.py
from datetime import datetime
from typing import Annotated, Literal

from fastapi import Depends, Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20


class UserFilterParams(PaginationParams):
    search: str = ""
    is_active: bool | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    sort_by: Literal["created_at", "email", "first_name"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


async def get_user_filters(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str, Query(max_length=100)] = "",
    is_active: bool | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    sort_by: Annotated[
        Literal["created_at", "email", "first_name"], Query()
    ] = "created_at",
    sort_order: Annotated[Literal["asc", "desc"], Query()] = "desc",
) -> UserFilterParams:
    """Dependency that parses and validates all filter query params."""
    return UserFilterParams(
        page=page,
        per_page=per_page,
        search=search,
        is_active=is_active,
        created_after=created_after,
        created_before=created_before,
        sort_by=sort_by,
        sort_order=sort_order,
    )


UserFilters = Annotated[UserFilterParams, Depends(get_user_filters)]
```

### Applying Filters in the Repository

```python
# app/repositories/user_repository.py
from sqlalchemy import asc, desc, or_, select, func

from app.models.user import User
from app.schemas.filters import UserFilterParams

SORT_FIELD_MAP = {
    "created_at": User.created_at,
    "email": User.email,
    "first_name": User.first_name,
}


class UserRepository:
    async def list_filtered(
        self, filters: UserFilterParams
    ) -> tuple[list[User], int]:
        query = select(User).where(User.is_active == True)

        if filters.search:
            pattern = f"%{filters.search}%"
            query = query.where(
                or_(
                    User.email.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )

        if filters.is_active is not None:
            query = query.where(User.is_active == filters.is_active)

        if filters.created_after:
            query = query.where(User.created_at >= filters.created_after)

        if filters.created_before:
            query = query.where(User.created_at <= filters.created_before)

        # Count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        # Sort — validate against allowlist
        sort_column = SORT_FIELD_MAP.get(filters.sort_by, User.created_at)
        direction = desc if filters.sort_order == "desc" else asc
        query = query.order_by(direction(sort_column))

        # Paginate
        query = query.offset((filters.page - 1) * filters.per_page).limit(filters.per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total
```

### Usage in Routes

```python
@router.get("", response_model=PaginatedResponse[UserResponse], summary="List users")
async def list_users(db: DBSession, _: CurrentUser, filters: UserFilters):
    service = UserService(db)
    items, total = await service.list_filtered(filters)
    pages = (total + filters.per_page - 1) // filters.per_page
    return PaginatedResponse(
        data=items,
        meta=PaginationMeta(
            total=total, page=filters.page, per_page=filters.per_page, pages=pages
        ),
    )
```

---

## 27. Database Transactions & Concurrency

### Explicit Transaction Boundaries

```python
# app/services/order_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError


class OrderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def place_order(self, user_id: int, items: list[dict]) -> "Order":
        """
        Place an order in a single transaction.
        Uses SELECT ... FOR UPDATE to lock inventory rows and prevent overselling.
        """
        async with self.db.begin_nested():
            order = Order(user_id=user_id, status="pending")
            self.db.add(order)

            for item in items:
                result = await self.db.execute(
                    select(Product)
                    .where(Product.id == item["product_id"])
                    .with_for_update()
                )
                product = result.scalar_one_or_none()

                if not product or product.stock < item["quantity"]:
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
                self.db.add(order_item)

        await self.db.commit()
        return order
```

### Optimistic Concurrency Control

```python
# app/db/base.py
class VersionedMixin:
    """Add a version column for optimistic concurrency control."""

    version: Mapped[int] = mapped_column(default=1, nullable=False)


# app/models/product.py
class Product(VersionedMixin, TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    stock: Mapped[int] = mapped_column(default=0, nullable=False)


# app/services/product_service.py
from sqlalchemy import update


class ProductService:
    async def update_with_version(
        self, product_id: int, data: dict, expected_version: int
    ) -> Product:
        """
        Update only if the version matches. Returns 409 if stale.
        """
        stmt = (
            update(Product)
            .where(Product.id == product_id, Product.version == expected_version)
            .values(**data, version=expected_version + 1)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        if result.rowcount == 0:
            raise ConflictError(
                "Resource was modified by another request. Reload and try again."
            )

        return await self.repo.get_by_id(product_id)
```

### Route with ETag / If-Match

```python
from typing import Annotated

from fastapi import Header
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    payload: UpdateProductRequest,
    db: DBSession,
    _: CurrentUser,
    if_match: Annotated[int, Header(alias="If-Match")] = ...,
):
    service = ProductService(db)
    product = await service.update_with_version(
        product_id, payload.model_dump(exclude_unset=True), if_match
    )
    return JSONResponse(
        content=jsonable_encoder(ProductResponse.model_validate(product)),
        headers={"ETag": str(product.version)},
    )
```

---

## 28. Idempotency Keys

### Redis-Backed Idempotency Handler

```python
# app/utils/idempotency.py
import hashlib
import json
from typing import Any

import redis.asyncio as aioredis

IDEMPOTENCY_TTL = 86400  # 24 hours


class IdempotencyHandler:
    """
    Stores and replays responses for POST requests that carry an Idempotency-Key header.
    Backed by Redis for distributed deployments.
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self.redis = redis_client

    async def get_cached_response(self, key: str) -> dict | None:
        raw = await self.redis.get(f"idempotency:{key}")
        if raw:
            return json.loads(raw)
        return None

    async def store_response(
        self, key: str, body_hash: str, response_body: Any, status_code: int
    ) -> None:
        await self.redis.setex(
            f"idempotency:{key}",
            IDEMPOTENCY_TTL,
            json.dumps({
                "body_hash": body_hash,
                "response_body": response_body,
                "status_code": status_code,
            }),
        )

    @staticmethod
    def hash_body(body: bytes) -> str:
        return hashlib.sha256(body).hexdigest()
```

### Usage in Routes

```python
from typing import Annotated

from fastapi import Header
from fastapi.responses import JSONResponse

from app.utils.idempotency import IdempotencyHandler
from app.utils.security import get_redis


@router.post("/orders", status_code=201, summary="Place order")
async def create_order(
    payload: CreateOrderRequest,
    db: DBSession,
    current_user: CurrentUser,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    if idempotency_key:
        handler = IdempotencyHandler(await get_redis())
        cached = await handler.get_cached_response(idempotency_key)
        if cached:
            return JSONResponse(
                content=cached["response_body"],
                status_code=cached["status_code"],
            )

    service = OrderService(db)
    order = await service.place_order(current_user.id, payload.items)
    response_data = {"data": OrderResponse.model_validate(order).model_dump(mode="json")}

    if idempotency_key:
        await handler.store_response(
            idempotency_key,
            body_hash=IdempotencyHandler.hash_body(payload.model_dump_json().encode()),
            response_body=response_data,
            status_code=201,
        )

    return JSONResponse(content=response_data, status_code=201)
```

---

## 29. External Service Resilience

### Async HTTP Client with Timeouts and Retries

```python
# app/utils/http_client.py
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0  # seconds
MAX_RETRIES = 3


def create_async_client(
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> httpx.AsyncClient:
    """Create an httpx async client with timeout and retry transport."""
    transport = httpx.AsyncHTTPTransport(retries=max_retries)
    return httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(timeout),
        follow_redirects=True,
    )


# Managed via lifespan — create on startup, close on shutdown
async_http_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    global async_http_client
    if async_http_client is None:
        async_http_client = create_async_client()
    return async_http_client
```

### Circuit Breaker

```python
# pip install aiobreaker
# app/utils/circuit_breaker.py
import logging

from aiobreaker import CircuitBreaker, CircuitBreakerListener

logger = logging.getLogger(__name__)


class LoggingListener(CircuitBreakerListener):
    async def state_change(self, cb, old_state, new_state):
        logger.warning(
            "Circuit breaker '%s': %s → %s", cb.name, old_state.name, new_state.name
        )


payment_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=30,
    listeners=[LoggingListener()],
    name="payment_gateway",
)


# app/services/payment_service.py
from aiobreaker import CircuitBreakerError

from app.utils.circuit_breaker import payment_breaker
from app.utils.http_client import get_http_client


class PaymentService:
    @staticmethod
    @payment_breaker
    async def charge(amount: int, currency: str, token: str) -> dict:
        """
        Call external payment gateway with circuit breaker protection.
        If the gateway fails 5 consecutive times, the circuit opens and calls
        fail fast for 30 seconds before allowing retries.
        """
        client = await get_http_client()
        response = await client.post(
            "https://api.payment-provider.com/v1/charges",
            json={"amount": amount, "currency": currency, "source": token},
        )
        response.raise_for_status()
        return response.json()
```

### Graceful Degradation

```python
from aiobreaker import CircuitBreakerError
import httpx

from app.exceptions import ApiError


@router.post("/checkout", summary="Checkout")
async def checkout(
    payload: CheckoutRequest, db: DBSession, current_user: CurrentUser
):
    try:
        payment = await PaymentService.charge(
            amount=payload.total,
            currency="usd",
            token=payload.payment_token,
        )
    except CircuitBreakerError:
        raise ApiError(
            "Payment service is temporarily unavailable. Try again later.",
        )
    except httpx.TimeoutException:
        raise ApiError(
            "Payment service timed out. Try again.",
        )
    ...
```

---

## 30. Bulk Operations & Streaming

### Batch Create

```python
# app/schemas/product.py
class BulkCreateProductRequest(BaseModel):
    items: list[CreateProductRequest] = Field(..., min_length=1, max_length=100)


# app/api/v1/products.py
@router.post("/bulk", status_code=201, summary="Bulk create products")
async def bulk_create_products(
    payload: BulkCreateProductRequest,
    db: DBSession,
    _: AdminUser,
):
    """
    Create up to 100 products in a single request.
    All succeed or all fail (transactional).
    """
    service = ProductService(db)
    products = await service.bulk_create(payload.items)
    return {"data": [ProductResponse.model_validate(p) for p in products]}
```

### Streaming Large Responses (CSV Export)

```python
import csv
import io

from fastapi.responses import StreamingResponse
from sqlalchemy import select


@router.get("/export", summary="Export users as CSV")
async def export_users(db: DBSession, _: AdminUser):
    """Stream users as CSV without loading all records into memory."""

    async def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "email", "first_name", "last_name", "created_at"])
        yield output.getvalue()

        offset = 0
        batch_size = 500

        while True:
            result = await db.execute(
                select(User)
                .where(User.is_active == True)
                .order_by(User.id)
                .offset(offset)
                .limit(batch_size)
            )
            users = result.scalars().all()

            if not users:
                break

            output = io.StringIO()
            writer = csv.writer(output)
            for user in users:
                writer.writerow([
                    user.id, user.email, user.first_name,
                    user.last_name, user.created_at.isoformat(),
                ])
            yield output.getvalue()
            offset += batch_size

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )
```

---

## 31. Anti-Patterns — Never Do These

- **Never put business logic in route handlers**: Routes coordinate — services decide
- **Never call the database directly from routes**: Always go through the service/repository layer
- **Never use synchronous database drivers** (e.g., `psycopg2`) with async FastAPI: Use `asyncpg` or `aiosqlite`
- **Never use `async def` for CPU-bound work without offloading** to a thread pool: Use `run_in_executor`
- **Never disable CORS in production with `allow_origins=["*"]`**: Restrict to known origins
- **Never return raw SQLAlchemy model objects** from routes: Always use Pydantic `response_model`
- **Never store secrets in code**: Use environment variables and `pydantic-settings`
- **Never skip `response_model`** on routes that return sensitive data: Uncontrolled fields leak
- **Never raise plain `Exception`**: Use custom `ApiError` subclasses for all error responses
- **Never ignore Alembic migration review**: Auto-generated migrations are not always correct
- **Never use `BackgroundTasks` for heavy or critical work**: Use a real task queue (ARQ, Celery)
- **Never suppress errors silently**: Log and surface them properly
- **Never share state via global variables in async code**: Use dependencies and request state
- **Never deploy without a readiness probe**: Know when the app is safe to receive traffic
- **Never store uploads on the container filesystem**: Use object storage (S3, GCS) in production
- **Never call external services without a timeout**: Set explicit timeouts on every HTTP call
- **Never retry failed requests without exponential backoff**: Prevents thundering herd on recovery
- **Never allow unbounded bulk operations**: Cap batch size and validate
- **Never overwrite concurrent changes silently**: Use optimistic concurrency control with version fields
- **Never allow arbitrary sort or filter fields from user input**: Validate against an explicit allowlist

---

## 32. Best Practices Summary

**Structure:**
- ✓ Use the application factory pattern via `create_app()`
- ✓ Use `pydantic-settings` for all configuration — fail fast on missing required values
- ✓ Use async SQLAlchemy with `asyncpg` for all database access
- ✓ Keep routes thin — delegate to service, service delegates to repository

**Data Access:**
- ✓ Use repository pattern for all database queries
- ✓ Use transactions for multi-step mutations with `begin_nested()`
- ✓ Use optimistic concurrency control with version fields for conflict-prone resources
- ✓ Use `SELECT ... FOR UPDATE` for inventory-style operations

**Validation & Filtering:**
- ✓ Use `response_model` on every route — never leak unintended fields
- ✓ Use `Annotated` type aliases for dependency injection to keep signatures clean
- ✓ Validate and whitelist all filter and sort parameters via typed dependencies

**API Design:**
- ✓ Version all APIs from day one (`/api/v1/`)
- ✓ Register all exception handlers centrally — never `try/except` in routes
- ✓ Paginate all list endpoints — never return unbounded collections (offset + cursor)
- ✓ Use idempotency keys for mutation endpoints

**Security:**
- ✓ Rate-limit authentication endpoints aggressively
- ✓ Use short-lived access tokens + refresh token rotation

**Resilience:**
- ✓ Set timeouts on all external HTTP calls
- ✓ Use circuit breakers for critical external dependencies
- ✓ Design for graceful degradation when non-critical services fail
- ✓ Stream large exports instead of loading into memory

**Testing:**
- ✓ Write async integration tests using `httpx.AsyncClient` and `pytest-asyncio`
- ✓ Use a lifespan context manager for startup/shutdown resource management
- ✓ Use Alembic for all schema changes — never mutate the database manually
