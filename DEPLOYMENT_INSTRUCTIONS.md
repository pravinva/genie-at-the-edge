# 🚀 ML Platform Deployment Instructions

## ✅ Code Successfully Pushed to GitHub

**Branch**: `feature/agentic-hmi-workstreams`
**Repository**: https://github.com/pravinva/genie-at-the-edge

Your complete ML platform has been pushed to GitHub and is ready for deployment.

---

## 📋 Next Steps

### 1. Sync Code to Databricks Workspace

1. **Open Databricks Workspace**:
   - URL: https://e2-demo-field-eng.cloud.databricks.com/
   - Go to: Workspace → Repos

2. **Sync Repository**:
   - Find repo: `genie-at-the-edge`
   - Click **"Pull"** or **"Sync"** button
   - Verify path: `/Repos/pravin.varma@databricks.com/genie-at-the-edge/`

3. **Verify Files**:
   - Navigate to `databricks/` folder
   - Check files are present:
     - ✅ `dlt_enrichment_pipeline.py`
     - ✅ `train_anomaly_detection_model.py`
     - ✅ `realtime_scoring_pipeline.py`
     - ✅ `weekly_model_retraining.py`
     - ✅ `deploy_dlt_pipeline.py`
     - ✅ `deploy_ml_jobs.py`
     - ✅ `DEPLOY_AUTOMATION.sh`

---

### 2. Run Automated Deployment

From your local machine:

```bash
cd /Users/pravin.varma/Documents/Demo/genie-at-the-edge/

# Run master automation script
./databricks/DEPLOY_AUTOMATION.sh
```

The script will:
1. ✅ Verify prerequisites
2. ✅ Deploy DLT pipeline (Bronze → Silver → Gold)
3. ✅ Create 3 ML jobs (Training, Scoring, Retraining)
4. ✅ Run initial model training (~15 min)
5. ✅ Verify model registration (@champion alias)
6. ✅ Check end-to-end data flow

**Expected Duration**: ~20 minutes

---

## 📦 What Will Be Deployed

### DLT Pipeline: `genie_edge_ml_enrichment`

**Tables Created**:
```
field_engineering.ml_silver.bronze_sensor_events
field_engineering.ml_silver.silver_enriched_sensors
field_engineering.ml_silver.gold_ml_features
field_engineering.ml_silver.gold_equipment_360 (view)
```

**Configuration**:
- Mode: Continuous (always running)
- Photon: Enabled
- Cluster: 1-4 workers auto-scale
- Latency: ~8 seconds (Bronze → Gold)

### ML Job 1: Initial Training

**Name**: `ml_anomaly_detection_initial_training`
**Notebook**: `databricks/train_anomaly_detection_model.py`
**Trigger**: Manual (run once)
**Runtime**: ~15 minutes
**Output**: Model registered as `field_engineering.ml_models.equipment_anomaly_detector@champion`

### ML Job 2: Real-time Scoring

**Name**: `ml_realtime_scoring_continuous`
**Notebook**: `databricks/realtime_scoring_pipeline.py`
**Trigger**: Continuous (always running)
**Batch**: 30-second micro-batches
**Latency**: ~20 seconds end-to-end

### ML Job 3: Weekly Retraining

**Name**: `ml_weekly_retraining`
**Notebook**: `databricks/weekly_model_retraining.py`
**Trigger**: Scheduled (Every Sunday 2 AM PST)
**Cron**: `0 0 2 ? * SUN`
**Runtime**: ~20 minutes

---

## 🔧 Manual Deployment (Alternative)

If you prefer to run commands manually:

### Step 1: Deploy DLT Pipeline

```bash
python3 databricks/deploy_dlt_pipeline.py
```

### Step 2: Deploy ML Jobs

```bash
python3 databricks/deploy_ml_jobs.py
```

### Step 3: Run Initial Training

```bash
# Get job ID
JOB_ID=$(databricks jobs list --output JSON | jq -r '.jobs[] | select(.settings.name=="ml_anomaly_detection_initial_training") | .job_id')

# Run job
databricks jobs run-now --job-id $JOB_ID
```

---

## ✅ Verification

### Check DLT Pipeline

**Via UI**:
- https://e2-demo-field-eng.cloud.databricks.com/#joblist/pipelines
- Look for: `genie_edge_ml_enrichment`
- Status should be: **RUNNING**

**Via SQL**:
```sql
-- Check if tables exist and have data
SELECT 'bronze_sensor_events' as table_name, COUNT(*) as row_count 
FROM field_engineering.ml_silver.bronze_sensor_events
UNION ALL
SELECT 'silver_enriched_sensors', COUNT(*) 
FROM field_engineering.ml_silver.silver_enriched_sensors
UNION ALL
SELECT 'gold_ml_features', COUNT(*) 
FROM field_engineering.ml_silver.gold_ml_features;
```

### Check ML Jobs

**Via UI**:
- https://e2-demo-field-eng.cloud.databricks.com/#job/list
- Look for:
  - ✅ `ml_anomaly_detection_initial_training`
  - ✅ `ml_realtime_scoring_continuous`
  - ✅ `ml_weekly_retraining`

**Via CLI**:
```bash
databricks jobs list --output JSON | jq -r '.jobs[] | select(.settings.name | contains("ml_"))'
```

### Check Model Registry

**Via Python**:
```python
import mlflow
mlflow.set_registry_uri("databricks-uc")

# Load model
model = mlflow.pyfunc.load_model(
    "models:/field_engineering.ml_models.equipment_anomaly_detector@champion"
)
print("✅ Model loaded successfully")
```

**Via UI**:
- https://e2-demo-field-eng.cloud.databricks.com/#mlflow/models/field_engineering.ml_models.equipment_anomaly_detector
- Check for: `@champion` alias

---

## 🎯 Complete Data Flow

```
Ignition (50 tags)
  └─> Zerobus Streaming (300ms)
      └─> Bronze: sensor_events
          └─> DLT Enrichment (8s)
              ├─> Silver: enriched_sensors (+ Historian/MES/SAP)
              └─> Gold: ml_features (time-windows)
                  └─> ML Scoring (20s)
                      └─> Lakebase: ml_recommendations
                          └─> Ignition HMI (50ms query)
                              └─> Operator Action
                                  └─> Feedback Loop
                                      └─> Weekly Retraining
```

**Total Latency**: ~35 seconds (sensor change → recommendation in HMI)

---

## 📊 Monitoring Dashboard

### Quick Health Check

```sql
-- Check latest data timestamps
SELECT 
    'Sensor Events (Bronze)' as layer,
    MAX(event_time) as latest_timestamp,
    COUNT(*) as total_rows
FROM field_engineering.ignition_streaming.sensor_events
UNION ALL
SELECT 
    'Enriched Sensors (Silver)',
    MAX(event_time),
    COUNT(*)
FROM field_engineering.ml_silver.silver_enriched_sensors
UNION ALL
SELECT 
    'ML Features (Gold)',
    MAX(window_end),
    COUNT(*)
FROM field_engineering.ml_silver.gold_ml_features
UNION ALL
SELECT 
    'ML Recommendations (Lakebase)',
    MAX(scored_at),
    COUNT(*)
FROM field_engineering.lakebase.ml_recommendations;
```

### Job Status

```bash
# Check running jobs
databricks jobs list --output JSON | jq -r '.jobs[] | select(.settings.name | contains("ml_")) | "Job: \(.settings.name)\nID: \(.job_id)\n"'
```

---

## 🐛 Troubleshooting

### Issue: DLT Pipeline Not Starting

**Symptoms**: Tables not being created

**Solution**:
1. Verify repo sync: `/Repos/pravin.varma@databricks.com/genie-at-the-edge/`
2. Check source table: `field_engineering.ignition_streaming.sensor_events` exists
3. View pipeline logs in UI for errors
4. Restart: UI → Stop → Start

### Issue: Training Job Fails

**Symptoms**: Initial training errors

**Common Causes**:
- **No data**: Gold features table empty (DLT needs 5-10 min to populate)
- **Permissions**: Service principal missing privileges
- **Cluster**: ML Runtime 15.4 not available

**Solution**:
```bash
# Check gold features exist
databricks sql execute --warehouse-id 4b9b953939869799 \
  --statement "SELECT COUNT(*) FROM field_engineering.ml_silver.gold_ml_features"

# If 0 rows, wait 5-10 minutes for DLT to process
```

### Issue: Scoring Pipeline Empty Results

**Symptoms**: `ml_recommendations` table has 0 rows

**Common Causes**:
- **No model**: Training didn't complete (@champion alias not set)
- **No anomalies**: All sensor values normal (anomaly_score < 0.5)
- **No data flow**: DLT pipeline not streaming

**Solution**:
```sql
-- Check if model exists
SELECT * FROM system.information_schema.models 
WHERE catalog_name = 'field_engineering' 
AND schema_name = 'ml_models';

-- Check if features are flowing
SELECT COUNT(*), MAX(window_end)
FROM field_engineering.ml_silver.gold_ml_features
WHERE window_end >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR;
```

---

## 💰 Cost Summary

### Monthly Costs (Continuous Operation)

| Component | Cluster | Workers | Hours/Month | Cost/Month |
|-----------|---------|---------|-------------|------------|
| DLT Pipeline | i3.xlarge | 2 | 730 | $1,460 |
| Scoring Job | i3.xlarge | 2 | 730 | $1,460 |
| Weekly Retraining | i3.xlarge | 2 | 1.3 | $20 |
| **Total** | | | | **$2,940** |

### Cost Optimization Options

1. **Reduce workers**: 1-2 instead of 2-4 auto-scale → Save 30%
2. **Pause during off-hours**: Schedule pause/resume → Save 50%
3. **Use spot instances**: Enable spot for non-critical jobs → Save 60%
4. **Increase batch interval**: 2-5 min instead of 30s → Save 20%

**Optimized Cost**: ~$1,200/month

---

## 📚 Documentation

- **Platform Architecture**: `databricks/ML_PLATFORM_README.md` (600+ lines)
- **Deployment Automation**: `DEPLOYMENT_AUTOMATION_README.md`
- **Ignition Integration**: `ignition/README.md`
- **Demo Site**: https://pravinva.github.io/genie-edge-demo/

---

## ✅ Success Criteria

Your deployment is successful when:

1. ✅ DLT pipeline shows **RUNNING** status
2. ✅ All 4 tables exist with data:
   - `bronze_sensor_events` (thousands of rows)
   - `silver_enriched_sensors` (thousands of rows)
   - `gold_ml_features` (hundreds of rows)
   - `ml_recommendations` (rows appear after 20-30 min)
3. ✅ Model registered with `@champion` alias
4. ✅ 3 ML jobs created and running/scheduled
5. ✅ Lakebase tables created:
   - `ml_recommendations`
   - `operator_feedback`
   - `equipment_state`

---

## 🎉 Next Steps After Deployment

1. **Configure Ignition HMI**:
   - JDBC connection to Lakebase
   - Named Queries for recommendations
   - Perspective views for operator panel

2. **Test Operator Feedback**:
   - Simulate operator actions (Execute/Defer/Ask Why)
   - Verify feedback recorded to Delta Lake

3. **Monitor Model Performance**:
   - Check anomaly detection accuracy
   - Review operator feedback quality
   - Validate weekly retraining

4. **Production Readiness**:
   - Set up alerts for job failures
   - Configure cost budgets
   - Document operational procedures

---

**Questions or Issues?**
- Check: `databricks/ML_PLATFORM_README.md` (comprehensive troubleshooting)
- Architecture: https://pravinva.github.io/genie-edge-demo/

---

**Deployment Prepared By**: Claude Code  
**Date**: 2024-03-15  
**Platform**: Genie @ Edge ML Platform v1.0
