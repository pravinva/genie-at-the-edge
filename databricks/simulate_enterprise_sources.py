"""
Simulate Enterprise Data Sources (Historian, MES, SAP)
This creates the additional context tables shown in the architecture diagram
These would normally come from enterprise systems via connectors
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime, timedelta
import random

spark = SparkSession.builder.appName("SimulateEnterpriseSources").getOrCreate()

# Configuration
CATALOG = "field_engineering"
SCHEMA = "mining_demo"

print("="*80)
print("SIMULATING ENTERPRISE DATA SOURCES")
print("="*80)

# ============================================================================
# HISTORIAN DATA (Time-series historical process data)
# ============================================================================

print("\n[1/4] Creating Historian Data (Historical Baselines)...")

# Generate 90 days of historical data for baseline calculations
def generate_historian_data():
    """
    Historian typically stores:
    - Long-term sensor history (years of data)
    - Baseline operating conditions
    - Seasonal patterns
    - Previous incident data
    """

    equipment_ids = [f"HAUL-{i:03d}" for i in range(1, 6)] + \
                   [f"CRUSH-{i:03d}" for i in range(1, 4)] + \
                   [f"CONV-{i:03d}" for i in range(1, 3)]

    data = []

    for equipment_id in equipment_ids:
        for days_ago in range(90):
            date = datetime.now() - timedelta(days=days_ago)

            # Simulate daily aggregates with seasonal patterns
            base_temp = 75.0 + (10 * random.gauss(0, 1))  # Normal operating temp
            base_vibration = 3.0 + (0.5 * random.gauss(0, 1))
            base_throughput = 1000 + (100 * random.gauss(0, 1))

            # Add weekly pattern (lower on weekends)
            if date.weekday() >= 5:  # Weekend
                base_throughput *= 0.7
                base_temp -= 5

            # Add seasonal pattern (hotter in summer months)
            if date.month in [6, 7, 8]:  # Summer
                base_temp += 8

            data.append({
                "equipment_id": equipment_id,
                "date": date.date(),
                "avg_temperature": base_temp,
                "avg_vibration": base_vibration,
                "avg_throughput": base_throughput,
                "total_runtime_hours": 24 if date.weekday() < 5 else 16,
                "anomaly_count": random.randint(0, 3),
                "baseline_temp_7d": base_temp,  # 7-day rolling average
                "baseline_temp_30d": base_temp - 2,  # 30-day rolling average
                "baseline_vibration_7d": base_vibration,
                "baseline_vibration_30d": base_vibration - 0.1
            })

    df = spark.createDataFrame(data)
    df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.historian_baselines")
    print(f"  ✓ Created historian_baselines with {df.count()} records")

    # Create incident history table
    incidents = []
    for i in range(50):
        equipment_id = random.choice(equipment_ids)
        incident_date = datetime.now() - timedelta(days=random.randint(1, 90))

        incidents.append({
            "incident_id": f"INC-{i:05d}",
            "equipment_id": equipment_id,
            "incident_timestamp": incident_date,
            "incident_type": random.choice(["overheating", "high_vibration", "low_throughput", "emergency_stop"]),
            "root_cause": random.choice(["bearing_failure", "belt_misalignment", "blockage", "sensor_fault"]),
            "resolution_time_hours": random.uniform(0.5, 8.0),
            "production_loss_tons": random.uniform(100, 5000),
            "severity": random.choice(["low", "medium", "high", "critical"])
        })

    incidents_df = spark.createDataFrame(incidents)
    incidents_df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.historian_incidents")
    print(f"  ✓ Created historian_incidents with {incidents_df.count()} records")

generate_historian_data()

# ============================================================================
# MES DATA (Manufacturing Execution System)
# ============================================================================

print("\n[2/4] Creating MES Data (Production Context)...")

def generate_mes_data():
    """
    MES typically provides:
    - Production schedules
    - Work orders
    - Quality metrics
    - Batch information
    - Downtime tracking
    """

    # Current production schedule
    schedule = []
    for i in range(24):  # Next 24 hours
        hour = datetime.now() + timedelta(hours=i)
        schedule.append({
            "schedule_hour": hour,
            "shift": "Day" if 6 <= hour.hour < 14 else "Night" if 14 <= hour.hour < 22 else "Graveyard",
            "planned_throughput_tph": 1200 if hour.hour in range(8, 20) else 800,
            "product_type": "Iron Ore" if i % 3 == 0 else "Copper Ore",
            "quality_target": 0.95,
            "crew_size": 12 if hour.hour in range(8, 20) else 8,
            "priority": "high" if hour.hour in range(10, 16) else "normal"
        })

    schedule_df = spark.createDataFrame(schedule)
    schedule_df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.mes_production_schedule")
    print(f"  ✓ Created mes_production_schedule with {schedule_df.count()} records")

    # Work orders
    work_orders = []
    equipment_ids = [f"HAUL-{i:03d}" for i in range(1, 6)] + \
                   [f"CRUSH-{i:03d}" for i in range(1, 4)]

    for i in range(30):
        work_orders.append({
            "work_order_id": f"WO-{i:05d}",
            "equipment_id": random.choice(equipment_ids),
            "order_type": random.choice(["preventive", "corrective", "inspection", "calibration"]),
            "scheduled_date": datetime.now() + timedelta(days=random.randint(1, 30)),
            "estimated_hours": random.uniform(1, 8),
            "priority": random.choice(["low", "medium", "high", "critical"]),
            "status": random.choice(["pending", "in_progress", "completed", "on_hold"]),
            "assigned_technician": f"Tech-{random.randint(1, 10):02d}"
        })

    wo_df = spark.createDataFrame(work_orders)
    wo_df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.mes_work_orders")
    print(f"  ✓ Created mes_work_orders with {wo_df.count()} records")

    # Quality metrics
    quality = []
    for i in range(100):
        timestamp = datetime.now() - timedelta(hours=i)
        quality.append({
            "sample_timestamp": timestamp,
            "batch_id": f"BATCH-{timestamp.strftime('%Y%m%d-%H')}",
            "ore_grade_percent": 65 + random.gauss(0, 2),
            "moisture_content": 8 + random.gauss(0, 1),
            "particle_size_mm": 25 + random.gauss(0, 3),
            "contamination_ppm": random.uniform(10, 50),
            "quality_score": random.uniform(0.85, 0.99),
            "passed_qa": random.random() > 0.05
        })

    quality_df = spark.createDataFrame(quality)
    quality_df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.mes_quality_metrics")
    print(f"  ✓ Created mes_quality_metrics with {quality_df.count()} records")

generate_mes_data()

# ============================================================================
# SAP DATA (Enterprise Resource Planning)
# ============================================================================

print("\n[3/4] Creating SAP Data (Business Context)...")

def generate_sap_data():
    """
    SAP typically provides:
    - Asset registry
    - Maintenance history
    - Spare parts inventory
    - Cost tracking
    - Vendor information
    """

    equipment_ids = [f"HAUL-{i:03d}" for i in range(1, 6)] + \
                   [f"CRUSH-{i:03d}" for i in range(1, 4)] + \
                   [f"CONV-{i:03d}" for i in range(1, 3)]

    # Asset registry with financial data
    assets = []
    for eq_id in equipment_ids:
        eq_type = eq_id.split("-")[0]
        if eq_type == "HAUL":
            purchase_cost = 2500000
            annual_maintenance = 150000
        elif eq_type == "CRUSH":
            purchase_cost = 5000000
            annual_maintenance = 300000
        else:
            purchase_cost = 1000000
            annual_maintenance = 75000

        assets.append({
            "equipment_id": eq_id,
            "asset_number": f"AS{random.randint(100000, 999999)}",
            "purchase_date": datetime.now() - timedelta(days=random.randint(365, 3650)),
            "purchase_cost_usd": purchase_cost,
            "depreciation_years": 10,
            "annual_maintenance_budget": annual_maintenance,
            "warranty_expiry": datetime.now() + timedelta(days=random.randint(-365, 365)),
            "criticality_rating": random.choice(["A", "B", "C"]),  # A=Critical
            "insurance_value": purchase_cost * 0.8
        })

    assets_df = spark.createDataFrame(assets)
    assets_df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.sap_asset_registry")
    print(f"  ✓ Created sap_asset_registry with {assets_df.count()} records")

    # Maintenance history
    maintenance = []
    for i in range(200):
        eq_id = random.choice(equipment_ids)
        maint_date = datetime.now() - timedelta(days=random.randint(1, 365))

        maintenance.append({
            "maintenance_id": f"PM-{i:06d}",
            "equipment_id": eq_id,
            "maintenance_date": maint_date,
            "maintenance_type": random.choice(["scheduled", "breakdown", "predictive"]),
            "cost_usd": random.uniform(1000, 50000),
            "downtime_hours": random.uniform(1, 24),
            "parts_replaced": random.choice(["bearings", "belts", "filters", "hydraulics", "electrical"]),
            "vendor": f"Vendor-{random.randint(1, 5):02d}",
            "next_scheduled": maint_date + timedelta(days=random.randint(30, 180))
        })

    maint_df = spark.createDataFrame(maintenance)
    maint_df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.sap_maintenance_history")
    print(f"  ✓ Created sap_maintenance_history with {maint_df.count()} records")

    # Spare parts inventory
    parts = [
        {"part_number": "BRG-001", "description": "Heavy Duty Bearing", "unit_cost": 2500, "lead_time_days": 14},
        {"part_number": "BLT-002", "description": "Conveyor Belt Section", "unit_cost": 5000, "lead_time_days": 21},
        {"part_number": "FLT-003", "description": "Hydraulic Filter", "unit_cost": 150, "lead_time_days": 7},
        {"part_number": "MOT-004", "description": "Drive Motor", "unit_cost": 15000, "lead_time_days": 45},
        {"part_number": "SEN-005", "description": "Temperature Sensor", "unit_cost": 500, "lead_time_days": 3},
    ]

    inventory = []
    for part in parts:
        for eq_id in equipment_ids:
            if random.random() > 0.5:  # Not all parts for all equipment
                inventory.append({
                    "part_number": part["part_number"],
                    "equipment_id": eq_id,
                    "description": part["description"],
                    "quantity_on_hand": random.randint(0, 10),
                    "quantity_on_order": random.randint(0, 5),
                    "reorder_point": random.randint(2, 5),
                    "unit_cost_usd": part["unit_cost"],
                    "lead_time_days": part["lead_time_days"],
                    "last_order_date": datetime.now() - timedelta(days=random.randint(1, 60))
                })

    inventory_df = spark.createDataFrame(inventory)
    inventory_df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.sap_spare_parts")
    print(f"  ✓ Created sap_spare_parts with {inventory_df.count()} records")

generate_sap_data()

# ============================================================================
# ENRICHMENT VIEWS (Combining all sources)
# ============================================================================

print("\n[4/4] Creating Enriched Views...")

# Create unified equipment context view
unified_view_sql = f"""
CREATE OR REPLACE VIEW {CATALOG}.{SCHEMA}.equipment_360_view AS
SELECT
    -- Real-time from Ignition
    s.equipment_id,
    s.sensor_name,
    s.sensor_value,
    s.event_timestamp,

    -- Historical context from Historian
    h.baseline_temp_7d,
    h.baseline_temp_30d,
    h.baseline_vibration_7d,
    h.anomaly_count as historical_anomalies_today,

    -- Production context from MES
    m.shift as current_shift,
    m.planned_throughput_tph,
    m.product_type,
    m.quality_target,

    -- Business context from SAP
    sap.criticality_rating,
    sap.annual_maintenance_budget,
    sap.warranty_expiry,
    DATEDIFF(sap.warranty_expiry, CURRENT_DATE()) as days_until_warranty_expiry,

    -- Maintenance insights
    mh.last_maintenance_date,
    mh.next_scheduled_maintenance,
    DATEDIFF(mh.next_scheduled_maintenance, CURRENT_DATE()) as days_until_maintenance,

    -- Spare parts availability
    sp.critical_parts_available,
    sp.parts_on_order

FROM {CATALOG}.{SCHEMA}.ot_sensors_normalized s
LEFT JOIN (
    SELECT equipment_id,
           MAX(baseline_temp_7d) as baseline_temp_7d,
           MAX(baseline_temp_30d) as baseline_temp_30d,
           MAX(baseline_vibration_7d) as baseline_vibration_7d,
           MAX(anomaly_count) as anomaly_count
    FROM {CATALOG}.{SCHEMA}.historian_baselines
    WHERE date = CURRENT_DATE()
    GROUP BY equipment_id
) h ON s.equipment_id = h.equipment_id
LEFT JOIN (
    SELECT *
    FROM {CATALOG}.{SCHEMA}.mes_production_schedule
    WHERE schedule_hour BETWEEN CURRENT_TIMESTAMP() AND CURRENT_TIMESTAMP() + INTERVAL 1 HOUR
    LIMIT 1
) m ON 1=1
LEFT JOIN {CATALOG}.{SCHEMA}.sap_asset_registry sap ON s.equipment_id = sap.equipment_id
LEFT JOIN (
    SELECT equipment_id,
           MAX(maintenance_date) as last_maintenance_date,
           MAX(next_scheduled) as next_scheduled_maintenance
    FROM {CATALOG}.{SCHEMA}.sap_maintenance_history
    GROUP BY equipment_id
) mh ON s.equipment_id = mh.equipment_id
LEFT JOIN (
    SELECT equipment_id,
           SUM(quantity_on_hand) as critical_parts_available,
           SUM(quantity_on_order) as parts_on_order
    FROM {CATALOG}.{SCHEMA}.sap_spare_parts
    WHERE reorder_point > 0
    GROUP BY equipment_id
) sp ON s.equipment_id = sp.equipment_id
"""

spark.sql(unified_view_sql)
print(f"  ✓ Created equipment_360_view with full enterprise context")

# Create ML feature table
ml_features_sql = f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.ml_feature_store AS
SELECT
    equipment_id,
    -- Sensor features
    AVG(CASE WHEN sensor_name = 'temperature' THEN sensor_value END) as current_temp,
    AVG(CASE WHEN sensor_name = 'vibration' THEN sensor_value END) as current_vibration,
    AVG(CASE WHEN sensor_name = 'throughput' THEN sensor_value END) as current_throughput,

    -- Deviation from baseline (key for anomaly detection)
    AVG(CASE WHEN sensor_name = 'temperature' THEN sensor_value END) - baseline_temp_7d as temp_deviation_7d,
    AVG(CASE WHEN sensor_name = 'vibration' THEN sensor_value END) - baseline_vibration_7d as vibration_deviation_7d,

    -- Production context
    CASE WHEN current_shift = 'Day' THEN 1 ELSE 0 END as is_day_shift,
    planned_throughput_tph,

    -- Maintenance risk factors
    days_until_maintenance,
    CASE WHEN days_until_maintenance < 7 THEN 1 ELSE 0 END as maintenance_due_soon,
    CASE WHEN days_until_warranty_expiry < 0 THEN 1 ELSE 0 END as out_of_warranty,

    -- Parts availability risk
    CASE WHEN critical_parts_available = 0 THEN 1 ELSE 0 END as no_spare_parts,

    -- Criticality for prioritization
    CASE
        WHEN criticality_rating = 'A' THEN 3
        WHEN criticality_rating = 'B' THEN 2
        ELSE 1
    END as criticality_score

FROM equipment_360_view
GROUP BY
    equipment_id, baseline_temp_7d, baseline_vibration_7d, current_shift,
    planned_throughput_tph, days_until_maintenance, days_until_warranty_expiry,
    critical_parts_available, criticality_rating
"""

spark.sql(ml_features_sql)
print(f"  ✓ Created ml_feature_store for enhanced ML models")

print("\n" + "="*80)
print("ENTERPRISE DATA SOURCES SIMULATED SUCCESSFULLY")
print("="*80)

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
│
└── Enriched Views
    ├── equipment_360_view       - Unified real-time context
    └── ml_feature_store        - ML-ready features

These tables provide the business context that makes ML recommendations
more intelligent and actionable:

1. PREDICTIVE: "Temperature 8°C above 30-day baseline"
2. CONTEXTUAL: "During night shift with reduced crew"
3. ACTIONABLE: "Spare bearing available, maintenance window in 3 days"
4. PRIORITIZED: "Critical equipment with expired warranty"

The AI can now make recommendations like:
"Schedule bearing replacement during next maintenance window (3 days).
Part BRG-001 in stock. Expected downtime: 4 hours.
Risk: Equipment out of warranty, failure would cost $50K."
""")

# Show sample enriched data
print("\nSample Enriched Data:")
spark.sql(f"SELECT * FROM {CATALOG}.{SCHEMA}.equipment_360_view LIMIT 5").show(truncate=False)