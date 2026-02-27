#!/usr/bin/env python3
"""
Fix table schema to match COMPLETE Zerobus proto definition
Including SDT (Swinging Door Trending) compression fields
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

print("🔧 Fixing Table Schema - Complete Proto Match")
print("=" * 70)

# Drop old table
print("\n⏳ Step 1: Dropping old table...")
drop_sql = "DROP TABLE IF EXISTS field_engineering.mining_demo.zerobus_sensor_stream"
try:
    w.statement_execution.execute_statement(
        statement=drop_sql,
        warehouse_id=warehouse_id
    )
    print("✅ Old table dropped")
except Exception as e:
    print(f"⚠️  {e}")

# Create new table with COMPLETE schema including SDT fields
print("\n⏳ Step 2: Creating table with COMPLETE proto schema...")
create_sql = """
CREATE TABLE field_engineering.mining_demo.zerobus_sensor_stream (
  event_id STRING COMMENT 'Unique event identifier',
  event_time TIMESTAMP COMMENT 'Event timestamp from Ignition',
  tag_path STRING COMMENT 'Full Ignition tag path',
  tag_provider STRING COMMENT 'Ignition tag provider name',
  numeric_value DOUBLE COMMENT 'Numeric tag value',
  string_value STRING COMMENT 'String tag value',
  boolean_value BOOLEAN COMMENT 'Boolean tag value',
  quality INT COMMENT 'OPC quality code (192 = good)',
  quality_code INT COMMENT 'Extended quality code',
  quality_string STRING COMMENT 'Quality indicator (GOOD, BAD, UNCERTAIN)',
  source_system STRING COMMENT 'Source Ignition Gateway identifier',
  ingestion_timestamp TIMESTAMP COMMENT 'Time ingested into Databricks',
  data_type STRING COMMENT 'Original data type from Ignition',
  alarm_state STRING COMMENT 'Alarm state if applicable',
  alarm_priority INT COMMENT 'Alarm priority if applicable',
  sdt_compressed BOOLEAN COMMENT 'SDT compression flag',
  compression_ratio DOUBLE COMMENT 'SDT compression ratio',
  sdt_enabled BOOLEAN COMMENT 'SDT enabled for this tag'
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Raw tag events from Ignition via Zerobus - COMPLETE proto schema with SDT'
"""

try:
    result = w.statement_execution.execute_statement(
        statement=create_sql,
        warehouse_id=warehouse_id
    )
    print(f"✅ Table created with complete schema!")
    print(f"   Status: {result.status.state}")

    # Verify schema
    print("\n⏳ Step 3: Verifying schema...")
    verify_sql = "DESCRIBE field_engineering.mining_demo.zerobus_sensor_stream"
    verify_result = w.statement_execution.execute_statement(
        statement=verify_sql,
        warehouse_id=warehouse_id
    )

    if verify_result.result and verify_result.result.data_array:
        print("\n📋 Table Schema (18 columns):")
        for i, row in enumerate(verify_result.result.data_array[:18], 1):
            if row and len(row) >= 2:
                col_name = row[0]
                col_type = row[1]
                print(f"   {i:2d}. {col_name:<25} {col_type}")

    # Grant permissions
    print("\n⏳ Step 4: Granting permissions...")
    sp_id = "6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb"

    grants = [
        f"GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `{sp_id}`",
        f"GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `account users`",
    ]

    for grant_sql in grants:
        try:
            w.statement_execution.execute_statement(
                statement=grant_sql,
                warehouse_id=warehouse_id
            )
            print(f"✅ {grant_sql[:75]}...")
        except Exception as e:
            print(f"⚠️  {grant_sql[:75]}... ({str(e)[:50]})")

    print("\n" + "=" * 70)
    print("✅ Table schema fixed with ALL proto fields:")
    print("   - event_id, event_time, tag_path, tag_provider ✓")
    print("   - quality (INT), quality_code (INT) ✓")
    print("   - SDT fields: sdt_compressed, compression_ratio, sdt_enabled ✓")
    print("   - Total: 18 columns")
    print("\n💡 Next: Restart Ignition to reconnect with new schema")
    print("   docker-compose -f docker/docker-compose.yml restart")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
