# Aegis — Renewable EV Charging Orchestration

HackOut’26 · PS 7 — EV Charging Optimization

Aegis connects three authenticated roles through one deterministic charging state:

```text
Grid Operator → Grid Signal → Network Operator → OR-Tools
                                            ↓
                                      Active Schedule
                                            ↓
                                      EV Driver
                                     ↙         ↘
                                  Accept      Override
                                            ↓
                                       Network Impact
```

## Stack

- React + TypeScript + Vite
- FastAPI + Pydantic
- SQLAlchemy + SQLite by default / PostgreSQL via Docker
- OR-Tools CP-SAT
- Recharts
- No mandatory paid API or LLM

## Local setup

### Backend

```powershell
cd backend
pip install -r requirements.txt
python ..\scripts\seed_demo.py
python -m uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Grid Operator | `grid@aegis.local` | `AegisGrid26!` |
| Network Operator | `network@aegis.local` | `AegisNet26!` |
| EV Driver | `driver@aegis.local` | `AegisDriver26!` |

Authentication is local and signed with an HMAC token. The API also enforces role authorization, so changing the frontend route cannot grant another role's permissions.

## Clean demo reset

The seed script clears runtime state in dependency order, including optimization runs, schedules, sessions and grid signals, then regenerates the deterministic synthetic dataset.

```powershell
cd C:\path\to\aegis\backend
python ..\scripts\seed_demo.py
```

## Verification

Backend:

```powershell
cd backend
python -m pytest -q app/tests
```

Frontend:

```powershell
cd frontend
npm run build
```

The core demo works locally without an LLM or external API.

## Aegis Intelligence

The product uses an auditable **signal-fusion / decision-trace** experience rather than a generic chatbot. The deterministic layer exposes the inputs that explain a decision: grid signals, renewable availability, EV flexibility, operator objective and scenario. Any future LLM remains explanation-only and never calculates charging power, price, carbon or Green Score.

## Core invariants

- Only an applied optimization run becomes active.
- Driver recommendations use the active run only.
- Grid signals are optimization guidance, not a substitute for physical constraints.
- Driver override never triggers punitive pricing, fines or reduced access.
- Numerical decisions are backend-authoritative and deterministic.
- Synthetic data is labeled and reproducible.
