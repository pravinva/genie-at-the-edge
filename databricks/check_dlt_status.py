#!/usr/bin/env python3
"""
Check DLT Pipeline Status and Query Gold Tables
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.pipelines import PipelineStateInfo
import time

w = WorkspaceClient()

pipeline_id = "9744a549-24f1-4650-8585-37cc323d5451"

print("="*80)
print("Mining Operations DLT Pipeline Status")
print("="*80)

# Get pipeline details
pipeline = w.pipelines.get(pipeline_id=pipeline_id)

print(f"\nPipeline: {pipeline.name}")
print(f"ID: {pipeline.pipeline_id}")
print(f"State: {pipeline.state}")
print(f"Latest Update ID: {pipeline.latest_updates[0].update_id if pipeline.latest_updates else 'None'}")

if pipeline.latest_updates:
    latest = pipeline.latest_updates[0]
    print(f"\nLatest Update:")
    print(f"  Update ID: {latest.update_id}")
    print(f"  State: {latest.state}")
    print(f"  Creation Time: {latest.creation_time}")

print(f"\nPipeline URL:")
print(f"https://e2-demo-field-eng.cloud.databricks.com/#joblist/pipelines/{pipeline_id}")

print("\n" + "="*80)
print("Checking Gold Tables (may take a few minutes to populate)...")
print("="*80)

# Wait a bit for tables to be created
time.sleep(5)

# Try to query tables
warehouse_id = "000000000000000d"  # Reyden Warehouse

tables_to_check = [
    "ignition_genie.mining_demo.tag_events_bronze",
    "ignition_genie.mining_demo.equipment_sensors_normalized",
    "ignition_genie.mining_demo.equipment_performance_1min",
    "ignition_genie.mining_demo.equipment_current_status"
]

for table in tables_to_check:
    print(f"\n[{table}]")
    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=f"SELECT COUNT(*) as cnt FROM {table}",
            wait_timeout="30s"
        )

        if result.result and result.result.data_array:
            count = result.result.data_array[0][0]
            print(f"  ✓ Row count: {count}")
        else:
            print(f"  ⏳ Table exists but may be empty (pipeline still starting)")

    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg.lower() or "table_or_view_not_found" in error_msg.lower():
            print(f"  ⏳ Table not created yet (pipeline still initializing)")
        else:
            print(f"  ⚠ Error: {error_msg[:100]}")

print("\n" + "="*80)
print("Next Steps:")
print("="*80)
print("1. Monitor pipeline in UI (link above)")
print("2. Wait 5-10 minutes for initial data population")
print("3. Query gold tables to verify data flow")
print("4. Deploy Genie Space for AI queries")
print("="*80)
