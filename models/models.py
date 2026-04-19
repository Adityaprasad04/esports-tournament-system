"""
models/models.py — SQLAlchemy ORM models and Pydantic schemas

Tables:
  - teams
  - players
  - tournaments
  - matches
  - player_stats
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from database.db import Base


# ─────────────────────────────────────────────────────────────
# ORM MODELS
# ─────────────────────────────────────────────────────────────

class Team(Base):
    __tablename__ = "teams"

    team_id   = Column(String(10), primary_key=True, index=True)
    team_name = Column(String(100), nullable=False)
    region    = Column(String(100))

    players  = relationship("Player",  back_populates="team")
    matches1 = relationship("Match",   foreign_keys="Match.team1_id", back_populates="team1")
    matches2 = relationship("Match",   foreign_keys="Match.team2_id", back_populates="team2")


class Player(Base):
    __tablename__ = "players"

    player_id     = Column(String(10), primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    ign           = Column(String(50),  nullable=False, unique=True)  # In-Game Name
    team_id       = Column(String(10),  ForeignKey("teams.team_id"))
    role          = Column(String(50))
    total_matches = Column(Integer, default=0)
    win_rate      = Column(Float, default=0.0)   # Computed by ETL
    kd_ratio      = Column(Float, default=0.0)   # Computed by ETL

    team  = relationship("Team",       back_populates="players")
    stats = relationship("PlayerStat", back_populates="player")


class Tournament(Base):
    __tablename__ = "tournaments"

    tournament_id = Column(String(10), primary_key=True, index=True)
    name          = Column(String(200), nullable=False)
    game          = Column(String(100))
    status        = Column(String(20), default="upcoming")  # live/upcoming/completed
    prize_pool    = Column(Integer, default=0)
    max_teams     = Column(Integer, default=16)
    start_date    = Column(Date)

    matches = relationship("Match", back_populates="tournament")


class Match(Base):
    __tablename__ = "matches"

    match_id         = Column(String(10), primary_key=True, index=True)
    tournament_id    = Column(String(10), ForeignKey("tournaments.tournament_id"))
    team1_id         = Column(String(10), ForeignKey("teams.team_id"))
    team2_id         = Column(String(10), ForeignKey("teams.team_id"))
    winner_id        = Column(String(10), ForeignKey("teams.team_id"), nullable=True)
    map_name         = Column(String(100))
    match_date       = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer)

    tournament = relationship("Tournament", back_populates="matches")
    team1      = relationship("Team", foreign_keys=[team1_id], back_populates="matches1")
    team2      = relationship("Team", foreign_keys=[team2_id], back_populates="matches2")
    stats      = relationship("PlayerStat", back_populates="match")


class PlayerStat(Base):
    __tablename__ = "player_stats"

    stat_id   = Column(String(10), primary_key=True, index=True)
    player_id = Column(String(10), ForeignKey("players.player_id"))
    match_id  = Column(String(10), ForeignKey("matches.match_id"))
    kills     = Column(Integer, default=0)
    deaths    = Column(Integer, default=0)
    assists   = Column(Integer, default=0)

    player = relationship("Player", back_populates="stats")
    match  = relationship("Match",  back_populates="stats")


# ─────────────────────────────────────────────────────────────
# PYDANTIC SCHEMAS (request/response validation)
# ─────────────────────────────────────────────────────────────

class TeamSchema(BaseModel):
    team_id: str
    team_name: str
    region: Optional[str] = None
    class Config: from_attributes = True

class PlayerSchema(BaseModel):
    player_id: str
    name: str
    ign: str
    team_id: Optional[str] = None
    role: Optional[str] = None
    total_matches: int = 0
    win_rate: float = 0.0
    kd_ratio: float = 0.0
    class Config: from_attributes = True

class PlayerCreateSchema(BaseModel):
    name: str = Field(..., min_length=2)
    ign:  str = Field(..., min_length=2)
    team_id: str
    role: Optional[str] = "Duelist"

class TournamentSchema(BaseModel):
    tournament_id: str
    name: str
    game: Optional[str] = None
    status: str = "upcoming"
    prize_pool: int = 0
    max_teams: int = 16
    start_date: Optional[date] = None
    class Config: from_attributes = True

class MatchSchema(BaseModel):
    match_id: str
    tournament_id: Optional[str] = None
    team1_id: str
    team2_id: str
    winner_id: Optional[str] = None
    map_name: Optional[str] = None
    match_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    class Config: from_attributes = True

class MatchCreateSchema(BaseModel):
    tournament_id: Optional[str] = None
    team1_id: str
    team2_id: str
    winner_id: Optional[str] = None
    map_name: Optional[str] = None
    duration_minutes: Optional[int] = 30

class PlayerStatSchema(BaseModel):
    stat_id: str
    player_id: str
    match_id: str
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    class Config: from_attributes = True
