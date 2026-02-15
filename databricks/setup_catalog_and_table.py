#!/usr/bin/env python3
"""
Create Ignition-Genie catalog, schema, and table with permissions
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import CatalogInfo, SchemaInfo, TableType
import time

# Initialize client
w = WorkspaceClient()

print("="*80)
print("Setting up Ignition-Genie Catalog and Table")
print("="*80)

# Step 1: Create catalog
catalog_name = "ignition_genie"
print(f"\n[1/5] Creating catalog: {catalog_name}")
try:
    catalog = w.catalogs.create(
        name=catalog_name,
        comment="Ignition Gateway data for Genie at the Edge demo"
    )
    print(f"✓ Created catalog: {catalog_name}")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"✓ Catalog {catalog_name} already exists")
    else:
        print(f"✗ Error: {str(e)}")

# Step 2: Create schema
schema_name = "mining_ops"
full_schema = f"{catalog_name}.{schema_name}"
print(f"\n[2/5] Creating schema: {full_schema}")
try:
    schema = w.schemas.create(
        name=schema_name,
        catalog_name=catalog_name,
        comment="Mining operations data from Ignition Gateway"
    )
    print(f"✓ Created schema: {full_schema}")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"✓ Schema {full_schema} already exists")
    else:
        print(f"✗ Error: {str(e)}")

# Step 3: Create table using SQL warehouse
warehouse_id = "000000000000000d"  # Reyden Warehouse
full_table = f"{catalog_name}.{schema_name}.tag_events_raw"

print(f"\n[3/5] Dropping old table (if exists): {full_table}")
try:
    drop_sql = f"DROP TABLE IF EXISTS {full_table}"
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=drop_sql,
        wait_timeout="30s"
    )
    print(f"✓ Old table dropped")
except Exception as e:
    print(f"✗ Error: {str(e)}")

print(f"\n[4/5] Creating table with Zerobus schema: {full_table}")
create_table_sql = f"""
CREATE TABLE {full_table} (
  event_id STRING,
  event_time TIMESTAMP,
  tag_path STRING,
  tag_provider STRING,
  numeric_value DOUBLE,
  string_value STRING,
  boolean_value BOOLEAN,
  quality STRING,
  quality_code INT,
  source_system STRING,
  ingestion_timestamp TIMESTAMP,
  data_type STRING,
  alarm_state STRING,
  alarm_priority INT
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
"""

try:
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=create_table_sql,
        wait_timeout="30s"
    )
    if statement.status.state == "SUCCEEDED":
        print(f"✓ Table created successfully")
    else:
        print(f"✗ Failed: {statement.status.state}")
        if statement.status.error:
            print(f"  Error: {statement.status.error.message}")
except Exception as e:
    print(f"✗ Error: {str(e)}")

# Step 5: Grant permissions using SDK
print(f"\n[5/5] Granting permissions to account users")
try:
    # Grant on catalog
    w.grants.update(
        securable_type="CATALOG",
        full_name=catalog_name,
        changes=[
            {
                "add": [
                    {"principal": "account users", "privileges": ["USE_CATALOG", "USE_SCHEMA"]}
                ]
            }
        ]
    )
    print(f"✓ Granted USE_CATALOG on {catalog_name}")
except Exception as e:
    print(f"  Catalog permissions: {str(e)}")

try:
    # Grant on schema
    w.grants.update(
        securable_type="SCHEMA",
        full_name=full_schema,
        changes=[
            {
                "add": [
                    {"principal": "account users", "privileges": ["USE_SCHEMA", "SELECT"]}
                ]
            }
        ]
    )
    print(f"✓ Granted USE_SCHEMA on {full_schema}")
except Exception as e:
    print(f"  Schema permissions: {str(e)}")

try:
    # Grant on table
    w.grants.update(
        securable_type="TABLE",
        full_name=full_table,
        changes=[
            {
                "add": [
                    {"principal": "account users", "privileges": ["SELECT", "MODIFY"]}
                ]
            }
        ]
    )
    print(f"✓ Granted SELECT, MODIFY on {full_table}")
except Exception as e:
    print(f"  Table permissions: {str(e)}")

print("\n" + "="*80)
print("Setup Complete!")
print(f"Catalog: {catalog_name}")
print(f"Schema: {schema_name}")
print(f"Table: {full_table}")
print("="*80)
print(f"\nZerobus Configuration:")
print(f"  Target Table: {full_table}")
print(f"  Endpoint: 1444828305810485.zerobus.us-west-2.cloud.databricks.com")
print("="*80)
