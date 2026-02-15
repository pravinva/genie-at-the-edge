#!/usr/bin/env python3
"""
Fix DLT Pipeline - Upload file to correct location
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.pipelines import *
from databricks.sdk.service.workspace import ImportFormat
import base64

w = WorkspaceClient()
pipeline_id = "9744a549-24f1-4650-8585-37cc323d5451"

print("="*80)
print("Fixing DLT Pipeline File Upload")
print("="*80)

# Use simpler path without subfolder
workspace_path = "/Users/pravin.varma@databricks.com/mining_realtime_dlt.py"

print(f"\n[1/3] Uploading to: {workspace_path}")

with open("databricks/mining_realtime_dlt.py", "r") as f:
    content = f.read()

try:
    # Delete if exists
    try:
        w.workspace.delete(path=workspace_path)
        print("  Deleted existing file")
    except:
        pass

    # Upload
    w.workspace.upload(
        path=workspace_path,
        content=content.encode('utf-8'),
        format=ImportFormat.SOURCE,
        overwrite=True
    )
    print(f"✓ File uploaded successfully")
except Exception as e:
    print(f"✗ Error: {str(e)}")
    exit(1)

# Update pipeline to use this path
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
                num_workers=1,
                node_type_id="i3.xlarge"
            )
        ],
        continuous=True,
        photon=True,
        development=True,
        edition="ADVANCED"
    )
    print(f"✓ Pipeline updated with file path: {workspace_path}")
except Exception as e:
    print(f"✗ Error: {str(e)}")
    exit(1)

# Start pipeline
print(f"\n[3/3] Starting pipeline...")

try:
    update = w.pipelines.start_update(pipeline_id=pipeline_id)
    print(f"✓ Pipeline started!")
    print(f"  Update ID: {update.update_id}")
except Exception as e:
    if "already exists" in str(e) or "active update" in str(e):
        print(f"  Pipeline update already in progress")
    else:
        print(f"✗ Error: {str(e)}")

print("\n" + "="*80)
print("DLT Pipeline Fixed and Running")
print("="*80)
print(f"\nFile Location: {workspace_path}")
print(f"Monitor Pipeline:")
print(f"  https://e2-demo-field-eng.cloud.databricks.com/#joblist/pipelines/{pipeline_id}")
print("="*80)
