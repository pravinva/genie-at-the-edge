"""
Mining Operations DLT Pipeline - Automated Deployment Script

This script automates the deployment of the Real-Time DLT pipeline using
Databricks SDK. It handles pipeline creation, configuration, and validation.

Prerequisites:
- Databricks SDK installed: pip install databricks-sdk
- Authentication configured (via .databrickscfg or environment variables)
- Dimension tables created (run dimension_tables.sql first)
- Zerobus stream active

Usage:
    python deploy_pipeline.py [--update] [--start]

Options:
    --update : Update existing pipeline if it exists
    --start  : Start pipeline immediately after deployment
"""

import sys
import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.pipelines import (
    PipelineLibrary,
    NotebookLibrary,
    PipelineCluster,
    PipelineClusterAutoscale,
    CreatePipeline,
    EditPipeline
)

# Configuration
PIPELINE_NAME = "mining_operations_realtime"
TARGET_CATALOG = "field_engineering"
TARGET_SCHEMA = "mining_demo"
NOTEBOOK_PATH = "/Repos/pravin.varma@databricks.com/genie-at-the-edge/databricks/pipelines/mining_realtime_dlt"
CLUSTER_LABEL = "default"
MIN_WORKERS = 2
MAX_WORKERS = 4
NODE_TYPE_ID = "i3.xlarge"  # Good for streaming workloads
DRIVER_NODE_TYPE_ID = "i3.xlarge"

# Real-Time Mode configuration
CONFIGURATION = {
    "spark.databricks.streaming.mode": "realtime",
    "spark.sql.shuffle.partitions": "200"
}

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(message):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_info(message):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def check_prerequisites(w: WorkspaceClient):
    """
    Check if prerequisites are met before deployment
    """
    print_header("Checking Prerequisites")

    all_good = True

    # Check if notebook exists
    try:
        w.workspace.get_status(NOTEBOOK_PATH + ".py")
        print_success(f"Notebook found: {NOTEBOOK_PATH}")
    except Exception as e:
        print_error(f"Notebook not found: {NOTEBOOK_PATH}")
        print_info("Please upload mining_realtime_dlt.py to Databricks Repos or Workspace")
        all_good = False

    # Check if target catalog/schema exists
    try:
        w.catalogs.get(TARGET_CATALOG)
        print_success(f"Catalog exists: {TARGET_CATALOG}")

        w.schemas.get(f"{TARGET_CATALOG}.{TARGET_SCHEMA}")
        print_success(f"Schema exists: {TARGET_CATALOG}.{TARGET_SCHEMA}")
    except Exception as e:
        print_error(f"Catalog or schema not found: {TARGET_CATALOG}.{TARGET_SCHEMA}")
        print_info("Run: CREATE SCHEMA IF NOT EXISTS field_engineering.mining_demo")
        all_good = False

    # Check if dimension tables exist
    required_tables = ["equipment_master"]
    for table in required_tables:
        try:
            w.tables.get(f"{TARGET_CATALOG}.{TARGET_SCHEMA}.{table}")
            print_success(f"Dimension table exists: {table}")
        except Exception as e:
            print_error(f"Dimension table not found: {table}")
            print_info("Run dimension_tables.sql to create required dimension tables")
            all_good = False

    return all_good


def find_existing_pipeline(w: WorkspaceClient):
    """
    Find existing pipeline by name
    """
    try:
        pipelines = w.pipelines.list_pipelines()
        for pipeline in pipelines:
            if pipeline.name == PIPELINE_NAME:
                return pipeline.pipeline_id
        return None
    except Exception as e:
        print_warning(f"Could not list pipelines: {e}")
        return None


def create_pipeline(w: WorkspaceClient):
    """
    Create new DLT pipeline
    """
    print_header("Creating DLT Pipeline")

    try:
        # Configure pipeline
        pipeline_spec = CreatePipeline(
            name=PIPELINE_NAME,
            catalog=TARGET_CATALOG,
            target=TARGET_SCHEMA,
            libraries=[
                PipelineLibrary(
                    notebook=NotebookLibrary(path=NOTEBOOK_PATH + ".py")
                )
            ],
            clusters=[
                PipelineCluster(
                    label=CLUSTER_LABEL,
                    autoscale=PipelineClusterAutoscale(
                        min_workers=MIN_WORKERS,
                        max_workers=MAX_WORKERS,
                        mode="ENHANCED"
                    ),
                    node_type_id=NODE_TYPE_ID,
                    driver_node_type_id=DRIVER_NODE_TYPE_ID,
                    enable_local_disk_encryption=False,
                    custom_tags={"project": "mining-genie-demo", "component": "dlt-pipeline"}
                )
            ],
            configuration=CONFIGURATION,
            continuous=False,  # Set to True for always-on streaming
            development=True,  # Set to False for production
            photon_enabled=True,
            serverless=False,  # Set to True if serverless is available
            channel="CURRENT"
        )

        print_info(f"Pipeline Name: {PIPELINE_NAME}")
        print_info(f"Target: {TARGET_CATALOG}.{TARGET_SCHEMA}")
        print_info(f"Notebook: {NOTEBOOK_PATH}")
        print_info(f"Cluster: {MIN_WORKERS}-{MAX_WORKERS} workers ({NODE_TYPE_ID})")
        print_info(f"Real-Time Mode: Enabled")
        print_info(f"Development Mode: Enabled")

        # Create pipeline
        response = w.pipelines.create(
            name=pipeline_spec.name,
            catalog=pipeline_spec.catalog,
            target=pipeline_spec.target,
            libraries=pipeline_spec.libraries,
            clusters=pipeline_spec.clusters,
            configuration=pipeline_spec.configuration,
            continuous=pipeline_spec.continuous,
            development=pipeline_spec.development,
            photon_enabled=pipeline_spec.photon_enabled,
            channel=pipeline_spec.channel
        )

        pipeline_id = response.pipeline_id
        print_success(f"Pipeline created successfully!")
        print_success(f"Pipeline ID: {pipeline_id}")
        print_info(f"View pipeline: https://{w.config.host}/pipelines/{pipeline_id}")

        return pipeline_id

    except Exception as e:
        print_error(f"Failed to create pipeline: {e}")
        return None


def update_pipeline(w: WorkspaceClient, pipeline_id: str):
    """
    Update existing DLT pipeline
    """
    print_header("Updating DLT Pipeline")

    try:
        print_info(f"Updating pipeline: {pipeline_id}")

        # Update pipeline configuration
        w.pipelines.update(
            pipeline_id=pipeline_id,
            name=PIPELINE_NAME,
            catalog=TARGET_CATALOG,
            target=TARGET_SCHEMA,
            libraries=[
                PipelineLibrary(
                    notebook=NotebookLibrary(path=NOTEBOOK_PATH + ".py")
                )
            ],
            clusters=[
                PipelineCluster(
                    label=CLUSTER_LABEL,
                    autoscale=PipelineClusterAutoscale(
                        min_workers=MIN_WORKERS,
                        max_workers=MAX_WORKERS,
                        mode="ENHANCED"
                    ),
                    node_type_id=NODE_TYPE_ID,
                    driver_node_type_id=DRIVER_NODE_TYPE_ID,
                    custom_tags={"project": "mining-genie-demo", "component": "dlt-pipeline"}
                )
            ],
            configuration=CONFIGURATION,
            development=True,
            photon_enabled=True,
            channel="CURRENT"
        )

        print_success("Pipeline updated successfully!")
        print_info(f"View pipeline: https://{w.config.host}/pipelines/{pipeline_id}")

        return True

    except Exception as e:
        print_error(f"Failed to update pipeline: {e}")
        return False


def start_pipeline(w: WorkspaceClient, pipeline_id: str):
    """
    Start the DLT pipeline
    """
    print_header("Starting DLT Pipeline")

    try:
        print_info("Starting pipeline update...")
        update_response = w.pipelines.start_update(pipeline_id=pipeline_id)
        update_id = update_response.update_id

        print_success(f"Pipeline update started!")
        print_info(f"Update ID: {update_id}")
        print_info("Monitoring progress (Ctrl+C to stop monitoring, pipeline continues)...")

        # Monitor progress
        previous_state = None
        while True:
            try:
                update_info = w.pipelines.get_update(pipeline_id=pipeline_id, update_id=update_id)
                current_state = update_info.update.state.value if update_info.update and update_info.update.state else "UNKNOWN"

                if current_state != previous_state:
                    if current_state == "COMPLETED":
                        print_success(f"Pipeline update completed successfully!")
                        return True
                    elif current_state in ["FAILED", "CANCELED"]:
                        print_error(f"Pipeline update {current_state.lower()}")
                        return False
                    else:
                        print_info(f"State: {current_state}")
                    previous_state = current_state

                time.sleep(5)

            except KeyboardInterrupt:
                print_warning("\nStopped monitoring. Pipeline continues running.")
                print_info(f"Check status: https://{w.config.host}/pipelines/{pipeline_id}")
                return True

    except Exception as e:
        print_error(f"Failed to start pipeline: {e}")
        return False


def validate_deployment(w: WorkspaceClient, pipeline_id: str):
    """
    Validate pipeline deployment
    """
    print_header("Validating Deployment")

    try:
        # Get pipeline details
        pipeline = w.pipelines.get(pipeline_id=pipeline_id)

        print_info(f"Pipeline Name: {pipeline.name}")
        print_info(f"Pipeline ID: {pipeline_id}")
        print_info(f"State: {pipeline.state}")

        if pipeline.latest_updates:
            latest = pipeline.latest_updates[0]
            print_info(f"Latest Update: {latest.state}")
            print_info(f"Creation Time: {latest.creation_time}")

        print_success("Deployment validated!")

        # Print next steps
        print_header("Next Steps")
        print("1. Monitor pipeline in UI:")
        print(f"   {Colors.OKCYAN}https://{w.config.host}/pipelines/{pipeline_id}{Colors.ENDC}")
        print("\n2. Check data quality metrics in DLT UI")
        print("\n3. Run validation queries:")
        print(f"   {Colors.OKCYAN}See validation_queries.sql{Colors.ENDC}")
        print("\n4. Create Genie space:")
        print(f"   {Colors.OKCYAN}Run genie_space_setup.sql{Colors.ENDC}")

        return True

    except Exception as e:
        print_error(f"Validation failed: {e}")
        return False


def main():
    """
    Main deployment flow
    """
    print_header("Mining Operations DLT Pipeline Deployment")

    # Parse arguments
    should_update = "--update" in sys.argv
    should_start = "--start" in sys.argv

    try:
        # Initialize Databricks client
        print_info("Initializing Databricks client...")
        w = WorkspaceClient()
        print_success(f"Connected to workspace: {w.config.host}")

        # Check prerequisites
        if not check_prerequisites(w):
            print_error("Prerequisites not met. Please fix issues above and retry.")
            sys.exit(1)

        # Check for existing pipeline
        existing_pipeline_id = find_existing_pipeline(w)

        if existing_pipeline_id:
            print_warning(f"Pipeline already exists: {existing_pipeline_id}")
            if should_update:
                if update_pipeline(w, existing_pipeline_id):
                    pipeline_id = existing_pipeline_id
                else:
                    sys.exit(1)
            else:
                print_info("Use --update flag to update existing pipeline")
                pipeline_id = existing_pipeline_id
        else:
            # Create new pipeline
            pipeline_id = create_pipeline(w)
            if not pipeline_id:
                sys.exit(1)

        # Start pipeline if requested
        if should_start:
            if not start_pipeline(w, pipeline_id):
                print_warning("Pipeline started with issues. Check UI for details.")

        # Validate deployment
        validate_deployment(w, pipeline_id)

        print_success("\nDeployment complete!")

    except Exception as e:
        print_error(f"Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
