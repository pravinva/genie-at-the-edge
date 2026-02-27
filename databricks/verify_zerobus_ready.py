#!/usr/bin/env python3
"""Verify that Databricks is ready for Zerobus streaming"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

print("="*70)
print("ZEROBUS READINESS CHECK")
print("="*70)

# Check catalog
print("\n1. Checking catalog...")
catalogs = [c for c in w.catalogs.list() if c.name == "field_engineering"]
if catalogs:
    print(f"   ✓ Catalog: field_engineering")
else:
    print(f"   ✗ Catalog not found!")
    exit(1)

# Check schema
print("\n2. Checking schema...")
schemas = [s for s in w.schemas.list(catalog_name="field_engineering") if s.name == "mining_demo"]
if schemas:
    print(f"   ✓ Schema: field_engineering.mining_demo")
else:
    print(f"   ✗ Schema not found!")
    exit(1)

# Check table
print("\n3. Checking table...")
try:
    table = w.tables.get(full_name="field_engineering.mining_demo.zerobus_sensor_stream")
    print(f"   ✓ Table: {table.full_name}")
    print(f"   ✓ Type: {table.table_type.value}")
    print(f"   ✓ Format: {table.data_source_format.value}")

    # Show columns
    print("\n4. Table schema:")
    if table.columns:
        for col in table.columns:
            print(f"   - {col.name:<25} {col.type_name}")

except Exception as e:
    print(f"   ✗ Table not found: {e}")
    exit(1)

# Check warehouse
print("\n5. Checking warehouse...")
warehouses = list(w.warehouses.list())
if warehouses:
    wh = warehouses[0]
    print(f"   ✓ Warehouse: {wh.name}")
    print(f"   ✓ State: {wh.state.value}")
    print(f"   ✓ Warehouse ID: {wh.id}")
else:
    print(f"   ✗ No warehouse found!")
    exit(1)

print("\n" + "="*70)
print("✅ ALL CHECKS PASSED - READY FOR ZEROBUS!")
print("="*70)

print("\n📋 ZEROBUS CONFIGURATION")
print("-"*70)
print("\nIn Ignition Gateway Config → Modules → Zerobus:")
print()
print("Connection Settings:")
print(f"  Host: e2-demo-field-eng.cloud.databricks.com")
print(f"  HTTP Path: /sql/1.0/warehouses/{wh.id}")
print(f"  Token: <your_databricks_token>")
print()
print("Table Settings:")
print(f"  Catalog: field_engineering")
print(f"  Schema: mining_demo")
print(f"  Table: zerobus_sensor_stream")
print()
print("Tag Configuration:")
print(f"  Tag Provider: Sample_Tags")
print(f"  Tag Path Pattern: Mining/*")
print(f"  Mode: On Change")
print(f"  Enabled: ✅")
print()
print("-"*70)

print("\n🔍 VERIFICATION QUERY")
print("-"*70)
print("""
After Zerobus is configured, run this query to verify streaming:

SELECT
    equipment_id,
    sensor_name,
    sensor_value,
    timestamp,
    _ingestion_timestamp
FROM field_engineering.mining_demo.zerobus_sensor_stream
ORDER BY _ingestion_timestamp DESC
LIMIT 20;

Expected: New records arriving every 1 second!
""")
print("-"*70)
