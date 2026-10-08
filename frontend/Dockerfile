# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

COPY frontend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production runtime
FROM python:3.11-slim AS runner

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    BACKEND_URL="http://backend:8000"

COPY --chown=appuser:appgroup frontend /app/frontend

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

WORKDIR /app/frontend
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
