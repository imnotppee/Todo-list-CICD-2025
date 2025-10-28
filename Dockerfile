# ---------- Build stage ----------
FROM python:3.11-slim AS builder
WORKDIR /app

# ติดตั้ง dependencies ที่จำเป็นตอน build
RUN apt-get update && apt-get install -y --no-install-recommends gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---------- Runtime stage ----------
FROM python:3.11-slim

# สร้าง user สำหรับรันแอป
RUN useradd -m -u 1000 appuser
WORKDIR /app

# ติดตั้ง dependencies ที่ใช้ตอนรัน
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# คัดลอก dependencies จาก builder stage
COPY --from=builder /root/.local /home/appuser/.local

# คัดลอกโค้ดแอปทั้งหมด
COPY --chown=appuser:appuser . .

# ตั้งค่า environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py

USER appuser

# expose port สำหรับ local หรือ container ภายใน
EXPOSE 5000

# Health check (Railway/Render ใช้ได้)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')" || exit 1

# ✅ ใช้ ${PORT:-5000} เพื่อให้รองรับทั้ง Railway (มี $PORT) และ Render/local (ไม่มี $PORT)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 4 --timeout 120 run:app"]
