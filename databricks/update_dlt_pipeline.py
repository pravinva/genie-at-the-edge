#!/usr/bin/env python3
"""
Update DLT Pipeline with correct file path
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.pipelines import *
from databricks.sdk.service.workspace import ImportFormat

w = WorkspaceClient()
pipeline_id = "9744a549-24f1-4650-8585-37cc323d5451"

print("="*80)
print("Updating DLT Pipeline with Source File")
print("="*80)

# Step 1: Upload Python file
workspace_path = "/Users/pravin.varma@databricks.com/mining-genie-demo/mining_realtime_dlt.py"

print(f"\n[1/3] Uploading DLT file to: {workspace_path}")

with open("databricks/mining_realtime_dlt.py", "r") as f:
    content = f.read()

try:
    w.workspace.upload(
        path=workspace_path,
        content=content.encode('utf-8'),
        format=ImportFormat.SOURCE,
        overwrite=True
    )
    print(f"✓ File uploaded successfully")
except Exception as e:
    print(f"✗ Upload error: {str(e)}")

# Step 2: Update pipeline configuration
print(f"\n[2/3] Updating pipeline configuration...")

try:
    w.pipelines.update(
        pipeline_id=pipeline_id,
        name="mining_operations_realtime",
        libraries=[
            PipelineLibrary(
                notebook=NotebookLibrary(path=workspace_path)
            )
        ],
        target="ignition_genie.mining_demo",
        storage="dbfs:/pipelines/mining_operations",
        configuration={
            "spark.databricks.streaming.mode": "realtime",
            "spark.sql.shuffle.partitions": "200"
        },
        clusters=[
            PipelineCluster(
                label="default",
                num_workers=2,
                node_type_id="i3.xlarge"
            )
        ],
        continuous=True,
        photon=True,
        development=True,
        edition="ADVANCED"
    )
    print(f"✓ Pipeline configuration updated")
except Exception as e:
    print(f"✗ Update error: {str(e)}")

# Step 3: Start pipeline
print(f"\n[3/3] Starting pipeline...")

try:
    update = w.pipelines.start_update(pipeline_id=pipeline_id)
    print(f"✓ Pipeline started!")
    print(f"  Update ID: {update.update_id}")
except Exception as e:
    error_msg = str(e)
    if "already exists" in error_msg or "active update" in error_msg:
        print(f"✓ Pipeline already running")
    else:
        print(f"✗ Start error: {str(e)}")

print("\n" + "="*80)
print("Pipeline Updated and Running")
print("="*80)
print(f"\nMonitor at:")
print(f"https://e2-demo-field-eng.cloud.databricks.com/#joblist/pipelines/{pipeline_id}")
print("="*80)
