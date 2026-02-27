#!/usr/bin/env python3
"""Check if the table exists via SQL query"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Get warehouse
warehouses = list(w.warehouses.list())
warehouse_id = warehouses[0].id

print(f"Using warehouse: {warehouses[0].name}\n")

# Try to describe the table
sql = "SHOW TABLES IN field_engineering.mining_demo"

print("Executing: SHOW TABLES IN field_engineering.mining_demo")
try:
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="30s"
    )

    if result.status.state.value == "SUCCEEDED":
        print("\n✓ Query succeeded")
        if result.result and result.result.data_array:
            print(f"\nTables in mining_demo schema:")
            for row in result.result.data_array:
                print(f"  - {row[1]}")  # table name is second column
        else:
            print("\n⚠ Schema exists but no tables found")

except Exception as e:
    print(f"\n✗ Error: {e}")

# Now try to describe the specific table
print("\n" + "="*70)
sql2 = "DESCRIBE EXTENDED field_engineering.mining_demo.zerobus_sensor_stream"
print(f"Executing: DESCRIBE EXTENDED ...")
try:
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql2,
        wait_timeout="30s"
    )

    if result.status.state.value == "SUCCEEDED":
        print("\n✓ Table exists!")
        if result.result and result.result.data_array:
            print(f"\nTable columns:")
            for row in result.result.data_array[:10]:
                print(f"  {row[0]:<25} {row[1]:<15}")

except Exception as e:
    print(f"\n✗ Table doesn't exist: {e}")
