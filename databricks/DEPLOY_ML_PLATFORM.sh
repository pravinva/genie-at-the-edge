#!/bin/bash
################################################################################
# Genie @ Edge ML Platform Deployment
# Complete end-to-end deployment of Ignition × Databricks ML platform
#
# Architecture:
# - Real-time sensor streaming (Zerobus OPC-UA → Delta Lake)
# - Enterprise data enrichment (DLT pipeline)
# - ML anomaly detection (Isolation Forest + Random Forest)
# - Low-latency serving (Lakebase with PG NOTIFY webhooks)
# - Operator feedback loop (continuous learning)
#
# Prerequisites:
# - Databricks workspace with Unity Catalog enabled
# - Ignition Gateway running with Zerobus module
# - Service principal: pravin_zerobus (OAuth configured)
# - Warehouse: 4b9b953939869799
################################################################################

set -e  # Exit on any error

echo "================================================================================"
echo "  GENIE @ EDGE ML PLATFORM DEPLOYMENT"
echo "================================================================================"
echo ""

# Configuration
CATALOG="field_engineering"
WAREHOUSE_ID="4b9b953939869799"
WORKSPACE_PROFILE="DEFAULT"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
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
# STEP 1: Verify Prerequisites
# ============================================================================

print_step 1 10 "Verifying prerequisites"

# Check Databricks CLI
if ! command -v databricks &> /dev/null; then
    print_error "Databricks CLI not found. Install: pip install databricks-cli"
    exit 1
fi
print_success "Databricks CLI found"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found"
    exit 1
fi
print_success "Python 3 found"

# Check Docker (for Ignition verification)
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found - skipping Ignition verification"
else
    # Check if Ignition container is running
    if docker ps | grep -q "genie-at-edge-ignition"; then
        print_success "Ignition container running"
    else
        print_warning "Ignition container not running - please start: docker-compose up -d"
    fi
fi

# ============================================================================
# STEP 2: Setup Enterprise Data Tables
# ============================================================================

print_step 2 10 "Setting up enterprise data tables"

python3 databricks/simulate_enterprise_sources_sdk.py

if [ $? -eq 0 ]; then
    print_success "Enterprise data tables created"
else
    print_error "Failed to create enterprise data tables"
    exit 1
fi

# Populate remaining data
python3 databricks/populate_enterprise_data.py

# ============================================================================
# STEP 3: Setup Lakebase Serving Tables
# ============================================================================

print_step 3 10 "Setting up Lakebase serving tables"

python3 databricks/setup_lakebase_serving.py

if [ $? -eq 0 ]; then
    print_success "Lakebase serving tables created"
else
    print_warning "Lakebase setup incomplete - may require manual UI configuration"
fi

# ============================================================================
# STEP 4: Upload DLT Pipeline to Workspace
# ============================================================================

print_step 4 10 "Uploading DLT pipeline to Databricks workspace"

# Note: This requires Databricks Repos or Workspace API
# For now, print instructions
print_warning "Upload DLT pipeline manually:"
echo "  1. Go to Databricks workspace"
echo "  2. Navigate to /Users/pravin.varma@databricks.com/"
echo "  3. Upload: databricks/dlt_enrichment_pipeline.py"
echo "  4. Or use: databricks workspace import databricks/dlt_enrichment_pipeline.py /Users/pravin.varma@databricks.com/dlt_enrichment_pipeline"
echo ""
read -p "Press Enter once DLT pipeline is uploaded..."

# ============================================================================
# STEP 5: Create DLT Pipeline
# ============================================================================

print_step 5 10 "Creating Delta Live Tables pipeline"

# Create DLT pipeline using config
# Note: This requires Databricks Pipelines API
print_warning "Create DLT pipeline manually or via API:"
echo "  databricks pipelines create --json-file databricks/dlt_pipeline_config.json"
echo ""
read -p "Press Enter once DLT pipeline is created..."

# ============================================================================
# STEP 6: Start DLT Pipeline
# ============================================================================

print_step 6 10 "Starting DLT pipeline"

print_warning "Start DLT pipeline:"
echo "  1. Go to Databricks UI → Workflows → Delta Live Tables"
echo "  2. Find pipeline: genie_edge_ml_enrichment"
echo "  3. Click 'Start'"
echo "  4. Monitor until Status = Running"
echo ""
read -p "Press Enter once DLT pipeline is running..."

# ============================================================================
# STEP 7: Train Initial ML Model
# ============================================================================

print_step 7 10 "Training initial ML model"

# Note: This should be run as a Databricks job, not locally
print_warning "Train model on Databricks cluster:"
echo "  1. Upload: databricks/train_anomaly_detection_model.py to workspace"
echo "  2. Create job:"
echo "     - Name: train_anomaly_detection_initial"
echo "     - Cluster: ML Runtime 14.3 LTS"
echo "     - Task type: Python script"
echo "     - Script path: /Users/pravin.varma@databricks.com/train_anomaly_detection_model.py"
echo "  3. Run job and wait for completion"
echo ""
read -p "Press Enter once model training is complete..."

# ============================================================================
# STEP 8: Deploy Real-time Scoring Pipeline
# ============================================================================

print_step 8 10 "Deploying real-time scoring pipeline"

print_warning "Deploy scoring pipeline as streaming job:"
echo "  1. Upload: databricks/realtime_scoring_pipeline.py"
echo "  2. Create job:"
echo "     - Name: realtime_ml_scoring"
echo "     - Cluster: ML Runtime 14.3 LTS (2 workers minimum)"
echo "     - Task type: Python script"
echo "     - Script path: /Users/pravin.varma@databricks.com/realtime_scoring_pipeline.py"
echo "     - Run continuously: Yes"
echo "  3. Start job"
echo ""
read -p "Press Enter once scoring pipeline is deployed..."

# ============================================================================
# STEP 9: Setup Weekly Retraining Job
# ============================================================================

print_step 9 10 "Setting up weekly retraining job"

print_warning "Create weekly retraining job:"
echo "  1. Upload: databricks/weekly_model_retraining.py"
echo "  2. Create job:"
echo "     - Name: weekly_model_retraining"
echo "     - Cluster: ML Runtime 14.3 LTS"
echo "     - Task type: Python script"
echo "     - Script path: /Users/pravin.varma@databricks.com/weekly_model_retraining.py"
echo "     - Schedule: Cron (0 2 * * 0) - Every Sunday 2 AM"
echo "  3. Enable job"
echo ""
read -p "Press Enter once retraining job is configured..."

# ============================================================================
# STEP 10: Verify End-to-End Data Flow
# ============================================================================

print_step 10 10 "Verifying end-to-end data flow"

echo "Checking data flow..."

# Check sensor data streaming
echo ""
echo "1. Sensor data (Bronze layer):"
python3 -c "
from databricks.sdk import WorkspaceClient
import time
w = WorkspaceClient(profile='DEFAULT')
result = w.statement_execution.execute_statement(
    warehouse_id='4b9b953939869799',
    statement='SELECT COUNT(*) FROM field_engineering.ignition_streaming.sensor_events',
    wait_timeout='0s'
)
time.sleep(2)
status = w.statement_execution.get_statement(result.statement_id)
if status.status.state.value == 'SUCCEEDED' and status.result and status.result.data_array:
    count = int(status.result.data_array[0][0])
    print(f'   ✅ {count:,} sensor events ingested')
else:
    print('   ❌ Failed to query sensor data')
"

# Check enterprise tables
echo ""
echo "2. Enterprise data tables:"
python3 -c "
from databricks.sdk import WorkspaceClient
import time
w = WorkspaceClient(profile='DEFAULT')
tables = ['historian_baselines', 'mes_production_schedule', 'sap_asset_registry']
for table in tables:
    result = w.statement_execution.execute_statement(
        warehouse_id='4b9b953939869799',
        statement=f'SELECT COUNT(*) FROM field_engineering.mining_demo.{table}',
        wait_timeout='0s'
    )
    time.sleep(1)
    status = w.statement_execution.get_statement(result.statement_id)
    if status.status.state.value == 'SUCCEEDED' and status.result and status.result.data_array:
        count = int(status.result.data_array[0][0])
        print(f'   ✅ {table}: {count:,} rows')
"

# Check DLT pipeline status
echo ""
echo "3. DLT Pipeline (check manually in UI)"
echo "   URL: https://e2-demo-field-eng.cloud.databricks.com/#joblist/pipelines"
echo "   Expected status: Running"

# Check Lakebase tables
echo ""
echo "4. Lakebase serving tables:"
python3 -c "
from databricks.sdk import WorkspaceClient
import time
w = WorkspaceClient(profile='DEFAULT')
result = w.statement_execution.execute_statement(
    warehouse_id='4b9b953939869799',
    statement='SHOW TABLES IN field_engineering.lakebase',
    wait_timeout='0s'
)
time.sleep(2)
status = w.statement_execution.get_statement(result.statement_id)
if status.status.state.value == 'SUCCEEDED' and status.result and status.result.data_array:
    print('   ✅ Lakebase schema exists')
    for row in status.result.data_array[:5]:
        print(f'      - {row[1]}')
"

# Check ML model
echo ""
echo "5. ML Model registration:"
echo "   Check MLflow UI:"
echo "   URL: https://e2-demo-field-eng.cloud.databricks.com/#mlflow/models/field_engineering.ml_models.equipment_anomaly_detector"
echo "   Expected: @champion alias set"

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================

echo ""
echo "================================================================================"
echo "  ✅ ML PLATFORM DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
echo "Platform Components:"
echo "  1. ✅ Enterprise data (Historian, MES, SAP) - 8 tables"
echo "  2. ✅ Lakebase serving tables (recommendations, feedback, equipment state)"
echo "  3. ⏳ DLT pipeline (Bronze → Silver → Gold enrichment)"
echo "  4. ⏳ ML model training (Isolation Forest + Random Forest)"
echo "  5. ⏳ Real-time scoring pipeline (streaming inference)"
echo "  6. ⏳ Weekly retraining job (operator feedback loop)"
echo ""
echo "Next Steps:"
echo "  1. Configure Ignition JDBC connection to Lakebase:"
echo "     - URL: jdbc:postgresql://[lakebase-endpoint]:5432/field_engineering"
echo "     - Schema: lakebase"
echo ""
echo "  2. Create Perspective views:"
echo "     - Recommendations panel (query: recommendations_serving)"
echo "     - Equipment dashboard (query: hmi_dashboard)"
echo "     - Operator feedback buttons (Execute/Defer/Ask AI)"
echo ""
echo "  3. Set up PG NOTIFY webhook listener in Ignition"
echo ""
echo "  4. Test complete workflow:"
echo "     - Sensor → Anomaly detection → Recommendation → Operator action → Feedback"
echo ""
echo "Documentation:"
echo "  - Architecture: https://pravinva.github.io/genie-edge-demo/"
echo "  - Setup guide: databricks/ML_PLATFORM_README.md"
echo ""
echo "================================================================================"
