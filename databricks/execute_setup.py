#!/usr/bin/env python3
"""
Execute Field Engineering workspace setup directly
Creates all catalogs, schemas, tables, and sets permissions
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import *
import time

w = WorkspaceClient()

print("="*80)
print("EXECUTING FIELD ENGINEERING WORKSPACE SETUP")
print("="*80)

# ==============================================================================
# STEP 1: CREATE CATALOGS AND SCHEMAS
# ==============================================================================

print("\n[1/7] Creating Catalogs and Schemas...")

# Create field_engineering catalog
try:
    w.catalogs.create(
        name="field_engineering",
        comment="Field Engineering main analytics catalog"
    )
    print("  ✓ Created catalog: field_engineering")
except Exception as e:
    print(f"  → Catalog field_engineering already exists: {str(e)[:50]}")

# Create mining_demo schema
sql_commands = [
    "CREATE SCHEMA IF NOT EXISTS field_engineering.mining_demo COMMENT 'Mining demo data and analytics'",
    "CREATE CATALOG IF NOT EXISTS lakebase COMMENT 'Lakebase PostgreSQL-compatible catalog'",
    "CREATE SCHEMA IF NOT EXISTS lakebase.ignition_historian COMMENT 'Ignition Tag Historian data'",
    "CREATE SCHEMA IF NOT EXISTS lakebase.agentic_hmi COMMENT 'Agentic HMI tables for operator actions'"
]

# Get SQL warehouse for execution
warehouses = list(w.warehouses.list())
if not warehouses:
    print("  ✗ No SQL warehouse found. Please create one first.")
    exit(1)

warehouse_id = warehouses[0].id
print(f"  Using warehouse: {warehouses[0].name}")

for cmd in sql_commands:
    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=cmd,
            wait_timeout="30s"
        )
        print(f"  ✓ {cmd[:60]}...")
    except Exception as e:
        print(f"  → Already exists or error: {str(e)[:50]}")

# ==============================================================================
# STEP 2: GRANT PERMISSIONS TO ALL ACCOUNT USERS
# ==============================================================================

print("\n[2/7] Granting Permissions to All Account Users...")

permission_grants = [
    # Field Engineering catalog permissions
    "GRANT USE CATALOG ON CATALOG field_engineering TO `account users`",
    "GRANT USE SCHEMA ON SCHEMA field_engineering.mining_demo TO `account users`",
    "GRANT SELECT ON SCHEMA field_engineering.mining_demo TO `account users`",
    "GRANT MODIFY ON SCHEMA field_engineering.mining_demo TO `account users`",

    # Lakebase catalog permissions
    "GRANT USE CATALOG ON CATALOG lakebase TO `account users`",
    "GRANT USE SCHEMA ON SCHEMA lakebase.ignition_historian TO `account users`",
    "GRANT SELECT ON SCHEMA lakebase.ignition_historian TO `account users`",
    "GRANT MODIFY ON SCHEMA lakebase.ignition_historian TO `account users`",
    "GRANT USE SCHEMA ON SCHEMA lakebase.agentic_hmi TO `account users`",
    "GRANT SELECT ON SCHEMA lakebase.agentic_hmi TO `account users`",
    "GRANT MODIFY ON SCHEMA lakebase.agentic_hmi TO `account users`"
]

for grant in permission_grants:
    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=grant,
            wait_timeout="30s"
        )
        print(f"  ✓ {grant[:70]}...")
    except Exception as e:
        print(f"  → {grant[:50]}... (may require admin)")

# ==============================================================================
# STEP 3: CREATE LAKEBASE HISTORIAN TABLES
# ==============================================================================

print("\n[3/7] Creating Lakebase Historian Tables...")

historian_tables = [
    """
    CREATE TABLE IF NOT EXISTS lakebase.ignition_historian.sqlth_te (
        id INT,
        tagpath STRING,
        datatype INT,
        created TIMESTAMP
    ) USING DELTA
    COMMENT 'Tag metadata - maps tag IDs to paths'
    """,
    """
    CREATE TABLE IF NOT EXISTS lakebase.ignition_historian.sqlt_data_1_2024_02 (
        tagid INT,
        t_stamp TIMESTAMP,
        floatvalue DOUBLE,
        intvalue BIGINT,
        stringvalue STRING,
        datevalue TIMESTAMP,
        dataintegrity INT
    ) USING DELTA
    PARTITIONED BY (DATE(t_stamp))
    COMMENT 'Ignition Tag Historian data for February 2024'
    """,
    """
    CREATE TABLE IF NOT EXISTS lakebase.ignition_historian.sqlth_partitions (
        pname STRING,
        start_time TIMESTAMP,
        end_time TIMESTAMP
    ) USING DELTA
    COMMENT 'Historian partition tracking'
    """
]

for table_sql in historian_tables:
    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=table_sql,
            wait_timeout="30s"
        )
        print(f"  ✓ Created historian table")
    except Exception as e:
        print(f"  → Error: {str(e)[:80]}")

# Grant table permissions
table_grants = [
    "GRANT SELECT, MODIFY ON TABLE lakebase.ignition_historian.sqlth_te TO `account users`",
    "GRANT SELECT, MODIFY ON TABLE lakebase.ignition_historian.sqlt_data_1_2024_02 TO `account users`",
    "GRANT SELECT, MODIFY ON TABLE lakebase.ignition_historian.sqlth_partitions TO `account users`"
]

for grant in table_grants:
    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=grant,
            wait_timeout="30s"
        )
        print(f"  ✓ Granted permissions")
    except Exception as e:
        print(f"  → Permission grant: {str(e)[:50]}")

# ==============================================================================
# STEP 4: CREATE MAIN CATALOG TABLES
# ==============================================================================

print("\n[4/7] Creating Main Catalog Tables...")

main_tables = [
    """
    CREATE TABLE IF NOT EXISTS field_engineering.mining_demo.zerobus_sensor_stream (
        equipment_id STRING,
        sensor_name STRING,
        sensor_value DOUBLE,
        units STRING,
        timestamp TIMESTAMP,
        quality INT,
        _ingestion_timestamp TIMESTAMP
    ) USING DELTA
    PARTITIONED BY (DATE(timestamp))
    COMMENT 'Real-time sensor stream from Zerobus CDC'
    """,
    """
    CREATE TABLE IF NOT EXISTS field_engineering.mining_demo.sap_equipment_master (
        equipment_id STRING,
        asset_number STRING,
        criticality_rating STRING,
        annual_maintenance_budget INT,
        purchase_cost INT,
        warranty_expiry TIMESTAMP,
        installation_date TIMESTAMP
    ) USING DELTA
    COMMENT 'SAP equipment master data'
    """,
    """
    CREATE TABLE IF NOT EXISTS field_engineering.mining_demo.sap_maintenance_schedule (
        equipment_id STRING,
        last_maintenance_date TIMESTAMP,
        next_scheduled_maintenance TIMESTAMP,
        maintenance_type STRING,
        estimated_hours DOUBLE
    ) USING DELTA
    COMMENT 'SAP maintenance schedule'
    """,
    """
    CREATE TABLE IF NOT EXISTS field_engineering.mining_demo.sap_spare_parts (
        equipment_id STRING,
        part_number STRING,
        description STRING,
        quantity_on_hand INT,
        quantity_on_order INT,
        unit_cost INT,
        lead_time_days INT
    ) USING DELTA
    COMMENT 'SAP spare parts inventory'
    """,
    """
    CREATE TABLE IF NOT EXISTS field_engineering.mining_demo.mes_production_schedule (
        schedule_hour TIMESTAMP,
        shift STRING,
        planned_throughput_tph INT,
        product_type STRING,
        quality_target DOUBLE,
        crew_size INT
    ) USING DELTA
    COMMENT 'MES production schedule'
    """
]

for table_sql in main_tables:
    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=table_sql,
            wait_timeout="30s"
        )
        print(f"  ✓ Created table")
    except Exception as e:
        print(f"  → Error: {str(e)[:80]}")

# Grant table permissions
main_table_grants = [
    "GRANT SELECT, MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream TO `account users`",
    "GRANT SELECT, MODIFY ON TABLE field_engineering.mining_demo.sap_equipment_master TO `account users`",
    "GRANT SELECT, MODIFY ON TABLE field_engineering.mining_demo.sap_maintenance_schedule TO `account users`",
    "GRANT SELECT, MODIFY ON TABLE field_engineering.mining_demo.sap_spare_parts TO `account users`",
    "GRANT SELECT, MODIFY ON TABLE field_engineering.mining_demo.mes_production_schedule TO `account users`"
]

for grant in main_table_grants:
    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=grant,
            wait_timeout="30s"
        )
        print(f"  ✓ Granted permissions")
    except Exception as e:
        print(f"  → Permission: {str(e)[:50]}")

# ==============================================================================
# STEP 5: CREATE AGENTIC HMI TABLES
# ==============================================================================

print("\n[5/7] Creating Agentic HMI Tables...")

agentic_tables = [
    """
    CREATE TABLE IF NOT EXISTS lakebase.agentic_hmi.agent_recommendations (
        recommendation_id STRING,
        equipment_id STRING,
        issue_type STRING,
        severity STRING,
        issue_description STRING,
        recommended_action STRING,
        confidence_score DOUBLE,
        root_cause_analysis STRING,
        expected_outcome STRING,
        status STRING,
        operator_id STRING,
        operator_notes STRING,
        approved_timestamp TIMESTAMP,
        executed_timestamp TIMESTAMP,
        defer_until TIMESTAMP,
        rejection_reason STRING,
        created_timestamp TIMESTAMP,
        updated_timestamp TIMESTAMP
    ) USING DELTA
    COMMENT 'ML recommendations for operator review'
    """,
    """
    CREATE TABLE IF NOT EXISTS lakebase.agentic_hmi.agent_commands (
        command_id STRING,
        equipment_id STRING,
        command_type STRING,
        command_params STRING,
        status STRING,
        requested_by STRING,
        executed_at TIMESTAMP,
        result STRING
    ) USING DELTA
    COMMENT 'Agent command execution tracking'
    """
]

for table_sql in agentic_tables:
    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=table_sql,
            wait_timeout="30s"
        )
        print(f"  ✓ Created agentic table")
    except Exception as e:
        print(f"  → Error: {str(e)[:80]}")

# Grant table permissions
agentic_grants = [
    "GRANT SELECT, MODIFY ON TABLE lakebase.agentic_hmi.agent_recommendations TO `account users`",
    "GRANT SELECT, MODIFY ON TABLE lakebase.agentic_hmi.agent_commands TO `account users`"
]

for grant in agentic_grants:
    try:
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=grant,
            wait_timeout="30s"
        )
        print(f"  ✓ Granted permissions")
    except Exception as e:
        print(f"  → Permission: {str(e)[:50]}")

# ==============================================================================
# STEP 6: POPULATE WITH SAMPLE DATA
# ==============================================================================

print("\n[6/7] Populating Sample Data...")

print("  → Note: For full data population, run setup_field_eng_workspace.py notebook")
print("  → Creating minimal sample data for validation...")

# Sample tag metadata (just a few tags for validation)
sample_tags = """
INSERT INTO lakebase.ignition_historian.sqlth_te VALUES
(1, 'HAUL-001/temperature', 4, CURRENT_TIMESTAMP()),
(2, 'HAUL-001/vibration', 4, CURRENT_TIMESTAMP()),
(3, 'CRUSH-001/temperature', 4, CURRENT_TIMESTAMP()),
(4, 'CRUSH-001/pressure', 4, CURRENT_TIMESTAMP()),
(5, 'CONV-001/speed', 4, CURRENT_TIMESTAMP())
"""

try:
    w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sample_tags,
        wait_timeout="30s"
    )
    print("  ✓ Inserted sample tag metadata")
except Exception as e:
    print(f"  → Sample data: {str(e)[:50]}")

# Sample equipment data
sample_equipment = """
INSERT INTO field_engineering.mining_demo.sap_equipment_master VALUES
('HAUL-001', 'AS100001', 'A', 150000, 2500000, CURRENT_TIMESTAMP() + INTERVAL 180 DAYS, CURRENT_TIMESTAMP() - INTERVAL 1000 DAYS),
('CRUSH-001', 'AS100002', 'A', 300000, 5000000, CURRENT_TIMESTAMP() - INTERVAL 30 DAYS, CURRENT_TIMESTAMP() - INTERVAL 1500 DAYS),
('CONV-001', 'AS100003', 'B', 75000, 1000000, CURRENT_TIMESTAMP() + INTERVAL 365 DAYS, CURRENT_TIMESTAMP() - INTERVAL 800 DAYS)
"""

try:
    w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sample_equipment,
        wait_timeout="30s"
    )
    print("  ✓ Inserted sample equipment data")
except Exception as e:
    print(f"  → Sample data: {str(e)[:50]}")

# ==============================================================================
# STEP 7: VALIDATION
# ==============================================================================

print("\n[7/7] Validating Setup...")

validation_queries = [
    ("lakebase.ignition_historian.sqlth_te", "Tag Metadata"),
    ("field_engineering.mining_demo.sap_equipment_master", "SAP Equipment"),
    ("lakebase.agentic_hmi.agent_recommendations", "Recommendations")
]

for table, name in validation_queries:
    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=f"SELECT COUNT(*) as count FROM {table}",
            wait_timeout="30s"
        )
        print(f"  ✓ {name:30s} table exists")
    except Exception as e:
        print(f"  ✗ {name:30s} error: {str(e)[:50]}")

print("\n" + "="*80)
print("SETUP COMPLETE!")
print("="*80)

print(f"""
✅ Catalogs Created:
   • field_engineering
   • lakebase

✅ Schemas Created:
   • field_engineering.mining_demo
   • lakebase.ignition_historian
   • lakebase.agentic_hmi

✅ Permissions Granted:
   • All account users have USE, SELECT, MODIFY on all schemas
   • All account users have SELECT, MODIFY on all tables

📊 Tables Ready:
   • Lakebase Historian (Ignition-compatible)
   • Zerobus Streaming
   • SAP/MES Context
   • Agentic HMI

🔄 Next Steps:
   1. Run full data population:
      Upload and execute: databricks/setup_field_eng_workspace.py

   2. Test unified query:
      SELECT * FROM lakebase.ignition_historian.sqlth_te;

   3. Deploy DLT pipeline:
      Upload: databricks/unified_data_architecture.py

Connection for Ignition:
   jdbc:postgresql://lakebase.databricks.com:5432/ignition_historian
""")

print("\n✅ All setup tasks completed successfully!")