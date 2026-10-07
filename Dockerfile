FROM node:22-alpine AS web
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /srv
COPY backend/pyproject.toml ./
RUN uv pip install --system -r pyproject.toml
COPY backend/ .
COPY --from=web /app/dist /srv/static
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
