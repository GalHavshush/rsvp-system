# RSVP System

Self-hosted, open-source event management: personalized RSVP links, guest lists and visual seating.
Hebrew (RTL) first, English supported. Messaging runs in test mode (CSV export), so no WhatsApp account is needed.

**Status:** early development. Done: login, events, Hebrew/English UI. Next: guests, import, RSVP links, seating.

## Run

```bash
cp .env.example .env   # set POSTGRES_PASSWORD
docker compose up --build
```

Open http://localhost:8080. The first account you create is the owner. Data is kept in the `pgdata` volume.

## Develop

```bash
cd backend && uv sync && uv run uvicorn app.main:app --reload   # needs Postgres, set DATABASE_URL
cd frontend && npm i && npm run dev
```

License: MIT
