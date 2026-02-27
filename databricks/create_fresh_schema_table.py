#!/usr/bin/env python3
"""
Create completely fresh schema + table to bypass Zerobus cache
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"
sp_id = "6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb"

print("🔧 Creating Fresh Schema + Table to Bypass Cache")
print("=" * 70)

# Step 1: Create new schema
print("\n⏳ Step 1: Creating fresh schema...")
schema_sql = "CREATE SCHEMA IF NOT EXISTS field_engineering.ignition_streaming COMMENT 'Ignition real-time streaming data'"
try:
    w.statement_execution.execute_statement(
        statement=schema_sql,
        warehouse_id=warehouse_id
    )
    print("✅ Schema created: field_engineering.ignition_streaming")
except Exception as e:
    print(f"⚠️  {e}")

# Step 2: Create table with complete schema
print("\n⏳ Step 2: Creating sensor_events table...")
create_sql = """
CREATE TABLE IF NOT EXISTS field_engineering.ignition_streaming.sensor_events (
  event_id STRING,
  event_time TIMESTAMP,
  tag_path STRING,
  tag_provider STRING,
  numeric_value DOUBLE,
  string_value STRING,
  boolean_value BOOLEAN,
  quality INT,
  quality_code INT,
  quality_string STRING,
  source_system STRING,
  ingestion_timestamp TIMESTAMP,
  data_type STRING,
  alarm_state STRING,
  alarm_priority INT,
  sdt_compressed BOOLEAN,
  compression_ratio DOUBLE,
  sdt_enabled BOOLEAN,
  batch_bytes_sent BIGINT
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Raw sensor events from Ignition Gateway'
"""

try:
    result = w.statement_execution.execute_statement(
        statement=create_sql,
        warehouse_id=warehouse_id
    )
    print(f"✅ Table created!")

    # Verify
    verify_sql = "SELECT column_name, data_type FROM field_engineering.information_schema.columns WHERE table_schema = 'ignition_streaming' AND table_name = 'sensor_events' ORDER BY ordinal_position"
    verify_result = w.statement_execution.execute_statement(
        statement=verify_sql,
        warehouse_id=warehouse_id
    )

    if verify_result.result and verify_result.result.data_array:
        print(f"\n📋 Schema ({len(verify_result.result.data_array)} columns):")
        for i, row in enumerate(verify_result.result.data_array, 1):
            if row:
                col = row[0]
                dtype = row[1]
                marker = ' ✓ INT' if col == 'quality' else ''
                print(f"   {i:2d}. {col:<30} {dtype}{marker}")

    # Step 3: Grant permissions
    print("\n⏳ Step 3: Granting permissions...")

    grants = [
        f"GRANT USAGE ON WAREHOUSE `{warehouse_id}` TO `{sp_id}`",
        f"GRANT USE SCHEMA ON SCHEMA field_engineering.ignition_streaming TO `{sp_id}`",
        f"GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.ignition_streaming.sensor_events TO `{sp_id}`",
        f"GRANT USE SCHEMA ON SCHEMA field_engineering.ignition_streaming TO `account users`",
        f"GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.ignition_streaming.sensor_events TO `account users`",
    ]

    for grant_sql in grants:
        try:
            w.statement_execution.execute_statement(
                statement=grant_sql,
                warehouse_id=warehouse_id
            )
            print(f"✅ {grant_sql[:70]}...")
        except Exception as e:
            if "already" in str(e).lower():
                print(f"✅ {grant_sql[:70]}... (exists)")
            else:
                print(f"⚠️  {grant_sql[:70]}... {str(e)[:50]}")

    print("\n" + "=" * 70)
    print("✅ FRESH TABLE READY - NO CACHE!")
    print("\n📋 NEW Zerobus Configuration:")
    print(f"   Catalog: field_engineering")
    print(f"   Schema: ignition_streaming")
    print(f"   Table: sensor_events")
    print(f"\n💡 Update in Ignition Gateway and restart")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
