# Production Hardening Implementation Plan

**Objective**: Harden the existing Enterprise AI Platform for enterprise production readiness while strictly preserving all existing UI, page structure, navigation, API contracts, and working functionality.

---

## 1. Scope & Hardening Checklist

### Priority 1: Security & Environment Hardening
- **Secrets & Token Expiration**: Enforce environment validation for `SECRET_KEY`, `JWT_ALGORITHM`, and token expiration limits in [`settings.py`](file:///d:/.gemini/antigravity-ide/scratch/enterprise-ai-platform/backend/app/config/settings.py).
- **CORS & Rate Limiting**: Ensure trusted origin matching and robust fallback in `assemble_cors_origins`.
- **Database Connection Pool Parameters**: Configure explicit production pool parameters (`pool_size=20`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800`, `pool_pre_ping=True`) in [`database.py`](file:///d:/.gemini/antigravity-ide/scratch/enterprise-ai-platform/backend/app/database/database.py).

### Priority 2: Backend Reliability & Deep Health Checks
- **Deep Readiness Probe**: Update `/api/v1/health/ready` in [`health.py`](file:///d:/.gemini/antigravity-ide/scratch/enterprise-ai-platform/backend/app/api/v1/health.py) to perform live asynchronous connectivity pings to PostgreSQL (`SELECT 1`), Redis (`ping`), and MLflow tracking server with timeouts and graceful degradation reporting.
- **Audit Logs REST Endpoint**: Create `GET /api/v1/audit-logs` in [`audit_logs.py`](file:///d:/.gemini/antigravity-ide/scratch/enterprise-ai-platform/backend/app/api/v1/audit_logs.py) to expose real-time audit records stored in the `audit_logs` table.

### Priority 3 & 4: ML & MLOps Reliability
- **Dataset Pre-flight Validation**: Enhance dataset and target column validation in [`trainer.py`](file:///d:/.gemini/antigravity-ide/scratch/enterprise-ai-platform/backend/app/ml/trainer.py) and [`training_service.py`](file:///d:/.gemini/antigravity-ide/scratch/enterprise-ai-platform/backend/app/services/training_service.py) (preventing division by zero, all-NaN columns, target distribution anomalies, and insufficient sample sizes).
- **Celery Worker Task Resilience**: Add retry configurations (`max_retries=3`, `default_retry_delay=5`) on Celery training and prediction tasks to handle transient storage or network glitches.

### Priority 5: Database & Alembic Migration Integrity
- **Alembic Migration Revision 0002**: Create [`0002_add_notifications.py`](file:///d:/.gemini/antigravity-ide/scratch/enterprise-ai-platform/backend/alembic/versions/0002_add_notifications.py) linking to `0001_initial_schema` to maintain 100% linear migration history for the `notifications` table.

### Priority 6 & 7: Frontend & Observability
- **Settings Audit Logs Query**: Connect Settings UI to the new audit logs endpoint while preserving existing layout and styling.
- **Form Submission Protection**: Prevent accidental duplicate submissions on training and inference forms.

---

## 2. Proposed Changes by Component

### Component 1: Database & Migrations
- **[NEW]** `backend/alembic/versions/0002_add_notifications.py`: Migration for `notifications` table, indexes, and foreign keys.
- **[MODIFY]** `backend/app/database/database.py`: Production connection pooling settings.

### Component 2: Security & Configuration
- **[MODIFY]** `backend/app/config/settings.py`: Add pool configuration fields and production secret checks.
- **[NEW]** `backend/app/api/v1/audit_logs.py`: Read-only audit log endpoint.
- **[MODIFY]** `backend/app/main.py`: Register `audit_logs_router`.

### Component 3: Backend Observability & Deep Readiness
- **[MODIFY]** `backend/app/api/v1/health.py`: Live asynchronous ping checks for PostgreSQL, Redis, and MLflow in `/ready`.

### Component 4: ML & Celery Worker Resilience
- **[MODIFY]** `backend/app/tasks/training_tasks.py`: Add task retry policy.
- **[MODIFY]** `backend/app/tasks/prediction_tasks.py`: Add task retry policy.
- **[MODIFY]** `backend/app/ml/trainer.py`: Add target column and dataset sanity assertions.

### Component 5: Test Suite Verification
- **[NEW]** `backend/tests/unit/test_health_and_audit.py`: Verify deep readiness probe and audit log query endpoints.

---

## 3. Verification Plan

### Automated Tests
```bash
# Run complete test suite (Unit, Integration, Security, Health)
pytest backend/tests/ -v
```

### Static Analysis
```bash
ruff check backend/
ruff format --check backend/
npx tsc --noEmit
```
