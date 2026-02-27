# Field Engineering Workspace Setup Guide

## Quick Start

```bash
# Run the complete setup
databricks workspace import \
  databricks/setup_field_eng_workspace.py \
  /Users/pravin.varma@databricks.com/genie-at-edge/setup_field_eng_workspace.py

# Execute in Databricks notebook
%run /Users/pravin.varma@databricks.com/genie-at-edge/setup_field_eng_workspace.py
```

## What Gets Created

### Catalogs & Schemas
```
field_engineering                    (Main Analytics)
├── mining_demo                      (Mining operations data)
│   ├── zerobus_sensor_stream       (Real-time streaming)
│   ├── sap_equipment_master        (Equipment business data)
│   ├── sap_maintenance_schedule    (Maintenance planning)
│   ├── sap_spare_parts            (Inventory)
│   └── mes_production_schedule    (Production planning)

lakebase                            (PostgreSQL-compatible)
├── ignition_historian              (Tag Historian data)
│   ├── sqlth_te                   (Tag metadata - 50 tags)
│   ├── sqlt_data_1_2024_02        (Historian data - 30 days)
│   └── sqlth_partitions           (Partition tracking)
│
└── agentic_hmi                     (Agent operations)
    ├── agent_recommendations       (ML recommendations)
    └── agent_commands              (Command tracking)
```

### Data Volumes
- **Historian**: 30 days × 50 tags × 60 samples/hour = ~2.16M records
- **Zerobus**: 1 hour × 15 tags × 360 samples = ~5,400 records (refreshed)
- **SAP/MES**: ~100 reference records

## Connection Details

### For Ignition Gateway
```yaml
Database Connection:
  Name: Lakebase_Historian
  Type: PostgreSQL
  URL: jdbc:postgresql://lakebase.databricks.com:5432/ignition_historian
  Username: token
  Password: <your_databricks_pat>

Tag Historian Provider:
  Storage: Lakebase_Historian
  Table Prefix: sqlt_
  Partition: Monthly
```

### For DLT Pipeline
```python
# Historian (already in Databricks!)
historian = spark.sql("""
    SELECT * FROM lakebase.ignition_historian.sqlt_data_1_2024_02
""")

# Real-time streaming
realtime = spark.readStream.table("field_engineering.mining_demo.zerobus_sensor_stream")

# SAP context
sap = spark.table("field_engineering.mining_demo.sap_equipment_master")
```

## Sample Queries

### 1. Check Historian Data
```sql
SELECT
    t.tagpath,
    COUNT(*) as sample_count,
    MIN(d.t_stamp) as oldest,
    MAX(d.t_stamp) as newest,
    AVG(d.floatvalue) as avg_value
FROM lakebase.ignition_historian.sqlt_data_1_2024_02 d
JOIN lakebase.ignition_historian.sqlth_te t ON d.tagid = t.id
GROUP BY t.tagpath
ORDER BY tagpath;
```

### 2. Current Streaming Data
```sql
SELECT
    equipment_id,
    sensor_name,
    sensor_value,
    timestamp,
    DATEDIFF(SECOND, timestamp, CURRENT_TIMESTAMP()) as lag_seconds
FROM field_engineering.mining_demo.zerobus_sensor_stream
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL 10 MINUTES
ORDER BY timestamp DESC;
```

### 3. Unified View (All Three Sources)
```sql
WITH realtime AS (
    SELECT
        equipment_id,
        sensor_name,
        AVG(sensor_value) as current_avg
    FROM field_engineering.mining_demo.zerobus_sensor_stream
    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL 5 MINUTES
    GROUP BY equipment_id, sensor_name
),
historical AS (
    SELECT
        SPLIT(t.tagpath, '/')[0] as equipment_id,
        SPLIT(t.tagpath, '/')[1] as sensor_name,
        AVG(d.floatvalue) as baseline_7d,
        STDDEV(d.floatvalue) as stddev_7d
    FROM lakebase.ignition_historian.sqlt_data_1_2024_02 d
    JOIN lakebase.ignition_historian.sqlth_te t ON d.tagid = t.id
    WHERE d.t_stamp > CURRENT_TIMESTAMP - INTERVAL 7 DAYS
    GROUP BY SPLIT(t.tagpath, '/')[0], SPLIT(t.tagpath, '/')[1]
),
business AS (
    SELECT
        e.equipment_id,
        e.criticality_rating,
        m.next_scheduled_maintenance,
        SUM(p.quantity_on_hand) as spare_parts_available
    FROM field_engineering.mining_demo.sap_equipment_master e
    LEFT JOIN field_engineering.mining_demo.sap_maintenance_schedule m
        ON e.equipment_id = m.equipment_id
    LEFT JOIN field_engineering.mining_demo.sap_spare_parts p
        ON e.equipment_id = p.equipment_id
    GROUP BY e.equipment_id, e.criticality_rating, m.next_scheduled_maintenance
)
SELECT
    r.equipment_id,
    r.sensor_name,
    r.current_avg,
    h.baseline_7d,
    r.current_avg - h.baseline_7d as deviation,
    (r.current_avg - h.baseline_7d) / h.stddev_7d as z_score,
    b.criticality_rating,
    CASE
        WHEN ABS((r.current_avg - h.baseline_7d) / h.stddev_7d) > 2 THEN 'ANOMALY'
        ELSE 'NORMAL'
    END as status,
    b.spare_parts_available,
    DATEDIFF(DAY, CURRENT_DATE(), b.next_scheduled_maintenance) as days_to_maintenance
FROM realtime r
LEFT JOIN historical h
    ON r.equipment_id = h.equipment_id AND r.sensor_name = h.sensor_name
LEFT JOIN business b
    ON r.equipment_id = b.equipment_id
WHERE h.baseline_7d IS NOT NULL
ORDER BY ABS((r.current_avg - h.baseline_7d) / h.stddev_7d) DESC;
```

## Next Steps

### 1. Deploy DLT Pipeline
```bash
# Create unified pipeline
databricks workspace import \
  databricks/unified_data_architecture.py \
  /Users/pravin.varma@databricks.com/genie-at-edge/unified_pipeline.py

# Create DLT pipeline via UI:
# - Add notebook: unified_pipeline.py
# - Target: field_engineering.mining_demo
# - Mode: Continuous
# - Photon: Enabled
```

### 2. Set Up PostgreSQL NOTIFY
```sql
-- Execute in Lakebase SQL editor
-- This enables event-driven notifications
\i databricks/lakebase_notify_trigger.sql
```

### 3. Configure Ignition
```yaml
# In Ignition Gateway Config
1. Add Lakebase database connection
2. Configure Tag Historian to use Lakebase
3. Enable Zerobus for real-time streaming
4. Install gateway scripts for NOTIFY listener
```

### 4. Test End-to-End
```python
# Insert test anomaly
spark.sql("""
    INSERT INTO field_engineering.mining_demo.zerobus_sensor_stream
    VALUES (
        'HAUL-001',
        'temperature',
        95.5,  -- Anomaly!
        '°C',
        CURRENT_TIMESTAMP(),
        192,
        CURRENT_TIMESTAMP()
    )
""")

# Check if recommendation generated
spark.sql("""
    SELECT * FROM lakebase.agentic_hmi.agent_recommendations
    WHERE created_timestamp > CURRENT_TIMESTAMP - INTERVAL 1 MINUTE
""").show()
```

## Troubleshooting

### No Historian Data?
```sql
-- Check if tags exist
SELECT COUNT(*) FROM lakebase.ignition_historian.sqlth_te;

-- Check if data exists
SELECT COUNT(*) FROM lakebase.ignition_historian.sqlt_data_1_2024_02;

-- Check date range
SELECT MIN(t_stamp), MAX(t_stamp)
FROM lakebase.ignition_historian.sqlt_data_1_2024_02;
```

### Streaming Not Working?
```sql
-- Check for recent data
SELECT MAX(timestamp) as latest
FROM field_engineering.mining_demo.zerobus_sensor_stream;

-- Should be within last hour
```

### SAP Data Missing?
```sql
-- Verify all SAP tables
SELECT 'equipment' as table, COUNT(*) as rows
FROM field_engineering.mining_demo.sap_equipment_master
UNION ALL
SELECT 'maintenance', COUNT(*)
FROM field_engineering.mining_demo.sap_maintenance_schedule
UNION ALL
SELECT 'parts', COUNT(*)
FROM field_engineering.mining_demo.sap_spare_parts;
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│         FIELD ENGINEERING WORKSPACE             │
├────────────────────┬────────────────────────────┤
│                    │                            │
│  LAKEBASE          │  MAIN CATALOG              │
│  (PostgreSQL)      │  (Analytics)               │
│                    │                            │
│  ┌──────────────┐  │  ┌──────────────────────┐  │
│  │  Historian   │  │  │  Zerobus Streaming   │  │
│  │  30 days     │  │  │  Real-time           │  │
│  │  2.16M rows  │  │  │  5.4K rows/hour      │  │
│  └──────┬───────┘  │  └─────────┬────────────┘  │
│         │          │            │                │
│  ┌──────────────┐  │  ┌──────────────────────┐  │
│  │  Agent Recs  │  │  │  SAP/MES Context     │  │
│  │  Lakebase    │  │  │  Business Data       │  │
│  └──────────────┘  │  └──────────────────────┘  │
│                    │                            │
└────────────────────┴────────────────────────────┘
                     │
                     ↓
         ┌──────────────────────┐
         │  UNIFIED SILVER      │
         │  (DLT Pipeline)      │
         └──────────────────────┘
                     │
                     ↓
         ┌──────────────────────┐
         │  ML RECOMMENDATIONS  │
         │  (Gold Layer)        │
         └──────────────────────┘
```

## Performance Expectations

| Query Type | Expected Latency | Notes |
|-----------|-----------------|-------|
| Historian lookup | < 500ms | Indexed on tagid + t_stamp |
| Real-time stream | < 100ms | Streaming query with watermark |
| SAP lookup | < 100ms | Small dimension tables, cached |
| Unified query | < 1 sec | All three sources joined |
| ML prediction | < 2 sec | Including feature extraction |

## Monitoring

```sql
-- Pipeline health check
CREATE OR REPLACE VIEW field_engineering.mining_demo.system_health AS
SELECT
    'Historian' as component,
    COUNT(*) as total_records,
    MAX(t_stamp) as latest_data,
    DATEDIFF(SECOND, MAX(t_stamp), CURRENT_TIMESTAMP()) as lag_seconds
FROM lakebase.ignition_historian.sqlt_data_1_2024_02
UNION ALL
SELECT
    'Streaming',
    COUNT(*),
    MAX(timestamp),
    DATEDIFF(SECOND, MAX(timestamp), CURRENT_TIMESTAMP())
FROM field_engineering.mining_demo.zerobus_sensor_stream
UNION ALL
SELECT
    'SAP',
    COUNT(*),
    CURRENT_TIMESTAMP(),
    0
FROM field_engineering.mining_demo.sap_equipment_master;

-- Run health check
SELECT * FROM field_engineering.mining_demo.system_health;
```

---

**Setup completed!** You now have a complete unified data architecture with Lakebase Historian, Zerobus streaming, and SAP/MES context all queryable in one place.