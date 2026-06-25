FROM python:3.11-slim

# system deps needed for chromadb/sentence-transformers
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install deps first — caches this layer, faster rebuilds when only code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app code
COPY backend/ ./backend/

# chroma_db will be mounted as a volume, not baked into image
RUN mkdir -p /app/chroma_db

EXPOSE 8000

# health check — Docker restarts container if this fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]