"""routes/teams.py"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from models.models import Team, TeamSchema

router = APIRouter()

@router.get("/", response_model=List[TeamSchema])
def get_teams(db: Session = Depends(get_db)):
    return db.query(Team).all()

@router.get("/{team_id}", response_model=TeamSchema)
def get_team(team_id: str, db: Session = Depends(get_db)):
    t = db.query(Team).filter(Team.team_id == team_id).first()
    if not t:
        raise HTTPException(404, f"Team {team_id} not found")
    return t
