# ── Stage 1: install dependencies ────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Bring in the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Build-time system libs required to compile psycopg2-binary and cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifest and lockfile first for layer-cache efficiency
COPY pyproject.toml uv.lock ./

# Sync production deps only into an isolated venv
RUN uv sync --frozen --no-dev --no-cache

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Runtime system libs: WeasyPrint (pango/cairo/gdk-pixbuf) + libpq
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built venv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Activate the venv for all subsequent RUN / CMD instructions
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY ./app ./app
COPY alembic.ini .
COPY ./alembic ./alembic

RUN useradd -m -u 1001 appuser \
    && mkdir -p /app/uploads/pdfs \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
