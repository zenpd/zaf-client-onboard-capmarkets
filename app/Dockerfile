FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
EXPOSE 8002

# Default: run FastAPI backend
# Override CMD to run temporal worker: python -m workers.temporal_worker
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]

