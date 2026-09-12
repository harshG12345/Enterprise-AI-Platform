"""Unit and integration tests for Prometheus Metrics, Structured JSON Logging, and Observability."""

import json
import logging
import uuid

import pytest
from httpx import AsyncClient

from app.core.logger import StructuredJSONFormatter, request_id_ctx, user_id_ctx
from app.monitoring.metrics import (
    record_drift_alert,
    record_model_prediction,
    update_model_psi_metric,
)


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoints(async_client: AsyncClient):
    """Verify /metrics and /api/v1/metrics endpoints expose standard Prometheus telemetry."""
    # 1. Root /metrics
    resp = await async_client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    content = resp.text
    assert "# HELP" in content
    assert "# TYPE" in content
    assert "http_requests_total" in content
    assert "model_predictions_total" in content
    assert "model_drift_alerts_total" in content

    # 2. Versioned /api/v1/metrics
    v1_resp = await async_client.get("/api/v1/metrics")
    assert v1_resp.status_code == 200
    assert "http_requests_total" in v1_resp.text


@pytest.mark.asyncio
async def test_metrics_recording_and_telemetry(async_client: AsyncClient):
    """Verify metric recording helper methods mutate Prometheus registry correctly."""
    # Record custom prediction metric
    test_model_id = str(uuid.uuid4())
    record_model_prediction(
        model_id=test_model_id,
        model_name="TestRFClassifier",
        task_type="classification",
        mode="realtime",
        duration_seconds=0.012,
    )

    # Record drift alert
    record_drift_alert(
        model_id=test_model_id,
        feature_name="income_feature",
        alert_level="CRITICAL",
    )

    # Update PSI gauge
    update_model_psi_metric(
        model_id=test_model_id,
        model_name="TestRFClassifier",
        max_psi=0.342,
    )

    # Fetch metrics
    resp = await async_client.get("/metrics")
    assert resp.status_code == 200
    metrics_text = resp.text

    assert test_model_id in metrics_text
    assert "TestRFClassifier" in metrics_text
    assert "income_feature" in metrics_text
    assert "CRITICAL" in metrics_text


def test_structured_json_log_formatter():
    """Verify StructuredJSONFormatter produces standard JSON format with correlation IDs."""
    formatter = StructuredJSONFormatter()

    # Set context variables
    req_token = request_id_ctx.set("req-test-trace-99")
    usr_token = user_id_ctx.set("user-uuid-12345")

    try:
        record = logging.LogRecord(
            name="enterprise_ai.test",
            level=logging.INFO,
            pathname="test_module.py",
            lineno=42,
            msg="User %s performed %s successfully",
            args=("admin", "login"),
            exc_info=None,
        )
        record.request_id = "req-test-trace-99"
        record.user_id = "user-uuid-12345"

        formatted_str = formatter.format(record)
        log_json = json.loads(formatted_str)

        assert log_json["level"] == "INFO"
        assert log_json["logger"] == "enterprise_ai.test"
        assert "User admin performed login successfully" in log_json["message"]
        assert log_json["request_id"] == "req-test-trace-99"
        assert log_json["user_id"] == "user-uuid-12345"
        assert "timestamp" in log_json
        assert "location" in log_json
    finally:
        request_id_ctx.reset(req_token)
        user_id_ctx.reset(usr_token)
