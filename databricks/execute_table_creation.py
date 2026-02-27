#!/usr/bin/env python3
"""Execute SQL to create the zerobus_sensor_stream table"""

from databricks.sdk import WorkspaceClient
import time

w = WorkspaceClient()

# Get warehouse
warehouses = list(w.warehouses.list())
if not warehouses:
    print("No warehouse found")
    exit(1)

warehouse_id = warehouses[0].id
print(f"Using warehouse: {warehouses[0].name}")

# SQL to create table
sql = """
CREATE TABLE IF NOT EXISTS field_engineering.mining_demo.zerobus_sensor_stream (
    equipment_id STRING COMMENT 'Equipment identifier (e.g., HAUL-001, CRUSH-002)',
    sensor_name STRING COMMENT 'Sensor type (temperature, vibration, pressure, throughput, speed)',
    sensor_value DOUBLE COMMENT 'Sensor reading value',
    units STRING COMMENT 'Unit of measurement',
    timestamp TIMESTAMP COMMENT 'Sensor reading timestamp from Ignition',
    quality INT COMMENT 'OPC quality code (192 = good)',
    _ingestion_timestamp TIMESTAMP COMMENT 'Databricks ingestion timestamp'
)
USING DELTA
COMMENT 'Real-time sensor stream from Ignition via Zerobus connector'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
"""

print("\nCreating table...")
try:
    # Execute statement
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="30s"
    )

    print("✓ Table created: field_engineering.mining_demo.zerobus_sensor_stream")

    # Verify by describing the table
    print("\nVerifying table...")
    verify_sql = "DESCRIBE EXTENDED field_engineering.mining_demo.zerobus_sensor_stream"
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=verify_sql,
        wait_timeout="30s"
    )

    if result.status.state.value == "SUCCEEDED":
        print("✓ Table verified successfully")
        print("\n📊 Table Details:")
        if result.result and result.result.data_array:
            for row in result.result.data_array[:10]:  # Show first 10 rows
                print(f"  {row[0]:<25} {row[1]:<15} {row[2] if len(row) > 2 else ''}")

except Exception as e:
    print(f"Error: {e}")
    exit(1)

print("\n" + "="*70)
print("✅ Setup Complete!")
print("="*70)
print("\nZerobus Configuration:")
print("  Catalog: field_engineering")
print("  Schema: mining_demo")
print("  Table: zerobus_sensor_stream")
print("\nTag Provider: Sample_Tags")
print("Tag Path Pattern: Mining/*")
print("\n" + "="*70)
