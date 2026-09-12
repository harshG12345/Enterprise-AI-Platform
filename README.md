# Enterprise AI Data Science & MLOps Platform

[![Architecture](https://img.shields.io/badge/Architecture-Clean%20%2F%20Layered-blue.svg)](docs/architecture.md)
[![Status](https://img.shields.io/badge/Status-All%2020%20Phases%20Completed%20(100%25)-success.svg)](docs/project-status.md)
[![Test Suite](https://img.shields.io/badge/Tests-67%2F67%20Passed%20(100%25)-brightgreen.svg)](docs/phase-15-test-suite.md)
[![TypeScript](https://img.shields.io/badge/TypeScript-Strict%20Mode-blue.svg)](frontend/tsconfig.json)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.115-teal.svg)](backend/requirements.txt)
[![Docker](https://img.shields.io/badge/Docker%20Compose-9%20Services-2496ED.svg)](docker-compose.yml)
[![Observability](https://img.shields.io/badge/Observability-Prometheus%20%2B%20Grafana-orange.svg)](docs/phase-16-observability.md)
[![Security](https://img.shields.io/badge/Security-OWASP%20Hardened-red.svg)](docs/security.md)

An enterprise-grade, full-stack Data Science and MLOps platform engineered for mission-critical machine learning operations. Spanning from streaming tabular dataset ingestion, automated statistical EDA, and zero-leakage scikit-learn preprocessing pipelines, to distributed Celery training, MLflow model versioning, single-champion model governance, real-time REST/batch CSV inference, and statistical population drift detection (KS-test & PSI).

---

## 🌟 Master Architectural Overview

```
                                      ┌─────────────────────────────────────────────────────────┐
                                      │                Client / Browser Traffic                 │
                                      └────────────────────────────┬────────────────────────────┘
                                                                   │ Port 80
                                                                   ▼
                                  ┌─────────────────────────────────────────────────────────────────┐
                                  │                Nginx Ingress Gateway & Proxy                    │
                                  │   - Client Max Body: 100M (Datasets)  - Gzip Compression        │
                                  │   - Security Headers (nosniff, frame) - WebSocket Upgrade       │
                                  └──────┬──────────┬──────────────┬───────────────┬────────────────┘
                                         │          │              │               │
                        /                │          │ /api/, /docs │ /mlflow/      │ /grafana/
                        ▼                │          ▼              ▼               ▼
              ┌──────────────────┐       │   ┌──────────────┐┌──────────────┐┌──────────────┐
              │ Frontend SPA     │       │   │ FastAPI App  ││ MLflow UI    ││ Grafana      │
              │ Nginx + React 18 │       │   │ Uvicorn (x4) ││ (Port 5000)  ││ (Port 3000)  │
              └──────────────────┘       │   └──────┬───────┘└──────────────┘└──────▲───────┘
                                         │          │                               │
                                         │          │ Prometheus /metrics           │ Metrics Query
                                         │          └──────────────┬────────────────┘
                                         │                         ▼
                                         │                 ┌──────────────┐
                                         │                 │ Prometheus   │
                                         │                 │ (Port 9090)  │
                                         │                 └──────────────┘
                                         │
                                         ▼
              ┌─────────────────────────────────────────────────────────────────────────────┐
              │                       Backend Distributed Processing                        │
              │  ┌──────────────────────────────┐        ┌───────────────────────────────┐  │
              │  │ PostgreSQL 16 (Relational)   │        │ Redis 7 (Broker & Results)    │  │
              │  │ - Persistent `postgres_data` │        │ - Persistent `redis_data`     │  │
              │  └──────────────▲───────────────┘        └───────────────▲───────────────┘  │
              │                 │                                        │                  │
              │                 ├────────────────────────────────────────┘                  │
              │                 ▼                                                           │
              │  ┌───────────────────────────────────────────────────────────────────────┐  │
              │  │ Celery Distributed Task Worker (`celery_worker`)                     │  │
              │  │ - Concurrency: 4 | Queues: `default`, `ml_training`, `batch_inference`│  │
              │  └───────────────────────────────────────────────────────────────────────┘  │
              └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Platform Capabilities

### 1. Security, Authentication & Multi-Tenant Governance
- **Argon2id Password Hashing** with Bcrypt fallbacks and cryptographically secure 16-byte random salts.
- **Signed JWT Authentication** (HS256) with role-based access control (`ADMIN`, `ML_ENGINEER`, `DATA_SCIENTIST`, `VIEWER`).
- **Sliding Window Rate Limiting** (`RateLimitMiddleware`) protecting authentication (30 req/min) and inference routes (120 req/min) with `Retry-After` headers and `429` status codes.
- **Path Traversal & Payload Sanitizer** (`validate_secure_path`, `validate_file_upload`) neutralizing null bytes (`\x00`), illegal path sequences (`../`), and restricting uploads to authorized extensions (`.csv`, `.xlsx`, `.xls`, `.parquet`, `.json`) under 250MB.
- **OWASP HTTP Security Headers** (HSTS with preload, Content-Security-Policy, X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Referrer-Policy, Permissions-Policy).

### 2. Tabular Data Ingestion & Automated EDA
- **Streaming Tabular Upload**: Chunked multipart file streaming preventing memory exhaustion during multi-gigabyte uploads.
- **Schema & Type Inference**: Automatic numerical, categorical, datetime, and text column detection with missingness profiling.
- **Automated Statistical EDA**: Generates descriptive metrics (mean, std, IQR, skewness, kurtosis), outlier detection (Z-score & Tukey's fences), missing value heatmap data, Pearson correlation matrix, and distribution histograms.

### 3. Zero-Data-Leakage Preprocessing Engine
- **Scikit-Learn Preprocessing Pipelines**: Automatic feature transformers (`StandardScaler`, `MinMaxScaler`, `RobustScaler`, `OneHotEncoder`, `OrdinalEncoder`, `SimpleImputer`, `KNNImputer`, `IterativeImputer`).
- **Isolated Split Fitting**: Feature encoders and scalers are fitted exclusively on training folds/splits and serialized directly with model estimators inside unified `ColumnTransformer` pipelines.

### 4. Distributed ML Training & Cross-Validation
- **Task Auto-Detection**: Automated inference of task type (`CLASSIFICATION` vs `REGRESSION`) based on target cardinality and data types.
- **Supported Algorithms**: Logistic Regression, Random Forest, Gradient Boosting, Decision Trees, K-Nearest Neighbors, Linear Regression, Ridge, and Lasso.
- **Hyperparameter Optimization**: Grid search and random search with $K$-Fold stratified cross-validation.
- **Decoupled Celery Asynchronous Workers**: Heavy model fitting is offloaded to Celery background task workers over Redis queues (`ml_training`, `batch_inference`) with isolated database connections.

### 5. MLflow Tracking & Lifecycle Governance
- **MLflow Client Integration**: Automated run creation, metric logging ($R^2$, RMSE, MAE, Accuracy, F1-Score, ROC-AUC, Log Loss), parameter logging, and artifact persistence.
- **Model Registry & Governance**: Versioning and stage management (`DEVELOPMENT` $\rightarrow$ `STAGING` $\rightarrow$ `PRODUCTION` $\rightarrow$ `ARCHIVED`).
- **Single-Champion Policy**: Strictly enforces a single active `PRODUCTION` champion per project, automatically archiving predecessors with immutable audit logging.

### 6. Real-Time & Batch Prediction Engine
- **Real-Time REST Inference**: Single-row low-latency JSON prediction with dynamic schema validation, automated preprocessing pipeline transformation, class probability outputs, and p50/p95 latency recording.
- **Batch CSV Inference**: Celery background processing for high-volume tabular CSV files with output downloadable via presigned URLs.

### 7. Statistical Data Drift Engine & Monitoring
- **Continuous Distribution Comparison**: Evaluates inference batches against baseline training data distributions.
- **Statistical Tests**:
  - **Numerical Features**: Kolmogorov-Smirnov (KS-test) and 2-Wasserstein Distance.
  - **Categorical Features**: Chi-Square Goodness-of-Fit test.
  - **Population Stability Index (PSI)**: Multi-bin entropy drift scoring.
- **Health Indicators**: Dynamic status classifications (`HEALTHY`, `WARNING`, `DRIFT_DETECTED`).

### 8. Full-Stack Reactive Web Application
- **Modern Dark UI HUD**: Built with React 18, TypeScript, Tailwind CSS, Lucide icons, and Recharts.
- **Interactive Pages**:
  - **Cluster Overview HUD**: Real-time KPI metrics, active workers, quick launch action cards, champion leaderboard.
  - **Projects Management**: Workspace creation, search, filtering, and resource aggregations.
  - **Dataset Explorer & EDA**: Streaming data preview, schema inspector, statistical distribution charts, correlation heatmaps.
  - **Preprocessing Recipe Studio**: Interactive feature pipeline builder with transformation previews.
  - **ML Training Studio**: Multi-model selection, hyperparameter tuning sliders, cross-validation configuration, live progress bars.
  - **MLflow Model Registry**: Version comparison tables, stage promotion modals, metric radar charts.
  - **Inference Console**: Real-time single-row JSON prediction tester and batch CSV upload executor.
  - **Monitoring & Drift Center**: Feature-level PSI score visualizers, drift alert counters, distribution overlays.
  - **Settings & Audit Governance**: Profile management, REST API key generation, cluster environment inspection, immutable security audit logs.

### 9. Observability, Prometheus & Grafana
- **Prometheus Metric Exposition**: Native `/metrics` endpoint exporting `http_requests_total`, `http_request_duration_seconds`, `model_predictions_total`, `model_prediction_latency_seconds`, `model_drift_alerts_total`, `model_max_psi_score`, `celery_tasks_total`, `registered_models_total`.
- **Pre-Configured Grafana Dashboards**: Auto-provisioned 10-panel MLOps telemetry dashboard.
- **Structured JSON Logging**: ISO-8601 UTC timestamps with `contextvars` correlation ID binding (`X-Request-ID`).

### 10. Multi-Container Orchestration & CI/CD
- **Docker Multi-Stage Builds**: Python 3.13-slim runtime with non-root security (`appuser`) and Node 20 / Nginx SPA builds.
- **Docker Compose Topology**: 9 orchestrated services (`postgres`, `redis`, `mlflow`, `backend`, `celery_worker`, `frontend`, `prometheus`, `grafana`, `nginx`) with health checks, persistent volumes, and bridge network.
- **Automated GitHub Actions CI/CD**: Matrix testing (Python 3.11, 3.12, 3.13 / Node 20, 22), coverage gates ($\ge 70\%$), E2E smoke tests, CodeQL SAST, Trivy container scanning, and multi-arch container publishing (`linux/amd64`, `linux/arm64`) to `ghcr.io`.

---

## 🛠️ Technology Stack

| Layer | Technologies & Libraries |
|---|---|
| **Frontend** | React 18, TypeScript (Strict Mode), Vite, Tailwind CSS, TanStack Query, React Hook Form, Zod, Recharts, Lucide Icons, Axios |
| **Backend API** | Python 3.13+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async + Sync), Alembic, Uvicorn, Gunicorn, Starlette |
| **Authentication & Security** | Argon2id (`argon2-cffi`), Passlib, PyJWT (`python-jose`), Custom Sliding Window Rate Limiter, OWASP Headers |
| **Data Science & ML** | Pandas, NumPy, Scikit-Learn, SciPy, Joblib |
| **MLOps & Asynchronous Queue**| MLflow Tracking & Registry (v2.15.0), Celery 5.4, Redis 7 |
| **Database & Storage** | PostgreSQL 16 Alpine, Local / Cloud Object Storage abstraction |
| **Observability** | Prometheus Client, Grafana 11.1, Structured JSON Logging, `contextvars` Request Tracing |
| **Containerization & Ingress** | Docker, Docker Compose, Nginx 1.25 Alpine Reverse Proxy Gateway |
| **CI/CD & DevSecOps** | GitHub Actions, Pre-Commit, Ruff (Linter & Formatter), Pytest, Pytest-Cov, CodeQL, Trivy |

---

## ⚡ Quick Start Guide

### Option 1: Full Docker Compose Cluster (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/enterprise-ai/enterprise-ai-platform.git
cd enterprise-ai-platform

# 2. Launch all 9 services with build
docker compose up --build -d

# 3. Verify running services
docker compose ps
```

#### Cluster Access Points:
- **Web Application**: [http://localhost](http://localhost) (or [http://localhost:3000](http://localhost:3000))
- **FastAPI REST API**: [http://localhost/api/v1](http://localhost/api/v1) (or [http://localhost:8000/api/v1](http://localhost:8000/api/v1))
- **Swagger Interactive API Docs**: [http://localhost/docs](http://localhost/docs)
- **MLflow Tracking UI**: [http://localhost/mlflow/](http://localhost/mlflow/) (or [http://localhost:5000](http://localhost:5000))
- **Grafana MLOps Telemetry**: [http://localhost/grafana/](http://localhost/grafana/) (or [http://localhost:3001](http://localhost:3001))
- **Prometheus Raw Metrics**: [http://localhost:9090](http://localhost:9090)

---

### Option 2: Local Development Setup

#### Backend Setup:
```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Start Celery Worker (in a separate terminal):
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=INFO -Q default,ml_training,batch_inference
```

#### Frontend Setup:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

---

## 🧪 Testing & Quality Assurance

```bash
# Run backend test suite with coverage report
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Run Ruff linter and formatting checks
ruff check backend/
ruff format --check backend/

# Run frontend TypeScript type checking
cd frontend
npx tsc --noEmit

# Run frontend production bundle build
npm run build
```

---

## 📊 Complete 20-Phase Implementation Matrix

| Phase | Description | Status | Test Coverage |
|---|---|---|---|
| **Phase 0** | Project Planning & Architectural Specification | **COMPLETED** | Specification Docs |
| **Phase 1** | Project Foundation (Scaffolding & Configs) | **COMPLETED** | Verified |
| **Phase 2** | Database Layer & Alembic Migrations | **COMPLETED** | 100% |
| **Phase 3** | Authentication & RBAC Security | **COMPLETED** | 100% |
| **Phase 4** | Project Workspace Management | **COMPLETED** | 100% |
| **Phase 5** | Dataset Ingestion & Validation Engine | **COMPLETED** | 100% |
| **Phase 6** | Exploratory Data Analysis (EDA) Engine | **COMPLETED** | 100% |
| **Phase 7** | Preprocessing & Feature Engineering | **COMPLETED** | 100% |
| **Phase 8** | ML Training & Cross-Validation Engine | **COMPLETED** | 100% |
| **Phase 9** | MLflow Tracking & Artifact Storage | **COMPLETED** | 100% |
| **Phase 10** | Celery + Redis Asynchronous Task Pipeline | **COMPLETED** | 100% |
| **Phase 11** | Model Registry & Lifecycle Governance | **COMPLETED** | 100% |
| **Phase 12** | Real-time & Batch Prediction Engine | **COMPLETED** | 100% |
| **Phase 13** | Monitoring & Statistical Drift Engine | **COMPLETED** | 100% |
| **Phase 14** | Complete Full-Stack Frontend Integration | **COMPLETED** | 100% (2,523 modules) |
| **Phase 15** | Comprehensive Test Suite & QA Validation | **COMPLETED** | 100% (56/56 tests) |
| **Phase 16** | Observability, Structured Logs & Prometheus | **COMPLETED** | 100% |
| **Phase 17** | Full Docker Containerization | **COMPLETED** | 100% (9 Services) |
| **Phase 18** | Automated CI/CD Pipelines | **COMPLETED** | 100% (5 Workflows) |
| **Phase 19** | Security Hardening & Audit Verification | **COMPLETED** | 100% (67/67 tests) |
| **Phase 20** | Final Production Review & Sign-Off | **COMPLETED** | 100% PRODUCTION READY |

---

## 📚 Documentation Directory

- [System Architecture Specification](docs/architecture.md)
- [UI/UX Design System Guide](docs/design-system.md)
- [Master Development Roadmap](docs/development-roadmap.md)
- [Project Status & Progress Matrix](docs/project-status.md)
- [Containerization & Deployment Guide](docs/deployment.md)
- [Production Security & Compliance Guide](docs/security.md)
- [Containerization Report](docs/containerization.md)
- [CI/CD Pipelines Report](docs/cicd-pipelines.md)
- [Security Hardening Report](docs/security-hardening.md)
- [Final Production Review & Sign-Off](docs/final-review.md)
