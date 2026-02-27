#!/usr/bin/env python3
"""
Verify Zerobus data ingestion
"""
from databricks.sdk import WorkspaceClient
import time

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

print("🔍 Verifying Zerobus Data Ingestion")
print("=" * 60)

# Check 1: Table exists and permissions
print("\n✅ Step 1: Checking table...")
try:
    describe_sql = "DESCRIBE EXTENDED field_engineering.mining_demo.zerobus_sensor_stream"
    result = w.statement_execution.execute_statement(
        statement=describe_sql,
        warehouse_id=warehouse_id
    )
    print("✅ Table exists with correct schema")
except Exception as e:
    print(f"❌ Table check failed: {e}")
    exit(1)

# Check 2: Row count
print("\n⏳ Step 2: Checking row count...")
count_sql = """
SELECT
    COUNT(*) as total_rows,
    MAX(ingestion_timestamp) as latest_ingestion,
    MIN(ingestion_timestamp) as first_ingestion
FROM field_engineering.mining_demo.zerobus_sensor_stream
"""

try:
    result = w.statement_execution.execute_statement(
        statement=count_sql,
        warehouse_id=warehouse_id
    )

    if result.result and result.result.data_array:
        row = result.result.data_array[0]
        total_rows = row[0] if row[0] else 0
        latest = row[1] if row[1] else "N/A"
        first = row[2] if row[2] else "N/A"

        print(f"📊 Total Rows: {total_rows}")
        print(f"   First Ingestion: {first}")
        print(f"   Latest Ingestion: {latest}")

        if total_rows == 0:
            print("\n⚠️  No data ingested yet")
            print("   - Check Zerobus connection status in Ignition")
            print("   - Verify OAuth credentials are correct")
            print("   - Check Ignition logs for errors")
        else:
            print(f"\n✅ Data is flowing! {total_rows} records ingested")

            # Check 3: Sample data
            print("\n⏳ Step 3: Checking sample data...")
            sample_sql = """
            SELECT
                tag_path,
                numeric_value,
                quality,
                event_time,
                ingestion_timestamp
            FROM field_engineering.mining_demo.zerobus_sensor_stream
            ORDER BY ingestion_timestamp DESC
            LIMIT 5
            """

            sample_result = w.statement_execution.execute_statement(
                statement=sample_sql,
                warehouse_id=warehouse_id
            )

            if sample_result.result and sample_result.result.data_array:
                print("\n📋 Latest Records:")
                print(f"{'Tag Path':<40} {'Value':<10} {'Quality':<8} {'Event Time'}")
                print("-" * 80)
                for row in sample_result.result.data_array[:5]:
                    tag = row[0] if row[0] else "N/A"
                    val = f"{row[1]:.2f}" if row[1] else "N/A"
                    qual = row[2] if row[2] else "N/A"
                    evt_time = row[3] if row[3] else "N/A"
                    print(f"{tag:<40} {val:<10} {qual:<8} {evt_time}")

            # Check 4: Ingestion rate
            print("\n⏳ Step 4: Checking ingestion rate...")
            rate_sql = """
            SELECT
                COUNT(*) as records_last_minute,
                COUNT(DISTINCT tag_path) as unique_tags
            FROM field_engineering.mining_demo.zerobus_sensor_stream
            WHERE ingestion_timestamp > CURRENT_TIMESTAMP() - INTERVAL 1 MINUTE
            """

            rate_result = w.statement_execution.execute_statement(
                statement=rate_sql,
                warehouse_id=warehouse_id
            )

            if rate_result.result and rate_result.result.data_array:
                row = rate_result.result.data_array[0]
                records_per_min = row[0] if row[0] else 0
                unique_tags = row[1] if row[1] else 0

                print(f"📈 Ingestion Rate:")
                print(f"   Records/minute: {records_per_min}")
                print(f"   Unique tags: {unique_tags}")
                print(f"   Expected: ~50 tags × 60 = ~3000 records/min")

                if records_per_min > 0:
                    print(f"\n✅ Real-time ingestion is working!")
                else:
                    print(f"\n⚠️  No recent data (check if streaming is active)")

except Exception as e:
    print(f"❌ Query failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ Verification complete!")
