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
    ${WORKSPACE_PATH}/setup_field_eng_workspace.py \
    --file databricks/setup_field_eng_workspace.py \
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
    ${WORKSPACE_PATH}/unified_data_architecture.py \
    --file databricks/unified_data_architecture.py \
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
echo "✅ Files uploaded successfully!"
echo "=========================================="