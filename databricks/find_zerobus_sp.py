#!/usr/bin/env python3
"""
Find Zerobus service principals
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(profile="DEFAULT")

print("🔍 Finding Zerobus Service Principals")
print("=" * 70)

try:
    # List all service principals
    all_sps = list(w.service_principals.list())
    print(f"\n📋 Total service principals: {len(all_sps)}")

    # Filter for Zerobus-related SPs
    zerobus_sps = [sp for sp in all_sps
                   if sp.display_name and 'zerobus' in sp.display_name.lower()]

    if zerobus_sps:
        print(f"\n✅ Found {len(zerobus_sps)} Zerobus service principal(s):\n")
        for sp in zerobus_sps:
            print(f"   Name: {sp.display_name}")
            print(f"   ID: {sp.id}")
            print(f"   Application ID: {sp.application_id}")
            print(f"   Active: {sp.active}")
            print()
    else:
        print("\n⚠️  No Zerobus service principals found. Showing all SPs:\n")
        for sp in all_sps[:10]:
            print(f"   Name: {sp.display_name}")
            print(f"   ID: {sp.id}")
            print()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
