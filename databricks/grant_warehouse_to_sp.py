#!/usr/bin/env python3
"""
Grant warehouse permissions to pravin_zerobus service principal
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"
sp_app_id = "6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb"  # Application ID

print("🔐 Granting Warehouse Permissions")
print("=" * 70)

grants = [
    f"GRANT USAGE ON WAREHOUSE `{warehouse_id}` TO `{sp_app_id}`",
    f"GRANT USE CATALOG ON CATALOG field_engineering TO `{sp_app_id}`",
    f"GRANT USE SCHEMA ON SCHEMA field_engineering.ignition_streaming TO `{sp_app_id}`",
]

for grant_sql in grants:
    try:
        w.statement_execution.execute_statement(
            statement=grant_sql,
            warehouse_id=warehouse_id
        )
        print(f"✅ {grant_sql}")
    except Exception as e:
        error_msg = str(e)
        if "already" in error_msg.lower() or "granted" in error_msg.lower():
            print(f"✅ {grant_sql} (already granted)")
        else:
            print(f"⚠️  {grant_sql}")
            print(f"   Error: {error_msg[:150]}")

# Verify
print(f"\n⏳ Verifying warehouse grants...")
try:
    verify_sql = f"SHOW GRANTS ON WAREHOUSE `{warehouse_id}`"
    result = w.statement_execution.execute_statement(
        statement=verify_sql,
        warehouse_id=warehouse_id
    )

    if result.result and result.result.data_array:
        sp_grants = [row for row in result.result.data_array
                    if row and len(row) >= 2 and sp_app_id in str(row[0])]

        if sp_grants:
            print("✅ Current warehouse grants:")
            for row in sp_grants:
                print(f"   {row[0]} → {row[1]}")
        else:
            print("⚠️  No grants found (might need to check using SP ID instead)")
except Exception as e:
    print(f"⚠️  {str(e)[:100]}")

print("\n" + "=" * 70)
print("✅ Permissions updated!")
print("\n💡 Restart Ignition to test OAuth connection:")
print("   docker-compose -f docker/docker-compose.yml restart")
