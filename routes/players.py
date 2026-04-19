"""routes/players.py — Player endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from database.db import get_db
from models.models import Player, PlayerSchema, PlayerCreateSchema

router = APIRouter()


@router.get("/", response_model=List[PlayerSchema])
def get_players(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Fetch all players with pagination."""
    return db.query(Player).offset(skip).limit(limit).all()


@router.get("/{player_id}", response_model=PlayerSchema)
def get_player(player_id: str, db: Session = Depends(get_db)):
    """Fetch a single player by ID."""
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return player


@router.post("/", response_model=PlayerSchema, status_code=201)
def add_player(data: PlayerCreateSchema, db: Session = Depends(get_db)):
    """Add a new player. ETL will compute kd_ratio and win_rate from match data."""
    # Check IGN uniqueness
    if db.query(Player).filter(Player.ign == data.ign).first():
        raise HTTPException(status_code=409, detail=f"IGN '{data.ign}' already exists")

    player_id = "P" + str(uuid.uuid4())[:6].upper()
    player = Player(
        player_id=player_id,
        name=data.name,
        ign=data.ign,
        team_id=data.team_id,
        role=data.role,
        total_matches=0,
        win_rate=0.0,
        kd_ratio=0.0,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.get("/{player_id}/stats")
def get_player_stats(player_id: str, db: Session = Depends(get_db)):
    """Get aggregated stats for a player (computed from player_stats table)."""
    from models.models import PlayerStat, Match
    from sqlalchemy import func

    stats = db.query(
        func.sum(PlayerStat.kills).label("total_kills"),
        func.sum(PlayerStat.deaths).label("total_deaths"),
        func.sum(PlayerStat.assists).label("total_assists"),
        func.count(PlayerStat.stat_id).label("matches_with_stats"),
    ).filter(PlayerStat.player_id == player_id).first()

    if not stats or stats.matches_with_stats == 0:
        raise HTTPException(status_code=404, detail="No stats found for player")

    kd = round(stats.total_kills / max(stats.total_deaths, 1), 2)
    return {
        "player_id": player_id,
        "total_kills": stats.total_kills,
        "total_deaths": stats.total_deaths,
        "total_assists": stats.total_assists,
        "kd_ratio": kd,
        "matches_with_stats": stats.matches_with_stats,
    }
