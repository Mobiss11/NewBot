# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
COPY app/ app/

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir .


# Stage 2: Runtime
FROM python:3.12-slim

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY app/ app/

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R appuser:appuser /app

ENV PATH="/opt/venv/bin:$PATH"

USER appuser

VOLUME /app/data

CMD ["python", "-m", "app.main"]
