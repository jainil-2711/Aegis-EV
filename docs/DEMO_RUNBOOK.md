# Aegis HackOut'26 Demo Runbook

## Start clean

Run the seed from the repository root or from `backend/`. The local SQLite path is anchored to the backend package, so both commands use the same database.

```powershell
cd C:\path\to\aegis
python scripts/seed_demo.py
```

Expected seed output:

```text
Seeded 6 stations, 24 chargers, 40 EVs, 48 energy slots (seed=42, demo_day=2026-09-12).
Demo runtime state reset: runs=0, schedule_entries=0, sessions=0, grid_signals=0
```

## Start services

Backend:

```powershell
cd backend
python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Demo identities

| Role | Email | Password |
|---|---|---|
| Grid Operator | grid@aegis.local | AegisGrid26! |
| Network Operator | network@aegis.local | AegisNet26! |
| EV Driver | driver@aegis.local | AegisDriver26! |

## End-to-end story

1. Sign in as Grid Operator.
2. Review demand, capacity, renewable generation, aggregate EV load and headroom.
3. Publish a quantitative `high_demand` or `high_renewable` GridSignal.
4. Sign out and sign in as Network Operator.
5. Review the network telemetry and the real 30-minute network chart.
6. Choose an optimization mode and a deterministic scenario.
7. Run optimization. The result is a candidate only.
8. Review the explicit `Baseline → optimized` metrics and Decision Trace.
9. Publish/apply the candidate as the active schedule.
10. Sign out and sign in as EV Driver.
11. Verify that the recommendation shows the exact active run ID.
12. Review cost, price, renewable share, CO₂ and Green Score.
13. Expand `Why this window?` and the Aegis Intelligence trace.
14. Accept the recommendation or use `Override / Charge now`.
15. Return to the Network Operator to inspect active network impact.

## Authorization checks

A signed token does not grant cross-role privileges. The backend enforces role access on every protected endpoint.

- Grid Operator: Grid views + GridSignal publishing.
- Network Operator: network views + optimization run/apply.
- EV Driver: driver session/preferences/recommendation/accept/override.

Changing frontend URLs or tabs cannot bypass these server-side checks.

## Core invariants to explain to judges

- `run` creates a candidate; `apply` creates the single active schedule.
- Driver recommendations use the active schedule, never an unapplied candidate.
- GridSignals are advisory optimization signals, while physical limits remain hard constraints.
- Renewable energy is allocated as a shared slot resource; it cannot be double-counted across EVs.
- Driver override is allowed and never causes a fine, punitive price or reduced access.
- Green Score is deterministic and informational.
- Aegis Intelligence is an auditable explanation/decision trace, not a black-box numerical controller.
