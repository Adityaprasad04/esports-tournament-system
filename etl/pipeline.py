"""
etl/pipeline.py — Full ETL Pipeline Runner

Orchestrates: Extract → Transform → Load

Usage:
  python -m etl.pipeline               # run once
  python -m etl.pipeline --schedule    # run on cron (every 30 mins)
  python -m etl.pipeline --file data/custom.csv
"""

import argparse
import time
from datetime import datetime
from utils.logger import logger
from etl.extract import extract_from_csv, extract_from_json
from etl.transform import transform
from etl.load import load
from database.db import SessionLocal, init_db


def run_etl(filepath: str = None) -> dict:
    """
    Execute one full ETL run.
    Returns summary of records processed.
    """
    run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"[PIPELINE] ===== ETL Run {run_id} STARTED =====")
    start = time.time()

    # ── Step 1: EXTRACT ─────────────────────────────────────────
    logger.info("[PIPELINE] Phase 1: EXTRACT")
    df = extract_from_csv(filepath)
    if df.empty:
        logger.warning("[PIPELINE] No data extracted. Aborting.")
        return {"run_id": run_id, "status": "aborted", "reason": "empty extract"}

    raw_count = len(df)

    # ── Step 2: TRANSFORM ────────────────────────────────────────
    logger.info("[PIPELINE] Phase 2: TRANSFORM")
    transformed = transform(df)
    clean_count = len(transformed.get("player_stats", []))

    # ── Step 3: LOAD ─────────────────────────────────────────────
    logger.info("[PIPELINE] Phase 3: LOAD")
    db = SessionLocal()
    try:
        counts = load(transformed, db)
    finally:
        db.close()

    elapsed = round(time.time() - start, 2)
    logger.info(f"[PIPELINE] ===== ETL Run {run_id} COMPLETE in {elapsed}s =====")

    summary = {
        "run_id": run_id,
        "status": "success",
        "raw_rows_extracted": raw_count,
        "clean_rows_transformed": clean_count,
        "rows_discarded": raw_count - clean_count,
        "rows_loaded": counts,
        "duration_seconds": elapsed,
    }
    logger.info(f"[PIPELINE] Summary: {summary}")
    return summary


def run_scheduled(interval_seconds: int = 1800):
    """Run ETL pipeline on a schedule (default: every 30 minutes)."""
    logger.info(f"[PIPELINE] Scheduled mode: running every {interval_seconds}s")
    while True:
        try:
            run_etl()
        except Exception as e:
            logger.error(f"[PIPELINE] ETL run failed: {e}")
        logger.info(f"[PIPELINE] Sleeping for {interval_seconds}s...")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexusArena ETL Pipeline")
    parser.add_argument("--schedule", action="store_true", help="Run on schedule")
    parser.add_argument("--interval", type=int, default=1800, help="Schedule interval in seconds")
    parser.add_argument("--file", type=str, default=None, help="Path to raw CSV file")
    args = parser.parse_args()

    init_db()

    if args.schedule:
        run_scheduled(args.interval)
    else:
        result = run_etl(args.file)
        print(f"\nETL Result: {result}")
