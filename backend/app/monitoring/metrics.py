"""Prometheus metrics instruments and exposition registry."""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

# -----------------------------------------------------------------------------
# Core Metric Definitions
# -----------------------------------------------------------------------------

# HTTP Request Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests processed by the platform",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ML Prediction Metrics
MODEL_PREDICTIONS_TOTAL = Counter(
    "model_predictions_total",
    "Total number of inference predictions performed",
    ["model_id", "model_name", "task_type", "inference_mode"],
)

MODEL_PREDICTION_LATENCY_SECONDS = Histogram(
    "model_prediction_latency_seconds",
    "Inference latency for model execution in seconds",
    ["model_id", "model_name"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)

# Statistical Data Drift Metrics
MODEL_DRIFT_ALERTS_TOTAL = Counter(
    "model_drift_alerts_total",
    "Total statistical data drift alerts detected across features",
    ["model_id", "feature_name", "alert_level"],
)

MODEL_MAX_PSI_GAUGE = Gauge(
    "model_max_psi_score",
    "Latest maximum Population Stability Index (PSI) score for model",
    ["model_id", "model_name"],
)

# Celery Background Task Metrics
CELERY_TASKS_TOTAL = Counter(
    "celery_tasks_total",
    "Total number of Celery asynchronous tasks executed",
    ["task_name", "status"],
)

CELERY_TASK_DURATION_SECONDS = Histogram(
    "celery_task_duration_seconds",
    "Execution duration of Celery asynchronous background tasks",
    ["task_name"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

# Model Registry Lifecycle Gauge
REGISTERED_MODELS_GAUGE = Gauge(
    "registered_models_total",
    "Number of models currently in registry by lifecycle stage",
    ["stage"],
)


# -----------------------------------------------------------------------------
# Recording Helper Functions
# -----------------------------------------------------------------------------


def record_http_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    """Record HTTP request count and latency."""
    # Normalize path to prevent high-cardinality explosions on UUID parameters
    clean_path = _normalize_path(path)
    HTTP_REQUESTS_TOTAL.labels(method=method, path=clean_path, status_code=str(status_code)).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=clean_path).observe(duration_seconds)


def record_model_prediction(
    model_id: str,
    model_name: str,
    task_type: str,
    mode: str,
    duration_seconds: float,
) -> None:
    """Record model inference execution count and latency."""
    MODEL_PREDICTIONS_TOTAL.labels(
        model_id=str(model_id),
        model_name=model_name or "unknown",
        task_type=task_type or "unknown",
        inference_mode=mode,
    ).inc()
    MODEL_PREDICTION_LATENCY_SECONDS.labels(
        model_id=str(model_id),
        model_name=model_name or "unknown",
    ).observe(duration_seconds)


def record_drift_alert(model_id: str, feature_name: str, alert_level: str) -> None:
    """Record statistical drift alert trigger."""
    MODEL_DRIFT_ALERTS_TOTAL.labels(
        model_id=str(model_id),
        feature_name=feature_name,
        alert_level=alert_level,
    ).inc()


def update_model_psi_metric(model_id: str, model_name: str, max_psi: float) -> None:
    """Update latest max PSI gauge for a model."""
    MODEL_MAX_PSI_GAUGE.labels(
        model_id=str(model_id),
        model_name=model_name or "unknown",
    ).set(max_psi)


def record_celery_task(task_name: str, status: str, duration_seconds: float) -> None:
    """Record asynchronous Celery task completion."""
    CELERY_TASKS_TOTAL.labels(task_name=task_name, status=status).inc()
    CELERY_TASK_DURATION_SECONDS.labels(task_name=task_name).observe(duration_seconds)


def update_model_registry_gauges(counts_by_stage: dict[str, int]) -> None:
    """Update active model counts across lifecycle stages."""
    for stage, count in counts_by_stage.items():
        REGISTERED_MODELS_GAUGE.labels(stage=stage).set(count)


def get_prometheus_metrics_response() -> Response:
    """Generate Prometheus scrape response in standard exposition format."""
    metrics_data = generate_latest(REGISTRY)
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
    )


def _normalize_path(path: str) -> str:
    """Replace dynamic UUIDs and integers with placeholders to limit cardinality."""
    parts = path.strip("/").split("/")
    clean_parts = []
    for part in parts:
        if len(part) == 36 and part.count("-") == 4:
            clean_parts.append("{id}")
        elif part.isdigit():
            clean_parts.append("{id}")
        else:
            clean_parts.append(part)
    return "/" + "/".join(clean_parts) if clean_parts else "/"
