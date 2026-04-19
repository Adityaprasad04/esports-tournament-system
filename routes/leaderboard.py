"""routes/leaderboard.py — Ranked player leaderboard"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from models.models import Player, Team

router = APIRouter()

@router.get("/")
def get_leaderboard(limit: int = 20, sort_by: str = "win_rate", db: Session = Depends(get_db)):
    """
    Return ranked player list.
    sort_by options: win_rate | kd_ratio | total_matches
    """
    sort_col = {
        "win_rate": Player.win_rate,
        "kd_ratio": Player.kd_ratio,
        "total_matches": Player.total_matches,
    }.get(sort_by, Player.win_rate)

    players = (
        db.query(Player)
        .order_by(sort_col.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "rank": i + 1,
            "player_id": p.player_id,
            "ign": p.ign,
            "name": p.name,
            "team_id": p.team_id,
            "role": p.role,
            "total_matches": p.total_matches,
            "win_rate": round(p.win_rate, 2),
            "kd_ratio": round(p.kd_ratio, 2),
        }
        for i, p in enumerate(players)
    ]
