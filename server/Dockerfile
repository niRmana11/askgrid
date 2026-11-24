FROM python:3.12-slim

# Install uv binary cleanly from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install production dependencies first (leverages Docker layer caching!)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application source and sample dataset
COPY app ./app

# Create non-root user and ephemeral session storage directory
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /tmp/askgrid_sessions \
    && chown -R appuser:appuser /app /tmp/askgrid_sessions

USER appuser

EXPOSE 8000

# Single worker keeps RAM safely within 512 MB free-tier container & shares Circuit Breaker state
CMD ["sh", "-c", "exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
