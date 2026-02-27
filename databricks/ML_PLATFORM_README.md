# Genie @ Edge ML Platform

**Real-time Anomaly Detection & Predictive Maintenance for Industrial Operations**

Complete Ignition × Databricks integration with:
- Sub-second sensor streaming (Zerobus OPC-UA → Delta Lake)
- Enterprise data enrichment (Historian, MES, SAP fusion)
- ML-powered recommendations (Isolation Forest + Random Forest)
- Operator feedback loop (continuous learning)
- Low-latency serving (Lakebase with <50ms queries)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IGNITION GATEWAY                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐      │
│  │  OPC-UA Tags │ →  │   Zerobus    │ →  │  Delta Lake (Bronze)    │      │
│  │  (50 tags)   │    │   Streaming  │    │  <500ms latency         │      │
│  └──────────────┘    └──────────────┘    └──────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATABRICKS - DLT PIPELINE                              │
│                                                                             │
│  Bronze Layer              Silver Layer               Gold Layer            │
│  ─────────────────         ──────────────────         ─────────────────    │
│  • sensor_events     →     • Enriched with:    →     • ML features       │
│  • Raw OPC-UA data         • Historian (90d)          • Time windows      │
│                            • MES schedules            • Aggregations      │
│                            • SAP assets               • Deviations        │
│                            • Maintenance logs                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ML MODEL TRAINING                                   │
│                                                                             │
│  ┌──────────────────────┐         ┌──────────────────────┐                │
│  │  Isolation Forest    │  +      │  Random Forest       │                │
│  │  ─────────────────   │         │  ───────────────     │                │
│  │  Anomaly scoring     │         │  Action classifier   │                │
│  │  0.0 - 1.0 range     │         │  5 action types      │                │
│  │  Unsupervised        │         │  Operator-labeled    │                │
│  └──────────────────────┘         └──────────────────────┘                │
│                                                                             │
│  Model Registry: field_engineering.ml_models.equipment_anomaly_detector     │
│  Aliases: @champion (production), @challenger (testing)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME SCORING PIPELINE                               │
│                                                                             │
│  Gold Features  →  ML Model UDF  →  Recommendations  →  Lakebase          │
│  (streaming)       (every 30s)       (anomaly > 0.5)     (<50ms queries)   │
│                                                                             │
│  Output: anomaly_score, action_code, confidence, recommendation_text       │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LAKEBASE SERVING LAYER                                │
│                                                                             │
│  PostgreSQL-compatible tables:                                             │
│  • recommendations_serving  ←──┐                                           │
│  • equipment_state          ←──┼── Ignition Perspective Views              │
│  • hmi_dashboard            ←──┘   (Named Queries)                         │
│                                                                             │
│  PG NOTIFY webhook → Instant push to Ignition sessions (<100ms)            │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                  IGNITION PERSPECTIVE HMI                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────┐                │
│  │  Equipment Dashboard                                  │                │
│  │  ─────────────────────                                │                │
│  │  [HAUL-001] Status: ⚠️  WARNING                       │                │
│  │  Temp: 87°C  Vibration: 4.8 g  Throughput: 850 TPH   │                │
│  │                                                       │                │
│  │  💡 AI Recommendation (Confidence: 87%)               │                │
│  │  "Reduce throughput to 60% - elevated temperature    │                │
│  │   and vibration detected. Estimated time to          │                │
│  │   failure: 48-72 hours"                              │                │
│  │                                                       │                │
│  │  [ ✅ Execute ]  [ ⏸️ Defer ]  [ 🤔 Ask AI Why ]      │                │
│  └───────────────────────────────────────────────────────┘                │
│                                  ↓                                          │
│                        Operator clicks button                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OPERATOR FEEDBACK LOOP                                  │
│                                                                             │
│  Ignition  →  Named Query  →  Lakebase  →  Delta Lake                     │
│   Button       INSERT            (async)      (5-min sync)                 │
│                                                                             │
│  Feedback signals:                                                         │
│  • Executed   → True positive (model correct)                              │
│  • Deferred   → Uncertain (more time needed)                               │
│  • Rejected   → False positive (model wrong)                               │
│  • Ask AI Why → Genie interaction                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                   WEEKLY MODEL RETRAINING                                   │
│                                                                             │
│  1. Load operator feedback (past week)                                     │
│  2. Label training data with corrected outcomes                            │
│  3. Retrain models with improved labels                                    │
│  4. Compare precision: new model vs @champion                              │
│  5. If improved: Promote to @challenger for A/B testing                    │
│  6. After validation: @challenger → @champion                              │
│                                                                             │
│  Schedule: Every Sunday 2 AM (cron: 0 2 * * 0)                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Real-time Data Streaming
- **Zerobus OPC-UA connector**: Direct Ignition → Delta Lake streaming
- **<500ms latency**: Tag change → Bronze table
- **50 tags**: Temperature, vibration, throughput, pressure per equipment
- **Auto-optimization**: Delta auto-compaction and Z-ordering

### 2. Enterprise Data Enrichment
- **Historian baselines**: 90 days of normal operating ranges
- **MES integration**: Production schedules, work orders, quality metrics
- **SAP context**: Asset registry, maintenance history, spare parts inventory
- **DLT pipeline**: Bronze → Silver → Gold transformation

### 3. ML Anomaly Detection
- **Isolation Forest**: Unsupervised anomaly scoring (0-1 scale)
- **Random Forest**: Supervised action classification (5 action types)
- **Multi-sensor correlation**: Temperature × vibration interactions
- **Time-window features**: 5-min, 15-min, 1-hour aggregations

### 4. Low-latency Serving
- **Lakebase**: PostgreSQL-compatible serving layer
- **<50ms queries**: Direct JDBC from Ignition
- **PG NOTIFY**: Instant webhook push to Ignition sessions
- **No polling**: Event-driven updates only

### 5. Continuous Learning
- **Operator feedback**: Execute/Defer/Reject decisions captured
- **Weekly retraining**: Incorporates corrected labels
- **Model versioning**: @champion/@challenger A/B testing
- **Precision tracking**: Monitors model accuracy over time

---

## File Structure

```
databricks/
├── DEPLOY_ML_PLATFORM.sh                 # Master deployment script
├── ML_PLATFORM_README.md                 # This file
│
├── Data Setup
│   ├── simulate_enterprise_sources_sdk.py    # Create Historian/MES/SAP tables
│   └── populate_enterprise_data.py           # Populate remaining tables
│
├── DLT Pipeline
│   ├── dlt_enrichment_pipeline.py            # Bronze → Silver → Gold
│   └── dlt_pipeline_config.json              # DLT deployment config
│
├── ML Training
│   ├── train_anomaly_detection_model.py      # Initial model training
│   └── weekly_model_retraining.py            # Weekly retraining job
│
├── Real-time Inference
│   └── realtime_scoring_pipeline.py          # Streaming ML inference
│
├── Serving & Feedback
│   ├── setup_lakebase_serving.py             # Lakebase tables & webhooks
│   └── operator_feedback_integration.py      # Feedback loop integration
│
└── Utilities
    ├── grant_all_permissions.py              # Permission management
    └── verify_zerobus_ready.py               # Connection verification
```

---

## Deployment Guide

### Prerequisites

1. **Databricks Workspace**
   - Unity Catalog enabled
   - Warehouse: `4b9b953939869799`
   - Profile: `DEFAULT` in ~/.databrickscfg

2. **Ignition Gateway**
   - Version: 8.1.x or higher
   - Zerobus module installed
   - Service principal OAuth configured

3. **Service Principal**
   - Name: `pravin_zerobus`
   - Client ID: `6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb`
   - OAuth secret configured
   - Permissions: ALL PRIVILEGES on catalog `field_engineering`

### Step-by-Step Deployment

```bash
# Clone repository
cd /Users/pravin.varma/Documents/Demo/genie-at-the-edge/

# Run master deployment script
./databricks/DEPLOY_ML_PLATFORM.sh
```

The script will guide you through:
1. ✅ Verify prerequisites (Databricks CLI, Python, Docker)
2. ✅ Setup enterprise data tables (automated)
3. ✅ Setup Lakebase serving tables (automated)
4. ⏳ Upload DLT pipeline (manual - workspace upload)
5. ⏳ Create DLT pipeline (manual - UI or API)
6. ⏳ Start DLT pipeline (manual - UI)
7. ⏳ Train initial ML model (manual - Databricks job)
8. ⏳ Deploy scoring pipeline (manual - Databricks job)
9. ⏳ Setup weekly retraining (manual - scheduled job)
10. ✅ Verify end-to-end data flow (automated)

### Manual Steps

#### 1. Upload DLT Pipeline to Workspace

```bash
databricks workspace import \
  databricks/dlt_enrichment_pipeline.py \
  /Users/pravin.varma@databricks.com/dlt_enrichment_pipeline \
  --language PYTHON
```

#### 2. Create DLT Pipeline

**Option A: Via UI**
1. Go to Databricks UI → Workflows → Delta Live Tables
2. Click "Create Pipeline"
3. Name: `genie_edge_ml_enrichment`
4. Notebook path: `/Users/pravin.varma@databricks.com/dlt_enrichment_pipeline`
5. Target: `field_engineering.ml_silver`
6. Storage: `/databricks/pipelines/genie_edge`
7. Cluster: Photon, 2-4 workers
8. Mode: Continuous
9. Click "Create"

**Option B: Via CLI**
```bash
databricks pipelines create \
  --json-file databricks/dlt_pipeline_config.json
```

#### 3. Train Initial Model

Create Databricks job:
```json
{
  "name": "train_anomaly_detection_initial",
  "tasks": [{
    "task_key": "train_model",
    "python_script": {
      "path": "/Users/pravin.varma@databricks.com/train_anomaly_detection_model.py"
    },
    "new_cluster": {
      "spark_version": "14.3.x-ml-scala2.12",
      "node_type_id": "i3.xlarge",
      "num_workers": 2
    }
  }]
}
```

Run job:
```bash
databricks jobs run-now --job-id <JOB_ID>
```

#### 4. Deploy Scoring Pipeline

Create streaming job (continuous):
```json
{
  "name": "realtime_ml_scoring",
  "tasks": [{
    "task_key": "scoring",
    "python_script": {
      "path": "/Users/pravin.varma@databricks.com/realtime_scoring_pipeline.py"
    },
    "new_cluster": {
      "spark_version": "14.3.x-ml-scala2.12",
      "node_type_id": "i3.xlarge",
      "num_workers": 2
    }
  }],
  "continuous": true
}
```

#### 5. Setup Weekly Retraining

Create scheduled job:
```json
{
  "name": "weekly_model_retraining",
  "schedule": {
    "quartz_cron_expression": "0 0 2 ? * SUN",
    "timezone_id": "America/Los_Angeles"
  },
  "tasks": [{
    "task_key": "retrain",
    "python_script": {
      "path": "/Users/pravin.varma@databricks.com/weekly_model_retraining.py"
    },
    "new_cluster": {
      "spark_version": "14.3.x-ml-scala2.12",
      "node_type_id": "i3.xlarge",
      "num_workers": 2
    }
  }]
}
```

---

## Ignition Integration

### 1. Configure JDBC Connection to Lakebase

**Connection Settings:**
```
Name: Databricks_Lakebase
Driver: PostgreSQL
URL: jdbc:postgresql://<lakebase-endpoint>:5432/field_engineering
Schema: lakebase
Username: token
Password: <databricks-access-token>
```

### 2. Create Named Queries

#### Query: Get Active Recommendations
```sql
-- Name: GetRecommendations
SELECT
  equipment_id,
  timestamp,
  anomaly_score,
  severity,
  action_code,
  recommendation_text,
  confidence,
  estimated_ttf,
  temp_avg_5min,
  vibration_avg_5min,
  throughput_avg_5min
FROM recommendations_serving
WHERE equipment_id = :equipment_id
  AND status = 'pending'
ORDER BY anomaly_score DESC
LIMIT 1
```

#### Query: Get Equipment Dashboard
```sql
-- Name: GetEquipmentDashboard
SELECT *
FROM hmi_dashboard
WHERE equipment_id = :equipment_id
```

#### Query: Record Operator Feedback
```sql
-- Name: RecordFeedback
INSERT INTO operator_feedback (
  feedback_id,
  equipment_id,
  recommendation_timestamp,
  action_code,
  anomaly_score,
  operator_action,
  operator_id,
  action_timestamp,
  operator_notes,
  shift,
  session_id,
  asked_genie
) VALUES (
  :feedback_id,
  :equipment_id,
  :recommendation_timestamp,
  :action_code,
  :anomaly_score,
  :operator_action,
  :operator_id,
  CURRENT_TIMESTAMP,
  :operator_notes,
  :shift,
  :session_id,
  :asked_genie
)
```

### 3. Create Perspective Views

#### Recommendations Panel Component

**Custom Properties:**
- `equipmentId` (string): Bound to parent view parameter
- `recommendation` (dataset): Bound to Named Query `GetRecommendations`

**Bindings:**
```python
# Indirect tag binding - poll every 5 seconds
self.custom.recommendation = system.db.runNamedQuery(
    "GetRecommendations",
    {"equipment_id": self.custom.equipmentId}
)
```

**Button onClick Scripts:**

```python
# Execute button
def onActionPerformed(self, event):
    feedback_id = str(system.util.getUUID())
    recommendation = self.parent.custom.recommendation

    system.db.runNamedQuery("RecordFeedback", {
        "feedback_id": feedback_id,
        "equipment_id": self.parent.custom.equipmentId,
        "recommendation_timestamp": recommendation[0]["timestamp"],
        "action_code": recommendation[0]["action_code"],
        "anomaly_score": recommendation[0]["anomaly_score"],
        "operator_action": "executed",
        "operator_id": self.session.props.auth.user.username,
        "operator_notes": "Executed via HMI",
        "shift": self.session.props.custom.currentShift,
        "session_id": self.session.props.id,
        "asked_genie": False
    })

    system.perspective.print("Recommendation executed: " + feedback_id)
    self.parent.refreshRecommendations()

# Defer button - similar but operator_action="deferred"
# Ask AI Why button - operator_action="ask_ai_why" + open Genie panel
```

### 4. PG NOTIFY Webhook Listener (Optional)

For instant push notifications (no polling):

```python
# WebSocket script (runs in session startup)
import psycopg2

def on_notification(notify):
    """Called when PG NOTIFY fires"""
    payload = json.loads(notify.payload)
    equipment_id = payload["equipment_id"]

    # Update session property to trigger view refresh
    self.session.props.custom.latestRecommendation = payload

    # Show toast notification
    system.perspective.sendMessage(
        "notification",
        payload={
            "message": f"New alert: {payload['recommendation_text']}",
            "severity": payload["severity"]
        }
    )

# Connect to Lakebase PostgreSQL
conn = psycopg2.connect(
    host="<lakebase-endpoint>",
    port=5432,
    database="field_engineering",
    user="token",
    password="<access-token>"
)

conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()
cursor.execute("LISTEN equipment_recommendations;")

# Poll for notifications in background thread
while True:
    if conn.poll() == psycopg2.extensions.POLL_OK:
        while conn.notifies:
            notify = conn.notifies.pop(0)
            on_notification(notify)
    time.sleep(0.1)
```

---

## Model Details

### Isolation Forest (Anomaly Scoring)

**Purpose**: Unsupervised anomaly detection
**Output**: Anomaly score 0.0-1.0 (higher = more anomalous)
**Features**: 20 numeric features (temperature, vibration, throughput, etc.)
**Threshold**: 0.7 for actionable alerts

**Interpretation:**
- `0.0 - 0.5`: Normal operation
- `0.5 - 0.7`: Minor deviation (monitor)
- `0.7 - 0.9`: Significant anomaly (action recommended)
- `0.9 - 1.0`: Critical anomaly (immediate action)

### Random Forest (Action Classification)

**Purpose**: Supervised action recommendation
**Output**: Action code + confidence
**Labels**: Trained on operator feedback

**Action Codes:**
1. `reduce_speed`: Reduce equipment speed to 60%
2. `schedule_maintenance`: Schedule bearing/belt inspection within 24h
3. `check_blockage`: Check for material blockage
4. `emergency_shutdown`: CRITICAL - immediate shutdown required
5. `preventive_inspection`: Upcoming maintenance window
6. `continue_operation`: Normal operation

**Confidence Threshold**: 0.75 for displaying recommendation

---

## Monitoring & Maintenance

### Daily Checks

1. **DLT Pipeline Health**
   ```sql
   SELECT
     COUNT(*) as events_last_hour
   FROM field_engineering.ml_silver.gold_ml_features
   WHERE window_end >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
   ```

2. **Model Inference Status**
   ```sql
   SELECT
     COUNT(*) as recommendations_today,
     AVG(confidence) as avg_confidence
   FROM field_engineering.lakebase.ml_recommendations
   WHERE scored_at >= CURRENT_DATE()
   ```

3. **Operator Feedback Rate**
   ```sql
   SELECT
     operator_action,
     COUNT(*) as count,
     AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) as accuracy
   FROM field_engineering.lakebase.operator_feedback
   WHERE created_at >= CURRENT_DATE()
   GROUP BY operator_action
   ```

### Weekly Tasks

1. **Review Model Performance**
   - Check @champion model accuracy
   - Review false positive rate
   - Validate operator feedback quality

2. **Monitor Retraining Job**
   - Verify weekly job completed successfully
   - Check if @challenger model was created
   - Compare precision: new model vs @champion

3. **Data Quality Checks**
   - Sensor data completeness (% non-null values)
   - Enterprise data freshness (last update timestamps)
   - Lakebase sync lag (Delta → PostgreSQL delay)

### Monthly Review

1. **Model Drift Analysis**
   - Compare feature distributions: current vs training data
   - Identify sensor calibration issues
   - Update baseline thresholds if needed

2. **Business Impact Metrics**
   - Equipment downtime prevented (via operator feedback outcomes)
   - False alarm rate trend
   - Operator acceptance rate (% recommendations executed)

---

## Troubleshooting

### Sensor Data Not Flowing

**Symptom**: `sensor_events` table not updating

**Checks:**
1. Ignition container running: `docker ps | grep ignition`
2. Zerobus connection status: Check Ignition Gateway logs
3. OAuth credentials valid: `python databricks/check_oauth_scopes.py`
4. Table permissions: `python databricks/grant_all_permissions.py`

### DLT Pipeline Stuck

**Symptom**: Silver/Gold tables not updating

**Checks:**
1. Pipeline status: UI → Delta Live Tables
2. Check pipeline logs for errors
3. Verify source tables exist: `SHOW TABLES IN field_engineering.ignition_streaming`
4. Restart pipeline: UI → Stop → Start

### Model Inference Slow

**Symptom**: Recommendations delayed >5 minutes

**Checks:**
1. Scoring pipeline running: Check Databricks jobs
2. Cluster size adequate: Minimum 2 workers
3. Feature query performance: Check query history in SQL warehouse
4. Model size: Ensure model artifact <50MB

### Lakebase Queries Timeout

**Symptom**: Ignition Named Queries fail

**Checks:**
1. Lakebase enabled on catalog: Check catalog properties
2. JDBC connection valid: Test in Ignition designer
3. Query syntax correct: PostgreSQL dialect, not Spark SQL
4. Warehouse running: Check warehouse status

---

## Performance Metrics

### Latency Benchmarks

| Stage | Target | Typical |
|-------|--------|---------|
| Sensor → Bronze | <500ms | 300ms |
| Bronze → Silver (DLT) | <5s | 3s |
| Silver → Gold (DLT) | <10s | 8s |
| Gold → ML Inference | <30s | 20s |
| Recommendation → Lakebase | <5s | 3s |
| Lakebase → Ignition Query | <50ms | 30ms |
| PG NOTIFY → Ignition | <100ms | 50ms |
| **End-to-end** | **<60s** | **35s** |

### Data Volumes

| Table | Update Frequency | Retention | Typical Size |
|-------|------------------|-----------|--------------|
| sensor_events (Bronze) | Real-time | 30 days | 50M rows |
| silver_enriched_sensors | Real-time | 30 days | 50M rows |
| gold_ml_features | 5-min windows | 90 days | 5M rows |
| ml_recommendations | 30s batch | 180 days | 100K rows |
| operator_feedback | On-demand | Indefinite | 10K rows |

### Resource Usage

**DLT Pipeline:**
- Workers: 2-4 (auto-scale)
- Node type: i3.xlarge
- Cost: ~$3/hour (continuous mode)

**ML Training:**
- Workers: 2
- Node type: i3.xlarge
- Runtime: ~15 minutes
- Frequency: Weekly
- Cost: ~$0.75/week

**Real-time Scoring:**
- Workers: 2
- Node type: i3.xlarge
- Cost: ~$3/hour (continuous)

**Total Monthly Cost**: ~$2,200 (continuous operations)

---

## Support & Documentation

- **Demo Site**: https://pravinva.github.io/genie-edge-demo/
- **Databricks Docs**: https://docs.databricks.com/
- **Ignition Docs**: https://docs.inductiveautomation.com/
- **MLflow Docs**: https://mlflow.org/docs/latest/

---

## License

Internal Databricks field engineering demo.
Not for production use without proper review and testing.

---

**Last Updated**: 2024-03-15
**Version**: 1.0
**Author**: Pravin Varma (pravin.varma@databricks.com)
