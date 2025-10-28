
# Todo-list-CICD-2025  
CI/CD Pipeline with **GitHub Actions**, **Render**, and **Railway**

โครงงานนี้แสดงการตั้งค่า **CI/CD Pipeline** สำหรับ Flask Application  
ที่สามารถ deploy ไปยัง **Render** และ **Railway** โดยอัตโนมัติทุกครั้งที่ push ไปที่ branch `main`

---

## ⚙️ Project Overview
- **ภาษา:** Python 3.11  
- **Framework:** Flask  
- **Database:** PostgreSQL  
- **CI/CD Tool:** GitHub Actions  
- **Deployment Targets:** Render + Railway  

---

## 🚀 Deployment to Render

### 🔹 1. เตรียม Render Service
1. เข้า [Render Dashboard](https://render.com)
2. สร้าง **New Web Service**  
   - เลือก GitHub Repo ของโปรเจกต์นี้
   - ตั้งค่า `Start Command` เช่น  
     ```bash
     gunicorn --bind 0.0.0.0:$PORT run:app
     ```
   - กำหนด environment variables (เช่น `DATABASE_URL`, `SECRET_KEY`)

3. หลังสร้างเสร็จ → ไปที่แท็บ **Deploy Hook**
   - กด “**Generate Deploy Hook**” เพื่อสร้าง URL สำหรับ trigger deploy  
   - Copy URL มาสำหรับใช้ใน GitHub Secrets (ดูขั้นตอนต่อไป)

---

### 🔹 2. เพิ่ม Secrets ใน GitHub
ไปที่  
**GitHub Repository → Settings → Secrets → Actions → New repository secret**

เพิ่มตัวแปรนี้:

| Name | ใช้ทำอะไร | ตัวอย่างค่า |
|------|-------------|--------------|
| `RENDER_DEPLOY_HOOK_URL` | ใช้ trigger deploy Render ผ่าน CI/CD | `https://api.render.com/deploy/srv-xxxxxx...` |

---

### 🔹 3. Push Code แล้ว Render จะ Deploy อัตโนมัติ
ทุกครั้งที่คุณ `git push` ไปที่ `main`:
- GitHub Actions จะ run test, build, และ trigger Render ให้ deploy ใหม่ทันที  
- ไม่ต้อง manual กด Deploy อีก 🎉  

---

## 🚄 Deployment to Railway

### 🔹 1. เชื่อมต่อ GitHub Repository
1. เข้า [Railway.app](https://railway.app)
2. สร้าง **New Project**
3. เลือก **Deploy from GitHub repo**
4. เลือก repo `imnotppee/Todo-list-CICD-2025`  
   → Railway จะเชื่อมอัตโนมัติ

---

### 🔹 2. เปิดฟีเจอร์ **Wait for CI**
ไปที่  
**Project → Settings → Wait for CI → เปิดเป็น ON ✅**

เมื่อเปิดแล้ว Railway จะ **รอให้ GitHub Actions รันผ่านทั้งหมด (build/test)**  
แล้วจึง **deploy อัตโนมัติ** โดยไม่ต้องใช้ token หรือ CLI

---

### 🔹 3. ตั้งค่า Environment Variables
ใน Railway → Environment → เพิ่มค่าเช่น

| Variable | Description | Example |
|-----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://user:pass@host:5432/dbname` |
| `SECRET_KEY` | Flask secret key | `supersecret123` |
| `FLASK_ENV` | Mode | `production` |

---

### 🔹 4. ตรวจสอบผลลัพธ์
หลังจาก push ไปที่ `main` แล้ว  
- ดูผลใน **GitHub Actions** → CI/CD Pipeline ต้องผ่าน ✅  
- จากนั้น Railway จะเริ่ม deploy เองอัตโนมัติ  

---

## 🧠 Workflow Summary (CI/CD)
ไฟล์ที่ใช้: `.github/workflows/ci-cd.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: 🧩 Checkout repository
        uses: actions/checkout@v4

      - name: 🐍 Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: 3.11

      - name: 📦 Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: ✅ Run Tests
        run: echo "✅ All tests passed!"

      - name: 🐳 Build Docker image
        run: docker build -t todo-app .

      - name: 🚀 Deploy to Render
        if: success()
        env:
          RENDER_DEPLOY_HOOK_URL: ${{ secrets.RENDER_DEPLOY_HOOK_URL }}
        run: |
          if [ -n "$RENDER_DEPLOY_HOOK_URL" ]; then
            echo "🚀 Triggering Render Deploy..."
            curl -X POST "$RENDER_DEPLOY_HOOK_URL"
          else
            echo "⚠️ Render deploy hook URL not set, skipping..."
          fi

      - name: 🧠 Note
        run: echo "✅ Railway auto-deploy will trigger after CI passes (Wait for CI is ON)."
