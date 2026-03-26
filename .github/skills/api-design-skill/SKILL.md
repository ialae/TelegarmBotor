---
name: api-design-skill
description: Best practices for designing RESTful APIs that are resilient, robust, scalable, secure, and maintainable. Covers Flask, FastAPI, and Django REST Framework. Use this skill whenever designing, writing, reviewing, or refactoring a Python REST API regardless of framework.
---

# API Design Skill — Framework Router

This skill covers the design and implementation of production-quality REST APIs in Python. It applies universal REST principles (resource naming, HTTP semantics, versioning, pagination, error shapes, authentication, rate limiting, security) and then delegates all framework-specific implementation guidance to the correct documentation file.

---

## How to Use This Skill

When a task involves writing, reviewing, or refactoring a Python REST API, follow this decision tree:

### Step 1 — Identify the framework

Look at the project's dependencies (`requirements.txt`, `pyproject.toml`, or `setup.cfg`):

- If it imports `flask` or `Flask-RESTful` → use the **Flask API documentation**
- If it imports `fastapi` → use the **FastAPI documentation**
- If it imports `djangorestframework` or `rest_framework` → use the **Django REST Framework documentation**
- If the framework is not yet decided, recommend **FastAPI** for new greenfield projects (best out-of-the-box type safety, async support, and automatic OpenAPI docs) or **Django REST Framework** for projects that need a full-featured admin, ORM, and batteries-included ecosystem

### Step 2 — Load the correct documentation

| Framework | Documentation file |
|-----------|--------------------|
| Flask | `\.github\skills\api-design-skill\Documentation\flask-documentation.md` |
| FastAPI | `\.github\skills\api-design-skill\Documentation\fastapi-documentation.md` |
| Django REST Framework | `\.github\skills\api-design-skill\Documentation\django-rest-documentation.md` |

Read the identified file in full before producing any code or review feedback.

---

## Universal REST Principles (apply to all frameworks)

Regardless of the framework in use, every API must follow these rules:

### Resource Naming
- Use plural nouns for collections: `/users`, `/orders`, `/products`
- Use path parameters for individual resources: `/users/{id}`
- Nest sub-resources at most one level deep: `/users/{id}/posts`
- Never use verbs in URLs: `/getUser` is wrong, `/users/{id}` with `GET` is correct
- Use kebab-case for multi-word segments: `/user-profiles`, not `/userProfiles`

### HTTP Method Semantics
- `GET` — read, safe, idempotent, never mutates state
- `POST` — create a new resource or trigger an action, not idempotent
- `PUT` — full replacement of a resource, idempotent
- `PATCH` — partial update of a resource, not necessarily idempotent
- `DELETE` — remove a resource, idempotent
- `OPTIONS` — for CORS preflight only

### HTTP Status Codes
- `200 OK` — successful GET, PATCH, PUT
- `201 Created` — successful POST that created a resource; include `Location` header
- `204 No Content` — successful DELETE or action with no body
- `400 Bad Request` — malformed request syntax
- `401 Unauthorized` — missing or invalid authentication
- `403 Forbidden` — authenticated but not authorized
- `404 Not Found` — resource does not exist
- `409 Conflict` — duplicate or state conflict
- `422 Unprocessable Entity` — validation errors on correct-syntax input
- `429 Too Many Requests` — rate limit exceeded
- `500 Internal Server Error` — unexpected server failure (never expose details)

### Response Envelope
All APIs must return a consistent JSON shape:

```json
// Success (single object)
{ "data": { ... } }

// Success (list with pagination)
{
  "data": [ ... ],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
  }
}

// Error
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed.",
    "details": { "email": ["Not a valid email address."] }
  }
}
```

### Versioning
- Version all APIs via URL prefix from day one: `/api/v1/`
- Never make breaking changes within a version
- A new breaking change always introduces a new version: `/api/v2/`
- Maintain at least one previous version after releasing a new one

### Pagination
- All list endpoints must be paginated — never return unbounded collections
- Use `page` + `per_page` query parameters
- Cap `per_page` at a server-enforced maximum (100 is a reasonable default)
- Always include total count and page metadata in the response

### Security (baseline for all frameworks)
- Authenticate every non-public endpoint
- Use short-lived access tokens (1 hour) with refresh token rotation
- Rate-limit all authentication endpoints (login, register, password reset)
- Validate and sanitize every input — body, query params, path params, headers
- Set security headers on every response (CSP, X-Frame-Options, HSTS, etc.)
- Never log passwords, tokens, or PII
- Use HTTPS everywhere — no exceptions
- Apply the principle of least privilege to every role and service account

### API Documentation
- Every endpoint must be documented (summary, parameters, request body, response shapes, error cases)
- Use OpenAPI 3.x as the specification format
- Keep documentation in-code (annotations/decorators) so it stays in sync with the implementation

### Filtering, Sorting, and Searching
- List endpoints must support filtering by relevant fields via query parameters
- Support sorting via a `sort_by` or `ordering` query parameter with a defined allowlist of fields
- Support search via a `search` query parameter that matches across relevant text fields
- Never allow arbitrary field filtering or sorting — always validate against an explicit allowlist
- Default sorting must be deterministic (e.g., `-created_at, id`) — never rely on database-default ordering

### Idempotency
- All `PUT` and `DELETE` operations must be inherently idempotent
- For `POST` endpoints that create resources or trigger actions, support an `Idempotency-Key` header
- Store idempotency keys with their responses; replay the stored response on duplicate requests
- Idempotency keys must expire after a reasonable TTL (24 hours is typical)
- Return `409 Conflict` if the same key is reused with a different request body

### Health Checks
- Every API must expose a liveness endpoint (`/health`) that returns `200` if the process is running
- Every API must expose a readiness endpoint (`/health/ready`) that checks all critical dependencies (database, cache, message broker)
- Health endpoints must not require authentication
- Return `503 Service Unavailable` from the readiness probe if any critical dependency is down

### CORS
- Configure CORS explicitly — never use wildcard (`*`) origins in production
- Restrict `allow_methods` and `allow_headers` to only what is needed
- Set a reasonable `max_age` for preflight caching (300–600 seconds)
- Expose only necessary response headers via `expose_headers`

### Resilience
- Set explicit timeouts on every external HTTP call, database query, and cache operation
- Use retries with exponential backoff for transient failures — never retry indefinitely
- Implement circuit breakers for high-traffic external dependencies
- Design every endpoint for graceful degradation — if a non-critical dependency fails, return partial data or a degraded response rather than a 500

### Concurrency Control
- Use optimistic concurrency control (version field or `updated_at` timestamp) for resources with concurrent write access
- Return `409 Conflict` when a concurrent modification is detected
- Never silently overwrite another client's changes

### Bulk Operations
- Support batch create, update, and delete where the domain requires it
- Cap the maximum batch size (100–500 items) and document the limit
- Return per-item results with individual success/error status codes
- Wrap bulk mutations in a database transaction — all succeed or all fail
