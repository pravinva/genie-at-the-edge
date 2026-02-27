#!/usr/bin/env python3
"""
Check table permissions and verify data ingestion
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

print("🔍 Checking Permissions and Data Ingestion")
print("=" * 70)

# Step 1: Check if table exists
print("\n⏳ Step 1: Checking table existence...")
try:
    describe_sql = "DESCRIBE EXTENDED field_engineering.mining_demo.zerobus_sensor_stream"
    result = w.statement_execution.execute_statement(
        statement=describe_sql,
        warehouse_id=warehouse_id
    )
    print("✅ Table exists")
except Exception as e:
    print(f"❌ Table does not exist: {e}")
    exit(1)

# Step 2: Check current permissions
print("\n⏳ Step 2: Checking current permissions...")
grants_sql = "SHOW GRANTS ON TABLE field_engineering.mining_demo.zerobus_sensor_stream"
try:
    result = w.statement_execution.execute_statement(
        statement=grants_sql,
        warehouse_id=warehouse_id
    )

    if result.result and result.result.data_array:
        print("📋 Current Grants:")
        for row in result.result.data_array:
            if row and len(row) >= 2:
                principal = row[0]
                privilege = row[1]
                print(f"   {principal:<50} {privilege}")
    else:
        print("⚠️  No grants found!")

except Exception as e:
    print(f"⚠️  Could not check grants: {str(e)[:150]}")

# Step 3: Re-grant permissions
print("\n⏳ Step 3: Re-granting permissions...")
sp_id = "6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb"

grants = [
    f"GRANT USAGE ON WAREHOUSE `{warehouse_id}` TO `{sp_id}`",
    f"GRANT USE CATALOG ON CATALOG field_engineering TO `{sp_id}`",
    f"GRANT USE SCHEMA ON SCHEMA field_engineering.mining_demo TO `{sp_id}`",
    f"GRANT SELECT ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `{sp_id}`",
    f"GRANT INSERT ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `{sp_id}`",
    f"GRANT MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `{sp_id}`",
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
        error_msg = str(e)
        if "already" in error_msg.lower() or "granted" in error_msg.lower():
            print(f"✅ {grant_sql[:75]}... (already granted)")
        else:
            print(f"⚠️  {grant_sql[:75]}...")
            print(f"   Error: {error_msg[:100]}")

# Step 4: Check row count
print("\n⏳ Step 4: Checking data ingestion...")
count_sql = """
SELECT
    COUNT(*) as row_count,
    MAX(ingestion_timestamp) as latest_ingestion
FROM field_engineering.mining_demo.zerobus_sensor_stream
"""

try:
    result = w.statement_execution.execute_statement(
        statement=count_sql,
        warehouse_id=warehouse_id
    )

    if result.result and result.result.data_array:
        row = result.result.data_array[0]
        row_count = row[0] if row[0] else 0
        latest = row[1] if row[1] else "N/A"

        print(f"📊 Data Status:")
        print(f"   Total Rows: {row_count}")
        print(f"   Latest Ingestion: {latest}")

        if row_count > 0:
            print(f"\n🎉 SUCCESS! Data is flowing!")

            # Sample data
            sample_sql = """
            SELECT tag_path, numeric_value, quality, event_time
            FROM field_engineering.mining_demo.zerobus_sensor_stream
            ORDER BY ingestion_timestamp DESC
            LIMIT 5
            """
            sample_result = w.statement_execution.execute_statement(
                statement=sample_sql,
                warehouse_id=warehouse_id
            )

            if sample_result.result and sample_result.result.data_array:
                print("\n📋 Sample Records:")
                for row in sample_result.result.data_array:
                    tag = row[0][:40] if row[0] else "N/A"
                    val = f"{row[1]:.2f}" if row[1] else "N/A"
                    qual = row[2] if row[2] else "N/A"
                    evt_time = row[3] if row[3] else "N/A"
                    print(f"   {tag:<40} {val:<10} Q:{qual} {evt_time}")
        else:
            print(f"\n⚠️  No data yet - check Zerobus connection status")

except Exception as e:
    print(f"❌ Query failed: {e}")

print("\n" + "=" * 70)
print("✅ Check complete!")
