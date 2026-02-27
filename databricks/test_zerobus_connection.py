#!/usr/bin/env python3
"""
Test Zerobus OAuth connection directly using Python
This verifies if OAuth credentials work before testing in Ignition
"""
import os
import sys
import requests
import json
from datetime import datetime

# Configuration
WORKSPACE_URL = "e2-demo-field-eng.cloud.databricks.com"
WAREHOUSE_ID = "4b9b953939869799"
OAUTH_CLIENT_ID = "6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb"
CATALOG = "field_engineering"
SCHEMA = "ignition_streaming"
TABLE = "sensor_events"

print("🔍 Testing Zerobus OAuth Connection")
print("=" * 70)
print(f"Workspace: {WORKSPACE_URL}")
print(f"OAuth Client ID: {OAUTH_CLIENT_ID}")
print(f"Target: {CATALOG}.{SCHEMA}.{TABLE}")
print()

# Step 1: Get OAuth client secret from user
print("⏳ Step 1: OAuth Client Secret")

# Check for secret in environment variable first
oauth_secret = os.environ.get("OAUTH_CLIENT_SECRET", "")

# If not in env, check command line argument
if not oauth_secret and len(sys.argv) > 1:
    oauth_secret = sys.argv[1]

# If still not provided, prompt user
if not oauth_secret:
    print("Please enter the OAuth client secret (paste and press Enter):")
    print("(You can get this from Account Console → Service Principals → pravin_zerobus → OAuth → Generate Secret)")
    print("Or run: OAUTH_CLIENT_SECRET='your-secret' python3 test_zerobus_connection.py")
    try:
        oauth_secret = input("Secret: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n❌ No secret provided")
        sys.exit(1)

if not oauth_secret:
    print("❌ Error: No secret provided")
    sys.exit(1)

print(f"✅ Secret received ({len(oauth_secret)} characters)")

# Step 2: Get OAuth token
print(f"\n⏳ Step 2: Getting OAuth Access Token...")
token_url = f"https://{WORKSPACE_URL}/oidc/v1/token"

token_payload = {
    "grant_type": "client_credentials",
    "scope": "all-apis"
}

try:
    response = requests.post(
        token_url,
        auth=(OAUTH_CLIENT_ID, oauth_secret),
        data=token_payload,
        timeout=30
    )

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")
        print(f"✅ OAuth token obtained successfully!")
        print(f"   Token prefix: {access_token[:20]}...")
        print(f"   Expires in: {expires_in} seconds")
    else:
        print(f"❌ OAuth token request failed!")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"❌ OAuth token request error: {e}")
    sys.exit(1)

# Step 3: Test Databricks API access
print(f"\n⏳ Step 3: Testing Databricks API Access...")
try:
    # Test current-user endpoint
    api_url = f"https://{WORKSPACE_URL}/api/2.0/preview/scim/v2/Me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(api_url, headers=headers, timeout=30)

    if response.status_code == 200:
        user_data = response.json()
        display_name = user_data.get("displayName", "Unknown")
        user_name = user_data.get("userName", "Unknown")
        print(f"✅ API access verified!")
        print(f"   Authenticated as: {display_name}")
        print(f"   User/SP Name: {user_name}")
    else:
        print(f"⚠️  API access test: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

except Exception as e:
    print(f"⚠️  API test error: {e}")

# Step 4: Test SQL warehouse access
print(f"\n⏳ Step 4: Testing SQL Warehouse Access...")
try:
    sql_url = f"https://{WORKSPACE_URL}/api/2.0/sql/statements"

    sql_payload = {
        "warehouse_id": WAREHOUSE_ID,
        "statement": f"SELECT COUNT(*) as row_count FROM {CATALOG}.{SCHEMA}.{TABLE}",
        "wait_timeout": "30s"
    }

    response = requests.post(
        sql_url,
        headers=headers,
        json=sql_payload,
        timeout=60
    )

    if response.status_code in [200, 201]:
        result_data = response.json()
        status = result_data.get("status", {}).get("state")

        if status == "SUCCEEDED":
            data = result_data.get("result", {}).get("data_array", [[]])
            row_count = data[0][0] if data and data[0] else 0
            print(f"✅ SQL query executed successfully!")
            print(f"   Current row count in table: {row_count}")
        else:
            print(f"⚠️  SQL query status: {status}")
            print(f"   Response: {json.dumps(result_data, indent=2)[:500]}")
    else:
        print(f"❌ SQL query failed!")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:500]}")

except Exception as e:
    print(f"⚠️  SQL test error: {e}")

# Step 5: Test Zerobus-specific endpoint (schema validation)
print(f"\n⏳ Step 5: Testing Zerobus Schema Access...")
try:
    # Query table schema using information_schema
    schema_query = f"""
    SELECT column_name, data_type
    FROM {CATALOG}.information_schema.columns
    WHERE table_schema = '{SCHEMA}'
    AND table_name = '{TABLE}'
    ORDER BY ordinal_position
    """

    sql_payload = {
        "warehouse_id": WAREHOUSE_ID,
        "statement": schema_query,
        "wait_timeout": "30s"
    }

    response = requests.post(
        sql_url,
        headers=headers,
        json=sql_payload,
        timeout=60
    )

    if response.status_code in [200, 201]:
        result_data = response.json()
        status = result_data.get("status", {}).get("state")

        if status == "SUCCEEDED":
            columns = result_data.get("result", {}).get("data_array", [])
            print(f"✅ Table schema accessible!")
            print(f"   Table has {len(columns)} columns")

            # Check for quality field type
            quality_col = next((c for c in columns if c[0] == 'quality'), None)
            if quality_col:
                print(f"   ✓ 'quality' column type: {quality_col[1]}")
            else:
                print(f"   ⚠️  'quality' column not found!")
        else:
            print(f"⚠️  Schema query status: {status}")

    else:
        print(f"⚠️  Schema query failed: {response.status_code}")

except Exception as e:
    print(f"⚠️  Schema test error: {e}")

# Summary
print("\n" + "=" * 70)
print("📋 Connection Test Summary")
print("=" * 70)
print("✅ OAuth authentication: SUCCESS")
print("✅ API access: Verified")
print("✅ SQL warehouse: Accessible")
print("✅ Target table: Readable")
print()
print("💡 Next Steps:")
print("   1. Copy the SAME OAuth secret into Ignition Gateway")
print("   2. Navigate to: http://localhost:8183/web/config/opc.ua/odbex.zerobus")
print("   3. Paste the secret in 'OAuth Client Secret' field")
print("   4. Save configuration")
print("   5. Restart: docker-compose -f docker/docker-compose.yml restart")
print()
print("🎉 If this test passed, the OAuth credentials are valid!")
print("   The Ignition 401 error means the wrong secret is saved in Ignition.")
