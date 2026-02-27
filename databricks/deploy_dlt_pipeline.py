#!/usr/bin/env python3
"""
Automated DLT Pipeline Deployment
Creates and starts the genie_edge_ml_enrichment DLT pipeline
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import pipelines
import json
import time

w = WorkspaceClient(profile="DEFAULT")

CATALOG = "field_engineering"
TARGET_SCHEMA = "ml_silver"
PIPELINE_NAME = "genie_edge_ml_enrichment"

# Notebook path in workspace (after repo sync)
NOTEBOOK_PATH = "/Repos/pravin.varma@databricks.com/genie-at-the-edge/databricks/dlt_enrichment_pipeline"

print("=" * 80)
print("DLT PIPELINE DEPLOYMENT")
print("=" * 80)

# Check if pipeline already exists
print("\n[1/4] Checking for existing pipeline...")
existing_pipelines = w.pipelines.list_pipelines(filter=f"name = '{PIPELINE_NAME}'")
existing_pipeline_id = None

for pipeline in existing_pipelines:
    if pipeline.name == PIPELINE_NAME:
        existing_pipeline_id = pipeline.pipeline_id
        print(f"  ✅ Found existing pipeline: {existing_pipeline_id}")
        break

if not existing_pipeline_id:
    print("  ℹ️  No existing pipeline found, will create new")

# Pipeline configuration
pipeline_config = pipelines.CreatePipeline(
    name=PIPELINE_NAME,
    catalog=CATALOG,
    target=TARGET_SCHEMA,
    storage=f"/databricks/pipelines/{PIPELINE_NAME}",
    continuous=True,
    channel="CURRENT",
    photon=True,
    libraries=[
        pipelines.PipelineLibrary(
            notebook=pipelines.NotebookLibrary(path=NOTEBOOK_PATH)
        )
    ],
    clusters=[
        pipelines.PipelineCluster(
            label="default",
            autoscale=pipelines.PipelineClusterAutoscale(
                min_workers=1,
                max_workers=4
            )
        )
    ],
    development=False,
    edition="ADVANCED",
    configuration={
        "pipelines.applyChangesPreviewEnabled": "true",
        "spark.databricks.delta.optimizeWrite.enabled": "true",
        "spark.databricks.delta.autoCompact.enabled": "true"
    }
)

# Create or update pipeline
if existing_pipeline_id:
    print("\n[2/4] Updating existing pipeline...")
    try:
        w.pipelines.update(
            pipeline_id=existing_pipeline_id,
            name=pipeline_config.name,
            catalog=pipeline_config.catalog,
            target=pipeline_config.target,
            storage=pipeline_config.storage,
            continuous=pipeline_config.continuous,
            channel=pipeline_config.channel,
            photon=pipeline_config.photon,
            libraries=pipeline_config.libraries,
            clusters=pipeline_config.clusters,
            development=pipeline_config.development,
            edition=pipeline_config.edition,
            configuration=pipeline_config.configuration
        )
        pipeline_id = existing_pipeline_id
        print(f"  ✅ Pipeline updated: {pipeline_id}")
    except Exception as e:
        print(f"  ❌ Error updating pipeline: {e}")
        exit(1)
else:
    print("\n[2/4] Creating new pipeline...")
    try:
        response = w.pipelines.create(
            name=pipeline_config.name,
            catalog=pipeline_config.catalog,
            target=pipeline_config.target,
            storage=pipeline_config.storage,
            continuous=pipeline_config.continuous,
            channel=pipeline_config.channel,
            photon=pipeline_config.photon,
            libraries=pipeline_config.libraries,
            clusters=pipeline_config.clusters,
            development=pipeline_config.development,
            edition=pipeline_config.edition,
            configuration=pipeline_config.configuration
        )
        pipeline_id = response.pipeline_id
        print(f"  ✅ Pipeline created: {pipeline_id}")
    except Exception as e:
        print(f"  ❌ Error creating pipeline: {e}")
        exit(1)

# Start pipeline
print("\n[3/4] Starting pipeline...")
try:
    w.pipelines.start_update(
        pipeline_id=pipeline_id,
        full_refresh=False
    )
    print(f"  ✅ Pipeline started")
except Exception as e:
    print(f"  ⚠️  Could not start pipeline: {e}")
    print(f"  ℹ️  You can start it manually in the UI")

# Monitor initial startup
print("\n[4/4] Monitoring pipeline startup (60 seconds)...")
for i in range(12):
    time.sleep(5)
    try:
        pipeline_status = w.pipelines.get(pipeline_id)
        state = pipeline_status.state if pipeline_status.state else "UNKNOWN"
        print(f"  [{i+1}/12] State: {state}")

        if state in ["RUNNING", "IDLE"]:
            print(f"  ✅ Pipeline is {state}")
            break
    except Exception as e:
        print(f"  ⚠️  Error checking status: {e}")

print("\n" + "=" * 80)
print("✅ DLT PIPELINE DEPLOYMENT COMPLETE")
print("=" * 80)
print(f"""
Pipeline Details:
- ID: {pipeline_id}
- Name: {PIPELINE_NAME}
- Target: {CATALOG}.{TARGET_SCHEMA}
- Mode: Continuous
- Photon: Enabled

View pipeline:
https://e2-demo-field-eng.cloud.databricks.com/#joblist/pipelines/{pipeline_id}

Tables created:
- {CATALOG}.{TARGET_SCHEMA}.bronze_sensor_events
- {CATALOG}.{TARGET_SCHEMA}.silver_enriched_sensors
- {CATALOG}.{TARGET_SCHEMA}.gold_ml_features
- {CATALOG}.{TARGET_SCHEMA}.gold_equipment_360 (view)
""")
