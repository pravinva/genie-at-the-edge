#!/usr/bin/env python3
"""
Deploy Delta Live Tables Pipeline Programmatically
Creates the mining_operations_realtime DLT pipeline via Databricks SDK
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.pipelines import *
import json

w = WorkspaceClient()

print("="*80)
print("Deploying Mining Operations DLT Pipeline")
print("="*80)

# Step 1: Upload Python file to workspace
print("\n[1/3] Uploading DLT Python file to workspace...")

workspace_path = "/Users/pravin.varma@databricks.com/mining-genie-demo/mining_realtime_dlt.py"

# Read the DLT file content
with open("databricks/mining_realtime_dlt.py", "r") as f:
    dlt_content = f.read()

# Upload to workspace
try:
    w.workspace.upload(
        path=workspace_path,
        content=dlt_content.encode('utf-8'),
        format=ImportFormat.SOURCE,
        overwrite=True
    )
    print(f"✓ Uploaded to: {workspace_path}")
except Exception as e:
    print(f"✗ Upload error: {str(e)}")
    print("  Note: File may already exist or path needs adjustment")

# Step 2: Create DLT Pipeline
print("\n[2/3] Creating DLT Pipeline...")

pipeline_config = PipelineSpec(
    name="mining_operations_realtime",
    storage=f"dbfs:/pipelines/mining_operations",
    configuration={
        "spark.databricks.streaming.mode": "realtime",
        "spark.sql.shuffle.partitions": "200"
    },
    clusters=[
        PipelineCluster(
            label="default",
            num_workers=2,
            node_type_id="i3.xlarge",
            spark_conf={
                "spark.databricks.delta.preview.enabled": "true"
            },
            custom_tags={
                "project": "genie-at-the-edge",
                "owner": "pravin.varma@databricks.com"
            }
        )
    ],
    libraries=[
        PipelineLibrary(
            notebook=NotebookLibrary(path=workspace_path)
        )
    ],
    target="ignition_genie.mining_demo",
    continuous=True,  # Continuous mode (not triggered)
    photon=True,
    development=True,  # Set to False for production
    channel="CURRENT",  # Use current DBR channel
    edition="ADVANCED"  # Required for Real-Time Mode
)

try:
    # Check if pipeline exists
    existing_pipelines = list(w.pipelines.list_pipelines())
    existing = None
    for p in existing_pipelines:
        if p.name == "mining_operations_realtime":
            existing = p
            break

    if existing:
        print(f"✓ Pipeline already exists: {existing.pipeline_id}")
        print(f"  Updating configuration...")

        # Update existing pipeline
        w.pipelines.update(
            pipeline_id=existing.pipeline_id,
            name=pipeline_config.name,
            storage=pipeline_config.storage,
            configuration=pipeline_config.configuration,
            clusters=pipeline_config.clusters,
            libraries=pipeline_config.libraries,
            target=pipeline_config.target,
            continuous=pipeline_config.continuous,
            photon=pipeline_config.photon,
            development=pipeline_config.development,
            edition=pipeline_config.edition
        )

        pipeline_id = existing.pipeline_id
        print(f"✓ Pipeline updated: {pipeline_id}")
    else:
        # Create new pipeline
        pipeline = w.pipelines.create(
            name=pipeline_config.name,
            storage=pipeline_config.storage,
            configuration=pipeline_config.configuration,
            clusters=pipeline_config.clusters,
            libraries=pipeline_config.libraries,
            target=pipeline_config.target,
            continuous=pipeline_config.continuous,
            photon=pipeline_config.photon,
            development=pipeline_config.development,
            edition=pipeline_config.edition
        )

        pipeline_id = pipeline.pipeline_id
        print(f"✓ Pipeline created: {pipeline_id}")

except Exception as e:
    print(f"✗ Error creating pipeline: {str(e)}")
    print(f"  Full error: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 3: Start the pipeline
print("\n[3/3] Starting DLT Pipeline...")

try:
    # Start the pipeline
    update_response = w.pipelines.start_update(pipeline_id=pipeline_id)

    print(f"✓ Pipeline started!")
    print(f"  Update ID: {update_response.update_id}")
    print(f"  Pipeline ID: {pipeline_id}")

except Exception as e:
    print(f"✗ Error starting pipeline: {str(e)}")
    print("  You can start it manually from the Databricks UI")

print("\n" + "="*80)
print("DLT Pipeline Deployment Complete!")
print("="*80)
print(f"\nPipeline Details:")
print(f"  Name: mining_operations_realtime")
print(f"  ID: {pipeline_id}")
print(f"  Target: ignition_genie.mining_demo")
print(f"  Mode: Continuous (Real-Time)")
print(f"  Photon: Enabled")
print(f"\nView Pipeline:")
print(f"  UI: https://e2-demo-field-eng.cloud.databricks.com/#joblist/pipelines/{pipeline_id}")
print(f"\nMonitor via SDK:")
print(f"  w.pipelines.get(pipeline_id='{pipeline_id}')")
print("="*80)
