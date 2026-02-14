#!/usr/bin/env python3
"""
Mining Operations Genie Demo - Databricks Deployment Automation
Deploys DLT pipeline, dimension tables, Genie space, and monitoring
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.catalog import MonitorInferenceProfile, MonitorCronSchedule
    from databricks.sdk.service.pipelines import PipelineSpecification, PipelineLibrary, NotebookLibrary
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.table import Table
    from rich.panel import Panel
except ImportError as e:
    print(f"Error: Missing required dependencies. Run: pip install -r requirements.txt")
    print(f"Details: {e}")
    sys.exit(1)

console = Console()


class DatabricksDeployer:
    """Handles deployment of all Databricks components"""

    def __init__(self, config_path: str = "environment_config.yaml", environment: str = "dev"):
        """Initialize deployer with configuration"""
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.workspace_client: Optional[WorkspaceClient] = None
        self.deployment_state: Dict[str, Any] = {}

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = self.project_root / "build" / config_path
        if not config_file.exists():
            console.print(f"[red]Error: Configuration file not found: {config_file}[/red]")
            sys.exit(1)

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def initialize_client(self) -> None:
        """Initialize Databricks workspace client"""
        console.print("[yellow]Initializing Databricks connection...[/yellow]")

        token = os.environ.get("DATABRICKS_TOKEN")
        if not token:
            console.print("[red]Error: DATABRICKS_TOKEN environment variable not set[/red]")
            console.print("Set it with: export DATABRICKS_TOKEN=your_token_here")
            sys.exit(1)

        db_config = self.config["databricks"][self.environment]
        workspace_url = db_config["workspace_url"]

        try:
            self.workspace_client = WorkspaceClient(
                host=workspace_url,
                token=token
            )
            # Test connection
            self.workspace_client.current_user.me()
            console.print(f"[green]✓ Connected to Databricks workspace: {workspace_url}[/green]")
        except Exception as e:
            console.print(f"[red]Error connecting to Databricks: {e}[/red]")
            sys.exit(1)

    def validate_prerequisites(self) -> bool:
        """Validate all prerequisites before deployment"""
        console.print("\n[bold blue]Validating Prerequisites[/bold blue]")

        checks = []
        db_config = self.config["databricks"][self.environment]

        # Check catalog and schema
        try:
            catalog = db_config["catalog"]
            schema = db_config["schema"]
            self.workspace_client.catalogs.get(catalog)
            checks.append(("Catalog exists", True, catalog))

            try:
                self.workspace_client.schemas.get(f"{catalog}.{schema}")
                checks.append(("Schema exists", True, f"{catalog}.{schema}"))
            except Exception:
                # Create schema if it doesn't exist
                self.workspace_client.schemas.create(
                    catalog_name=catalog,
                    name=schema,
                    comment="Mining Operations Demo"
                )
                checks.append(("Schema created", True, f"{catalog}.{schema}"))

        except Exception as e:
            checks.append(("Catalog/Schema", False, str(e)))

        # Check warehouse
        try:
            warehouse_id = db_config["warehouse_id"]
            warehouse = self.workspace_client.warehouses.get(warehouse_id)
            checks.append(("Warehouse exists", True, warehouse.name))

            # Start warehouse if not running
            if warehouse.state.value != "RUNNING":
                console.print(f"[yellow]Starting warehouse {warehouse.name}...[/yellow]")
                self.workspace_client.warehouses.start(warehouse_id)
                time.sleep(10)
                checks.append(("Warehouse started", True, warehouse.name))
        except Exception as e:
            checks.append(("Warehouse", False, str(e)))

        # Display results
        table = Table(title="Prerequisite Validation")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")

        all_passed = True
        for check_name, passed, details in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            color = "green" if passed else "red"
            table.add_row(check_name, f"[{color}]{status}[/{color}]", str(details))
            if not passed:
                all_passed = False

        console.print(table)
        return all_passed

    def deploy_dimension_tables(self) -> bool:
        """Deploy dimension tables (equipment_master, etc.)"""
        console.print("\n[bold blue]Deploying Dimension Tables[/bold blue]")

        sql_file = self.project_root / "databricks" / "pipelines" / "dimension_tables.sql"
        if not sql_file.exists():
            console.print(f"[red]Error: SQL file not found: {sql_file}[/red]")
            return False

        with open(sql_file, 'r') as f:
            sql_content = f.read()

        # Split into individual statements
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]

        db_config = self.config["databricks"][self.environment]
        warehouse_id = db_config["warehouse_id"]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Executing SQL statements...", total=len(statements))

            for i, statement in enumerate(statements, 1):
                if statement.lower().startswith(('create', 'insert', 'drop', 'use')):
                    try:
                        progress.update(task, description=f"Executing statement {i}/{len(statements)}")
                        self.workspace_client.statement_execution.execute_statement(
                            warehouse_id=warehouse_id,
                            statement=statement,
                            wait_timeout="30s"
                        )
                        progress.advance(task)
                    except Exception as e:
                        console.print(f"[yellow]Warning on statement {i}: {e}[/yellow]")
                        progress.advance(task)

        console.print("[green]✓ Dimension tables deployed[/green]")
        self.deployment_state["dimension_tables"] = True
        return True

    def deploy_dlt_pipeline(self) -> bool:
        """Deploy DLT real-time pipeline"""
        console.print("\n[bold blue]Deploying DLT Pipeline[/bold blue]")

        pipeline_file = self.project_root / "databricks" / "pipelines" / "mining_realtime_dlt.py"
        if not pipeline_file.exists():
            console.print(f"[red]Error: Pipeline file not found: {pipeline_file}[/red]")
            return False

        # Upload pipeline notebook to workspace
        workspace_path = f"/Workspace/Users/{self.workspace_client.current_user.me().user_name}/mining_demo"

        try:
            # Create directory
            self.workspace_client.workspace.mkdirs(workspace_path)

            # Upload notebook
            with open(pipeline_file, 'rb') as f:
                notebook_content = f.read()

            self.workspace_client.workspace.upload(
                path=f"{workspace_path}/mining_realtime_dlt.py",
                content=notebook_content,
                overwrite=True,
                format="SOURCE"
            )
            console.print(f"[green]✓ Uploaded pipeline notebook to {workspace_path}[/green]")

        except Exception as e:
            console.print(f"[red]Error uploading notebook: {e}[/red]")
            return False

        # Create or update DLT pipeline
        db_config = self.config["databricks"][self.environment]
        pipeline_config = self.config["components"]["dlt_pipeline"]

        catalog = db_config["catalog"]
        schema = db_config["schema"]
        pipeline_name = pipeline_config["name"]

        # Check if pipeline exists
        existing_pipeline = None
        try:
            pipelines = self.workspace_client.pipelines.list_pipelines()
            for pipeline in pipelines:
                if pipeline.name == pipeline_name:
                    existing_pipeline = pipeline
                    break
        except Exception as e:
            console.print(f"[yellow]Warning listing pipelines: {e}[/yellow]")

        pipeline_spec = {
            "name": pipeline_name,
            "catalog": catalog,
            "target": schema,
            "continuous": True,
            "development": (self.environment == "dev"),
            "channel": pipeline_config["channel"],
            "libraries": [
                {"notebook": {"path": f"{workspace_path}/mining_realtime_dlt.py"}}
            ],
            "clusters": [
                {
                    "label": "default",
                    "autoscale": {
                        "min_workers": pipeline_config["min_workers"],
                        "max_workers": pipeline_config["max_workers"]
                    },
                    "spark_conf": {
                        "spark.databricks.delta.preview.enabled": "true"
                    }
                }
            ]
        }

        try:
            if existing_pipeline:
                console.print(f"[yellow]Updating existing pipeline: {pipeline_name}[/yellow]")
                self.workspace_client.pipelines.update(
                    pipeline_id=existing_pipeline.pipeline_id,
                    **pipeline_spec
                )
                pipeline_id = existing_pipeline.pipeline_id
            else:
                console.print(f"[yellow]Creating new pipeline: {pipeline_name}[/yellow]")
                response = self.workspace_client.pipelines.create(**pipeline_spec)
                pipeline_id = response.pipeline_id

            console.print(f"[green]✓ DLT pipeline deployed: {pipeline_id}[/green]")
            self.deployment_state["dlt_pipeline_id"] = pipeline_id

            # Start pipeline if requested
            console.print("[yellow]Starting pipeline (this may take 5-10 minutes)...[/yellow]")
            self.workspace_client.pipelines.start_update(pipeline_id)

            return True

        except Exception as e:
            console.print(f"[red]Error deploying pipeline: {e}[/red]")
            return False

    def deploy_genie_space(self) -> bool:
        """Deploy Genie space for natural language queries"""
        console.print("\n[bold blue]Deploying Genie Space[/bold blue]")

        # Read Genie setup SQL
        genie_file = self.project_root / "databricks" / "pipelines" / "genie_space_setup.sql"
        if not genie_file.exists():
            console.print(f"[yellow]Warning: Genie setup file not found: {genie_file}[/yellow]")
            console.print("[yellow]Genie space must be created manually via Databricks UI[/yellow]")
            return True

        db_config = self.config["databricks"][self.environment]
        genie_config = self.config["components"]["genie"]

        console.print(f"""
[cyan]Genie Space Configuration:[/cyan]
- Name: {genie_config['space_name']}
- Catalog: {db_config['catalog']}
- Schema: {db_config['schema']}
- Warehouse: {db_config['warehouse_id']}

[yellow]Note: Genie spaces must be created via the Databricks UI or API.[/yellow]
[yellow]Instructions are in: databricks/pipelines/genie_space_setup.sql[/yellow]
        """)

        self.deployment_state["genie_space"] = "manual"
        return True

    def deploy_monitoring(self) -> bool:
        """Deploy Lakehouse Monitoring for data quality"""
        console.print("\n[bold blue]Deploying Monitoring[/bold blue]")

        console.print("[yellow]Lakehouse Monitoring deployment coming soon...[/yellow]")
        console.print("[yellow]For now, use Databricks UI to create monitors[/yellow]")

        self.deployment_state["monitoring"] = "manual"
        return True

    def run_validation_tests(self) -> bool:
        """Run validation queries to verify deployment"""
        console.print("\n[bold blue]Running Validation Tests[/bold blue]")

        validation_file = self.project_root / "databricks" / "pipelines" / "validation_queries.sql"
        if not validation_file.exists():
            console.print(f"[yellow]Validation file not found: {validation_file}[/yellow]")
            return True

        with open(validation_file, 'r') as f:
            queries = [q.strip() for q in f.read().split(';') if q.strip() and q.strip().startswith('SELECT')]

        db_config = self.config["databricks"][self.environment]
        warehouse_id = db_config["warehouse_id"]

        results = []
        for query in queries[:5]:  # Run first 5 validation queries
            try:
                result = self.workspace_client.statement_execution.execute_statement(
                    warehouse_id=warehouse_id,
                    statement=query,
                    wait_timeout="30s"
                )
                results.append((query[:50] + "...", True, "OK"))
            except Exception as e:
                results.append((query[:50] + "...", False, str(e)[:50]))

        # Display results
        table = Table(title="Validation Results")
        table.add_column("Query", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Result", style="white")

        for query, success, result in results:
            status = "✓ PASS" if success else "✗ FAIL"
            color = "green" if success else "red"
            table.add_row(query, f"[{color}]{status}[/{color}]", result)

        console.print(table)
        return all(success for _, success, _ in results)

    def save_deployment_state(self) -> None:
        """Save deployment state for rollback"""
        state_file = self.project_root / "build" / f"deployment_state_{self.environment}.json"
        state_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "environment": self.environment,
            "state": self.deployment_state
        }

        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)

        console.print(f"\n[green]✓ Deployment state saved to: {state_file}[/green]")

    def deploy_all(self) -> bool:
        """Deploy all Databricks components"""
        console.print(Panel.fit(
            f"[bold green]Mining Operations Genie Demo[/bold green]\n"
            f"Databricks Deployment - Environment: {self.environment.upper()}",
            border_style="green"
        ))

        # Initialize
        self.initialize_client()

        # Validate prerequisites
        if not self.validate_prerequisites():
            console.print("\n[red]✗ Prerequisites validation failed. Fix issues and retry.[/red]")
            return False

        # Deploy components
        steps = [
            ("Dimension Tables", self.deploy_dimension_tables),
            ("DLT Pipeline", self.deploy_dlt_pipeline),
            ("Genie Space", self.deploy_genie_space),
            ("Monitoring", self.deploy_monitoring),
            ("Validation Tests", self.run_validation_tests)
        ]

        for step_name, step_func in steps:
            try:
                if not step_func():
                    console.print(f"\n[red]✗ Failed at step: {step_name}[/red]")
                    return False
            except Exception as e:
                console.print(f"\n[red]✗ Error in {step_name}: {e}[/red]")
                return False

        # Save state
        self.save_deployment_state()

        # Success summary
        console.print(Panel.fit(
            "[bold green]✓ Databricks Deployment Complete![/bold green]\n\n"
            "Next steps:\n"
            "1. Verify DLT pipeline is running in Databricks UI\n"
            "2. Create Genie space using genie_space_setup.sql\n"
            "3. Deploy Ignition components: python build/deploy_ignition.py\n"
            "4. Deploy UI: python build/deploy_ui.py",
            border_style="green"
        ))

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy Databricks components")
    parser.add_argument(
        "--environment",
        choices=["dev", "prod"],
        default="dev",
        help="Deployment environment"
    )
    parser.add_argument(
        "--component",
        choices=["all", "tables", "pipeline", "genie", "monitoring"],
        default="all",
        help="Component to deploy"
    )

    args = parser.parse_args()

    deployer = DatabricksDeployer(environment=args.environment)

    if args.component == "all":
        success = deployer.deploy_all()
    else:
        deployer.initialize_client()
        if args.component == "tables":
            success = deployer.deploy_dimension_tables()
        elif args.component == "pipeline":
            success = deployer.deploy_dlt_pipeline()
        elif args.component == "genie":
            success = deployer.deploy_genie_space()
        elif args.component == "monitoring":
            success = deployer.deploy_monitoring()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
