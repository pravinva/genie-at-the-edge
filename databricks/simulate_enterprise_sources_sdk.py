#!/usr/bin/env python3
"""
Simulate Enterprise Data Sources using Databricks SDK
Creates Historian, MES, and SAP data for demo
"""
from databricks.sdk import WorkspaceClient
from datetime import datetime, timedelta
import random

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

CATALOG = "field_engineering"
SCHEMA = "mining_demo"

print("=" * 80)
print("SIMULATING ENTERPRISE DATA SOURCES")
print("=" * 80)

# Helper function to execute SQL
def execute_sql(sql, description):
    print(f"\n{description}...")
    try:
        result = w.statement_execution.execute_statement(
            statement=sql,
            warehouse_id=warehouse_id
        )
        print(f"  ✅ Success")
        return result
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:200]}")
        return None

# ============================================================================
# CREATE HISTORIAN DATA (Historical Baselines)
# ============================================================================

print("\n[1/4] Creating Historian Data Tables...")

# Historian baselines table
historian_baselines_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.historian_baselines (
  equipment_id STRING,
  date DATE,
  avg_temperature DOUBLE,
  avg_vibration DOUBLE,
  avg_throughput DOUBLE,
  total_runtime_hours DOUBLE,
  anomaly_count INT,
  baseline_temp_7d DOUBLE,
  baseline_temp_30d DOUBLE,
  baseline_vibration_7d DOUBLE,
  baseline_vibration_30d DOUBLE
)
USING DELTA
"""
execute_sql(historian_baselines_sql, "Creating historian_baselines table")

# Insert 90 days of data using SQL
insert_baselines_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.historian_baselines
SELECT
  equipment_id,
  date,
  75.0 + (RAND() * 20 - 10) as avg_temperature,
  3.0 + (RAND() * 1 - 0.5) as avg_vibration,
  1000 + (RAND() * 200 - 100) as avg_throughput,
  CASE WHEN DAYOFWEEK(date) IN (1, 7) THEN 16 ELSE 24 END as total_runtime_hours,
  CAST(RAND() * 3 AS INT) as anomaly_count,
  75.0 + (RAND() * 20 - 10) as baseline_temp_7d,
  73.0 + (RAND() * 20 - 10) as baseline_temp_30d,
  3.0 + (RAND() * 1 - 0.5) as baseline_vibration_7d,
  2.9 + (RAND() * 1 - 0.5) as baseline_vibration_30d
FROM (
  SELECT equipment_id, date_sub(CURRENT_DATE(), seq) as date
  FROM (
    SELECT explode(sequence(0, 89)) as seq
  ) days
  CROSS JOIN (
    SELECT explode(array('HAUL-001', 'HAUL-002', 'HAUL-003', 'HAUL-004', 'HAUL-005',
                          'CRUSH-001', 'CRUSH-002', 'CRUSH-003',
                          'CONV-001', 'CONV-002')) as equipment_id
  ) equipment
)
"""
execute_sql(insert_baselines_sql, "Inserting 90 days of historian baseline data")

# Historian incidents table
historian_incidents_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.historian_incidents (
  incident_id STRING,
  equipment_id STRING,
  incident_timestamp TIMESTAMP,
  incident_type STRING,
  root_cause STRING,
  resolution_time_hours DOUBLE,
  production_loss_tons DOUBLE,
  severity STRING
)
USING DELTA
"""
execute_sql(historian_incidents_sql, "Creating historian_incidents table")

insert_incidents_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.historian_incidents
SELECT
  CONCAT('INC-', LPAD(CAST(seq AS STRING), 5, '0')) as incident_id,
  equipment_id,
  timestamp_sub(CURRENT_TIMESTAMP(), CAST(RAND() * 90 * 24 * 60 * 60 AS INT)) as incident_timestamp,
  incident_type,
  root_cause,
  RAND() * 7.5 + 0.5 as resolution_time_hours,
  RAND() * 4900 + 100 as production_loss_tons,
  severity
FROM (
  SELECT explode(sequence(0, 49)) as seq
) incidents
CROSS JOIN (
  SELECT explode(array('HAUL-001', 'HAUL-002', 'HAUL-003', 'CRUSH-001', 'CRUSH-002')) as equipment_id
) equipment
CROSS JOIN (
  SELECT explode(array('overheating', 'high_vibration', 'low_throughput', 'emergency_stop')) as incident_type
) types
CROSS JOIN (
  SELECT explode(array('bearing_failure', 'belt_misalignment', 'blockage', 'sensor_fault')) as root_cause
) causes
CROSS JOIN (
  SELECT explode(array('low', 'medium', 'high', 'critical')) as severity
) severities
LIMIT 50
"""
execute_sql(insert_incidents_sql, "Inserting 50 historical incidents")

# ============================================================================
# CREATE MES DATA (Manufacturing Execution System)
# ============================================================================

print("\n[2/4] Creating MES Data Tables...")

# MES production schedule
mes_schedule_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.mes_production_schedule (
  schedule_hour TIMESTAMP,
  shift STRING,
  planned_throughput_tph INT,
  product_type STRING,
  quality_target DOUBLE,
  crew_size INT,
  priority STRING
)
USING DELTA
"""
execute_sql(mes_schedule_sql, "Creating mes_production_schedule table")

insert_schedule_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.mes_production_schedule
SELECT
  timestamp_add(CURRENT_TIMESTAMP(), seq * INTERVAL 1 HOUR) as schedule_hour,
  CASE
    WHEN HOUR(timestamp_add(CURRENT_TIMESTAMP(), seq * INTERVAL 1 HOUR)) BETWEEN 6 AND 13 THEN 'Day'
    WHEN HOUR(timestamp_add(CURRENT_TIMESTAMP(), seq * INTERVAL 1 HOUR)) BETWEEN 14 AND 21 THEN 'Night'
    ELSE 'Graveyard'
  END as shift,
  CASE
    WHEN HOUR(timestamp_add(CURRENT_TIMESTAMP(), seq * INTERVAL 1 HOUR)) BETWEEN 8 AND 19 THEN 1200
    ELSE 800
  END as planned_throughput_tph,
  CASE WHEN MOD(seq, 3) = 0 THEN 'Iron Ore' ELSE 'Copper Ore' END as product_type,
  0.95 as quality_target,
  CASE
    WHEN HOUR(timestamp_add(CURRENT_TIMESTAMP(), seq * INTERVAL 1 HOUR)) BETWEEN 8 AND 19 THEN 12
    ELSE 8
  END as crew_size,
  CASE
    WHEN HOUR(timestamp_add(CURRENT_TIMESTAMP(), seq * INTERVAL 1 HOUR)) BETWEEN 10 AND 15 THEN 'high'
    ELSE 'normal'
  END as priority
FROM (SELECT explode(sequence(0, 23)) as seq)
"""
execute_sql(insert_schedule_sql, "Inserting 24-hour production schedule")

# MES work orders
mes_work_orders_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.mes_work_orders (
  work_order_id STRING,
  equipment_id STRING,
  order_type STRING,
  scheduled_date TIMESTAMP,
  estimated_hours DOUBLE,
  priority STRING,
  status STRING,
  assigned_technician STRING
)
USING DELTA
"""
execute_sql(mes_work_orders_sql, "Creating mes_work_orders table")

insert_work_orders_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.mes_work_orders
SELECT
  CONCAT('WO-', LPAD(CAST(seq AS STRING), 5, '0')) as work_order_id,
  equipment_id,
  order_type,
  timestamp_add(CURRENT_TIMESTAMP(), CAST(RAND() * 30 AS INT) * INTERVAL 1 DAY) as scheduled_date,
  RAND() * 7 + 1 as estimated_hours,
  priority,
  status,
  CONCAT('Tech-', LPAD(CAST(CAST(RAND() * 10 AS INT) + 1 AS STRING), 2, '0')) as assigned_technician
FROM (SELECT explode(sequence(0, 29)) as seq) orders
CROSS JOIN (
  SELECT explode(array('HAUL-001', 'HAUL-002', 'HAUL-003', 'CRUSH-001', 'CRUSH-002')) as equipment_id
) equipment
CROSS JOIN (
  SELECT explode(array('preventive', 'corrective', 'inspection', 'calibration')) as order_type
) types
CROSS JOIN (
  SELECT explode(array('low', 'medium', 'high', 'critical')) as priority
) priorities
CROSS JOIN (
  SELECT explode(array('pending', 'in_progress', 'completed', 'on_hold')) as status
) statuses
LIMIT 30
"""
execute_sql(insert_work_orders_sql, "Inserting 30 work orders")

# MES quality metrics
mes_quality_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.mes_quality_metrics (
  sample_timestamp TIMESTAMP,
  batch_id STRING,
  ore_grade_percent DOUBLE,
  moisture_content DOUBLE,
  particle_size_mm DOUBLE,
  contamination_ppm DOUBLE,
  quality_score DOUBLE,
  passed_qa BOOLEAN
)
USING DELTA
"""
execute_sql(mes_quality_sql, "Creating mes_quality_metrics table")

insert_quality_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.mes_quality_metrics
SELECT
  timestamp_sub(CURRENT_TIMESTAMP(), seq * INTERVAL 1 HOUR) as sample_timestamp,
  CONCAT('BATCH-', DATE_FORMAT(timestamp_sub(CURRENT_TIMESTAMP(), seq * INTERVAL 1 HOUR), 'yyyyMMdd-HH')) as batch_id,
  65 + (RAND() * 4 - 2) as ore_grade_percent,
  8 + (RAND() * 2 - 1) as moisture_content,
  25 + (RAND() * 6 - 3) as particle_size_mm,
  RAND() * 40 + 10 as contamination_ppm,
  RAND() * 0.14 + 0.85 as quality_score,
  RAND() > 0.05 as passed_qa
FROM (SELECT explode(sequence(0, 99)) as seq)
"""
execute_sql(insert_quality_sql, "Inserting 100 quality samples")

# ============================================================================
# CREATE SAP DATA (Enterprise Resource Planning)
# ============================================================================

print("\n[3/4] Creating SAP Data Tables...")

# SAP asset registry
sap_assets_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.sap_asset_registry (
  equipment_id STRING,
  asset_number STRING,
  purchase_date DATE,
  purchase_cost_usd DOUBLE,
  depreciation_years INT,
  annual_maintenance_budget DOUBLE,
  warranty_expiry DATE,
  criticality_rating STRING,
  insurance_value DOUBLE
)
USING DELTA
"""
execute_sql(sap_assets_sql, "Creating sap_asset_registry table")

insert_assets_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.sap_asset_registry
SELECT
  equipment_id,
  CONCAT('AS', CAST(CAST(RAND() * 900000 + 100000 AS INT) AS STRING)) as asset_number,
  date_sub(CURRENT_DATE(), CAST(RAND() * 2850 + 365 AS INT)) as purchase_date,
  CASE
    WHEN equipment_id LIKE 'HAUL%' THEN 2500000
    WHEN equipment_id LIKE 'CRUSH%' THEN 5000000
    ELSE 1000000
  END as purchase_cost_usd,
  10 as depreciation_years,
  CASE
    WHEN equipment_id LIKE 'HAUL%' THEN 150000
    WHEN equipment_id LIKE 'CRUSH%' THEN 300000
    ELSE 75000
  END as annual_maintenance_budget,
  date_add(CURRENT_DATE(), CAST(RAND() * 730 - 365 AS INT)) as warranty_expiry,
  CASE
    WHEN RAND() < 0.33 THEN 'A'
    WHEN RAND() < 0.67 THEN 'B'
    ELSE 'C'
  END as criticality_rating,
  CASE
    WHEN equipment_id LIKE 'HAUL%' THEN 2000000
    WHEN equipment_id LIKE 'CRUSH%' THEN 4000000
    ELSE 800000
  END as insurance_value
FROM (
  SELECT explode(array('HAUL-001', 'HAUL-002', 'HAUL-003', 'HAUL-004', 'HAUL-005',
                        'CRUSH-001', 'CRUSH-002', 'CRUSH-003',
                        'CONV-001', 'CONV-002')) as equipment_id
)
"""
execute_sql(insert_assets_sql, "Inserting 10 asset records")

# SAP maintenance history
sap_maintenance_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.sap_maintenance_history (
  maintenance_id STRING,
  equipment_id STRING,
  maintenance_date TIMESTAMP,
  maintenance_type STRING,
  cost_usd DOUBLE,
  downtime_hours DOUBLE,
  parts_replaced STRING,
  vendor STRING,
  next_scheduled DATE
)
USING DELTA
"""
execute_sql(sap_maintenance_sql, "Creating sap_maintenance_history table")

insert_maintenance_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.sap_maintenance_history
SELECT
  CONCAT('PM-', LPAD(CAST(seq AS STRING), 6, '0')) as maintenance_id,
  equipment_id,
  timestamp_sub(CURRENT_TIMESTAMP(), CAST(RAND() * 365 * 24 * 60 * 60 AS INT)) as maintenance_date,
  maint_type,
  RAND() * 49000 + 1000 as cost_usd,
  RAND() * 23 + 1 as downtime_hours,
  parts,
  CONCAT('Vendor-', LPAD(CAST(CAST(RAND() * 5 AS INT) + 1 AS STRING), 2, '0')) as vendor,
  date_add(CURRENT_DATE(), CAST(RAND() * 150 + 30 AS INT)) as next_scheduled
FROM (SELECT explode(sequence(0, 199)) as seq) records
CROSS JOIN (
  SELECT explode(array('HAUL-001', 'HAUL-002', 'HAUL-003', 'CRUSH-001', 'CRUSH-002')) as equipment_id
) equipment
CROSS JOIN (
  SELECT explode(array('scheduled', 'breakdown', 'predictive')) as maint_type
) types
CROSS JOIN (
  SELECT explode(array('bearings', 'belts', 'filters', 'hydraulics', 'electrical')) as parts
) parts_list
LIMIT 200
"""
execute_sql(insert_maintenance_sql, "Inserting 200 maintenance records")

# SAP spare parts
sap_parts_sql = f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.sap_spare_parts (
  part_number STRING,
  equipment_id STRING,
  description STRING,
  quantity_on_hand INT,
  quantity_on_order INT,
  reorder_point INT,
  unit_cost_usd DOUBLE,
  lead_time_days INT,
  last_order_date DATE
)
USING DELTA
"""
execute_sql(sap_parts_sql, "Creating sap_spare_parts table")

insert_parts_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.sap_spare_parts
SELECT
  part_number,
  equipment_id,
  description,
  CAST(RAND() * 10 AS INT) as quantity_on_hand,
  CAST(RAND() * 5 AS INT) as quantity_on_order,
  CAST(RAND() * 3 + 2 AS INT) as reorder_point,
  unit_cost,
  lead_time_days,
  date_sub(CURRENT_DATE(), CAST(RAND() * 60 AS INT)) as last_order_date
FROM (
  SELECT
    'BRG-001' as part_number,
    'Heavy Duty Bearing' as description,
    2500.0 as unit_cost,
    14 as lead_time_days
  UNION ALL SELECT 'BLT-002', 'Conveyor Belt Section', 5000.0, 21
  UNION ALL SELECT 'FLT-003', 'Hydraulic Filter', 150.0, 7
  UNION ALL SELECT 'MOT-004', 'Drive Motor', 15000.0, 45
  UNION ALL SELECT 'SEN-005', 'Temperature Sensor', 500.0, 3
) parts
CROSS JOIN (
  SELECT explode(array('HAUL-001', 'HAUL-002', 'HAUL-003', 'HAUL-004', 'HAUL-005',
                        'CRUSH-001', 'CRUSH-002', 'CRUSH-003',
                        'CONV-001', 'CONV-002')) as equipment_id
)
WHERE RAND() > 0.5
"""
execute_sql(insert_parts_sql, "Inserting spare parts inventory")

# ============================================================================
# VERIFY DATA
# ============================================================================

print("\n[4/4] Verifying Created Data...")

tables = [
    "historian_baselines",
    "historian_incidents",
    "mes_production_schedule",
    "mes_work_orders",
    "mes_quality_metrics",
    "sap_asset_registry",
    "sap_maintenance_history",
    "sap_spare_parts"
]

for table in tables:
    result = w.statement_execution.execute_statement(
        statement=f"SELECT COUNT(*) FROM {CATALOG}.{SCHEMA}.{table}",
        warehouse_id=warehouse_id
    )
    if result.result and result.result.data_array:
        count = result.result.data_array[0][0]
        print(f"  ✅ {table:<35} {count:>6} rows")

print("\n" + "=" * 80)
print("ENTERPRISE DATA SOURCES CREATED SUCCESSFULLY")
print("=" * 80)

print("""
Created Tables:
├── Historian (Time-series)
│   ├── historian_baselines       - 90 days of baseline metrics
│   └── historian_incidents       - Historical incident tracking
│
├── MES (Production)
│   ├── mes_production_schedule   - 24-hour production plan
│   ├── mes_work_orders          - Maintenance work orders
│   └── mes_quality_metrics      - Product quality tracking
│
├── SAP (Business)
│   ├── sap_asset_registry       - Asset financial data
│   ├── sap_maintenance_history  - Maintenance records
│   └── sap_spare_parts         - Inventory levels

Next Step: Create enriched views to combine real-time sensor data with enterprise context
""")
