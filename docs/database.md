# Enterprise AI Platform: Database Architecture & Schema Specification

## 1. Overview
The database layer uses **PostgreSQL** in production with **SQLAlchemy 2.0** typed declarative models (`Mapped[...]`, `mapped_column`) and **Alembic** migration management. For local test environments, platform-independent `GUID` type decorators seamlessly support PostgreSQL native UUIDs and SQLite CHAR(36) representations.

---

## 2. Entity-Relationship Diagram

```
+------------------+          1:N          +-------------------+
|      users       |---------------------->|     projects      |
|------------------|                       |-------------------|
| id (UUID, PK)    |                       | id (UUID, PK)     |
| email (UQ, IX)   |                       | name (IX)         |
| full_name        |                       | description       |
| password_hash    |                       | owner_id (FK->usr)|
| role (ENUM, IX)  |                       | created_at        |
| is_active        |                       | updated_at        |
| created_at       |                       +---------+---------+
| updated_at       |                                 |
+--------+---------+                                 | 1:N
         |                                           v
         | 1:N                             +-------------------+
         |----------------------+          |     datasets      |
         |                      |          |-------------------|
         v                      |          | id (UUID, PK)     |
+-------------------+           |          | project_id (FK)   |
|    audit_logs     |           |          | filename          |
|-------------------|           |          | storage_path      |
| id (UUID, PK)     |           |          | file_size         |
| user_id (FK->usr) |           |          | row_count         |
| action (IX)       |           |          | column_count      |
| resource_type (IX)|           |          | schema_metadata   |
| resource_id       |           |          | status (ENUM, IX) |
| ip_address        |           |          | created_at        |
| metadata (JSON)   |           |          | updated_at        |
| created_at (IX)   |           |          +----+----+---------+
+-------------------+           |               |    |
                                | 1:N           |    | 1:N
                                v               |    v
                       +-------------------+    |  +---------------------+
                       |   training_jobs   |<---+  |     experiments     |
                       |-------------------|       |---------------------|
                       | id (UUID, PK)     |       | id (UUID, PK)       |
                       | project_id (FK)   |       | project_id (FK)     |
                       | dataset_id (FK)   |       | dataset_id (FK)     |
                       | user_id (FK->usr) |       | name (IX)           |
                       | status (ENUM, IX) |       | mlflow_exp_id (IX)  |
                       | target_column     |       | created_at          |
                       | task_type (ENUM)  |       +----------+----------+
                       | celery_task_id(IX)|                  |
                       | error_message     |                  | 1:N
                       | started_at        |                  v
                       | completed_at      |       +---------------------+
                       | created_at        |       |   trained_models    |
                       +-------------------+       |---------------------|
                                                   | id (UUID, PK)       |
                                                   | project_id (FK)     |
                                                   | dataset_id (FK)     |
                                                   | experiment_id (FK)  |
                                                   | name (IX)           |
                                                   | version             |
                                                   | task_type           |
                                                   | framework           |
                                                   | metrics (JSON)      |
                                                   | artifact_path       |
                                                   | mlflow_run_id (IX)  |
                                                   | status (ENUM, IX)   |
                                                   | created_at          |
                                                   +----------+----------+
                                                              |
                                                              | 1:N
                                                              v
                                                   +---------------------+
                                                   |     predictions     |
                                                   |---------------------|
                                                   | id (UUID, PK)       |
                                                   | model_id (FK->mod)  |
                                                   | user_id (FK->usr)   |
                                                   | input_data (JSON)   |
                                                   | prediction (JSON)   |
                                                   | latency_ms          |
                                                   | created_at (IX)     |
                                                   +---------------------+
```

---

## 3. Database Tables Reference

### 3.1 `users`
- **Primary Key**: `id UUID`
- **Unique Indexes**: `ix_users_email`
- **Indexes**: `ix_users_role`
- **Roles**: `ADMIN`, `DATA_SCIENTIST`, `USER`

### 3.2 `projects`
- **Primary Key**: `id UUID`
- **Foreign Keys**: `owner_id -> users.id (ON DELETE CASCADE)`
- **Indexes**: `ix_projects_name`, `ix_projects_owner_id`

### 3.3 `datasets`
- **Primary Key**: `id UUID`
- **Foreign Keys**: `project_id -> projects.id (ON DELETE CASCADE)`
- **Status Enum**: `PENDING`, `PROCESSING`, `VALIDATED`, `ERROR`
- **JSON Column**: `schema_metadata` (stores detected columns, dtypes, summary stats)

### 3.4 `experiments`
- **Primary Key**: `id UUID`
- **Foreign Keys**: `project_id -> projects.id (ON DELETE CASCADE)`, `dataset_id -> datasets.id (ON DELETE SET NULL)`
- **Indexes**: `ix_experiments_name`, `ix_experiments_mlflow_experiment_id`

### 3.5 `training_jobs`
- **Primary Key**: `id UUID`
- **Foreign Keys**: `project_id -> projects.id`, `dataset_id -> datasets.id`, `user_id -> users.id`
- **Status Enum**: `PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `CANCELLED`
- **Task Type Enum**: `classification`, `regression`
- **Indexes**: `ix_training_jobs_status`, `ix_training_jobs_celery_task_id`

### 3.6 `trained_models`
- **Primary Key**: `id UUID`
- **Foreign Keys**: `project_id -> projects.id`, `dataset_id -> datasets.id`, `experiment_id -> experiments.id`
- **Status Enum**: `NONE`, `DEVELOPMENT`, `STAGING`, `PRODUCTION`, `ARCHIVED`
- **JSON Column**: `metrics` (accuracy, precision, recall, f1, roc_auc, mae, mse, rmse, r2)
- **Indexes**: `ix_trained_models_status`, `ix_trained_models_mlflow_run_id`

### 3.7 `predictions`
- **Primary Key**: `id UUID`
- **Foreign Keys**: `model_id -> trained_models.id (ON DELETE CASCADE)`, `user_id -> users.id (ON DELETE SET NULL)`
- **JSON Columns**: `input_data`, `prediction`
- **Indexes**: `ix_predictions_created_at`, `ix_predictions_model_id`

### 3.8 `audit_logs`
- **Primary Key**: `id UUID`
- **Foreign Keys**: `user_id -> users.id (ON DELETE SET NULL)`
- **JSON Column**: `metadata`
- **Indexes**: `ix_audit_logs_action`, `ix_audit_logs_resource_type`, `ix_audit_logs_created_at`

---

## 4. Migration Protocol
All schema evolutions MUST be created and executed through Alembic:
```bash
# Check current migration revision
alembic current

# Check pending heads
alembic heads

# Apply migrations
alembic upgrade head
```
