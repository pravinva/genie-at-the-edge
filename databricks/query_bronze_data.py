#!/usr/bin/env python3
"""
Query Bronze Table Directly
"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
warehouse_id = "000000000000000d"

print("="*80)
print("Querying Bronze Table: ignition_genie.mining_ops.tag_events_raw")
print("="*80)

# Count total rows
sql = "SELECT COUNT(*) as cnt FROM ignition_genie.mining_ops.tag_events_raw"
result = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql,
    wait_timeout="30s"
)

if result.result and result.result.data_array:
    count = result.result.data_array[0][0]
    print(f"\n✓ Total events in bronze table: {count:,}")

# Sample data
sql2 = """
SELECT
    event_time,
    tag_path,
    numeric_value,
    quality
FROM ignition_genie.mining_ops.tag_events_raw
ORDER BY event_time DESC
LIMIT 10
"""

result2 = w.statement_execution.execute_statement(
    warehouse_id=warehouse_id,
    statement=sql2,
    wait_timeout="30s"
)

if result2.result and result2.result.data_array:
    print("\n✓ Latest 10 events:")
    print(f"{'Time':<25} {'Tag Path':<60} {'Value':<10} {'Quality':<10}")
    print("-"*110)
    for row in result2.result.data_array:
        event_time, tag_path, value, quality = row
        print(f"{str(event_time):<25} {tag_path:<60} {value if value else 'NULL':<10} {quality:<10}")

print("\n" + "="*80)
