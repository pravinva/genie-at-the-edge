# Zerobus Streaming Diagnosis

**Date**: February 27, 2026
**Status**: Container shut down per user request

---

## What I Found

### ✅ Zerobus Module Status
- **Installed**: Yes ✅
- **Version**: 1.0.10
- **License**: Free
- **Module File**: `/usr/local/bin/ignition/user-lib/modules/zerobus-connector-1.0.10.modl`
- **JAR Files**: Present in `/usr/local/bin/ignition/data/jar-cache/com.example.ignition.zerobus/`

### ❓ Configuration Status
- **Config Database**: `/usr/local/bin/ignition/data/db/config.idb` exists
- **Zerobus Config Files**: No JSON configuration files found in expected locations
- **This suggests**: Zerobus was installed but **not configured**

### 🔍 Why Zerobus Wasn't Streaming

Based on the file structure analysis:

1. **Module is installed** but there's no evidence of:
   - Databricks connection configuration
   - Tag subscription setup
   - Active connection logs

2. **Missing Configuration**:
   - No Zerobus configuration JSON files
   - No logs showing connection attempts
   - No tag subscription settings

3. **What Was Needed**:
   - Configure Databricks connection in Gateway Config
   - Set up tag subscription for `[Sample_Tags]Mining/*`
   - Enable the connection

---

## Databricks Readiness

### ✅ All Databricks Infrastructure Ready

**Completed**:
- ✅ Catalog: `field_engineering`
- ✅ Schema: `field_engineering.mining_demo`
- ✅ Table: `zerobus_sensor_stream` (created via SQL)
- ✅ Warehouse: Running
- ✅ Historical data: 30 days populated
- ✅ SAP/MES context data: Populated

**Table Structure** (confirmed created):
```sql
field_engineering.mining_demo.zerobus_sensor_stream (
    equipment_id STRING,
    sensor_name STRING,
    sensor_value DOUBLE,
    units STRING,
    timestamp TIMESTAMP,
    quality INT,
    _ingestion_timestamp TIMESTAMP
)
```

---

## Ignition Readiness

### ✅ Tag Simulation Ready

**Tags Created**:
- Provider: `Sample_Tags`
- Path: `Mining/*`
- Total: 50 tags (10 equipment × 5 sensors)

**Timer Script**:
- Location: `ignition/tags/timer_script_mining_operations.py`
- Status: Fixed and working (simplified version)
- Update Frequency: 1 second
- Features: Shift patterns, noise, anomalies

---

## What Needs to Be Done Next

When you restart Ignition, you'll need to **configure Zerobus manually**:

### Step 1: Access Gateway Configuration
```
URL: http://localhost:8183/web/config
Login: admin / password
```

### Step 2: Navigate to Zerobus
```
Config → Modules → Zerobus → Configuration
```

### Step 3: Add Databricks Connection

**Connection Settings**:
```yaml
Connection Name: FieldEngineering
Description: Mining demo real-time streaming

Host: e2-demo-field-eng.cloud.databricks.com
HTTP Path: /sql/1.0/warehouses/<warehouse_id>
Token: <your_databricks_token>

Catalog: field_engineering
Schema: mining_demo
Table: zerobus_sensor_stream
```

**Get Warehouse ID**:
```bash
databricks warehouses list
# Use the ID of "⚡ Reyden Warehouse" or "Serverless Endpoint"
```

**Get Token**:
```bash
databricks auth token
# Copy the access_token value
```

### Step 4: Configure Tag Subscription

**Tag Group Settings**:
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

### Step 5: Test Connection
- Click **Test Connection** button
- Should show: "Connected ✅"

### Step 6: Start Streaming
- Enable the tag group
- Check Status page for:
  - Connection: Connected
  - Tags Subscribed: 50
  - Records Sent: Should increase

---

## Verification After Restart

### In Databricks SQL Editor

**Check for streaming data**:
```sql
SELECT
    equipment_id,
    sensor_name,
    sensor_value,
    timestamp,
    _ingestion_timestamp,
    DATEDIFF(SECOND, timestamp, _ingestion_timestamp) as latency_seconds
FROM field_engineering.mining_demo.zerobus_sensor_stream
ORDER BY _ingestion_timestamp DESC
LIMIT 20;
```

**Expected**: New records appearing every 1 second

---

## Container Commands

### Start Colima & Ignition
```bash
# Start Colima
colima start

# Start Ignition
cd /Users/pravin.varma/Documents/Demo/genie-at-the-edge/docker
docker-compose up -d

# Check status
docker ps | grep ignition
```

### Access Ignition
```bash
# Gateway Web Interface
open http://localhost:8183

# Designer Launcher
open http://localhost:8183/web/home
```

### Stop Containers
```bash
# Stop Ignition
cd /Users/pravin.varma/Documents/Demo/genie-at-the-edge/docker
docker-compose down

# Stop Colima
colima stop
```

---

## Summary

**Why Zerobus wasn't streaming**:
- Zerobus module was **installed** but **not configured**
- No Databricks connection setup found
- No tag subscription configured

**What's ready**:
- ✅ Databricks infrastructure complete
- ✅ Table created and ready
- ✅ Tags created in Ignition
- ✅ Timer script working
- ✅ All documentation prepared

**Next action**:
1. Restart Colima & Ignition
2. Configure Zerobus connection (see Step 3 above)
3. Enable tag subscription (see Step 4 above)
4. Verify streaming with SQL query (see Verification section)

---

## Reference Files

- **Complete Setup Guide**: `ZEROBUS_SETUP_COMPLETE.md`
- **SQL Statements**: `databricks/ZEROBUS_SETUP.sql`
- **Timer Script**: `ignition/tags/timer_script_mining_operations.py`
- **Tag Definitions**: `ignition/tags/mining_operations_tags.json`
- **Quick Start**: `ignition/tags/QUICK_START.md`

---

**Status**: Container stopped ✅
**Next**: Configure Zerobus after restart
