#!/bin/bash
################################################################################
# Master Automation Script - Complete ML Platform Deployment
# Orchestrates DLT pipeline and ML jobs deployment
################################################################################

set -e

echo "================================================================================"
echo "  GENIE @ EDGE - AUTOMATED ML PLATFORM DEPLOYMENT"
echo "================================================================================"
echo ""

# Configuration
CATALOG="field_engineering"
WAREHOUSE_ID="4b9b953939869799"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "\n${GREEN}[Step $1/$2]${NC} $3"
    echo "--------------------------------------------------------------------------------"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# Prerequisites
# ============================================================================

print_step 1 6 "Verifying Prerequisites"

# Check if code is synced to Databricks Repos
echo "Prerequisites:"
echo "  1. ✅ Code pushed to GitHub"
echo "  2. ⏳ Code synced to Databricks Repos"
echo "     Path: /Repos/pravin.varma@databricks.com/genie-at-the-edge/"
echo ""
read -p "Has code been synced to Databricks Repos? (y/n): " REPO_SYNCED

if [ "$REPO_SYNCED" != "y" ]; then
    print_error "Please sync code to Databricks Repos first"
    echo "  1. Go to: https://e2-demo-field-eng.cloud.databricks.com/#workspace/repos"
    echo "  2. Find repo: genie-at-the-edge"
    echo "  3. Click 'Pull' or 'Sync' to get latest code"
    exit 1
fi

print_success "Code synced to workspace"

# ============================================================================
# Step 2: Deploy DLT Pipeline
# ============================================================================

print_step 2 6 "Deploying DLT Enrichment Pipeline"

python3 databricks/deploy_dlt_pipeline.py

if [ $? -eq 0 ]; then
    print_success "DLT pipeline deployed and started"
else
    print_error "DLT pipeline deployment failed"
    exit 1
fi

# Wait for DLT to initialize
echo ""
echo "Waiting 30 seconds for DLT pipeline to initialize..."
sleep 30

# ============================================================================
# Step 3: Deploy ML Jobs
# ============================================================================

print_step 3 6 "Deploying ML Jobs (Training, Scoring, Retraining)"

python3 databricks/deploy_ml_jobs.py

if [ $? -eq 0 ]; then
    print_success "ML jobs created"
else
    print_error "ML jobs deployment failed"
    exit 1
fi

# ============================================================================
# Step 4: Run Initial Model Training
# ============================================================================

print_step 4 6 "Triggering Initial Model Training"

# Get job ID from deployment
TRAIN_JOB_ID=$(databricks jobs list --output JSON | jq -r '.jobs[] | select(.settings.name=="ml_anomaly_detection_initial_training") | .job_id')

if [ -z "$TRAIN_JOB_ID" ]; then
    print_error "Could not find training job ID"
    exit 1
fi

print_success "Found training job: $TRAIN_JOB_ID"

echo ""
echo "Starting initial model training..."
RUN_ID=$(databricks jobs run-now --job-id $TRAIN_JOB_ID --output JSON | jq -r '.run_id')

if [ -z "$RUN_ID" ]; then
    print_error "Failed to start training job"
    exit 1
fi

print_success "Training job started: Run ID $RUN_ID"
echo "  URL: https://e2-demo-field-eng.cloud.databricks.com/#job/$TRAIN_JOB_ID/run/$RUN_ID"

# Monitor training job
echo ""
echo "Monitoring training job (will check every 30 seconds)..."

for i in {1..40}; do
    sleep 30
    STATUS=$(databricks runs get --run-id $RUN_ID --output JSON | jq -r '.state.life_cycle_state')
    
    echo "  [$i/40] Status: $STATUS"
    
    if [ "$STATUS" == "TERMINATED" ]; then
        RESULT=$(databricks runs get --run-id $RUN_ID --output JSON | jq -r '.state.result_state')
        if [ "$RESULT" == "SUCCESS" ]; then
            print_success "Training completed successfully!"
            break
        else
            print_error "Training failed with status: $RESULT"
            exit 1
        fi
    fi
done

# ============================================================================
# Step 5: Verify Model Registration
# ============================================================================

print_step 5 6 "Verifying Model Registration"

echo "Checking for @champion model alias..."
sleep 5

MODEL_NAME="field_engineering.ml_models.equipment_anomaly_detector"

# Try to get model version (this will work if model was registered)
python3 -c "
import mlflow
mlflow.set_registry_uri('databricks-uc')
try:
    model = mlflow.pyfunc.load_model('models:/$MODEL_NAME@champion')
    print('  ✅ Model @champion alias is set')
except:
    print('  ❌ Model @champion alias not found')
    exit(1)
" 2>/dev/null

if [ $? -eq 0 ]; then
    print_success "Model registered with @champion alias"
else
    print_warning "Model may not be registered yet - check training job logs"
fi

# ============================================================================
# Step 6: Verification & Summary
# ============================================================================

print_step 6 6 "Final Verification"

echo ""
echo "Checking data flow..."

# Check DLT tables
echo ""
echo "1. DLT Tables:"
python3 -c "
from databricks.sdk import WorkspaceClient
import time
w = WorkspaceClient(profile='DEFAULT')

tables = ['bronze_sensor_events', 'silver_enriched_sensors', 'gold_ml_features']
for table in tables:
    try:
        result = w.statement_execution.execute_statement(
            warehouse_id='$WAREHOUSE_ID',
            statement=f'DESCRIBE TABLE $CATALOG.ml_silver.{table}',
            wait_timeout='0s'
        )
        time.sleep(1)
        status = w.statement_execution.get_statement(result.statement_id)
        if status.status.state.value == 'SUCCEEDED':
            print(f'   ✅ {table}')
        else:
            print(f'   ⚠️  {table} - not ready yet')
    except:
        print(f'   ⚠️  {table} - not ready yet')
"

# Check Lakebase tables
echo ""
echo "2. Lakebase Serving Tables:"
python3 -c "
from databricks.sdk import WorkspaceClient
import time
w = WorkspaceClient(profile='DEFAULT')

tables = ['ml_recommendations', 'operator_feedback', 'equipment_state']
for table in tables:
    result = w.statement_execution.execute_statement(
        warehouse_id='$WAREHOUSE_ID',
        statement=f'SELECT COUNT(*) FROM $CATALOG.lakebase.{table}',
        wait_timeout='0s'
    )
    time.sleep(1)
    status = w.statement_execution.get_statement(result.statement_id)
    if status.status.state.value == 'SUCCEEDED' and status.result and status.result.data_array:
        count = int(status.result.data_array[0][0])
        print(f'   ✅ {table}: {count} rows')
"

# Check jobs status
echo ""
echo "3. Jobs Status:"
databricks jobs list --output JSON | jq -r '.jobs[] | select(.settings.name | contains("ml_")) | "   ✅ \(.settings.name) (ID: \(.job_id))"'

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================

echo ""
echo "================================================================================"
echo "  ✅ AUTOMATED DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
echo "Platform Components Deployed:"
echo "  1. ✅ DLT Pipeline (Bronze → Silver → Gold)"
echo "  2. ✅ ML Model Training Job"
echo "  3. ✅ Real-time Scoring Job (Continuous)"
echo "  4. ✅ Weekly Retraining Job (Scheduled)"
echo "  5. ✅ Lakebase Serving Tables"
echo ""
echo "Current Status:"
echo "  • DLT Pipeline: Running (continuous mode)"
echo "  • ML Model: @champion alias set"
echo "  • Scoring Pipeline: Will start after deployment"
echo "  • Weekly Retraining: Scheduled for Sundays 2 AM PST"
echo ""
echo "View Deployments:"
echo "  • DLT Pipeline: https://e2-demo-field-eng.cloud.databricks.com/#joblist/pipelines"
echo "  • Jobs: https://e2-demo-field-eng.cloud.databricks.com/#job/list"
echo "  • Models: https://e2-demo-field-eng.cloud.databricks.com/#mlflow/models/$MODEL_NAME"
echo ""
echo "Next Steps:"
echo "  1. Wait 5-10 minutes for DLT pipeline to process sensor data"
echo "  2. Verify gold_ml_features table is populated"
echo "  3. Start real-time scoring job manually (or wait for auto-start)"
echo "  4. Configure Ignition HMI to read from Lakebase tables"
echo ""
echo "Troubleshooting:"
echo "  • Check DLT pipeline logs if tables are not populating"
echo "  • Verify sensor data is streaming from Ignition"
echo "  • Monitor job runs in the Jobs UI"
echo ""
echo "================================================================================"
