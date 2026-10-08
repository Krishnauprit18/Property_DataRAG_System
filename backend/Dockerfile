# ==========================================
# STAGE 1: Builder (Compile dependencies)
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Pre-download the Sentence-Transformer model into a shared directory
ENV HF_HOME=/build/hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ==========================================
# STAGE 2: Production Runtime
# ==========================================
FROM python:3.11-slim AS runner

# Install curl for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged security user (UID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Copy python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy pre-downloaded HuggingFace model cache to appuser home
COPY --from=builder --chown=appuser:appgroup /build/hf_cache /home/appuser/.cache/huggingface

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/home/appuser/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/home/appuser/.cache/huggingface

# Copy project code and dataset
COPY --chown=appuser:appgroup backend /app/backend
COPY --chown=appuser:appgroup scripts /app/scripts
COPY --chown=appuser:appgroup Property_data.csv /app/Property_data.csv

# Create writable persistent directories for ChromaDB and Analytics
RUN mkdir -p /app/backend/chroma_db /app/backend/analytics/conversations && \
    chown -R appuser:appgroup /app && \
    chmod -R 775 /app/backend/chroma_db /app/backend/analytics

# Switch to non-root user
USER appuser

EXPOSE 8000

# Enterprise Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]