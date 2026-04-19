"""
etl/extract.py — Extract Phase
Reads raw match data from CSV / JSON sources.

In a production system this could pull from:
  - S3 buckets
  - Game server APIs
  - Kafka streams
"""

import pandas as pd
import json
import os
from pathlib import Path
from utils.logger import logger

DATA_DIR = Path(__file__).parent.parent / "data"


def extract_from_csv(filepath: str = None) -> pd.DataFrame:
    """
    Read raw match log CSV.
    Expected columns: match_id, player_id, team_id, kills, deaths,
                      assists, win, timestamp, map, duration_minutes
    """
    path = filepath or (DATA_DIR / "raw_data.csv")
    if not os.path.exists(path):
        logger.warning(f"CSV not found at {path}. Generating synthetic data.")
        return _generate_synthetic_data()

    logger.info(f"[EXTRACT] Reading CSV from: {path}")
    df = pd.read_csv(path)
    logger.info(f"[EXTRACT] Loaded {len(df)} rows from CSV.")
    return df


def extract_from_json(filepath: str = None) -> pd.DataFrame:
    """Read raw match data from a JSON file (list of match objects)."""
    path = filepath or (DATA_DIR / "raw_data.json")
    if not os.path.exists(path):
        logger.warning(f"JSON not found at {path}.")
        return pd.DataFrame()

    logger.info(f"[EXTRACT] Reading JSON from: {path}")
    with open(path, "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    logger.info(f"[EXTRACT] Loaded {len(df)} records from JSON.")
    return df


def _generate_synthetic_data() -> pd.DataFrame:
    """
    Simulate daily match log ingestion.
    Creates realistic structured records for ETL development/testing.
    """
    import random
    from datetime import datetime, timedelta

    players = ["P001","P002","P003","P004","P005","P006","P007","P008","P009","P010"]
    teams   = {"P001":"NX","P002":"SR","P003":"VR","P004":"EV","P005":"NX",
               "P006":"SR","P007":"VR","P008":"EV","P009":"NX","P010":"SR"}
    maps    = ["Ascent","Bind","Haven","Inferno","Mirage","Storm Point","Overpass"]

    records = []
    base_date = datetime.now() - timedelta(days=30)

    for day in range(30):
        match_date = base_date + timedelta(days=day)
        num_matches = random.randint(3, 8)

        for m in range(num_matches):
            match_id = f"M{9000 + day*10 + m}"
            # Pick 2 teams for this match
            team_pair = random.sample(["NX","SR","VR","EV"], 2)
            winner = random.choice(team_pair)
            duration = random.randint(25, 65)

            for pid in players:
                kills   = random.randint(5, 30)
                deaths  = random.randint(3, 18)
                assists = random.randint(2, 15)
                win     = 1 if teams[pid] == winner else 0

                records.append({
                    "match_id": match_id,
                    "player_id": pid,
                    "team_id": teams[pid],
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                    "win": win,
                    "timestamp": match_date.isoformat(),
                    "map": random.choice(maps),
                    "duration_minutes": duration,
                })

    df = pd.DataFrame(records)
    logger.info(f"[EXTRACT] Generated {len(df)} synthetic records.")
    return df
