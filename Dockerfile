# --- Stage 1: build the React frontend -------------------------------------
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build            # → /app/frontend/dist

# --- Stage 2: Python backend serving the API + built frontend ---------------
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY --from=frontend /app/frontend/dist frontend/dist

# Render injects $PORT; default to 8000 for local `docker run`.
ENV PORT=8000
# Shell form so $PORT expands at runtime.
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
