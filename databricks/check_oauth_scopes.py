#!/usr/bin/env python3
"""
Check OAuth scopes for service principal
"""
from databricks.sdk import WorkspaceClient
import requests

w = WorkspaceClient(profile="DEFAULT")
sp_app_id = "6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb"

print("🔍 Checking OAuth Scopes for pravin_zerobus")
print("=" * 70)

# Get service principal details
try:
    all_sps = w.service_principals.list(filter=f'displayName eq pravin_zerobus')
    sp_list = list(all_sps)

    if sp_list:
        sp = sp_list[0]
        print(f"✅ Service Principal: {sp.display_name}")
        print(f"   ID: {sp.id}")
        print(f"   Application ID: {sp.application_id}")
        print(f"   Active: {sp.active}")
    else:
        print("❌ Service principal not found")
        exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Try to get OAuth app details via Account API
print(f"\n⏳ Checking OAuth configuration...")
print(f"\n⚠️  Note: OAuth scopes are managed in Account Console")
print(f"   Go to: Account Console → User Management → Service Principals → pravin_zerobus → OAuth")
print(f"\n📋 Required Scopes for Zerobus:")
print(f"   ✓ all-apis (recommended)")
print(f"   OR")
print(f"   ✓ sql (minimum for Zerobus streaming)")
print(f"\n💡 How to check/add scopes:")
print(f"   1. Open Account Console (https://accounts.cloud.databricks.com)")
print(f"   2. Navigate to User Management → Service Principals")
print(f"   3. Click on 'pravin_zerobus'")
print(f"   4. Go to OAuth tab")
print(f"   5. Check 'Scopes' section - should show 'all-apis' or 'sql'")
print(f"   6. If missing, click 'Edit' and add 'all-apis' scope")
print(f"   7. Save changes")
print(f"\n🔑 OAuth Configuration Summary:")
print(f"   Client ID: {sp_app_id}")
print(f"   Secret: <OAUTH_CLIENT_SECRET>")
print(f"   Required Scope: all-apis")

print("\n" + "=" * 70)
print("💡 If scopes are correct and secret is correct:")
print("   The issue might be with HOW Ignition is sending the OAuth request")
print("   - Check if Ignition is using a different workspace URL")
print("   - Verify the account and workspace are correctly linked")
