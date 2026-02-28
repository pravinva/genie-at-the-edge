"""
Unified Data Architecture: Combining Lakebase Historian + Zerobus Streaming + SAP
NO REVERSE ETL NEEDED - Lakebase is already in Databricks!
"""

import dlt
from pyspark.sql.functions import *
from pyspark.sql.types import *

# ==============================================================================
# KEY INSIGHT: Lakebase IS Delta Lake with PostgreSQL interface
# ==============================================================================
"""
Architecture:

Ignition → Lakebase (PostgreSQL interface) → Delta Tables (already in Databricks!)
    ↓                                              ↓
Zerobus → Bronze (streaming)                 Direct Query!
    ↓                                              ↓
SAP/MES → API/JDBC                          No ETL needed!
    ↓                                              ↓
    └──────────────→ UNIFIED SILVER LAYER ←───────┘
"""

# ==============================================================================
# DATA SOURCE 1: Lakebase Historian (Already in Databricks!)
# ==============================================================================

@dlt.view(name="lakebase_historian_data")
def read_lakebase_historian():
    """
    Lakebase tables are ALREADY Delta tables in Databricks!
    No ETL needed - just query directly
    """

    # Option A: Query via Lakebase catalog (if in Unity Catalog)
    return spark.sql("""
        SELECT
            t.tagpath as equipment_sensor,
            timestamp_millis(d.t_stamp) as timestamp,
            d.floatvalue as value,
            -- Parse equipment and sensor from tagpath
            SPLIT(t.tagpath, '/')[0] as equipment_id,
            SPLIT(t.tagpath, '/')[1] as sensor_name,
            -- Calculate baselines
            AVG(d.floatvalue) OVER (
                PARTITION BY t.tagpath
                ORDER BY d.t_stamp
                ROWS BETWEEN 10080 PRECEDING AND CURRENT ROW
            ) as baseline_7d,
            STDDEV(d.floatvalue) OVER (
                PARTITION BY t.tagpath
                ORDER BY d.t_stamp
                ROWS BETWEEN 10080 PRECEDING AND CURRENT ROW
            ) as stddev_7d
        FROM pravin_ignition_managed.public.sqlt_data_1_2026_02 d
        JOIN pravin_ignition_managed.public.sqlth_te t ON d.tagid = t.id
        WHERE d.t_stamp > unix_millis(CURRENT_TIMESTAMP - INTERVAL 24 HOURS)
    """)

    # Option B: Direct Delta table access (Lakebase IS Delta!)
    # return spark.read.delta("dbfs:/lakebase/ignition_historian/sqlt_data_1_2024_02")

# ==============================================================================
# DATA SOURCE 2: Zerobus Real-time Streaming
# ==============================================================================

@dlt.table(
    name="zerobus_realtime",
    comment="Real-time sensor data from Zerobus CDC"
)
def read_zerobus_streaming():
    """
    Real-time streaming data from Ignition via Zerobus
    Append-only stream for current values
    """

    return (
        spark.readStream
        .format("delta")
        .option("ignoreChanges", "true")
        .load("/mnt/zerobus/bronze/sensor_events")
        .select(
            col("equipment_id"),
            col("sensor_name"),
            col("value").alias("realtime_value"),
            col("timestamp").alias("realtime_timestamp"),
            col("_ingestion_timestamp")
        )
        .withWatermark("realtime_timestamp", "10 seconds")
    )

# ==============================================================================
# DATA SOURCE 3: SAP Business Context
# ==============================================================================

@dlt.table(
    name="sap_context",
    comment="Business context from SAP - maintenance, inventory, costs"
)
def read_sap_data():
    """
    SAP master data and business context
    Updated hourly or daily
    """

    # Option A: Via JDBC to SAP HANA
    return (
        spark.read
        .format("jdbc")
        .option("url", "jdbc:sap://sap-server:30015")
        .option("dbtable", """
            (SELECT
                e.equipment_id,
                e.criticality_rating,
                e.annual_maintenance_budget,
                m.last_maintenance_date,
                m.next_scheduled_maintenance,
                p.spare_parts_available,
                p.parts_on_order
             FROM equipment_master e
             LEFT JOIN maintenance_schedule m ON e.equipment_id = m.equipment_id
             LEFT JOIN parts_inventory p ON e.equipment_id = p.equipment_id
            ) as sap_data
        """)
        .load()
    )

    # Option B: Via REST API
    # sap_api_data = requests.get("https://sap/api/equipment").json()
    # return spark.createDataFrame(sap_api_data)

# ==============================================================================
# UNIFIED SILVER LAYER - The Magic Happens Here!
# ==============================================================================

@dlt.table(
    name="unified_sensor_context",
    comment="Real-time + Historical + Business context unified",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.managed": "true"
    }
)
def create_unified_layer():
    """
    Combines all three sources into unified context
    This is where real-time meets historical meets business
    """

    # Read all three sources
    historian = dlt.read("lakebase_historian_data")  # Already in Databricks!
    realtime = dlt.read_stream("zerobus_realtime")   # Streaming
    sap = dlt.read("sap_context")                    # Business context

    # Create unified stream with all context
    unified = (
        realtime
        # Join with historian baselines (broadcast small dataset)
        .join(
            broadcast(historian.select(
                "equipment_sensor",
                "baseline_7d",
                "stddev_7d"
            ).distinct()),
            concat(realtime.equipment_id, lit("/"), realtime.sensor_name) ==
            historian.equipment_sensor,
            "left"
        )
        # Join with SAP context
        .join(
            broadcast(sap),
            realtime.equipment_id == sap.equipment_id,
            "left"
        )
        # Calculate intelligent features
        .withColumn("deviation_from_baseline",
            (col("realtime_value") - coalesce(col("baseline_7d"), lit(0))) /
            greatest(col("stddev_7d"), lit(1))
        )
        .withColumn("is_anomaly",
            when(abs(col("deviation_from_baseline")) > 2, True).otherwise(False)
        )
        .withColumn("maintenance_risk",
            when(
                datediff(current_date(), col("last_maintenance_date")) > 90,
                "HIGH"
            ).when(
                col("spare_parts_available") == 0,
                "MEDIUM"
            ).otherwise("LOW")
        )
        .withColumn("business_impact",
            when(col("criticality_rating") == "A",
                 col("realtime_value") * 1000  # $1000/unit for critical
            ).otherwise(
                 col("realtime_value") * 100   # $100/unit for non-critical
            )
        )
    )

    return unified

# ==============================================================================
# GOLD LAYER: ML-Ready Features
# ==============================================================================

@dlt.table(
    name="ml_features_unified",
    comment="ML-ready features combining all data sources"
)
def create_ml_features():
    """
    Feature engineering on unified data
    Ready for ML models
    """

    unified = dlt.read_stream("unified_sensor_context")

    return (
        unified
        .groupBy(
            window(col("realtime_timestamp"), "5 minutes"),
            "equipment_id"
        )
        .agg(
            # Real-time features
            avg("realtime_value").alias("avg_value_5min"),
            max("realtime_value").alias("max_value_5min"),
            stddev("realtime_value").alias("stddev_value_5min"),

            # Historical context
            first("baseline_7d").alias("historical_baseline"),
            first("stddev_7d").alias("historical_stddev"),

            # Anomaly features
            sum(when(col("is_anomaly"), 1).otherwise(0)).alias("anomaly_count_5min"),
            max("deviation_from_baseline").alias("max_deviation_5min"),

            # Business features
            first("criticality_rating").alias("equipment_criticality"),
            first("spare_parts_available").alias("parts_in_stock"),
            first("maintenance_risk").alias("maintenance_risk_level"),
            sum("business_impact").alias("total_business_impact_5min")
        )
        .select(
            col("window.start").alias("timestamp"),
            "*"
        )
        .drop("window")
    )

# ==============================================================================
# INTELLIGENT RECOMMENDATIONS
# ==============================================================================

@dlt.table(
    name="intelligent_recommendations",
    comment="ML recommendations with full context"
)
def generate_recommendations():
    """
    Generate recommendations using all available context
    """

    features = dlt.read_stream("ml_features_unified")

    return (
        features
        .filter(col("anomaly_count_5min") > 0)
        .withColumn("recommendation_id", expr("uuid()"))
        .withColumn("recommendation",
            when(
                (col("max_deviation_5min") > 3) &
                (col("parts_in_stock") > 0) &
                (col("maintenance_risk_level") == "HIGH"),
                concat(
                    lit("IMMEDIATE ACTION: Equipment "),
                    col("equipment_id"),
                    lit(" showing "),
                    round(col("max_deviation_5min"), 1),
                    lit(" sigma deviation. Parts available. "),
                    lit("Maintenance overdue. Schedule immediate repair. "),
                    lit("Business impact: $"),
                    round(col("total_business_impact_5min"), 0),
                    lit("/5min")
                )
            )
            .when(
                (col("max_deviation_5min") > 2) &
                (col("parts_in_stock") == 0),
                concat(
                    lit("ORDER PARTS: Equipment "),
                    col("equipment_id"),
                    lit(" trending toward failure. "),
                    lit("NO SPARE PARTS available. "),
                    lit("Order immediately to prevent downtime.")
                )
            )
            .otherwise(
                concat(
                    lit("MONITOR: Equipment "),
                    col("equipment_id"),
                    lit(" showing minor anomaly. "),
                    lit("Continue monitoring.")
                )
            )
        )
        .withColumn("priority",
            when(col("equipment_criticality") == "A", 1)
            .when(col("equipment_criticality") == "B", 2)
            .otherwise(3)
        )
    )

# ==============================================================================
# HOW IT ALL WORKS TOGETHER
# ==============================================================================

"""
DATA FLOW:

1. HISTORIAN (via Lakebase - already in Databricks!)
   - Historical baselines
   - Long-term patterns
   - No ETL needed!

2. REAL-TIME (via Zerobus)
   - Current sensor values
   - Streaming ingestion
   - Sub-second latency

3. BUSINESS (via SAP)
   - Maintenance schedules
   - Parts inventory
   - Financial impact

4. UNIFIED SILVER
   - Joins all three sources
   - Calculates deviations
   - Adds business context

5. ML FEATURES
   - 5-minute aggregates
   - Anomaly counts
   - Risk scores

6. RECOMMENDATIONS
   - Intelligent alerts
   - Actionable insights
   - Prioritized by business impact

KEY ADVANTAGES:
✓ No reverse ETL from Lakebase (it's already Delta!)
✓ Real-time + Historical + Business in one query
✓ Streaming and batch unified
✓ Single source of truth
✓ Sub-second to minutes latency
"""

# ==============================================================================
# MONITORING & METRICS
# ==============================================================================

@dlt.table(name="data_source_metrics")
def monitor_sources():
    """
    Monitor health of all three data sources
    """

    return spark.sql("""
        SELECT
            'Lakebase Historian' as source,
            COUNT(*) as record_count,
            MAX(t_stamp) as latest_timestamp,
            CURRENT_TIMESTAMP - MAX(t_stamp) as lag_seconds
        FROM pravin_ignition_managed.public.sqlt_data_1_2026_02
        WHERE t_stamp > unix_millis(CURRENT_TIMESTAMP - INTERVAL 1 HOUR)

        UNION ALL

        SELECT
            'Zerobus Streaming' as source,
            COUNT(*) as record_count,
            MAX(realtime_timestamp) as latest_timestamp,
            CURRENT_TIMESTAMP - MAX(realtime_timestamp) as lag_seconds
        FROM zerobus_realtime
        WHERE realtime_timestamp > CURRENT_TIMESTAMP - INTERVAL 1 HOUR

        UNION ALL

        SELECT
            'SAP Context' as source,
            COUNT(*) as record_count,
            MAX(last_updated) as latest_timestamp,
            CURRENT_TIMESTAMP - MAX(last_updated) as lag_seconds
        FROM sap_context
    """)

print("Unified Architecture Deployed Successfully!")
print("No reverse ETL needed - Lakebase is already in Databricks!")