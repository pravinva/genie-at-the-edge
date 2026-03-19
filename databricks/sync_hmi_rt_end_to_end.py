#!/usr/bin/env python3
"""
End-to-end HMI_RT sync:
1) Verifies HMI_RT events are landing in Delta via Zerobus.
2) Runs lightweight anomaly scoring over latest readings.
3) Writes sensor history + recommendations into Lakebase historian DB.

Uses Databricks CLI profile: DEFAULT
"""

import json
import math
import os
import subprocess
import time
from datetime import datetime, timezone

from databricks.sdk import WorkspaceClient


WORKSPACE_HOST = "https://e2-demo-field-eng.cloud.databricks.com"
WAREHOUSE_ID = "4b9b953939869799"

PG_HOST = "ep-raspy-bread-d1h1jnc5.database.us-west-2.cloud.databricks.com"
PG_DB = "historian"
PG_USER = "pravin.varma@databricks.com"


def wait_statement(w: WorkspaceClient, statement_id: str, timeout_sec: int = 90):
    start = time.time()
    while time.time() - start < timeout_sec:
        st = w.statement_execution.get_statement(statement_id)
        state = st.status.state.value
        if state == "SUCCEEDED":
            return st
        if state in ("FAILED", "CANCELED", "CLOSED"):
            msg = st.status.error.message if st.status and st.status.error else state
            raise RuntimeError(msg)
        time.sleep(1)
    raise TimeoutError(f"Statement {statement_id} timed out after {timeout_sec}s")


def run_sql(w: WorkspaceClient, sql: str):
    res = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql,
        wait_timeout="0s",
    )
    st = wait_statement(w, res.statement_id)
    return st.result.data_array if st.result and st.result.data_array else []


def quote_sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main():
    print("Connecting to Databricks (DEFAULT profile)...")
    w = WorkspaceClient(profile="DEFAULT")

    print("Checking fresh HMI_RT events in Delta...")
    recent_count_rows = run_sql(
        w,
        """
        SELECT COUNT(*)
        FROM field_engineering.ignition_streaming.sensor_events
        WHERE tag_path LIKE '%HMI_RT/%'
          AND event_time > CURRENT_TIMESTAMP() - INTERVAL 10 MINUTES
        """,
    )
    recent_count = int(recent_count_rows[0][0]) if recent_count_rows else 0
    print(f"Recent HMI_RT events (10 min): {recent_count}")
    if recent_count == 0:
        raise RuntimeError("No recent HMI_RT events found in Delta. Zerobus ingestion is not active for HMI_RT.")

    print("Reading latest HMI_RT history for chart backfill...")
    history_rows = run_sql(
        w,
        """
        WITH parsed AS (
          SELECT
            regexp_extract(tag_path, 'HMI_RT/([^/]+)/', 1) AS equipment_id,
            lower(regexp_extract(tag_path, 'HMI_RT/[^/]+/([^/]+)$', 1)) AS sensor_type,
            CAST(numeric_value AS DOUBLE) AS sensor_value,
            CAST(event_time AS TIMESTAMP) AS event_time
          FROM field_engineering.ignition_streaming.sensor_events
          WHERE tag_path LIKE '%HMI_RT/%'
            AND numeric_value IS NOT NULL
            AND event_time > CURRENT_TIMESTAMP() - INTERVAL 2 DAYS
        ),
        ranked AS (
          SELECT
            equipment_id,
            sensor_type,
            sensor_value,
            event_time,
            row_number() OVER (
              PARTITION BY equipment_id, sensor_type
              ORDER BY event_time DESC
            ) AS rn
          FROM parsed
          WHERE equipment_id <> ''
            AND sensor_type IN ('temperature', 'flow_rate')
        )
        SELECT equipment_id, sensor_type, sensor_value, event_time
        FROM ranked
        WHERE rn <= 120
        ORDER BY equipment_id, sensor_type, event_time
        """,
    )
    print(f"History rows pulled from Delta: {len(history_rows)}")

    print("Reading latest points per equipment for anomaly scoring...")
    latest_rows = run_sql(
        w,
        """
        WITH parsed AS (
          SELECT
            regexp_extract(tag_path, 'HMI_RT/([^/]+)/', 1) AS equipment_id,
            lower(regexp_extract(tag_path, 'HMI_RT/[^/]+/([^/]+)$', 1)) AS sensor_type,
            CAST(numeric_value AS DOUBLE) AS sensor_value,
            CAST(event_time AS TIMESTAMP) AS event_time
          FROM field_engineering.ignition_streaming.sensor_events
          WHERE tag_path LIKE '%HMI_RT/%'
            AND numeric_value IS NOT NULL
            AND event_time > CURRENT_TIMESTAMP() - INTERVAL 2 HOURS
        ),
        ranked AS (
          SELECT
            equipment_id,
            sensor_type,
            sensor_value,
            event_time,
            row_number() OVER (
              PARTITION BY equipment_id, sensor_type
              ORDER BY event_time DESC
            ) AS rn
          FROM parsed
          WHERE equipment_id <> ''
            AND sensor_type IN ('temperature', 'flow_rate')
        )
        SELECT equipment_id, sensor_type, sensor_value, event_time
        FROM ranked
        WHERE rn = 1
        ORDER BY equipment_id, sensor_type
        """,
    )
    print(f"Latest sensor points: {len(latest_rows)}")

    # Build per-equipment feature map
    by_eq = {}
    for eq, sensor, value, evt in latest_rows:
        by_eq.setdefault(eq, {})[sensor] = (float(value), str(evt))

    # Heuristic anomaly scoring (kept transparent for operator trust)
    recommendations = []
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for eq, sensors in by_eq.items():
        if "temperature" not in sensors or "flow_rate" not in sensors:
            continue
        temp = sensors["temperature"][0]
        flow = sensors["flow_rate"][0]

        temp_score = max(0.0, min(1.0, (temp - 75.0) / 35.0))
        flow_score = max(0.0, min(1.0, (110.0 - flow) / 50.0))
        anomaly = round(max(temp_score, flow_score), 3)
        confidence = round(min(0.99, 0.6 + anomaly * 0.35), 2)

        if anomaly >= 0.85:
            severity = "critical"
            ttf = 30
            rec = "Immediate intervention: reduce load and inspect cooling/flow path."
        elif anomaly >= 0.65:
            severity = "high"
            ttf = 120
            rec = "High risk: schedule urgent inspection and validate pump/heat exchange."
        elif anomaly >= 0.45:
            severity = "medium"
            ttf = 360
            rec = "Monitor closely and plan maintenance in next window."
        else:
            severity = "low"
            ttf = 1440
            rec = "Within expected range. Continue monitoring."

        recommendations.append(
            {
                "equipment_id": eq,
                "severity": severity,
                "anomaly_score": anomaly,
                "confidence": confidence,
                "recommendation_text": f"{rec} (temp={temp:.1f}C, flow={flow:.1f} LPM)",
                "estimated_ttf": ttf,
                "scored_at": now_utc,
            }
        )

    if not recommendations:
        raise RuntimeError("No complete equipment rows found for recommendation generation.")
    print(f"Recommendations generated: {len(recommendations)}")

    # Fetch Databricks token to use as Lakebase password
    token_json = subprocess.check_output(
        ["databricks", "auth", "token", "--profile", "DEFAULT", "--host", WORKSPACE_HOST],
        text=True,
    )
    token = json.loads(token_json)["access_token"]

    # Build SQL batch for Lakebase writes.
    history_values = []
    for eq, sensor, val, evt in history_rows:
        units = "C" if sensor == "temperature" else "LPM"
        quality = "good"
        history_values.append(
            "("
            + ",".join(
                [
                    quote_sql(str(eq)),
                    quote_sql(str(sensor)),
                    str(float(val)),
                    quote_sql(units),
                    quote_sql(quality),
                    f"CAST({quote_sql(str(evt))} AS TIMESTAMP)",
                ]
            )
            + ")"
        )

    rec_values = []
    for r in recommendations:
        rec_values.append(
            "("
            + ",".join(
                [
                    quote_sql(r["equipment_id"]),
                    quote_sql(r["severity"]),
                    str(r["anomaly_score"]),
                    str(r["confidence"]),
                    quote_sql(r["recommendation_text"]),
                    str(int(r["estimated_ttf"])),
                    f"CAST({quote_sql(r['scored_at'])} AS TIMESTAMP)",
                ]
            )
            + ")"
        )

    sql_parts = [
        "BEGIN;",
        "DELETE FROM public.sensor_data WHERE timestamp < NOW() - INTERVAL '7 days';",
    ]

    if history_values:
        sql_parts.append(
            "INSERT INTO public.sensor_data "
            "(equipment_id, sensor_type, sensor_value, units, quality, timestamp) VALUES "
            + ",\n".join(history_values)
            + ";"
        )

    sql_parts.append(
        "INSERT INTO public.ml_recommendations "
        "(equipment_id, severity, anomaly_score, confidence, recommendation_text, estimated_ttf, scored_at) VALUES "
        + ",\n".join(rec_values)
        + ";"
    )
    sql_parts.append("COMMIT;")
    sql_batch = "\n".join(sql_parts)

    print("Writing sensor_data + ml_recommendations to Lakebase historian...")
    proc = subprocess.run(
        [
            "psql",
            "-h",
            PG_HOST,
            "-U",
            PG_USER,
            "-d",
            PG_DB,
            "-v",
            "ON_ERROR_STOP=1",
        ],
        input=sql_batch,
        text=True,
        capture_output=True,
        env={**os.environ, "PGPASSWORD": token},
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "psql write failed")

    print("Lakebase write completed.")
    print("Verifying latest rows...")
    verify = subprocess.run(
        [
            "psql",
            "-h",
            PG_HOST,
            "-U",
            PG_USER,
            "-d",
            PG_DB,
            "-c",
            """
            SELECT equipment_id, severity, confidence, scored_at
            FROM public.ml_recommendations
            ORDER BY scored_at DESC
            LIMIT 10;
            """,
        ],
        text=True,
        capture_output=True,
        env={**os.environ, "PGPASSWORD": token},
    )
    print(verify.stdout)

    print("DONE: Zerobus -> Delta -> anomaly scoring -> Lakebase historian sync complete.")
    print("Perspective should refresh on next poll / row selection.")


if __name__ == "__main__":
    main()
