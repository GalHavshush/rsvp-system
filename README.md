# RSVP System

Self-hosted, open-source event management: RSVP via personalized links, spreadsheet import, visual seating.
Hebrew (RTL) first, English supported. Messaging runs in **test mode** (CSV export); no WhatsApp account needed.

**Status:** Phase 1 (auth, i18n/RTL, events). See the roadmap in the project plan.

## Run
```bash
cp .env.example .env   # set POSTGRES_PASSWORD
docker compose up --build
```
Open http://localhost:8080 (one container serves both the API and the web app; use your own reverse proxy for HTTPS) — the first account you create becomes the owner. Data lives in the `pgdata` volume.

## Develop
```bash
# backend (needs Postgres; DATABASE_URL env var)
cd backend && uv sync && uv run alembic upgrade head && uv run uvicorn app.main:app --reload
uv run pytest                      # tests expect Postgres at localhost:5433 (see tests/conftest.py)
# frontend
cd frontend && npm i && npm run dev   # proxies /api to :8000
# after changing API models:
cd backend && uv run python -c "import json;from app.main import app;json.dump(app.openapi(),open('openapi.json','w'),indent=1)"
cd frontend && npm run gen:api
```

## Backup / restore
```bash
docker compose exec db pg_dump -U rsvp rsvp > backup.sql
docker compose exec -T db psql -U rsvp rsvp < backup.sql
```

License: MIT
