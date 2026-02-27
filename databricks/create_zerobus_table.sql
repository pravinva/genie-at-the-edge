-- Create the zerobus_sensor_stream table for Ignition streaming
-- Schema was already created: field_engineering.mining_demo

CREATE TABLE IF NOT EXISTS field_engineering.mining_demo.zerobus_sensor_stream (
    equipment_id STRING COMMENT 'Equipment identifier (e.g., HAUL-001, CRUSH-002)',
    sensor_name STRING COMMENT 'Sensor type (temperature, vibration, pressure, throughput, speed)',
    sensor_value DOUBLE COMMENT 'Sensor reading value',
    units STRING COMMENT 'Unit of measurement',
    timestamp TIMESTAMP COMMENT 'Sensor reading timestamp from Ignition',
    quality INT COMMENT 'OPC quality code (192 = good)',
    _ingestion_timestamp TIMESTAMP COMMENT 'Databricks ingestion timestamp'
)
USING DELTA
COMMENT 'Real-time sensor stream from Ignition via Zerobus connector'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- Verify table was created
DESCRIBE EXTENDED field_engineering.mining_demo.zerobus_sensor_stream;
