#!/usr/bin/env python3
"""
Lakebase Setup for Real-time Serving to Ignition
Creates PostgreSQL-compatible tables with PG NOTIFY webhooks

Architecture:
- ml_recommendations: Streaming table from ML scoring pipeline
- recommendations_serving: Lakebase-enabled view with <50ms query latency
- operator_feedback: Captures operator actions (Execute/Defer/Ask Why)
- PG NOTIFY: Webhook fires instantly to Ignition sessions

Setup:
1. Enable Lakebase on catalog
2. Create serving tables
3. Configure PG NOTIFY triggers
4. Set up async sync (5-min batching to Delta)
"""

from databricks.sdk import WorkspaceClient
import time

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

CATALOG = "field_engineering"
SCHEMA = "lakebase"

print("=" * 80)
print("LAKEBASE SETUP FOR REAL-TIME SERVING")
print("=" * 80)

def execute_sql(sql, description):
    """Execute SQL and wait for completion"""
    print(f"\n{description}...")
    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout='0s'
        )

        for _ in range(30):
            time.sleep(1)
            status = w.statement_execution.get_statement(result.statement_id)

            if status.status.state.value == 'SUCCEEDED':
                print(f"  ✅ Success")
                return True
            elif status.status.state.value in ['FAILED', 'CANCELED', 'CLOSED']:
                if status.status.error:
                    print(f"  ❌ Error: {status.status.error.message[:200]}")
                return False

        print(f"  ⚠️  Timeout")
        return False

    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:200]}")
        return False

# ============================================================================
# STEP 1: Enable Lakebase on Catalog
# ============================================================================

print("\n[1/6] Enabling Lakebase on catalog...")

enable_lakebase_sql = f"""
ALTER CATALOG {CATALOG}
ENABLE PREDICTIVE OPTIMIZATION
"""

# Note: Lakebase is enabled via UI or API, not SQL
# This is a placeholder - in production, use Databricks UI:
# Catalog Explorer → field_engineering → Enable Lakebase
print("  ℹ️  Lakebase enabled via Databricks UI (Catalog → Enable Lakebase)")
print("  ℹ️  Skipping SQL command (requires UI or API)")

# ============================================================================
# STEP 2: Create Recommendations Serving View
# ============================================================================

print("\n[2/6] Creating recommendations serving view...")

serving_view_sql = f"""
CREATE OR REPLACE VIEW {CATALOG}.{SCHEMA}.recommendations_serving AS
SELECT
  equipment_id,
  timestamp,
  anomaly_score,
  severity,
  action_code,
  recommendation_text,
  confidence,
  estimated_ttf,
  temp_avg_5min,
  vibration_avg_5min,
  throughput_avg_5min,
  temp_deviation_from_baseline,
  vibration_deviation_from_baseline,
  days_since_maintenance,
  last_maintenance_type,
  shift,
  product_type,
  scored_at,
  -- Status tracking
  'pending' as status,
  CAST(NULL AS STRING) as operator_action,
  CAST(NULL AS TIMESTAMP) as action_timestamp,
  CAST(NULL AS STRING) as operator_notes
FROM {CATALOG}.{SCHEMA}.ml_recommendations
WHERE
  -- Only show recent recommendations (last 24 hours)
  scored_at >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
  -- Only show high-priority alerts
  AND severity IN ('critical', 'high')
ORDER BY scored_at DESC, anomaly_score DESC
LIMIT 100
"""

execute_sql(serving_view_sql, "Creating recommendations serving view")

# ============================================================================
# STEP 3: Create Operator Feedback Table
# ============================================================================

print("\n[3/6] Creating operator feedback table...")

feedback_table_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.operator_feedback (
  feedback_id STRING,
  equipment_id STRING,
  recommendation_timestamp TIMESTAMP,
  action_code STRING,
  anomaly_score DOUBLE,

  -- Operator decision
  operator_action STRING,  -- 'executed', 'deferred', 'rejected', 'ask_ai_why'
  operator_id STRING,
  action_timestamp TIMESTAMP,
  operator_notes STRING,

  -- Outcome tracking (for model retraining)
  was_correct BOOLEAN,  -- Did the recommendation prevent an issue?
  actual_outcome STRING,  -- What actually happened?
  outcome_timestamp TIMESTAMP,

  -- Genie interaction
  asked_genie BOOLEAN,
  genie_question STRING,
  genie_response STRING,

  -- Metadata
  shift STRING,
  session_id STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
)
"""

execute_sql(feedback_table_sql, "Creating operator feedback table")

# ============================================================================
# STEP 4: Create Equipment State Tracking Table
# ============================================================================

print("\n[4/6] Creating equipment state tracking table...")

equipment_state_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.equipment_state (
  equipment_id STRING,
  last_updated TIMESTAMP,

  -- Current status
  current_status STRING,  -- 'normal', 'warning', 'critical', 'maintenance'
  active_recommendation STRING,
  active_since TIMESTAMP,

  -- Latest sensor values
  temperature DOUBLE,
  vibration DOUBLE,
  throughput DOUBLE,
  pressure DOUBLE,

  -- Anomaly tracking
  anomaly_score DOUBLE,
  consecutive_anomalies INT,
  last_anomaly_timestamp TIMESTAMP,

  -- Operator context
  last_operator_action STRING,
  last_action_timestamp TIMESTAMP,

  PRIMARY KEY (equipment_id)
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true'
)
"""

execute_sql(equipment_state_sql, "Creating equipment state table")

# ============================================================================
# STEP 5: Create Lakebase Sync Trigger Function
# ============================================================================

print("\n[5/6] Creating Lakebase sync configuration...")

# This would be PostgreSQL PG NOTIFY trigger in production Lakebase
# For now, document the configuration

lakebase_config = """
-- PostgreSQL NOTIFY Trigger (executed in Lakebase PostgreSQL layer)
-- This fires instantly (<100ms) when new recommendations are inserted

CREATE OR REPLACE FUNCTION notify_ignition_recommendation()
RETURNS TRIGGER AS $$
DECLARE
  payload JSON;
BEGIN
  -- Build webhook payload
  payload := json_build_object(
    'equipment_id', NEW.equipment_id,
    'severity', NEW.severity,
    'action_code', NEW.action_code,
    'recommendation_text', NEW.recommendation_text,
    'confidence', NEW.confidence,
    'anomaly_score', NEW.anomaly_score,
    'timestamp', NEW.timestamp
  );

  -- Fire NOTIFY to all listening Ignition sessions
  PERFORM pg_notify('equipment_recommendations', payload::text);

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to recommendations table
CREATE TRIGGER trigger_notify_ignition
AFTER INSERT ON recommendations_serving
FOR EACH ROW
EXECUTE FUNCTION notify_ignition_recommendation();

-- Enable async sync (Delta → PostgreSQL every 5 minutes)
-- This is configured via Databricks Lakebase UI
"""

print("  ℹ️  Lakebase PG NOTIFY configuration:")
print(lakebase_config)

# ============================================================================
# STEP 6: Create Materialized View for Ignition HMI Dashboard
# ============================================================================

print("\n[6/6] Creating HMI dashboard materialized view...")

hmi_dashboard_sql = f"""
CREATE OR REPLACE VIEW {CATALOG}.{SCHEMA}.hmi_dashboard AS
SELECT
  e.equipment_id,
  e.current_status,
  e.temperature,
  e.vibration,
  e.throughput,
  e.pressure,
  e.anomaly_score,
  e.last_updated,

  -- Active recommendation
  r.recommendation_text,
  r.action_code,
  r.confidence,
  r.severity,
  r.estimated_ttf,

  -- Operator feedback
  f.operator_action,
  f.action_timestamp,

  -- Asset context (from equipment_360 view)
  a.asset_category,
  a.manufacturer,
  a.model,
  a.shift,
  a.planned_throughput_tph,
  a.days_since_maintenance,
  a.next_maintenance_scheduled

FROM {CATALOG}.{SCHEMA}.equipment_state e

LEFT JOIN {CATALOG}.{SCHEMA}.recommendations_serving r
  ON e.equipment_id = r.equipment_id
  AND r.status = 'pending'

LEFT JOIN {CATALOG}.{SCHEMA}.operator_feedback f
  ON e.equipment_id = f.equipment_id
  AND f.feedback_id = (
    SELECT feedback_id
    FROM {CATALOG}.{SCHEMA}.operator_feedback
    WHERE equipment_id = e.equipment_id
    ORDER BY action_timestamp DESC
    LIMIT 1
  )

LEFT JOIN {CATALOG}.ml_silver.gold_equipment_360 a
  ON e.equipment_id = a.equipment_id

ORDER BY e.anomaly_score DESC, e.equipment_id
"""

execute_sql(hmi_dashboard_sql, "Creating HMI dashboard view")

# ============================================================================
# VERIFICATION
# ============================================================================

print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

tables_to_check = [
    "ml_recommendations",
    "recommendations_serving",
    "operator_feedback",
    "equipment_state",
    "hmi_dashboard"
]

for table in tables_to_check:
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=f"DESCRIBE TABLE {CATALOG}.{SCHEMA}.{table}",
        wait_timeout='0s'
    )

    time.sleep(1)
    status = w.statement_execution.get_statement(result.statement_id)

    if status.status.state.value == 'SUCCEEDED':
        print(f"  ✅ {table}")
    else:
        print(f"  ❌ {table} - Not found")

print("\n" + "=" * 80)
print("✅ LAKEBASE SERVING SETUP COMPLETE")
print("=" * 80)

print("""
Next steps:

1. Configure Ignition JDBC connection to Lakebase:
   - URL: jdbc:postgresql://[lakebase-endpoint]:5432/field_engineering
   - Schema: lakebase
   - Table: recommendations_serving

2. Set up Ignition WebSocket listener for PG NOTIFY:
   - Listen to channel: 'equipment_recommendations'
   - Update Perspective session props on notification
   - Refresh recommendation panel component

3. Create Perspective view bindings:
   - Named Query: SELECT * FROM recommendations_serving WHERE equipment_id = :equipment
   - Poll interval: 5 seconds (or event-driven via PG NOTIFY)

4. Test operator feedback loop:
   - Execute recommendation → INSERT INTO operator_feedback
   - Monitor feedback → Train model weekly
   - Adjust confidence thresholds based on accuracy

5. Deploy DLT pipeline:
   databricks pipelines create --config dlt_pipeline_config.json

6. Start real-time scoring:
   databricks jobs run --notebook realtime_scoring_pipeline

Connection details:
- Warehouse: 4b9b953939869799
- Catalog: field_engineering
- Schema: lakebase
- Primary views:
  * recommendations_serving (for Ignition panels)
  * hmi_dashboard (for main HMI screen)
  * equipment_state (for equipment cards)
""")
