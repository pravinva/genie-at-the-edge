-- Correct Zerobus Table Schema (matches ot_event.proto)
-- Catalog: ignition-genie
-- Schema: mining_ops
-- Table: tag_events_raw

USE CATALOG `ignition-genie`;

CREATE SCHEMA IF NOT EXISTS mining_ops
COMMENT 'Mining operations data from Ignition Gateway';

USE SCHEMA mining_ops;

-- Drop old table if it exists with wrong schema
DROP TABLE IF EXISTS tag_events_raw;

-- Create table with schema that EXACTLY matches ot_event.proto
CREATE TABLE tag_events_raw (
  event_id STRING COMMENT 'Unique event identifier',
  event_time TIMESTAMP COMMENT 'Event timestamp from Ignition',
  tag_path STRING COMMENT 'Full Ignition tag path',
  tag_provider STRING COMMENT 'Ignition tag provider name',
  numeric_value DOUBLE COMMENT 'Numeric tag value',
  string_value STRING COMMENT 'String tag value',
  boolean_value BOOLEAN COMMENT 'Boolean tag value',
  quality STRING COMMENT 'Quality indicator (GOOD, BAD, UNCERTAIN)',
  quality_code INT COMMENT 'Numeric quality code',
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
COMMENT 'Raw tag events from Ignition via Zerobus connector';

-- Verify schema
DESCRIBE EXTENDED tag_events_raw;

-- Show full table name for Zerobus config
SELECT 'ignition-genie.mining_ops.tag_events_raw' AS zerobus_target_table;
