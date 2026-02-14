-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Mining Operations Dimension Tables
-- MAGIC
-- MAGIC Supporting dimension tables for DLT pipeline enrichment.
-- MAGIC
-- MAGIC **Run this BEFORE deploying the DLT pipeline** - the pipeline expects these tables to exist.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1. Equipment Master Table

-- COMMAND ----------

-- Create or replace equipment master dimension
CREATE OR REPLACE TABLE field_engineering.mining_demo.equipment_master (
  equipment_id STRING NOT NULL COMMENT 'Unique equipment identifier',
  equipment_type STRING NOT NULL COMMENT 'Equipment category (Crusher, Conveyor, Stacker, etc.)',
  manufacturer STRING COMMENT 'Equipment manufacturer',
  model STRING COMMENT 'Equipment model number',
  location STRING COMMENT 'Physical location in mine site',
  criticality STRING COMMENT 'Operational criticality: Critical, High, Medium, Low',
  max_capacity DOUBLE COMMENT 'Maximum rated capacity (tonnes/hour)',
  installation_date DATE COMMENT 'Equipment installation date',
  last_maintenance_date DATE COMMENT 'Last scheduled maintenance',
  maintenance_interval_days INT COMMENT 'Days between maintenance',
  is_active BOOLEAN COMMENT 'Currently operational',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT equipment_pk PRIMARY KEY (equipment_id)
) COMMENT 'Master list of all mining equipment with metadata';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2. Populate Equipment Master Data

-- COMMAND ----------

-- Insert equipment data matching the Ignition UDT structure
INSERT INTO field_engineering.mining_demo.equipment_master VALUES
-- Crushers (Critical)
('CR_001', 'Crusher', 'Metso', 'C160', 'Primary Crushing Station', 'Critical', 800.0, '2020-03-15', '2024-01-10', 90, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('CR_002', 'Crusher', 'Metso', 'C160', 'Primary Crushing Station', 'Critical', 800.0, '2020-03-20', '2024-01-12', 90, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),

-- Conveyors (High priority)
('CV_001', 'Conveyor', 'ThyssenKrupp', 'BC-2400', 'Primary to Secondary', 'High', 1200.0, '2020-04-05', '2024-01-15', 60, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('CV_002', 'Conveyor', 'ThyssenKrupp', 'BC-2400', 'Secondary to Tertiary', 'High', 1200.0, '2020-04-08', '2024-01-17', 60, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('CV_003', 'Conveyor', 'ThyssenKrupp', 'BC-1800', 'Tertiary to Stockpile', 'High', 900.0, '2020-04-12', '2024-01-20', 60, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('CV_004', 'Conveyor', 'Continental', 'BC-1800', 'Stockpile to Port', 'High', 900.0, '2020-04-15', '2024-01-22', 60, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),

-- Stackers (Medium priority)
('ST_001', 'Stacker', 'TAKRAF', 'SR-5000', 'Stockpile Area A', 'Medium', 5000.0, '2020-05-20', '2024-01-25', 120, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('ST_002', 'Stacker', 'TAKRAF', 'SR-5000', 'Stockpile Area B', 'Medium', 5000.0, '2020-05-25', '2024-01-28', 120, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),

-- Reclaimers (Medium priority)
('RC_001', 'Reclaimer', 'TAKRAF', 'RR-4000', 'Stockpile Area A', 'Medium', 4000.0, '2020-06-10', '2024-02-01', 120, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('RC_002', 'Reclaimer', 'TAKRAF', 'RR-4000', 'Stockpile Area B', 'Medium', 4000.0, '2020-06-15', '2024-02-03', 120, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),

-- Ship Loaders (Critical - port operations)
('SL_001', 'ShipLoader', 'Vigan', 'SL-12000', 'Port Terminal 1', 'Critical', 12000.0, '2020-07-01', '2024-02-05', 90, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('SL_002', 'ShipLoader', 'Vigan', 'SL-12000', 'Port Terminal 2', 'Critical', 12000.0, '2020-07-10', '2024-02-07', 90, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),

-- Screens (Medium priority)
('SC_001', 'Screen', 'Terex', 'TS-2000', 'Secondary Screening', 'Medium', 600.0, '2020-08-01', '2024-02-10', 60, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('SC_002', 'Screen', 'Terex', 'TS-2000', 'Tertiary Screening', 'Medium', 600.0, '2020-08-05', '2024-02-12', 60, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),

-- Feeders (Low priority - auxiliary)
('FD_001', 'Feeder', 'Eriez', 'VF-800', 'Primary Feed Station', 'Low', 800.0, '2020-09-01', '2024-02-14', 30, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. Sensor Definitions Table

-- COMMAND ----------

-- Create sensor definitions (optional - for documentation)
CREATE OR REPLACE TABLE field_engineering.mining_demo.sensor_definitions (
  sensor_name STRING NOT NULL COMMENT 'Sensor tag name',
  sensor_type STRING COMMENT 'Type: Vibration, Temperature, Production, Speed, etc.',
  unit_of_measure STRING COMMENT 'Engineering units',
  normal_min DOUBLE COMMENT 'Normal operating range minimum',
  normal_max DOUBLE COMMENT 'Normal operating range maximum',
  alarm_low DOUBLE COMMENT 'Low alarm threshold',
  alarm_high DOUBLE COMMENT 'High alarm threshold',
  description STRING COMMENT 'Sensor description',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT sensor_pk PRIMARY KEY (sensor_name)
) COMMENT 'Sensor metadata and operating ranges';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Populate Sensor Definitions

-- COMMAND ----------

-- Insert common sensor definitions
INSERT INTO field_engineering.mining_demo.sensor_definitions VALUES
-- Vibration sensors (mm/s)
('Vibration_MM_S', 'Vibration', 'mm/s', 0.0, 10.0, -1.0, 12.0, 'Bearing vibration velocity', CURRENT_TIMESTAMP()),

-- Temperature sensors (Celsius)
('Bearing_Temperature_C', 'Temperature', '°C', 40.0, 75.0, 30.0, 85.0, 'Bearing housing temperature', CURRENT_TIMESTAMP()),
('Motor_Temperature_C', 'Temperature', '°C', 50.0, 80.0, 40.0, 90.0, 'Motor winding temperature', CURRENT_TIMESTAMP()),
('Ambient_Temperature_C', 'Temperature', '°C', 10.0, 40.0, -5.0, 50.0, 'Ambient air temperature', CURRENT_TIMESTAMP()),

-- Production sensors
('Production_Rate_TPH', 'Production', 't/h', 0.0, 1200.0, -10.0, 1500.0, 'Material throughput rate', CURRENT_TIMESTAMP()),
('Tonnage', 'Production', 'tonnes', 0.0, 100000.0, -10.0, 200000.0, 'Cumulative tonnage', CURRENT_TIMESTAMP()),

-- Speed sensors
('Belt_Speed_MPS', 'Speed', 'm/s', 0.0, 5.0, -0.5, 6.0, 'Conveyor belt speed', CURRENT_TIMESTAMP()),
('Motor_Speed_RPM', 'Speed', 'RPM', 0.0, 1800.0, -50.0, 2000.0, 'Motor shaft speed', CURRENT_TIMESTAMP()),

-- Power sensors
('Motor_Power_KW', 'Power', 'kW', 0.0, 500.0, -10.0, 600.0, 'Motor power consumption', CURRENT_TIMESTAMP()),
('Motor_Current_A', 'Power', 'A', 0.0, 200.0, -5.0, 250.0, 'Motor current draw', CURRENT_TIMESTAMP());

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 5. Location Hierarchy Table

-- COMMAND ----------

-- Create location hierarchy for reporting
CREATE OR REPLACE TABLE field_engineering.mining_demo.location_hierarchy (
  location_id STRING NOT NULL COMMENT 'Location identifier',
  location_name STRING COMMENT 'Location display name',
  location_type STRING COMMENT 'Type: Site, Area, Zone, Station',
  parent_location_id STRING COMMENT 'Parent location (for hierarchy)',
  latitude DOUBLE COMMENT 'GPS latitude',
  longitude DOUBLE COMMENT 'GPS longitude',
  timezone STRING COMMENT 'Local timezone',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT location_pk PRIMARY KEY (location_id)
) COMMENT 'Physical location hierarchy for equipment';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 6. Populate Location Hierarchy

-- COMMAND ----------

INSERT INTO field_engineering.mining_demo.location_hierarchy VALUES
-- Site level
('SITE_001', 'Mining Site Alpha', 'Site', NULL, -23.5505, 148.7800, 'Australia/Brisbane', CURRENT_TIMESTAMP()),

-- Area level
('AREA_CRUSHING', 'Crushing Plant Area', 'Area', 'SITE_001', -23.5510, 148.7810, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('AREA_CONVEYOR', 'Conveyor Transport Area', 'Area', 'SITE_001', -23.5515, 148.7820, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('AREA_STOCKPILE', 'Stockpile Management Area', 'Area', 'SITE_001', -23.5520, 148.7830, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('AREA_PORT', 'Port Loading Terminal', 'Area', 'SITE_001', -23.5525, 148.7840, 'Australia/Brisbane', CURRENT_TIMESTAMP()),

-- Station level (specific locations)
('Primary Crushing Station', 'Primary Crushing Station', 'Station', 'AREA_CRUSHING', -23.5512, 148.7812, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Primary to Secondary', 'Primary to Secondary Transfer', 'Station', 'AREA_CONVEYOR', -23.5516, 148.7822, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Secondary to Tertiary', 'Secondary to Tertiary Transfer', 'Station', 'AREA_CONVEYOR', -23.5518, 148.7826, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Tertiary to Stockpile', 'Tertiary to Stockpile Transfer', 'Station', 'AREA_CONVEYOR', -23.5519, 148.7828, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Stockpile to Port', 'Stockpile to Port Transfer', 'Station', 'AREA_CONVEYOR', -23.5521, 148.7832, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Stockpile Area A', 'Stockpile Area A', 'Station', 'AREA_STOCKPILE', -23.5522, 148.7834, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Stockpile Area B', 'Stockpile Area B', 'Station', 'AREA_STOCKPILE', -23.5523, 148.7836, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Port Terminal 1', 'Port Terminal 1', 'Station', 'AREA_PORT', -23.5526, 148.7842, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Port Terminal 2', 'Port Terminal 2', 'Station', 'AREA_PORT', -23.5527, 148.7844, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Secondary Screening', 'Secondary Screening Plant', 'Station', 'AREA_CRUSHING', -23.5513, 148.7814, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Tertiary Screening', 'Tertiary Screening Plant', 'Station', 'AREA_CRUSHING', -23.5514, 148.7816, 'Australia/Brisbane', CURRENT_TIMESTAMP()),
('Primary Feed Station', 'Primary Feed Station', 'Station', 'AREA_CRUSHING', -23.5511, 148.7811, 'Australia/Brisbane', CURRENT_TIMESTAMP());

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 7. Shift Schedule Table

-- COMMAND ----------

-- Create shift schedule for business context
CREATE OR REPLACE TABLE field_engineering.mining_demo.shift_schedule (
  shift_id STRING NOT NULL COMMENT 'Shift identifier',
  shift_name STRING COMMENT 'Shift display name',
  start_time TIME COMMENT 'Shift start time',
  end_time TIME COMMENT 'Shift end time',
  shift_type STRING COMMENT 'Day/Night/Swing',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT shift_pk PRIMARY KEY (shift_id)
) COMMENT 'Operational shift schedule for contextualized reporting';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 8. Populate Shift Schedule

-- COMMAND ----------

INSERT INTO field_engineering.mining_demo.shift_schedule VALUES
('SHIFT_DAY', 'Day Shift', '06:00:00', '14:00:00', 'Day', CURRENT_TIMESTAMP()),
('SHIFT_AFTERNOON', 'Afternoon Shift', '14:00:00', '22:00:00', 'Swing', CURRENT_TIMESTAMP()),
('SHIFT_NIGHT', 'Night Shift', '22:00:00', '06:00:00', 'Night', CURRENT_TIMESTAMP());

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 9. Validation Queries

-- COMMAND ----------

-- Verify equipment master data
SELECT
  equipment_type,
  criticality,
  COUNT(*) as equipment_count,
  AVG(max_capacity) as avg_capacity
FROM field_engineering.mining_demo.equipment_master
GROUP BY equipment_type, criticality
ORDER BY equipment_type, criticality;

-- COMMAND ----------

-- Verify sensor definitions
SELECT
  sensor_type,
  COUNT(*) as sensor_count,
  COLLECT_LIST(sensor_name) as sensors
FROM field_engineering.mining_demo.sensor_definitions
GROUP BY sensor_type
ORDER BY sensor_type;

-- COMMAND ----------

-- Verify location hierarchy
SELECT
  location_type,
  COUNT(*) as location_count
FROM field_engineering.mining_demo.location_hierarchy
GROUP BY location_type
ORDER BY
  CASE location_type
    WHEN 'Site' THEN 1
    WHEN 'Area' THEN 2
    WHEN 'Station' THEN 3
    ELSE 4
  END;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 10. Grant Permissions

-- COMMAND ----------

-- Grant read access to all users (adjust as needed)
GRANT SELECT ON TABLE field_engineering.mining_demo.equipment_master TO `account users`;
GRANT SELECT ON TABLE field_engineering.mining_demo.sensor_definitions TO `account users`;
GRANT SELECT ON TABLE field_engineering.mining_demo.location_hierarchy TO `account users`;
GRANT SELECT ON TABLE field_engineering.mining_demo.shift_schedule TO `account users`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Setup Complete
-- MAGIC
-- MAGIC Dimension tables created and populated:
-- MAGIC - `equipment_master` - 15 equipment assets
-- MAGIC - `sensor_definitions` - 10 sensor types
-- MAGIC - `location_hierarchy` - 16 locations
-- MAGIC - `shift_schedule` - 3 shifts
-- MAGIC
-- MAGIC Next step: Deploy DLT pipeline (mining_realtime_dlt.py)
