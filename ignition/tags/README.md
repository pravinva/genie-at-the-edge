# Ignition Tag Import and Simulation Setup

This directory contains tag definitions and simulation scripts for mining operations that match the historian data structure in Databricks.

## Files

- **mining_operations_tags.json** - Tag browser import file with 50 tags (10 equipment × 5 sensors)
- **timer_script_mining_operations.py** - Jython timer script to simulate realistic sensor values

## Tag Structure

Tags follow the format: `[default]Mining/<equipment_id>/<sensor_name>`

**Equipment**:
- HAUL-001 through HAUL-005 (Haul Trucks)
- CRUSH-001 through CRUSH-003 (Crushers)
- CONV-001, CONV-002 (Conveyors)

**Sensors** (per equipment):
- temperature (°C)
- vibration (mm/s)
- pressure (bar)
- throughput (TPH)
- speed (RPM)

**Total**: 50 tags with history enabled on all sensors

---

## Step 1: Access Ignition Gateway

```bash
# Ensure Colima is running
colima status

# Start Ignition container if not running
cd docker && docker-compose up -d
```

**Access Ignition Gateway**:
- Gateway: http://localhost:8183
- Designer Launcher: http://localhost:8183/web/home
- Username: `admin`
- Password: `password`

---

## Step 2: Import Tags into Tag Browser

### Option A: Import via Designer (Recommended)

1. **Launch Ignition Designer**:
   - Go to: http://localhost:8183/web/home
   - Click "Launch Designer"
   - Login with username `admin`, password `password`

2. **Import Tags**:
   - In Designer, go to: **Tag Browser** (left panel)
   - Right-click on **All Providers** → **Default** folder
   - Select: **Import Tags** → **From File**
   - Choose: `mining_operations_tags.json`
   - Click **Import**

3. **Verify Import**:
   - Expand: `[default]Mining`
   - You should see folders: `Config`, `HAUL-001`, `HAUL-002`, ..., `CONV-002`
   - Each equipment folder contains 5 sensor tags

### Option B: Import via Gateway Webpage

1. Go to: http://localhost:8183/web/config/tags.tageditor
2. Login with admin credentials
3. Select **Import/Export** → **Import**
4. Upload `mining_operations_tags.json`
5. Click **Import Tags**

---

## Step 3: Configure Tag Historian (Optional)

If you want tags to write to Lakebase historian:

1. **In Gateway Config** (http://localhost:8183/web/config):
   - Go to: **Tag Configuration** → **Tag Providers** → **default**
   - Under **Tag History**: Select history provider
   - Click **Save**

2. **For Lakebase Integration**:
   ```yaml
   Database Connection:
     Name: Lakebase_Historian
     Type: PostgreSQL
     URL: jdbc:postgresql://lakebase.databricks.com:5432/ignition_historian
     Username: token
     Password: <databricks_token>
   ```

---

## Step 4: Set Up Timer Script for Simulation

### Create Gateway Timer Script

1. **In Gateway Config**:
   - Go to: **Scripting** → **Gateway Event Scripts**
   - Or in Designer: **Project Browser** → **Gateway Events** → **Timer Scripts**

2. **Add New Timer Script**:
   - Name: `MiningOperationsSimulator`
   - Execution Mode: **Fixed Rate**
   - Execution Rate: `1000` (runs every 1 second)
   - Enabled: ✅

3. **Paste Script**:
   - Copy contents of `timer_script_mining_operations.py`
   - Paste into script editor
   - Click **Save**

### What the Script Does

The timer script simulates realistic mining operations:

**Realistic Patterns**:
- **Shift variations**: Higher production during day shift (8am-8pm), lower at night
- **Weekend reduction**: 70% production on Saturday/Sunday
- **Gaussian noise**: ±10% natural variation
- **Anomalies**: 5% chance of 1.3-1.5x spikes (matches historian data)

**Equipment-Specific Behavior**:
- Crushers run hotter than haul trucks
- Conveyors have lower temperatures and vibration
- Each equipment has unique baseline adjustments

**Sensor Ranges**:
- Temperature: 40-120°C
- Vibration: 0.5-10 mm/s
- Pressure: 1-10 bar
- Throughput: 500-1500 TPH
- Speed: 50-500 RPM

---

## Step 5: Verify Simulation

### In Designer Tag Browser

1. Expand `[default]Mining/HAUL-001`
2. Double-click any sensor tag (e.g., `temperature`)
3. You should see the value updating every 1 second
4. Values should vary realistically with noise

### In Gateway Tag Browser

1. Go to: http://localhost:8183/web/config/tags.tageditor
2. Navigate to: `Mining` → any equipment
3. Watch values update in real-time

---

## Step 6: Configure Zerobus for Streaming to Databricks

### Install Zerobus Module

1. Download from: https://github.com/pravinva/lakeflow-ignition-zerobus-connector
2. Or use pre-installed module in: `module/Zerobus-unsigned.modl`
3. Install via: **Config** → **Modules** → **Install or Upgrade a Module**

### Configure Zerobus Connector

1. **In Gateway Config**:
   - Go to: **Modules** → **Zerobus** → **Configuration**

2. **Add Databricks Connection**:
   ```yaml
   Connection Name: FieldEngineering
   Catalog: field_engineering
   Schema: mining_demo
   Table: zerobus_sensor_stream
   Host: <workspace-host>.cloud.databricks.com
   Token: <databricks_token>
   HTTP Path: /sql/1.0/warehouses/<warehouse_id>
   ```

3. **Configure Tag Groups**:
   - Tag Provider: `default`
   - Tag Path: `Mining/*`
   - Mode: `On Change` or `Periodic (1 second)`
   - Enabled: ✅

### Verify Streaming

After Zerobus is configured, verify data is flowing:

```sql
-- In Databricks SQL Editor
SELECT
    equipment_id,
    sensor_name,
    sensor_value,
    timestamp,
    _ingestion_timestamp
FROM field_engineering.mining_demo.zerobus_sensor_stream
ORDER BY _ingestion_timestamp DESC
LIMIT 20;
```

You should see new records arriving every 1 second!

---

## Step 7: Run Unified Query

Once tags are streaming, test the unified architecture:

```sql
-- Combine real-time Zerobus + 30-day historian baselines + SAP context
WITH realtime AS (
    SELECT
        equipment_id,
        sensor_name,
        AVG(sensor_value) as current_avg
    FROM field_engineering.mining_demo.zerobus_sensor_stream
    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL 10 MINUTES
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
    GROUP BY equipment_id, sensor_name
),
business AS (
    SELECT
        equipment_id,
        criticality_rating,
        SUM(quantity_on_hand) as spare_parts_available
    FROM field_engineering.mining_demo.sap_equipment_master e
    LEFT JOIN field_engineering.mining_demo.sap_spare_parts p USING (equipment_id)
    GROUP BY equipment_id, criticality_rating
)
SELECT
    r.equipment_id,
    r.sensor_name,
    r.current_avg as current_value,
    h.baseline_7d,
    r.current_avg - h.baseline_7d as deviation,
    (r.current_avg - h.baseline_7d) / NULLIF(h.stddev_7d, 0) as z_score,
    CASE
        WHEN ABS((r.current_avg - h.baseline_7d) / NULLIF(h.stddev_7d, 0)) > 2 THEN 'ANOMALY'
        ELSE 'NORMAL'
    END as status,
    b.criticality_rating,
    b.spare_parts_available
FROM realtime r
LEFT JOIN historical h USING (equipment_id, sensor_name)
LEFT JOIN business b USING (equipment_id)
WHERE h.baseline_7d IS NOT NULL
ORDER BY ABS((r.current_avg - h.baseline_7d) / NULLIF(h.stddev_7d, 0)) DESC
LIMIT 10;
```

**Expected Result**: Equipment with anomalies ranked by deviation!

---

## Troubleshooting

### Tags Not Updating

1. **Check Script Status**:
   - Gateway Config → **Status** → **Scripting**
   - Look for `MiningOperationsSimulator` in **Gateway Timer Scripts**
   - Check **Last Execution** timestamp

2. **Check Logs**:
   - Gateway Config → **Status** → **Diagnostics** → **Logs**
   - Filter by: `mining.simulator`
   - Should see: "Updated 50 tags successfully"

3. **Enable Simulation**:
   - Tag: `[default]Mining/Config/SimEnabled`
   - Value should be: `true`

### Zerobus Not Streaming

1. **Check Module Status**:
   - Gateway Config → **Modules**
   - Zerobus status should be: **Running**

2. **Check Connection**:
   - Modules → **Zerobus** → **Status**
   - Connection to Databricks should be: **Connected**

3. **Check Tag Subscriptions**:
   - Verify tag paths in Zerobus config match: `Mining/*`

### History Not Recording

1. **Check History Provider**:
   - Tag Browser → Right-click tag → **Edit Tag**
   - **Tag History** section:
     - History Enabled: ✅
     - Storage Provider: `default`

2. **Check Database Connection**:
   - Gateway Config → **Databases** → **Connections**
   - Test connection to Lakebase

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ IGNITION DESIGNER                                           │
│                                                             │
│ 1. Import mining_operations_tags.json                      │
│    → Creates 50 tags: Mining/<equipment>/<sensor>          │
│                                                             │
│ 2. Gateway Timer Script runs every 1 second                │
│    → Updates all 50 tag values with simulation             │
│                                                             │
│ 3. Tag Historian writes to Lakebase (optional)             │
│    → lakebase.ignition_historian.sqlt_data_1_2024_02      │
│                                                             │
│ 4. Zerobus streams tag changes to Databricks               │
│    → field_engineering.mining_demo.zerobus_sensor_stream  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ DATABRICKS (Field Engineering Workspace)                    │
│                                                             │
│ 5. Unified query combines three sources:                   │
│    • Lakebase Historian (30-day baselines)                │
│    • Zerobus Streaming (current values)                   │
│    • SAP/MES Context (business data)                      │
│                                                             │
│ 6. ML detects anomalies: deviation > 2× std dev           │
│                                                             │
│ 7. Recommendations → agentic_hmi.agent_recommendations     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

✅ **Tags**: 50 tags matching historian structure (equipment_id/sensor_name)
✅ **Simulation**: Realistic patterns with shift variations, noise, and anomalies
✅ **Historian**: Optional Lakebase integration for time-series storage
✅ **Streaming**: Zerobus ready to stream to `zerobus_sensor_stream` table
✅ **Unified Queries**: Real-time + historical + business context in one SQL

**Next Steps**:
1. Import tags into Ignition Designer
2. Set up timer script in Gateway
3. Configure Zerobus for streaming
4. Watch unified queries come alive!

---

**Reference Files**:
- Zerobus Examples: `/tmp/zerobus-connector/examples/`
- Deployment Docs: `READY_FOR_IGNITION.md`
- Test Queries: `databricks/test_unified_query.sql`
