#!/usr/bin/env python3
"""
Execute Zerobus table setup SQL with permissions
"""

from databricks.sdk import WorkspaceClient
import time

# Initialize client
w = WorkspaceClient()

# SQL statements to execute
sql_statements = [
    "USE CATALOG `ignition-genie`",

    """CREATE SCHEMA IF NOT EXISTS mining_ops
    COMMENT 'Mining operations data from Ignition Gateway'""",

    "USE SCHEMA mining_ops",

    "DROP TABLE IF EXISTS tag_events_raw",

    """CREATE TABLE tag_events_raw (
      event_id STRING COMMENT 'Unique event identifier',
      event_time TIMESTAMP COMMENT 'Event timestamp from Ignition',
      tag_path STRING COMMENT 'Full Ignition tag path',
      tag_provider STRING COMMENT 'Ignition tag provider name',
      numeric_value DOUBLE COMMENT 'Numeric tag value',
      string_value STRING COMMENT 'String tag value',
      boolean_value BOOLEAN COMMENT 'Boolean tag value',
      quality STRING COMMENT 'Quality indicator (GOOD, BAD, UNCERTAIN)',
      quality_code INT COMMENT 'Numeric quality code',
      source_system STRING COMMENT 'Source Ignition Gateway identifier',
      ingestion_timestamp TIMESTAMP COMMENT 'Time ingested into Databricks',
      data_type STRING COMMENT 'Original data type from Ignition',
      alarm_state STRING COMMENT 'Alarm state if applicable',
      alarm_priority INT COMMENT 'Alarm priority if applicable'
    )
    USING DELTA
    TBLPROPERTIES (
      'delta.autoOptimize.optimizeWrite' = 'true',
      'delta.autoOptimize.autoCompact' = 'true'
    )
    COMMENT 'Raw tag events from Ignition via Zerobus connector'""",

    "GRANT USE CATALOG ON CATALOG `ignition-genie` TO `account users`",
    "GRANT USE SCHEMA ON SCHEMA mining_ops TO `account users`",
    "GRANT SELECT, MODIFY ON TABLE tag_events_raw TO `account users`",

    "DESCRIBE EXTENDED tag_events_raw",
]

# Use Reyden Warehouse (running)
warehouse_id = "000000000000000d"

print(f"Executing SQL statements on warehouse {warehouse_id}...")

for i, sql in enumerate(sql_statements, 1):
    print(f"\n[{i}/{len(sql_statements)}] Executing: {sql[:80]}{'...' if len(sql) > 80 else ''}")

    try:
        # Execute statement
        statement = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout="30s"
        )

        # Check result
        if statement.status.state == "SUCCEEDED":
            print(f"✓ Success")
            if statement.result:
                # Print results if any (like DESCRIBE)
                if statement.result.data_array:
                    for row in statement.result.data_array[:5]:  # Show first 5 rows
                        print(f"  {row}")
        else:
            print(f"✗ Failed: {statement.status.state}")
            if statement.status.error:
                print(f"  Error: {statement.status.error.message}")

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        if "permission" in str(e).lower():
            print("  Hint: You may need admin privileges to grant permissions")
        continue

print("\n" + "="*80)
print("Table setup complete!")
print("Target table: ignition-genie.mining_ops.tag_events_raw")
print("="*80)
