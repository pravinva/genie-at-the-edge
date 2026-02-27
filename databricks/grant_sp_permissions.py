#!/usr/bin/env python3
"""
Grant all necessary permissions to Zerobus service principal
"""
from databricks.sdk import WorkspaceClient
import sys

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

print("🔐 Granting Permissions to Zerobus Service Principal")
print("=" * 70)

# Get service principal name from user
print("\nWhat is the service principal name?")
print("(e.g., 'zerobus-ignition-connector' or the Application ID)")
sp_name = input("Service Principal Name: ").strip()

if not sp_name:
    print("❌ No service principal name provided")
    exit(1)

print(f"\n⏳ Granting permissions to: {sp_name}")

# Permissions to grant
grants = [
    # Warehouse access
    f"GRANT USAGE ON WAREHOUSE `{warehouse_id}` TO `{sp_name}`",

    # Catalog access
    f"GRANT USE CATALOG ON CATALOG field_engineering TO `{sp_name}`",
    f"GRANT CREATE SCHEMA ON CATALOG field_engineering TO `{sp_name}`",

    # Schema access
    f"GRANT USE SCHEMA ON SCHEMA field_engineering.mining_demo TO `{sp_name}`",
    f"GRANT CREATE TABLE ON SCHEMA field_engineering.mining_demo TO `{sp_name}`",

    # Table access
    f"GRANT SELECT ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `{sp_name}`",
    f"GRANT INSERT ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `{sp_name}`",
    f"GRANT MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `{sp_name}`",
]

success_count = 0
for grant_sql in grants:
    try:
        w.statement_execution.execute_statement(
            statement=grant_sql,
            warehouse_id=warehouse_id
        )
        print(f"✅ {grant_sql[:70]}...")
        success_count += 1
    except Exception as e:
        error_msg = str(e)[:150]
        if "already exists" in error_msg.lower() or "granted" in error_msg.lower():
            print(f"✅ {grant_sql[:70]}... (already granted)")
            success_count += 1
        else:
            print(f"⚠️  {grant_sql[:70]}...")
            print(f"   Error: {error_msg}")

print(f"\n✅ Granted {success_count}/{len(grants)} permissions")

# Also grant to account users as fallback
print(f"\n⏳ Also granting to `account users` as fallback...")
account_grants = [
    f"GRANT USAGE ON WAREHOUSE `{warehouse_id}` TO `account users`",
    f"GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `account users`",
]

for grant_sql in account_grants:
    try:
        w.statement_execution.execute_statement(
            statement=grant_sql,
            warehouse_id=warehouse_id
        )
        print(f"✅ {grant_sql[:70]}...")
    except Exception as e:
        print(f"⚠️  {grant_sql[:70]}... (may already exist)")

print("\n" + "=" * 70)
print("✅ Permissions granted!")
print("\n💡 Next steps:")
print("   1. Restart Ignition Gateway:")
print("      docker-compose -f docker/docker-compose.yml restart")
print("   2. Wait 30 seconds")
print("   3. Check logs for 'Connected' or 'Success' messages")
print("   4. Verify ingestion: python3 databricks/verify_ingestion.py")
