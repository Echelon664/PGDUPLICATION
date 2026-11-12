FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install dependencies first so this layer is cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application and data. data/search.db is excluded via .dockerignore
# and is built automatically on first request.
COPY . .

# Run as an unprivileged user; /app/data must stay writable for the index.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c 'import os,urllib.request,sys; p=os.environ.get("PORT","8000"); sys.exit(0 if urllib.request.urlopen(f"http://127.0.0.1:{p}/health", timeout=3).status==200 else 1)'

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
