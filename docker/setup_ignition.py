#!/usr/bin/env python3
"""
Automated Ignition Gateway Setup Script
Configures UDTs, tags, and gateway scripts programmatically via REST API
"""

import json
import time
import base64
import requests
from pathlib import Path
from typing import Dict, List, Any

# Configuration
GATEWAY_URL = "http://localhost:8181"
USERNAME = "admin"
PASSWORD = "password"
IGNITION_BASE = Path(__file__).parent.parent / "ignition"

class IgnitionAPI:
    """Wrapper for Ignition Gateway REST API calls"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Basic {self.auth}',
            'Content-Type': 'application/json'
        })

    def wait_for_gateway(self, timeout: int = 60) -> bool:
        """Wait for gateway to be ready"""
        print(f"Waiting for gateway at {self.base_url}...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = self.session.get(f"{self.base_url}/system/gateway/status", timeout=5)
                if resp.status_code in [200, 302]:
                    print("Gateway is ready!")
                    return True
            except requests.RequestException:
                pass
            time.sleep(2)
        return False

    def import_tags(self, tag_json: Dict[str, Any], provider: str = "default") -> bool:
        """Import tags via REST API"""
        endpoint = f"{self.base_url}/data/tag-import"

        # Wrap in proper import structure
        import_data = {
            "tags": [tag_json]
        }

        try:
            resp = self.session.post(
                endpoint,
                json=import_data,
                params={"provider": provider}
            )
            if resp.status_code in [200, 201]:
                print(f"✓ Imported tag: {tag_json.get('name', 'Unknown')}")
                return True
            else:
                print(f"✗ Failed to import tag: {resp.status_code} - {resp.text}")
                return False
        except requests.RequestException as e:
            print(f"✗ Request failed: {e}")
            return False

    def create_gateway_script(self, name: str, script_code: str,
                            delay_ms: int = 1000, enabled: bool = True) -> bool:
        """Create gateway timer script"""
        endpoint = f"{self.base_url}/data/gateway-scripts"

        script_data = {
            "name": name,
            "scriptType": "timer",
            "script": script_code,
            "delay": delay_ms,
            "enabled": enabled
        }

        try:
            resp = self.session.post(endpoint, json=script_data)
            if resp.status_code in [200, 201]:
                print(f"✓ Created gateway script: {name}")
                return True
            else:
                print(f"✗ Failed to create script: {resp.status_code} - {resp.text}")
                return False
        except requests.RequestException as e:
            print(f"✗ Request failed: {e}")
            return False


def setup_via_designer_automation():
    """
    Setup using Ignition Designer automation (script console approach)
    This creates a script that can be run in the Gateway Script Console
    """
    print("\n" + "="*70)
    print("IGNITION SETUP AUTOMATION SCRIPT")
    print("="*70)

    # Read UDT definitions
    udt_files = [
        IGNITION_BASE / "udts" / "HaulTruck_UDT.json",
        IGNITION_BASE / "udts" / "Crusher_UDT.json",
        IGNITION_BASE / "udts" / "Conveyor_UDT.json"
    ]

    # Read gateway scripts
    physics_script = IGNITION_BASE / "scripts" / "mining_physics_simulation.py"
    fault_script = IGNITION_BASE / "scripts" / "fault_injection_cr002.py"
    tag_creation_script = IGNITION_BASE / "udts" / "create_tag_instances.py"

    print("\nGenerating automation scripts...\n")

    # Generate the complete setup script for Gateway Script Console
    setup_script = """# Ignition Gateway Setup Script
# Run this in: Config > Scripting > Script Console

import system.tag as tag
import system.util as util

print("Starting Ignition setup...")

# Step 1: Import UDT definitions
print("\\nStep 1: Importing UDT definitions...")

"""

    # Add UDT imports
    for udt_file in udt_files:
        if udt_file.exists():
            udt_data = json.loads(udt_file.read_text())
            udt_name = udt_data.get('name', udt_file.stem)
            setup_script += f"""
# Import {udt_name} UDT
udt_{udt_name.lower()}_json = '''{udt_file.read_text()}'''
tag.importTags(udt_{udt_name.lower()}_json, "default")
print("  Imported {udt_name} UDT")
"""

    # Add tag instance creation
    if tag_creation_script.exists():
        setup_script += f"""

# Step 2: Create tag instances
print("\\nStep 2: Creating tag instances...")
{tag_creation_script.read_text()}
"""

    # Save the complete setup script
    output_file = IGNITION_BASE.parent / "docker" / "gateway_setup_script.py"
    output_file.write_text(setup_script)

    print(f"✓ Generated setup script: {output_file}")

    # Generate instructions
    instructions = f"""
================================================================================
MANUAL SETUP INSTRUCTIONS
================================================================================

Since Ignition Gateway REST API has limited tag import capabilities,
follow these steps to complete the setup:

STEP 1: Access Gateway Configuration
-------------------------------------
1. Open browser: {GATEWAY_URL}
2. Login with: {USERNAME} / {PASSWORD}
3. Click "Config" tab

STEP 2: Import UDT Definitions
-------------------------------
1. Go to: Tags > Tag Browser
2. Click: "Import Tags" button
3. Import each UDT file:
   - {udt_files[0]}
   - {udt_files[1]}
   - {udt_files[2]}

STEP 3: Create Tag Instances
-----------------------------
1. Go to: Config > Scripting > Script Console
2. Copy contents from: {tag_creation_script}
3. Paste into Script Console
4. Click "Run Script"
5. Verify output shows 107 tags created

STEP 4: Deploy Physics Simulation Script
-----------------------------------------
1. Go to: Config > Scripting > Gateway Timer Scripts
2. Click "Add New Timer Script"
3. Configure:
   Name: MiningPhysicsSimulation
   Delay: 1000 ms (Fixed Rate)
   Enabled: Yes
4. Copy contents from: {physics_script}
5. Paste into script editor
6. Click "Save"

STEP 5: Deploy Fault Injection Script (Optional)
-------------------------------------------------
1. Go to: Config > Scripting > Gateway Timer Scripts
2. Click "Add New Timer Script"
3. Configure:
   Name: FaultInjectionCR002
   Delay: 1000 ms (Fixed Rate)
   Enabled: No (enable when ready for demo)
4. Copy contents from: {fault_script}
5. Paste into script editor
6. Click "Save"

STEP 6: Verify Tag Updates
---------------------------
1. Go to: Tags > Tag Browser
2. Expand: default provider
3. Check tags are updating (every 1 second)
4. Verify haul trucks cycling through states

QUICK SETUP (Using Script Console):
------------------------------------
1. Go to: Config > Scripting > Script Console
2. Open generated script: {output_file}
3. Copy entire contents
4. Paste into Script Console
5. Click "Run Script"
6. Manually add Timer Scripts (Steps 4 & 5 above)

================================================================================
"""

    instructions_file = IGNITION_BASE.parent / "docker" / "SETUP_INSTRUCTIONS.txt"
    instructions_file.write_text(instructions)

    print(f"✓ Generated instructions: {instructions_file}")
    print(instructions)

    return True


def upload_ui_to_databricks():
    """Upload Genie chat UI to Databricks Files"""
    print("\n" + "="*70)
    print("DATABRICKS UI UPLOAD")
    print("="*70)

    ui_file = IGNITION_BASE.parent / "ui" / "genie_chat_perspective.html"

    if not ui_file.exists():
        print(f"✗ UI file not found: {ui_file}")
        return False

    print(f"\nTo upload the Genie chat UI to Databricks:")
    print(f"1. Open Databricks workspace")
    print(f"2. Go to: Workspace > Create > Upload Files")
    print(f"3. Upload: {ui_file}")
    print(f"4. Note the file path (e.g., /Workspace/Users/<email>/genie_chat_perspective.html)")
    print(f"5. Update perspective_view_spec.json with the Databricks file URL")

    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("GENIE AT THE EDGE - IGNITION SETUP AUTOMATION")
    print("="*70)

    # Check if gateway is accessible
    api = IgnitionAPI(GATEWAY_URL, USERNAME, PASSWORD)

    if not api.wait_for_gateway():
        print("\n✗ Gateway not accessible. Make sure Docker container is running:")
        print("  cd docker && docker-compose up -d")
        exit(1)

    print("\n✓ Gateway is accessible")

    # Generate setup scripts and instructions
    setup_via_designer_automation()

    # Upload UI instructions
    upload_ui_to_databricks()

    print("\n" + "="*70)
    print("SETUP SCRIPT GENERATION COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Follow instructions in: docker/SETUP_INSTRUCTIONS.txt")
    print("2. Import UDTs via Designer")
    print("3. Run tag creation script in Script Console")
    print("4. Deploy gateway timer scripts")
    print("5. Verify tags are updating")
    print("\nEstimated time: 15-20 minutes")
    print("="*70 + "\n")
