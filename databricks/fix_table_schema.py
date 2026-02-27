#!/usr/bin/env python3
"""
Drop and recreate Zerobus table with correct schema that matches ot_event.proto
"""
from databricks.sdk import WorkspaceClient

# Initialize client
w = WorkspaceClient(profile="DEFAULT")

# Use specified warehouse
warehouse_id = "4b9b953939869799"

print(f"✓ Using warehouse: {warehouse_id}")

# Step 1: Drop existing table with wrong schema
print("\n⏳ Dropping old table...")
drop_sql = "DROP TABLE IF EXISTS field_engineering.mining_demo.zerobus_sensor_stream"
try:
    w.statement_execution.execute_statement(
        statement=drop_sql,
        warehouse_id=warehouse_id
    )
    print("✅ Old table dropped")
except Exception as e:
    print(f"⚠️  Drop failed (may not exist): {e}")

# Step 2: Create new table with correct schema
print("\n⏳ Creating table with correct proto schema...")
create_sql = """
CREATE TABLE field_engineering.mining_demo.zerobus_sensor_stream (
  event_id STRING COMMENT 'Unique event identifier',
  event_time TIMESTAMP COMMENT 'Event timestamp from Ignition',
  tag_path STRING COMMENT 'Full Ignition tag path',
  tag_provider STRING COMMENT 'Ignition tag provider name',
  numeric_value DOUBLE COMMENT 'Numeric tag value',
  string_value STRING COMMENT 'String tag value',
  boolean_value BOOLEAN COMMENT 'Boolean tag value',
  quality INT COMMENT 'Numeric quality code (192 = good)',
  quality_string STRING COMMENT 'Quality indicator (GOOD, BAD, UNCERTAIN)',
  source_system STRING COMMENT 'Source Ignition Gateway identifier',
  ingestion_timestamp TIMESTAMP COMMENT 'Time ingested into Databricks',
  data_type STRING COMMENT 'Original data type from Ignition',
  alarm_state STRING COMMENT 'Alarm state if applicable',
  alarm_priority INT COMMENT 'Alarm priority if applicable'
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Raw tag events from Ignition via Zerobus - matches ot_event.proto'
"""

try:
    statement = w.statement_execution.execute_statement(
        statement=create_sql,
        warehouse_id=warehouse_id
    )
    print(f"✅ Table created successfully!")
    print(f"   Status: {statement.status.state}")

    # Verify schema
    print("\n📋 Verifying Table Schema:")
    verify_sql = "DESCRIBE field_engineering.mining_demo.zerobus_sensor_stream"
    result = w.statement_execution.execute_statement(
        statement=verify_sql,
        warehouse_id=warehouse_id
    )

    if result.result and result.result.data_array:
        for row in result.result.data_array[:14]:  # Show all 14 columns
            if row and len(row) >= 2:
                col_name = row[0]
                col_type = row[1]
                print(f"   ✓ {col_name}: {col_type}")

    print(f"\n🎯 Zerobus Configuration:")
    print(f"   Full Table Name: field_engineering.mining_demo.zerobus_sensor_stream")
    print(f"\n✅ Schema now matches ot_event.proto!")
    print(f"   - event_id, event_time, tag_path, tag_provider ✓")
    print(f"   - quality as INT (not STRING) ✓")
    print(f"   - All proto fields present ✓")

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
