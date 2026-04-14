"""
main.py
========
DAF Phase 1 — FastAPI application entry point.

Run from the daf/ project root:
    uvicorn main:app --reload
"""

import sys
import os

# Ensure the project root is always on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from settings import app_settings
from database import engine, Base, UserModel  # noqa: F401
from routes import router


# ---------------------------------------------------------------------------
# Lifespan — create DB tables on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title=app_settings.APP_NAME,
    version=app_settings.VERSION,
    description=(
        "Dynamic Auth Framework — Phase 1. "
        "Built on the Dynamic Password Protocol (DPP). "
        "Original research: H. Channabasava & S. Kanthimathi, CompCom 2019."
    ),
    lifespan=lifespan,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(router)
