# Automated ML Platform Deployment

Complete automation for deploying the Genie @ Edge ML platform with DLT pipelines, ML jobs, and scheduling.

## Prerequisites

1. **Code in GitHub**: Push code to your GitHub repository
2. **Databricks Repo Sync**: Sync GitHub repo to Databricks workspace
3. **Service Principal**: OAuth configured for Zerobus
4. **Ignition Running**: Container streaming sensor data

## Quick Start

### Step 1: Push Code to GitHub

```bash
git add .
git commit -m "feat: Complete ML platform with automated deployment"
git push origin feature/agentic-hmi-workstreams
```

### Step 2: Sync to Databricks Repos

1. Go to Databricks UI → Workspace → Repos
2. Find your repo: `genie-at-the-edge`
3. Click "Pull" or "Sync" to get latest code
4. Verify path: `/Repos/pravin.varma@databricks.com/genie-at-the-edge/`

### Step 3: Run Automated Deployment

```bash
cd /Users/pravin.varma/Documents/Demo/genie-at-the-edge/
./databricks/DEPLOY_AUTOMATION.sh
```

The script will:
1. ✅ Verify prerequisites
2. ✅ Deploy DLT pipeline (Bronze → Silver → Gold)
3. ✅ Create ML jobs (Training, Scoring, Retraining)
4. ✅ Run initial model training
5. ✅ Verify model registration (@champion alias)
6. ✅ Check data flow end-to-end

**Total time**: ~20 minutes (mostly waiting for training job)

## What Gets Deployed

### 1. DLT Pipeline: `genie_edge_ml_enrichment`

**Script**: `databricks/deploy_dlt_pipeline.py`

**Tables Created**:
- `field_engineering.ml_silver.bronze_sensor_events`
- `field_engineering.ml_silver.silver_enriched_sensors`
- `field_engineering.ml_silver.gold_ml_features`
- `field_engineering.ml_silver.gold_equipment_360` (view)

**Configuration**:
- Mode: Continuous (always running)
- Photon: Enabled
- Cluster: 1-4 workers (auto-scale)
- Channel: CURRENT

### 2. ML Training Job: `ml_anomaly_detection_initial_training`

**Script**: `databricks/deploy_ml_jobs.py`

**Notebook**: `databricks/train_anomaly_detection_model.py`

**Purpose**: Train initial Isolation Forest + Random Forest ensemble

**Trigger**: Manual (run once during deployment)

**Runtime**: ~15 minutes

**Output**: Model registered as `field_engineering.ml_models.equipment_anomaly_detector@champion`

### 3. Real-time Scoring Job: `ml_realtime_scoring_continuous`

**Notebook**: `databricks/realtime_scoring_pipeline.py`

**Purpose**: Stream ML inference on gold features, write to Lakebase

**Trigger**: Continuous (always running)

**Micro-batch**: Every 30 seconds

**Latency**: ~20 seconds end-to-end

### 4. Weekly Retraining Job: `ml_weekly_retraining`

**Notebook**: `databricks/weekly_model_retraining.py`

**Purpose**: Retrain model with operator feedback, promote to @challenger

**Trigger**: Scheduled (Every Sunday 2 AM PST)

**Cron**: `0 0 2 ? * SUN`

**Runtime**: ~20 minutes

## Cluster Configuration

All jobs use the same cluster configuration:

```python
{
    "spark_version": "15.4.x-cpu-ml-scala2.12",
    "node_type_id": "i3.xlarge",
    "num_workers": 2,
    "spark_conf": {
        "spark.databricks.delta.preview.enabled": "true"
    }
}
```

**ML Runtime**: 15.4 LTS
**Node Type**: i3.xlarge (4 cores, 30.5 GB RAM)
**Workers**: 2 (can adjust based on load)

## Manual Deployment (Alternative)

If you prefer manual control, run scripts individually:

### Deploy DLT Pipeline

```bash
python3 databricks/deploy_dlt_pipeline.py
```

### Deploy ML Jobs

```bash
python3 databricks/deploy_ml_jobs.py
```

### Run Initial Training

```bash
# Get job ID
JOB_ID=$(databricks jobs list --output JSON | jq -r '.jobs[] | select(.settings.name=="ml_anomaly_detection_initial_training") | .job_id')

# Run job
databricks jobs run-now --job-id $JOB_ID
```

## Verification

### Check DLT Pipeline

```bash
# Via CLI
databricks pipelines list --filter "name = 'genie_edge_ml_enrichment'"

# Via UI
https://e2-demo-field-eng.cloud.databricks.com/#joblist/pipelines
```

### Check ML Jobs

```bash
# List all ML jobs
databricks jobs list --output JSON | jq -r '.jobs[] | select(.settings.name | contains("ml_"))'

# Get job status
databricks jobs get --job-id <JOB_ID>
```

### Check Model Registry

```bash
# Via Python
python3 -c "
import mlflow
mlflow.set_registry_uri('databricks-uc')
model = mlflow.pyfunc.load_model('models:/field_engineering.ml_models.equipment_anomaly_detector@champion')
print('✅ Model loaded successfully')
"
```

### Check Data Flow

```sql
-- Sensor events (Bronze)
SELECT COUNT(*) FROM field_engineering.ignition_streaming.sensor_events;

-- Enriched sensors (Silver)
SELECT COUNT(*) FROM field_engineering.ml_silver.silver_enriched_sensors;

-- ML features (Gold)
SELECT COUNT(*) FROM field_engineering.ml_silver.gold_ml_features;

-- Recommendations (Lakebase)
SELECT COUNT(*) FROM field_engineering.lakebase.ml_recommendations;
```

## Monitoring

### DLT Pipeline Health

```sql
-- Check latest processing timestamp
SELECT MAX(window_end) as latest_window
FROM field_engineering.ml_silver.gold_ml_features;
```

### Job Run History

```bash
# Get recent runs for a job
databricks runs list --job-id <JOB_ID> --limit 10
```

### Model Performance

```sql
-- Check operator feedback accuracy
SELECT
    operator_action,
    COUNT(*) as count,
    AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) as accuracy
FROM field_engineering.lakebase.operator_feedback
WHERE created_at >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY operator_action;
```

## Troubleshooting

### DLT Pipeline Not Starting

**Symptom**: Tables not being created

**Solution**:
1. Check notebook path is correct in workspace
2. Verify source table exists: `field_engineering.ignition_streaming.sensor_events`
3. Check pipeline logs in UI for errors
4. Restart pipeline: UI → Stop → Start

### Training Job Fails

**Symptom**: Initial training job errors

**Common Issues**:
1. **No data**: DLT pipeline needs time to populate gold_ml_features (5-10 min)
2. **Permissions**: Verify service principal has ALL PRIVILEGES on catalog
3. **Cluster**: Ensure ML Runtime 15.4 is available in workspace

**Solution**:
```bash
# Check if gold features exist
databricks sql execute --warehouse-id 4b9b953939869799 \
  --statement "SELECT COUNT(*) FROM field_engineering.ml_silver.gold_ml_features"

# If 0 rows, wait for DLT pipeline to process data
# If error, check permissions
```

### Scoring Pipeline Not Writing

**Symptom**: `ml_recommendations` table empty

**Common Issues**:
1. **No model**: Training job didn't complete successfully
2. **No data**: DLT pipeline not streaming features
3. **Threshold**: No anomalies above 0.5 threshold

**Solution**:
```sql
-- Check model exists
DESCRIBE TABLE field_engineering.ml_models.equipment_anomaly_detector;

-- Check if features are flowing
SELECT COUNT(*), MAX(window_end)
FROM field_engineering.ml_silver.gold_ml_features
WHERE window_end >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR;
```

## Cost Estimation

### Continuous Operations

| Component | Instance | Workers | Hours/Month | Cost/Month |
|-----------|----------|---------|-------------|------------|
| DLT Pipeline | i3.xlarge | 2 | 730 | ~$1,460 |
| Scoring Job | i3.xlarge | 2 | 730 | ~$1,460 |
| **Total** | | | | **~$2,920** |

### Scheduled Operations

| Component | Instance | Workers | Runs/Month | Duration | Cost/Month |
|-----------|----------|---------|------------|----------|------------|
| Weekly Retraining | i3.xlarge | 2 | 4 | 20 min | ~$20 |

**Total Monthly Cost**: ~$2,940

### Cost Optimization

1. **Reduce DLT workers**: Change auto-scale to 1-2 workers
2. **Pause scoring during off-hours**: Add schedule to pause/resume
3. **Use spot instances**: Configure cluster to use spot instances (60% savings)
4. **Optimize batch size**: Increase scoring micro-batch from 30s to 2-5 min

With optimization: **~$1,200/month**

## Updating Deployments

### Update DLT Pipeline

```bash
# After pushing code changes to GitHub and syncing
python3 databricks/deploy_dlt_pipeline.py

# Pipeline will update and restart automatically
```

### Update ML Jobs

```bash
# After pushing code changes
python3 databricks/deploy_ml_jobs.py

# Jobs will update, but running instances need manual restart
```

### Force Retrain Model

```bash
# Get retraining job ID
JOB_ID=$(databricks jobs list --output JSON | jq -r '.jobs[] | select(.settings.name=="ml_weekly_retraining") | .job_id')

# Run manually (don't wait for Sunday)
databricks jobs run-now --job-id $JOB_ID
```

## Support

- **Architecture**: `databricks/ML_PLATFORM_README.md`
- **Manual Deployment**: `databricks/DEPLOY_ML_PLATFORM.sh`
- **Ignition Integration**: `ignition/README.md`
- **Demo Site**: https://pravinva.github.io/genie-edge-demo/

---

**Last Updated**: 2024-03-15
**Version**: 1.0
**Author**: Pravin Varma
