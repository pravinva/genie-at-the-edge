#!/usr/bin/env python3
"""
Verify Service Principal OAuth configuration and permissions
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"
sp_id = "6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb"

print("🔍 Verifying Service Principal OAuth & Permissions")
print("=" * 70)

# Step 1: Check if service principal exists
print(f"\n⏳ Step 1: Checking service principal {sp_id}...")
try:
    sp = w.service_principals.get(sp_id)
    print(f"✅ Service Principal found: {sp.display_name}")
    print(f"   Application ID: {sp.application_id}")
    print(f"   Active: {sp.active}")
except Exception as e:
    print(f"❌ Service principal not found: {e}")
    exit(1)

# Step 2: Check warehouse permissions
print(f"\n⏳ Step 2: Checking warehouse permissions...")
try:
    grants_sql = f"SHOW GRANTS ON WAREHOUSE `{warehouse_id}`"
    result = w.statement_execution.execute_statement(
        statement=grants_sql,
        warehouse_id=warehouse_id
    )

    if result.result and result.result.data_array:
        sp_warehouse_grants = [row for row in result.result.data_array
                               if row and len(row) >= 2 and sp_id in str(row[0])]
        if sp_warehouse_grants:
            print("✅ Warehouse grants found for service principal:")
            for row in sp_warehouse_grants:
                print(f"   {row[1]}")
        else:
            print("⚠️  No warehouse grants found for service principal")
except Exception as e:
    print(f"⚠️  Could not check warehouse grants: {str(e)[:100]}")

# Step 3: Check catalog permissions
print(f"\n⏳ Step 3: Checking catalog permissions...")
try:
    grants_sql = "SHOW GRANTS ON CATALOG field_engineering"
    result = w.statement_execution.execute_statement(
        statement=grants_sql,
        warehouse_id=warehouse_id
    )

    if result.result and result.result.data_array:
        sp_catalog_grants = [row for row in result.result.data_array
                            if row and len(row) >= 2 and sp_id in str(row[0])]
        if sp_catalog_grants:
            print("✅ Catalog grants found for service principal:")
            for row in sp_catalog_grants:
                print(f"   {row[1]}")
        else:
            print("⚠️  No catalog grants found for service principal")
except Exception as e:
    print(f"⚠️  Could not check catalog grants: {str(e)[:100]}")

# Step 4: Check table permissions
print(f"\n⏳ Step 4: Checking table permissions...")
tables_to_check = [
    "field_engineering.ignition_streaming.sensor_events",
    "field_engineering.mining_demo.sensor_stream_bronze",
    "field_engineering.mining_demo.zerobus_sensor_stream"
]

for table_name in tables_to_check:
    try:
        grants_sql = f"SHOW GRANTS ON TABLE {table_name}"
        result = w.statement_execution.execute_statement(
            statement=grants_sql,
            warehouse_id=warehouse_id
        )

        if result.result and result.result.data_array:
            sp_table_grants = [row for row in result.result.data_array
                              if row and len(row) >= 2 and sp_id in str(row[0])]
            if sp_table_grants:
                print(f"\n✅ {table_name}:")
                for row in sp_table_grants:
                    print(f"   {row[1]}")
    except Exception as e:
        if "does not exist" in str(e).lower() or "not found" in str(e).lower():
            print(f"\n⚠️  {table_name}: Table does not exist")
        else:
            print(f"\n⚠️  {table_name}: {str(e)[:80]}")

# Step 5: Current OAuth configuration info
print("\n" + "=" * 70)
print("📋 OAuth Configuration Expected:")
print(f"   Service Principal ID: {sp_id}")
print(f"   OAuth Client ID: {sp_id}")
print(f"   OAuth Client Secret: <regenerated secret from account console>")
print(f"   Workspace: e2-demo-field-eng.cloud.databricks.com")
print(f"   Warehouse ID: {warehouse_id}")
print(f"   Target Table: field_engineering.ignition_streaming.sensor_events")
print("\n💡 If OAuth 401 persists:")
print("   1. Verify the secret in Ignition Gateway matches the latest generated secret")
print("   2. Check Account Console > Service Principals > OAuth Secrets")
print("   3. Ensure 'all-apis' scope is granted to the OAuth application")
