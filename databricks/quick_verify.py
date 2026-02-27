#!/usr/bin/env python3
"""Quick verification that everything is ready"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

print("🔍 Quick Verification\n")
print("="*70)

# Get warehouse
warehouses = list(w.warehouses.list())
wh = warehouses[0]
print(f"✅ Warehouse: {wh.name} (state: {wh.state.value})")

# Simple query to show tables
sql = "SHOW TABLES IN field_engineering.mining_demo"
print(f"\n📋 Running: {sql}")

result = w.statement_execution.execute_statement(
    warehouse_id=wh.id,
    statement=sql,
    wait_timeout="30s"
)

if result.status.state.value == "SUCCEEDED":
    print(f"✅ Query succeeded\n")
    print("Tables in field_engineering.mining_demo:")
    if result.result and result.result.data_array:
        for row in result.result.data_array:
            # Format: [database, tableName, isTemporary]
            print(f"  ✓ {row[1]}")
    else:
        print("  ⚠️ No tables found")
else:
    print(f"❌ Query failed: {result.status.error}")

print("\n" + "="*70)
print("✅ Verification Complete!")
print("\nNext: Configure Zerobus in Ignition Gateway")
print("See: ZEROBUS_SETUP_COMPLETE.md for instructions")
