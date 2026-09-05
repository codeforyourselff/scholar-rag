# Stage 1 - Build dependencies
FROM python:3.12-slim AS builder

ENV PYTHONDONOTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME="/opt/models" \
    TORCH_HOME="/opt/models"

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt .

RUN pip install --upgrade pip 
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
RUN pip install --no-cache-dir -r requirements.txt

# We run a small script to force the download of weights into /opt/models
RUN mkdir -p /opt/models && \
    python -c "import os; \
    from sentence_transformers import SentenceTransformer; \
    from marker.models import create_model_dict; \
    print('Downloading Embedding models...'); SentenceTransformer('all-MiniLM-L6-v2'); \
    print('Downloading Marker v2 models...'); create_model_dict()"

# Stage 2 - The Runtime
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    HF_HOME="/opt/models" \
    TORCH_HOME="/opt/models" \
    TORCH_DEVICE="cpu" \
    INFERENCE_DEVICE="cpu"

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    libmagic1 \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 appuser

RUN mkdir -p /tmp/scholar_rag_staging && \
    chown -R appuser:appuser /tmp/scholar_rag_staging && \
    chmod 775 /tmp/scholar_rag_staging

COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
COPY --from=builder --chown=appuser:appuser /opt/models /opt/models

WORKDIR /code
COPY --chown=appuser:appuser ./app ./app

USER appuser
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]