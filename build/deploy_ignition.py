#!/usr/bin/env python3
"""
Mining Operations Genie Demo - Ignition Deployment Automation
Deploys UDTs, tag instances, scripts, and Perspective views
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml

try:
    import requests
    from requests.auth import HTTPBasicAuth
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.panel import Panel
except ImportError as e:
    print(f"Error: Missing required dependencies. Run: pip install -r requirements.txt")
    print(f"Details: {e}")
    sys.exit(1)

console = Console()


class IgnitionDeployer:
    """Handles deployment of all Ignition components"""

    def __init__(self, config_path: str = "environment_config.yaml", environment: str = "dev"):
        """Initialize deployer with configuration"""
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.gateway_url: Optional[str] = None
        self.session: Optional[requests.Session] = None
        self.deployment_state: Dict[str, Any] = {}

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = self.project_root / "build" / config_path
        if not config_file.exists():
            console.print(f"[red]Error: Configuration file not found: {config_file}[/red]")
            sys.exit(1)

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def initialize_connection(self) -> None:
        """Initialize connection to Ignition Gateway"""
        console.print("[yellow]Initializing Ignition connection...[/yellow]")

        ignition_config = self.config["ignition"][self.environment]
        self.gateway_url = ignition_config["gateway_url"]

        # Get credentials from environment
        username = os.environ.get("IGNITION_USERNAME", "admin")
        password = os.environ.get("IGNITION_PASSWORD", "password")

        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({"Content-Type": "application/json"})

        # Test connection (simplified - actual Ignition API varies)
        try:
            response = self.session.get(f"{self.gateway_url}/StatusPing", timeout=5)
            if response.status_code == 200:
                console.print(f"[green]✓ Connected to Ignition Gateway: {self.gateway_url}[/green]")
            else:
                console.print(f"[yellow]Warning: Connection test returned status {response.status_code}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not verify connection: {e}[/yellow]")
            console.print("[yellow]Proceeding with manual deployment instructions...[/yellow]")

    def deploy_udts(self) -> bool:
        """Deploy UDT definitions"""
        console.print("\n[bold blue]Deploying UDTs[/bold blue]")

        udts_dir = self.project_root / "ignition" / "udts"
        udt_files = list(udts_dir.glob("*_UDT.json"))

        if not udt_files:
            console.print(f"[red]Error: No UDT files found in {udts_dir}[/red]")
            return False

        console.print(f"[cyan]Found {len(udt_files)} UDT definitions:[/cyan]")
        for udt_file in udt_files:
            console.print(f"  - {udt_file.name}")

        console.print(f"""
[yellow]Manual Deployment Required:[/yellow]

Ignition UDTs must be imported through the Designer:

1. Open Ignition Designer
2. Navigate to: Tag Browser > Data Types
3. Right-click > Import > JSON
4. Import each UDT file from: {udts_dir}/

UDT Files to import:
        """)

        for udt_file in udt_files:
            console.print(f"  - {udt_file.name}")

        console.print("""
5. After import, verify UDTs appear in Data Types folder
6. Proceed to create tag instances using: create_tag_instances.py

[cyan]Alternatively, use the Python script:[/cyan]
  cd ignition/udts
  python create_tag_instances.py
        """)

        self.deployment_state["udts"] = "manual"
        return True

    def deploy_scripts(self) -> bool:
        """Deploy Gateway scripts"""
        console.print("\n[bold blue]Deploying Gateway Scripts[/bold blue]")

        scripts_dir = self.project_root / "ignition" / "scripts"
        script_files = [
            ("mining_physics_simulation.py", "Physics Simulation", 1000),
            ("fault_injection_cr002.py", "Fault Injection", 1000)
        ]

        console.print(f"""
[yellow]Manual Deployment Required:[/yellow]

Gateway scripts must be configured through the Gateway webpage:

1. Open Gateway webpage: {self.gateway_url}
2. Navigate to: Config > Scripting > Gateway Event Scripts
3. Create new Gateway Timer Scripts for each:

        """)

        for script_file, script_name, interval in script_files:
            full_path = scripts_dir / script_file
            if full_path.exists():
                console.print(f"""
[cyan]{script_name}:[/cyan]
  - Name: {script_name}
  - File: {scripts_dir}/{script_file}
  - Script Type: Gateway Timer Script
  - Interval: {interval}ms
  - Enabled: Yes

  Copy script content from file and paste into Gateway script editor.
                """)

        console.print("""
[cyan]Quick Reference:[/cyan]
  - Full deployment guide: ignition/scripts/deployment_guide.md
  - Testing procedures: ignition/scripts/README.md
        """)

        self.deployment_state["scripts"] = "manual"
        return True

    def deploy_perspective_view(self) -> bool:
        """Deploy Perspective view"""
        console.print("\n[bold blue]Deploying Perspective View[/bold blue]")

        view_spec = self.project_root / "ui" / "perspective_view_spec.json"

        if not view_spec.exists():
            console.print(f"[yellow]Warning: View specification not found: {view_spec}[/yellow]")
            return True

        console.print(f"""
[yellow]Manual Deployment Required:[/yellow]

Perspective view must be created through the Designer:

1. Open Ignition Designer
2. Create new Perspective project (if not exists): MiningOperations
3. Create new View: MiningOperationsDashboard
4. Design view layout based on specification: {view_spec}

[cyan]View Structure:[/cyan]
  - Header: Status indicators and title
  - Left Panel: Equipment status cards (70% width)
  - Right Panel: Genie chat iframe (30% width)
  - Bottom: Alarm table with "Ask AI" buttons

[cyan]Key Components:[/cyan]
  - Embedded Frame for chat UI (URL from UI deployment)
  - Custom properties for Databricks configuration
  - Alarm action buttons with onClick scripts
  - Real-time tag bindings for equipment status

[cyan]Detailed Guide:[/cyan]
  - See: ui/deployment_guide.md
  - View spec: ui/perspective_view_spec.json
        """)

        self.deployment_state["perspective_view"] = "manual"
        return True

    def deploy_zerobus_configuration(self) -> bool:
        """Configure Zerobus streaming to Databricks"""
        console.print("\n[bold blue]Configuring Zerobus Streaming[/bold blue]")

        console.print(f"""
[yellow]Manual Configuration Required:[/yellow]

Configure Zerobus module through Gateway:

1. Open Gateway webpage: {self.gateway_url}
2. Navigate to: Config > Zerobus (your streaming module)
3. Configure connection:

[cyan]Databricks Connection:[/cyan]
  - Workspace URL: {self.config['databricks'][self.environment]['workspace_url']}
  - Token: (from DATABRICKS_TOKEN environment variable)
  - Stream Name: mining_ot_stream
  - Target Table: field_engineering.mining_demo.ot_telemetry_bronze

[cyan]Tag Selection:[/cyan]
  - Tag Provider: [default]
  - Tag Path: Mining/Equipment/**/*
  - Include all child tags

[cyan]Streaming Settings:[/cyan]
  - Batch Size: 50 tags
  - Interval: 500ms
  - Buffer Size: 1000 records
  - Compression: Enabled

[cyan]Data Format:[/cyan]
  - Format: JSON
  - Include timestamp: Yes
  - Include quality: Yes
  - Include tag path: Yes

4. Enable streaming and save configuration
5. Monitor Gateway logs for successful connection
6. Verify data flow in Databricks bronze table

[cyan]Validation Query (run in Databricks):[/cyan]
  SELECT COUNT(*)
  FROM field_engineering.mining_demo.ot_telemetry_bronze
  WHERE timestamp > current_timestamp() - INTERVAL 5 MINUTES;

[yellow]Expected result: Hundreds of records within 2-3 minutes[/yellow]
        """)

        self.deployment_state["zerobus"] = "manual"
        return True

    def run_validation(self) -> bool:
        """Run validation tests"""
        console.print("\n[bold blue]Running Validation[/bold blue]")

        validation_script = self.project_root / "ignition" / "udts" / "validation_tests.py"

        if validation_script.exists():
            console.print(f"""
[cyan]Run validation tests:[/cyan]

  cd ignition/udts
  python validation_tests.py

This will verify:
  - UDT structures are correct
  - Tag instances exist
  - Scripts are generating data
  - Values are within expected ranges
            """)
        else:
            console.print("[yellow]Validation script not found[/yellow]")

        return True

    def create_deployment_checklist(self) -> None:
        """Create deployment checklist"""
        checklist_file = self.project_root / "build" / f"ignition_deployment_checklist_{self.environment}.md"

        checklist_content = f"""# Ignition Deployment Checklist - {self.environment.upper()}

Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}

## Pre-Deployment

- [ ] Ignition Gateway accessible: {self.gateway_url}
- [ ] Admin credentials available
- [ ] Designer installed and connected
- [ ] Gateway licenses valid
- [ ] Perspective module enabled

## UDT Deployment

- [ ] Import HaulTruck_UDT.json
- [ ] Import Crusher_UDT.json
- [ ] Import Conveyor_UDT.json
- [ ] Verify UDTs in Data Types folder
- [ ] Create tag provider: [default]

## Tag Instance Creation

- [ ] Create Mining/Equipment folder
- [ ] Create 5 HaulTruck instances (HT_001 to HT_005)
- [ ] Create 3 Crusher instances (CR_001 to CR_003)
- [ ] Create 2 Conveyor instances (CV_001, CV_002)
- [ ] Verify all tags visible in Tag Browser
- [ ] Total tags created: 105 (15 equipment × 7 avg tags)

## Alarm Configuration

- [ ] Configure high vibration alarm for CR_001 (threshold: >40 mm/s)
- [ ] Configure high vibration alarm for CR_002 (threshold: >40 mm/s)
- [ ] Configure high vibration alarm for CR_003 (threshold: >40 mm/s)
- [ ] Test alarm by setting vibration to 45 mm/s
- [ ] Verify alarm fires and appears in alarm journal

## Gateway Scripts

- [ ] Create Gateway Timer Script: Physics Simulation
  - Interval: 1000ms
  - Script content from: ignition/scripts/mining_physics_simulation.py
- [ ] Create Gateway Timer Script: Fault Injection
  - Interval: 1000ms
  - Script content from: ignition/scripts/fault_injection_cr002.py
- [ ] Enable both scripts
- [ ] Verify scripts running in Gateway logs
- [ ] Monitor tags updating in Tag Browser

## Zerobus Streaming

- [ ] Install Zerobus module (if not already installed)
- [ ] Create Databricks connection
- [ ] Configure stream: mining_ot_stream
- [ ] Set tag selection: Mining/Equipment/**/*
- [ ] Set batch size: 50, interval: 500ms
- [ ] Enable streaming
- [ ] Verify data in Databricks bronze table

## Perspective Project

- [ ] Create project: MiningOperations
- [ ] Set as Perspective project
- [ ] Configure authentication (if needed)
- [ ] Create session custom properties

## Perspective View

- [ ] Create view: MiningOperationsDashboard
- [ ] Add header container
- [ ] Add equipment status cards (left panel)
- [ ] Add chat iframe (right panel)
- [ ] Configure iframe URL (from UI deployment)
- [ ] Add alarm table
- [ ] Add "Ask AI" action buttons
- [ ] Configure tag bindings
- [ ] Test view in session

## Validation

- [ ] Run validation_tests.py
- [ ] Verify tag values updating every second
- [ ] Verify HaulTruck cycle behavior (5 min cycle)
- [ ] Verify CR_002 fault injection (after 30 min)
- [ ] Check Gateway logs for errors
- [ ] Monitor CPU/memory usage
- [ ] Verify data flowing to Databricks

## Integration Testing

- [ ] Open Perspective session
- [ ] Verify equipment status displays
- [ ] Verify chat UI loads in iframe
- [ ] Test "Ask AI" button functionality
- [ ] Verify alarm notifications
- [ ] Test end-to-end latency (tag change → Genie response)

## Documentation

- [ ] Update deployment_guide.md with any deviations
- [ ] Document configuration changes
- [ ] Record any issues encountered
- [ ] Save deployment state

## Sign-off

- Deployed by: _______________
- Date: _______________
- Environment: {self.environment.upper()}
- Notes: _______________

"""

        with open(checklist_file, 'w') as f:
            f.write(checklist_content)

        console.print(f"\n[green]✓ Deployment checklist created: {checklist_file}[/green]")

    def deploy_all(self) -> bool:
        """Deploy all Ignition components"""
        console.print(Panel.fit(
            f"[bold green]Mining Operations Genie Demo[/bold green]\n"
            f"Ignition Deployment - Environment: {self.environment.upper()}",
            border_style="green"
        ))

        # Initialize connection
        self.initialize_connection()

        # Deploy components (mostly manual instructions)
        steps = [
            ("UDTs", self.deploy_udts),
            ("Gateway Scripts", self.deploy_scripts),
            ("Perspective View", self.deploy_perspective_view),
            ("Zerobus Configuration", self.deploy_zerobus_configuration),
            ("Validation", self.run_validation)
        ]

        for step_name, step_func in steps:
            try:
                if not step_func():
                    console.print(f"\n[red]✗ Failed at step: {step_name}[/red]")
                    return False
            except Exception as e:
                console.print(f"\n[red]✗ Error in {step_name}: {e}[/red]")
                return False

        # Create checklist
        self.create_deployment_checklist()

        # Summary
        console.print(Panel.fit(
            "[bold green]Ignition Deployment Instructions Generated![/bold green]\n\n"
            "Next steps:\n"
            "1. Follow deployment checklist created above\n"
            "2. Import UDTs through Designer\n"
            "3. Create tag instances\n"
            "4. Deploy Gateway scripts\n"
            "5. Configure Zerobus streaming\n"
            "6. Create Perspective view\n\n"
            "[yellow]Note: Most steps require manual configuration through Ignition UI[/yellow]",
            border_style="green"
        ))

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy Ignition components")
    parser.add_argument(
        "--environment",
        choices=["dev", "prod"],
        default="dev",
        help="Deployment environment"
    )

    args = parser.parse_args()

    deployer = IgnitionDeployer(environment=args.environment)
    success = deployer.deploy_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
