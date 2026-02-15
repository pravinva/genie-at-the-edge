#!/usr/bin/env python3
"""Get DLT Pipeline Error Details"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
pipeline_id = "9744a549-24f1-4650-8585-37cc323d5451"

# Get update details
updates = w.pipelines.list_pipeline_events(pipeline_id=pipeline_id, max_results=50)

print("="*80)
print("DLT Pipeline Events (Recent Errors)")
print("="*80)

for event in updates:
    if event.level == "ERROR" or event.level == "WARN":
        print(f"\n[{event.timestamp}] {event.level}")
        print(f"  {event.message}")
        if event.details:
            print(f"  Details: {event.details}")

print("\n" + "="*80)
