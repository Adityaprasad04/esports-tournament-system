"""
NexusArena Esports Tournament System — FastAPI Backend
Data Engineering Capstone Project
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from database.db import init_db
from routes import players, teams, tournaments, matches, leaderboard, analytics
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize database and seed data."""
    logger.info("Starting NexusArena Backend...")
    init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down NexusArena Backend.")


app = FastAPI(
    title="NexusArena Esports API",
    description="Data Engineering Capstone — Esports Tournament System REST API",
    version="1.0.0",
    lifespan=lifespan
)

# Allow frontend requests (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(players.router,     prefix="/players",     tags=["Players"])
app.include_router(teams.router,       prefix="/teams",       tags=["Teams"])
app.include_router(tournaments.router, prefix="/tournaments", tags=["Tournaments"])
app.include_router(matches.router,     prefix="/matches",     tags=["Matches"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboard"])
app.include_router(analytics.router,   prefix="/analytics",   tags=["Analytics"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "online", "system": "NexusArena", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "db": "connected", "etl": "active"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
