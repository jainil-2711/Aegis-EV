# GreenCharge — Unified Developer Workflow (P1–P4)

> **Purpose:** This is the single coordination file all four AI coding sessions
> read before doing any work. It turns `phases.md` + `architecture.md` +
> `api-contract.md` + `data-spec.md` + `schemas.py` / `api.ts` into a concrete,
> file-level task list per developer, in build order, so four independent
> sessions never touch the same file in the same phase.
>
> Every developer still reads `rules.md` and `architecture.md` first, per the
> AI START PROMPT in `rules.md` §25. This file does not replace those — it
> sequences them.

---

## 0. Ground Rules (apply to all four)

0. **Synthetic-data independence (P1):** Synthetic EV/grid inputs are generated independently of optimizer outcomes.
   P1 must not reduce target SOC, alter charging windows, reassign driver requests,
   or otherwise tune input values solely to make the optimizer feasible or improve demo metrics.
   Physical validity checks are allowed; modifying a generated request after inspecting solver capacity is not.
   Validation should include multiple deterministic seeds (currently 7, 42, 123, 999).

1. **The contract is frozen before Phase 0.** `schemas.py` (backend) and
   `api.ts` (frontend) are already fully specified in this repo. No developer
   invents new field names, endpoints, or enum values. If something is
   missing, it goes in the **STOP list** (§7), not silently added.
2. **One file, one owner, per phase.** The ownership table in §2 is
   authoritative for *this hackathon*. If two people genuinely need to touch
   the same file in the same phase, that's a STOP-list item, not a race.
3. **`services/shared/ev_load.py` is the one exception**: P1 authors it in
   Phase 1, and after that it is read-only for everyone except via a
   coordinated PR (architecture.md §4, rules.md §14).
4. **Baseline computation lives inside `POST /optimization/run`** (P2-owned),
   never duplicated elsewhere (architecture.md §6).
5. Every phase below ends with an **Exit Check** — the next phase does not
   start for a given dev until their own exit check passes, but devs do not
   block each other unless the dependency is explicit.

6. **Fresh demo data:** When starting the UI with a fresh/changed dataset, run `python scripts\seed_demo.py` from the repo root.
   The test suite seeds its own test database; the running demo does not.

7. Handoff format at the end of every task is the standard block from
   `memory.md` §21 / `rules.md` §23 (`DONE / FILES / TESTS / ASSUMPTIONS /
   SHARED IMPACT / BLOCKERS / NEXT`).

---

## 1. Roles Recap

| Dev | Owns |
|---|---|
| **P1** | Grid & Data — synthetic data generator, seed script, `/api/grid/*`, `services/shared/ev_load.py` (initial author) |
| **P2** | Optimization & AI — OR-Tools engine, `/api/optimization/*`, pricing/carbon/green-score engines, optional `/api/explanations/*` |
| **P3** | Driver — `/api/driver/*`, driver frontend pages |
| **P4** | Charging Network Operator — `/api/stations`, `/api/chargers`, `/api/operator/*` (network status/impact), operator frontend pages |

Shared (nobody exclusively owns, all coordinate): `backend/app/schemas/`,
`backend/app/models/`, `backend/app/main.py`, migrations,
`frontend/src/types/api.ts`, `services/shared/ev_load.py`,
generic shared components (`MetricCard`, `StatusBadge`, etc.).

---

## 2. File Ownership Map

```text
backend/app/
├── main.py                        SHARED (Phase 0 scaffold, then append-only route registration)
├── api/
│   ├── health.py                  SHARED (Phase 0, trivial)
│   ├── grid.py                    P1
│   ├── driver.py                  P3
│   ├── operator.py                P4   (stations, chargers, network status/impact)
│   ├── optimization.py            P2
│   └── explanations.py            P2   (optional, Phase 11)
├── models/                        SHARED — coordinate before editing (rules.md §13)
├── schemas/                       SHARED — mirror of schemas.py, split by domain, frozen contract
├── services/
│   ├── grid/                      P1
│   ├── driver/                    P3
│   ├── operator/                  P4
│   ├── optimization/              P2
│   └── shared/ev_load.py          P1 authors in Phase 1; read-only after
├── engine/
│   ├── pricing.py                 P2
│   ├── carbon.py                  P2
│   └── green_score.py             P2
├── data/
│   ├── synthetic/                 P1
│   └── external/                  P1 (optional Open-Meteo adapter)
└── tests/                         each dev owns tests for their own module

frontend/src/
├── types/api.ts                   SHARED — frozen, mirrors schemas.py
├── services/                      one API client file per domain: grid.ts (P1), driver.ts (P3), operator.ts (P4), optimization.ts (P2)
├── components/                    SHARED generic components — check before adding a duplicate (design.md §4)
├── pages/
│   ├── driver/                    P3
│   ├── operator/                  P4
│   └── grid/                      P1
└── hooks/                         each dev owns hooks for their own domain

scripts/seed_demo.py               P1
docker-compose.yml, .env.example   SHARED (Phase 0 scaffold)
```

---

## 3. Build Order (why this sequence avoids collisions)

Because the contract (`schemas.py` / `api.ts`) is already frozen, all four
devs can build in parallel against it. The only real dependency chain is:

```text
Phase 0  Scaffold (shared, once)
   ↓
Phase 1  P1 seed/data + shared ev_load.py   ──┐
         P2 optimizer skeleton               │  parallel, no shared files touched
         P3 driver page skeleton             │
         P4 operator page skeleton          ──┘
   ↓
Phase 2  First vertical slice: P1 data → P2 optimizer → P3 driver recommendation
   ↓
Phase 3  P2 hardens optimizer (constraints, modes, baseline)
   ↓
Phase 4  P4 integrates operator view against P2's real output
   ↓
Phase 5  P1 integrates grid view + signals
   ↓
Phase 6–13  Renewable intelligence, pricing, driver polish, impact, green score,
            optional AI, scenarios, simulated-live — each dev works their own
            files per §2, consuming the shared contract, nobody touches
            another owner's file.
   ↓
Phase 14  Integration sprint (all four, but touching only their own files +
           main.py route wiring)
   ↓
Phase 15–17  Demo, polish, final validation
```

This mirrors `phases.md` exactly; the only addition here is pinning **which
file** each hour-range maps to, so four separate AI sessions never guess.

---

## 4. Per-Person Task Checklists

### 4.1 P1 — Grid & Data

**Phase 0 (Hr 0–1.5) — shared scaffold participation**
- Confirm repo/dirs from `architecture.md` §4 exist.
- Files: none exclusive yet.

**Phase 1 (Hr 1–3) — Skeleton**
- `backend/app/data/synthetic/` — deterministic generator: 40 EVs, 5–8
  stations, 20–30 chargers, 24h horizon, 30-min slots, fixed seed
  (data-spec.md §16).
- `scripts/seed_demo.py` — runs generator, writes to DB, idempotent re-run.
- `backend/app/services/shared/ev_load.py` — **single source of truth** for
  `current_ev_load_kw`, `scheduled_ev_load_kw`, `peak_ev_load_kw`
  (architecture.md §4). Export a plain function, no side effects, callable by
  both `grid.py` and `operator.py`.
- `backend/app/api/grid.py` — stub routes returning schema-shaped placeholder
  data: `GET /api/health` shared trivially, `GET /api/grid/status`,
  `GET /api/grid/forecast`.
- Exit check: seed script runs twice → identical output; health endpoint
  returns `{status:"ok"}`.

**Phase 2 (Hr 3–7) — Vertical slice support**
- Ensure EV/charger/energy data produced in Phase 1 is queryable by P2's
  optimizer (read-only for P2). No API shape changes without updating
  `api-contract.md` + `schemas.py` + `api.ts` together (rules.md §12).

**Phase 5 (Hr 10–15) — Grid integration**
- `backend/app/api/grid.py` — finish `GET /api/grid/status` (demand,
  capacity, renewable generation, `ev_load` from shared module, headroom),
  `GET /api/grid/forecast` (EnergySlot list), `POST /api/grid/signals`,
  `GET /api/grid/signals`, `GET /api/grid/ev-load`.
- `frontend/src/pages/grid/` — Grid dashboard: demand/capacity/renewable
  chart, EV load cards, headroom, signal publishing form (design.md §8).
- `frontend/src/services/grid.ts` — typed API client using `api.ts`.
- Exit check: publishing a signal via UI persists and appears in
  `GET /api/grid/signals`; P2's optimizer can read it as a soft signal.

**Phase 6 (Hr 12–17) — Renewable intelligence**
- Deterministic synthetic renewable profiles feeding `EnergySlot.renewable_kw`.
- Optional Open-Meteo adapter in `backend/app/data/external/`, isolated
  behind an adapter with synthetic fallback (architecture.md §11).

**Phase 14+ — Integration/polish**
- Only touch `grid.py`, `services/grid/`, `pages/grid/`, `ev_load.py`.

---

### 4.2 P2 — Optimization & AI

**Phase 1 (Hr 1–3) — Skeleton**
- `backend/app/services/optimization/` — OR-Tools (CP-SAT/MILP) service
  skeleton with a canonical interface: `run(mode, scenario) -> candidate +
  baseline`.
- `backend/app/api/optimization.py` — stub `POST /api/optimization/run`
  returning schema-shaped placeholder data.
- Exit check: optimizer service importable and callable with dummy data.

**Phase 2 (Hr 3–7) — Vertical slice**
- Real `POST /api/optimization/run`: consumes P1's seeded EV/charger/energy
  data, produces a `candidate` `OptimizationRunResponse` (status enum from
  data-spec.md §11).
- Exit check: driver (P3) can call this end-to-end and get a real schedule.

**Phase 3 (Hr 6–11) — Optimization maturity**
- Implement hard constraints: charger max power, station capacity, physical
  grid capacity, arrival/departure, target SOC, efficiency (architecture.md
  §8).
- Implement soft signals: grid demand, renewable availability, price, carbon
  intensity, operator objective, driver preference (architecture.md §9).
- Implement `cheapest` / `greenest` / `balanced` modes.
- **Baseline computation**: inside the same `run` handler, one deterministic
  rule — "charge immediately at max feasible power within each EV's window"
  (architecture.md §6). Never compute baseline elsewhere.
- `POST /api/optimization/apply`, `GET /api/optimization/{id}`,
  `GET /api/optimization/schedule` — apply transitions status to `applied`,
  supersedes prior applied run (data-spec.md §12).

**Phase 7 (Hr 14–18) — Carbon and pricing**
- `backend/app/engine/pricing.py` — deterministic, transparent, bounded,
  non-punitive rule (PRD.md §8). Never triggered punitively by driver
  override (rules.md §18).
- `backend/app/engine/carbon.py` — renewable share, CO₂, CO₂ reduction
  formulas (PRD.md §9).
- `backend/app/engine/green_score.py` — 0–100 deterministic, informational,
  non-punitive.
- These three engines are called from `optimization.py` and surfaced via
  `NetworkImpactResponse.pricing_rule`, `DriverRecommendationResponse`, etc.
  Exposed via existing endpoints only — **no new pricing endpoint**
  (api-contract.md §8).

**Phase 11 (Hr 20–23) — Optional AI explanation**
- `backend/app/api/explanations.py` — `POST /api/explanations/charging`.
  Takes already-computed deterministic numbers, produces text only. No
  numerical decisions. Deterministic template fallback if no LLM configured
  (PRD.md §14, architecture.md §12).

**Phase 12 (Hr 21–25) — Scenarios**
- `POST /api/scenario` (optional) — modifies the one base dataset per
  `Scenario` enum, no second dataset (api-contract.md §11).

**Phase 14+ — Integration/polish**
- Only touch `optimization.py`, `services/optimization/`, `engine/*`,
  `explanations.py`.

---

### 4.3 P3 — Driver

**Phase 1 (Hr 1–3) — Skeleton**
- Role selection screen (shared, but P3 can scaffold it) +
  `frontend/src/pages/driver/` skeleton.
- `backend/app/api/driver.py` — stub `GET /api/driver/session`.

**Phase 2 (Hr 3–7) — Vertical slice**
- `GET /api/driver/session` — returns demo driver's EV/session
  (`DriverSessionResponse`).
- `GET /api/driver/recommendation` — derived only from P2's active/applied run
  (`DriverRecommendationResponse`); candidates are not exposed to drivers.
- `POST /api/driver/schedule/accept`, `POST /api/driver/schedule/override`
  (override never triggers punitive pricing/access — rules.md §18; infeasible
  override returns explanation + alternatives, not a silent failure).
- Exit check: driver can see an EV, get a real optimizer-backed
  recommendation, and accept it (phases.md §6 exit criterion).

**Phase 8 (Hr 15–20) — Driver experience**
- Full driver page: battery/SOC, target SOC, departure time, preference
  selector, recommendation card (window, cost, price/kWh, renewable share,
  CO₂, Green Score), "Why" explanation, Accept / Override actions
  (design.md §6).
- `POST /api/driver/preferences`.

**Phase 13 (Hr 20–24) — Simulated-live session** (joint with P4 pattern, but
driver-side files only)
- `GET /api/driver/session/status` — polling-based simulated-live SOC/cost/
  renewable/CO₂ progression, `simulated: true` always set and labeled in UI
  (api-contract.md §12, design.md §13).

**Phase 14+ — Integration/polish**
- Only touch `driver.py`, `services/driver/`, `pages/driver/`.

---

### 4.4 P4 — Charging Network Operator

**Phase 1 (Hr 1–3) — Skeleton**
- `frontend/src/pages/operator/` skeleton, network metrics skeleton.
- `backend/app/api/operator.py` — stub `GET /api/stations`,
  `GET /api/chargers`.

**Phase 2 (Hr 3–7) — Initial network summary**
- Real `GET /api/stations`, `GET /api/chargers` against P1's seeded data.

**Phase 4 (Hr 8–13) — Operator integration**
- `GET /api/network/status` — active EVs/chargers, `ev_load` (from
  `services/shared/ev_load.py`, **read-only** — do not reimplement),
  renewable availability %, grid demand/capacity/renewable generation.
- Optimization controls in UI: mode selector (cheapest/greenest/balanced),
  Run button → calls P2's `POST /api/optimization/run`.
- Candidate vs. active schedule display; Apply button → P2's
  `POST /api/optimization/apply`.
- `GET /api/network/impact` — before/after peak/cost/renewable/CO₂ **plus**
  `pricing_rule` (sourced from P2's pricing engine, just surfaced here per
  api-contract.md §5/§8 — P4 does not compute pricing).
- `frontend/src/pages/operator/` — metric cards, network chart (demand vs
  capacity vs renewable vs EV load), before/after impact card
  (design.md §7, §11).
- Exit check: operator can run optimization, see before/after, apply it, and
  that becomes the schedule Driver/Grid views see.

**Phase 9 (Hr 17–21) — Network impact polish**
- Finish before/after visualization, avoid misleading scales
  (design.md §11).

**Phase 14+ — Integration/polish**
- Only touch `operator.py`, `services/operator/`, `pages/operator/`.

---

## 5. Cross-Cutting Sync Checkpoints (from phases.md §3, §27)

| Checkpoint | Who must be done | Gate |
|---|---|---|
| First vertical slice (end Phase 2) | P1 data ready, P2 optimizer real, P3 driver flow | Driver sees a real recommendation and can accept it |
| Integration sprint start (Phase 14) | P1/P2/P3/P4 individually feature-complete | Same EV IDs, same charger IDs, same units, one active schedule across all views |
| Feature freeze (~Hr 30) | All | No new features, only fixes |
| Final validation (Phase 17) | All | Seed, build, tests, full demo script (phases.md §19) all pass |

---

## 6. What Nobody Should Ever Do (rules.md §6, §22 — STOP conditions)

- Change a field name/enum/response shape in `schemas.py`/`api.ts` without
  updating both files + `api-contract.md` + `CHANGELOG.md` in the same PR.
- Compute `current_ev_load_kw` / `scheduled_ev_load_kw` / `peak_ev_load_kw`
  anywhere except `services/shared/ev_load.py`.
- Compute baseline metrics anywhere except inside
  `POST /api/optimization/run`.
- Add a dedicated pricing endpoint.
- Wire driver override to any pricing/access penalty.
- Introduce microservices, a second database, a second optimizer, or any
  mandatory paid dependency.
- Add WebSockets/OCPP/real vehicle control for the "real-time" requirement.

---

## 7. STOP List (fill in if something is genuinely ambiguous)

```text
None yet.
```

---

## 8. Handoff Report Template (use after every task, per dev)

```text
DEV: P#
PHASE: #
DONE
- ...
FILES
- ...
TESTS
- ...
ASSUMPTIONS
- ...
SHARED IMPACT
- None / ...
BLOCKERS
- None / ...
NEXT
- ...
```

---

## 9. Environment & Test Prerequisites (must be checked before claiming tests pass)

1. Before running backend tests, install the complete dependency set from:
   `backend/requirements.txt`.
2. **OR-Tools is a required runtime dependency for P2 optimization.** It is not optional for a working optimization implementation.
3. Run the backend test suite from the repository with:
   `pytest -q backend/app/tests`
4. Do not report the suite as fully verified if OR-Tools is unavailable. If OR-Tools is missing, the optimizer-specific solver tests may be skipped or unavailable; explicitly report that limitation.
5. A future developer/AI who encounters an OR-Tools import or solver failure must install the declared dependency first rather than replacing OR-Tools, creating a fallback optimizer, or changing the optimization architecture.
6. Previous verification status (before local OR-Tools installation): **16 passed, 3 skipped** because the environment could not install OR-Tools.
7. After P1–P4 integration, the repository has a self-contained deterministic test dataset. Environments without OR-Tools may skip only optimizer-dependent tests; once OR-Tools is installed, those tests must execute.
8. A seeded EV must be physically coherent as an input: its requested energy must fit its own requested charging rate and connection window, and its assigned charger must have sufficient physical power. P1 must not change a generated EV target after inspecting optimizer capacity. P2 remains responsible for time-slot scheduling and charger/grid constraints.
9. Synthetic-data validation must include multiple deterministic seeds (currently 7, 42, 123, 999) and confirm that different seeds produce genuinely different but valid fleets.
10. The current repository requires OR-Tools for full P2 verification. Once installed, rerun the full suite and treat any optimizer failure as a real implementation issue, not a reason to skip the tests.

---

## Current Integrated Implementation State — P1 + P2 + P3 + P4

The actual repository currently contains the integrated P1/P2/P3/P4 backend and the Grid, Driver, and Charging Network Operator frontend views.

### P2 complete through current optimization phase

- Canonical OR-Tools optimizer service and optimization API are present.
- `POST /api/optimization/run` creates a candidate run only.
- `POST /api/optimization/apply` promotes a candidate to the active schedule and supersedes the prior active run.
- `GET /api/optimization/{id}` and `GET /api/optimization/schedule` expose optimization state.
- P2 exposes read-only optimization-state helpers for other role modules.
- Deterministic pricing rule exists as a P2-owned engine and is surfaced inside operator impact responses; no dedicated pricing endpoint is used.

### P3 complete for current driver phase

- Driver session, preference, recommendation, accept, override, and simulated-live status endpoints are integrated. Driver recommendations and accepts require the active/applied optimization schedule; candidate runs are never exposed to drivers.
- Driver logic consumes P2 optimization state and P1's simulation clock/flexibility data.
- Overrides remain non-punitive and infeasible requests return explanations/alternatives.

### P4 complete for current operator phase

- `GET /api/stations`
- `GET /api/chargers`
- `GET /api/network/status`
- `GET /api/network/impact`
- Operator optimization controls call the existing P2 optimization client; P4 does not duplicate optimizer logic.
- Network EV-load values MUST come from P1's shared `services/shared/ev_load.py` path.
- Network grid figures use P1's existing grid-status service so network/grid views share the same source logic.

### Frontend integration

The original P1 repository did not contain a frontend scaffold. A minimal Vite/React/Tailwind scaffold now mounts the Driver and Charging Network Operator views. This does not add a new business layer or alternate backend API.

Frontend build dependencies must be installed before running the build:

```text
cd frontend
npm install
npm run build
```

### Verification snapshot

- The user's Windows/Python 3.14 environment previously verified the integrated P1–P4 backend at **32 passed, 1 skipped** with OR-Tools 9.15.6755 installed, before the synthetic-data independence change.
- After the current synthetic-data change, the repository's local test suite must be rerun by the team; the generator-specific suite now includes multi-seed validation for seeds **7, 42, 123, 999**.
- Environments without OR-Tools may skip only the optimizer-dependent tests; those tests are not considered verified until OR-Tools is installed and the tests execute successfully.

### Current data-integrity rule

Synthetic EV requests are generated independently of optimizer outcomes. P1 does not clamp target SOC after inspecting solver capacity. P1 may use domain/physical validity checks and deterministic rejection sampling against the EV's own requested power/window, but it must not tune inputs to improve optimization metrics or screenshots.

### Next integration owner

P1's Grid frontend is implemented under `frontend/src/pages/grid/`. It consumes the existing `/api/grid/*` contract and shared EV-load service; it does not duplicate backend Grid logic.


### Environment verification note — 2026-09-12

The integrated repository was rebuilt from the current uploaded repository and verified as a combined P1/P2/P3/P4 state.

Backend verification:
- `PYTHONPATH=. pytest -q app/tests`
- Result: **24 passed, 7 skipped, 2 warnings**
- The skipped tests are the OR-Tools-dependent solver tests because OR-Tools is unavailable in this execution environment.
- This is an environment limitation, not permission to omit OR-Tools.

Frontend verification:
- The repository contains the Vite/React frontend scaffold plus Driver and Operator views.
- `node_modules` is intentionally not included in the repository.
- `npm install` could not complete in this environment because the package installation command timed out.
- Therefore `npm run build` was not claimed as verified here.
- The next developer with normal npm package access MUST run:
  `cd frontend && npm install && npm run build`
  and report any TypeScript/build failures before treating the frontend as fully verified.

Integration rule:
- Do not revert P2 optimizer changes when applying P3/P4 changes.
- P3/P4 must consume P2 public integration helpers and the existing P1 shared services.
- Do not reintroduce duplicate optimization, EV-load, flexibility, grid-status, pricing, or simulation-clock logic.

### Synthetic-data integrity and simulated-live demo gate

- Synthetic data must be generated independently of optimizer outcomes. Do not tune EV demand, target SOC, charging windows, charger assignment, renewable profiles, prices, or other inputs solely to improve optimizer feasibility or demo metrics.
- The fixed seed makes the primary demo reproducible, but validation should use multiple deterministic seeds where practical.
- Test fixtures must seed their own required data; the running demo application must be seeded explicitly with `python scripts\seed_demo.py` from the repository root (or `python ..\scripts\seed_demo.py` from `backend/`).
- The Driver simulated-live flow must clearly distinguish `scheduled` (waiting for window), `charging` (window active), and `completed` (window finished). Use the shared simulation clock; do not use independent wall-clock calculations.
- Before commit, verify the Operator → optimization → apply → Driver → accept/override flow and confirm the status transitions are observable.
