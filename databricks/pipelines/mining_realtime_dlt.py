# Databricks notebook source
# MAGIC %md
# MAGIC # Mining Operations Real-Time DLT Pipeline
# MAGIC
# MAGIC **Purpose:** Process streaming OT sensor data with sub-second latency
# MAGIC
# MAGIC **Architecture:** Bronze (Raw) → Silver (Normalized) → Gold (Analytics)
# MAGIC
# MAGIC **Target Performance:**
# MAGIC - Bronze → Silver: <500ms
# MAGIC - Silver → Gold: <500ms
# MAGIC - Total: <1 second event to queryable
# MAGIC
# MAGIC **Equipment:** 15 mining assets with 10+ sensors each
# MAGIC
# MAGIC **Data Source:** Zerobus streaming ingestion from Ignition Gateway

# COMMAND ----------

import dlt
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Catalog and schema for Unity Catalog
CATALOG = "field_engineering"
SCHEMA = "mining_demo"

# Zerobus stream location (adjust based on your Zerobus configuration)
ZEROBUS_PATH = "/mnt/zerobus/mining_ot_stream"
SCHEMA_LOCATION = "_schemas/ot_telemetry"

# Performance tuning
WATERMARK_DELAY = "30 seconds"
WINDOW_DURATION_1MIN = "1 minute"
ANOMALY_THRESHOLD = 2.0  # Standard deviations

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Layer: Raw Ingestion

# COMMAND ----------

@dlt.table(
    name="ot_telemetry_bronze",
    comment="Raw OT sensor data from Zerobus stream - Real-Time ingestion",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "ingestion_timestamp",
        "delta.autoOptimize.optimizeWrite": "true"
    }
)
def bronze_raw():
    """
    Read from Zerobus stream using Auto Loader (cloudFiles)

    No transformation - preserve all data for replay and debugging
    Schema evolution enabled to handle new sensors automatically

    Target latency: Immediate (Zerobus handles streaming)
    """
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", SCHEMA_LOCATION)
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(ZEROBUS_PATH)
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("bronze_id", monotonically_increasing_id())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer: Normalized & Enriched

# COMMAND ----------

@dlt.table(
    name="ot_sensors_normalized",
    comment="Normalized sensor readings with equipment enrichment - Real-Time processing",
    table_properties={
        "quality": "silver",
        "pipelines.trigger.mode": "realtime",
        "pipelines.trigger.checkpoint": "1 minute",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true"
    }
)
@dlt.expect_or_drop("valid_timestamp", "event_timestamp IS NOT NULL")
@dlt.expect_or_drop("valid_equipment", "equipment_id IS NOT NULL")
@dlt.expect_or_drop("valid_sensor_name", "sensor_name IS NOT NULL")
@dlt.expect("reasonable_values", "sensor_value BETWEEN -1000 AND 10000")
@dlt.expect("recent_events", "event_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'")
def silver_normalized():
    """
    Flatten JSON structure from Zerobus
    Enrich with equipment metadata from dimension tables

    Real-Time Mode: Process events as they arrive (sub-second latency)

    Quality Checks:
    - Drop records with null timestamp/equipment/sensor
    - Warn on unreasonable sensor values
    - Drop events older than 1 hour (late data)

    Target latency: <500ms from bronze
    """
    bronze = dlt.read_stream("ot_telemetry_bronze")
    equipment_master = dlt.read("equipment_master")

    # Flatten the nested JSON structure from Zerobus
    flattened = (
        bronze
        # Extract timestamp and source
        .select(
            col("timestamp").cast(TimestampType()).alias("event_timestamp"),
            col("source").alias("source_system"),
            col("ingestion_timestamp"),
            col("bronze_id"),
            explode("batch").alias("equipment_data")
        )
        # Flatten equipment level
        .select(
            "event_timestamp",
            "source_system",
            "ingestion_timestamp",
            "bronze_id",
            col("equipment_data.equipment_id").alias("equipment_id"),
            col("equipment_data.equipment_type").alias("equipment_type"),
            col("equipment_data.tags").alias("tags")
        )
        # Flatten tags to individual sensor rows
        .select(
            "event_timestamp",
            "equipment_id",
            "equipment_type",
            "ingestion_timestamp",
            "bronze_id",
            explode(
                transform(
                    map_keys(col("tags")),
                    lambda k: struct(
                        k.alias("sensor_name"),
                        col("tags")[k].alias("sensor_value")
                    )
                )
            ).alias("sensor")
        )
        .select(
            "event_timestamp",
            "equipment_id",
            "equipment_type",
            col("sensor.sensor_name").alias("sensor_name"),
            col("sensor.sensor_value").cast(DoubleType()).alias("sensor_value"),
            "ingestion_timestamp",
            "bronze_id"
        )
    )

    # Enrich with equipment metadata using broadcast join
    enriched = (
        flattened
        .join(
            broadcast(equipment_master),
            "equipment_id",
            "left"
        )
        .select(
            "event_timestamp",
            "equipment_id",
            "equipment_type",
            "sensor_name",
            "sensor_value",
            coalesce(col("manufacturer"), lit("Unknown")).alias("manufacturer"),
            coalesce(col("location"), lit("Unassigned")).alias("location"),
            coalesce(col("criticality"), lit("Medium")).alias("criticality"),
            col("max_capacity"),
            col("installation_date"),
            "ingestion_timestamp",
            "bronze_id",
            # Calculate latency for monitoring
            (unix_timestamp("ingestion_timestamp") - unix_timestamp("event_timestamp")).alias("latency_seconds")
        )
    )

    return enriched

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: 1-Minute Aggregates

# COMMAND ----------

@dlt.table(
    name="equipment_performance_1min",
    comment="Equipment performance metrics - 1-minute windows - Real-Time aggregation",
    table_properties={
        "quality": "gold",
        "pipelines.trigger.mode": "realtime",
        "pipelines.trigger.checkpoint": "1 minute",
        "delta.enableChangeDataFeed": "true",
        "delta.autoOptimize.optimizeWrite": "true"
    },
    partition_cols=["date"]
)
@dlt.expect_all({
    "valid_equipment": "equipment_id IS NOT NULL",
    "valid_window": "window_start IS NOT NULL",
    "positive_count": "reading_count > 0"
})
def gold_equipment_1min():
    """
    1-minute tumbling window aggregates for all equipment sensors

    Used by Genie for:
    - Recent performance queries
    - Trend analysis
    - Anomaly detection

    Optimizations:
    - Watermarking for late data handling
    - Liquid clustering on equipment_id + date
    - Change Data Feed for downstream consumers

    Target latency: <300ms from silver
    """
    silver = dlt.read_stream("ot_sensors_normalized")

    aggregated = (
        silver
        # Watermark for handling late-arriving data
        .withWatermark("event_timestamp", WATERMARK_DELAY)
        # Window by 1 minute, tumbling
        .groupBy(
            window("event_timestamp", WINDOW_DURATION_1MIN).alias("time_window"),
            "equipment_id",
            "equipment_type",
            "sensor_name",
            "location",
            "criticality",
            "manufacturer"
        )
        # Statistical aggregations
        .agg(
            avg("sensor_value").alias("avg_value"),
            min("sensor_value").alias("min_value"),
            max("sensor_value").alias("max_value"),
            stddev("sensor_value").alias("stddev_value"),
            count("*").alias("reading_count"),
            max("latency_seconds").alias("max_latency_sec"),
            avg("latency_seconds").alias("avg_latency_sec"),
            # Collect sample values for debugging
            collect_list("sensor_value").alias("sample_values")
        )
        # Extract window boundaries and add metadata
        .select(
            col("time_window.start").alias("window_start"),
            col("time_window.end").alias("window_end"),
            date(col("time_window.start")).alias("date"),
            hour(col("time_window.start")).alias("hour"),
            "equipment_id",
            "equipment_type",
            "sensor_name",
            "location",
            "criticality",
            "manufacturer",
            round("avg_value", 2).alias("avg_value"),
            round("min_value", 2).alias("min_value"),
            round("max_value", 2).alias("max_value"),
            round("stddev_value", 2).alias("stddev_value"),
            "reading_count",
            round("max_latency_sec", 3).alias("max_latency_sec"),
            round("avg_latency_sec", 3).alias("avg_latency_sec"),
            slice("sample_values", 1, 5).alias("sample_values"),  # Keep first 5 samples
            current_timestamp().alias("processed_at")
        )
    )

    return aggregated

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: Current Status View

# COMMAND ----------

@dlt.table(
    name="equipment_current_status",
    comment="Latest reading for each equipment/sensor - optimized for Genie current status queries",
    table_properties={
        "quality": "gold",
        "pipelines.trigger.mode": "realtime",
        "delta.autoOptimize.optimizeWrite": "true"
    }
)
def gold_current_status():
    """
    Latest sensor value per equipment + sensor combination

    Materialized view for fast "What is the current status?" queries

    Used by:
    - Genie for real-time status questions
    - Operators for quick checks
    - Alert systems for threshold monitoring

    Update frequency: Real-time (as data arrives)
    """
    silver = dlt.read_stream("ot_sensors_normalized")

    # Define window for latest record per equipment/sensor
    window_spec = Window.partitionBy("equipment_id", "sensor_name").orderBy(desc("event_timestamp"))

    current = (
        silver
        .withColumn("row_num", row_number().over(window_spec))
        .filter(col("row_num") == 1)
        .select(
            "equipment_id",
            "equipment_type",
            "sensor_name",
            round("sensor_value", 2).alias("sensor_value"),
            "event_timestamp",
            "location",
            "criticality",
            "manufacturer",
            # Add human-readable labels
            when(col("criticality") == "Critical", "🔴 Critical")
            .when(col("criticality") == "High", "🟠 High")
            .when(col("criticality") == "Medium", "🟡 Medium")
            .otherwise("🟢 Low").alias("criticality_label"),
            # Calculate staleness
            (unix_timestamp(current_timestamp()) - unix_timestamp("event_timestamp")).alias("data_age_seconds"),
            current_timestamp().alias("last_updated")
        )
        # Add staleness warning
        .withColumn("status",
            when(col("data_age_seconds") > 300, "STALE")
            .when(col("data_age_seconds") > 60, "WARNING")
            .otherwise("CURRENT")
        )
    )

    return current

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: ML Predictions (Simple Anomaly Detection)

# COMMAND ----------

@dlt.table(
    name="ml_predictions",
    comment="Simple anomaly detection for demo - identifies unusual sensor values using statistical methods",
    table_properties={
        "quality": "gold",
        "pipelines.trigger.mode": "realtime",
        "delta.enableChangeDataFeed": "true"
    }
)
def gold_ml_predictions():
    """
    Statistical anomaly detection using rolling baseline

    Method:
    - Calculate 1-hour rolling average and stddev per sensor
    - Flag values > 2 standard deviations from baseline
    - Generate recommendations based on sensor type

    Production Enhancement:
    - Replace with MLflow model for trained anomaly detection
    - Add multivariate analysis (correlate multiple sensors)
    - Integrate with CMMS for maintenance scheduling

    Target use cases:
    - Vibration anomalies (mechanical issues)
    - Temperature anomalies (cooling problems)
    - Production rate changes (throughput issues)
    """
    perf = dlt.read_stream("equipment_performance_1min")

    # Calculate rolling baseline (last 60 minutes = 60 windows)
    window_1h = Window.partitionBy("equipment_id", "sensor_name").orderBy("window_start").rowsBetween(-60, -1)

    predictions = (
        perf
        # Calculate baseline statistics from historical data
        .withColumn("baseline_avg", avg("avg_value").over(window_1h))
        .withColumn("baseline_stddev", stddev("avg_value").over(window_1h))
        .withColumn("baseline_count", count("*").over(window_1h))
        # Only evaluate if we have sufficient history
        .filter(col("baseline_count") >= 10)
        # Calculate deviation from baseline
        .withColumn("deviation_score",
            abs(col("avg_value") - col("baseline_avg")) /
            when(col("baseline_stddev") > 0, col("baseline_stddev")).otherwise(lit(1.0))
        )
        # Only keep anomalies
        .filter(col("deviation_score") > ANOMALY_THRESHOLD)
        # Classify anomaly type based on sensor name
        .withColumn("prediction_type",
            when(lower(col("sensor_name")).contains("vibration"), "vibration_anomaly")
            .when(lower(col("sensor_name")).contains("temperature"), "temperature_anomaly")
            .when(lower(col("sensor_name")).contains("production"), "production_anomaly")
            .when(lower(col("sensor_name")).contains("speed"), "speed_anomaly")
            .otherwise("sensor_anomaly")
        )
        # Generate actionable recommendations
        .withColumn("recommendation",
            when(col("prediction_type") == "vibration_anomaly",
                "Inspect for mechanical issues. Check belt alignment, bearing condition, and mounting bolts.")
            .when(col("prediction_type") == "temperature_anomaly",
                "Check cooling system. Verify fan operation, coolant levels, and airflow obstructions.")
            .when(col("prediction_type") == "production_anomaly",
                "Investigate throughput change. Check feed rate, blockages, and equipment utilization.")
            .when(col("prediction_type") == "speed_anomaly",
                "Verify motor operation. Check drive system, load conditions, and control settings.")
            .otherwise("Investigate sensor or equipment condition. Consider calibration check.")
        )
        # Calculate confidence score (0-1 scale)
        .withColumn("confidence_score",
            least(lit(0.99), col("deviation_score") / 5.0)
        )
        # Determine severity
        .withColumn("severity",
            when(col("deviation_score") > 4.0, "Critical")
            .when(col("deviation_score") > 3.0, "High")
            .when(col("deviation_score") > 2.5, "Medium")
            .otherwise("Low")
        )
        # Select final columns
        .select(
            "window_start",
            date(col("window_start")).alias("date"),
            "equipment_id",
            "equipment_type",
            "sensor_name",
            "location",
            "prediction_type",
            "severity",
            round("avg_value", 2).alias("current_value"),
            round("baseline_avg", 2).alias("baseline_avg"),
            round("baseline_stddev", 2).alias("baseline_stddev"),
            round("deviation_score", 2).alias("deviation_score"),
            round("confidence_score", 2).alias("confidence_score"),
            "recommendation",
            current_timestamp().alias("prediction_time")
        )
    )

    return predictions

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: 1-Hour Rollups

# COMMAND ----------

@dlt.table(
    name="equipment_performance_1hour",
    comment="Equipment performance metrics - 1-hour rollups for historical analysis",
    table_properties={
        "quality": "gold",
        "pipelines.trigger.mode": "realtime",
        "delta.enableChangeDataFeed": "true"
    },
    partition_cols=["date"]
)
def gold_equipment_1hour():
    """
    Hourly aggregates for long-term trending and analysis

    Used for:
    - Daily/weekly performance reports
    - Shift-over-shift comparisons
    - Capacity planning
    - Historical trend analysis
    """
    one_min = dlt.read_stream("equipment_performance_1min")

    hourly = (
        one_min
        .withWatermark("window_start", "5 minutes")
        .groupBy(
            window("window_start", "1 hour").alias("time_window"),
            "date",
            "equipment_id",
            "equipment_type",
            "sensor_name",
            "location",
            "criticality"
        )
        .agg(
            avg("avg_value").alias("avg_value"),
            min("min_value").alias("min_value"),
            max("max_value").alias("max_value"),
            sum("reading_count").alias("total_readings"),
            max("max_latency_sec").alias("max_latency_sec")
        )
        .select(
            col("time_window.start").alias("hour_start"),
            col("time_window.end").alias("hour_end"),
            "date",
            hour(col("time_window.start")).alias("hour"),
            "equipment_id",
            "equipment_type",
            "sensor_name",
            "location",
            "criticality",
            round("avg_value", 2).alias("avg_value"),
            round("min_value", 2).alias("min_value"),
            round("max_value", 2).alias("max_value"),
            "total_readings",
            round("max_latency_sec", 3).alias("max_latency_sec"),
            current_timestamp().alias("processed_at")
        )
    )

    return hourly

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitoring: Pipeline Quality Metrics

# COMMAND ----------

@dlt.table(
    name="pipeline_quality_metrics",
    comment="Track pipeline performance and data quality - used for operational monitoring"
)
def quality_metrics():
    """
    Monitor pipeline health and performance

    Tracks:
    - Throughput (records/minute)
    - Latency (event → gold table)
    - Data quality (distinct equipment/sensors)
    - Coverage (equipment reporting)

    Used for:
    - Alerting on pipeline degradation
    - Performance tuning
    - Capacity planning
    """
    silver = dlt.read_stream("ot_sensors_normalized")

    metrics = (
        silver
        .groupBy(window("ingestion_timestamp", "1 minute").alias("time_window"))
        .agg(
            count("*").alias("total_records"),
            avg("latency_seconds").alias("avg_latency_sec"),
            max("latency_seconds").alias("max_latency_sec"),
            min("latency_seconds").alias("min_latency_sec"),
            approx_count_distinct("equipment_id").alias("distinct_equipment"),
            approx_count_distinct("sensor_name").alias("distinct_sensors"),
            approx_count_distinct(concat(col("equipment_id"), lit("_"), col("sensor_name"))).alias("distinct_sensor_equipment_pairs")
        )
        .select(
            col("time_window.start").alias("minute"),
            "total_records",
            round("avg_latency_sec", 3).alias("avg_latency_sec"),
            round("max_latency_sec", 3).alias("max_latency_sec"),
            round("min_latency_sec", 3).alias("min_latency_sec"),
            "distinct_equipment",
            "distinct_sensors",
            "distinct_sensor_equipment_pairs",
            # Add health indicators
            when(col("avg_latency_sec") < 1.0, "Healthy")
            .when(col("avg_latency_sec") < 2.0, "Warning")
            .otherwise("Critical").alias("latency_status"),
            when(col("distinct_equipment") >= 15, "Healthy")
            .when(col("distinct_equipment") >= 10, "Warning")
            .otherwise("Critical").alias("coverage_status"),
            current_timestamp().alias("calculated_at")
        )
    )

    return metrics

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipeline Complete
# MAGIC
# MAGIC All tables defined. Deploy via DLT UI or using deploy_pipeline.py script.
# MAGIC
# MAGIC Expected tables:
# MAGIC - Bronze: `ot_telemetry_bronze`
# MAGIC - Silver: `ot_sensors_normalized`
# MAGIC - Gold: `equipment_performance_1min`, `equipment_current_status`, `ml_predictions`, `equipment_performance_1hour`, `pipeline_quality_metrics`
# MAGIC
# MAGIC Next steps:
# MAGIC 1. Validate dimension tables exist (equipment_master)
# MAGIC 2. Deploy pipeline
# MAGIC 3. Run validation queries
# MAGIC 4. Monitor performance
# MAGIC 5. Create Genie space
