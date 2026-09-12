"""GreenCharge FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import driver, grid, health, optimization, operator
from app.config import get_settings
from app.database import create_all_tables

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_all_tables()
    yield


app = FastAPI(
    title="GreenCharge API",
    description="Renewable-aware EV charging orchestration platform (HackOut'26 PS 7).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(grid.router)
app.include_router(optimization.router)
app.include_router(driver.router, prefix="/api/driver", tags=["driver"])
app.include_router(operator.router, prefix="/api", tags=["operator"])
