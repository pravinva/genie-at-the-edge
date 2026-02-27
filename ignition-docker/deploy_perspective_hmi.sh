#!/bin/bash

echo "======================================"
echo "DEPLOYING PERSPECTIVE HMI TO IGNITION"
echo "======================================"

# Configuration
IGNITION_HOST="localhost"
IGNITION_PORT="8088"
GATEWAY_URL="http://${IGNITION_HOST}:${IGNITION_PORT}"

# Colors for output
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "Target Gateway: ${GATEWAY_URL}"
echo ""

# Function to check if Ignition is running
check_ignition() {
    echo -n "Checking Ignition Gateway status... "
    if curl -s "${GATEWAY_URL}/StatusPing" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Online${NC}"
        return 0
    else
        echo -e "${RED}✗ Offline${NC}"
        echo ""
        echo "Please ensure Ignition is running at ${GATEWAY_URL}"
        echo "You can start it with: docker-compose up -d"
        return 1
    fi
}

# Function to import Perspective resources
import_perspective_resources() {
    echo ""
    echo "📦 IMPORTING PERSPECTIVE RESOURCES"
    echo "=================================="

    # Copy files to Ignition data directory (assuming Docker volume)
    IGNITION_DATA="/ignition-data"

    if [ -d "../docker/ignition-data" ]; then
        IGNITION_DATA="../docker/ignition-data"
    elif [ -d "./ignition-data" ]; then
        IGNITION_DATA="./ignition-data"
    else
        echo -e "${ORANGE}Warning: Could not find ignition-data directory${NC}"
        echo "Please manually import the following files:"
        echo ""
    fi

    # List files to import
    echo ""
    echo "📁 Files to Import:"
    echo "==================="
    echo ""
    echo "1. PERSPECTIVE VIEW:"
    echo "   • perspective-views/MainOperationsView.json"
    echo "   → Import via Designer: Perspective → Views → Import"
    echo ""
    echo "2. STYLES:"
    echo "   • perspective-views/styles.json"
    echo "   → Import via Designer: Perspective → Styles → Import"
    echo ""
    echo "3. SPARKLINE COMPONENT:"
    echo "   • perspective-views/TrendSparkline.json"
    echo "   → Import via Designer: Perspective → Components → Import"
    echo ""
    echo "4. WEBDEV MODULE:"
    echo "   • webdev-modules/genie_chat.py"
    echo "   → Import via Gateway: Config → WebDev → Create New Resource"
    echo ""
    echo "5. EVENT HANDLERS:"
    echo "   • scripts/perspective_event_handlers.py"
    echo "   → Import via Designer: Scripting → Project Library"
    echo ""

    # Create import package
    echo "📦 Creating Import Package..."
    mkdir -p import_package/{views,styles,components,scripts,webdev}

    cp perspective-views/MainOperationsView.json import_package/views/
    cp perspective-views/styles.json import_package/styles/
    cp perspective-views/TrendSparkline.json import_package/components/
    cp scripts/perspective_event_handlers.py import_package/scripts/
    cp webdev-modules/genie_chat.py import_package/webdev/

    # Create README for import
    cat > import_package/README.md << 'EOF'
# Perspective HMI Import Instructions

## Quick Import Steps

### 1. Open Ignition Designer
- Launch Designer from Gateway webpage
- Connect to your project

### 2. Import Perspective View
- Navigate to: Perspective → Views
- Right-click → Import
- Select: `views/MainOperationsView.json`
- Name it: "MainOperations/Dashboard"

### 3. Import Styles
- Navigate to: Perspective → Styles
- Click Import button
- Select: `styles/styles.json`

### 4. Import Custom Component
- Navigate to: Perspective → Components
- Right-click → Import Component
- Select: `components/TrendSparkline.json`

### 5. Import Scripts
- Navigate to: Scripting → Project Library
- Create new script: "perspective_handlers"
- Copy content from: `scripts/perspective_event_handlers.py`

### 6. Configure WebDev (Gateway)
- Open Gateway Config page
- Navigate to: Config → WebDev
- Create new Python resource: "genie_chat"
- Copy content from: `webdev/genie_chat.py`

### 7. Create Required Tags
Run this script in Script Console:

```python
# Create tag structure
base_paths = [
    "[default]Equipment/HaulTruck_001",
    "[default]Equipment/Crusher_001",
    "[default]Equipment/Crusher_002",
    "[default]Equipment/Conveyor_001",
    "[default]Equipment/Conveyor_002",
    "[default]Predictions/Anomalies",
    "[default]Predictions/Maintenance",
    "[default]AI/Recommendations/Active",
    "[default]HMI",
    "[default]Genie",
    "[default]Databricks"
]

for path in base_paths:
    system.tag.configure(path, {}, "o")
    print(f"Created: {path}")

# Configure Databricks connection
system.tag.write("[default]Databricks/Host", "your-workspace.databricks.com")
system.tag.write("[default]Databricks/Token", "your-token")
system.tag.write("[default]Databricks/GenieSpaceId", "your-space-id")
```

### 8. Test the View
- Create new Perspective session
- Navigate to: /MainOperations/Dashboard
- Verify all components load correctly

## Styling Notes
- Font: Share Tech Mono (will fallback to monospace if not available)
- Primary Color: #00ff00 (green)
- Alert Color: #ff6b00 (orange)
- Background: #0d0d0d (dark)

## Troubleshooting
- If styles don't apply: Check Perspective → Project Properties → Stylesheets
- If WebDev doesn't work: Ensure Python scripting is enabled in Gateway
- If tags are missing: Run the tag creation script above
EOF

    echo -e "${GREEN}✓ Import package created${NC}"
    echo ""
    echo "📂 Package Location: ./import_package/"
    echo ""
}

# Function to create test data generator
create_test_data() {
    echo "🔧 CREATING TEST DATA GENERATOR"
    echo "================================"

    cat > import_package/scripts/generate_test_data.py << 'EOF'
"""
Test Data Generator for Perspective HMI
Run this in Script Console to generate test data
"""

import random
import system.date

def generate_test_data():
    """Generate test data for all equipment"""

    equipment_list = [
        "HaulTruck_001",
        "Crusher_001",
        "Crusher_002",
        "Conveyor_001",
        "Conveyor_002"
    ]

    for equipment in equipment_list:
        base_path = f"[default]Equipment/{equipment}"

        # Generate random status
        status_options = ["Running", "Running", "Running", "Idle", "Warning", "Maintenance"]
        status = random.choice(status_options)

        # Generate temperature (60-95°C)
        temperature = random.uniform(60, 95)

        # Generate flow rate (100-500 m³/h)
        flow_rate = random.uniform(100, 500)

        # Write tags
        system.tag.write(f"{base_path}/Status", status)
        system.tag.write(f"{base_path}/Temperature", temperature)
        system.tag.write(f"{base_path}/FlowRate", flow_rate)

        # Generate anomaly scores
        if status == "Warning":
            anomaly_score = random.uniform(0.7, 0.9)
        elif status == "Maintenance":
            anomaly_score = random.uniform(0.8, 1.0)
        else:
            anomaly_score = random.uniform(0.1, 0.4)

        system.tag.write(f"[default]Predictions/Anomalies/{equipment}", anomaly_score)

        # Generate maintenance prediction
        if anomaly_score > 0.7:
            maintenance = "Required"
        elif anomaly_score > 0.5:
            maintenance = "Scheduled"
        else:
            maintenance = "Not Required"

        system.tag.write(f"[default]Predictions/Maintenance/{equipment}", maintenance)

        print(f"Generated data for {equipment}: Status={status}, Temp={temperature:.1f}°C, Anomaly={anomaly_score:.2f}")

    # Generate a sample AI recommendation
    create_sample_recommendation()

    print("\n✓ Test data generation complete!")

def create_sample_recommendation():
    """Create a sample AI recommendation"""

    import uuid
    rec_id = str(uuid.uuid4())[:8]
    rec_path = f"[default]AI/Recommendations/Active/{rec_id}"

    recommendations = [
        {
            "content": "Recommend reducing Crusher_001 speed by 15% to prevent bearing wear",
            "equipment": "Crusher_001",
            "type": "ADJUST_SETPOINT",
            "confidence": 0.89
        },
        {
            "content": "Schedule maintenance for Conveyor_002 within next 48 hours",
            "equipment": "Conveyor_002",
            "type": "SCHEDULE_MAINTENANCE",
            "confidence": 0.92
        },
        {
            "content": "Optimize HaulTruck_001 route to reduce cycle time by 3 minutes",
            "equipment": "HaulTruck_001",
            "type": "OPERATIONAL",
            "confidence": 0.76
        }
    ]

    rec = random.choice(recommendations)

    system.tag.write(f"{rec_path}/Id", rec_id)
    system.tag.write(f"{rec_path}/Content", rec["content"])
    system.tag.write(f"{rec_path}/Equipment", rec["equipment"])
    system.tag.write(f"{rec_path}/ActionType", rec["type"])
    system.tag.write(f"{rec_path}/Confidence", rec["confidence"])
    system.tag.write(f"{rec_path}/Status", "Pending")
    system.tag.write(f"{rec_path}/Timestamp", system.date.now())

    print(f"Created recommendation: {rec['content']}")

# Run the generator
generate_test_data()
EOF

    echo -e "${GREEN}✓ Test data generator created${NC}"
}

# Function to create launcher HTML
create_launcher() {
    echo ""
    echo "🚀 CREATING LAUNCHER"
    echo "==================="

    cat > import_package/launch_hmi.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Launch Perspective HMI</title>
    <style>
        body {
            font-family: 'Share Tech Mono', monospace;
            background: #0d0d0d;
            color: #00ff00;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .launcher {
            text-align: center;
            padding: 40px;
            border: 1px solid #00ff00;
            border-radius: 10px;
            background: rgba(0,255,0,0.05);
        }
        h1 {
            margin-bottom: 30px;
            text-shadow: 0 0 10px rgba(0,255,0,0.5);
        }
        .btn {
            display: inline-block;
            padding: 15px 40px;
            margin: 10px;
            border: 2px solid #00ff00;
            background: transparent;
            color: #00ff00;
            text-decoration: none;
            border-radius: 5px;
            font-size: 18px;
            transition: all 0.3s;
        }
        .btn:hover {
            background: rgba(0,255,0,0.1);
            box-shadow: 0 0 20px rgba(0,255,0,0.5);
            transform: scale(1.05);
        }
        .info {
            margin-top: 30px;
            padding: 20px;
            background: rgba(255,107,0,0.1);
            border: 1px solid #ff6b00;
            border-radius: 5px;
        }
        .info h3 {
            color: #ff6b00;
            margin-top: 0;
        }
    </style>
</head>
<body>
    <div class="launcher">
        <h1>🚀 Perspective HMI with Embedded AI</h1>

        <a href="http://localhost:8088/data/perspective/client/MainOperations/Dashboard"
           class="btn" target="_blank">
            Launch Perspective View
        </a>

        <a href="http://localhost:8088/"
           class="btn" target="_blank">
            Open Gateway
        </a>

        <div class="info">
            <h3>Quick Setup Checklist:</h3>
            <ul style="text-align: left; display: inline-block;">
                <li>✓ Ignition Gateway running on port 8088</li>
                <li>✓ Perspective module installed</li>
                <li>✓ Views and styles imported</li>
                <li>✓ WebDev module configured</li>
                <li>✓ Test data generated</li>
            </ul>
        </div>
    </div>
</body>
</html>
EOF

    echo -e "${GREEN}✓ Launcher created${NC}"
}

# Main execution
echo ""
echo "🚀 Starting Deployment Process..."
echo ""

# Check if Ignition is running
if ! check_ignition; then
    echo ""
    echo -e "${RED}Deployment aborted. Please start Ignition first.${NC}"
    exit 1
fi

# Import resources
import_perspective_resources

# Create test data generator
create_test_data

# Create launcher
create_launcher

echo ""
echo "======================================"
echo -e "${GREEN}✅ DEPLOYMENT PACKAGE READY!${NC}"
echo "======================================"
echo ""
echo "📋 NEXT STEPS:"
echo "============="
echo ""
echo "1. Open Ignition Designer:"
echo "   ${GATEWAY_URL} → Launch Designer"
echo ""
echo "2. Import components:"
echo "   Follow instructions in: import_package/README.md"
echo ""
echo "3. Generate test data:"
echo "   Run script: import_package/scripts/generate_test_data.py"
echo ""
echo "4. Launch the HMI:"
echo "   Open: import_package/launch_hmi.html"
echo ""
echo "📦 All files are in: ./import_package/"
echo ""
echo -e "${ORANGE}Note: The view will look exactly like the HTML demo,${NC}"
echo -e "${ORANGE}with the same dark theme, green text, and AI panel layout.${NC}"
echo ""