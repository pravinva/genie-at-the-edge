# Ignition Setup Complete

**Date**: February 27, 2026
**Status**: ✅ READY FOR TAG IMPORT

---

## What's Ready

### ✅ Colima/Docker
- **Status**: Running and healthy
- **Ignition Container**: `genie-at-edge-ignition` (Up 6 days)
- **Gateway Access**: http://localhost:8183
- **Designer Launcher**: http://localhost:8183/web/home

### ✅ Tag Definition Files
- **Location**: `ignition/tags/`
- **Files Created**:
  1. `mining_operations_tags.json` - 50 tags for import into Tag Browser
  2. `timer_script_mining_operations.py` - Simulation script (Jython)
  3. `README.md` - Complete setup instructions

### ✅ Tag Structure (Matches Historian)

**Format**: `[default]Mining/<equipment_id>/<sensor_name>`

**Equipment** (10 total):
- HAUL-001, HAUL-002, HAUL-003, HAUL-004, HAUL-005 (Haul Trucks)
- CRUSH-001, CRUSH-002, CRUSH-003 (Crushers)
- CONV-001, CONV-002 (Conveyors)

**Sensors** (5 per equipment):
- temperature
- vibration
- pressure
- throughput
- speed

**Total Tags**: 50 (10 equipment × 5 sensors)

**History**: All tags have `historyEnabled: true`

---

## Next Steps to Complete Integration

### Step 1: Import Tags (5 minutes)

```
1. Open Ignition Designer
   URL: http://localhost:8183/web/home
   Login: admin / password

2. Tag Browser → Right-click [default] folder
   → Import Tags → From File
   → Select: ignition/tags/mining_operations_tags.json

3. Verify: You should see Mining/ folder with all equipment
```

### Step 2: Set Up Timer Script (5 minutes)

```
1. In Designer or Gateway Config
   → Gateway Event Scripts → Timer Scripts

2. Add New Timer Script:
   Name: MiningOperationsSimulator
   Rate: 1000 ms (1 second)
   Enabled: ✅

3. Copy/paste contents of:
   ignition/tags/timer_script_mining_operations.py

4. Save and enable
```

### Step 3: Configure Zerobus (10 minutes)

```
1. Install Zerobus module (if not already installed)
   Source: https://github.com/pravinva/lakeflow-ignition-zerobus-connector

2. Configure connection to Databricks:
   Catalog: field_engineering
   Schema: mining_demo
   Table: zerobus_sensor_stream

3. Set tag subscription:
   Tag Path: Mining/*
   Mode: On Change / Periodic
```

### Step 4: Verify Data Flow (2 minutes)

```sql
-- In Databricks SQL Editor
SELECT
    equipment_id,
    sensor_name,
    sensor_value,
    timestamp
FROM field_engineering.mining_demo.zerobus_sensor_stream
ORDER BY _ingestion_timestamp DESC
LIMIT 20;
```

Expected: New records arriving every 1 second!

---

## Simulation Details

### Realistic Patterns

**Shift Multipliers**:
- Day shift (8am-8pm): 1.2× production
- Night shift (8pm-8am): 0.8× production

**Weekend**: 0.7× production on Sat/Sun

**Noise**: ±10% Gaussian variation

**Anomalies**: 5% chance of 1.3-1.5× spikes (matches historian data)

### Equipment-Specific Baselines

| Equipment | Temperature | Vibration | Pressure | Throughput | Speed |
|-----------|-------------|-----------|----------|------------|-------|
| HAUL-001  | 75°C        | 3.0 mm/s  | 3.5 bar  | 1000 TPH   | 100 RPM |
| HAUL-002  | 73°C        | 2.8 mm/s  | 3.6 bar  | 950 TPH    | 105 RPM |
| CRUSH-001 | 85°C        | 4.5 mm/s  | 5.2 bar  | 1200 TPH   | 450 RPM |
| CONV-001  | 55°C        | 2.5 mm/s  | 3.0 bar  | 980 TPH    | 100 RPM |

*All values vary with noise, shift patterns, and occasional anomalies*

---

## Data Flow Architecture

```
┌──────────────────────────────────────────────────────────┐
│ IGNITION (localhost:8183)                                │
│                                                          │
│  50 Tags: Mining/<equipment>/<sensor>                   │
│  Timer Script: Updates values every 1 second            │
│  Zerobus: Streams changes to Databricks                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
                        ↓ (Zerobus CDC)
┌──────────────────────────────────────────────────────────┐
│ DATABRICKS (Field Engineering Workspace)                 │
│                                                          │
│  Real-time Stream:                                       │
│  → field_engineering.mining_demo.zerobus_sensor_stream  │
│                                                          │
│  Historical Baseline (30 days):                         │
│  → lakebase.ignition_historian.sqlt_data_1_2024_02     │
│                                                          │
│  Business Context:                                       │
│  → field_engineering.mining_demo.sap_equipment_master   │
│  → field_engineering.mining_demo.sap_maintenance_schedule│
│  → field_engineering.mining_demo.sap_spare_parts        │
│                                                          │
│  Unified Query: All sources in ONE SQL statement!       │
│  → Detects anomalies by comparing current vs baseline   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## File Locations

### Tag Files
```
ignition/tags/
├── mining_operations_tags.json          ← Import this into Tag Browser
├── timer_script_mining_operations.py    ← Copy to Gateway Timer Script
└── README.md                             ← Complete setup guide
```

### Databricks Setup
```
databricks/
├── execute_setup.py                      ✅ Already executed
├── populate_data.py                      ✅ Already executed
├── test_unified_query.sql                ← Test queries
└── unified_data_architecture.py          ← DLT pipeline (optional)
```

### Documentation
```
DEPLOYMENT_COMPLETE.md                    ← Databricks deployment summary
READY_FOR_IGNITION.md                     ← Integration guide
IGNITION_SETUP_COMPLETE.md               ← This file
```

---

## Login Credentials

**Ignition Gateway**:
- URL: http://localhost:8183
- Username: `admin`
- Password: `password`

**Databricks**:
- Workspace: e2-demo-field-eng.cloud.databricks.com
- Authentication: Standard Databricks CLI auth

---

## Example Tag Paths

After import, tags will be at:

```
[default]Mining/
├── Config/
│   ├── SimEnabled (Boolean)
│   └── UpdateEveryMs (Int4)
├── HAUL-001/
│   ├── temperature (Float4, history enabled)
│   ├── vibration (Float4, history enabled)
│   ├── pressure (Float4, history enabled)
│   ├── throughput (Float4, history enabled)
│   └── speed (Float4, history enabled)
├── HAUL-002/
│   └── (same 5 sensors)
...
└── CONV-002/
    └── (same 5 sensors)
```

**Tag Path Format**: `[default]Mining/HAUL-001/temperature`

This matches the historian tagpath: `HAUL-001/temperature`

---

## Verification Checklist

After setup, verify each component:

### ✅ Tag Import
- [ ] Tags visible in Tag Browser under `[default]Mining`
- [ ] Each equipment folder has 5 sensor tags
- [ ] Total 50 tags (excluding Config folder)

### ✅ Simulation Running
- [ ] Timer script enabled in Gateway Events
- [ ] Tag values updating every 1 second
- [ ] Check Gateway logs for "Updated 50 tags successfully"

### ✅ Zerobus Streaming
- [ ] Zerobus module installed and running
- [ ] Connection to Databricks: Connected
- [ ] Query shows new records in `zerobus_sensor_stream`

### ✅ Unified Query Works
- [ ] Run test query from `databricks/test_unified_query.sql`
- [ ] Results show real-time values + historical baselines
- [ ] Anomalies detected (z_score > 2)

---

## Troubleshooting

### Tags Not Updating

**Check**: Gateway → Status → Diagnostics → Logs
**Filter**: `mining.simulator`
**Expected**: "Updated 50 tags successfully"

**If not**:
1. Verify timer script is enabled
2. Check `[default]Mining/Config/SimEnabled` = true
3. Check for script errors in logs

### Zerobus Not Streaming

**Check**: Modules → Zerobus → Status
**Expected**: Connection = Connected

**If not**:
1. Verify Databricks token is valid
2. Check network connectivity to Databricks
3. Verify warehouse ID in HTTP path

### Unified Query Returns No Rows

**Possible causes**:
1. Zerobus hasn't started streaming yet (wait 10 seconds)
2. Time filters too restrictive (adjust INTERVAL values)
3. Tag paths don't match historian data (verify SPLIT() logic)

---

## Support Files

- **Zerobus Examples**: `/tmp/zerobus-connector/examples/`
- **Setup Guide**: `ignition/tags/README.md`
- **Databricks Deployment**: `DEPLOYMENT_COMPLETE.md`
- **Integration Guide**: `READY_FOR_IGNITION.md`

---

## Summary

✅ **Colima**: Running
✅ **Ignition**: Healthy and accessible at http://localhost:8183
✅ **Tags**: 50 tags ready for import (matches historian structure)
✅ **Simulation**: Timer script ready (realistic patterns with anomalies)
✅ **Databricks**: Field Engineering workspace fully deployed with 30 days of data
✅ **Streaming**: Zerobus-compatible structure ready

**You are now ready to**:
1. Import `mining_operations_tags.json` into Ignition Designer
2. Set up the timer script to start simulation
3. Configure Zerobus to stream to Databricks
4. Run unified queries combining all three data sources!

---

**Status**: ✅ READY FOR IGNITION INTEGRATION
**Next Action**: Import tags and set up timer script (see Step 1 above)
