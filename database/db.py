"""
database/db.py — PostgreSQL connection using SQLAlchemy
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.logger import logger

# Read from environment variable; fallback for local dev
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:2004@localhost:5432/nexusarena"
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist, then seed sample data."""
    from models.models import Player, Team, Tournament, Match, PlayerStat
    Base.metadata.create_all(bind=engine)
    logger.info("All tables created (if not existing).")

    # Seed only if empty
    db = SessionLocal()
    try:
        if db.query(Team).count() == 0:
            _seed_data(db)
            logger.info("Sample data seeded into database.")
    finally:
        db.close()


def _seed_data(db):
    """Insert sample teams, players, tournaments, matches, stats."""
    from models.models import Player, Team, Tournament, Match, PlayerStat
    from datetime import datetime, date

    # Teams
    teams = [
        Team(team_id="NX", team_name="NexForce", region="South Asia"),
        Team(team_id="SR", team_name="Spectral",  region="South Asia"),
        Team(team_id="VR", team_name="Vortex",    region="East Asia"),
        Team(team_id="EV", team_name="Evolve",    region="Southeast Asia"),
    ]
    db.add_all(teams)

    # Players
    players = [
        Player(player_id="P001", name="Arjun Sharma",  ign="PhantomX",    team_id="NX", role="Duelist",    total_matches=142, win_rate=69.0, kd_ratio=2.14),
        Player(player_id="P002", name="Priya Nair",    ign="ShadowByte",  team_id="SR", role="Controller", total_matches=128, win_rate=63.3, kd_ratio=1.87),
        Player(player_id="P003", name="Rahul Verma",   ign="VoidCaster",  team_id="VR", role="Initiator",  total_matches=156, win_rate=60.3, kd_ratio=1.73),
        Player(player_id="P004", name="Sneha Reddy",   ign="NeonPulse",   team_id="EV", role="Sentinel",   total_matches=118, win_rate=61.0, kd_ratio=1.64),
        Player(player_id="P005", name="Vikram Singh",  ign="IronGhost",   team_id="NX", role="IGL",        total_matches=163, win_rate=64.4, kd_ratio=1.52),
        Player(player_id="P006", name="Ananya Patel",  ign="CipherX",     team_id="SR", role="Duelist",    total_matches=101, win_rate=57.4, kd_ratio=1.91),
        Player(player_id="P007", name="Dev Mehta",     ign="QuantumFrag", team_id="VR", role="Duelist",    total_matches=88,  win_rate=53.4, kd_ratio=2.03),
        Player(player_id="P008", name="Kavita Joshi",  ign="LunarAce",    team_id="EV", role="Controller", total_matches=134, win_rate=56.7, kd_ratio=1.45),
        Player(player_id="P009", name="Aakash Gupta",  ign="StormRift",   team_id="NX", role="Initiator",  total_matches=97,  win_rate=56.7, kd_ratio=1.38),
        Player(player_id="P010", name="Riya Kapoor",   ign="HexBlast",    team_id="SR", role="Sentinel",   total_matches=115, win_rate=57.4, kd_ratio=1.29),
    ]
    db.add_all(players)

    # Tournaments
    tournaments = [
        Tournament(tournament_id="T001", name="NexusArena World Cup",   game="Valorant", status="live",      prize_pool=25000, max_teams=16, start_date=date(2026,4,15)),
        Tournament(tournament_id="T002", name="Cyber Storm Open",        game="CS2",       status="live",      prize_pool=15000, max_teams=8,  start_date=date(2026,4,16)),
        Tournament(tournament_id="T003", name="Apex Predators League",   game="Apex",      status="live",      prize_pool=10000, max_teams=20, start_date=date(2026,4,17)),
        Tournament(tournament_id="T004", name="Shadow Protocol Cup",     game="Valorant", status="upcoming",  prize_pool=20000, max_teams=16, start_date=date(2026,4,25)),
        Tournament(tournament_id="T005", name="Winter Iron Series",      game="CS2",       status="completed", prize_pool=8000,  max_teams=8,  start_date=date(2026,3,10)),
        Tournament(tournament_id="T006", name="Neon Recon Open",         game="Valorant", status="upcoming",  prize_pool=12000, max_teams=12, start_date=date(2026,5,2)),
    ]
    db.add_all(tournaments)

    # Matches
    matches = [
        Match(match_id="M0892", tournament_id="T001", team1_id="NX", team2_id="SR", winner_id="NX", map_name="Ascent",   match_date=datetime(2026,4,17,14,0), duration_minutes=42),
        Match(match_id="M0891", tournament_id="T002", team1_id="VR", team2_id="EV", winner_id="VR", map_name="Inferno",  match_date=datetime(2026,4,17,12,0), duration_minutes=38),
        Match(match_id="M0890", tournament_id="T001", team1_id="NX", team2_id="VR", winner_id="NX", map_name="Haven",    match_date=datetime(2026,4,16,16,0), duration_minutes=35),
        Match(match_id="M0889", tournament_id="T003", team1_id="SR", team2_id="EV", winner_id="SR", map_name="Storm Pt", match_date=datetime(2026,4,15,18,0), duration_minutes=55),
        Match(match_id="M0888", tournament_id="T001", team1_id="EV", team2_id="SR", winner_id="SR", map_name="Bind",     match_date=datetime(2026,4,15,10,0), duration_minutes=48),
    ]
    db.add_all(matches)

    # Player Stats per match
    stats = [
        PlayerStat(stat_id="S001", player_id="P001", match_id="M0892", kills=24, deaths=10, assists=7),
        PlayerStat(stat_id="S002", player_id="P002", match_id="M0892", kills=18, deaths=12, assists=14),
        PlayerStat(stat_id="S003", player_id="P003", match_id="M0891", kills=19, deaths=11, assists=12),
        PlayerStat(stat_id="S004", player_id="P004", match_id="M0891", kills=14, deaths=13, assists=9),
        PlayerStat(stat_id="S005", player_id="P001", match_id="M0890", kills=22, deaths=8,  assists=6),
        PlayerStat(stat_id="S006", player_id="P005", match_id="M0890", kills=15, deaths=9,  assists=13),
        PlayerStat(stat_id="S007", player_id="P002", match_id="M0889", kills=20, deaths=10, assists=10),
        PlayerStat(stat_id="S008", player_id="P006", match_id="M0889", kills=17, deaths=11, assists=8),
    ]
    db.add_all(stats)

    db.commit()
