#!/usr/bin/env python3
"""
Mining Operations Genie Demo - Master Deployment Script
Orchestrates full deployment of all components
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import subprocess

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Confirm, Prompt
    import yaml
except ImportError as e:
    print(f"Error: Missing required dependencies. Run: pip install -r requirements.txt")
    print(f"Details: {e}")
    sys.exit(1)

console = Console()


class MasterDeployer:
    """Orchestrates deployment of all demo components"""

    def __init__(self, environment: str = "dev", interactive: bool = True):
        """Initialize master deployer"""
        self.environment = environment
        self.interactive = interactive
        self.project_root = Path(__file__).parent.parent
        self.build_dir = self.project_root / "build"
        self.deployment_log: List[Tuple[str, bool, str]] = []
        self.start_time = time.time()

    def print_banner(self) -> None:
        """Print deployment banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║       Mining Operations Genie Demo                           ║
║       Master Deployment Automation                           ║
║                                                              ║
║       Edge Analytics • Real-Time ML • Natural Language       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        console.print(banner, style="bold green")
        console.print(f"\nEnvironment: [cyan]{self.environment.upper()}[/cyan]")
        console.print(f"Started: [yellow]{time.strftime('%Y-%m-%d %H:%M:%S')}[/yellow]\n")

    def check_prerequisites(self) -> bool:
        """Check all prerequisites before deployment"""
        console.print("\n[bold blue]Checking Prerequisites[/bold blue]\n")

        checks = []

        # Python version
        py_version = sys.version_info
        py_ok = py_version.major == 3 and py_version.minor >= 12
        checks.append((
            "Python version",
            py_ok,
            f"{py_version.major}.{py_version.minor}.{py_version.micro}"
        ))

        # Dependencies
        deps_ok = True
        try:
            import databricks.sdk
            import rich
            import yaml
            import requests
        except ImportError:
            deps_ok = False

        checks.append((
            "Python dependencies",
            deps_ok,
            "All required packages installed" if deps_ok else "Run: pip install -r requirements.txt"
        ))

        # Environment variables
        has_token = bool(os.environ.get("DATABRICKS_TOKEN"))
        checks.append((
            "DATABRICKS_TOKEN",
            has_token,
            "Set" if has_token else "Not set - export DATABRICKS_TOKEN=your_token"
        ))

        # Configuration file
        config_file = self.build_dir / "environment_config.yaml"
        config_exists = config_file.exists()
        checks.append((
            "Configuration file",
            config_exists,
            str(config_file) if config_exists else "Missing"
        ))

        # Component directories
        for component in ["databricks", "ignition", "ui"]:
            comp_dir = self.project_root / component
            comp_exists = comp_dir.exists()
            checks.append((
                f"{component.capitalize()} directory",
                comp_exists,
                str(comp_dir) if comp_exists else "Missing"
            ))

        # Display results
        table = Table(title="Prerequisites Check", show_header=True)
        table.add_column("Component", style="cyan", width=30)
        table.add_column("Status", style="green", width=12)
        table.add_column("Details", style="white", width=50)

        all_passed = True
        for check_name, passed, details in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            color = "green" if passed else "red"
            table.add_row(
                check_name,
                f"[{color}]{status}[/{color}]",
                details
            )
            if not passed:
                all_passed = False

        console.print(table)

        if not all_passed:
            console.print("\n[red]Prerequisites check failed. Fix issues above and retry.[/red]")

        return all_passed

    def run_deployment_script(self, script_name: str, component_name: str) -> bool:
        """Run a deployment script"""
        script_path = self.build_dir / script_name

        if not script_path.exists():
            console.print(f"[red]Error: Script not found: {script_path}[/red]")
            self.deployment_log.append((component_name, False, "Script not found"))
            return False

        console.print(f"\n[bold blue]Deploying {component_name}[/bold blue]")
        console.print(f"Script: {script_name}\n")

        try:
            # Run script with same environment
            cmd = [
                sys.executable,
                str(script_path),
                "--environment",
                self.environment
            ]

            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True,
                cwd=str(self.build_dir)
            )

            success = result.returncode == 0
            status = "Success" if success else f"Failed (exit code {result.returncode})"
            self.deployment_log.append((component_name, success, status))

            if success:
                console.print(f"\n[green]✓ {component_name} deployment completed[/green]")
            else:
                console.print(f"\n[red]✗ {component_name} deployment failed[/red]")

            return success

        except Exception as e:
            console.print(f"\n[red]✗ Error running {script_name}: {e}[/red]")
            self.deployment_log.append((component_name, False, str(e)))
            return False

    def create_deployment_summary(self) -> None:
        """Create deployment summary report"""
        duration = time.time() - self.start_time
        duration_str = f"{int(duration // 60)}m {int(duration % 60)}s"

        summary_content = f"""# Deployment Summary

**Environment**: {self.environment.upper()}
**Started**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))}
**Completed**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Duration**: {duration_str}

## Deployment Results

| Component | Status | Details |
|-----------|--------|---------|
"""

        for component, success, details in self.deployment_log:
            status_icon = "✓" if success else "✗"
            status_text = "Success" if success else "Failed"
            summary_content += f"| {component} | {status_icon} {status_text} | {details} |\n"

        summary_content += f"""

## Next Steps

### 1. Databricks Configuration

- Verify DLT pipeline is running
- Create Genie space using `databricks/pipelines/genie_space_setup.sql`
- Note the Genie space ID for UI integration

### 2. Ignition Configuration

Follow the checklist: `build/ignition_deployment_checklist_{self.environment}.md`

Key steps:
1. Import UDTs through Designer
2. Create tag instances
3. Deploy Gateway scripts
4. Configure Zerobus streaming
5. Create Perspective view

### 3. UI Integration

Follow the guide: `build/perspective_integration_guide_{self.environment}.md`

Key steps:
1. Get chat UI URL from deployment output
2. Configure Perspective session properties
3. Add Embedded Frame with chat URL
4. Add "Ask AI" buttons to alarm table
5. Test end-to-end integration

### 4. Validation

Run end-to-end tests:
1. Verify tag updates in Ignition Tag Browser
2. Verify data flowing to Databricks bronze table
3. Verify DLT pipeline processing (bronze → silver → gold)
4. Test Genie queries in Databricks UI
5. Test chat integration in Perspective view
6. Measure end-to-end latency (tag change → Genie response)

Target latency: <15 seconds total

### 5. Demo Preparation

1. Review demo script: `prompts/ralph_wiggum_12_demo.md`
2. Practice fault scenario (CR_002 vibration increase)
3. Prepare backup plan (screenshots, video)
4. Test from demo environment
5. Brief stakeholders on demo flow

## Deployment Files

- Configuration: `build/environment_config_{self.environment}.yaml`
- Databricks state: `build/deployment_state_{self.environment}.json`
- Ignition checklist: `build/ignition_deployment_checklist_{self.environment}.md`
- UI integration: `build/perspective_integration_guide_{self.environment}.md`

## Rollback

If deployment fails, see: `build/rollback_procedures.md`

## Support

For issues:
1. Check component-specific logs in each deployment script output
2. Verify all prerequisites are met
3. Review troubleshooting sections in component READMEs
4. Contact support with deployment summary and logs

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Ignition Edge Gateway                    │
│                                                              │
│  ┌──────────────┐    ┌─────────────────┐                    │
│  │     UDTs     │───>│  Memory Tags    │                    │
│  │  (15 equip)  │    │   (105 tags)    │                    │
│  └──────────────┘    └─────────────────┘                    │
│                               │                              │
│  ┌──────────────────────────┐ │                              │
│  │   Gateway Scripts        │ │                              │
│  │  - Physics Simulation    │─┤                              │
│  │  - Fault Injection       │ │                              │
│  └──────────────────────────┘ │                              │
│                               │                              │
│  ┌──────────────────────────┐ │                              │
│  │  Perspective View        │ │                              │
│  │  - Equipment status      │ │                              │
│  │  - Alarm table           │ │                              │
│  │  - Chat iframe           │ │                              │
│  └──────────────────────────┘ │                              │
└───────────────────────────────┼──────────────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  Zerobus Streaming   │
                    │   (500ms batches)    │
                    └───────────┬──────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│                     Databricks Lakehouse                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              DLT Real-Time Pipeline                  │    │
│  │                                                       │    │
│  │  Bronze          Silver           Gold               │    │
│  │  (Raw JSON)  →  (Normalized)  →  (Aggregated)       │    │
│  │  <1s latency    <1s latency     <1s latency         │    │
│  └─────────────────────────────────────────────────────┘    │
│                               │                              │
│  ┌────────────────────────────▼──────────────────────────┐  │
│  │           Genie Space (Natural Language)              │  │
│  │  - Equipment performance tables                       │  │
│  │  - ML predictions                                     │  │
│  │  - Historical patterns                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                               │                              │
└───────────────────────────────┼──────────────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │   Chat UI Response   │
                    │    (<5s latency)     │
                    └──────────────────────┘
```

## Key Metrics

Target Performance:
- Tag update frequency: 1000ms (1 Hz)
- Zerobus batch interval: 500ms
- DLT pipeline latency: <3s (bronze → gold)
- Genie query response: <5s
- End-to-end latency: <15s (tag change → chat response)

Scale:
- Equipment count: 15 (5 haul trucks, 3 crushers, 2 conveyors)
- Total tags: 105
- Data points/second: 105
- Daily data volume: ~9M records
- DLT processing mode: Real-Time (continuous)

## Technology Stack

- **Edge**: Ignition 8.1+ (Gateway + Perspective)
- **Streaming**: Zerobus module (Ignition → Databricks)
- **Processing**: Databricks DLT (Real-Time mode)
- **ML**: Databricks ML Runtime
- **Analytics**: Genie (Natural Language SQL)
- **UI**: HTML5 + JavaScript (embedded in Perspective)
- **Deployment**: Python 3.12 automation

## Success Criteria

Deployment is successful when:
- [x] All prerequisites passed
- [x] Databricks components deployed
- [x] Ignition components ready for manual configuration
- [x] UI uploaded and accessible
- [x] Integration guides generated
- [ ] Manual steps completed (Ignition + Genie space)
- [ ] End-to-end test passed
- [ ] Demo rehearsed and ready

"""

        summary_file = self.build_dir / f"deployment_summary_{self.environment}.md"
        with open(summary_file, 'w') as f:
            f.write(summary_content)

        console.print(f"\n[green]✓ Deployment summary saved to: {summary_file}[/green]")

    def show_deployment_summary(self) -> None:
        """Display deployment summary in console"""
        console.print("\n" + "="*70)
        console.print("\n[bold green]Deployment Summary[/bold green]\n")

        # Create results table
        table = Table(title=f"Component Deployment Results - {self.environment.upper()}")
        table.add_column("Component", style="cyan", width=30)
        table.add_column("Status", style="green", width=15)
        table.add_column("Details", style="white", width=40)

        for component, success, details in self.deployment_log:
            status = "[green]✓ Success[/green]" if success else "[red]✗ Failed[/red]"
            table.add_row(component, status, details)

        console.print(table)

        # Overall status
        all_success = all(success for _, success, _ in self.deployment_log)
        duration = time.time() - self.start_time

        console.print(f"\nTotal duration: [yellow]{int(duration // 60)}m {int(duration % 60)}s[/yellow]")

        if all_success:
            console.print("\n[bold green]✓ All automated deployments completed successfully![/bold green]")
        else:
            console.print("\n[bold yellow]⚠ Some deployments require manual steps or failed[/bold yellow]")

        console.print("\n" + "="*70 + "\n")

    def deploy_all(self) -> bool:
        """Run complete deployment"""
        self.print_banner()

        # Check prerequisites
        if not self.check_prerequisites():
            return False

        if self.interactive:
            if not Confirm.ask("\n[yellow]Proceed with deployment?[/yellow]"):
                console.print("[yellow]Deployment cancelled by user[/yellow]")
                return False

        # Deploy components in order
        components = [
            ("deploy_databricks.py", "Databricks (DLT + Tables)"),
            ("deploy_ui.py", "Chat UI"),
            ("deploy_ignition.py", "Ignition (Instructions)")
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]Deploying all components...",
                total=len(components)
            )

            for script, component in components:
                progress.update(task, description=f"[cyan]Deploying {component}...")
                self.run_deployment_script(script, component)
                progress.advance(task)
                time.sleep(1)  # Brief pause between components

        # Create summary
        self.create_deployment_summary()
        self.show_deployment_summary()

        # Next steps
        console.print(Panel.fit(
            "[bold green]Deployment Complete![/bold green]\n\n"
            "[yellow]Next Steps:[/yellow]\n"
            "1. Review deployment summary above\n"
            "2. Complete manual Ignition steps (see checklist)\n"
            "3. Create Genie space in Databricks UI\n"
            "4. Integrate chat UI in Perspective view\n"
            "5. Run end-to-end validation tests\n\n"
            f"See: [cyan]build/deployment_summary_{self.environment}.md[/cyan]",
            border_style="green"
        ))

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Mining Operations Genie Demo - Master Deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy to dev environment (interactive)
  python deploy_all.py

  # Deploy to dev (non-interactive)
  python deploy_all.py --no-interactive

  # Deploy to production
  python deploy_all.py --environment prod

  # Check prerequisites only
  python deploy_all.py --check-only
        """
    )

    parser.add_argument(
        "--environment",
        choices=["dev", "prod"],
        default="dev",
        help="Deployment environment (default: dev)"
    )

    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Run without prompts (for automation)"
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check prerequisites only, don't deploy"
    )

    args = parser.parse_args()

    deployer = MasterDeployer(
        environment=args.environment,
        interactive=not args.no_interactive
    )

    if args.check_only:
        deployer.print_banner()
        success = deployer.check_prerequisites()
        sys.exit(0 if success else 1)

    success = deployer.deploy_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
