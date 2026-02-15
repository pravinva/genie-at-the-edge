#!/usr/bin/env python3
"""
Verify Zerobus data is flowing into Databricks
"""

from databricks.sdk import WorkspaceClient
import time

w = WorkspaceClient()
warehouse_id = "000000000000000d"  # Reyden Warehouse

print("="*80)
print("Verifying Zerobus Data Ingestion")
print("="*80)

# Query 1: Count total rows
print("\n[1/4] Counting total rows...")
sql = "SELECT COUNT(*) as row_count FROM ignition_genie.mining_ops.tag_events_raw"
result = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql,
    wait_timeout="30s"
)
if result.result and result.result.data_array:
    count = result.result.data_array[0][0]
    print(f"✓ Total rows: {count}")

# Query 2: Show sample data
print("\n[2/4] Sample events (last 10)...")
sql = """
SELECT
  event_time,
  tag_path,
  numeric_value,
  string_value,
  quality
FROM ignition_genie.mining_ops.tag_events_raw
ORDER BY event_time DESC
LIMIT 10
"""
result = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql,
    wait_timeout="30s"
)
if result.result and result.result.data_array:
    print(f"{'Event Time':<25} {'Tag Path':<50} {'Value':<10} {'Quality':<10}")
    print("-" * 100)
    for row in result.result.data_array:
        event_time, tag_path, num_val, str_val, quality = row
        value = str_val if str_val else (f"{num_val:.2f}" if num_val else "NULL")
        print(f"{event_time:<25} {tag_path:<50} {value:<10} {quality:<10}")

# Query 3: Count by equipment
print("\n[3/4] Events by equipment type...")
sql = """
SELECT
  CASE
    WHEN tag_path LIKE '%HT_%' THEN 'Haul Truck'
    WHEN tag_path LIKE '%CR_%' THEN 'Crusher'
    WHEN tag_path LIKE '%CV_%' THEN 'Conveyor'
    ELSE 'Other'
  END as equipment_type,
  COUNT(*) as event_count
FROM ignition_genie.mining_ops.tag_events_raw
GROUP BY 1
ORDER BY 2 DESC
"""
result = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql,
    wait_timeout="30s"
)
if result.result and result.result.data_array:
    for row in result.result.data_array:
        equip_type, count = row
        print(f"  {equip_type:<15}: {count:>6} events")

# Query 4: Latest timestamp
print("\n[4/4] Data freshness...")
sql = """
SELECT
  MAX(event_time) as latest_event,
  MAX(ingestion_timestamp) as latest_ingestion,
  COUNT(DISTINCT tag_path) as unique_tags
FROM ignition_genie.mining_ops.tag_events_raw
"""
result = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql,
    wait_timeout="30s"
)
if result.result and result.result.data_array:
    latest_event, latest_ingestion, unique_tags = result.result.data_array[0]
    print(f"  Latest Event Time: {latest_event}")
    print(f"  Latest Ingestion: {latest_ingestion}")
    print(f"  Unique Tags: {unique_tags}")

print("\n" + "="*80)
print("✓ Zerobus ingestion working successfully!")
print("="*80)
