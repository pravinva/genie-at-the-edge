-- ============================================================================
-- RUN THIS ENTIRE SCRIPT IN DATABRICKS SQL EDITOR
-- Warehouse: 4b9b953939869799 (or any running warehouse)
-- ============================================================================

-- Step 1: Create catalog (if doesn't exist)
CREATE CATALOG IF NOT EXISTS ignition_genie
COMMENT 'Ignition Gateway data for Genie at the Edge demo';

-- Step 2: Create schema
CREATE SCHEMA IF NOT EXISTS ignition_genie.mining_ops
COMMENT 'Mining operations data from Ignition Gateway';

-- Step 3: Drop old table (if exists with wrong schema)
DROP TABLE IF EXISTS ignition_genie.mining_ops.tag_events_raw;

-- Step 4: Create table with EXACT Zerobus schema (matches ot_event.proto)
CREATE TABLE ignition_genie.mining_ops.tag_events_raw (
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
  ingestion_timestamp TIMESTAMP,
  data_type STRING,
  alarm_state STRING,
  alarm_priority INT
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Step 5: Grant permissions to all account users
GRANT USE CATALOG ON CATALOG ignition_genie TO `account users`;
GRANT USE SCHEMA ON SCHEMA ignition_genie.mining_ops TO `account users`;
GRANT SELECT, MODIFY ON TABLE ignition_genie.mining_ops.tag_events_raw TO `account users`;

-- Step 6: Verify table schema
DESCRIBE EXTENDED ignition_genie.mining_ops.tag_events_raw;

-- Step 7: Show row count (should be 0 initially)
SELECT COUNT(*) as row_count FROM ignition_genie.mining_ops.tag_events_raw;

-- ============================================================================
-- AFTER RUNNING THIS SCRIPT:
-- 1. Update Zerobus module config in Ignition:
--    http://localhost:8183/system/zerobus/configure
--
--    Target Table: ignition_genie.mining_ops.tag_events_raw
--    Zerobus Endpoint: 1444828305810485.zerobus.us-west-2.cloud.databricks.com
--
-- 2. Check diagnostics:
--    curl http://localhost:8183/system/zerobus/diagnostics
--
--    Look for:
--    - Initialized: true
--    - Connected: true
--    - Total Events Sent: increasing
--
-- 3. Query data after a few seconds:
--    SELECT * FROM ignition_genie.mining_ops.tag_events_raw LIMIT 100;
-- ============================================================================
