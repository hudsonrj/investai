# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies (psycopg2-binary needs libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a prefix so we can copy them later
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Runtime library for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY agents/      ./agents/
COPY api/         ./api/
COPY core/        ./core/
COPY dashboard/   ./dashboard/
COPY feeds/       ./feeds/
COPY ml/          ./ml/
COPY migrations/  ./migrations/
COPY static/      ./static/
COPY schema.sql   .
COPY requirements.txt .

# Non-root user for security
RUN useradd -m -u 1000 investai && chown -R investai:investai /app
USER investai

EXPOSE 8091

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -sf http://localhost:8091/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8091", \
     "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
