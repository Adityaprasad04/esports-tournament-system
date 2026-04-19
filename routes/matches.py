"""routes/matches.py"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from database.db import get_db
from models.models import Match, MatchSchema, MatchCreateSchema

router = APIRouter()

@router.get("/", response_model=List[MatchSchema])
def get_matches(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Match).order_by(Match.match_date.desc()).offset(skip).limit(limit).all()

@router.get("/{match_id}", response_model=MatchSchema)
def get_match(match_id: str, db: Session = Depends(get_db)):
    m = db.query(Match).filter(Match.match_id == match_id).first()
    if not m:
        raise HTTPException(404, f"Match {match_id} not found")
    return m

@router.post("/", response_model=MatchSchema, status_code=201)
def add_match(data: MatchCreateSchema, db: Session = Depends(get_db)):
    """Insert a new match record. ETL will process player_stats separately."""
    if data.team1_id == data.team2_id:
        raise HTTPException(400, "team1_id and team2_id must differ")
    match_id = "M" + str(uuid.uuid4())[:6].upper()
    match = Match(
        match_id=match_id,
        tournament_id=data.tournament_id,
        team1_id=data.team1_id,
        team2_id=data.team2_id,
        winner_id=data.winner_id,
        map_name=data.map_name,
        match_date=datetime.utcnow(),
        duration_minutes=data.duration_minutes,
    )
    db.add(match); db.commit(); db.refresh(match)
    return match
