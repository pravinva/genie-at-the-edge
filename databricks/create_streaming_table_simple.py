#!/usr/bin/env python3
"""Simple script to create the streaming table"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Get warehouse
warehouses = list(w.warehouses.list())
if not warehouses:
    print("No warehouse found")
    exit(1)

warehouse_id = warehouses[0].id
print(f"Using warehouse: {warehouses[0].name}")

# Create schema
print("\n1. Creating schema...")
try:
    w.schemas.create(
        catalog_name="field_engineering",
        name="mining_demo",
        comment="Mining demo schema"
    )
    print("✓ Schema created: field_engineering.mining_demo")
except Exception as e:
    if "already exists" in str(e).lower():
        print("✓ Schema already exists")
    else:
        print(f"Error: {e}")

# Create table using catalog API
print("\n2. Creating table...")
try:
    w.tables.create(
        catalog_name="field_engineering",
        schema_name="mining_demo",
        name="zerobus_sensor_stream",
        table_type="MANAGED",
        data_source_format="DELTA",
        columns=[
            {"name": "equipment_id", "type_name": "STRING"},
            {"name": "sensor_name", "type_name": "STRING"},
            {"name": "sensor_value", "type_name": "DOUBLE"},
            {"name": "units", "type_name": "STRING"},
            {"name": "timestamp", "type_name": "TIMESTAMP"},
            {"name": "quality", "type_name": "INT"},
            {"name": "_ingestion_timestamp", "type_name": "TIMESTAMP"}
        ],
        comment="Real-time sensor stream from Ignition via Zerobus"
    )
    print("✓ Table created: field_engineering.mining_demo.zerobus_sensor_stream")
except Exception as e:
    if "already exists" in str(e).lower():
        print("✓ Table already exists")
    else:
        print(f"Error: {e}")

print("\n✅ Setup complete!")
print("\nTable path: field_engineering.mining_demo.zerobus_sensor_stream")
print("\nFor Zerobus config:")
print("  Catalog: field_engineering")
print("  Schema: mining_demo")
print("  Table: zerobus_sensor_stream")
