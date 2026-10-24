# Production Dockerfile for LegalConnect Backend
FROM python:3.10-slim

# Create non-root user with UID 1000 (standard for Hugging Face Spaces)
RUN useradd -m -u 1000 user

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface

WORKDIR $HOME/app

# Install minimal system utilities for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install backend python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user before caching model and copying application source
USER user

# Pre-download ONNX embedding model into user-accessible cache during image build
# This makes container startup instant, avoids PyTorch (~200+ MB RAM savings), and eliminates runtime network dependencies
RUN python -c "from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2; ef = ONNXMiniLM_L6_V2(); ef(['warmup'])"

# Copy application source code with user ownership
COPY --chown=user:user . $HOME/app

# Expose backend port
EXPOSE 8000 7860 10000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start FastAPI server on dynamic platform port
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
