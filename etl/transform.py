"""
etl/transform.py — Transform Phase
Cleans raw data and computes derived analytics metrics.

Transformations applied:
  1. Remove duplicate records
  2. Handle null/missing values
  3. Validate data types and ranges
  4. Calculate K/D ratio per player
  5. Calculate win rate per player
  6. Aggregate total matches per player
  7. Normalize into relational structure
"""

import pandas as pd
import numpy as np
from utils.logger import logger


def transform(df: pd.DataFrame) -> dict:
    """
    Main transform entry point.

    Returns:
        dict with keys:
            'player_stats'   — cleaned per-match stats (→ player_stats table)
            'player_summary' — aggregated player metrics (→ players table update)
            'match_summary'  — per-match aggregates
    """
    logger.info(f"[TRANSFORM] Starting transform on {len(df)} raw rows.")

    df = _clean(df)
    df = _validate(df)
    df = _enrich(df)

    player_stats   = _build_player_stats(df)
    player_summary = _build_player_summary(df)
    match_summary  = _build_match_summary(df)

    logger.info(f"[TRANSFORM] Complete. {len(player_stats)} stat rows, "
                f"{len(player_summary)} player summaries, "
                f"{len(match_summary)} match summaries.")

    return {
        "player_stats":   player_stats,
        "player_summary": player_summary,
        "match_summary":  match_summary,
    }


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Step 1 & 2: Remove duplicates and handle missing values."""
    initial = len(df)

    # Drop exact duplicates
    df = df.drop_duplicates()
    dup_removed = initial - len(df)
    if dup_removed > 0:
        logger.info(f"[TRANSFORM] Removed {dup_removed} duplicate rows.")

    # Required fields — drop rows where these are null
    required = ["match_id", "player_id", "team_id", "kills", "deaths"]
    before = len(df)
    df = df.dropna(subset=required)
    null_removed = before - len(df)
    if null_removed > 0:
        logger.warning(f"[TRANSFORM] Dropped {null_removed} rows with null required fields.")

    # Fill optional nulls with safe defaults
    df["assists"] = df["assists"].fillna(0)
    df["win"]     = df["win"].fillna(0)
    df["map"]     = df["map"].fillna("Unknown")
    df["duration_minutes"] = df["duration_minutes"].fillna(30)

    return df


def _validate(df: pd.DataFrame) -> pd.DataFrame:
    """Step 3: Enforce data type constraints and clip outliers."""

    # Cast numeric columns
    numeric_cols = ["kills", "deaths", "assists", "win", "duration_minutes"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Clip unrealistic values (e.g., kills can't be < 0 or > 100)
    df["kills"]   = df["kills"].clip(lower=0, upper=100)
    df["deaths"]  = df["deaths"].clip(lower=0, upper=100)
    df["assists"] = df["assists"].clip(lower=0, upper=50)
    df["win"]     = df["win"].clip(lower=0, upper=1).astype(int)
    df["duration_minutes"] = df["duration_minutes"].clip(lower=5, upper=120)

    # Ensure IDs are strings
    df["match_id"]  = df["match_id"].astype(str).str.strip()
    df["player_id"] = df["player_id"].astype(str).str.strip()
    df["team_id"]   = df["team_id"].astype(str).str.strip()

    invalid = df[df["player_id"].str.len() < 2]
    if not invalid.empty:
        logger.warning(f"[TRANSFORM] {len(invalid)} rows with invalid player_id dropped.")
        df = df[df["player_id"].str.len() >= 2]

    return df


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Step 4: Compute derived fields on the raw dataframe."""

    # K/D ratio per row — avoid div/0
    df["kd_ratio"] = np.where(
        df["deaths"] > 0,
        (df["kills"] / df["deaths"]).round(2),
        df["kills"].astype(float)   # deaths = 0 → kd = kills
    )

    # Timestamp parsing
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["match_date"] = df["timestamp"].dt.date
    else:
        df["match_date"] = pd.Timestamp.now().date()

    return df


def _build_player_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build normalized player_stats records.
    One row per (player_id, match_id).
    """
    cols = ["match_id", "player_id", "team_id", "kills", "deaths", "assists", "win", "kd_ratio"]
    available = [c for c in cols if c in df.columns]
    stats = df[available].copy()
    stats["stat_id"] = ["S" + str(i).zfill(6) for i in range(len(stats))]
    return stats.reset_index(drop=True)


def _build_player_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate per-player metrics:
      - total_matches, wins, win_rate, avg_kills, avg_deaths, avg_assists, kd_ratio
    """
    summary = df.groupby("player_id").agg(
        total_matches  = ("match_id", "nunique"),
        wins           = ("win", "sum"),
        avg_kills      = ("kills",   "mean"),
        avg_deaths     = ("deaths",  "mean"),
        avg_assists    = ("assists", "mean"),
    ).reset_index()

    summary["win_rate"] = (summary["wins"] / summary["total_matches"] * 100).round(2)
    summary["kd_ratio"] = (summary["avg_kills"] / summary["avg_deaths"].replace(0, 0.1)).round(2)
    summary["avg_kills"]   = summary["avg_kills"].round(1)
    summary["avg_deaths"]  = summary["avg_deaths"].round(1)
    summary["avg_assists"] = summary["avg_assists"].round(1)

    return summary


def _build_match_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-match totals for match analytics."""
    summary = df.groupby("match_id").agg(
        total_kills   = ("kills",   "sum"),
        total_deaths  = ("deaths",  "sum"),
        total_assists = ("assists", "sum"),
        players_count = ("player_id", "nunique"),
        avg_kd        = ("kd_ratio", "mean"),
    ).reset_index()
    summary["avg_kd"] = summary["avg_kd"].round(2)
    return summary
