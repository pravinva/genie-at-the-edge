#!/usr/bin/env python3
"""
Create fresh sensor_stream_bronze table with complete schema
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"
sp_id = "6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb"

print("🔧 Creating sensor_stream_bronze Table")
print("=" * 70)

# Step 1: Drop if exists
print("\n⏳ Step 1: Dropping old table if exists...")
drop_sql = "DROP TABLE IF EXISTS field_engineering.mining_demo.sensor_stream_bronze"
try:
    w.statement_execution.execute_statement(
        statement=drop_sql,
        warehouse_id=warehouse_id
    )
    print("✅ Cleaned up")
except Exception as e:
    print(f"⚠️  {e}")

# Step 2: Create new table with complete schema
print("\n⏳ Step 2: Creating sensor_stream_bronze with complete schema...")
create_sql = """
CREATE TABLE field_engineering.mining_demo.sensor_stream_bronze (
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
  sdt_enabled BOOLEAN COMMENT 'SDT enabled for this tag',
  batch_bytes_sent BIGINT COMMENT 'Batch bytes sent (Zerobus metadata)'
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Bronze layer: Raw sensor stream from Ignition via Zerobus'
"""

try:
    result = w.statement_execution.execute_statement(
        statement=create_sql,
        warehouse_id=warehouse_id
    )
    print(f"✅ Table created!")
    print(f"   Status: {result.status.state}")

    # Verify schema
    print("\n⏳ Step 3: Verifying schema...")
    verify_sql = "DESCRIBE field_engineering.mining_demo.sensor_stream_bronze"
    verify_result = w.statement_execution.execute_statement(
        statement=verify_sql,
        warehouse_id=warehouse_id
    )

    if verify_result.result and verify_result.result.data_array:
        columns = [r for r in verify_result.result.data_array if r and len(r) >= 2 and r[0] and not r[0].startswith("#")]
        print(f"\n📋 Table Schema ({len(columns)} columns):")
        for i, row in enumerate(columns, 1):
            col_name = row[0]
            col_type = row[1]
            print(f"   {i:2d}. {col_name:<30} {col_type}")

    # Step 4: Grant permissions
    print("\n⏳ Step 4: Granting permissions...")

    grants = [
        # Service Principal
        f"GRANT USAGE ON WAREHOUSE `{warehouse_id}` TO `{sp_id}`",
        f"GRANT USE CATALOG ON CATALOG field_engineering TO `{sp_id}`",
        f"GRANT USE SCHEMA ON SCHEMA field_engineering.mining_demo TO `{sp_id}`",
        f"GRANT SELECT ON TABLE field_engineering.mining_demo.sensor_stream_bronze TO `{sp_id}`",
        f"GRANT INSERT ON TABLE field_engineering.mining_demo.sensor_stream_bronze TO `{sp_id}`",
        f"GRANT MODIFY ON TABLE field_engineering.mining_demo.sensor_stream_bronze TO `{sp_id}`",

        # Account Users
        f"GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.mining_demo.sensor_stream_bronze TO `account users`",
    ]

    for grant_sql in grants:
        try:
            w.statement_execution.execute_statement(
                statement=grant_sql,
                warehouse_id=warehouse_id
            )
            print(f"✅ {grant_sql[:75]}...")
        except Exception as e:
            error_msg = str(e)
            if "already" in error_msg.lower() or "granted" in error_msg.lower():
                print(f"✅ {grant_sql[:75]}... (already granted)")
            else:
                print(f"⚠️  {grant_sql[:75]}...")
                print(f"   Error: {error_msg[:100]}")

    print("\n" + "=" * 70)
    print("✅ Table sensor_stream_bronze is ready!")
    print("\n📋 Update Zerobus Configuration:")
    print(f"   Catalog: field_engineering")
    print(f"   Schema: mining_demo")
    print(f"   Table: sensor_stream_bronze")
    print(f"   Full Name: field_engineering.mining_demo.sensor_stream_bronze")
    print("\n💡 Next: Update table name in Ignition Gateway Zerobus config")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
