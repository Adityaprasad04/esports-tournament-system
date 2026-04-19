"""routes/tournaments.py"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database.db import get_db
from models.models import Tournament, TournamentSchema

router = APIRouter()

@router.get("/", response_model=List[TournamentSchema])
def get_tournaments(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Tournament)
    if status:
        q = q.filter(Tournament.status == status)
    return q.all()

@router.get("/{tournament_id}", response_model=TournamentSchema)
def get_tournament(tournament_id: str, db: Session = Depends(get_db)):
    t = db.query(Tournament).filter(Tournament.tournament_id == tournament_id).first()
    if not t:
        raise HTTPException(404, f"Tournament {tournament_id} not found")
    return t

@router.post("/", response_model=TournamentSchema, status_code=201)
def add_tournament(data: dict, db: Session = Depends(get_db)):
    import uuid
    tid = "T" + str(uuid.uuid4())[:6].upper()
    t = Tournament(tournament_id=tid, **data)
    db.add(t); db.commit(); db.refresh(t)
    return t
