CREATE TABLE IF NOT EXISTS field_engineering.mining_demo.zerobus_sensor_stream (
    equipment_id STRING COMMENT 'Equipment identifier',
    sensor_name STRING COMMENT 'Sensor type',
    sensor_value DOUBLE COMMENT 'Sensor reading value',
    units STRING COMMENT 'Unit of measurement',
    timestamp TIMESTAMP COMMENT 'Sensor reading timestamp',
    quality INT COMMENT 'OPC quality code',
    _ingestion_timestamp TIMESTAMP COMMENT 'Ingestion timestamp'
)
USING DELTA
COMMENT 'Real-time sensor stream from Ignition via Zerobus';
