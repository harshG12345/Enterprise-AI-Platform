# Enterprise AI Platform: Authentication & RBAC Specification

## 1. Overview
The platform implements a stateless **JSON Web Token (JWT)** authentication architecture with **Argon2id** password hashing and **Role-Based Access Control (RBAC)** enforced at the API gateway layer.

---

## 2. Authentication Flow

```
+----------------+               +------------------+               +--------------------+
|  React Client  |               | FastAPI Gateway  |               | PostgreSQL / Store |
+-------+--------+               +--------+---------+               +---------+----------+
        |                                 |                                   |
        | 1. POST /api/v1/auth/register   |                                   |
        |-------------------------------->| 2. Argon2 Hash & Validate         |
        |                                 |---------------------------------->|
        |                                 | 3. Create User & Audit Log        |
        | 4. 201 Created (User Profile)   |<----------------------------------|
        |<--------------------------------|                                   |
        |                                 |                                   |
        | 5. POST /api/v1/auth/login      |                                   |
        |-------------------------------->| 6. Verify Argon2 Hash             |
        |                                 |---------------------------------->|
        |                                 | 7. Generate Signed JWT            |
        | 8. 200 OK (access_token, exp)   |<----------------------------------|
        |<--------------------------------|                                   |
        |                                 |                                   |
        | 9. GET /api/v1/users/me (Bearer)|                                   |
        |-------------------------------->| 10. Verify JWT & Extract Sub ID   |
        |                                 |---------------------------------->|
        | 11. 200 OK (User Profile Data)  |<----------------------------------|
        |<--------------------------------|                                   |
```

---

## 3. Role-Based Access Control (RBAC) Matrix

| Resource / Capability | ADMIN | DATA_SCIENTIST | USER |
|---|---|---|---|
| **User Management** | Full CRUD | None | None |
| **System Audit Logs** | Read All | None | None |
| **Project Management** | All Projects | Own Projects | Assigned / Read |
| **Dataset Ingestion & EDA** | Full | Full | Read Only |
| **Model Training & Tuning** | Full | Full | None |
| **Model Registry & Promotion** | Full | Staging Only | None |
| **Model Inference (Single/Batch)**| Full | Full | Full |
| **Drift & Health Monitoring** | Full | Full | Read Only |

---

## 4. Password Security Standards
- Minimum length: 8 characters
- Complexity: At least 1 uppercase, 1 lowercase, and 1 numeric digit
- Algorithm: `Argon2id` via `passlib[argon2]` with automatic salts and memory cost parameters
- Rate Limiting & Audit: Every failed and successful authentication event is recorded in the `audit_logs` table with IP address and timestamp.
