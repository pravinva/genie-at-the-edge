#!/usr/bin/env python3
"""
Populate Enterprise Data Tables with corrected SQL
Fixes INSERT statements that failed in initial run
"""
from databricks.sdk import WorkspaceClient
import time

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

CATALOG = "field_engineering"
SCHEMA = "mining_demo"

print("=" * 80)
print("POPULATING ENTERPRISE DATA TABLES")
print("=" * 80)

def execute_sql(sql, description):
    print(f"\n{description}...")
    try:
        result = w.statement_execution.execute_statement(
            statement=sql,
            warehouse_id=warehouse_id,
            wait_timeout='0s'
        )

        # Poll for completion
        for _ in range(30):
            time.sleep(1)
            status = w.statement_execution.get_statement(result.statement_id)

            if status.status.state.value == 'SUCCEEDED':
                print(f"  ✅ Success")
                return True
            elif status.status.state.value in ['FAILED', 'CANCELED', 'CLOSED']:
                if status.status.error:
                    print(f"  ❌ Error: {status.status.error.message[:200]}")
                else:
                    print(f"  ❌ Failed with status: {status.status.state.value}")
                return False

        print(f"  ⚠️  Timeout waiting for query")
        return False

    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:200]}")
        return False

# ============================================================================
# HISTORIAN INCIDENTS (Fixed)
# ============================================================================

print("\n[1/5] Populating historian_incidents...")

insert_incidents_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.historian_incidents
SELECT
  CONCAT('INC-', LPAD(CAST(seq AS STRING), 5, '0')) as incident_id,
  equipment_id,
  date_sub(CURRENT_TIMESTAMP(), CAST(RAND() * 90 AS INT)) as incident_timestamp,
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
# MES PRODUCTION SCHEDULE (Fixed)
# ============================================================================

print("\n[2/5] Populating mes_production_schedule...")

insert_schedule_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.mes_production_schedule
SELECT
  date_add(CURRENT_TIMESTAMP(), seq) as schedule_hour,
  CASE
    WHEN HOUR(date_add(CURRENT_TIMESTAMP(), seq)) BETWEEN 6 AND 13 THEN 'Day'
    WHEN HOUR(date_add(CURRENT_TIMESTAMP(), seq)) BETWEEN 14 AND 21 THEN 'Night'
    ELSE 'Graveyard'
  END as shift,
  CASE
    WHEN HOUR(date_add(CURRENT_TIMESTAMP(), seq)) BETWEEN 8 AND 19 THEN 1200
    ELSE 800
  END as planned_throughput_tph,
  CASE WHEN MOD(seq, 3) = 0 THEN 'Iron Ore' ELSE 'Copper Ore' END as product_type,
  0.95 as quality_target,
  CASE
    WHEN HOUR(date_add(CURRENT_TIMESTAMP(), seq)) BETWEEN 8 AND 19 THEN 12
    ELSE 8
  END as crew_size,
  CASE
    WHEN HOUR(date_add(CURRENT_TIMESTAMP(), seq)) BETWEEN 10 AND 15 THEN 'high'
    ELSE 'normal'
  END as priority
FROM (SELECT explode(sequence(0, 23)) as seq)
"""
execute_sql(insert_schedule_sql, "Inserting 24-hour production schedule")

# ============================================================================
# MES WORK ORDERS (Fixed)
# ============================================================================

print("\n[3/5] Populating mes_work_orders...")

insert_work_orders_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.mes_work_orders
SELECT
  CONCAT('WO-', LPAD(CAST(seq AS STRING), 6, '0')) as work_order_id,
  equipment_id,
  order_type,
  date_add(CURRENT_DATE(), CAST(RAND() * 14 AS INT)) as scheduled_date,
  RAND() * 7 + 1 as estimated_hours,
  priority,
  CASE WHEN RAND() > 0.3 THEN 'open' ELSE 'scheduled' END as status,
  CONCAT('Tech-', LPAD(CAST(CAST(RAND() * 10 AS INT) AS STRING), 2, '0')) as assigned_technician
FROM (
  SELECT explode(sequence(0, 29)) as seq
) orders
CROSS JOIN (
  SELECT explode(array('HAUL-001', 'HAUL-002', 'HAUL-003', 'CRUSH-001', 'CRUSH-002')) as equipment_id
) equipment
CROSS JOIN (
  SELECT explode(array('preventive', 'predictive', 'corrective')) as order_type
) types
CROSS JOIN (
  SELECT explode(array('high', 'medium', 'low')) as priority
) priorities
LIMIT 30
"""
execute_sql(insert_work_orders_sql, "Inserting 30 work orders")

# ============================================================================
# MES QUALITY METRICS (Fixed)
# ============================================================================

print("\n[4/5] Populating mes_quality_metrics...")

insert_quality_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.mes_quality_metrics
SELECT
  CONCAT('QC-', LPAD(CAST(seq AS STRING), 6, '0')) as sample_id,
  date_sub(CURRENT_TIMESTAMP(), CAST(RAND() * 7 AS INT)) as sample_timestamp,
  product_type,
  95 + RAND() * 4.5 as quality_score,
  RAND() * 0.05 as contamination_pct,
  850 + RAND() * 300 as particle_size_microns,
  10 + RAND() * 5 as moisture_pct,
  CASE WHEN RAND() > 0.15 THEN 'pass' ELSE 'fail' END as pass_fail
FROM (
  SELECT explode(sequence(0, 99)) as seq
) samples
CROSS JOIN (
  SELECT explode(array('Iron Ore', 'Copper Ore')) as product_type
) products
LIMIT 100
"""
execute_sql(insert_quality_sql, "Inserting 100 quality samples")

# ============================================================================
# SAP MAINTENANCE HISTORY (Fixed)
# ============================================================================

print("\n[5/5] Populating sap_maintenance_history...")

insert_maintenance_sql = f"""
INSERT INTO {CATALOG}.{SCHEMA}.sap_maintenance_history
SELECT
  CONCAT('MAINT-', LPAD(CAST(seq AS STRING), 6, '0')) as maintenance_id,
  equipment_id,
  date_sub(CURRENT_DATE(), CAST(RAND() * 365 AS INT)) as maintenance_date,
  maint_type,
  parts,
  500 + RAND() * 4500 as cost_usd,
  2 + RAND() * 6 as duration_hours,
  CASE WHEN RAND() > 0.1 THEN 'completed' ELSE 'failed' END as completion_status
FROM (
  SELECT explode(sequence(0, 199)) as seq
) records
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

# ============================================================================
# VERIFY DATA
# ============================================================================

print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

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
        warehouse_id=warehouse_id,
        wait_timeout='0s'
    )

    time.sleep(1)
    status = w.statement_execution.get_statement(result.statement_id)

    if status.status.state.value == 'SUCCEEDED' and status.result and status.result.data_array:
        count = int(status.result.data_array[0][0])
        icon = '✅' if count > 0 else '⚠️ '
        print(f"  {icon} {table:<35} {count:>6} rows")

print("\n" + "=" * 80)
print("✅ ENTERPRISE DATA POPULATION COMPLETE")
print("=" * 80)
