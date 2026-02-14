-- Databricks notebook source
-- MAGIC %md
-- MAGIC # DLT Pipeline Validation Queries
-- MAGIC
-- MAGIC Run these queries to validate the pipeline is working correctly.
-- MAGIC
-- MAGIC **Run after:**
-- MAGIC - DLT pipeline has been started
-- MAGIC - Data is flowing from Zerobus
-- MAGIC - At least 5-10 minutes of runtime

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1. Bronze Layer Validation

-- COMMAND ----------

-- Check bronze table ingestion
SELECT
  COUNT(*) as total_records,
  MIN(ingestion_timestamp) as first_event,
  MAX(ingestion_timestamp) as last_event,
  ROUND((UNIX_TIMESTAMP(MAX(ingestion_timestamp)) - UNIX_TIMESTAMP(MIN(ingestion_timestamp))) / 60, 2) as duration_minutes,
  ROUND(COUNT(*) / ((UNIX_TIMESTAMP(MAX(ingestion_timestamp)) - UNIX_TIMESTAMP(MIN(ingestion_timestamp))) / 60), 0) as avg_records_per_minute
FROM field_engineering.mining_demo.ot_telemetry_bronze
WHERE ingestion_timestamp > CURRENT_TIMESTAMP - INTERVAL '30 minutes';

-- Expected: Records accumulating, duration > 5 minutes, consistent rate

-- COMMAND ----------

-- Check bronze data freshness
SELECT
  MAX(ingestion_timestamp) as last_ingestion,
  ROUND((UNIX_TIMESTAMP(CURRENT_TIMESTAMP()) - UNIX_TIMESTAMP(MAX(ingestion_timestamp))) / 60, 2) as minutes_ago,
  CASE
    WHEN MAX(ingestion_timestamp) > CURRENT_TIMESTAMP - INTERVAL '2 minutes' THEN 'HEALTHY'
    WHEN MAX(ingestion_timestamp) > CURRENT_TIMESTAMP - INTERVAL '5 minutes' THEN 'WARNING'
    ELSE 'STALE'
  END as status
FROM field_engineering.mining_demo.ot_telemetry_bronze;

-- Expected: status = 'HEALTHY', minutes_ago < 2

-- COMMAND ----------

-- Check bronze data structure (sample)
SELECT *
FROM field_engineering.mining_demo.ot_telemetry_bronze
ORDER BY ingestion_timestamp DESC
LIMIT 3;

-- Expected: Valid JSON structure with timestamp, source, batch array

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2. Silver Layer Validation

-- COMMAND ----------

-- Check silver normalization
SELECT
  equipment_id,
  equipment_type,
  COUNT(DISTINCT sensor_name) as sensor_count,
  COUNT(*) as reading_count,
  MAX(event_timestamp) as latest_reading,
  ROUND(AVG(latency_seconds), 3) as avg_latency_sec
FROM field_engineering.mining_demo.ot_sensors_normalized
WHERE event_timestamp > CURRENT_TIMESTAMP - INTERVAL '10 minutes'
GROUP BY equipment_id, equipment_type
ORDER BY equipment_id;

-- Expected:
-- - 15 distinct equipment_id
-- - Each equipment has multiple sensors (5-10)
-- - avg_latency_sec < 2.0 seconds

-- COMMAND ----------

-- Check silver data quality (null checks)
SELECT
  COUNT(*) as total_records,
  SUM(CASE WHEN equipment_id IS NULL THEN 1 ELSE 0 END) as null_equipment_id,
  SUM(CASE WHEN sensor_name IS NULL THEN 1 ELSE 0 END) as null_sensor_name,
  SUM(CASE WHEN sensor_value IS NULL THEN 1 ELSE 0 END) as null_sensor_value,
  SUM(CASE WHEN event_timestamp IS NULL THEN 1 ELSE 0 END) as null_timestamp,
  ROUND(100.0 * SUM(CASE WHEN equipment_id IS NOT NULL AND sensor_name IS NOT NULL AND sensor_value IS NOT NULL AND event_timestamp IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as quality_pct
FROM field_engineering.mining_demo.ot_sensors_normalized
WHERE event_timestamp > CURRENT_TIMESTAMP - INTERVAL '30 minutes';

-- Expected: quality_pct > 99%, all null counts = 0 (due to expect_or_drop)

-- COMMAND ----------

-- Check silver sensor distribution
SELECT
  sensor_name,
  COUNT(DISTINCT equipment_id) as equipment_count,
  COUNT(*) as reading_count,
  ROUND(AVG(sensor_value), 2) as avg_value,
  ROUND(MIN(sensor_value), 2) as min_value,
  ROUND(MAX(sensor_value), 2) as max_value
FROM field_engineering.mining_demo.ot_sensors_normalized
WHERE event_timestamp > CURRENT_TIMESTAMP - INTERVAL '30 minutes'
GROUP BY sensor_name
ORDER BY sensor_name;

-- Expected: Multiple sensor types, realistic value ranges

-- COMMAND ----------

-- Check silver enrichment (joined with equipment_master)
SELECT
  location,
  criticality,
  COUNT(DISTINCT equipment_id) as equipment_count,
  COUNT(*) as reading_count
FROM field_engineering.mining_demo.ot_sensors_normalized
WHERE event_timestamp > CURRENT_TIMESTAMP - INTERVAL '10 minutes'
GROUP BY location, criticality
ORDER BY criticality, location;

-- Expected: All records enriched with location and criticality

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. Gold Layer - 1-Minute Aggregates Validation

-- COMMAND ----------

-- Check 1-minute aggregation
SELECT
  window_start,
  COUNT(DISTINCT equipment_id) as equipment_count,
  COUNT(DISTINCT sensor_name) as sensor_count,
  COUNT(*) as aggregate_count,
  ROUND(AVG(reading_count), 0) as avg_readings_per_aggregate,
  ROUND(MAX(max_latency_sec), 3) as max_latency_sec
FROM field_engineering.mining_demo.equipment_performance_1min
WHERE window_start > CURRENT_TIMESTAMP - INTERVAL '30 minutes'
GROUP BY window_start
ORDER BY window_start DESC
LIMIT 10;

-- Expected:
-- - Continuous 1-minute windows
-- - equipment_count = 15
-- - sensor_count = 10 (or number of sensor types)
-- - max_latency_sec < 2.0

-- COMMAND ----------

-- Check specific equipment performance (CR_002 example)
SELECT
  window_start,
  sensor_name,
  ROUND(avg_value, 2) as avg_value,
  ROUND(min_value, 2) as min_value,
  ROUND(max_value, 2) as max_value,
  reading_count
FROM field_engineering.mining_demo.equipment_performance_1min
WHERE equipment_id = 'CR_002'
  AND window_start > CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY window_start DESC, sensor_name
LIMIT 30;

-- Expected: Recent windows with realistic sensor values

-- COMMAND ----------

-- Check aggregation freshness
SELECT
  MAX(window_start) as latest_window,
  ROUND((UNIX_TIMESTAMP(CURRENT_TIMESTAMP()) - UNIX_TIMESTAMP(MAX(window_start))) / 60, 2) as minutes_behind,
  CASE
    WHEN MAX(window_start) > CURRENT_TIMESTAMP - INTERVAL '3 minutes' THEN 'HEALTHY'
    WHEN MAX(window_start) > CURRENT_TIMESTAMP - INTERVAL '10 minutes' THEN 'WARNING'
    ELSE 'STALE'
  END as status
FROM field_engineering.mining_demo.equipment_performance_1min;

-- Expected: status = 'HEALTHY', minutes_behind < 3

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Gold Layer - Current Status Validation

-- COMMAND ----------

-- Check current status table
SELECT
  equipment_id,
  equipment_type,
  COUNT(*) as sensor_count,
  MAX(event_timestamp) as latest_reading,
  ROUND(AVG(data_age_seconds), 1) as avg_data_age_sec,
  COUNT(CASE WHEN status = 'CURRENT' THEN 1 END) as current_sensors,
  COUNT(CASE WHEN status = 'WARNING' THEN 1 END) as warning_sensors,
  COUNT(CASE WHEN status = 'STALE' THEN 1 END) as stale_sensors
FROM field_engineering.mining_demo.equipment_current_status
GROUP BY equipment_id, equipment_type
ORDER BY equipment_id;

-- Expected:
-- - 15 equipment with sensors
-- - Most sensors in 'CURRENT' status
-- - avg_data_age_sec < 60 for active equipment

-- COMMAND ----------

-- Check equipment with issues
SELECT
  equipment_id,
  equipment_type,
  sensor_name,
  sensor_value,
  event_timestamp,
  criticality,
  status,
  ROUND(data_age_seconds, 1) as data_age_sec
FROM field_engineering.mining_demo.equipment_current_status
WHERE status IN ('WARNING', 'STALE')
  OR criticality IN ('Critical', 'High')
ORDER BY criticality DESC, status, data_age_seconds DESC;

-- Expected: Minimal stale sensors, investigate any critical equipment with issues

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 5. Gold Layer - ML Predictions Validation

-- COMMAND ----------

-- Check anomaly detection
SELECT
  DATE(window_start) as date,
  COUNT(*) as anomaly_count,
  COUNT(DISTINCT equipment_id) as affected_equipment,
  SUM(CASE WHEN severity = 'Critical' THEN 1 ELSE 0 END) as critical_count,
  SUM(CASE WHEN severity = 'High' THEN 1 ELSE 0 END) as high_count,
  SUM(CASE WHEN severity = 'Medium' THEN 1 ELSE 0 END) as medium_count
FROM field_engineering.mining_demo.ml_predictions
WHERE window_start > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY DATE(window_start)
ORDER BY date DESC;

-- Expected: Some anomalies detected (depends on simulation), distributed across severity levels

-- COMMAND ----------

-- Check recent predictions (last hour)
SELECT
  window_start,
  equipment_id,
  sensor_name,
  prediction_type,
  severity,
  ROUND(current_value, 2) as current_value,
  ROUND(baseline_avg, 2) as baseline_avg,
  ROUND(deviation_score, 2) as deviation_score,
  ROUND(confidence_score, 2) as confidence,
  recommendation
FROM field_engineering.mining_demo.ml_predictions
WHERE window_start > CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY severity DESC, deviation_score DESC
LIMIT 10;

-- Expected: Anomalies with recommendations, sorted by severity

-- COMMAND ----------

-- Check prediction types distribution
SELECT
  prediction_type,
  COUNT(*) as prediction_count,
  AVG(deviation_score) as avg_deviation,
  AVG(confidence_score) as avg_confidence
FROM field_engineering.mining_demo.ml_predictions
WHERE window_start > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY prediction_type
ORDER BY prediction_count DESC;

-- Expected: Different anomaly types (vibration, temperature, etc.)

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 6. Pipeline Quality Metrics Validation

-- COMMAND ----------

-- Check pipeline health (last hour)
SELECT
  minute,
  total_records,
  ROUND(avg_latency_sec, 3) as avg_latency_sec,
  ROUND(max_latency_sec, 3) as max_latency_sec,
  distinct_equipment,
  distinct_sensors,
  latency_status,
  coverage_status
FROM field_engineering.mining_demo.pipeline_quality_metrics
WHERE minute > CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY minute DESC
LIMIT 20;

-- Expected:
-- - latency_status = 'Healthy' (avg < 1s)
-- - coverage_status = 'Healthy' (15 equipment)
-- - Consistent metrics across windows

-- COMMAND ----------

-- Pipeline health summary
SELECT
  COUNT(*) as total_windows,
  ROUND(AVG(avg_latency_sec), 3) as overall_avg_latency,
  ROUND(MAX(max_latency_sec), 3) as overall_max_latency,
  ROUND(AVG(distinct_equipment), 1) as avg_equipment_reporting,
  ROUND(AVG(total_records), 0) as avg_records_per_minute,
  SUM(CASE WHEN latency_status = 'Healthy' THEN 1 ELSE 0 END) as healthy_windows,
  SUM(CASE WHEN latency_status = 'Warning' THEN 1 ELSE 0 END) as warning_windows,
  SUM(CASE WHEN latency_status = 'Critical' THEN 1 ELSE 0 END) as critical_windows,
  ROUND(100.0 * SUM(CASE WHEN latency_status = 'Healthy' THEN 1 ELSE 0 END) / COUNT(*), 1) as health_pct
FROM field_engineering.mining_demo.pipeline_quality_metrics
WHERE minute > CURRENT_TIMESTAMP - INTERVAL '1 hour';

-- Expected:
-- - overall_avg_latency < 1.0s
-- - health_pct > 90%
-- - avg_equipment_reporting = 15

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 7. End-to-End Latency Check

-- COMMAND ----------

-- Measure Bronze → Silver → Gold latency
WITH latest_bronze AS (
  SELECT MAX(ingestion_timestamp) as bronze_time
  FROM field_engineering.mining_demo.ot_telemetry_bronze
),
latest_silver AS (
  SELECT MAX(ingestion_timestamp) as silver_time
  FROM field_engineering.mining_demo.ot_sensors_normalized
),
latest_gold AS (
  SELECT MAX(processed_at) as gold_time
  FROM field_engineering.mining_demo.equipment_performance_1min
)
SELECT
  bronze_time,
  silver_time,
  gold_time,
  ROUND(UNIX_TIMESTAMP(silver_time) - UNIX_TIMESTAMP(bronze_time), 2) as bronze_to_silver_sec,
  ROUND(UNIX_TIMESTAMP(gold_time) - UNIX_TIMESTAMP(silver_time), 2) as silver_to_gold_sec,
  ROUND(UNIX_TIMESTAMP(gold_time) - UNIX_TIMESTAMP(bronze_time), 2) as end_to_end_sec,
  CASE
    WHEN UNIX_TIMESTAMP(gold_time) - UNIX_TIMESTAMP(bronze_time) < 2.0 THEN 'EXCELLENT'
    WHEN UNIX_TIMESTAMP(gold_time) - UNIX_TIMESTAMP(bronze_time) < 5.0 THEN 'GOOD'
    WHEN UNIX_TIMESTAMP(gold_time) - UNIX_TIMESTAMP(bronze_time) < 10.0 THEN 'ACCEPTABLE'
    ELSE 'NEEDS_IMPROVEMENT'
  END as performance_rating
FROM latest_bronze, latest_silver, latest_gold;

-- Expected: end_to_end_sec < 2.0s (EXCELLENT), < 5.0s (GOOD)

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 8. Data Completeness Check

-- COMMAND ----------

-- Check for missing equipment (should see all 15)
WITH expected_equipment AS (
  SELECT equipment_id
  FROM field_engineering.mining_demo.equipment_master
  WHERE is_active = true
),
reporting_equipment AS (
  SELECT DISTINCT equipment_id
  FROM field_engineering.mining_demo.equipment_current_status
)
SELECT
  e.equipment_id,
  CASE WHEN r.equipment_id IS NOT NULL THEN 'REPORTING' ELSE 'MISSING' END as status
FROM expected_equipment e
LEFT JOIN reporting_equipment r ON e.equipment_id = r.equipment_id
ORDER BY status DESC, e.equipment_id;

-- Expected: All equipment with status = 'REPORTING'

-- COMMAND ----------

-- Check for sensor coverage per equipment
SELECT
  em.equipment_id,
  em.equipment_type,
  em.criticality,
  COUNT(DISTINCT ecs.sensor_name) as reporting_sensors,
  MAX(ecs.event_timestamp) as last_seen,
  ROUND((UNIX_TIMESTAMP(CURRENT_TIMESTAMP()) - UNIX_TIMESTAMP(MAX(ecs.event_timestamp))) / 60, 1) as minutes_ago
FROM field_engineering.mining_demo.equipment_master em
LEFT JOIN field_engineering.mining_demo.equipment_current_status ecs
  ON em.equipment_id = ecs.equipment_id
WHERE em.is_active = true
GROUP BY em.equipment_id, em.equipment_type, em.criticality
ORDER BY em.criticality DESC, minutes_ago DESC;

-- Expected: All equipment reporting multiple sensors, last_seen within 5 minutes

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 9. Performance Benchmarks

-- COMMAND ----------

-- Measure query performance on gold tables
SELECT
  'equipment_performance_1min' as table_name,
  COUNT(*) as row_count,
  COUNT(DISTINCT equipment_id) as distinct_equipment,
  MIN(window_start) as earliest_data,
  MAX(window_start) as latest_data
FROM field_engineering.mining_demo.equipment_performance_1min
WHERE window_start > CURRENT_TIMESTAMP - INTERVAL '24 hours'

UNION ALL

SELECT
  'equipment_current_status' as table_name,
  COUNT(*) as row_count,
  COUNT(DISTINCT equipment_id) as distinct_equipment,
  MIN(event_timestamp) as earliest_data,
  MAX(event_timestamp) as latest_data
FROM field_engineering.mining_demo.equipment_current_status

UNION ALL

SELECT
  'ml_predictions' as table_name,
  COUNT(*) as row_count,
  COUNT(DISTINCT equipment_id) as distinct_equipment,
  MIN(window_start) as earliest_data,
  MAX(window_start) as latest_data
FROM field_engineering.mining_demo.ml_predictions
WHERE window_start > CURRENT_TIMESTAMP - INTERVAL '24 hours';

-- Expected: All tables populated, latest_data recent

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 10. Troubleshooting Queries

-- COMMAND ----------

-- Check for errors in DLT event log
SELECT
  timestamp,
  event_type,
  message,
  level,
  details
FROM event_log('field_engineering.mining_demo')
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
  AND level IN ('ERROR', 'WARN')
ORDER BY timestamp DESC
LIMIT 20;

-- Expected: Minimal errors, investigate any critical issues

-- COMMAND ----------

-- Check for data quality violations (rescued data)
SELECT
  COUNT(*) as rescued_count,
  COUNT(CASE WHEN _rescued_data IS NOT NULL THEN 1 END) as records_with_rescued_data,
  ROUND(100.0 * COUNT(CASE WHEN _rescued_data IS NOT NULL THEN 1 END) / COUNT(*), 2) as rescued_pct
FROM field_engineering.mining_demo.ot_sensors_normalized
WHERE ingestion_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour';

-- Expected: rescued_pct = 0% (all data conforming to schema)

-- COMMAND ----------

-- Check table sizes and partitions
DESCRIBE DETAIL field_engineering.mining_demo.equipment_performance_1min;

-- Check partition distribution
SELECT
  date,
  COUNT(*) as row_count,
  COUNT(DISTINCT equipment_id) as equipment_count
FROM field_engineering.mining_demo.equipment_performance_1min
GROUP BY date
ORDER BY date DESC
LIMIT 7;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Validation Complete
-- MAGIC
-- MAGIC If all queries return expected results:
-- MAGIC - Pipeline is healthy
-- MAGIC - Data quality is good
-- MAGIC - Latency targets met (<2s end-to-end)
-- MAGIC - Ready for Genie integration
-- MAGIC
-- MAGIC Next: Run genie_space_setup.sql to create Genie space
