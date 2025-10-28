# ---------- Build stage ----------
FROM python:3.11-slim as builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---------- Runtime stage ----------
FROM python:3.11-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py

USER appuser
EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')" || exit 1

CMD ["bash", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 4 --timeout 120 run:app"]
