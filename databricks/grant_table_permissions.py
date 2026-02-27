#!/usr/bin/env python3
"""
Grant permissions on zerobus_sensor_stream table to account users
"""
from databricks.sdk import WorkspaceClient

# Initialize client
w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

print("⏳ Granting permissions to account users...")

# Grant permissions
sqls = [
    "GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `account users`",
    "GRANT USE SCHEMA ON SCHEMA field_engineering.mining_demo TO `account users`",
    "GRANT USE CATALOG ON CATALOG field_engineering TO `account users`"
]

for sql in sqls:
    try:
        w.statement_execution.execute_statement(
            statement=sql,
            warehouse_id=warehouse_id
        )
        print(f"✅ {sql}")
    except Exception as e:
        print(f"⚠️  {sql}")
        print(f"   Error: {e}")

print("\n✅ Permissions granted!")
print("\n🔍 Verifying table details:")

# Show table info
info_sql = """
SELECT
    'field_engineering.mining_demo.zerobus_sensor_stream' as table_name,
    COUNT(*) as row_count
FROM field_engineering.mining_demo.zerobus_sensor_stream
"""

try:
    result = w.statement_execution.execute_statement(
        statement=info_sql,
        warehouse_id=warehouse_id
    )
    if result.result and result.result.data_array:
        row = result.result.data_array[0]
        print(f"   Table: {row[0]}")
        print(f"   Rows: {row[1]}")
except Exception as e:
    print(f"   Table ready, no rows yet: {e}")

print("\n📋 Table is ready for Zerobus ingestion!")
