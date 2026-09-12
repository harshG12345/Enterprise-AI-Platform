#!/bin/bash
set -e

# ==============================================================================
# Enterprise AI Platform - Backend Entrypoint Script
# Handles DB migrations, Celery worker orchestration, and API initialization
# ==============================================================================

echo "[entrypoint] Initializing Enterprise AI Platform service container..."
echo "[entrypoint] Python Version: $(python --version)"
echo "[entrypoint] Environment: ${ENVIRONMENT:-production}"

# Wait for PostgreSQL if DATABASE_URL or DATABASE_HOST is configured
if [ -n "$DATABASE_HOST" ] || [ -n "$POSTGRES_HOST" ]; then
    DB_HOST=${DATABASE_HOST:-${POSTGRES_HOST:-postgres}}
    DB_PORT=${DATABASE_PORT:-5432}
    echo "[entrypoint] Checking database availability at ${DB_HOST}:${DB_PORT}..."
    
    TIMEOUT=30
    COUNTER=0
    until python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(('$DB_HOST', int('$DB_PORT')))
    s.close()
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; do
        COUNTER=$((COUNTER + 1))
        if [ $COUNTER -ge $TIMEOUT ]; then
            echo "[entrypoint] WARNING: Database at ${DB_HOST}:${DB_PORT} not reachable after ${TIMEOUT}s. Proceeding..."
            break
        fi
        echo "[entrypoint] Waiting for database (${COUNTER}/${TIMEOUT}s)..."
        sleep 1
    done
    echo "[entrypoint] Database check completed."
fi

# Route entrypoint action
case "$1" in
    api|"")
        echo "[entrypoint] Applying database migrations via Alembic..."
        alembic upgrade head || echo "[entrypoint] WARNING: Alembic migration encountered an error or already up-to-date."
        
        echo "[entrypoint] Starting FastAPI application server on port 8000..."
        WORKERS=${WEB_CONCURRENCY:-4}
        LOG_LEVEL=${LOG_LEVEL:-info}
        exec uvicorn app.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --workers "$WORKERS" \
            --log-level "$LOG_LEVEL" \
            --proxy-headers \
            --forwarded-allow-ips="*"
        ;;
    
    worker)
        echo "[entrypoint] Starting Celery Distributed Task Worker..."
        CONCURRENCY=${CELERY_CONCURRENCY:-4}
        LOG_LEVEL=${LOG_LEVEL:-INFO}
        exec celery -A app.core.celery_app worker \
            --loglevel="$LOG_LEVEL" \
            --concurrency="$CONCURRENCY" \
            --queues=default,ml_training,batch_inference \
            --heartbeat-interval=10
        ;;
        
    beat)
        echo "[entrypoint] Starting Celery Beat Periodic Scheduler..."
        LOG_LEVEL=${LOG_LEVEL:-INFO}
        exec celery -A app.core.celery_app beat \
            --loglevel="$LOG_LEVEL" \
            --schedule=/tmp/celerybeat-schedule
        ;;

    test)
        echo "[entrypoint] Running backend test suite..."
        exec pytest backend/tests/ -v --cov=app --cov-report=term-missing
        ;;

    *)
        echo "[entrypoint] Executing custom command: $@"
        exec "$@"
        ;;
esac
