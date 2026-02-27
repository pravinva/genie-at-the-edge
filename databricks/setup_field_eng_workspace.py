#!/usr/bin/env python3
"""
Complete Field Engineering Workspace Setup for Genie at the Edge
Creates Lakebase catalog, simulates all data sources, and deploys unified pipeline

Catalogs:
- field_engineering: Main catalog for analytics
- lakebase: PostgreSQL-compatible catalog for Ignition Historian
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime, timedelta
import random

spark = SparkSession.builder \
    .appName("GenieAtEdgeSetup") \
    .config("spark.sql.catalog.lakebase", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

print("="*80)
print("GENIE AT THE EDGE - FIELD ENGINEERING WORKSPACE SETUP")
print("="*80)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

CATALOGS = {
    "main": "field_engineering",
    "lakebase": "lakebase"
}

SCHEMAS = {
    "main": "mining_demo",
    "lakebase_historian": "ignition_historian",
    "lakebase_agentic": "agentic_hmi"
}

print(f"\nUsing Catalogs:")
print(f"  Main: {CATALOGS['main']}")
print(f"  Lakebase: {CATALOGS['lakebase']}")

# ==============================================================================
# STEP 1: CREATE CATALOGS AND SCHEMAS
# ==============================================================================

print("\n[1/6] Creating Catalogs and Schemas...")

def create_catalog_structure():
    """Create all required catalogs and schemas"""

    # Main catalog (should already exist)
    spark.sql(f"""
        CREATE CATALOG IF NOT EXISTS {CATALOGS['main']}
        COMMENT 'Field Engineering main analytics catalog'
    """)

    spark.sql(f"""
        CREATE SCHEMA IF NOT EXISTS {CATALOGS['main']}.{SCHEMAS['main']}
        COMMENT 'Mining demo data and analytics'
    """)

    # Lakebase catalog (PostgreSQL-compatible interface)
    spark.sql(f"""
        CREATE CATALOG IF NOT EXISTS {CATALOGS['lakebase']}
        COMMENT 'Lakebase PostgreSQL-compatible catalog for Ignition integration'
    """)

    spark.sql(f"""
        CREATE SCHEMA IF NOT EXISTS {CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}
        COMMENT 'Ignition Tag Historian data (PostgreSQL interface to Delta)'
    """)

    spark.sql(f"""
        CREATE SCHEMA IF NOT EXISTS {CATALOGS['lakebase']}.{SCHEMAS['lakebase_agentic']}
        COMMENT 'Agentic HMI tables for operator actions'
    """)

    print(f"  ✓ Created catalog: {CATALOGS['main']}")
    print(f"  ✓ Created schema: {CATALOGS['main']}.{SCHEMAS['main']}")
    print(f"  ✓ Created catalog: {CATALOGS['lakebase']}")
    print(f"  ✓ Created schema: {CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}")
    print(f"  ✓ Created schema: {CATALOGS['lakebase']}.{SCHEMAS['lakebase_agentic']}")

create_catalog_structure()

# ==============================================================================
# STEP 2: CREATE LAKEBASE HISTORIAN TABLES (Ignition-compatible schema)
# ==============================================================================

print("\n[2/6] Creating Lakebase Historian Tables...")

def create_lakebase_historian_tables():
    """
    Create Ignition Tag Historian compatible tables in Lakebase
    These tables match Ignition's schema expectations
    """

    # Tag metadata table (sqlth_te)
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}.sqlth_te (
            id INT,
            tagpath STRING,
            datatype INT,
            created TIMESTAMP
        ) USING DELTA
        COMMENT 'Tag metadata - maps tag IDs to paths'
    """)

    # Main historian data table (sqlt_data_1_2024_02)
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}.sqlt_data_1_2024_02 (
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
    """)

    # Partition tracking table
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}.sqlth_partitions (
            pname STRING,
            start_time TIMESTAMP,
            end_time TIMESTAMP
        ) USING DELTA
        COMMENT 'Historian partition tracking'
    """)

    print(f"  ✓ Created sqlth_te (tag metadata)")
    print(f"  ✓ Created sqlt_data_1_2024_02 (historian data)")
    print(f"  ✓ Created sqlth_partitions (partition tracking)")

create_lakebase_historian_tables()

# ==============================================================================
# STEP 3: POPULATE HISTORIAN WITH SIMULATED DATA
# ==============================================================================

print("\n[3/6] Populating Historian with Simulated Data...")

def populate_historian_data():
    """Simulate 30 days of Ignition Historian data"""

    # Equipment list
    equipment = [
        "HAUL-001", "HAUL-002", "HAUL-003", "HAUL-004", "HAUL-005",
        "CRUSH-001", "CRUSH-002", "CRUSH-003",
        "CONV-001", "CONV-002"
    ]

    sensors = ["temperature", "vibration", "pressure", "throughput", "speed"]

    # Create tag metadata
    tag_metadata = []
    tag_id = 1
    for eq in equipment:
        for sensor in sensors:
            tag_metadata.append({
                "id": tag_id,
                "tagpath": f"{eq}/{sensor}",
                "datatype": 4,  # Float
                "created": datetime.now() - timedelta(days=90)
            })
            tag_id += 1

    tag_df = spark.createDataFrame(tag_metadata)
    tag_df.write.mode("overwrite").saveAsTable(
        f"{CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}.sqlth_te"
    )
    print(f"  ✓ Created {len(tag_metadata)} tag definitions")

    # Generate 30 days of historical data
    print("  → Generating 30 days of sensor data...")
    historian_data = []

    base_values = {
        "temperature": 75.0,
        "vibration": 3.0,
        "pressure": 3.5,
        "throughput": 1000.0,
        "speed": 100.0
    }

    # Generate data every 1 minute for 30 days
    start_date = datetime.now() - timedelta(days=30)
    intervals = 30 * 24 * 60  # 30 days * 24 hours * 60 minutes

    for i in range(0, intervals, 60):  # Every hour to keep data manageable
        timestamp = start_date + timedelta(minutes=i)

        for tag in tag_metadata:
            sensor_type = tag["tagpath"].split("/")[1]
            base = base_values[sensor_type]

            # Add realistic patterns
            hour = timestamp.hour
            day_of_week = timestamp.weekday()

            # Daytime variations
            if 8 <= hour < 20:
                multiplier = 1.2  # Higher during work hours
            else:
                multiplier = 0.8

            # Weekend reduction
            if day_of_week >= 5:
                multiplier *= 0.7

            # Random walk with noise
            value = base * multiplier + random.gauss(0, base * 0.1)

            # Inject some anomalies (5% chance)
            if random.random() < 0.05:
                value *= random.uniform(1.3, 1.5)

            historian_data.append({
                "tagid": tag["id"],
                "t_stamp": timestamp,
                "floatvalue": round(value, 2),
                "intvalue": None,
                "stringvalue": None,
                "datevalue": None,
                "dataintegrity": 192  # Good quality
            })

    # Write in batches to avoid memory issues
    batch_size = 50000
    for i in range(0, len(historian_data), batch_size):
        batch = historian_data[i:i+batch_size]
        batch_df = spark.createDataFrame(batch)
        batch_df.write.mode("append").saveAsTable(
            f"{CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}.sqlt_data_1_2024_02"
        )
        print(f"  → Wrote batch {i//batch_size + 1} ({len(batch)} records)")

    print(f"  ✓ Generated {len(historian_data)} historian records")

    # Create partition tracking
    partition_data = [{
        "pname": "sqlt_data_1_2024_02",
        "start_time": start_date,
        "end_time": datetime.now()
    }]

    spark.createDataFrame(partition_data).write.mode("overwrite").saveAsTable(
        f"{CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}.sqlth_partitions"
    )
    print(f"  ✓ Created partition tracking")

populate_historian_data()

# ==============================================================================
# STEP 4: CREATE ZEROBUS STREAMING SIMULATION
# ==============================================================================

print("\n[4/6] Setting up Zerobus Streaming Simulation...")

def create_zerobus_tables():
    """Create tables to simulate Zerobus real-time streaming"""

    # Bronze layer - raw streaming data
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {CATALOGS['main']}.{SCHEMAS['main']}.zerobus_sensor_stream (
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
    """)

    # Simulate current streaming data (last hour)
    stream_data = []
    base_time = datetime.now() - timedelta(hours=1)

    equipment = ["HAUL-001", "HAUL-002", "CRUSH-001", "CRUSH-002", "CONV-001"]
    sensors = [
        ("temperature", "°C", 75.0),
        ("vibration", "mm/s", 3.0),
        ("throughput", "TPH", 1000.0)
    ]

    # Generate data every 10 seconds for last hour
    for minutes in range(60):
        for seconds in range(0, 60, 10):
            ts = base_time + timedelta(minutes=minutes, seconds=seconds)

            for eq in equipment:
                for sensor_name, unit, base_val in sensors:
                    value = base_val * random.uniform(0.95, 1.05)

                    # Inject current anomaly (2% chance)
                    if random.random() < 0.02:
                        value *= 1.4

                    stream_data.append({
                        "equipment_id": eq,
                        "sensor_name": sensor_name,
                        "sensor_value": round(value, 2),
                        "units": unit,
                        "timestamp": ts,
                        "quality": 192,
                        "_ingestion_timestamp": ts + timedelta(milliseconds=random.randint(10, 100))
                    })

    stream_df = spark.createDataFrame(stream_data)
    stream_df.write.mode("overwrite").saveAsTable(
        f"{CATALOGS['main']}.{SCHEMAS['main']}.zerobus_sensor_stream"
    )

    print(f"  ✓ Created zerobus_sensor_stream with {len(stream_data)} records")

create_zerobus_tables()

# ==============================================================================
# STEP 5: CREATE SAP/MES SIMULATION DATA
# ==============================================================================

print("\n[5/6] Creating SAP/MES Simulation Data...")

def create_sap_mes_tables():
    """Create SAP and MES business context tables"""

    equipment = ["HAUL-001", "HAUL-002", "HAUL-003", "HAUL-004", "HAUL-005",
                 "CRUSH-001", "CRUSH-002", "CRUSH-003", "CONV-001", "CONV-002"]

    # SAP Equipment Master
    sap_equipment = []
    for eq in equipment:
        eq_type = eq.split("-")[0]
        criticality = "A" if "CRUSH" in eq else "B" if "HAUL" in eq else "C"

        sap_equipment.append({
            "equipment_id": eq,
            "asset_number": f"AS{random.randint(100000, 999999)}",
            "criticality_rating": criticality,
            "annual_maintenance_budget": random.randint(50000, 300000),
            "purchase_cost": random.randint(1000000, 5000000),
            "warranty_expiry": datetime.now() + timedelta(days=random.randint(-180, 365)),
            "installation_date": datetime.now() - timedelta(days=random.randint(365, 3650))
        })

    spark.createDataFrame(sap_equipment).write.mode("overwrite").saveAsTable(
        f"{CATALOGS['main']}.{SCHEMAS['main']}.sap_equipment_master"
    )
    print(f"  ✓ Created sap_equipment_master")

    # SAP Maintenance Schedule
    maintenance = []
    for eq in equipment:
        maintenance.append({
            "equipment_id": eq,
            "last_maintenance_date": datetime.now() - timedelta(days=random.randint(1, 90)),
            "next_scheduled_maintenance": datetime.now() + timedelta(days=random.randint(7, 60)),
            "maintenance_type": random.choice(["preventive", "predictive", "breakdown"]),
            "estimated_hours": random.uniform(2, 8)
        })

    spark.createDataFrame(maintenance).write.mode("overwrite").saveAsTable(
        f"{CATALOGS['main']}.{SCHEMAS['main']}.sap_maintenance_schedule"
    )
    print(f"  ✓ Created sap_maintenance_schedule")

    # SAP Spare Parts Inventory
    parts = [
        ("BRG-001", "Heavy Duty Bearing", 2500),
        ("BLT-002", "Conveyor Belt Section", 5000),
        ("FLT-003", "Hydraulic Filter", 150),
        ("MOT-004", "Drive Motor", 15000),
        ("SEN-005", "Temperature Sensor", 500)
    ]

    inventory = []
    for eq in equipment:
        for part_num, desc, cost in parts:
            if random.random() > 0.3:  # Not all parts for all equipment
                inventory.append({
                    "equipment_id": eq,
                    "part_number": part_num,
                    "description": desc,
                    "quantity_on_hand": random.randint(0, 5),
                    "quantity_on_order": random.randint(0, 2),
                    "unit_cost": cost,
                    "lead_time_days": random.randint(3, 45)
                })

    spark.createDataFrame(inventory).write.mode("overwrite").saveAsTable(
        f"{CATALOGS['main']}.{SCHEMAS['main']}.sap_spare_parts"
    )
    print(f"  ✓ Created sap_spare_parts")

    # MES Production Schedule
    schedule = []
    for hour in range(24):
        shift = "Day" if 6 <= hour < 14 else "Night" if 14 <= hour < 22 else "Graveyard"
        schedule.append({
            "schedule_hour": datetime.now().replace(hour=hour, minute=0, second=0),
            "shift": shift,
            "planned_throughput_tph": 1200 if shift == "Day" else 800,
            "product_type": random.choice(["Iron Ore", "Copper Ore"]),
            "quality_target": 0.95,
            "crew_size": 12 if shift == "Day" else 8
        })

    spark.createDataFrame(schedule).write.mode("overwrite").saveAsTable(
        f"{CATALOGS['main']}.{SCHEMAS['main']}.mes_production_schedule"
    )
    print(f"  ✓ Created mes_production_schedule")

create_sap_mes_tables()

# ==============================================================================
# STEP 6: CREATE AGENTIC HMI TABLES IN LAKEBASE
# ==============================================================================

print("\n[6/6] Creating Agentic HMI Tables in Lakebase...")

def create_agentic_hmi_tables():
    """Create tables for ML recommendations and operator actions"""

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {CATALOGS['lakebase']}.{SCHEMAS['lakebase_agentic']}.agent_recommendations (
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
    """)

    print(f"  ✓ Created agent_recommendations table in Lakebase")

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {CATALOGS['lakebase']}.{SCHEMAS['lakebase_agentic']}.agent_commands (
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
    """)

    print(f"  ✓ Created agent_commands table in Lakebase")

create_agentic_hmi_tables()

# ==============================================================================
# VALIDATION AND SUMMARY
# ==============================================================================

print("\n" + "="*80)
print("SETUP COMPLETE - VALIDATION")
print("="*80)

def validate_setup():
    """Validate all tables were created and populated"""

    tables_to_check = [
        (f"{CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}.sqlth_te", "Tag Metadata"),
        (f"{CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}.sqlt_data_1_2024_02", "Historian Data"),
        (f"{CATALOGS['main']}.{SCHEMAS['main']}.zerobus_sensor_stream", "Zerobus Stream"),
        (f"{CATALOGS['main']}.{SCHEMAS['main']}.sap_equipment_master", "SAP Equipment"),
        (f"{CATALOGS['main']}.{SCHEMAS['main']}.sap_maintenance_schedule", "SAP Maintenance"),
        (f"{CATALOGS['main']}.{SCHEMAS['main']}.sap_spare_parts", "SAP Parts"),
        (f"{CATALOGS['main']}.{SCHEMAS['main']}.mes_production_schedule", "MES Schedule"),
        (f"{CATALOGS['lakebase']}.{SCHEMAS['lakebase_agentic']}.agent_recommendations", "Agent Recommendations")
    ]

    print("\nTable Validation:")
    for table, name in tables_to_check:
        try:
            count = spark.table(table).count()
            print(f"  ✓ {name:30s} {count:>10,} records")
        except Exception as e:
            print(f"  ✗ {name:30s} ERROR: {str(e)[:50]}")

    # Show sample unified query
    print("\n" + "-"*80)
    print("SAMPLE UNIFIED QUERY (All Three Sources):")
    print("-"*80)

    sample_query = f"""
        SELECT
            z.equipment_id,
            z.sensor_name,
            z.sensor_value as current_value,
            h.baseline_7d,
            z.sensor_value - h.baseline_7d as deviation,
            s.criticality_rating,
            m.next_scheduled_maintenance,
            p.spare_parts_count
        FROM {CATALOGS['main']}.{SCHEMAS['main']}.zerobus_sensor_stream z
        LEFT JOIN (
            SELECT
                SPLIT(t.tagpath, '/')[0] as equipment_id,
                SPLIT(t.tagpath, '/')[1] as sensor_name,
                AVG(d.floatvalue) as baseline_7d
            FROM {CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}.sqlt_data_1_2024_02 d
            JOIN {CATALOGS['lakebase']}.{SCHEMAS['lakebase_historian']}.sqlth_te t
                ON d.tagid = t.id
            WHERE d.t_stamp > CURRENT_TIMESTAMP - INTERVAL 7 DAYS
            GROUP BY SPLIT(t.tagpath, '/')[0], SPLIT(t.tagpath, '/')[1]
        ) h ON z.equipment_id = h.equipment_id AND z.sensor_name = h.sensor_name
        LEFT JOIN {CATALOGS['main']}.{SCHEMAS['main']}.sap_equipment_master s
            ON z.equipment_id = s.equipment_id
        LEFT JOIN {CATALOGS['main']}.{SCHEMAS['main']}.sap_maintenance_schedule m
            ON z.equipment_id = m.equipment_id
        LEFT JOIN (
            SELECT equipment_id, SUM(quantity_on_hand) as spare_parts_count
            FROM {CATALOGS['main']}.{SCHEMAS['main']}.sap_spare_parts
            GROUP BY equipment_id
        ) p ON z.equipment_id = p.equipment_id
        WHERE z.timestamp > CURRENT_TIMESTAMP - INTERVAL 10 MINUTES
        LIMIT 5
    """

    result = spark.sql(sample_query)
    result.show(5, truncate=False)

    print("\n" + "="*80)
    print("SETUP SUMMARY")
    print("="*80)
    print(f"""
Catalogs Created:
  • {CATALOGS['main']} (Main analytics)
  • {CATALOGS['lakebase']} (PostgreSQL-compatible for Ignition)

Data Sources Ready:
  ✓ Lakebase Historian (30 days of data)
  ✓ Zerobus Streaming (1 hour real-time)
  ✓ SAP/MES Context (equipment, maintenance, parts)

Next Steps:
  1. Configure Ignition to write to Lakebase:
     jdbc:postgresql://lakebase:5432/{SCHEMAS['lakebase_historian']}

  2. Deploy unified DLT pipeline:
     databricks/unified_data_architecture.py

  3. Query all three sources together:
     See sample query above

  4. Set up PostgreSQL NOTIFY triggers:
     databricks/lakebase_notify_trigger.sql

Connection String for Ignition:
  URL: jdbc:postgresql://lakebase.databricks.com:5432/{SCHEMAS['lakebase_historian']}
  Database: {SCHEMAS['lakebase_historian']}
  Schema: public
  User: (your Databricks token)
""")

validate_setup()

print("\n✅ Field Engineering workspace setup complete!")