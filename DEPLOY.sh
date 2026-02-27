#!/bin/bash
# Quick deployment script for Field Engineering workspace setup

echo "=========================================="
echo "GENIE AT THE EDGE - DEPLOYMENT"
echo "=========================================="

# Check if databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "❌ Databricks CLI not found. Install with: pip install databricks-cli"
    exit 1
fi

echo "✓ Databricks CLI found"

# Set workspace path
WORKSPACE_PATH="/Users/pravin.varma@databricks.com/genie-at-edge"

echo ""
echo "Uploading setup script to workspace..."
databricks workspace import \
    databricks/setup_field_eng_workspace.py \
    ${WORKSPACE_PATH}/setup_field_eng_workspace.py \
    --language PYTHON \
    --overwrite

if [ $? -eq 0 ]; then
    echo "✓ Setup script uploaded"
else
    echo "❌ Failed to upload setup script"
    exit 1
fi

echo ""
echo "Uploading unified pipeline..."
databricks workspace import \
    databricks/unified_data_architecture.py \
    ${WORKSPACE_PATH}/unified_data_architecture.py \
    --language PYTHON \
    --overwrite

if [ $? -eq 0 ]; then
    echo "✓ Unified pipeline uploaded"
else
    echo "❌ Failed to upload pipeline"
    exit 1
fi

echo ""
echo "=========================================="
echo "NEXT STEPS:"
echo "=========================================="
echo ""
echo "1. Run setup in Databricks:"
echo "   https://e2-demo-field-eng.cloud.databricks.com/"
echo "   Navigate to: ${WORKSPACE_PATH}/setup_field_eng_workspace"
echo "   Click 'Run All'"
echo ""
echo "2. This will create:"
echo "   • Lakebase catalog with Historian tables"
echo "   • Field Engineering catalog with streaming data"
echo "   • SAP/MES simulation tables"
echo "   • 30 days of historical data"
echo "   • 1 hour of real-time streaming data"
echo ""
echo "3. Verify with sample query:"
echo "   SELECT * FROM lakebase.ignition_historian.sqlth_te;"
echo ""
echo "4. Deploy DLT pipeline:"
echo "   Create new DLT pipeline in UI"
echo "   Add notebook: ${WORKSPACE_PATH}/unified_data_architecture"
echo ""
echo "=========================================="
echo "✅ Files uploaded successfully!"
echo "=========================================="