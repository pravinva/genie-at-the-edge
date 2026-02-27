# Zerobus Setup - Complete Guide

**Date**: February 27, 2026
**Status**: ✅ DATABRICKS READY FOR STREAMING

---

## 1. Databricks Setup (COMPLETED)

### Schema and Table Created

```sql
-- Schema already created
CREATE SCHEMA IF NOT EXISTS field_engineering.mining_demo
COMMENT 'Mining demo schema';

-- Table for Zerobus streaming
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
```

### Verify Table Exists

```sql
-- List tables in schema
SHOW TABLES IN field_engineering.mining_demo;

-- Describe table structure
DESCRIBE EXTENDED field_engineering.mining_demo.zerobus_sensor_stream;
```

---

## 2. Ignition Setup (NEXT STEPS)

### Step 1: Install Zerobus Module

1. **Download** the module:
   - From: https://github.com/pravinva/lakeflow-ignition-zerobus-connector
   - Or use pre-built: `module/Zerobus-unsigned.modl`

2. **Install** in Ignition:
   - Go to: **Gateway Config** (http://localhost:8183/web/config)
   - Navigate to: **Config** → **Modules**
   - Click: **Install or Upgrade a Module**
   - Upload: `Zerobus-unsigned.modl`
   - Restart Gateway if prompted

### Step 2: Configure Databricks Connection

1. **Go to Zerobus Configuration**:
   - Gateway Config → **Modules** → **Zerobus** → **Configuration**

2. **Add New Connection**:
   ```yaml
   Connection Name: FieldEngineering
   Description: Mining demo streaming to Databricks
   ```

3. **Databricks Settings**:
   ```yaml
   Host: e2-demo-field-eng.cloud.databricks.com
   HTTP Path: /sql/1.0/warehouses/<warehouse_id>
   Token: <your_databricks_token>
   ```

   **Get Warehouse ID**:
   ```bash
   databricks warehouses list
   # Copy the ID from the output
   ```

   **Get Token** (if needed):
   ```bash
   databricks auth token
   # Use the access_token value
   ```

4. **Unity Catalog Settings**:
   ```yaml
   Catalog: field_engineering
   Schema: mining_demo
   Table: zerobus_sensor_stream
   ```

5. **Test Connection**: Click **Test** button - should show "Connected"

### Step 3: Configure Tag Subscription

1. **In Zerobus Configuration** → **Tag Groups**:
   ```yaml
   Group Name: MiningOperations
   Enabled: ✅

   Tag Provider: Sample_Tags
   Tag Path: Mining/*

   Mode: On Change
   Deadband: 0.1
   Max Buffer Size: 1000

   Databricks Connection: FieldEngineering
   ```

2. **Save Configuration**

3. **Start Streaming**: Enable the tag group

---

## 3. Verification

### In Ignition

**Check Zerobus Status**:
- Gateway Config → **Status** → **Modules** → **Zerobus**
- Connection Status: **Connected** ✅
- Tags Subscribed: **50** (Mining/*)
- Records Sent: Should increase every second

**Check Gateway Logs**:
- Gateway Config → **Status** → **Diagnostics** → **Logs**
- Filter by: `zerobus`
- Should see: "Sent 50 tag changes to Databricks"

### In Databricks

**Query Recent Data**:
```sql
SELECT
    equipment_id,
    sensor_name,
    sensor_value,
    units,
    timestamp,
    _ingestion_timestamp,
    DATEDIFF(SECOND, timestamp, _ingestion_timestamp) as latency_seconds
FROM field_engineering.mining_demo.zerobus_sensor_stream
ORDER BY _ingestion_timestamp DESC
LIMIT 20;
```

**Expected Output**:
```
equipment_id  sensor_name  sensor_value  timestamp            _ingestion_timestamp  latency_seconds
HAUL-001      temperature  82.45         2026-02-27 01:30:15  2026-02-27 01:30:16   1
HAUL-001      vibration    3.21          2026-02-27 01:30:15  2026-02-27 01:30:16   1
HAUL-002      temperature  78.93         2026-02-27 01:30:15  2026-02-27 01:30:16   1
...
```

**Count Records Per Equipment**:
```sql
SELECT
    equipment_id,
    COUNT(*) as record_count,
    MIN(_ingestion_timestamp) as first_record,
    MAX(_ingestion_timestamp) as latest_record
FROM field_engineering.mining_demo.zerobus_sensor_stream
GROUP BY equipment_id
ORDER BY equipment_id;
```

**Monitor Streaming Rate**:
```sql
SELECT
    DATE_TRUNC('minute', _ingestion_timestamp) as minute,
    COUNT(*) as records_per_minute
FROM field_engineering.mining_demo.zerobus_sensor_stream
WHERE _ingestion_timestamp > CURRENT_TIMESTAMP - INTERVAL 10 MINUTES
GROUP BY minute
ORDER BY minute DESC;
```

**Expected**: ~3000 records/minute (50 tags × 1 update/second × 60 seconds)

---

## 4. Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│ IGNITION GATEWAY (localhost:8183)                       │
│                                                         │
│  Tag Provider: Sample_Tags                             │
│  Tag Path: Mining/<equipment>/<sensor>                 │
│                                                         │
│  ┌──────────────────────────────────┐                 │
│  │ Timer Script (Every 1 second)    │                 │
│  │ - Updates 50 tags                │                 │
│  │ - Shift patterns (day/night)     │                 │
│  │ - Equipment-specific baselines   │                 │
│  │ - 5% anomaly injection           │                 │
│  └──────────────────────────────────┘                 │
│                 ↓                                       │
│  ┌──────────────────────────────────┐                 │
│  │ Zerobus Connector                │                 │
│  │ - Subscribes to Mining/*         │                 │
│  │ - Captures tag changes           │                 │
│  │ - Batches updates                │                 │
│  └──────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────┘
                 ↓ HTTPS (Change Data Capture)
┌─────────────────────────────────────────────────────────┐
│ DATABRICKS (e2-demo-field-eng.cloud.databricks.com)    │
│                                                         │
│  ⚡ Warehouse: Reyden Warehouse                         │
│                                                         │
│  📊 Table: field_engineering.mining_demo               │
│            .zerobus_sensor_stream                      │
│                                                         │
│  Columns:                                              │
│  - equipment_id (STRING)                               │
│  - sensor_name (STRING)                                │
│  - sensor_value (DOUBLE)                               │
│  - units (STRING)                                      │
│  - timestamp (TIMESTAMP)                               │
│  - quality (INT)                                       │
│  - _ingestion_timestamp (TIMESTAMP)                    │
│                                                         │
│  Delta Lake Format: ACID + Time Travel                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow Details

### Tag Update Frequency
- **Timer Script**: 1 second interval
- **Tags Updated**: 50 tags (10 equipment × 5 sensors)
- **Update Rate**: 50 updates/second

### Zerobus Behavior
- **Mode**: On Change (only sends when value changes)
- **Expected Rate**: ~50 changes/second (since values update every second)
- **Batching**: Groups multiple changes into single HTTP request
- **Retry Logic**: Auto-retries failed sends with exponential backoff

### Expected Data Volume
- **Per Hour**: ~180,000 records (50 × 3600)
- **Per Day**: ~4.3 million records
- **Per Week**: ~30 million records

### Delta Lake Benefits
- **Compression**: Parquet format reduces storage by 70-80%
- **Auto-optimize**: Compaction runs automatically
- **Time Travel**: Query historical data (`SELECT * FROM table TIMESTAMP AS OF '2026-02-26'`)
- **ACID**: Concurrent reads/writes without corruption

---

## 6. Troubleshooting

### Zerobus Not Connecting

**Symptom**: Connection status shows "Disconnected"

**Checks**:
1. Verify Databricks token is valid:
   ```bash
   curl -H "Authorization: Bearer <token>" \
        https://e2-demo-field-eng.cloud.databricks.com/api/2.0/clusters/list
   ```

2. Verify warehouse ID is correct:
   ```bash
   databricks warehouses list
   ```

3. Check Ignition Gateway logs:
   ```
   Filter: zerobus
   Look for: Connection errors, authentication failures
   ```

**Solutions**:
- Regenerate Databricks token
- Verify HTTP path format: `/sql/1.0/warehouses/<id>` (no extra slashes)
- Ensure warehouse is **Running** (not Stopped)

### No Data Arriving

**Symptom**: Query returns 0 rows

**Checks**:
1. Verify timer script is running:
   ```
   Gateway Config → Status → Scripting → Gateway Timer Scripts
   Look for: MiningOperationsSimulator (Last Execution: < 2 seconds ago)
   ```

2. Verify tags are updating:
   ```
   Designer → Tag Browser → [Sample_Tags]Mining/HAUL-001/temperature
   Value should change every 1 second
   ```

3. Verify Zerobus is subscribed:
   ```
   Gateway Config → Modules → Zerobus → Status
   Tags Subscribed: 50
   ```

4. Check Zerobus logs:
   ```
   Gateway Logs → Filter: zerobus
   Should see: "Sent N tag changes"
   ```

**Solutions**:
- Enable timer script if disabled
- Set `[Sample_Tags]Mining/Config/SimEnabled` to `true`
- Restart Zerobus module
- Check Databricks warehouse is **Running**

### High Latency

**Symptom**: `latency_seconds > 5` in verification query

**Causes**:
- Warehouse is cold (first query after idle period)
- Network congestion
- Large batch size in Zerobus

**Solutions**:
- Use Serverless warehouse (auto-starts faster)
- Reduce Zerobus max buffer size to 500
- Check network connectivity between Ignition and Databricks

### Duplicate Records

**Symptom**: Same timestamp appears multiple times

**Causes**:
- Zerobus retry logic (expected and safe)
- Timer script running multiple times

**Solutions**:
- Use `DISTINCT` or `GROUP BY` in queries
- Add deduplication logic:
  ```sql
  SELECT DISTINCT * FROM (
      SELECT *, ROW_NUMBER() OVER (
          PARTITION BY equipment_id, sensor_name, timestamp
          ORDER BY _ingestion_timestamp DESC
      ) as rn
      FROM field_engineering.mining_demo.zerobus_sensor_stream
  ) WHERE rn = 1
  ```

---

## 7. Summary

✅ **Databricks Ready**:
- Schema: `field_engineering.mining_demo` ✅
- Table: `zerobus_sensor_stream` ✅
- Warehouse: Active and running ✅

✅ **Ignition Ready**:
- Tags: 50 tags under `[Sample_Tags]Mining` ✅
- Timer Script: Updating every 1 second ✅
- Tag Provider: Sample_Tags ✅

⏳ **Next Action**:
1. Install Zerobus module in Ignition
2. Configure connection to Databricks (use settings above)
3. Enable tag subscription for `Mining/*`
4. Verify data streaming with SQL queries

---

## 8. Quick Reference

| Component | Value |
|-----------|-------|
| **Databricks Host** | e2-demo-field-eng.cloud.databricks.com |
| **Catalog** | field_engineering |
| **Schema** | mining_demo |
| **Table** | zerobus_sensor_stream |
| **Tag Provider** | Sample_Tags |
| **Tag Path** | Mining/* |
| **Update Frequency** | 1 second |
| **Expected Rate** | 50 records/second |

---

**Status**: ✅ READY FOR ZEROBUS CONFIGURATION
**Next**: Configure Zerobus in Ignition Gateway (see Step 2 above)
