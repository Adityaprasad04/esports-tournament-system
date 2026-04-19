"""
etl/load.py — Load Phase
Inserts transformed data into PostgreSQL.

Strategy: UPSERT (insert or update) to support repeated ETL runs.
"""

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from utils.logger import logger


def load(transformed: dict, db: Session) -> dict:
    """
    Load all transformed DataFrames into the database.

    Args:
        transformed: dict from transform.py with keys player_stats, player_summary, match_summary
        db: active SQLAlchemy session

    Returns:
        dict with row counts inserted/updated per table
    """
    counts = {}

    counts["player_stats"]   = _load_player_stats(transformed.get("player_stats",   pd.DataFrame()), db)
    counts["player_summary"] = _load_player_summary(transformed.get("player_summary", pd.DataFrame()), db)

    logger.info(f"[LOAD] Load complete. Counts: {counts}")
    return counts


def _load_player_stats(df: pd.DataFrame, db: Session) -> int:
    """Upsert rows into player_stats table."""
    from models.models import PlayerStat

    if df.empty:
        logger.warning("[LOAD] player_stats DataFrame is empty, skipping.")
        return 0

    inserted = 0
    for _, row in df.iterrows():
        # Check if record already exists
        existing = db.query(PlayerStat).filter(
            PlayerStat.player_id == str(row["player_id"]),
            PlayerStat.match_id  == str(row["match_id"]),
        ).first()

        if existing:
            # UPDATE existing record
            existing.kills   = int(row.get("kills", 0))
            existing.deaths  = int(row.get("deaths", 0))
            existing.assists = int(row.get("assists", 0))
        else:
            # INSERT new record
            stat = PlayerStat(
                stat_id   = str(row.get("stat_id", f"S{inserted}")),
                player_id = str(row["player_id"]),
                match_id  = str(row["match_id"]),
                kills     = int(row.get("kills", 0)),
                deaths    = int(row.get("deaths", 0)),
                assists   = int(row.get("assists", 0)),
            )
            db.add(stat)
            inserted += 1

    db.commit()
    logger.info(f"[LOAD] player_stats: {inserted} rows inserted.")
    return inserted


def _load_player_summary(df: pd.DataFrame, db: Session) -> int:
    """
    Update players table with aggregated ETL-computed metrics.
    win_rate and kd_ratio are computed by ETL — not manually entered.
    """
    from models.models import Player

    if df.empty:
        logger.warning("[LOAD] player_summary DataFrame is empty, skipping.")
        return 0

    updated = 0
    for _, row in df.iterrows():
        player = db.query(Player).filter(Player.player_id == str(row["player_id"])).first()
        if player:
            player.total_matches = int(row.get("total_matches", player.total_matches))
            player.win_rate      = float(row.get("win_rate",  player.win_rate))
            player.kd_ratio      = float(row.get("kd_ratio",  player.kd_ratio))
            updated += 1

    db.commit()
    logger.info(f"[LOAD] players updated: {updated} rows.")
    return updated
