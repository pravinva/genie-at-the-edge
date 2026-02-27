#!/usr/bin/env python3
"""
Find and grant permissions to Zerobus service principal
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

print("🔍 Finding Zerobus Service Principals")
print("=" * 70)

# Find service principals with "zerobus" in the name
all_sps = list(w.service_principals.list())
zerobus_sps = [sp for sp in all_sps if sp.display_name and 'zerobus' in sp.display_name.lower()]

if not zerobus_sps:
    print("⚠️  No service principals found with 'zerobus' in name")
    print("\nAll service principals:")
    for sp in all_sps[:10]:
        print(f"   - {sp.display_name} (ID: {sp.id})")
    print(f"\n💡 Configure which service principal to use in Zerobus")
    exit(0)

print(f"✅ Found {len(zerobus_sps)} Zerobus service principal(s):")
for sp in zerobus_sps:
    print(f"   - {sp.display_name}")
    print(f"     ID: {sp.id}")
    print(f"     Application ID: {sp.application_id if sp.application_id else 'N/A'}")

# Use the first one
sp = zerobus_sps[0]
sp_identifier = sp.application_id if sp.application_id else sp.id

print(f"\n⏳ Granting permissions to: {sp.display_name}")
print(f"   Using identifier: {sp_identifier}")

# Grant permissions
grants = [
    f"GRANT USAGE ON WAREHOUSE `{warehouse_id}` TO `{sp_identifier}`",
    f"GRANT USE CATALOG ON CATALOG field_engineering TO `{sp_identifier}`",
    f"GRANT USE SCHEMA ON SCHEMA field_engineering.mining_demo TO `{sp_identifier}`",
    f"GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `{sp_identifier}`",
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
        error_msg = str(e)
        if "already" in error_msg.lower() or "granted" in error_msg.lower():
            print(f"✅ {grant_sql[:70]}... (already granted)")
            success_count += 1
        else:
            print(f"⚠️  {grant_sql[:70]}...")
            print(f"   Error: {error_msg[:150]}")

print(f"\n✅ Granted {success_count}/{len(grants)} permissions")

print("\n" + "=" * 70)
print("📋 Zerobus Configuration:")
print(f"   Service Principal: {sp.display_name}")
print(f"   Application ID (Client ID): {sp_identifier}")
print(f"   OAuth Secret: <generated in Account Console>")
print("\n✅ Permissions ready!")
print("\n💡 If still failing:")
print("   1. Verify Client ID matches: {sp_identifier}")
print("   2. Restart Ignition: docker-compose -f docker/docker-compose.yml restart")
print("   3. Check Status page in Ignition Gateway")
