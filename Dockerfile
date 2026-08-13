FROM python:3.11-slim

# security — run as non-root user
RUN groupadd -r moreai && useradd -r -g moreai moreai

RUN apt-get update && apt-get install -y \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install deps first — layer cache optimization
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY backend/ ./backend/
COPY .env.example ./.env.example

# create dirs with correct ownership
RUN mkdir -p /app/chroma_db /app/mlruns /app/eval_runs \
    && chown -R moreai:moreai /app

# switch to non-root
USER moreai

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info"]