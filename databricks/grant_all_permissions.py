#!/usr/bin/env python3
"""
Grant ALL necessary permissions for Zerobus service principal
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"
sp_id = "6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb"

print("🔐 Granting ALL Permissions for Zerobus")
print("=" * 70)

# Comprehensive permission grants
grants = [
    # Warehouse
    f"GRANT USAGE ON WAREHOUSE `{warehouse_id}` TO `{sp_id}`",

    # Catalog level
    f"GRANT USE CATALOG ON CATALOG field_engineering TO `{sp_id}`",
    f"GRANT CREATE SCHEMA ON CATALOG field_engineering TO `{sp_id}`",

    # Schema level
    f"GRANT USE SCHEMA ON SCHEMA field_engineering.ignition_streaming TO `{sp_id}`",
    f"GRANT CREATE TABLE ON SCHEMA field_engineering.ignition_streaming TO `{sp_id}`",
    f"GRANT CREATE FUNCTION ON SCHEMA field_engineering.ignition_streaming TO `{sp_id}`",

    # Table level
    f"GRANT ALL PRIVILEGES ON TABLE field_engineering.ignition_streaming.sensor_events TO `{sp_id}`",

    # Also to account users as backup
    f"GRANT USAGE ON WAREHOUSE `{warehouse_id}` TO `account users`",
    f"GRANT ALL PRIVILEGES ON TABLE field_engineering.ignition_streaming.sensor_events TO `account users`",
]

success = 0
for grant_sql in grants:
    try:
        w.statement_execution.execute_statement(
            statement=grant_sql,
            warehouse_id=warehouse_id
        )
        print(f"✅ {grant_sql[:75]}...")
        success += 1
    except Exception as e:
        error_msg = str(e)
        if "already" in error_msg.lower() or "granted" in error_msg.lower():
            print(f"✅ {grant_sql[:75]}... (already granted)")
            success += 1
        else:
            print(f"⚠️  {grant_sql[:75]}...")
            print(f"   Error: {error_msg[:150]}")

print(f"\n✅ Granted {success}/{len(grants)} permissions")

# Show current grants
print("\n⏳ Checking current grants on table...")
show_grants_sql = "SHOW GRANTS ON TABLE field_engineering.ignition_streaming.sensor_events"
try:
    result = w.statement_execution.execute_statement(
        statement=show_grants_sql,
        warehouse_id=warehouse_id
    )
    if result.result and result.result.data_array:
        print("\n📋 Current Grants:")
        for row in result.result.data_array:
            if row and len(row) >= 2:
                print(f"   {row[0]:<50} {row[1]}")
except Exception as e:
    print(f"⚠️  Could not show grants: {str(e)[:100]}")

print("\n" + "=" * 70)
print("✅ Permissions updated!")
print("\n💡 Next: Restart Ignition to apply new permissions")
print("   docker-compose -f docker/docker-compose.yml restart")
