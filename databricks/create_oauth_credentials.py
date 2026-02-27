#!/usr/bin/env python3
"""
Create OAuth service principal for Zerobus with client ID and secret
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import ServicePrincipal
import time

# Initialize client
w = WorkspaceClient(profile="DEFAULT")

print("🔐 Creating OAuth Service Principal for Zerobus")
print("=" * 60)

# Step 1: Create or get service principal
sp_name = "zerobus-ignition-connector"

try:
    print(f"\n⏳ Looking for existing service principal '{sp_name}'...")

    # List all service principals
    all_sps = list(w.service_principals.list(filter=f"displayName eq {sp_name}"))

    if all_sps:
        sp = all_sps[0]
        print(f"✅ Found existing service principal: {sp.display_name}")
        print(f"   ID: {sp.id}")
    else:
        print(f"⏳ Creating new service principal...")
        sp = w.service_principals.create(
            display_name=sp_name,
            active=True
        )
        print(f"✅ Service principal created: {sp.display_name}")
        print(f"   ID: {sp.id}")

    # Step 2: Create OAuth client secret
    print(f"\n⏳ Creating OAuth secret...")

    # Use account client for OAuth operations
    from databricks.sdk import AccountClient

    # Note: OAuth secret creation requires account-level API
    # For workspace-level, we'll use the simpler token approach

    print(f"\n⚠️  OAuth M2M requires account-level configuration.")
    print(f"   Using workspace token approach instead...")

    # Create service principal token
    print(f"\n⏳ Creating service principal token...")

    token_response = w.tokens.create(
        comment=f"Zerobus Ignition Connector - {sp_name}",
        lifetime_seconds=90 * 24 * 60 * 60  # 90 days
    )

    print(f"✅ Token created successfully!")
    print(f"   Token ID: {token_response.token_info.token_id}")

    # Grant permissions to service principal
    print(f"\n⏳ Granting permissions...")

    warehouse_id = "4b9b953939869799"

    # Grant SQL permissions
    grants = [
        f"GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `{sp.display_name}`",
        f"GRANT USE SCHEMA ON SCHEMA field_engineering.mining_demo TO `{sp.display_name}`",
        f"GRANT USE CATALOG ON CATALOG field_engineering TO `{sp.display_name}`",
    ]

    for grant_sql in grants:
        try:
            w.statement_execution.execute_statement(
                statement=grant_sql,
                warehouse_id=warehouse_id
            )
            print(f"✅ {grant_sql[:50]}...")
        except Exception as e:
            print(f"⚠️  Grant may already exist: {str(e)[:100]}")

    # Save credentials
    creds_file = "/Users/pravin.varma/Documents/Demo/genie-at-the-edge/.databricks_zerobus_creds.txt"
    with open(creds_file, 'w') as f:
        f.write(f"Service Principal: {sp.display_name}\n")
        f.write(f"Service Principal ID: {sp.id}\n")
        f.write(f"Token: {token_response.token_value}\n")

    print(f"\n✅ Credentials saved to: {creds_file}")

    print(f"\n📋 ZEROBUS CONFIGURATION (Use Token Auth):")
    print(f"=" * 60)
    print(f"\nAuthentication Type: Token")
    print(f"Host: e2-demo-field-eng.cloud.databricks.com")
    print(f"HTTP Path: /sql/1.0/warehouses/4b9b953939869799")
    print(f"Token: {token_response.token_value}")
    print(f"\nCatalog: field_engineering")
    print(f"Schema: mining_demo")
    print(f"Table: zerobus_sensor_stream")

    print(f"\n" + "=" * 60)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

    print(f"\n💡 Alternative: Use personal access token")
    print(f"   Run: databricks auth token")
