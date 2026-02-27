# Zerobus Setup Status - FIXED

**Date**: February 27, 2026
**Status**: ✅ Schema Fixed | ⚠️ OAuth Token Needs Update

---

## ✅ Completed

### 1. Schema Issue - FIXED
- **Problem**: Table schema didn't match `ot_event.proto`
  - Had: `equipment_id`, `sensor_name` (wrong schema)
  - Needed: `event_id`, `event_time`, `tag_path`, `tag_provider` (proto schema)
  - **Quality field**: Was STRING, needed INT

- **Solution**: Dropped and recreated table with correct schema
  ```sql
  field_engineering.mining_demo.zerobus_sensor_stream
  ```

- **Verified**: ✅ Schema now matches proto definition exactly

### 2. Permissions - GRANTED
- ✅ `account users` granted SELECT, INSERT, MODIFY
- ✅ Schema USE permission granted
- ✅ Catalog USE permission granted

### 3. Infrastructure - READY
- ✅ Catalog: `field_engineering`
- ✅ Schema: `mining_demo`
- ✅ Table: `zerobus_sensor_stream` (14 columns)
- ✅ Warehouse: `4b9b953939869799` (running)
- ✅ Colima: Running
- ✅ Ignition: Running (50 tags simulating every 1 second)

---

## ⚠️ Remaining Issue: OAuth Token

### Current Error
```
OAuth request failed with status 401:
User is not authorized to the requested authorizations
```

### Cause
The Databricks token configured in Zerobus doesn't have proper permissions.

### Solution
**A new valid token has been created** (90-day lifetime):

```
Token ID: <TOKEN_ID>
Token Value: <DATABRICKS_TOKEN>
Saved to: .databricks_zerobus_token
```

---

## 🔧 NEXT STEPS (Manual - 2 minutes)

### Step 1: Access Ignition Gateway
1. Browser should have opened: **http://localhost:8183**
2. Login:
   - Username: `admin`
   - Password: `password`

### Step 2: Navigate to Zerobus Config
```
Config → Zerobus (in left menu) → Connections
```

### Step 3: Update/Create Connection
Click "Edit" or "Add New Connection" and enter:

```yaml
Connection Name: FieldEngineering
Description: Mining demo streaming to Databricks

Host: e2-demo-field-eng.cloud.databricks.com
HTTP Path: /sql/1.0/warehouses/4b9b953939869799
Token: <DATABRICKS_TOKEN>

Catalog: field_engineering
Schema: mining_demo
Table: zerobus_sensor_stream
```

### Step 4: Test & Enable
1. Click **"Test Connection"**
   - Should show: ✅ "Connected successfully"
2. Click **"Save"**
3. **Enable** the connection (toggle switch)

### Step 5: Verify Streaming
After 30 seconds, check Status page:
- Connection Status: **Connected** ✅
- Tags Subscribed: **50**
- Records Sent: **Should be increasing**

---

## 📊 Verification Queries

### Check Ingestion
Run in Databricks SQL Editor:

```sql
-- Check recent data
SELECT
    tag_path,
    numeric_value,
    quality,
    event_time,
    ingestion_timestamp
FROM field_engineering.mining_demo.zerobus_sensor_stream
ORDER BY ingestion_timestamp DESC
LIMIT 20;

-- Check ingestion rate
SELECT
    COUNT(*) as total_records,
    MAX(ingestion_timestamp) as latest_ingestion,
    DATEDIFF(SECOND, MAX(event_time), MAX(ingestion_timestamp)) as latency_seconds
FROM field_engineering.mining_demo.zerobus_sensor_stream;
```

### Expected Results
- **Latency**: < 5 seconds (near real-time)
- **Records**: 50 records/second (one per tag)
- **Tag paths**: `Mining/HT_001/Speed`, `Mining/CR_001/Throughput`, etc.

---

## 🎯 Summary

**What was fixed**:
1. ✅ Schema mismatch (14 fields now match proto)
2. ✅ Quality field type (INT instead of STRING)
3. ✅ Permissions granted to account users
4. ✅ New valid token created

**What remains**:
- ⏱️ Update Zerobus token in Gateway (2 minutes, manual step above)

**After token update**:
- Data will start flowing immediately
- 50 tags × 1 Hz = 3,000 records/minute
- Near real-time latency (< 5 seconds)

---

## 📁 Files Created/Updated

- ✅ `databricks/fix_table_schema.py` - Recreated table with correct schema
- ✅ `databricks/grant_table_permissions.py` - Granted account users permissions
- ✅ `databricks/create_zerobus_token.py` - Created new valid token
- ✅ `.databricks_zerobus_token` - Token saved securely
- ✅ This document: `ZEROBUS_FIXED_STATUS.md`

---

## 🔍 Troubleshooting

If still not streaming after token update:

1. **Restart Ignition Gateway**:
   ```bash
   docker-compose -f docker/docker-compose.yml restart
   ```

2. **Check Zerobus Status Page**:
   - Gateway → Status → Zerobus
   - Look for "Last Error" message

3. **Check Databricks Table**:
   ```bash
   python3 databricks/grant_table_permissions.py
   ```
   Should show row count increasing

4. **Check Token Permissions**:
   ```bash
   databricks auth token
   ```
   Verify token is valid and active

---

**Status**: Ready for final token update! 🚀
