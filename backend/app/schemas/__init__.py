"""
Aegis — Pydantic schemas (SHARED, frozen contract)

Split by domain, mirroring backend/app/schemas/*.py in architecture.md SS4:
    enums.py, shared.py, health.py   -> shared, everyone reads
    grid.py                          -> P1
    driver.py                        -> P3 (added when P3 starts)
    operator.py                      -> P4 (added when P4 starts)
    optimization.py                  -> P2 (added when P2 starts)
    explanation.py, scenario.py      -> P2 / P1+P2, optional (added later)

Only grid/health/shared/enums exist so far — this file is being built out
incrementally as each developer's phase starts (see docs/DEV_WORKFLOWS.md).
"""
