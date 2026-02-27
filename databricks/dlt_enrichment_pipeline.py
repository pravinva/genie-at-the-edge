"""
Delta Live Tables Pipeline: Real-time Sensor Enrichment
Bronze → Silver → Gold layers with enterprise context fusion

Architecture:
- Bronze: Raw Zerobus sensor events (field_engineering.ignition_streaming.sensor_events)
- Silver: Enriched with Historian baselines, MES schedules, SAP asset data
- Gold: ML-ready features with time-window aggregations

Deploy with:
databricks pipelines create --config dlt_pipeline_config.json
"""

import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

CATALOG = "field_engineering"
SCHEMA_BRONZE = "ignition_streaming"
SCHEMA_ENTERPRISE = "mining_demo"
SCHEMA_SILVER = "ml_silver"
SCHEMA_GOLD = "ml_gold"

# ============================================================================
# BRONZE LAYER: Streaming Sensor Events (already exists from Zerobus)
# ============================================================================

@dlt.table(
    name="bronze_sensor_events",
    comment="Raw sensor events from Zerobus (streaming source)",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "tag_path,event_time"
    }
)
def bronze_sensor_events():
    """
    Read streaming sensor data from Zerobus target table
    Extracts equipment_id from tag_path (e.g., 'Sim/HAUL-001/Temperature')
    """
    return (
        spark.readStream
        .table(f"{CATALOG}.{SCHEMA_BRONZE}.sensor_events")
        .withColumn("equipment_id",
            F.regexp_extract(F.col("tag_path"), r"Sim/([A-Z]+-\d+)/", 1))
        .withColumn("metric_name",
            F.regexp_extract(F.col("tag_path"), r"Sim/[A-Z]+-\d+/(.+)", 1))
        .filter(F.col("equipment_id") != "")  # Filter out non-equipment tags
    )

# ============================================================================
# SILVER LAYER: Enterprise-Enriched Sensor Events
# ============================================================================

@dlt.table(
    name="silver_enriched_sensors",
    comment="Real-time sensors enriched with historian baselines, MES schedules, SAP assets",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "equipment_id,event_time"
    }
)
def silver_enriched_sensors():
    """
    Enrich sensor events with enterprise context:
    - Historian baselines (what's normal for this equipment)
    - MES production schedule (current shift, throughput targets)
    - SAP asset registry (purchase date, warranty, cost)
    - Recent maintenance history
    """
    sensors = dlt.read_stream("bronze_sensor_events")

    # Load enterprise context tables (batch)
    historian_baselines = spark.table(f"{CATALOG}.{SCHEMA_ENTERPRISE}.historian_baselines")
    mes_schedule = spark.table(f"{CATALOG}.{SCHEMA_ENTERPRISE}.mes_production_schedule")
    sap_assets = spark.table(f"{CATALOG}.{SCHEMA_ENTERPRISE}.sap_asset_registry")
    sap_maintenance = spark.table(f"{CATALOG}.{SCHEMA_ENTERPRISE}.sap_maintenance_history")

    # Get latest baseline for each equipment (last 7 days)
    latest_baselines = (
        historian_baselines
        .filter(F.col("date") >= F.date_sub(F.current_date(), 7))
        .groupBy("equipment_id")
        .agg(
            F.avg("baseline_temp_7d").alias("baseline_temp_7d"),
            F.avg("baseline_vibration_7d").alias("baseline_vibration_7d"),
            F.avg("avg_throughput").alias("baseline_throughput"),
            F.max("anomaly_count").alias("recent_anomaly_count")
        )
    )

    # Get current shift schedule (nearest hour)
    current_schedule = (
        mes_schedule
        .withColumn("hour_diff",
            F.abs(F.unix_timestamp("schedule_hour") - F.unix_timestamp(F.current_timestamp())) / 3600)
        .withColumn("rank", F.row_number().over(Window.partitionBy().orderBy("hour_diff")))
        .filter(F.col("rank") == 1)
        .select("shift", "planned_throughput_tph", "product_type", "crew_size", "priority")
    )

    # Get last maintenance for each equipment
    last_maintenance = (
        sap_maintenance
        .withColumn("rank",
            F.row_number().over(Window.partitionBy("equipment_id").orderBy(F.desc("maintenance_date"))))
        .filter(F.col("rank") == 1)
        .select(
            F.col("equipment_id").alias("maint_equipment_id"),
            F.col("maintenance_date").alias("last_maintenance_date"),
            F.col("maintenance_type").alias("last_maintenance_type"),
            F.col("cost_usd").alias("last_maintenance_cost"),
            F.col("parts_replaced").alias("last_parts_replaced"),
            F.col("next_scheduled").alias("next_maintenance_scheduled")
        )
    )

    # Perform enrichment joins
    enriched = (
        sensors
        # Join historian baselines
        .join(latest_baselines, on="equipment_id", how="left")
        # Cross join current schedule (broadcast)
        .crossJoin(F.broadcast(current_schedule))
        # Join SAP asset data
        .join(sap_assets, on="equipment_id", how="left")
        # Join last maintenance
        .join(last_maintenance,
            sensors["equipment_id"] == last_maintenance["maint_equipment_id"],
            how="left")
        .drop("maint_equipment_id")
        # Calculate deviation from baseline
        .withColumn("temp_deviation",
            F.when(F.col("metric_name") == "Temperature",
                F.col("numeric_value") - F.col("baseline_temp_7d")).otherwise(None))
        .withColumn("vibration_deviation",
            F.when(F.col("metric_name") == "Vibration",
                F.col("numeric_value") - F.col("baseline_vibration_7d")).otherwise(None))
        # Calculate days since last maintenance
        .withColumn("days_since_maintenance",
            F.datediff(F.current_date(), F.col("last_maintenance_date")))
        # Calculate days until next maintenance
        .withColumn("days_until_maintenance",
            F.datediff(F.col("next_maintenance_scheduled"), F.current_date()))
    )

    return enriched

# ============================================================================
# GOLD LAYER: ML Feature Store (Time-Window Aggregations)
# ============================================================================

@dlt.table(
    name="gold_ml_features",
    comment="ML-ready features with 5-min, 15-min, 1-hour aggregations per equipment",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.zOrderCols": "equipment_id,window_end"
    }
)
def gold_ml_features():
    """
    Time-windowed aggregations for ML model features
    Creates 5-min, 15-min, and 1-hour rolling windows per equipment
    """
    silver = dlt.read_stream("silver_enriched_sensors")

    # Pivot sensor metrics to columns for easier feature engineering
    pivoted = (
        silver
        .groupBy(
            F.col("equipment_id"),
            F.col("event_time"),
            F.window(F.col("event_time"), "5 minutes").alias("window_5min"),
            # Include context columns
            F.col("shift"),
            F.col("planned_throughput_tph"),
            F.col("product_type"),
            F.col("asset_category"),
            F.col("purchase_date"),
            F.col("days_since_maintenance"),
            F.col("days_until_maintenance"),
            F.col("last_maintenance_type"),
            F.col("recent_anomaly_count")
        )
        .pivot("metric_name", ["Temperature", "Vibration", "Throughput", "Pressure"])
        .agg(
            F.avg("numeric_value").alias("avg"),
            F.max("numeric_value").alias("max"),
            F.min("numeric_value").alias("min"),
            F.stddev("numeric_value").alias("stddev"),
            F.avg("temp_deviation").alias("temp_deviation"),
            F.avg("vibration_deviation").alias("vibration_deviation")
        )
    )

    # Calculate multi-sensor correlation features
    features = (
        pivoted
        .select(
            F.col("equipment_id"),
            F.col("window_5min.end").alias("window_end"),
            F.col("shift"),
            F.col("planned_throughput_tph"),
            F.col("product_type"),

            # Temperature features
            F.col("Temperature_avg").alias("temp_avg_5min"),
            F.col("Temperature_max").alias("temp_max_5min"),
            F.col("Temperature_stddev").alias("temp_std_5min"),
            F.col("Temperature_temp_deviation").alias("temp_deviation_from_baseline"),

            # Vibration features
            F.col("Vibration_avg").alias("vibration_avg_5min"),
            F.col("Vibration_max").alias("vibration_max_5min"),
            F.col("Vibration_stddev").alias("vibration_std_5min"),
            F.col("Vibration_vibration_deviation").alias("vibration_deviation_from_baseline"),

            # Throughput features
            F.col("Throughput_avg").alias("throughput_avg_5min"),
            F.col("Throughput_min").alias("throughput_min_5min"),

            # Pressure features
            F.col("Pressure_avg").alias("pressure_avg_5min"),
            F.col("Pressure_max").alias("pressure_max_5min"),

            # Multi-sensor correlation
            (F.col("Temperature_avg") * F.col("Vibration_avg")).alias("temp_vibration_interaction"),
            (F.col("Temperature_stddev") + F.col("Vibration_stddev")).alias("total_variability"),

            # Enterprise context
            F.col("asset_category"),
            F.col("days_since_maintenance"),
            F.col("days_until_maintenance"),
            F.col("last_maintenance_type"),
            F.col("recent_anomaly_count"),
            F.datediff(F.current_date(), F.col("purchase_date")).alias("equipment_age_days")
        )
        # Add 15-min and 1-hour rolling aggregations
        .withColumn("temp_avg_15min",
            F.avg("temp_avg_5min").over(
                Window.partitionBy("equipment_id")
                .orderBy(F.col("window_end").cast("long"))
                .rangeBetween(-15*60, 0)))
        .withColumn("vibration_avg_15min",
            F.avg("vibration_avg_5min").over(
                Window.partitionBy("equipment_id")
                .orderBy(F.col("window_end").cast("long"))
                .rangeBetween(-15*60, 0)))
        .withColumn("temp_avg_1hour",
            F.avg("temp_avg_5min").over(
                Window.partitionBy("equipment_id")
                .orderBy(F.col("window_end").cast("long"))
                .rangeBetween(-60*60, 0)))
        .withColumn("vibration_avg_1hour",
            F.avg("vibration_avg_5min").over(
                Window.partitionBy("equipment_id")
                .orderBy(F.col("window_end").cast("long"))
                .rangeBetween(-60*60, 0)))
    )

    return features

# ============================================================================
# GOLD LAYER: Equipment 360 View (Latest State)
# ============================================================================

@dlt.view(
    name="gold_equipment_360",
    comment="Latest enriched state per equipment (for dashboards and Genie queries)"
)
def gold_equipment_360():
    """
    Latest sensor values + enterprise context for each equipment
    Used by Ignition Perspective HMI and Genie chat interface
    """
    silver = dlt.read("silver_enriched_sensors")

    # Get latest value for each metric per equipment
    latest_values = (
        silver
        .withColumn("rank",
            F.row_number().over(
                Window.partitionBy("equipment_id", "metric_name")
                .orderBy(F.desc("event_time"))))
        .filter(F.col("rank") == 1)
    )

    # Pivot to wide format
    wide_format = (
        latest_values
        .groupBy(
            "equipment_id",
            "asset_category",
            "manufacturer",
            "model",
            "purchase_date",
            "warranty_expiry",
            "replacement_cost_usd",
            "shift",
            "planned_throughput_tph",
            "product_type",
            "crew_size",
            "priority",
            "last_maintenance_date",
            "last_maintenance_type",
            "last_parts_replaced",
            "next_maintenance_scheduled",
            "days_since_maintenance",
            "days_until_maintenance",
            "recent_anomaly_count"
        )
        .pivot("metric_name")
        .agg(F.first("numeric_value"))
        .withColumn("last_updated", F.current_timestamp())
    )

    return wide_format
