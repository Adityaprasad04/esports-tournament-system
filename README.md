# NexusArena — Esports Tournament System
### Data Engineering Capstone Project

---

## Project Overview

NexusArena is a full-stack data-driven esports tournament management system built as a Data Engineering Capstone Project. It demonstrates end-to-end data engineering concepts:

```
Raw CSV/JSON → Extract → Transform → Load → PostgreSQL → FastAPI → React Dashboard
```

---

## Architecture

```
esports_backend/
├── main.py                  ← FastAPI application entry point
├── requirements.txt         ← Python dependencies
├── .env.example             ← Environment variable template
│
├── database/
│   └── db.py                ← SQLAlchemy engine, session factory, DB init + seeding
│
├── models/
│   └── models.py            ← ORM models (Team, Player, Tournament, Match, PlayerStat)
│                               + Pydantic schemas for validation
│
├── routes/
│   ├── players.py           ← GET /players, GET /players/{id}, POST /players
│   ├── teams.py             ← GET /teams, GET /teams/{id}
│   ├── tournaments.py       ← GET /tournaments, POST /tournaments
│   ├── matches.py           ← GET /matches, POST /matches
│   ├── leaderboard.py       ← GET /leaderboard?sort_by=win_rate|kd_ratio|total_matches
│   └── analytics.py         ← GET /analytics/player-performance
│                               GET /analytics/team-stats
│                               GET /analytics/match-trends
│                               GET /analytics/overview
│
├── etl/
│   ├── extract.py           ← Read from CSV/JSON; auto-generates synthetic data
│   ├── transform.py         ← Clean → validate → enrich → aggregate
│   ├── load.py              ← Upsert into PostgreSQL tables
│   └── pipeline.py          ← Full pipeline runner + cron scheduler
│
├── data/
│   └── raw_data.csv         ← Sample raw match log (28 rows)
│
└── utils/
    └── logger.py            ← Structured logging
```

---

## Database Schema

```sql
teams          (team_id PK, team_name, region)
players        (player_id PK, name, ign, team_id FK, role, total_matches, win_rate, kd_ratio)
tournaments    (tournament_id PK, name, game, status, prize_pool, max_teams, start_date)
matches        (match_id PK, tournament_id FK, team1_id FK, team2_id FK, winner_id FK, map_name, match_date, duration_minutes)
player_stats   (stat_id PK, player_id FK, match_id FK, kills, deaths, assists)
```

---

## Setup & Run

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 14+ (running locally or via Docker)

### 2. Create PostgreSQL Database
```sql
CREATE DATABASE nexusarena;
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env and set your DATABASE_URL
```

### 5. Run the API Server
```bash
python main.py
# Server starts at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

The database tables are created and seeded with sample data automatically on first startup.

---

## Running the ETL Pipeline

### Run once (uses data/raw_data.csv)
```bash
python -m etl.pipeline
```

### Run with a custom CSV file
```bash
python -m etl.pipeline --file path/to/your_data.csv
```

### Run on automated schedule (every 30 minutes)
```bash
python -m etl.pipeline --schedule --interval 1800
```

### ETL Output Example
```
2026-04-18 09:42:00 [INFO] [PIPELINE] ===== ETL Run RUN_20260418_094200 STARTED =====
2026-04-18 09:42:00 [INFO] [EXTRACT]  Reading CSV from: data/raw_data.csv
2026-04-18 09:42:00 [INFO] [EXTRACT]  Loaded 28 rows from CSV.
2026-04-18 09:42:01 [INFO] [TRANSFORM] Starting transform on 28 raw rows.
2026-04-18 09:42:01 [INFO] [TRANSFORM] Complete. 28 stat rows, 10 player summaries, 7 match summaries.
2026-04-18 09:42:01 [INFO] [LOAD]  player_stats: 28 rows inserted.
2026-04-18 09:42:01 [INFO] [LOAD]  players updated: 10 rows.
2026-04-18 09:42:01 [INFO] [PIPELINE] ===== ETL Run COMPLETE in 1.24s =====
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/players` | All players |
| GET | `/players/{id}` | Single player |
| GET | `/players/{id}/stats` | Aggregated match stats |
| POST | `/players` | Add new player |
| GET | `/teams` | All teams |
| GET | `/tournaments` | All tournaments (filter by ?status=live) |
| POST | `/tournaments` | Add tournament |
| GET | `/matches` | Match history |
| POST | `/matches` | Ingest new match |
| GET | `/leaderboard` | Ranked players |
| GET | `/analytics/player-performance` | Per-player KPIs |
| GET | `/analytics/team-stats` | Team win/loss records |
| GET | `/analytics/match-trends` | Daily match counts |
| GET | `/analytics/overview` | Dashboard summary stats |

Interactive API docs: **http://localhost:8000/docs**

---

## ETL Pipeline — Data Flow

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────┐
│  Data Source │ →  │    Extract   │ →  │  Transform   │ →  │    Load     │
│  raw_data.csv│    │  extract.py  │    │ transform.py │    │  load.py    │
│  JSON feeds  │    │              │    │              │    │             │
└─────────────┘    └──────────────┘    └──────────────┘    └─────────────┘
                         ↓                    ↓                    ↓
                   Read CSV/JSON        Clean nulls          Upsert into
                   Parse timestamps     Remove dupes         player_stats
                   Generate synthetic   Clip outliers        Update players
                   data if needed       Compute KD ratio     (win_rate, kd)
                                        Compute win_rate
                                        Aggregate stats
```

---

## Technologies Used

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI (Python) |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| ETL Processing | Pandas + NumPy |
| Data Validation | Pydantic v2 |
| Scheduling | Python scheduler (cron-compatible) |
| Frontend | React + Chart.js (see frontend/) |

---

## Sample Data Fields

The `raw_data.csv` follows this schema, simulating match server log output:

| Field | Type | Description |
|-------|------|-------------|
| match_id | STRING | Unique match identifier |
| player_id | STRING | Player foreign key |
| team_id | STRING | Team foreign key |
| kills | INTEGER | Kills in this match |
| deaths | INTEGER | Deaths in this match |
| assists | INTEGER | Assists in this match |
| win | INTEGER | 1 = win, 0 = loss |
| timestamp | DATETIME | Match start time (ISO 8601) |
| map | STRING | Map name |
| duration_minutes | INTEGER | Match duration |

---

*NexusArena — Data Engineering Capstone Project*
