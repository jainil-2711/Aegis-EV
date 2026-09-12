# GreenCharge — GreenCharge Prototype (P1–P4 integrated)

This is the P1 (Grid & Data) slice of the GreenCharge backend, built per
`docs/DEV_WORKFLOWS.md`. It runs standalone with zero external services.

## What's included

- Full repo scaffold: FastAPI app, SQLAlchemy models/schemas for the whole
  data model, DB wiring (shared foundation for P2/P3/P4 to build on).
- P1's own modules: synthetic data generator, seed script, the shared
  `services/shared/ev_load.py`, and all `/api/grid/*` endpoints.
- Integrated P1–P4 backend and frontend slices with automated tests.

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

By default the app uses a local SQLite file (`greencharge.db`) — no
database server required. To use the provided PostgreSQL container
instead (matches architecture.md's chosen stack):

```bash
docker compose up -d postgres
cp .env.example .env
# edit .env: uncomment the postgresql:// DATABASE_URL line
```

## Seed the demo dataset

```bash
# from repo root
python scripts/seed_demo.py
```

Re-runnable any time — it wipes and regenerates only the P1-owned tables
(stations, chargers, evs, energy_slots), deterministically (fixed seed).

## Run the API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Then:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/grid/status
curl http://localhost:8000/api/grid/forecast
curl http://localhost:8000/api/grid/ev-load
curl -X POST http://localhost:8000/api/grid/signals \
  -H "Content-Type: application/json" \
  -d '{"start_time":"2026-09-12T18:00:00","end_time":"2026-09-12T20:00:00","condition":"high_demand","recommended_ev_load_kw":300,"signal_operator":"lte","renewable_availability":"low"}'
curl http://localhost:8000/api/grid/signals
```

Interactive API docs: `http://localhost:8000/docs`

## Run tests

```bash
cd backend
python -m pytest app/tests -v
```

## Next developer

Read `docs/DEV_WORKFLOWS.md` before starting P2/P3/P4 work — it tells you
exactly which files are yours and what's already been built here that you
should read (not duplicate), especially `services/shared/ev_load.py` and
the `backend/app/schemas/` / `backend/app/models/` foundation.

## Data validation

The synthetic generator is deterministic but intentionally independent of optimizer outcomes.
For a lightweight anti-demo-tuning check, validation uses multiple seeds:

```bash
cd backend
python -m pytest app/tests/test_synthetic_generator.py -q
```

Fresh demo data is generated from the repository root with:

```bash
python scripts/seed_demo.py
```

Set `GREENCHARGE_SEED` to a different deterministic seed when validating alternate datasets.
