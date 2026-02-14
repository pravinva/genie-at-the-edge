# RALPH WIGGUM WORKSTREAM - FILE 06
## Databricks Delta Live Tables Pipeline (Real-Time Mode)

**Purpose:** Process streaming OT data with sub-second latency using Real-Time Mode
**Location:** Databricks Repos or Workspace
**Language:** Python (PySpark with DLT decorators)
**Dependencies:** Zerobus stream active, File 05 (dimension tables)

---

## CLAUDE CODE PROMPT

```
Create a Delta Live Tables pipeline with Real-Time Mode for mining operations streaming data.

CONTEXT:
This pipeline processes sensor data from 15 pieces of mining equipment streaming via Zerobus.
It must achieve sub-second latency using Spark Structured Streaming Real-Time Mode.
The pipeline follows medallion architecture: Bronze (raw) → Silver (normalized) → Gold (analytics).

REQUIREMENTS:

1. USE DELTA LIVE TABLES FRAMEWORK:
   - Import: import dlt
   - Use @dlt.table decorators
   - Use @dlt.expect for data quality
   - Enable Real-Time Mode with table properties

2. ENABLE REAL-TIME MODE:
   - Add to EVERY streaming table: "pipelines.trigger.mode": "realtime"
   - Set checkpoint interval: "pipelines.trigger.checkpoint": "1 minute"
   - Use streaming shuffle for low latency

3. TARGET PERFORMANCE:
   - Bronze → Silver: <500ms
   - Silver → Gold: <500ms
   - Total: <1 second event to gold table

4. MEDALLION LAYERS:

BRONZE (Raw from Zerobus):
- Table: ot_telemetry_bronze
- Schema: Auto-inferred from JSON
- Quality: None (accept all)
- Retention: 30 days

SILVER (Normalized, enriched):
- Table: ot_sensors_normalized
- Schema: Flattened, typed columns
- Quality: Drop nulls, validate ranges
- Retention: 90 days
- Optimizations: Liquid clustering by equipment_id

GOLD (Analytics-ready aggregates):
- Tables: 
  - equipment_performance_1min (1-minute windows)
  - equipment_performance_1hour (1-hour rollups)
  - ml_predictions (anomaly detection)
- Quality: Complete, validated
- Retention: 2 years
- Optimizations: Partitioned by date, liquid clustering

5. DATA QUALITY:
- Use @dlt.expect_or_drop for critical validations
- Use @dlt.expect_or_fail for schema violations
- Log quarantined records
- Track quality metrics

6. JOINS WITH DIMENSION TABLES:
- Join with equipment_master for metadata
- Join with shift_schedule for business context
- Use broadcast joins for small dimensions

DETAILED SPECIFICATION:

```python
import dlt
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window

# ============================================
# BRONZE LAYER: Raw from Zerobus
# ============================================

@dlt.table(
    name="ot_telemetry_bronze",
    comment="Raw OT sensor data from Zerobus stream - Real-Time ingestion",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "ingestion_timestamp"
    }
)
def bronze_raw():
    """
    Read from Zerobus stream
    No transformation, preserve all data
    Target latency: Immediate (Zerobus handles this)
    """
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", "_schemas/ot_telemetry")
        .load("/mnt/zerobus/mining_ot_stream")  # Adjust path to your Zerobus output
        .withColumn("ingestion_timestamp", current_timestamp())
    )

# ============================================
# SILVER LAYER: Normalized with Real-Time Mode
# ============================================

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
@dlt.expect("reasonable_values", "sensor_value BETWEEN -1000 AND 10000")
def silver_normalized():
    """
    Flatten JSON structure from Zerobus
    Enrich with equipment metadata
    Real-Time Mode: Process events as they arrive
    Target latency: <500ms from bronze
    """
    bronze = dlt.read_stream("ot_telemetry_bronze")
    equipment_master = dlt.read("equipment_master")
    
    return (
        bronze
        # Explode batch array
        .select(
            col("timestamp").alias("event_timestamp"),
            col("source").alias("source_system"),
            col("ingestion_timestamp"),
            explode("batch").alias("equipment_data")
        )
        # Flatten equipment data
        .select(
            "event_timestamp",
            "source_system",
            "ingestion_timestamp",
            col("equipment_data.equipment_id").alias("equipment_id"),
            col("equipment_data.equipment_type").alias("equipment_type"),
            col("equipment_data.tags").alias("tags")
        )
        # Flatten tags to individual sensors
        .select(
            "event_timestamp",
            "equipment_id",
            "equipment_type",
            "ingestion_timestamp",
            # Dynamically extract all tag values
            # Adjust based on actual JSON structure
            explode(
                expr("""
                    transform(
                        map_keys(tags),
                        k -> struct(
                            k as sensor_name,
                            tags[k] as sensor_value
                        )
                    )
                """)
            ).alias("sensor")
        )
        .select(
            "event_timestamp",
            "equipment_id",
            "equipment_type",
            col("sensor.sensor_name").alias("sensor_name"),
            col("sensor.sensor_value").alias("sensor_value"),
            "ingestion_timestamp"
        )
        # Enrich with equipment metadata
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
            "manufacturer",
            "location",
            "criticality",
            "ingestion_timestamp",
            # Latency tracking
            (unix_timestamp("ingestion_timestamp") - unix_timestamp("event_timestamp")).alias("latency_seconds")
        )
    )

# ============================================
# GOLD LAYER: Analytics Aggregates (Real-Time)
# ============================================

@dlt.table(
    name="equipment_performance_1min",
    comment="Equipment performance metrics - 1-minute windows - Real-Time aggregation",
    table_properties={
        "quality": "gold",
        "pipelines.trigger.mode": "realtime",
        "pipelines.trigger.checkpoint": "1 minute",
        "delta.enableChangeDataFeed": "true"
    },
    partition_cols=["date"]
)
@dlt.expect_all({
    "valid_equipment": "equipment_id IS NOT NULL",
    "valid_window": "window_start IS NOT NULL"
})
def gold_equipment_1min():
    """
    1-minute aggregates for all equipment sensors
    Used by Genie for recent performance queries
    Target latency: <300ms from silver
    """
    silver = dlt.read_stream("ot_sensors_normalized")
    
    return (
        silver
        # Watermark for handling late data
        .withWatermark("event_timestamp", "30 seconds")
        # Window by 1 minute, tumbling
        .groupBy(
            window("event_timestamp", "1 minute").alias("time_window"),
            "equipment_id",
            "equipment_type",
            "sensor_name",
            "location",
            "criticality"
        )
        # Aggregations
        .agg(
            avg("sensor_value").alias("avg_value"),
            min("sensor_value").alias("min_value"),
            max("sensor_value").alias("max_value"),
            stddev("sensor_value").alias("stddev_value"),
            count("*").alias("reading_count"),
            max("latency_seconds").alias("max_latency_sec")
        )
        # Extract window boundaries
        .select(
            col("time_window.start").alias("window_start"),
            col("time_window.end").alias("window_end"),
            date(col("time_window.start")).alias("date"),
            "equipment_id",
            "equipment_type",
            "sensor_name",
            "location",
            "criticality",
            "avg_value",
            "min_value",
            "max_value",
            "stddev_value",
            "reading_count",
            "max_latency_sec",
            current_timestamp().alias("processed_at")
        )
        # Liquid clustering for Genie query patterns
        .withMetadata("delta.clustering.columns", "equipment_id,date")
    )

# ============================================
# GOLD: Simplified Current Status View
# ============================================

@dlt.table(
    name="equipment_current_status",
    comment="Latest reading for each equipment - optimized for Genie current status queries",
    table_properties={
        "quality": "gold",
        "pipelines.trigger.mode": "realtime"
    }
)
def gold_current_status():
    """
    Latest sensor values per equipment
    Materialized for fast "current status" queries
    """
    silver = dlt.read_stream("ot_sensors_normalized")
    
    # Window function to get latest per equipment + sensor
    window_spec = Window.partitionBy("equipment_id", "sensor_name").orderBy(desc("event_timestamp"))
    
    return (
        silver
        .withColumn("row_num", row_number().over(window_spec))
        .filter(col("row_num") == 1)
        .select(
            "equipment_id",
            "equipment_type",
            "sensor_name",
            "sensor_value",
            "event_timestamp",
            "location",
            "criticality",
            "manufacturer"
        )
    )

# ============================================
# GOLD: Simple Anomaly Detection (ML Predictions)
# ============================================

@dlt.table(
    name="ml_predictions",
    comment="Simple anomaly detection for demo - identifies unusual sensor values",
    table_properties={
        "quality": "gold",
        "pipelines.trigger.mode": "realtime"
    }
)
def gold_ml_predictions():
    """
    Simple statistical anomaly detection
    For production: Replace with MLflow model
    """
    perf = dlt.read_stream("equipment_performance_1min")
    
    # Calculate rolling baseline (last 1 hour)
    window_1h = Window.partitionBy("equipment_id", "sensor_name").orderBy("window_start").rowsBetween(-60, -1)
    
    return (
        perf
        # Calculate baseline from history
        .withColumn("baseline_avg", avg("avg_value").over(window_1h))
        .withColumn("baseline_stddev", stddev("avg_value").over(window_1h))
        # Detect anomalies (> 2 standard deviations)
        .withColumn("deviation_score", 
            abs(col("avg_value") - col("baseline_avg")) / col("baseline_stddev")
        )
        .filter(col("deviation_score") > 2.0)  # Only anomalies
        # Classify prediction type
        .withColumn("prediction_type",
            when(col("sensor_name").contains("Vibration"), "vibration_anomaly")
            .when(col("sensor_name").contains("Temperature"), "temperature_anomaly")
            .otherwise("sensor_anomaly")
        )
        # Generate recommendation
        .withColumn("recommendation",
            when(col("prediction_type") == "vibration_anomaly", 
                "Inspect for mechanical issues. Check belt alignment and bearing condition.")
            .when(col("prediction_type") == "temperature_anomaly",
                "Check cooling system. Verify fan operation and coolant levels.")
            .otherwise("Investigate sensor or equipment condition.")
        )
        # Confidence score (simple: based on deviation)
        .withColumn("confidence_score",
            least(lit(0.99), col("deviation_score") / 5.0)  # Scale to 0-1
        )
        .select(
            "window_start",
            "equipment_id",
            "sensor_name",
            "prediction_type",
            "avg_value",
            "baseline_avg",
            "deviation_score",
            "confidence_score",
            "recommendation",
            current_timestamp().alias("prediction_time")
        )
    )

# ============================================
# MONITORING & QUALITY METRICS
# ============================================

@dlt.table(
    name="pipeline_quality_metrics",
    comment="Track pipeline performance and data quality"
)
def quality_metrics():
    """
    Monitor pipeline health
    """
    silver = dlt.read_stream("ot_sensors_normalized")
    
    return (
        silver
        .groupBy(window("ingestion_timestamp", "1 minute"))
        .agg(
            count("*").alias("total_records"),
            avg("latency_seconds").alias("avg_latency_sec"),
            max("latency_seconds").alias("max_latency_sec"),
            approx_count_distinct("equipment_id").alias("distinct_equipment"),
            approx_count_distinct("sensor_name").alias("distinct_sensors")
        )
        .select(
            col("window.start").alias("minute"),
            "total_records",
            "avg_latency_sec",
            "max_latency_sec",
            "distinct_equipment",
            "distinct_sensors"
        )
    )
```

---

## PIPELINE CONFIGURATION

**Create DLT Pipeline in Databricks UI:**

```
Workflow > Delta Live Tables > Create Pipeline

Name: mining_operations_realtime
Target: field_engineering.mining_demo
Notebook/File: [Path to this Python file]
Cluster Mode: Enhanced Autoscaling (for Real-Time Mode)
Cluster Config:
  - Runtime: 16.4 or higher (required for Real-Time Mode)
  - Photon: Enabled
  - Node type: i3.xlarge or similar (good for streaming)
  - Min workers: 2
  - Max workers: 4

Advanced:
  - Enable Real-Time processing: ✓ (checked)
  - Configuration:
    - spark.databricks.streaming.mode: realtime
    - spark.sql.shuffle.partitions: 200
  - Storage location: Default (Unity Catalog managed)
  - Checkpoint location: Default

Development: ✓ (for testing, uncheck for production)
```

---

## OPTIMIZATION TECHNIQUES

**1. Liquid Clustering (Better than partitioning for this use case):**

```python
# After table creation, enable clustering
@dlt.table(
    table_properties={
        "delta.enableChangeDataFeed": "true",
        "delta.tuneFileSizesForRewrites": "true"
    }
)
def equipment_performance_1min():
    # ... table definition
    pass

# After pipeline runs once, optimize:
# In SQL notebook:
# ALTER TABLE field_engineering.mining_demo.equipment_performance_1min
# CLUSTER BY (equipment_id, date(window_start));
```

**2. Broadcast Joins for Small Tables:**

```python
from pyspark.sql.functions import broadcast

# When joining with equipment_master (small table)
.join(broadcast(equipment_master), "equipment_id", "left")
```

**3. Watermarking for Late Data:**

```python
# Handle events arriving out of order
.withWatermark("event_timestamp", "30 seconds")
# Events >30s late will be dropped
```

**4. Z-Ordering (in addition to clustering):**

```sql
-- Run after pipeline deployed:
OPTIMIZE field_engineering.mining_demo.equipment_performance_1min
ZORDER BY (equipment_id, window_start);
```

---

## ALTERNATIVE: Simple Pipeline (If Real-Time Mode Has Issues)

**Fallback to micro-batch with very short intervals:**

```python
# If Real-Time Mode is unstable in preview

@dlt.table(
    table_properties={
        "pipelines.trigger": "availableNow",  # Process immediately
        "pipelines.microbatchInterval": "2 seconds"  # Very short batches
    }
)
def silver_normalized_microbatch():
    # Same logic, but micro-batch instead of real-time
    # Latency: ~2-3 seconds instead of <1s
    pass
```

---

## DEPLOYMENT STEPS

**1. Create Python file in Databricks:**

```
Location: 
/Repos/pravin.varma@databricks.com/mining-genie-demo/pipelines/mining_realtime_dlt.py

Paste the generated code from Claude Code
```

**2. Create DLT Pipeline via UI:**

```
Workflows > Delta Live Tables > Create Pipeline
- Name: mining_operations_realtime
- Select: mining_realtime_dlt.py
- Target: field_engineering.mining_demo
- Configure as specified above
- Save (don't start yet)
```

**3. Validate configuration:**

```
Click: Validate
Should show:
- ✓ Tables: bronze, silver, gold detected
- ✓ Dependencies: Correctly ordered
- ✓ Quality expectations: Defined
```

**4. Start pipeline:**

```
Click: Start
Watch: Graph updates showing data flow
Bronze → Silver → Gold
Check: Update latencies in graph
```

---

## VALIDATION QUERIES

**After pipeline running:**

**1. Check bronze ingestion:**
```sql
SELECT 
  count(*) as total_records,
  min(ingestion_timestamp) as first_event,
  max(ingestion_timestamp) as last_event,
  count(DISTINCT equipment_id) as distinct_equipment
FROM field_engineering.mining_demo.ot_telemetry_bronze
WHERE ingestion_timestamp > CURRENT_TIMESTAMP - INTERVAL '5 minutes';

-- Should see: Records accumulating, 15 distinct equipment IDs
```

**2. Check silver normalization:**
```sql
SELECT 
  equipment_id,
  sensor_name,
  count(*) as reading_count,
  avg(sensor_value) as avg_value,
  max(event_timestamp) as latest_reading
FROM field_engineering.mining_demo.ot_sensors_normalized
WHERE event_timestamp > CURRENT_TIMESTAMP - INTERVAL '5 minutes'
GROUP BY equipment_id, sensor_name
ORDER BY equipment_id, sensor_name;

-- Should see: All 15 equipment, multiple sensors each, recent timestamps
```

**3. Check gold aggregation:**
```sql
SELECT 
  window_start,
  equipment_id,
  sensor_name,
  avg_value,
  reading_count
FROM field_engineering.mining_demo.equipment_performance_1min
WHERE window_start > CURRENT_TIMESTAMP - INTERVAL '30 minutes'
  AND equipment_id = 'CR_002'
  AND sensor_name = 'Vibration_MM_S'
ORDER BY window_start DESC
LIMIT 30;

-- Should see: 1-minute windows, recent data, realistic values
```

**4. Check latency:**
```sql
SELECT 
  avg(max_latency_sec) as avg_pipeline_latency,
  max(max_latency_sec) as max_pipeline_latency,
  count(*) as windows_processed
FROM field_engineering.mining_demo.pipeline_quality_metrics
WHERE minute > CURRENT_TIMESTAMP - INTERVAL '10 minutes';

-- Target: avg_latency < 1 second, max < 2 seconds
```

---

## MONITORING

**DLT Pipeline UI:**
- Watch: Data Quality tab (expectation pass rates)
- Watch: Progress tab (tables updating in real-time)
- Watch: Latency metrics in lineage graph

**SQL Queries:**
```sql
-- Check for quarantined records (quality failures)
SELECT * FROM field_engineering.mining_demo.ot_sensors_normalized
WHERE _rescued_data IS NOT NULL
LIMIT 10;

-- Should be empty or minimal
```

**System Tables:**
```sql
-- Pipeline event log
SELECT * FROM event_log('field_engineering.mining_demo')
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

---

## TROUBLESHOOTING

**Pipeline won't start:**
- Check: Runtime version ≥16.4 (for Real-Time Mode)
- Check: Cluster has sufficient resources
- Check: No syntax errors in Python code
- Check: Zerobus stream exists and has data

**High latency (>5s):**
- Check: Too many shuffle partitions (reduce to 50-100 for small data)
- Check: Not using broadcast for small dimension joins
- Check: Warehouse is warmed up (not cold start)
- Optimize: Add liquid clustering, z-ordering

**Data quality issues:**
- Check: Bronze has valid JSON (not malformed)
- Check: Expectation rules (might be too strict)
- Review: Quarantine table for failed records
- Fix: Upstream Zerobus JSON format

**Real-Time Mode errors:**
- Fallback: Remove "realtime" trigger, use micro-batch
- Check: DBR version supports Real-Time Mode (16.4+)
- Review: Databricks documentation for latest Real-Time Mode requirements

---

## COMPLETION CHECKLIST

- [ ] Python file created in Repos/Workspace
- [ ] DLT pipeline configured via UI
- [ ] Pipeline starts without errors
- [ ] Bronze table receiving data from Zerobus
- [ ] Silver table normalizing within <1s
- [ ] Gold tables aggregating within <1s
- [ ] Quality metrics show <1s latency
- [ ] Validation queries return expected results
- [ ] No errors in pipeline event log
- [ ] Data visible in all 3 layers (bronze/silver/gold)
- [ ] Ready for Genie integration (File 07)

---

**Estimated time:** 3-4 hours (including Claude Code generation + validation)
**Next:** File 07 - Genie space configuration to query these gold tables
