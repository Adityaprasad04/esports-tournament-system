"""routes/analytics.py — Analytics endpoints for dashboard"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.db import get_db
from models.models import Player, Match, PlayerStat, Team

router = APIRouter()


@router.get("/player-performance")
def player_performance(db: Session = Depends(get_db)):
    """
    Per-player aggregate performance metrics.
    Calculates: avg_kills, avg_deaths, avg_assists, kd_ratio, total_stats_matches
    """
    results = (
        db.query(
            PlayerStat.player_id,
            func.avg(PlayerStat.kills).label("avg_kills"),
            func.avg(PlayerStat.deaths).label("avg_deaths"),
            func.avg(PlayerStat.assists).label("avg_assists"),
            func.count(PlayerStat.stat_id).label("stat_matches"),
        )
        .group_by(PlayerStat.player_id)
        .all()
    )

    output = []
    for r in results:
        player = db.query(Player).filter(Player.player_id == r.player_id).first()
        kd = round(r.avg_kills / max(r.avg_deaths, 0.1), 2)
        output.append({
            "player_id": r.player_id,
            "ign": player.ign if player else "Unknown",
            "avg_kills": round(r.avg_kills, 1),
            "avg_deaths": round(r.avg_deaths, 1),
            "avg_assists": round(r.avg_assists, 1),
            "kd_ratio": kd,
            "stat_matches": r.stat_matches,
        })
    output.sort(key=lambda x: x["kd_ratio"], reverse=True)
    return output


@router.get("/team-stats")
def team_stats(db: Session = Depends(get_db)):
    """
    Per-team win/loss record and performance summary.
    """
    teams = db.query(Team).all()
    result = []
    for team in teams:
        wins = db.query(Match).filter(Match.winner_id == team.team_id).count()
        played = db.query(Match).filter(
            (Match.team1_id == team.team_id) | (Match.team2_id == team.team_id)
        ).count()
        losses = played - wins
        win_rate = round((wins / played * 100), 1) if played > 0 else 0.0
        result.append({
            "team_id": team.team_id,
            "team_name": team.team_name,
            "matches_played": played,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
        })
    result.sort(key=lambda x: x["win_rate"], reverse=True)
    return result


@router.get("/match-trends")
def match_trends(db: Session = Depends(get_db)):
    """Daily match count for the last 30 days."""
    from sqlalchemy import cast, Date
    from datetime import datetime, timedelta

    rows = (
        db.query(
            cast(Match.match_date, Date).label("day"),
            func.count(Match.match_id).label("count")
        )
        .group_by("day")
        .order_by("day")
        .all()
    )
    return [{"date": str(r.day), "match_count": r.count} for r in rows]


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    """High-level system overview for dashboard stat cards."""
    return {
        "total_players":     db.query(Player).count(),
        "total_matches":     db.query(Match).count(),
        "total_tournaments": db.query(Team).count(),
        "live_tournaments":  0,   # Extend with Tournament query if needed
        "total_stat_records": db.query(PlayerStat).count(),
    }
