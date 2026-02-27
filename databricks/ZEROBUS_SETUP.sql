-- ==============================================================================
-- ZEROBUS DATABRICKS SETUP - Complete SQL Script
-- ==============================================================================
-- Purpose: Create schema and table for Ignition Zerobus streaming
-- Target: field_engineering.ignition_streaming.sensor_events
-- Date: February 27, 2026
-- ==============================================================================

-- 1. CREATE SCHEMA
-- ------------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS field_engineering.ignition_streaming
COMMENT 'Ignition Zerobus bronze schema';

-- Verify schema created
SHOW SCHEMAS IN field_engineering;

-- 2. CREATE STREAMING TABLE
-- ------------------------------------------------------------------------------
-- IMPORTANT:
-- This schema must match module/src/main/proto/ot_event.proto and current mapper behavior.
CREATE TABLE IF NOT EXISTS field_engineering.ignition_streaming.sensor_events (
    event_id STRING,
    event_time TIMESTAMP,
    tag_path STRING,
    tag_provider STRING,
    numeric_value DOUBLE,
    string_value STRING,
    boolean_value BOOLEAN,
    quality STRING,
    quality_code INT,
    source_system STRING,
    ingestion_timestamp BIGINT,
    data_type STRING,
    alarm_state STRING,
    alarm_priority INT,
    sdt_compressed BOOLEAN,
    compression_ratio DOUBLE,
    sdt_enabled BOOLEAN,
    batch_bytes_sent BIGINT
)
USING DELTA
COMMENT 'Ignition Zerobus OT event bronze stream'
TBLPROPERTIES (
    'delta.enableZerobus' = 'true',
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- Verify table created
SHOW TABLES IN field_engineering.ignition_streaming;

-- 3. DESCRIBE TABLE STRUCTURE
-- ------------------------------------------------------------------------------
DESCRIBE EXTENDED field_engineering.ignition_streaming.sensor_events;

-- 4. GRANT PERMISSIONS
-- ------------------------------------------------------------------------------
-- Replace with your service principal UUID/client id as needed.
-- GRANT USE CATALOG ON CATALOG field_engineering TO `6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb`;
-- GRANT USE SCHEMA ON SCHEMA field_engineering.ignition_streaming TO `6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb`;
-- GRANT SELECT, MODIFY ON TABLE field_engineering.ignition_streaming.sensor_events TO `6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb`;

-- ==============================================================================
-- VERIFICATION QUERIES
-- ==============================================================================

-- 5. CHECK IF DATA IS STREAMING (run after Zerobus is configured)
-- ------------------------------------------------------------------------------
SELECT
    event_id,
    event_time,
    tag_path,
    numeric_value,
    string_value,
    boolean_value,
    quality,
    quality_code,
    source_system,
    ingestion_timestamp
FROM field_engineering.ignition_streaming.sensor_events
ORDER BY ingestion_timestamp DESC
LIMIT 20;

-- Expected: New records appearing every 1 second with active tag paths

-- 6. COUNT RECORDS BY TAG PROVIDER/PATH
-- ------------------------------------------------------------------------------
SELECT
    tag_provider,
    COUNT(*) AS total_records,
    COUNT(DISTINCT tag_path) AS distinct_tags,
    MIN(event_time) AS first_event_time,
    MAX(event_time) AS last_event_time
FROM field_engineering.ignition_streaming.sensor_events
GROUP BY tag_provider
ORDER BY total_records DESC;

-- Expected: Non-zero rows and non-zero distinct_tags for active providers

-- 7. MONITOR STREAMING RATE
-- ------------------------------------------------------------------------------
WITH normalized AS (
    SELECT
        tag_path,
        COALESCE(
            TRY_CAST(event_time AS TIMESTAMP),
            TIMESTAMP_MICROS(TRY_CAST(event_time AS BIGINT))
        ) AS event_ts,
        COALESCE(
            TRY_CAST(ingestion_timestamp AS BIGINT),
            UNIX_MICROS(TRY_CAST(ingestion_timestamp AS TIMESTAMP))
        ) AS ingestion_us
    FROM field_engineering.ignition_streaming.sensor_events
)
SELECT
    DATE_TRUNC('minute', event_ts) AS minute_bucket,
    COUNT(*) AS records_per_minute,
    COUNT(DISTINCT tag_path) AS unique_tags,
    AVG((ingestion_us - UNIX_MICROS(event_ts)) / 1000.0) AS avg_latency_ms
FROM normalized
WHERE event_ts IS NOT NULL
  AND ingestion_us IS NOT NULL
  AND event_ts > CURRENT_TIMESTAMP - INTERVAL 10 MINUTES
GROUP BY DATE_TRUNC('minute', event_ts)
ORDER BY minute_bucket DESC;

-- Expected: ~3000 records/minute (50 tags x 60 seconds)

-- 8. CHECK DATA QUALITY
-- ------------------------------------------------------------------------------
SELECT
    tag_path,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN quality_code = 192 THEN 1 END) AS good_quality,
    COUNT(CASE WHEN quality_code != 192 THEN 1 END) AS bad_quality,
    ROUND(100.0 * COUNT(CASE WHEN quality_code = 192 THEN 1 END) / COUNT(*), 2) AS quality_pct
FROM field_engineering.ignition_streaming.sensor_events
GROUP BY tag_path
ORDER BY quality_pct ASC
LIMIT 50;

-- Expected: Mostly 100% good quality (quality_code = 192)

-- 9. DETECT NUMERIC ANOMALIES (OT event numeric stream)
-- ------------------------------------------------------------------------------
WITH stats AS (
    SELECT
        tag_path,
        AVG(numeric_value) AS avg_value,
        STDDEV(numeric_value) AS stddev_value
    FROM field_engineering.ignition_streaming.sensor_events
    WHERE event_time > CURRENT_TIMESTAMP - INTERVAL 1 HOUR
      AND numeric_value IS NOT NULL
    GROUP BY tag_path
),
recent AS (
    SELECT
        tag_path,
        numeric_value,
        event_time
    FROM field_engineering.ignition_streaming.sensor_events
    WHERE event_time > CURRENT_TIMESTAMP - INTERVAL 5 MINUTES
      AND numeric_value IS NOT NULL
)
SELECT
    r.tag_path,
    r.numeric_value AS current_value,
    s.avg_value AS hourly_avg,
    r.numeric_value - s.avg_value AS deviation,
    (r.numeric_value - s.avg_value) / NULLIF(s.stddev_value, 0) AS z_score,
    r.event_time
FROM recent r
JOIN stats s ON r.tag_path = s.tag_path
WHERE ABS((r.numeric_value - s.avg_value) / NULLIF(s.stddev_value, 0)) > 2
ORDER BY ABS((r.numeric_value - s.avg_value) / NULLIF(s.stddev_value, 0)) DESC
LIMIT 10;

-- Expected: Occasional anomalies from synthetic demo generators

-- 10. VIEW TAG TRENDS
-- ------------------------------------------------------------------------------
SELECT
    DATE_TRUNC('minute', event_time) AS minute_bucket,
    tag_path,
    AVG(numeric_value) AS avg_value,
    MIN(numeric_value) AS min_value,
    MAX(numeric_value) AS max_value,
    STDDEV(numeric_value) AS stddev_value
FROM field_engineering.ignition_streaming.sensor_events
WHERE event_time > CURRENT_TIMESTAMP - INTERVAL 30 MINUTES
  AND numeric_value IS NOT NULL
GROUP BY DATE_TRUNC('minute', event_time), tag_path
ORDER BY minute_bucket DESC, tag_path
LIMIT 50;

-- ==============================================================================
-- CLEANUP (use with caution - deletes all data)
-- ==============================================================================

-- Drop table (if you need to start over)
-- DROP TABLE IF EXISTS field_engineering.ignition_streaming.sensor_events;

-- Truncate table (delete data but keep structure)
-- DELETE FROM field_engineering.ignition_streaming.sensor_events;

-- ==============================================================================
-- NOTES
-- ==============================================================================

-- Zerobus Configuration (in Ignition Gateway):
--   Workspace URL: https://e2-demo-field-eng.cloud.databricks.com/
--   Zerobus Endpoint: 1444828305810485.zerobus.us-west-2.cloud.databricks.com
--   OAuth Client ID/Secret: service principal credentials
--   Target Table: field_engineering.ignition_streaming.sensor_events
--
-- Tag Configuration (in Ignition):
--   Tag Provider: Sample_Tags
--   Tag Folder Path: [Sample_Tags]Mining
--   Mode: Folder + include subfolders
--   Update Rate: 1 second
--
-- Expected Data:
--   Total Tags: ~50 (mining demo)
--   Update Frequency: ~50 records/second
--   Fields follow OTEvent protobuf contract
--
-- ==============================================================================
