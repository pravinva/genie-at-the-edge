#!/usr/bin/env python3
"""
Create OAuth M2M service principal for Zerobus
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import iam
import json

# Initialize workspace client
w = WorkspaceClient(profile="DEFAULT")

print("🔐 Creating OAuth M2M Credentials for Zerobus")
print("=" * 70)

sp_name = "zerobus-ignition-connector"
warehouse_id = "4b9b953939869799"

try:
    # Step 1: Create or find service principal
    print(f"\n⏳ Step 1: Creating service principal '{sp_name}'...")

    existing_sps = list(w.service_principals.list(filter=f'displayName eq "{sp_name}"'))

    if existing_sps:
        sp = existing_sps[0]
        print(f"✅ Found existing service principal")
        print(f"   Display Name: {sp.display_name}")
        print(f"   ID: {sp.id}")
        print(f"   Application ID: {sp.application_id}")
    else:
        sp = w.service_principals.create(
            display_name=sp_name,
            active=True
        )
        print(f"✅ Created new service principal")
        print(f"   Display Name: {sp.display_name}")
        print(f"   ID: {sp.id}")
        print(f"   Application ID: {sp.application_id}")

    # Step 2: Generate OAuth secret
    print(f"\n⏳ Step 2: Generating OAuth secret...")

    try:
        # Try to create OAuth secret
        secret = w.service_principal_secrets.create(
            service_principal_id=sp.id
        )

        print(f"✅ OAuth secret generated!")
        print(f"   Secret ID: {secret.id}")
        print(f"   Secret Value: {secret.secret}")
        print(f"   Created Time: {secret.create_time}")

        client_id = sp.application_id
        client_secret = secret.secret

        print(f"\n📋 OAuth Credentials:")
        print(f"   Client ID: {client_id}")
        print(f"   Client Secret: {client_secret}")

    except Exception as secret_err:
        print(f"⚠️  OAuth secret creation failed: {str(secret_err)[:200]}")
        print(f"\n💡 OAuth secrets must be created through Account Console:")
        print(f"   1. Go to https://accounts.cloud.databricks.com/")
        print(f"   2. User management → Service principals → {sp_name}")
        print(f"   3. OAuth tab → Generate secret")
        print(f"   4. Copy Client ID and Secret")

        client_id = sp.application_id if sp.application_id else "See Account Console"
        client_secret = "Generate in Account Console"

    # Step 3: Grant permissions
    print(f"\n⏳ Step 3: Granting permissions...")

    sp_identifier = f"`{sp.application_id}`" if sp.application_id else f"`{sp.id}`"

    grants = [
        f"GRANT USAGE ON WAREHOUSE `{warehouse_id}` TO {sp_identifier}",
        f"GRANT USE CATALOG ON CATALOG field_engineering TO {sp_identifier}",
        f"GRANT USE SCHEMA ON SCHEMA field_engineering.mining_demo TO {sp_identifier}",
        f"GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO {sp_identifier}",
    ]

    for grant_sql in grants:
        try:
            result = w.statement_execution.execute_statement(
                statement=grant_sql,
                warehouse_id=warehouse_id
            )
            print(f"✅ {grant_sql[:60]}...")
        except Exception as grant_err:
            print(f"⚠️  {grant_sql[:60]}...")
            print(f"   Error: {str(grant_err)[:100]}")

    # Save configuration
    print(f"\n⏳ Step 4: Saving configuration...")

    config = {
        "service_principal_name": sp.display_name,
        "service_principal_id": sp.id,
        "application_id": sp.application_id if sp.application_id else sp.id,
        "client_id": client_id,
        "client_secret": client_secret,
        "workspace_host": "e2-demo-field-eng.cloud.databricks.com",
        "warehouse_id": warehouse_id,
        "http_path": f"/sql/1.0/warehouses/{warehouse_id}",
        "catalog": "field_engineering",
        "schema": "mining_demo",
        "table": "zerobus_sensor_stream"
    }

    config_file = "/Users/pravin.varma/Documents/Demo/genie-at-the-edge/.databricks_oauth_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ Configuration saved to: {config_file}")

    # Display Zerobus configuration
    print(f"\n" + "=" * 70)
    print(f"📋 ZEROBUS CONFIGURATION (Ignition Gateway)")
    print(f"=" * 70)
    print(f"\nAuthentication Type: OAuth M2M")
    print(f"Host: {config['workspace_host']}")
    print(f"HTTP Path: {config['http_path']}")
    print(f"\nOAuth Client ID: {config['client_id']}")
    print(f"OAuth Client Secret: {config['client_secret']}")
    print(f"\nCatalog: {config['catalog']}")
    print(f"Schema: {config['schema']}")
    print(f"Table: {config['table']}")
    print(f"\n" + "=" * 70)

    if client_secret == "Generate in Account Console":
        print(f"\n⚠️  IMPORTANT: Generate OAuth secret in Account Console first!")
        print(f"   URL: https://accounts.cloud.databricks.com/")
        print(f"   Path: User management → Service principals → {sp_name}")

    print(f"\n✅ Service principal ready for Zerobus!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
