# Django REST Framework — Complete Implementation Guide

These instructions define a complete implementation guide for building scalable, secure, and production-ready REST APIs with Django REST Framework. Covers project structure, models, serializers, viewsets, routers, permissions, authentication, filtering, pagination, throttling, signals, testing, and deployment. Use this skill whenever writing, reviewing, or refactoring Django REST Framework code.

**One command runs the app:**

```bash
python manage.py runserver
```

---

## 1. Project Structure

### Recommended Layout

```
my_api/
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py          # Shared settings
│   │   ├── development.py
│   │   ├── testing.py
│   │   └── production.py
│   ├── urls.py              # Root URL config
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── filters.py       # django-filter FilterSets
│   │   ├── models.py
│   │   ├── permissions.py   # Custom DRF permissions
│   │   ├── serializers.py
│   │   ├── services.py      # Business logic
│   │   ├── signals.py
│   │   ├── urls.py          # App-level URL routing
│   │   └── views.py         # ViewSets
│   └── products/
│       └── ...              # Same structure
├── common/
│   ├── __init__.py
│   ├── exceptions.py        # Custom exception handler
│   ├── mixins.py            # Reusable ViewSet mixins
│   ├── pagination.py        # Pagination classes
│   ├── renderers.py         # Custom response renderers
│   └── utils.py
├── tests/
│   ├── conftest.py
│   ├── factories.py         # factory_boy model factories
│   ├── users/
│   │   ├── test_views.py
│   │   └── test_serializers.py
│   └── products/
├── .env.example
├── .env
├── manage.py
├── pyproject.toml
└── Dockerfile
```

---

## 2. Settings

### Split Settings Pattern

```python
# config/settings/base.py
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # Local apps
    "apps.users",
    "apps.products",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

AUTH_USER_MODEL = "users.User"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "common.renderers.EnvelopeRenderer",
    ],
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "login": "5/minute",
        "register": "3/hour",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# SimpleJWT
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    "TITLE": "My API",
    "DESCRIPTION": "My API documentation",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# Caching
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
```

```python
# config/settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
```

---

## 3. Custom User Model

### Always Define a Custom User Model First

```python
# apps/users/models.py
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str, **extra_fields) -> "User":
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=80, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
        ]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.email
```

---

## 4. Serializers

### Request and Response Serializers

```python
# apps/users/serializers.py
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Output serializer — safe fields only."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "full_name", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]


class CreateUserSerializer(serializers.ModelSerializer):
    """Input serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = ["email", "username", "password", "first_name", "last_name"]

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate_username(self, value: str) -> str:
        return value.lower().strip()

    def validate(self, attrs: dict) -> dict:
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError(
                {"email": "Email is already registered."},
                code="conflict",
            )
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError(
                {"username": "Username is already taken."},
                code="conflict",
            )
        return attrs

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    """Partial update serializer — no sensitive fields."""

    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True, min_length=8, validators=[validate_password]
    )

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must differ from current password."}
            )
        return attrs
```

---

## 5. ViewSets

### ModelViewSet with Granular Controls

```python
# apps/users/views.py
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.users.filters import UserFilter
from apps.users.models import User
from apps.users.permissions import IsSelfOrAdmin
from apps.users.serializers import (
    ChangePasswordSerializer,
    CreateUserSerializer,
    UpdateUserSerializer,
    UserSerializer,
)
from common.mixins import SerializerClassMixin


@extend_schema_view(
    list=extend_schema(summary="List users", tags=["Users"]),
    retrieve=extend_schema(summary="Get user", tags=["Users"]),
    create=extend_schema(summary="Create user", tags=["Users"]),
    partial_update=extend_schema(summary="Update user", tags=["Users"]),
    destroy=extend_schema(summary="Delete user", tags=["Users"]),
)
class UserViewSet(SerializerClassMixin, ModelViewSet):
    queryset = User.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = UserSerializer
    filterset_class = UserFilter
    search_fields = ["email", "first_name", "last_name", "username"]
    ordering_fields = ["created_at", "email", "first_name"]
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    serializer_classes = {
        "create": CreateUserSerializer,
        "partial_update": UpdateUserSerializer,
        "change_password": ChangePasswordSerializer,
    }

    permission_classes_by_action = {
        "create": [AllowAny],
        "list": [IsAuthenticated, IsAdminUser],
        "retrieve": [IsAuthenticated, IsSelfOrAdmin],
        "partial_update": [IsAuthenticated, IsSelfOrAdmin],
        "destroy": [IsAuthenticated, IsAdminUser],
        "change_password": [IsAuthenticated, IsSelfOrAdmin],
        "me": [IsAuthenticated],
    }

    def get_permissions(self):
        permissions = self.permission_classes_by_action.get(
            self.action, self.permission_classes
        )
        return [permission() for permission in permissions]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output = UserSerializer(user).data
        return Response({"data": output}, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance: User) -> None:
        """Soft delete — never hard delete users."""
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Return the authenticated user's own profile."""
        serializer = UserSerializer(request.user)
        return Response({"data": serializer.data})

    @action(detail=True, methods=["post"], url_path="change-password")
    def change_password(self, request, pk=None):
        """Change password for the specified user."""
        user = self.get_object()
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])

        return Response(
            {"data": {"message": "Password updated successfully."}},
            status=status.HTTP_200_OK,
        )
```

---

## 6. Mixins

```python
# common/mixins.py
class SerializerClassMixin:
    """
    Override get_serializer_class to allow per-action serializer mapping.
    Define serializer_classes = {"action_name": SerializerClass} on the ViewSet.
    """

    serializer_classes: dict = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, super().get_serializer_class())
```

---

## 7. URL Routing

```python
# apps/users/urls.py
from rest_framework.routers import DefaultRouter

from apps.users.views import UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = router.urls
```

```python
# config/urls.py
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.products.urls")),
    path("api/v1/auth/", include("apps.users.auth_urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
```

---

## 8. Authentication

### JWT Auth Views with SimpleJWT

```python
# apps/users/auth_urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.auth_views import LoginView, LogoutView

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
]
```

```python
# apps/users/auth_views.py
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


class LoginThrottle(AnonRateThrottle):
    rate = "5/minute"
    scope = "login"


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(
        request=LoginSerializer,
        summary="Login",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower()
        password = serializer.validated_data["password"]

        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            return Response(
                {"error": {"code": "UNAUTHORIZED", "message": "Invalid email or password."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": {"code": "ACCOUNT_DISABLED", "message": "Account is disabled."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at"])

        refresh = RefreshToken.for_user(user)

        from apps.users.serializers import UserSerializer

        return Response({
            "data": {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "token_type": "bearer",
                "user": UserSerializer(user).data,
            }
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Logout", tags=["Authentication"])
    def delete(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except TokenError:
            pass  # Already invalid — treat as success

        return Response(status=status.HTTP_204_NO_CONTENT)
```

---

## 9. Permissions

### Custom DRF Permissions

```python
# apps/users/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSelfOrAdmin(BasePermission):
    """
    Allow access if the authenticated user is accessing their own resource
    or is a staff/admin user.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        return obj == request.user or request.user.is_staff


class IsOwnerOrReadOnly(BasePermission):
    """Allow write access only to the resource owner."""

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAdminOrReadOnly(BasePermission):
    """Read access to all, write access to admins only."""

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
```

---

## 10. Filtering

```python
# apps/users/filters.py
import django_filters

from apps.users.models import User


class UserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(lookup_expr="icontains")
    username = django_filters.CharFilter(lookup_expr="icontains")
    is_active = django_filters.BooleanFilter()
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = User
        fields = ["email", "username", "is_active", "created_after", "created_before"]
```

---

## 11. Pagination

```python
# common/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "per_page"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response({
            "data": data,
            "meta": {
                "total": self.page.paginator.count,
                "page": self.page.number,
                "per_page": self.get_page_size(self.request),
                "pages": self.page.paginator.num_pages,
            },
        })

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "data": schema,
                "meta": {
                    "type": "object",
                    "properties": {
                        "total": {"type": "integer"},
                        "page": {"type": "integer"},
                        "per_page": {"type": "integer"},
                        "pages": {"type": "integer"},
                    },
                },
            },
        }
```

---

## 12. Exception Handling

```python
# common/exceptions.py
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

ERROR_CODE_MAP = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
}


def custom_exception_handler(exc, context):
    """
    DRF custom exception handler. Wraps all errors in a consistent envelope:
    { "error": { "code": "...", "message": "...", "details": {...} } }
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.message_dict)

    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled exception in %s", context.get("view"))
        return Response(
            {"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = ERROR_CODE_MAP.get(response.status_code, "ERROR")
    message = "An error occurred."
    details = None

    if isinstance(exc, ValidationError):
        # Route uniqueness/conflict validations to 409
        is_conflict = getattr(exc, "code", None) == "conflict" or (
            hasattr(exc.detail, "values")
            and any(
                "already" in str(v).lower()
                for v in exc.detail.values()
            )
        )
        if is_conflict:
            code = "CONFLICT"
            message = "A resource with that value already exists."
            details = response.data
            response.status_code = 409
        else:
            code = "VALIDATION_ERROR"
            message = "Input validation failed."
            details = response.data
    elif hasattr(response.data, "get"):
        message = response.data.get("detail", message)

    payload = {"error": {"code": code, "message": str(message)}}
    if details:
        payload["error"]["details"] = details

    response.data = payload
    return response
```

---

## 13. Response Renderer

```python
# common/renderers.py
from rest_framework.renderers import JSONRenderer


class EnvelopeRenderer(JSONRenderer):
    """
    Wraps non-paginated, non-enveloped responses in { "data": ... }.
    Paginated responses are already wrapped by the pagination class.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context:
            response = renderer_context.get("response")
            if response and response.status_code == 204:
                return b""
            # Already wrapped (pagination, errors, explicit data key)
            if isinstance(data, dict) and ("data" in data or "error" in data):
                return super().render(data, accepted_media_type, renderer_context)
            # Wrap bare data
            data = {"data": data}
        return super().render(data, accepted_media_type, renderer_context)
```

---

## 14. Service Layer

```python
# apps/users/services.py
from typing import Any

from django.db import transaction

from apps.users.models import User


class UserService:
    """
    Business logic layer. Never call ORM methods directly from views — use this layer.
    """

    @staticmethod
    @transaction.atomic
    def create_user(email: str, username: str, password: str, **kwargs) -> User:
        """
        Create user inside a transaction.
        Sends welcome email after commit via signal.
        """
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            **kwargs,
        )
        return user

    @staticmethod
    def deactivate_user(user: User) -> User:
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return user

    @staticmethod
    def set_avatar(user: User, filename: str) -> User:
        user.avatar = filename
        user.save(update_fields=["avatar", "updated_at"])
        return user
```

---

## 15. Signals

```python
# apps/users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import User


@receiver(post_save, sender=User)
def on_user_created(sender, instance: User, created: bool, **kwargs) -> None:
    """Triggered after a new user is saved. Schedules a welcome email."""
    if not created:
        return
    from apps.users.tasks import send_welcome_email
    send_welcome_email.delay(str(instance.id))


# Register signals in AppConfig
# apps/users/apps.py
from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "apps.users"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        import apps.users.signals  # noqa: F401
```

---

## 16. Background Tasks (Celery)

```python
# apps/users/tasks.py
import logging

from celery import shared_task
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id: str) -> None:
    """Send welcome email. Retries up to 3 times on transient failure."""
    try:
        user = User.objects.get(id=user_id)
        from apps.users.services import EmailService
        EmailService.send_welcome(user)
    except User.DoesNotExist:
        logger.warning("send_welcome_email: User %s not found.", user_id)
    except Exception as exc:
        logger.exception("send_welcome_email: Unexpected error for %s.", user_id)
        raise self.retry(exc=exc)
```

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("my_api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

---

## 17. Throttling

```python
# Custom throttle classes
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    rate = "5/minute"
    scope = "login"


class RegisterRateThrottle(AnonRateThrottle):
    rate = "3/hour"
    scope = "register"


class UploadRateThrottle(UserRateThrottle):
    rate = "10/hour"
    scope = "upload"


# On a view
class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]
    ...


# On a specific action
@action(detail=False, methods=["post"], throttle_classes=[RegisterRateThrottle])
def register(self, request):
    ...
```

---

## 18. File Uploads

```python
# apps/users/views.py
import os
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class UserViewSet(...):
    ...

    @action(detail=True, methods=["post"], url_path="avatar")
    def upload_avatar(self, request, pk=None):
        user = self.get_object()

        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": {"code": "BAD_REQUEST", "message": "No file uploaded."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file.content_type not in ALLOWED_IMAGE_TYPES:
            return Response(
                {"error": {"code": "BAD_REQUEST", "message": "File type not allowed."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file.size > MAX_FILE_SIZE:
            return Response(
                {"error": {"code": "BAD_REQUEST", "message": "File exceeds 5MB."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext = file.name.rsplit(".", 1)[-1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        # In production, use django-storages with S3/GCS, not local filesystem
        save_path = os.path.join(settings.MEDIA_ROOT, "avatars", unique_name)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb+") as f:
            for chunk in file.chunks():
                f.write(chunk)

        user.avatar = unique_name
        user.save(update_fields=["avatar", "updated_at"])

        return Response({"data": {"filename": unique_name}})
```

---

## 19. Health Checks

```python
# apps/health/views.py
from django.db import connection
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Liveness probe."""
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]  # Bypass EnvelopeRenderer for health checks

    def get(self, request):
        return Response({"status": "ok"})


class ReadinessView(APIView):
    """Readiness probe. Checks database and cache connectivity."""
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]  # Bypass EnvelopeRenderer for health checks

    def get(self, request):
        checks = {}

        try:
            connection.ensure_connection()
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"

        try:
            cache.set("__probe__", "1", timeout=5)
            checks["cache"] = "ok"
        except Exception:
            checks["cache"] = "error"

        all_ok = all(v == "ok" for v in checks.values())
        return Response(
            {"status": "ok" if all_ok else "degraded", "checks": checks},
            status=200 if all_ok else 503,
        )
```

---

## 20. Admin

```python
# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "full_name", "is_active", "is_staff", "created_at"]
    list_filter = ["is_active", "is_staff", "created_at"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at", "last_login_at"]

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Personal Info", {"fields": ("username", "first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Dates", {"fields": ("last_login_at", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "first_name", "last_name"),
        }),
    )
```

---

## 21. Testing

### Test Setup with Factories

```python
# tests/factories.py
import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "Test1234!")
        user = super()._create(model_class, *args, **kwargs)
        user.set_password(password)
        user.save()
        return user


class AdminFactory(UserFactory):
    is_staff = True
    is_superuser = True
```

```python
# tests/conftest.py
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from tests.factories import AdminFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def admin_user(db):
    return AdminFactory()


@pytest.fixture
def auth_client(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client
```

### Integration Tests

```python
# tests/users/test_views.py
import pytest


@pytest.mark.django_db
class TestCreateUser:
    url = "/api/v1/users/"

    def test_creates_user_with_valid_data(self, api_client):
        response = api_client.post(self.url, data={
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

    def test_rejects_duplicate_email(self, api_client, user):
        response = api_client.post(self.url, data={
            "email": user.email,
            "username": "newusername",
            "password": "Password1!",
            "first_name": "Alice",
            "last_name": "Smith",
        })

        assert response.status_code == 409

    def test_rejects_weak_password(self, api_client):
        response = api_client.post(self.url, data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "weakpassword",
            "first_name": "Test",
            "last_name": "User",
        })

        assert response.status_code == 422


@pytest.mark.django_db
class TestGetUser:
    def test_returns_404_for_missing_user(self, auth_client):
        response = auth_client.get("/api/v1/users/00000000-0000-0000-0000-000000000000/")
        assert response.status_code == 404

    def test_requires_authentication(self, api_client, user):
        response = api_client.get(f"/api/v1/users/{user.id}/")
        assert response.status_code == 401

    def test_user_can_read_own_profile(self, auth_client, user):
        response = auth_client.get(f"/api/v1/users/{user.id}/")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == str(user.id)

    def test_regular_user_cannot_read_others(self, auth_client, db):
        other_user = UserFactory()
        response = auth_client.get(f"/api/v1/users/{other_user.id}/")
        assert response.status_code == 403


@pytest.mark.django_db
class TestListUsers:
    def test_admin_can_list_users(self, admin_client, db):
        UserFactory.create_batch(3)
        response = admin_client.get("/api/v1/users/")
        assert response.status_code == 200
        assert response.json()["meta"]["total"] >= 3

    def test_regular_user_cannot_list(self, auth_client):
        response = auth_client.get("/api/v1/users/")
        assert response.status_code == 403
```

---

## 22. API Versioning

### URL-Based Versioning (Recommended)

```python
# config/urls.py — register each version as a separate include
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.api_v1.urls")),
    path("api/v2/", include("apps.api_v2.urls")),
]
```

```python
# apps/api_v1/urls.py
from rest_framework.routers import DefaultRouter
from apps.users.views_v1 import UserViewSetV1

app_name = "v1"
router = DefaultRouter()
router.register("users", UserViewSetV1, basename="user")
urlpatterns = router.urls
```

```python
# apps/api_v2/urls.py
from rest_framework.routers import DefaultRouter
from apps.users.views_v2 import UserViewSetV2

app_name = "v2"
router = DefaultRouter()
router.register("users", UserViewSetV2, basename="user")
urlpatterns = router.urls
```

### Reusing Logic Across Versions

```python
# views_v2.py — same service layer, different serializer
from apps.users.serializers_v2 import UserSerializerV2
from apps.users.views import UserViewSet as UserViewSetV1


class UserViewSetV2(UserViewSetV1):
    """V2 extends V1 — override only what changes."""

    serializer_class = UserSerializerV2

    # Additional action available only in v2
    @action(detail=True, methods=["get"], url_path="activity")
    def activity(self, request, pk=None):
        user = self.get_object()
        return Response({"data": {"last_login_at": user.last_login_at}})
```

```python
# schemas_v2.py — extend v1 schema with new fields
from apps.users.serializers import UserSerializer


class UserSerializerV2(UserSerializer):
    post_count = serializers.IntegerField(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["post_count", "avatar_url"]

    def get_avatar_url(self, obj) -> str | None:
        return obj.avatar.url if obj.avatar else None
```

### DRF Built-in Versioning Classes (Alternative)

```python
# URL path versioning via DRF's built-in class
# config/settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1", "v2"],
    "VERSION_PARAM": "version",
}

# config/urls.py
urlpatterns = [
    path("api/<version>/", include("apps.users.urls")),
]

# In a ViewSet — access the version via request.version
class UserViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.request.version == "v2":
            return UserSerializerV2
        return UserSerializer
```

---

## 23. Security and CORS

### CORS Configuration

```python
# pip install django-cors-headers
# config/settings/base.py
INSTALLED_APPS += ["corsheaders"]

# Must appear before CommonMiddleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    ...
]

# Development
CORS_ALLOW_ALL_ORIGINS = True  # development only — never in production

# Production (config/settings/production.py)
CORS_ALLOWED_ORIGINS = [
    "https://app.example.com",
    "https://admin.example.com",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "x-request-id",
]
CORS_EXPOSE_HEADERS = ["X-Request-ID"]
CORS_PREFLIGHT_MAX_AGE = 600
```

### Security Headers

```python
# config/settings/production.py
# Django built-in security middleware settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
```

```python
# common/middleware.py — additional headers not provided by Django
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Adds CSP and Permissions-Policy headers."""

    def process_response(self, request, response):
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "frame-ancestors 'none';"
        )
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response["X-Request-ID"] = getattr(request, "request_id", "")
        return response


# config/settings/base.py
MIDDLEWARE += ["common.middleware.SecurityHeadersMiddleware"]
```

### Input Sanitization

```python
# pip install bleach
import bleach


def sanitize_html(value: str) -> str:
    """Strip all HTML tags. Use for user-submitted plain-text fields."""
    return bleach.clean(value, tags=[], strip=True)


def sanitize_rich_content(value: str) -> str:
    """Allow a safe subset of HTML (for rich text editors)."""
    return bleach.clean(
        value,
        tags=["b", "i", "em", "strong", "a", "ul", "ol", "li", "p", "br"],
        attributes={"a": ["href", "title"]},
        strip=True,
    )


# Use in serializer validate_* methods
class CommentSerializer(serializers.ModelSerializer):
    def validate_body(self, value: str) -> str:
        return sanitize_html(value)
```

---

## 24. Logging

### Django Logging Configuration

```python
# config/settings/base.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
```

### Request Logging Middleware

```python
# common/middleware.py
import logging
import time
import uuid

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("apps.requests")


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request) -> None:
        request.request_id = str(uuid.uuid4())
        request._start_time = time.perf_counter()

    def process_response(self, request, response):
        duration_ms = round(
            (time.perf_counter() - getattr(request, "_start_time", time.perf_counter())) * 1000,
            2,
        )
        logger.info(
            "HTTP request",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id": getattr(request, "request_id", ""),
                "user_id": str(request.user.pk) if request.user.is_authenticated else None,
            },
        )
        response["X-Request-ID"] = getattr(request, "request_id", "")
        return response


# Register in settings
MIDDLEWARE += ["common.middleware.RequestLoggingMiddleware"]
```

### Logging in Application Code

```python
# Always use __name__ — do not use root logger in application code
import logging

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def create_user(email: str, **kwargs) -> User:
        logger.info("Creating user", extra={"email": email})
        user = User.objects.create_user(email=email, **kwargs)
        logger.info("User created", extra={"user_id": str(user.pk)})
        return user

    @staticmethod
    def deactivate_user(user: User) -> User:
        logger.warning(
            "Deactivating user",
            extra={"user_id": str(user.pk), "email": user.email},
        )
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return user
```

---

## 25. Caching

### Configuration

```python
# pip install django-redis
# config/settings/base.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "CONNECTION_POOL_KWARGS": {"max_connections": 20},
        },
        "KEY_PREFIX": "myapi",
        "TIMEOUT": 300,
    }
}
```

### View-Level Caching

```python
# Cache the entire ViewSet list response for 5 minutes
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


class ProductViewSet(ModelViewSet):
    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

### Service-Level Caching

```python
from django.core.cache import cache


class ProductService:
    CACHE_TTL = 300  # 5 minutes

    @staticmethod
    def get_by_id(product_id: int) -> "Product":
        cache_key = f"product:{product_id}"
        product = cache.get(cache_key)
        if product is None:
            product = Product.objects.select_related("category").get(pk=product_id)
            cache.set(cache_key, product, timeout=ProductService.CACHE_TTL)
        return product

    @staticmethod
    def invalidate(product_id: int) -> None:
        cache.delete(f"product:{product_id}")
        cache.delete_pattern("products:list:*")  # requires django-redis
```

### Signal-Based Cache Invalidation

```python
# apps/products/signals.py
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.products.models import Product


@receiver(post_save, sender=Product)
def invalidate_product_cache(sender, instance: Product, **kwargs) -> None:
    cache.delete(f"product:{instance.pk}")
    cache.delete_pattern("products:list:*")


@receiver(post_delete, sender=Product)
def on_product_deleted(sender, instance: Product, **kwargs) -> None:
    cache.delete(f"product:{instance.pk}")
```

### Low-Level Cache API

```python
cache.set("key", value, timeout=300)
cache.get("key", default=None)
cache.get_or_set("key", lambda: expensive_call(), timeout=300)
cache.delete("key")
cache.set_many({"k1": v1, "k2": v2}, timeout=300)
cache.get_many(["k1", "k2"])
cache.incr("counter")         # atomic increment
cache.delete_pattern("products:*")  # wildcard delete (django-redis only)
```

---

## 26. API Documentation (drf-spectacular)

### Setup

```python
# pip install drf-spectacular
# config/settings/base.py
INSTALLED_APPS += ["drf_spectacular"]

REST_FRAMEWORK = {
    ...
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "My API",
    "DESCRIPTION": "My API — complete reference documentation.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "COMPONENT_SPLIT_REQUEST": True,  # separate request vs response schemas
    "SORT_OPERATIONS": True,
    "CONTACT": {"name": "API Support", "email": "api@example.com"},
    "TAGS": [
        {"name": "Authentication", "description": "Login, logout, token refresh"},
        {"name": "Users", "description": "User CRUD and profile management"},
        {"name": "Products", "description": "Product catalogue endpoints"},
    ],
}
```

```python
# config/urls.py
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns += [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
```

### Annotating ViewSets

```python
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)


@extend_schema_view(
    list=extend_schema(
        summary="List users",
        description="Returns a paginated list of active users.",
        parameters=[
            OpenApiParameter("search", str, description="Search by email or name"),
            OpenApiParameter("page", int, description="Page number", default=1),
            OpenApiParameter("per_page", int, description="Items per page", default=20),
        ],
        responses={200: UserSerializer(many=True)},
        tags=["Users"],
    ),
    create=extend_schema(
        summary="Create user",
        request=CreateUserSerializer,
        responses={201: UserSerializer, 409: None},
        tags=["Users"],
    ),
    partial_update=extend_schema(
        summary="Update user",
        request=UpdateUserSerializer,
        responses={200: UserSerializer},
        tags=["Users"],
    ),
    destroy=extend_schema(
        summary="Delete user (soft)",
        responses={204: None},
        tags=["Users"],
    ),
)
class UserViewSet(ModelViewSet):
    ...
```

### Annotating Custom Actions

```python
@extend_schema(
    summary="Change password",
    request=ChangePasswordSerializer,
    responses={
        200: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: None,
    },
    tags=["Users"],
)
@action(detail=True, methods=["post"], url_path="change-password")
def change_password(self, request, pk=None):
    ...
```

### Response Examples

```python
@extend_schema(
    examples=[
        OpenApiExample(
            "Login success",
            value={
                "access_token": "eyJhbGciOi...",
                "refresh_token": "eyJhbGciOi...",
                "token_type": "bearer",
            },
            response_only=True,
            status_codes=["200"],
        ),
        OpenApiExample(
            "Invalid credentials",
            value={"error": {"code": "UNAUTHORIZED", "message": "Invalid email or password."}},
            response_only=True,
            status_codes=["401"],
        ),
    ],
    tags=["Authentication"],
)
class LoginView(APIView):
    ...
```

---

## 27. Database Migrations

```bash
# After any model change
python manage.py makemigrations --name "describe_change_here"

# Always review the generated migration file before applying
# Never edit squashed or applied migrations in production

# Apply
python manage.py migrate

# Rollback one step
python manage.py migrate users 0002  # back to migration 0002

# Squash old migrations (after all environments are up to date)
python manage.py squashmigrations users 0001 0010
```

---

## 28. Deployment

### Production Entry Point (gunicorn)

```bash
gunicorn config.wsgi:application \
  --workers 4 \
  --worker-class gevent \
  --bind 0.0.0.0:8000 \
  --timeout 30 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --access-logfile - \
  --error-logfile -
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

CMD ["gunicorn", "config.wsgi:application", \
     "--workers", "4", "--bind", "0.0.0.0:8000", "--timeout", "30"]
```

### Management Commands for Production

```bash
# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput

# Create superuser non-interactively
DJANGO_SUPERUSER_EMAIL=admin@example.com \
DJANGO_SUPERUSER_PASSWORD=securepass \
python manage.py createsuperuser --noinput --username admin
```

---

## 29. Repository Layer

### Data Access Abstraction

```python
# common/repositories.py
from typing import Generic, TypeVar

from django.db import models
from django.db.models import QuerySet

T = TypeVar("T", bound=models.Model)


class BaseRepository(Generic[T]):
    """
    Generic repository pattern. Wraps Django ORM queries.
    All database access goes through repositories — never call
    ORM methods from views or serializers directly.
    """

    model: type[T]

    def get_by_id(self, pk) -> T | None:
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def get_queryset(self) -> QuerySet[T]:
        return self.model.objects.all()

    def save(self, instance: T) -> T:
        instance.full_clean()
        instance.save()
        return instance

    def delete(self, instance: T) -> None:
        instance.delete()

    def exists(self, **kwargs) -> bool:
        return self.model.objects.filter(**kwargs).exists()
```

```python
# apps/users/repositories.py
from django.db.models import QuerySet

from apps.users.models import User
from common.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        try:
            return User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return None

    def get_by_username(self, username: str) -> User | None:
        try:
            return User.objects.get(username=username.lower())
        except User.DoesNotExist:
            return None

    def get_active_users(self) -> QuerySet[User]:
        return User.objects.filter(is_active=True)
```

---

## 30. Database Transactions & Concurrency

### Explicit Transaction Boundaries

```python
# apps/orders/services.py
from django.db import transaction
from rest_framework import serializers

from apps.orders.models import Order, OrderItem
from apps.products.models import Product


class OrderService:
    @staticmethod
    @transaction.atomic
    def place_order(user, items: list[dict]) -> Order:
        """
        Place an order inside a single database transaction.
        Uses select_for_update to lock product rows and prevent overselling.
        All succeed or all fail.
        """
        order = Order.objects.create(user=user, status="pending")

        for item in items:
            product = (
                Product.objects
                .select_for_update()
                .get(pk=item["product_id"])
            )

            if product.stock < item["quantity"]:
                raise serializers.ValidationError(
                    {"items": f"Insufficient stock for product {product.pk}."}
                )

            product.stock -= item["quantity"]
            product.save(update_fields=["stock", "updated_at"])

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                unit_price=product.price,
            )

        return order
```

### Optimistic Concurrency Control

```python
# common/mixins.py
from django.db import models


class VersionedMixin(models.Model):
    """Add a version field for optimistic concurrency control."""

    version = models.PositiveIntegerField(default=1)

    class Meta:
        abstract = True


# apps/products/models.py
class Product(VersionedMixin, models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# apps/products/services.py
from rest_framework.exceptions import ValidationError


class ProductService:
    @staticmethod
    def update_with_version(product_id, data: dict, expected_version: int):
        """
        Update only if the version matches. Returns 409 if stale.
        """
        rows_updated = Product.objects.filter(
            pk=product_id, version=expected_version
        ).update(**data, version=expected_version + 1)

        if rows_updated == 0:
            raise ValidationError(
                {"version": "Resource was modified by another request. Reload and try again."}
            )

        return Product.objects.get(pk=product_id)
```

### ViewSet with ETag Support

```python
@action(detail=True, methods=["patch"], url_path="versioned-update")
def versioned_update(self, request, pk=None):
    """Update with optimistic concurrency control via If-Match header."""
    expected_version = request.META.get("HTTP_IF_MATCH")
    if not expected_version:
        return Response(
            {"error": {"code": "BAD_REQUEST", "message": "If-Match header is required."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = UpdateProductSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product = ProductService.update_with_version(
        pk, serializer.validated_data, int(expected_version)
    )
    response = Response({"data": ProductSerializer(product).data})
    response["ETag"] = str(product.version)
    return response
```

---

## 31. Idempotency Keys

### Middleware for Idempotent POST Requests

```python
# common/idempotency.py
import hashlib
import json

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

IDEMPOTENCY_TTL = 86400  # 24 hours


class IdempotencyMiddleware(MiddlewareMixin):
    """
    For POST requests with an Idempotency-Key header, replay the stored
    response on duplicate requests instead of re-executing the view.
    """

    def process_request(self, request):
        if request.method != "POST":
            return None

        key = request.META.get("HTTP_IDEMPOTENCY_KEY")
        if not key:
            return None

        cache_key = f"idempotency:{key}"
        cached = cache.get(cache_key)
        body_hash = hashlib.sha256(request.body).hexdigest()

        if cached is None:
            request._idempotency_key = key
            request._idempotency_cache_key = cache_key
            request._idempotency_body_hash = body_hash
            return None

        if cached["body_hash"] != body_hash:
            return JsonResponse(
                {"error": {
                    "code": "CONFLICT",
                    "message": "Idempotency key reused with a different request body.",
                }},
                status=409,
            )

        return JsonResponse(cached["response_body"], status=cached["status_code"])

    def process_response(self, request, response):
        cache_key = getattr(request, "_idempotency_cache_key", None)
        if not cache_key:
            return response

        if 200 <= response.status_code < 300:
            try:
                response_body = json.loads(response.content)
            except (json.JSONDecodeError, ValueError):
                return response

            cache.set(cache_key, {
                "body_hash": getattr(request, "_idempotency_body_hash", ""),
                "response_body": response_body,
                "status_code": response.status_code,
            }, timeout=IDEMPOTENCY_TTL)

        return response


# config/settings/base.py
MIDDLEWARE += ["common.idempotency.IdempotencyMiddleware"]
```

---

## 32. External Service Resilience

### HTTP Client with Timeouts and Retries

```python
# common/http_client.py
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

### Circuit Breaker

```python
# pip install pybreaker
# common/circuit_breaker.py
import logging

import pybreaker

logger = logging.getLogger(__name__)


class LoggingListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        logger.warning(
            "Circuit breaker '%s': %s → %s", cb.name, old_state.name, new_state.name
        )


payment_circuit = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    listeners=[LoggingListener()],
    name="payment_gateway",
)


# apps/payments/services.py
from common.circuit_breaker import payment_circuit
from common.http_client import http_client


class PaymentService:
    @staticmethod
    @payment_circuit
    def charge(amount: int, currency: str, token: str) -> dict:
        """
        Call external payment gateway with circuit breaker protection.
        If the gateway fails 5 consecutive times, the circuit opens and calls
        fail fast for 30 seconds before allowing retries.
        """
        response = http_client.post(
            "https://api.payment-provider.com/v1/charges",
            json={"amount": amount, "currency": currency, "source": token},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
```

### Graceful Degradation in Views

```python
import pybreaker
import requests as req_lib

from rest_framework import status
from rest_framework.response import Response


class CheckoutView(APIView):
    def post(self, request):
        try:
            payment = PaymentService.charge(
                amount=data["total"],
                currency="usd",
                token=data["payment_token"],
            )
        except pybreaker.CircuitBreakerError:
            return Response(
                {"error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Payment service is temporarily unavailable.",
                }},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except req_lib.Timeout:
            return Response(
                {"error": {
                    "code": "GATEWAY_TIMEOUT",
                    "message": "Payment service timed out.",
                }},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        ...
```

---

## 33. Bulk Operations & Streaming

### Batch Create

```python
# apps/products/serializers.py
class BulkCreateProductSerializer(serializers.Serializer):
    items = CreateProductSerializer(many=True)

    def validate_items(self, value):
        if len(value) > 100:
            raise serializers.ValidationError("Maximum 100 items per batch.")
        return value


# apps/products/views.py
@action(detail=False, methods=["post"], url_path="bulk")
def bulk_create(self, request):
    """Create up to 100 products in a single transactional request."""
    serializer = BulkCreateProductSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        products = [
            Product.objects.create(**item)
            for item in serializer.validated_data["items"]
        ]

    return Response(
        {"data": ProductSerializer(products, many=True).data},
        status=status.HTTP_201_CREATED,
    )
```

### Streaming Large Responses (CSV Export)

```python
import csv

from django.http import StreamingHttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser


class UserViewSet(ModelViewSet):
    @action(
        detail=False,
        methods=["get"],
        url_path="export",
        permission_classes=[IsAdminUser],
    )
    def export(self, request):
        """Stream users as CSV without loading all into memory."""

        def generate():
            yield "id,email,first_name,last_name,created_at\n"

            queryset = User.objects.filter(is_active=True).order_by("id")
            batch_size = 500
            last_pk = 0

            while True:
                batch = list(queryset.filter(pk__gt=last_pk)[:batch_size])
                if not batch:
                    break

                for user in batch:
                    yield (
                        f"{user.pk},{user.email},{user.first_name},"
                        f"{user.last_name},{user.created_at.isoformat()}\n"
                    )
                last_pk = batch[-1].pk

        response = StreamingHttpResponse(generate(), content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=users.csv"
        return response
```

### Cursor-Based Pagination

```python
# common/pagination.py
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class StandardCursorPagination(CursorPagination):
    """
    Cursor-based pagination for large or frequently-updated datasets.
    More efficient than offset pagination for large tables.
    """

    page_size = 20
    page_size_query_param = "per_page"
    max_page_size = 100
    ordering = "-created_at"
    cursor_query_param = "cursor"

    def get_paginated_response(self, data):
        return Response({
            "data": data,
            "meta": {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "per_page": self.get_page_size(self.request),
            },
        })
```

---

## 34. Anti-Patterns — Never Do These

- **Never put business logic in serializers or views**: Use a service layer
- **Never expose model fields directly without a serializer**: Always control output shape
- **Never skip defining a custom user model before the first migration**: It is extremely difficult to change later
- **Never hardcode `AUTH_USER_MODEL = "auth.User"`**: Always use a custom model
- **Never use `objects.all()` in views without filtering or pagination**: Always bound the query
- **Never select `*` with `.values()` or serializer `fields = "__all__"`**: Be explicit
- **Never allow hard deletes on user accounts**: Use soft delete (is_active)
- **Never run `manage.py migrate` in application code**: Run it at deploy time only
- **Never edit applied migrations in production**: Create a new migration
- **Never use `DEBUG=True` in production**: Exposes internals
- **Never return HTTP 200 for an error**: Use proper status codes
- **Never suppress DRF exceptions silently**: Use `EXCEPTION_HANDLER` setting
- **Never store secrets in `settings.py`**: Use environment variables
- **Never skip `db_index=True` on foreign keys and frequently filtered fields**: Index them
- **Never use `django.contrib.auth.User` directly**: Always proxy via `get_user_model()`
- **Never use synchronous tasks for slow operations in a request**: Use Celery
- **Never store uploads on the container filesystem**: Use `django-storages` with S3/GCS
- **Never skip writing `Meta.ordering`**: Unpredictable ordering breaks pagination
- **Never allow CORS `allow_origins=["*"]` in production**: Restrict to known origins
- **Never call external services without a timeout**: Set explicit timeouts on every HTTP call
- **Never retry failed requests without exponential backoff**: Prevents thundering herd on recovery
- **Never allow unbounded bulk operations**: Cap batch size and validate
- **Never overwrite concurrent changes silently**: Use optimistic concurrency control with version fields

---

## 35. Best Practices Summary

**Structure:**
- ✓ Split settings into base, development, testing, production
- ✓ Use feature-based app structure under `apps/`
- ✓ Separate views, serializers, services, repositories, permissions per app
- ✓ Register routes via DRF `DefaultRouter`

**Models:**
- ✓ Define a custom user model before the first migration
- ✓ Use UUIDs as primary keys for user-facing models
- ✓ Index all `ForeignKey`, filter, and search fields
- ✓ Use `auto_now_add` / `auto_now` for timestamps

**Data Access:**
- ✓ Use repository pattern for all database queries
- ✓ Use `@transaction.atomic` for multi-step mutations
- ✓ Use `select_for_update()` for inventory-style operations
- ✓ Use optimistic concurrency control with version fields for conflict-prone resources

**Serializers:**
- ✓ Use separate serializers for input and output
- ✓ Use `write_only=True` for passwords and tokens
- ✓ Use `read_only_fields` for `id`, timestamps, computed fields
- ✓ Validate and normalize in `validate_*` methods

**ViewSets:**
- ✓ Use `ModelViewSet` with explicit `http_method_names`
- ✓ Map per-action permissions and serializer classes
- ✓ Use `@action` for non-CRUD endpoints
- ✓ Keep action methods thin — delegate to service layer

**Security:**
- ✓ Use SimpleJWT with short-lived tokens and rotation
- ✓ Enable token blacklisting on logout
- ✓ Apply throttling on login, registration, and upload endpoints
- ✓ Set all security settings in production config

**Resilience:**
- ✓ Set timeouts on all external HTTP calls
- ✓ Use circuit breakers for critical external dependencies
- ✓ Use idempotency keys for mutation endpoints
- ✓ Design for graceful degradation when non-critical services fail
- ✓ Stream large exports instead of loading into memory

**Testing:**
- ✓ Use `factory_boy` for model creation
- ✓ Use `APIClient` and JWT fixtures for auth
- ✓ Test auth boundaries — every protected endpoint
- ✓ Use `@pytest.mark.django_db` sparingly — prefer `db` fixture via conftest
