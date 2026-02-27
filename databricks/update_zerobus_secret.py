#!/usr/bin/env python3
"""
Update Zerobus OAuth secret directly in the database
"""
import sqlite3
import shutil
from datetime import datetime

DB_PATH = "/tmp/ignition-backup/db_backup_sqlite.idb"
CORRECT_SECRET = "<OAUTH_CLIENT_SECRET>"
CLIENT_ID = "6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb"

print("🔧 Updating Zerobus OAuth Secret in Database")
print("=" * 70)

# Backup the database first
backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy(DB_PATH, backup_path)
print(f"✅ Backed up database to: {backup_path}")

# Connect and update
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check current value
cursor.execute("SELECT OAUTHCLIENTSECRET FROM ZEROBUSSETTINGS WHERE OAUTHCLIENTID=?", (CLIENT_ID,))
current_secret = cursor.fetchone()

if current_secret:
    print(f"\n📋 Current OAuth Secret: {current_secret[0][:50]}...")
    print(f"   Length: {len(current_secret[0])} characters")
else:
    print("\n⚠️  No record found!")
    conn.close()
    exit(1)

# Update the secret
print(f"\n⏳ Updating to new secret...")
cursor.execute(
    "UPDATE ZEROBUSSETTINGS SET OAUTHCLIENTSECRET=? WHERE OAUTHCLIENTID=?",
    (CORRECT_SECRET, CLIENT_ID)
)

conn.commit()
affected_rows = cursor.rowcount
print(f"✅ Updated {affected_rows} row(s)")

# Verify the update
cursor.execute("SELECT OAUTHCLIENTSECRET FROM ZEROBUSSETTINGS WHERE OAUTHCLIENTID=?", (CLIENT_ID,))
new_secret = cursor.fetchone()

if new_secret and new_secret[0] == CORRECT_SECRET:
    print(f"\n✅ Verification: Secret updated successfully!")
    print(f"   New secret: {new_secret[0]}")
    print(f"   Length: {len(new_secret[0])} characters")
else:
    print(f"\n❌ Verification failed!")

conn.close()

print("\n" + "=" * 70)
print("📋 Next Steps:")
print("=" * 70)
print("1. Stop Ignition container:")
print("   docker stop genie-at-edge-ignition")
print()
print("2. Copy updated database to container:")
print("   docker cp /tmp/ignition-backup/db_backup_sqlite.idb \\")
print("     genie-at-edge-ignition:/usr/local/bin/ignition/data/db/config.idb")
print()
print("3. Start Ignition container:")
print("   docker start genie-at-edge-ignition")
print()
print("4. Check logs for successful connection:")
print("   docker logs genie-at-edge-ignition -f | grep -i 'zerobus\\|oauth'")
