# Enterprise AI Platform: Production Security & Compliance Guide

## 1. AUTHENTICATION & ACCESS CONTROL (RBAC)

### Password Hashing
- **Algorithms**: Argon2id (`argon2-cffi`) with Bcrypt fallback.
- **Salt Generation**: Cryptographically secure random 16-byte salts per credential.
- **Verification**: Constant-time verification preventing timing side-channel attacks.

### Token Architecture
- **Type**: Signed JSON Web Tokens (JWT) adhering to RFC 7519.
- **Algorithm**: `HS256` HMAC with SHA-256 (32+ character minimum entropy key).
- **Expiration**: Default 60 minutes with UTC timezone validation (`exp`, `iat`).

### Role-Based Access Control Matrix
| Role | Workspaces | Dataset Upload | ML Training | Stage Promotion | User Admin |
|---|---|---|---|---|---|
| `ADMIN` | All Projects | Full Access | Full Access | Full Access | Full Access |
| `ML_ENGINEER` | Assigned Projects | Full Access | Full Access | Staging / Prod | Read-Only |
| `DATA_SCIENTIST` | Assigned Projects | Full Access | Full Access | Staging Only | Read-Only |
| `VIEWER` | Assigned Projects | Read-Only | Read-Only | Read-Only | No Access |

---

## 2. API RATE LIMITING & DOS DEFENSE

The platform enforces tiered sliding window rate limiting via `app.core.rate_limiter.RateLimitMiddleware`:

| Endpoint Class | Rate Limit Quota | Window | Burst Handling |
|---|---|---|---|
| **Authentication** (`/api/v1/auth/*`) | 30 requests | 60 seconds | `429 Too Many Requests` + `Retry-After` |
| **Realtime Prediction** (`/api/v1/predictions/realtime`) | 120 requests | 60 seconds | `429 Too Many Requests` + `Retry-After` |
| **Standard API** (`/api/v1/*`) | 300 requests | 60 seconds | `429 Too Many Requests` + `Retry-After` |
| **Health & Metrics** (`/health`, `/metrics`) | Whitelisted | - | Unlimited |

---

## 3. PATH TRAVERSAL & FILE UPLOAD HARDENING

All file operations pass through `app.core.sanitizer`:
1. **Filename Sanitization**: Replaces directory paths, non-alphanumeric characters, and null bytes (`\x00`) with safe underscores.
2. **Canonical Path Assertion**: Validates `os.path.realpath` against base storage root to prevent escape attempts via symlinks or `../` sequences.
3. **Extension Whitelisting**: Strictly restricts uploads to tabular extensions: `.csv`, `.xlsx`, `.xls`, `.parquet`, `.json`.
4. **File Size Enforcement**: Caps single file uploads at 250MB (HTTP 413 response on violation).

---

## 4. HTTP SECURITY HEADERS SPECIFICATION

Every API response enforces modern OWASP security headers:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=()`
- `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' http: https: ws: wss:; frame-ancestors 'none';`
