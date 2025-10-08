set dotenv-required

@install:
    uv sync --all-extras --frozen
    just install-hooks

# Start all services for local development
@dev:
    echo "🚀 Starting Redis, Celery worker, and FastAPI server..."
    just redis-start
    just worker &
    sleep 2
    just server

# Start FastAPI server only
@server:
    uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Start or reuse existing Redis container
redis-start:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔍 Checking Redis container..."
    if docker ps --format '{{{{.Names}}' | grep -q '^redis-calculate-pi$'; then
        echo "✅ Redis already running"
    elif docker ps -a --format '{{{{.Names}}' | grep -q '^redis-calculate-pi$'; then
        docker start redis-calculate-pi
        echo "✅ Redis container started"
    else
        docker run -d --name redis-calculate-pi -p 6379:6379 redis:7-alpine
        echo "✅ Redis container created and started"
    fi

redis-stop:
    #!/usr/bin/env bash
    if docker stop redis-calculate-pi 2>/dev/null; then
        echo "🛑 Redis stopped"
    else
        echo "⚠️  Redis not running"
    fi

redis-rm:
    #!/usr/bin/env bash
    if docker rm -f redis-calculate-pi 2>/dev/null; then
        echo "🗑️  Redis container removed"
    else
        echo "⚠️  Redis container not found"
    fi

@worker:
    uv run celery -A app.celery_app worker --loglevel=info

stop:
    #!/usr/bin/env bash
    echo "🛑 Stopping services..."
    if ! pkill -f "celery.*app.celery_app"; then
        echo "⚠️  No Celery worker running"
    fi
    just redis-stop

@lint:
    uv run ruff check --select I --fix  # Include imports sorting
    uv run ruff format

@test:
    uv run pytest -vv


@install-hooks:
    uv run pre-commit install

@update-hooks:
    uv run pre-commit autoupdate
