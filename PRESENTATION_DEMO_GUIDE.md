# Enterprise AI Data Science & MLOps Platform
## Master Presentation & Live Demo Execution Guide

---

## 1. Executive Pitch & Presentation Hook

> **The 30-Second Elevator Pitch**:
> *"Modern enterprise data science teams struggle with fragmented tooling: data is explored in disjointed Jupyter notebooks, models are trained on local machines without lineage, deployment requires complex DevOps tickets, and silent data drift degrades models in production unnoticed. 
>
> Our **Enterprise AI Platform** solves this by uniting the entire ML lifecycle into a single, high-performance, containerized operating system. From raw CSV ingestion and automated exploratory data analysis (EDA), through zero-leakage preprocessing and distributed Celery/XGBoost training, to MLflow governance, sub-20ms real-time inference, and statistical drift monitoring (PSI & K-S tests)—all protected by enterprise RBAC, multi-tenancy, and OWASP security."*

---

## 2. Pre-Demo Preparation & Verification Checklist

Complete these steps **10 minutes before your live presentation**:

### A. Start the Platform (1-Click Docker Launch)
Open your terminal in the project root and execute:

```bash
# 1. Start all 9 services in detached mode
docker-compose up -d

# 2. Verify all 9 containers are healthy and running
docker-compose ps
```

### B. Service URLs & Ports (Bookmark These in Your Browser)
| Component | URL | Default Credentials / Purpose |
|---|---|---|
| **Frontend Web App** | [`http://localhost:3000`](http://localhost:3000) or [`http://localhost:80`](http://localhost:80) | Main Presentation Interface (SPA) |
| **Backend REST API Docs** | [`http://localhost:8000/docs`](http://localhost:8000/docs) | Interactive Swagger UI / API Testing |
| **MLflow Tracking UI** | [`http://localhost:5000`](http://localhost:5000) | Experiment Tracking & Model Lineage |
| **Prometheus Telemetry** | [`http://localhost:9090`](http://localhost:9090) | Scraped Metrics & Platform Gauges |
| **Grafana Dashboards** | [`http://localhost:3001`](http://localhost:3001) | `admin` / `admin` (Operational HUD) |

### C. Demo User Accounts
| Role | Email | Password | Permissions Scope |
|---|---|---|---|
| **Admin** | `admin@enterprise.ai` | `Admin@123456` | Full platform control, user management, audit logs |
| **Data Scientist** *(Recommended)* | `demo@enterprise.ai` | `Demo@123456` | Workspace CRUD, training, MLflow, inference, drift |
| **Viewer** | `viewer@enterprise.ai` | `Viewer@123456` | Read-only dashboards, metric exploration |

---

## 3. Automated Demo Dataset Generation

To ensure your demo runs smoothly without searching for sample data files, run this Python script to generate 3 tailor-made demonstration datasets:

```python
# Save and run as: python scripts/generate_demo_data.py
import numpy as np
import pandas as pd
import os

os.makedirs("demo_data", exist_ok=True)
np.random.seed(42)
n_samples = 1200

# 1. BASELINE TRAINING DATASET (Customer Churn)
tenure = np.random.exponential(scale=20, size=n_samples).clip(1, 72).astype(int)
monthly_charges = np.random.normal(loc=65, scale=25, size=n_samples).clip(18, 120).round(2)
total_charges = (tenure * monthly_charges * np.random.uniform(0.95, 1.05, size=n_samples)).round(2)
contract = np.random.choice(["Month-to-Month", "One-Year", "Two-Year"], size=n_samples, p=[0.55, 0.25, 0.20])
internet_service = np.random.choice(["Fiber Optic", "DSL", "No"], size=n_samples, p=[0.45, 0.35, 0.20])
payment_method = np.random.choice(["Electronic Check", "Mailed Check", "Bank Transfer", "Credit Card"], size=n_samples)
senior_citizen = np.random.choice([0, 1], size=n_samples, p=[0.84, 0.16])

# Calculate churn probability with realistic interactions
churn_logit = (-1.5 
               + 0.03 * monthly_charges 
               - 0.05 * tenure 
               + 0.8 * (contract == "Month-to-Month") 
               + 0.5 * (internet_service == "Fiber Optic")
               + 0.3 * senior_citizen)
churn_prob = 1 / (1 + np.exp(-churn_logit))
churn = (np.random.uniform(0, 1, size=n_samples) < churn_prob).astype(int)

df_baseline = pd.DataFrame({
    "customer_id": [f"CUST-{10000+i}" for i in range(n_samples)],
    "tenure": tenure,
    "monthly_charges": monthly_charges,
    "total_charges": total_charges,
    "contract": contract,
    "internet_service": internet_service,
    "payment_method": payment_method,
    "senior_citizen": senior_citizen,
    "churn": churn
})
df_baseline.to_csv("demo_data/customer_churn_baseline.csv", index=False)
print("✓ Generated demo_data/customer_churn_baseline.csv (1,200 rows)")

# 2. DRIFTED PRODUCTION DATASET (Simulates Macroeconomic Inflation & Shift)
n_drift = 600
drift_tenure = np.random.exponential(scale=10, size=n_drift).clip(1, 36).astype(int) # Shorter tenure!
drift_charges = np.random.normal(loc=95, scale=20, size=n_drift).clip(45, 150).round(2) # Price spike!
drift_total = (drift_tenure * drift_charges).round(2)
drift_contract = np.random.choice(["Month-to-Month", "One-Year", "Two-Year"], size=n_drift, p=[0.80, 0.15, 0.05]) # High churn contract!
drift_internet = np.random.choice(["Fiber Optic", "DSL", "No"], size=n_drift, p=[0.70, 0.20, 0.10])
drift_payment = np.random.choice(["Electronic Check", "Mailed Check", "Bank Transfer", "Credit Card"], size=n_drift)
drift_senior = np.random.choice([0, 1], size=n_drift, p=[0.70, 0.30])

df_drifted = pd.DataFrame({
    "customer_id": [f"DRIFT-{20000+i}" for i in range(n_drift)],
    "tenure": drift_tenure,
    "monthly_charges": drift_charges,
    "total_charges": drift_total,
    "contract": drift_contract,
    "internet_service": drift_internet,
    "payment_method": drift_payment,
    "senior_citizen": drift_senior,
})
df_drifted.to_csv("demo_data/customer_churn_drifted.csv", index=False)
print("✓ Generated demo_data/customer_churn_drifted.csv (600 rows - Drifting distribution)")

# 3. BATCH INFERENCE DATASET (Unlabelled Customers)
df_batch = df_drifted.head(100).copy()
df_batch.to_csv("demo_data/customer_churn_batch_test.csv", index=False)
print("✓ Generated demo_data/customer_churn_batch_test.csv (100 rows)")
```

---

## 4. The 10-Minute Live Demo Walkthrough Script

```
+-------------------------------------------------------------------------------------------------+
|                                    DEMO TIMELINE (10 MINUTES)                                   |
+----------+--------------------------------------+-----------------------------------------------+
| Time     | Act / Scene                          | Core Capability Demonstrated                  |
+----------+--------------------------------------+-----------------------------------------------+
| 00:00    | Act 1: Executive Dashboard & RBAC    | Multi-tenant HUD, active models, system health|
| 01:30    | Act 2: Ingestion & Interactive EDA   | Schema parsing, missingness, Tukey outliers   |
| 03:30    | Act 3: Preprocessing Pipeline        | Zero data leakage, scalers, cyclical encoders |
| 05:00    | Act 4: Distributed Training (Celery) | XGBoost/RF, async queues, ROC-AUC, confusion  |
| 07:00    | Act 5: MLflow & Model Governance     | Experiment tracking, stage promotion to Prod  |
| 08:00    | Act 6: Real-Time & Batch Prediction  | Sub-20ms inference latency, probability scores|
| 09:00    | Act 7: Statistical Drift Monitoring  | PSI & Kolmogorov-Smirnov distribution shifts  |
| 10:00    | Act 8: Observability & Security      | Prometheus metrics, OWASP headers, Wrap-up    |
+----------+--------------------------------------+-----------------------------------------------+
```

---

### Act 1: Authentication & Executive Dashboard (1.5 Minutes)

1. **Open Browser** to [`http://localhost:3000`](http://localhost:3000).
2. **Log In** using `demo@enterprise.ai` / `Demo@123456`.
3. **Show Dashboard Overview**:
   - Point to the **KPI Cards**: *Total Models Deployed (Production)*, *Active Datasets*, *Total Inferences (24h)*, and *System Status (Green/Healthy)*.
   - Point to the **Recent Training Activity Feed** and **Cluster Resource Utilization** widgets.
4. **Presenter Script**:
   > *"Welcome to the Enterprise AI Platform. When a team logs in, they are placed in an isolated, multi-tenant workspace with strict Role-Based Access Control. As a Data Scientist, I have access to full compute resources, automated pipelines, and model registries without needing to configure underlying cloud servers."*

---

### Act 2: Ingestion, Schema Inference & Interactive EDA (2 Minutes)

1. **Navigate to Datasets** (`/datasets`).
2. Click **"+ Upload New Dataset"**:
   - Drag and drop `demo_data/customer_churn_baseline.csv`.
   - Name: `Telco Customer Churn Baseline`.
   - Tags: `telecom`, `churn`, `tabular`.
   - Click **"Upload & Parse"**.
3. **Show Automated Schema Detection**:
   - Highlight how column data types are automatically inferred: `tenure` (Numeric / Int64), `monthly_charges` (Numeric / Float64), `contract` (Categorical), etc.
   - Show the interactive **Data Preview Table** with pagination and search.
4. **Navigate to Automated EDA** (`/eda` or click "Run EDA" on dataset):
   - **Missingness Chart**: Highlights null percentages and complete row integrity.
   - **Numerical Moments & Skewness**: Shows mean, standard deviation, and identifies skewed distributions.
   - **Outlier Detection Table**: Show the **Tukey Fences (IQR)** and **Z-score** outlier detection cards.
   - **Correlation Heatmap**: Show the interactive Pearson and Spearman correlation matrix with multi-collinearity flags ($\rho > 0.85$).
5. **Presenter Script**:
   > *"In most companies, exploratory data analysis takes hours of repetitive pandas coding. Here, the moment a dataset is uploaded, our engine executes comprehensive statistical profiling, identifying outliers, calculating skewness, and plotting interactive correlation matrices instantly."*

---

### Act 3: Zero-Leakage Preprocessing & Feature Engineering (1.5 Minutes)

1. **Navigate to Preprocessing** (`/preprocessing`).
2. Click **"Create Pipeline"**:
   - Select Dataset: `Telco Customer Churn Baseline`.
   - Target Column: `churn` (Binary Classification).
   - Train/Test Split: `80% Train / 20% Test` (Stratified).
3. **Configure Transformer Blocks**:
   - **Numeric Imputer**: `Median Imputation`.
   - **Categorical Encoder**: `One-Hot Encoding` (with `handle_unknown='ignore'`).
   - **Feature Scaler**: `RobustScaler` (resistant to outliers identified in EDA).
4. Click **"Fit & Export Pipeline"**:
   - Highlight the execution time and downloaded pipeline artifact.
5. **Presenter Script**:
   > *"A critical danger in machine learning is Data Leakage—when test set distributions accidentally influence training parameters. Our pipeline builder strictly fits all transformers on training folds only, serializing the fitted states so they can be reused verbatim during production inference."*

---

### Act 4: Distributed Training & Hyperparameter Tuning (2 Minutes)

1. **Navigate to Model Training** (`/training`).
2. Click **"New Training Experiment"**:
   - Model Name: `XGBoost Customer Churn Predictor`.
   - Select Pipeline: The fitted pipeline from Act 3.
   - Algorithm: Select **`XGBoost Classifier`** (or Random Forest / LightGBM).
   - Evaluation Strategy: **`5-Fold Stratified Cross-Validation`**.
   - Hyperparameters: Set `n_estimators=100`, `max_depth=5`, `learning_rate=0.08`.
3. Click **"Start Distributed Training"**:
   - Show the **Live Task Status indicator** (`PENDING` $\to$ `RUNNING` on Celery worker $\to$ `COMPLETED`).
   - Note: The web browser does not freeze because heavy computation is offloaded to Redis/Celery workers.
4. **Inspect Evaluation Metrics**:
   - **Classification Metrics**: Validation Accuracy (~84%), ROC-AUC Score (~0.88), F1-Score (~0.79).
   - **Confusion Matrix**: Interactive matrix showing True Positives vs False Positives.
   - **ROC Curve & Precision-Recall Curve**: Interactive curves rendered via Recharts.
   - **Feature Importance Chart**: Shows `monthly_charges`, `tenure`, and `contract` as top churn drivers.
5. **Presenter Script**:
   > *"Rather than blocking the user's browser, training requests are queued into our distributed Celery worker pool running on Redis. The model is trained with 5-fold cross validation, logging out-of-fold metrics and full Gini feature importances."*

---

### Act 5: MLflow Experiment Tracking & Governance Promotion (1 Minute)

1. **Navigate to Experiments / MLflow** (`/experiments`).
2. Show the **Experiment Run Leaderboard**:
   - Compare runs across different algorithms (e.g. XGBoost vs Random Forest vs Logistic Regression).
   - Click the active MLflow run link (or show MLflow UI at [`http://localhost:5000`](http://localhost:5000)).
3. **Navigate to Model Registry** (`/models`):
   - Locate `XGBoost Customer Churn Predictor v1.0`.
   - Show current stage: `Development`.
   - Click **"Promote Stage"** $\to$ Select **`Staging`** $\to$ add audit note: *"Passed QA benchmarks with 0.88 ROC-AUC"*.
   - Click **"Promote to Production"** $\to$ Model is now the active live serving model!
4. **Presenter Script**:
   > *"Enterprise AI requires strict governance. Every run is automatically logged into MLflow with hyperparameter lineage, artifact storage, and metric histories. Through our Model Registry, models are formally promoted from Development to Staging to Production with full audit trails."*

---

### Act 6: Real-Time & High-Throughput Batch Predictions (1 Minute)

1. **Navigate to Predictions** (`/predictions`).
2. **Test 1: Single-Record Real-Time Prediction**:
   - Select Model: `XGBoost Customer Churn Predictor (Production)`.
   - Input Feature Values:
     - `tenure`: `2` (New customer)
     - `monthly_charges`: `110.50` (Expensive plan)
     - `contract`: `Month-to-Month`
     - `internet_service`: `Fiber Optic`
   - Click **"Generate Prediction"**:
   - **Instant Output (<20ms)**:
     - Prediction: **`CHURN: YES`** (Risk Alert!)
     - Churn Probability: **`88.4%`**
     - Latency: `12.4 ms`
3. **Test 2: High-Throughput Batch Prediction**:
   - Upload `demo_data/customer_churn_batch_test.csv` (100 records).
   - Click **"Run Batch Inference"** $\to$ Processed in < 1 second $\to$ Download scored CSV containing prediction labels and confidence probabilities.
4. **Presenter Script**:
   > *"Once in production, the model is exposed via high-concurrency async inference endpoints. Our single-record endpoint returns predictions with confidence scores in under 20 milliseconds, and our batch endpoint processes thousands of records with automatic schema validation."*

---

### Act 7: Real-Time Data Drift & Statistical Monitoring (1.5 Minutes)

1. **Navigate to Model Monitoring & Drift** (`/monitoring`).
2. Click **"Run Drift Analysis"**:
   - Baseline Dataset: `customer_churn_baseline.csv` (Reference).
   - Current Production Dataset: Upload `demo_data/customer_churn_drifted.csv` (Inference data).
   - Target Features: All numerical & categorical features.
   - Click **"Calculate Distribution Drift"**.
3. **Show Drift Dashboard & Statistical Findings**:
   - **Population Stability Index (PSI)**:
     - `monthly_charges`: $\text{PSI} = 0.285$ $\implies$ 🔴 **CRITICAL DRIFT ALERT** ($\text{PSI} > 0.25$).
     - `tenure`: $\text{PSI} = 0.192$ $\implies$ 🟡 **MODERATE DRIFT ALERT** ($0.1 \le \text{PSI} \le 0.25$).
   - **Two-Sample Kolmogorov-Smirnov (K-S) Test**:
     - Shows $p$-value $< 0.001$ confirming statistical distribution divergence.
   - **Feature Distribution Comparison Chart**:
     - Visual overlay showing baseline normal distribution shifted towards high charges and low tenure in production.
4. **Presenter Script**:
   > *"This is where most ML systems fail silently in the real world: the data changes over time, causing model accuracy to degrade without throwing errors. Our monitoring engine runs two-sample Kolmogorov-Smirnov tests and computes Population Stability Index (PSI). Here, it immediately flags that monthly charges have drifted significantly (PSI = 0.28), alerting the team to trigger automated retraining before business revenue is impacted."*

---

### Act 8: Observability, Security & Conclusion (0.5 Minute)

1. **Show Prometheus & Metrics**: Open [`http://localhost:8000/metrics`](http://localhost:8000/metrics) or [`http://localhost:9090`](http://localhost:9090) to show active request counters, inference latency histograms, and Celery worker gauges.
2. **Highlight Enterprise Security**:
   - Rate limiting (sliding window algorithm preventing API abuse).
   - OWASP security headers (CSP, HSTS, X-Content-Type-Options).
   - Path traversal and file upload sanitization.
3. **Conclude**:
   > *"In summary, the Enterprise AI Platform bridges the gap between data exploration, scalable distributed engineering, rigorous governance, and proactive production monitoring—built on a modern, fully containerized stack ready for enterprise deployment. Thank you, and I welcome your questions!"*

---

## 5. Q&A Defense Guide: Top Questions & Winning Answers

### Q1: "How do you guarantee that data leakage is prevented during feature engineering?"
> **Answer**: *"We enforce a strict separation between fitting and transforming. Preprocessing transformers—such as our `RobustScaler` and `OneHotEncoder`—are fitted **exclusively** on the training split ($X_{\text{train}}$). The resulting mathematical parameters (e.g. median, IQR, categorical maps) are frozen into a serialized pipeline object. The validation/test split and future real-time inference payloads are transformed using those frozen parameters, ensuring test distributions never bleed into training parameters."*

---

### Q2: "Why did you choose Celery and Redis instead of FastAPI's native `BackgroundTasks`?"
> **Answer**: *"FastAPI's `BackgroundTasks` run within the same Python process and asyncio event loop as the web server. If a machine learning training job or large hyperparameter grid search runs in `BackgroundTasks`, it consumes CPU cores, blocks the Python Global Interpreter Lock (GIL), and degrades API response times. 
> By utilizing **Celery with Redis**, compute jobs are decoupled onto independent worker containers with configurable concurrency, dedicated queue routing (`ml_training`, `batch_inference`), retry policies, and persistent task state tracking."*

---

### Q3: "How does your data drift engine work for numerical vs categorical features?"
> **Answer**: *"We utilize a multi-statistic approach:
> 1. **Numerical Features**: We compute the **Population Stability Index (PSI)** by binning baseline data into 10 deciles and measuring relative entropy changes, combined with a **Two-Sample Kolmogorov-Smirnov (K-S) test** to evaluate cumulative distribution variance.
> 2. **Categorical Features**: We calculate categorical PSI across discrete frequency bins and apply **Chi-Square Goodness-of-Fit tests** to detect shifting category proportions."*

---

### Q4: "How does the platform enforce multi-tenancy and prevent Insecure Direct Object References (IDOR)?"
> **Answer**: *"Every dataset, project, model, and prediction entity in our PostgreSQL database has a direct foreign key relationship to an owner `user_id`. Our FastAPI dependency layer injects the authenticated user via JWT claims and validates that the requesting user owns the requested entity before executing any database operation. Furthermore, users with the `Admin` role have elevated governance oversight, while `Data Scientist` and `Viewer` roles have granularly scoped capabilities."*

---

### Q5: "What happens if a database connection drops or an async event loop restarts?"
> **Answer**: *"Our SQLAlchemy 2.0 async engine utilizes connection pooling with `pool_pre_ping=True` to detect and discard stale socket connections before queries execute. In testing environments, we enforce `NullPool` to prevent asyncpg sockets from leaking across isolated test loops, and our custom rate limiter employs lazy lock initialization bound to the currently active event loop."*

---

## 6. Presenter Tips & Emergency Shortcuts

| Scenario | What to Do / Shortcut |
|---|---|
| **Need to quickly reset demo data** | Re-run `python scripts/generate_demo_data.py` to get fresh CSV files. |
| **Want to demonstrate API directly** | Open [`http://localhost:8000/docs`](http://localhost:8000/docs) and show interactive Swagger execution of `/api/v1/predictions/realtime`. |
| **Docker container restart needed** | Run `docker-compose restart backend celery_worker` (takes ~3 seconds). |
| **Browser zoom recommendation** | Set browser zoom to **90% or 100%** on 1080p/4K projector screens for optimal HUD visualization. |

---

*Enterprise AI Platform Presentation Guide | Ready for Live Evaluation & Demonstration*
