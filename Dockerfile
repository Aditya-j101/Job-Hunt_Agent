# ── Stage 1: Build React frontend ──────────────────────────────
FROM node:18-slim AS frontend-builder
WORKDIR /app/Frontend

COPY Frontend/package*.json ./
RUN npm ci

COPY Frontend/ .
RUN npm run build

# ── Stage 2: Python backend ─────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# copy built React files from Stage 1
COPY --from=frontend-builder /app/Frontend/dist ./Frontend/dist

RUN mkdir -p data/sample_jobs

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]