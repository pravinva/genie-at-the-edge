#!/usr/bin/env python3
"""
Create a service principal token for Zerobus with proper permissions
"""
from databricks.sdk import WorkspaceClient
import json

# Initialize client
w = WorkspaceClient(profile="DEFAULT")

print("🔐 Creating Zerobus Service Principal Token")
print("=" * 60)

# Get current user info
user = w.current_user.me()
print(f"✓ Current user: {user.user_name}")

# Create token for Zerobus
print("\n⏳ Creating token...")

try:
    # Create token with 90 days lifetime
    token_response = w.tokens.create(
        comment="Ignition Zerobus Connector",
        lifetime_seconds=90 * 24 * 60 * 60  # 90 days
    )

    print(f"✅ Token created successfully!")
    print(f"\n🔑 Token Details:")
    print(f"   Token ID: {token_response.token_info.token_id}")
    print(f"   Comment: {token_response.token_info.comment}")
    print(f"   Created: {token_response.token_info.creation_time}")

    # Save token to file for easy access
    token_file = "/Users/pravin.varma/Documents/Demo/genie-at-the-edge/.databricks_zerobus_token"
    with open(token_file, 'w') as f:
        f.write(token_response.token_value)

    print(f"\n✅ Token saved to: {token_file}")

    print(f"\n📋 ZEROBUS CONFIGURATION:")
    print(f"=" * 60)
    print(f"\n1. Open Ignition Gateway Web Interface:")
    print(f"   URL: http://localhost:8183")
    print(f"   Username: admin")
    print(f"   Password: password")

    print(f"\n2. Navigate to:")
    print(f"   Config → Zerobus → Connections")

    print(f"\n3. Update/Create Connection:")
    print(f"   Host: e2-demo-field-eng.cloud.databricks.com")
    print(f"   HTTP Path: /sql/1.0/warehouses/4b9b953939869799")
    print(f"   Token: {token_response.token_value}")
    print(f"   Catalog: field_engineering")
    print(f"   Schema: mining_demo")
    print(f"   Table: zerobus_sensor_stream")

    print(f"\n4. Test Connection (should show SUCCESS)")

    print(f"\n5. Save and Enable the connection")

    print(f"\n" + "=" * 60)
    print(f"✅ Token is ready! Update Zerobus config with this token.")

except Exception as e:
    print(f"❌ Error creating token: {e}")
    print(f"\n💡 Alternative: Use existing token from:")
    print(f"   databricks auth token")
    exit(1)
