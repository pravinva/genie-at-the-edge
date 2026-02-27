-- Create correct Zerobus table that matches ot_event.proto
-- This matches Ignition's Zerobus connector schema exactly

USE CATALOG field_engineering;
USE SCHEMA mining_demo;

-- Create table with schema that EXACTLY matches ot_event.proto
CREATE TABLE IF NOT EXISTS zerobus_sensor_stream (
  event_id STRING COMMENT 'Unique event identifier',
  event_time TIMESTAMP COMMENT 'Event timestamp from Ignition',
  tag_path STRING COMMENT 'Full Ignition tag path',
  tag_provider STRING COMMENT 'Ignition tag provider name',
  numeric_value DOUBLE COMMENT 'Numeric tag value',
  string_value STRING COMMENT 'String tag value',
  boolean_value BOOLEAN COMMENT 'Boolean tag value',
  quality INT COMMENT 'Numeric quality code (192 = good)',
  quality_string STRING COMMENT 'Quality indicator (GOOD, BAD, UNCERTAIN)',
  source_system STRING COMMENT 'Source Ignition Gateway identifier',
  ingestion_timestamp TIMESTAMP COMMENT 'Time ingested into Databricks',
  data_type STRING COMMENT 'Original data type from Ignition',
  alarm_state STRING COMMENT 'Alarm state if applicable',
  alarm_priority INT COMMENT 'Alarm priority if applicable'
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Raw tag events from Ignition via Zerobus connector - matches ot_event.proto schema';

-- Verify schema
DESCRIBE EXTENDED zerobus_sensor_stream;

-- Show full table name for Zerobus config
SELECT 'field_engineering.mining_demo.zerobus_sensor_stream' AS zerobus_target_table;
