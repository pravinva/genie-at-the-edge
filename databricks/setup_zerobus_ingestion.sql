-- Databricks Setup for Zerobus Ingestion
-- Catalog: ignition-genie (already exists)
-- Schema: mining_ops (new)
-- Table: tag_events_raw (new)

-- Use the catalog
USE CATALOG `ignition-genie`;

-- Create schema
CREATE SCHEMA IF NOT EXISTS mining_ops
COMMENT 'Mining operations data from Ignition Gateway';

USE SCHEMA mining_ops;

-- Create raw tag events table (Zerobus target)
CREATE TABLE IF NOT EXISTS tag_events_raw (
  source_system_id STRING COMMENT 'Ignition Gateway identifier',
  tag_path STRING COMMENT 'Full tag path from Ignition',
  tag_name STRING COMMENT 'Tag name only',
  value VARIANT COMMENT 'Tag value (can be string, number, boolean)',
  quality STRING COMMENT 'Tag quality (Good, Bad, etc)',
  event_timestamp TIMESTAMP COMMENT 'Event time from Ignition',
  ingestion_timestamp TIMESTAMP COMMENT 'Time ingested into Databricks',
  ingestion_date DATE GENERATED ALWAYS AS (CAST(ingestion_timestamp AS DATE)) COMMENT 'Partition column'
)
USING DELTA
PARTITIONED BY (ingestion_date)
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Raw tag events from Ignition via Zerobus connector';

-- Grant permissions (if using service principal)
-- GRANT SELECT, MODIFY ON TABLE tag_events_raw TO `<service_principal>`;

-- Display table info
DESCRIBE EXTENDED tag_events_raw;

-- Show the full table name for Zerobus configuration
SELECT 'ignition-genie.mining_ops.tag_events_raw' AS zerobus_target_table;
