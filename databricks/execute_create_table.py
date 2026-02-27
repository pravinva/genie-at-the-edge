#!/usr/bin/env python3
"""
Create Zerobus sensor stream table with correct schema
"""
from databricks.sdk import WorkspaceClient

# Initialize client
w = WorkspaceClient(profile="DEFAULT")

# SQL to create table
sql = """
CREATE TABLE IF NOT EXISTS field_engineering.mining_demo.zerobus_sensor_stream (
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
COMMENT 'Raw tag events from Ignition via Zerobus connector - matches ot_event.proto schema'
"""

try:
    # Get warehouse
    warehouses = list(w.warehouses.list())
    warehouse_id = next((wh.id for wh in warehouses if wh.state.value == "RUNNING"), warehouses[0].id if warehouses else None)

    if not warehouse_id:
        print("❌ No warehouse available")
        exit(1)

    print(f"✓ Using warehouse: {warehouse_id}")

    # Execute SQL
    print("\n⏳ Creating table...")
    statement = w.statement_execution.execute_statement(
        statement=sql,
        warehouse_id=warehouse_id
    )

    print(f"✅ Table created successfully!")
    print(f"   Status: {statement.status.state}")

    # Verify table exists
    verify_sql = "DESCRIBE EXTENDED field_engineering.mining_demo.zerobus_sensor_stream"
    result = w.statement_execution.execute_statement(
        statement=verify_sql,
        warehouse_id=warehouse_id
    )

    print(f"\n📋 Table Schema:")
    if result.result and result.result.data_array:
        for row in result.result.data_array[:14]:  # Show first 14 columns
            if row and len(row) >= 2:
                col_name = row[0]
                col_type = row[1]
                print(f"   {col_name}: {col_type}")

    print(f"\n🎯 Zerobus Configuration:")
    print(f"   Catalog: field_engineering")
    print(f"   Schema: mining_demo")
    print(f"   Table: zerobus_sensor_stream")
    print(f"   Full Name: field_engineering.mining_demo.zerobus_sensor_stream")

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
