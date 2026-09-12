# Single-image deployment (Render / any container host).
# Stage 1 builds the SPA, stage 2 runs FastAPI which serves both the API
# and the built frontend from one origin — see app/main.py spa_fallback.

# ---------- stage 1: build the frontend ----------
# Debian-based (not alpine): rolldown/lightningcss ship both gnu and musl
# binaries, but glibc is the better-trodden path and this stage is
# discarded anyway — only its dist/ output reaches the final image.
FROM node:22-slim AS frontend
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---------- stage 2: runtime ----------
FROM python:3.13-slim
WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONDONTWRITEBYTECODE=1

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
# Seed assets (style covers, hand samples, VLM tags) ship in-repo so the
# container can build a fully-imaged demo database with no external fetch.
COPY assets/ /app/assets/
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Runtime-written dirs are gitignored, so create them explicitly.
RUN mkdir -p static/cache static/uploads static/styles static/samples

CMD ["sh", "scripts/start.sh"]
