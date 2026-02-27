#!/usr/bin/env python3
"""
Check Ignition Gateway configuration via API
"""
import requests
from requests.auth import HTTPBasicAuth
import json

GATEWAY_URL = "http://localhost:8183"
# Default Ignition admin credentials (might need to be changed)
USERNAME = "admin"
PASSWORD = "password"

print("🔍 Checking Ignition Gateway Configuration")
print("=" * 70)

# Step 1: Check if Gateway API is accessible
print("\n⏳ Step 1: Testing Gateway API access...")
try:
    # Try to get system info
    response = requests.get(
        f"{GATEWAY_URL}/system/gwinfo",
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        timeout=5
    )

    if response.status_code == 200:
        print("✅ Gateway API accessible")
        info = response.json()
        print(f"   Gateway Version: {info.get('version', 'unknown')}")
    elif response.status_code == 401:
        print("⚠️  Gateway API requires authentication")
        print("   Default credentials might not work")
    else:
        print(f"⚠️  Gateway API returned: {response.status_code}")
except Exception as e:
    print(f"⚠️  Gateway API not accessible: {e}")

# Step 2: Try to access module configuration
print("\n⏳ Step 2: Checking for Zerobus module configuration...")
endpoints_to_try = [
    "/system/modules",
    "/data/config",
    "/config/modules",
    "/system/config",
]

for endpoint in endpoints_to_try:
    try:
        response = requests.get(
            f"{GATEWAY_URL}{endpoint}",
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=5
        )
        if response.status_code == 200:
            print(f"✅ Found endpoint: {endpoint}")
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:500]}")
            except:
                print(f"   Response (text): {response.text[:200]}")
        else:
            print(f"⚠️  {endpoint} -> {response.status_code}")
    except Exception as e:
        print(f"⚠️  {endpoint} -> {str(e)[:50]}")

# Step 3: Check for config files directly
print("\n⏳ Step 3: Checking for Zerobus configuration files...")
print("   Looking in Ignition data directory...")

print("\n" + "=" * 70)
print("💡 Alternative Approach: Direct Database Query")
print("=" * 70)
print("The Zerobus configuration is stored in Ignition's internal database.")
print("We can try to export it using Ignition's gateway backup feature.")
print()
print("Via Docker:")
print("  1. Export config: docker exec genie-at-edge-ignition \\")
print("       gwcmd --backup /tmp/backup.gwbk")
print("  2. Copy backup: docker cp genie-at-edge-ignition:/tmp/backup.gwbk ./")
print("  3. Extract (it's a zip file) and inspect")
print()
print("Or restart with verbose logging:")
print("  docker-compose -f docker/docker-compose.yml restart")
print("  docker logs genie-at-edge-ignition -f | grep -i 'zerobus.*config\\|oauth.*config'")
