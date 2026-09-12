# Enterprise AI Data Science & MLOps Platform
## System Architecture & Technical Specification

### 1. Executive Overview & System Topology

The **Enterprise AI Data Science & MLOps Platform** is an enterprise-grade, full-lifecycle machine learning and data science system designed to orchestrate the journey from raw tabular data ingestion to validated production inference, drift detection, and automated governance.

```
                                  +---------------------------------------+
                                  |                CLIENTS                |
                                  |     (React 18 / TypeScript SPA)      |
                                  +-------------------+-------------------+
                                                      |
                                             HTTPS / WSS / REST
                                                      |
                                                      v
+-----------------------------------------------------+-----------------------------------------------------+
|                                                  NGINX                                                    |
|                                       (Reverse Proxy & SSL Term)                                         |
+-----------------------------------------------------+-----------------------------------------------------+
                          |                                                   |
                          | /api/v1/*                                         | /* (Static Assets)
                          v                                                   v
+-----------------------------------------------------+     +-----------------------------------------------+
|                 FASTAPI BACKEND                      |     |            VITE / REACT CLIENT                |
|  - Pydantic v2 Contract Validation                  |     |  - TanStack Query v5 Server State             |
|  - JWT + Argon2 RBAC Enforcement                    |     |  - Tailwind CSS + shadcn/ui Design Tokens     |
|  - Request ID Tracing Middleware                     |     |  - Recharts / Plotly Visualizations           |
|  - Storage Abstraction Layer                         |     |  - React Hook Form + Zod Strict Schemas       |
|  - RESTful API Routers (v1)                         |     +-----------------------------------------------+
+-----------------------------------------------------+
      |                   |                     |                   |
      | Metadata & State  | Caching & Broker   | Experiment Store  | Raw Files & Artifacts
      v                   v                     v                   v
+--------------+    +------------+       +--------------+    +-----------------------+
|  POSTGRESQL  |    |   REDIS    |       |    MLFLOW    |    | LOCAL / S3 STORAGE    |
|   (SQLAlchemy|    |  (Celery   |       |  TRACKING    |    |  - Uploaded Datasets  |
|    2 + Async)|    |   Broker)  |       |   SERVER     |    |  - Serialized Models  |
+--------------+    +------------+       +--------------+    +-----------------------+
                          |
                          v
+---------------------------------------------------------------------------------------------------+
|                                      CELERY WORKER POOL                                           |
|  - Task Layer: Isolated Execution Contexts                                                        |
|  - ML Pipeline Engine: Task Detection, Preprocessing, Cross-Validation, Hyperparameter Tuning     |
|  - Evaluation Engine: Classification & Regression Metrics + Residuals/ROC/PR-AUC                  |
|  - Serialization: joblib Safe Pipelines with Immutability Checks                                  |
|  - MLflow Integration: Automatic Metric, Param & Artifact Registration                            |
+---------------------------------------------------------------------------------------------------+
      |                                                                             |
      v Metrics                                                                     v Alerts & Logs
+----------------------------------+                              +---------------------------------+
|        PROMETHEUS METRICS        |                              |       GRAFANA DASHBOARDS        |
|  - HTTP Latency & Throughput     |                              |  - System Health & Node Metrics |
|  - ML Training Queue Latency     |                              |  - Inference Latency Heatmaps   |
|  - Real-Time Inference Latency   |                              |  - Feature Drift Gauges & Alarms|
|  - Model Drift PSI/KS Metrics    |                              |                                 |
+----------------------------------+                              +---------------------------------+
```

---

### 2. Multi-Layer Separation of Concerns

1. **Presentation Layer (Frontend)**:
   - Client-side routing with `react-router-dom` v6.
   - Authentication guard (`ProtectedRoute.tsx`, `RoleRoute.tsx`).
   - Server-state synchronization via `@tanstack/react-query`.
   - Form handling with `@hookform/resolvers/zod` guaranteeing zero invalid inputs before network dispatch.
   - Pure presentation components decoupled from business logic.

2. **API & Security Gateway Layer (FastAPI)**:
   - Request-ID tracking (`X-Request-ID` header injected and logged across all spans).
   - Rate limiting, CORS origin sanitization, Trusted Host enforcement, and Secure Security Headers (`Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options: DENY`).
   - JWT validation with Argon2 password hashing. Role-Based Access Control (`ADMIN`, `DATA_SCIENTIST`, `USER`).
   - Unified API Response format (`APIResponse[T]` & `APIErrorResponse`).

3. **Domain Service Layer**:
   - Encapsulates enterprise business logic: project lifecycle, dataset versioning, schema detection, model promotion gating, prediction orchestration, drift calculation.
   - Decoupled from transport mechanism (FastAPI dependencies supply repository sessions; Celery tasks instantiate independent unit-of-work sessions).

4. **Data Access & Storage Layer**:
   - SQLAlchemy 2.0 with strict typed mappings (`Mapped[...]`).
   - Alembic migration version control (all schema updates version-tracked).
   - Storage Abstraction Layer (`StorageBackend` interface with `LocalStorageBackend` and `S3StorageBackend` implementations) ensuring file system portability.

5. **Asynchronous ML & Worker Layer**:
   - Celery with Redis broker and result backend.
   - Strict serialization protocol: ONLY primitive identifiers (`dataset_id: str`, `target_col: str`, `user_id: str`) are passed across queues.
   - Automatic execution of:
     - Dataset Validation & Summary Statistics
     - Exploratory Data Analysis (EDA)
     - Scikit-learn Pipeline Construction (`ColumnTransformer` with zero data leakage)
     - Multi-Model Parallel/Sequential Training & Evaluation
     - MLflow Experiment and Run Logging
     - Model Serialization & Checksum Hashing

6. **Monitoring & Drift Engine**:
   - Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) test evaluations comparing production inference inputs against baseline training feature distributions.
   - Prometheus metrics exporter emitting custom counters and histograms.

---

### 3. Naming Conventions & Code Style Guidelines

- **Python (Backend)**:
  - Modules & Packages: `snake_case` (e.g., `dataset_service.py`, `task_detector.py`)
  - Classes: `PascalCase` (e.g., `TrainedModel`, `DatasetValidator`)
  - Functions & Variables: `snake_case` (e.g., `calculate_eda_summary`, `mlflow_run_id`)
  - Constants & Enums: `UPPER_SNAKE_CASE` (e.g., `MAX_UPLOAD_SIZE_BYTES`, `ModelStatus.PRODUCTION`)
  - Typing: Strict Python type hints on all signatures with Pydantic v2 schemas.
- **TypeScript / React (Frontend)**:
  - Components & Layouts: `PascalCase.tsx` (e.g., `DashboardLayout.tsx`, `DatasetPreviewTable.tsx`)
  - Hooks: `camelCase.ts` prefixed with `use` (e.g., `useProjects.ts`, `useTrainingJob.ts`)
  - Utilities & Services: `camelCase.ts` (e.g., `formatBytes.ts`, `authClient.ts`)
  - Types & Interfaces: `PascalCase` (e.g., `Project`, `DatasetMetadata`, `ModelMetrics`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`, `POLLING_INTERVAL_MS`)
- **Database**:
  - Tables: Plural `snake_case` (e.g., `users`, `projects`, `datasets`, `trained_models`)
  - Foreign Keys: Singular reference `snake_case` (e.g., `project_id`, `owner_id`)
  - Indexes: `ix_<table>_<columns>`
  - Constraints: `fk_<table>_<column>_<ref_table>`, `uq_<table>_<column>`

---

### 4. Enterprise Security Architecture

- **Authentication Protocol**: Access tokens issued via JWT with cryptographic HS256/RS256, expiration configured via settings, refresh token lifecycle support.
- **Password Security**: Argon2id hashing algorithm with random salting.
- **Path Traversal Protection**: All uploaded file operations strictly resolve paths inside the configured secure base directory using canonical path resolution.
- **Data Leakage Elimination**: Preprocessing pipelines (`StandardScaler`, `OneHotEncoder`, `SimpleImputer`) are strictly fitted on the training split only during cross-validation / training pipelines.
- **Information Disclosure Prevention**: Error handlers strip stack traces, database internals, and credentials from API responses, returning standard sanitized error envelopes referencing correlation `request_id`s.
