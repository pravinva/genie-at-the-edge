#!/usr/bin/env python3
"""
Get service principal by name: pravin_zerobus
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

print("🔍 Finding pravin_zerobus Service Principal")
print("=" * 70)

try:
    # Search for service principal by name
    all_sps = w.service_principals.list(filter='displayName eq pravin_zerobus')

    sp_list = list(all_sps)

    if sp_list:
        sp = sp_list[0]
        print(f"\n✅ Found service principal:")
        print(f"   Display Name: {sp.display_name}")
        print(f"   ID: {sp.id}")
        print(f"   Application ID: {sp.application_id}")
        print(f"   Active: {sp.active}")

        sp_id = sp.id
        app_id = sp.application_id

        # Check warehouse grants
        print(f"\n⏳ Checking warehouse permissions...")
        try:
            grants_sql = f"SHOW GRANTS ON WAREHOUSE `{warehouse_id}`"
            result = w.statement_execution.execute_statement(
                statement=grants_sql,
                warehouse_id=warehouse_id
            )

            if result.result and result.result.data_array:
                sp_grants = [row for row in result.result.data_array
                           if row and len(row) >= 2 and
                           (sp_id in str(row[0]) or app_id in str(row[0]) or 'pravin' in str(row[0]).lower())]

                if sp_grants:
                    print("✅ Warehouse grants:")
                    for row in sp_grants:
                        print(f"   {row[0]} → {row[1]}")
                else:
                    print("⚠️  No warehouse grants found")
        except Exception as e:
            print(f"⚠️  {str(e)[:100]}")

        # Check table grants
        print(f"\n⏳ Checking table permissions on sensor_events...")
        try:
            grants_sql = "SHOW GRANTS ON TABLE field_engineering.ignition_streaming.sensor_events"
            result = w.statement_execution.execute_statement(
                statement=grants_sql,
                warehouse_id=warehouse_id
            )

            if result.result and result.result.data_array:
                sp_grants = [row for row in result.result.data_array
                           if row and len(row) >= 2 and
                           (sp_id in str(row[0]) or app_id in str(row[0]) or 'pravin' in str(row[0]).lower())]

                if sp_grants:
                    print("✅ Table grants:")
                    for row in sp_grants:
                        print(f"   {row[0]} → {row[1]}")
                else:
                    print("⚠️  No table grants found")
                    print(f"\n💡 NEED TO GRANT PERMISSIONS!")
                    print(f"   Service Principal ID: {sp_id}")
                    print(f"   Application ID: {app_id}")
        except Exception as e:
            print(f"⚠️  {str(e)[:100]}")

        print(f"\n" + "=" * 70)
        print(f"📋 OAuth Configuration:")
        print(f"   Service Principal: pravin_zerobus")
        print(f"   OAuth Client ID (Application ID): {app_id}")
        print(f"   OAuth Client Secret ID: 6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb")
        print(f"\n💡 Use the Application ID as OAuth Client ID in Ignition!")

    else:
        print("\n❌ Service principal 'pravin_zerobus' not found")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
