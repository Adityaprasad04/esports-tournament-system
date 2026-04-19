"""
etl/airflow_dag.py — Apache Airflow DAG for NexusArena ETL
(Optional advanced automation — requires Apache Airflow installed)

Schedule: Every 30 minutes
DAG ID:   nexusarena_etl_pipeline

Tasks:
  1. extract_raw_data
  2. transform_data
  3. load_to_db
  4. refresh_analytics_cache

To deploy:
  Copy this file to your Airflow DAGs folder:
    $AIRFLOW_HOME/dags/nexusarena_etl_dag.py

  Then trigger via Airflow UI or:
    airflow dags trigger nexusarena_etl_pipeline
"""

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.empty import EmptyOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False
    print("Apache Airflow not installed. Use etl/pipeline.py --schedule instead.")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Task functions ────────────────────────────────────────────

def task_extract(**context):
    """Extract raw match data from CSV source."""
    from etl.extract import extract_from_csv
    df = extract_from_csv()
    # Push to XCom so downstream tasks can access
    context["ti"].xcom_push(key="raw_row_count", value=len(df))
    # Save to temp file for next task
    temp_path = "/tmp/nexusarena_raw.parquet"
    df.to_parquet(temp_path, index=False)
    context["ti"].xcom_push(key="temp_path", value=temp_path)
    print(f"[EXTRACT] {len(df)} rows extracted.")
    return len(df)


def task_transform(**context):
    """Transform extracted data."""
    import pandas as pd
    from etl.transform import transform

    temp_path = context["ti"].xcom_pull(key="temp_path", task_ids="extract_raw_data")
    df = pd.read_parquet(temp_path)
    transformed = transform(df)

    # Save transformed data
    stats_path = "/tmp/nexusarena_stats.parquet"
    summary_path = "/tmp/nexusarena_summary.parquet"
    transformed["player_stats"].to_parquet(stats_path, index=False)
    transformed["player_summary"].to_parquet(summary_path, index=False)

    context["ti"].xcom_push(key="stats_path",   value=stats_path)
    context["ti"].xcom_push(key="summary_path", value=summary_path)
    context["ti"].xcom_push(key="clean_count",  value=len(transformed["player_stats"]))

    print(f"[TRANSFORM] {len(transformed['player_stats'])} clean rows.")
    return len(transformed["player_stats"])


def task_load(**context):
    """Load transformed data into PostgreSQL."""
    import pandas as pd
    from etl.load import load
    from database.db import SessionLocal, init_db

    stats_path   = context["ti"].xcom_pull(key="stats_path",   task_ids="transform_data")
    summary_path = context["ti"].xcom_pull(key="summary_path", task_ids="transform_data")

    player_stats   = pd.read_parquet(stats_path)
    player_summary = pd.read_parquet(summary_path)

    init_db()
    db = SessionLocal()
    try:
        counts = load({"player_stats": player_stats, "player_summary": player_summary}, db)
    finally:
        db.close()

    print(f"[LOAD] Records loaded: {counts}")
    return counts


def task_notify(**context):
    """Log completion summary (extend to send Slack/email alerts)."""
    raw_count   = context["ti"].xcom_pull(key="raw_row_count", task_ids="extract_raw_data")
    clean_count = context["ti"].xcom_pull(key="clean_count",   task_ids="transform_data")
    discarded   = (raw_count or 0) - (clean_count or 0)

    summary = {
        "dag_run_id":    context["run_id"],
        "execution_date": str(context["execution_date"]),
        "raw_extracted":  raw_count,
        "clean_loaded":   clean_count,
        "discarded":      discarded,
    }
    print(f"[NOTIFY] ETL Complete: {summary}")
    # TODO: Add Slack webhook, email, or monitoring alert here
    return summary


# ── DAG Definition ────────────────────────────────────────────

if AIRFLOW_AVAILABLE:
    default_args = {
        "owner": "nexusarena",
        "depends_on_past": False,
        "start_date": datetime(2026, 4, 1),
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    }

    with DAG(
        dag_id="nexusarena_etl_pipeline",
        default_args=default_args,
        description="NexusArena — Daily match data ETL pipeline",
        schedule_interval="*/30 * * * *",   # Every 30 minutes
        catchup=False,
        tags=["esports", "etl", "data-engineering"],
    ) as dag:

        start = EmptyOperator(task_id="start")

        extract = PythonOperator(
            task_id="extract_raw_data",
            python_callable=task_extract,
        )

        transform = PythonOperator(
            task_id="transform_data",
            python_callable=task_transform,
        )

        load = PythonOperator(
            task_id="load_to_db",
            python_callable=task_load,
        )

        notify = PythonOperator(
            task_id="notify_completion",
            python_callable=task_notify,
        )

        end = EmptyOperator(task_id="end")

        # DAG dependency chain
        start >> extract >> transform >> load >> notify >> end
