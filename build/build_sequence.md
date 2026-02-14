# Build Sequence Guide

Complete step-by-step guide for building and deploying the Mining Operations Genie Demo.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Deployment Sequence](#deployment-sequence)
5. [Component Details](#component-details)
6. [Validation](#validation)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IGNITION EDGE GATEWAY                     │
│                                                              │
│  UDTs → Memory Tags → Gateway Scripts → Perspective View    │
│                                │                             │
│                          Zerobus Module                      │
└──────────────────────────────┼───────────────────────────────┘
                                │ (500ms batches)
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATABRICKS LAKEHOUSE                       │
│                                                              │
│  Bronze (Raw) → Silver (Clean) → Gold (Aggregated)          │
│  DLT Pipeline (<3s latency)                                 │
│                                │                             │
│                      Genie Space (NLP)                       │
└──────────────────────────────┼───────────────────────────────┘
                                │ (<5s response)
                                ▼
                           Chat UI (HTML5)
```

### Timeline

- **Automated Deployment**: 30 minutes (Databricks + UI upload)
- **Manual Configuration**: 2-3 hours (Ignition setup)
- **Testing & Validation**: 1 hour
- **Total**: 4-5 hours for complete working system

---

## Prerequisites

### Software Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Deployment automation |
| Ignition | 8.1+ | Edge gateway and HMI |
| Databricks | Runtime 16.4+ | Data processing and ML |
| Web Browser | Modern (Chrome/Edge) | UI testing |

### Access Requirements

- [x] Databricks workspace access (Field Engineering)
- [x] Personal access token with admin privileges
- [x] Ignition Gateway with admin credentials
- [x] Network connectivity: Ignition ↔ Databricks

### Knowledge Prerequisites

- Basic Python scripting
- Familiarity with Ignition Designer
- Understanding of SQL and data pipelines
- Comfort with terminal/command line

---

## Environment Setup

### 1. Clone Repository

```bash
cd ~/Documents/Demo
git clone <repository-url> genie-at-the-edge
cd genie-at-the-edge
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd build
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Set Databricks token
export DATABRICKS_TOKEN=dapi1234567890abcdef

# Optional: Set Ignition credentials (if different from defaults)
export IGNITION_USERNAME=admin
export IGNITION_PASSWORD=password

# Verify
echo $DATABRICKS_TOKEN | head -c 20
```

### 4. Validate Configuration

```bash
# Run prerequisites check
python deploy_all.py --check-only

# Should show all green checkmarks
```

Expected output:
```
Prerequisites Check
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component              ┃ Status   ┃ Details                 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Python version         │ ✓ PASS   │ 3.12.x                  │
│ Python dependencies    │ ✓ PASS   │ All required packages   │
│ DATABRICKS_TOKEN       │ ✓ PASS   │ Set                     │
│ Configuration file     │ ✓ PASS   │ environment_config.yaml │
│ Databricks directory   │ ✓ PASS   │ ../databricks           │
│ Ignition directory     │ ✓ PASS   │ ../ignition             │
│ UI directory           │ ✓ PASS   │ ../ui                   │
└────────────────────────┴──────────┴─────────────────────────┘
```

---

## Deployment Sequence

### Phase 1: Automated Databricks Deployment (20 min)

Deploy Databricks components using automation:

```bash
cd build
python deploy_databricks.py --environment dev
```

**What this does**:
1. Validates workspace access
2. Creates catalog and schema (if needed)
3. Starts SQL warehouse
4. Deploys dimension tables
5. Uploads DLT pipeline notebook
6. Creates or updates DLT pipeline
7. Starts pipeline in Real-Time mode
8. Runs validation queries

**Expected output**:
```
Mining Operations Genie Demo
Databricks Deployment - Environment: DEV

✓ Connected to Databricks workspace
✓ Catalog exists: field_engineering
✓ Schema exists: field_engineering.mining_demo
✓ Warehouse running: 4b9b953939869799

Deploying Dimension Tables
✓ Dimension tables deployed

Deploying DLT Pipeline
✓ Uploaded pipeline notebook
✓ DLT pipeline deployed: abc123def456
✓ Pipeline started

✓ Deployment Complete!
```

**Validation**:
```sql
-- In Databricks SQL Editor
USE field_engineering.mining_demo;

-- Check tables exist
SHOW TABLES;
-- Should show: equipment_master, equipment_types, etc.

-- Check pipeline status
-- Go to: Workflows > Delta Live Tables
-- Pipeline: mining_realtime_pipeline
-- Status: Should be "Running"
```

### Phase 2: UI Deployment (10 min)

Deploy chat UI to Databricks Files:

```bash
python deploy_ui.py --environment dev
```

**What this does**:
1. Validates UI files exist
2. Uploads HTML file to Databricks Files
3. Generates public URL
4. Creates Genie integration configuration
5. Creates Perspective integration guide

**Expected output**:
```
UI Deployment - Environment: DEV

Validating UI Files
✓ Found: genie_chat_perspective.html (45,231 bytes)

Uploading UI to Databricks Files
✓ Created directory: /Volumes/field_engineering/mining_demo/files/ui
✓ Uploaded successfully

Chat UI URL:
https://field-eng.cloud.databricks.com/files/Volumes/field_engineering/mining_demo/files/ui/genie_chat_perspective.html

✓ Configuration saved to: genie_integration_config_dev.md
✓ Integration guide saved to: perspective_integration_guide_dev.md
```

**Save the URL** - you'll need it for Perspective view configuration.

### Phase 3: Genie Space Creation (10 min - Manual)

Create Genie space via Databricks UI:

1. Open Databricks workspace
2. Navigate to: **AI & ML > Genie**
3. Click **"Create Genie Space"**
4. Configure:
   - **Name**: Mining Operations Intelligence
   - **Catalog**: field_engineering
   - **Schema**: mining_demo
   - **Warehouse**: 4b9b953939869799
5. Click **"Create"**
6. Add instructions (copy from `databricks/pipelines/genie_space_setup.sql`)
7. Add sample questions:
   - "Show me current status of all crushers"
   - "Why is Crusher 2 vibration high?"
   - "Compare Crusher 2 to other crushers"
   - "Show production for last hour"
   - "Which equipment has anomalies?"
8. Click **"Save"**
9. **Copy the Space ID** (from URL: `/genie/spaces/<space-id>`)

**Test Genie**:
- Type: "Show me current crusher status"
- Should respond in <5 seconds
- If no data yet, that's OK (data comes in Phase 4)

### Phase 4: Ignition Deployment (2-3 hours - Manual)

Deploy Ignition components following the generated checklist:

```bash
python deploy_ignition.py --environment dev
```

This generates a comprehensive checklist. Follow it step-by-step:

#### 4.1 Import UDTs (30 min)

1. Open **Ignition Designer**
2. Connect to gateway
3. Navigate to: **Tag Browser > Data Types**
4. Right-click > **Import > JSON**
5. Import each file from `ignition/udts/`:
   - `HaulTruck_UDT.json`
   - `Crusher_UDT.json`
   - `Conveyor_UDT.json`
6. Verify UDTs appear in Data Types folder

#### 4.2 Create Tag Instances (30 min)

**Option A - Script** (recommended):
```bash
cd ../ignition/udts
python create_tag_instances.py
```

**Option B - Manual**:
1. In Designer Tag Browser
2. Right-click **[default]** > **New Folder**: "Mining"
3. Right-click **Mining** > **New Folder**: "Equipment"
4. For each equipment:
   - Right-click **Equipment** > **New Tag** > **UDT Instance**
   - Select appropriate UDT type
   - Name: HT_001, HT_002, ..., CR_001, ..., CV_001, ...
   - Total: 5 trucks, 3 crushers, 2 conveyors

**Validation**:
- Count tags: Should be 105 total
- All tags should have initial values (0 or default)

#### 4.3 Configure Alarms (15 min)

1. Navigate to: **CR_001/Vibration_MM_S**
2. Double-click tag to edit
3. **Alarms tab** > **Add Alarm**
4. Configure:
   - **Type**: Value Above
   - **Threshold**: 40
   - **Priority**: High
   - **Alarm Name**: "High Vibration"
5. Repeat for CR_002, CR_003
6. Test:
   - Right-click tag > **Edit Tag**
   - Set value to 45
   - Verify alarm fires in Alarm Status Table

#### 4.4 Deploy Gateway Scripts (30 min)

1. Open **Gateway Webpage**: http://localhost:8088
2. Login with admin credentials
3. Navigate to: **Config > Scripting > Gateway Event Scripts**
4. Click **Create new Timer Script**

**Script 1: Physics Simulation**
- **Name**: Mining Physics Simulation
- **Script Type**: Gateway Timer Script
- **Interval**: 1000 (ms)
- **Delay**: 0
- **Script**: Copy from `ignition/scripts/mining_physics_simulation.py`
- **Enabled**: Yes

**Script 2: Fault Injection**
- **Name**: Fault Injection CR002
- **Script Type**: Gateway Timer Script
- **Interval**: 1000 (ms)
- **Delay**: 500
- **Script**: Copy from `ignition/scripts/fault_injection_cr002.py`
- **Enabled**: Yes (or wait until demo time)

5. Click **Save Changes**
6. Navigate to: **Status > Gateway Scripting**
7. Verify scripts show "Running"

**Validation**:
- Open **Tag Browser**
- Watch tags update every second
- Values should be realistic and changing
- Check Gateway logs for errors: **Status > Diagnostics > Logs**

#### 4.5 Configure Zerobus Streaming (30 min)

1. In Gateway webpage: **Config > Zerobus** (or your streaming module)
2. Click **Add Connection**
3. Configure:
   - **Name**: Databricks Mining Demo
   - **Workspace URL**: https://field-eng.cloud.databricks.com
   - **Token**: (paste DATABRICKS_TOKEN)
   - **Stream Name**: mining_ot_stream
   - **Target Table**: field_engineering.mining_demo.ot_telemetry_bronze
4. Configure **Tag Selection**:
   - **Provider**: [default]
   - **Tag Path**: Mining/Equipment/**/*
   - **Include children**: Yes
5. Configure **Streaming Settings**:
   - **Batch Size**: 50
   - **Interval**: 500 (ms)
   - **Format**: JSON
6. Check **Enabled**
7. Click **Save**

**Validation**:
```sql
-- In Databricks, after 2-3 minutes
SELECT COUNT(*) as record_count,
       MAX(timestamp) as latest_data
FROM field_engineering.mining_demo.ot_telemetry_bronze;

-- Should have hundreds of records
-- latest_data should be within last minute
```

If no data:
- Check Gateway logs for Zerobus errors
- Verify network connectivity
- Verify token permissions
- Verify tag path is correct

#### 4.6 Create Perspective View (60 min)

See detailed guide: `build/perspective_integration_guide_dev.md`

**Quick steps**:

1. In Designer, create **Perspective Project**: "MiningOperations"
2. Create **View**: "MiningOperationsDashboard"
3. Add **Session Startup Script** (configure custom properties)
4. Design view layout:
   - **Header**: Title and status indicators
   - **Left Panel (70%)**: Equipment status cards
   - **Right Panel (30%)**: Embedded Frame (chat UI)
   - **Bottom**: Alarm table with "Ask AI" buttons
5. Configure **Embedded Frame**:
   - **URL**: `{{session.custom.genie_chat_url}}`
   - **Sandbox**: Allow scripts, Allow same origin
6. Bind equipment cards to tags:
   - CR_002/Vibration → Display value + color indicator
7. Add **"Ask AI" buttons** to alarm table:
   - onClick script updates session.custom.pending_question
8. Save and publish project

**Validation**:
- Open Perspective Session in browser
- Verify equipment status displays
- Verify chat UI loads in iframe
- Type test question in chat
- Verify Genie responds

### Phase 5: Master Deployment (Optional)

Or run everything in one command:

```bash
python deploy_all.py --environment dev
```

This orchestrates all automated steps and generates all checklists/guides.

---

## Component Details

### Databricks Components

#### Dimension Tables

Static reference data:

- **equipment_master**: 15 equipment records (metadata)
- **equipment_types**: 3 types (HaulTruck, Crusher, Conveyor)
- **shift_calendar**: Shift schedules
- **maintenance_history**: Historical maintenance records

#### DLT Pipeline

Three-layer architecture:

**Bronze Layer** (Raw Data):
- Table: `ot_telemetry_bronze`
- Source: Zerobus stream from Ignition
- Schema: JSON with tag_path, value, timestamp, quality
- Updates: Real-time streaming

**Silver Layer** (Normalized):
- Table: `ot_telemetry_silver`
- Transformation: Parse tag paths, type conversion, quality filtering
- Schema: Structured columns per equipment type
- Updates: <1s after bronze

**Gold Layer** (Aggregated):
- Table: `equipment_performance_1min`
- Aggregation: 1-minute windows with statistics
- Schema: Equipment_id, metrics, aggregations
- Updates: <1s after silver
- Additional gold tables:
  - `production_summary`
  - `ml_predictions`
  - `anomaly_alerts`

#### Genie Space

Natural language query interface:

- **Name**: Mining Operations Intelligence
- **Tables**: All gold tables + dimension tables
- **Warehouse**: Configured warehouse ID
- **Instructions**: Mining-specific terminology and patterns
- **Sample Questions**: Pre-configured common queries
- **Response Time**: <5s target

### Ignition Components

#### UDTs (User Defined Types)

**HaulTruck** (14 members):
- Location: lat, lon, altitude
- Status: speed, load_tons, fuel_level
- State: operating_state (loading, hauling, dumping, returning)

**Crusher** (9 members):
- Performance: throughput, power_draw, vibration
- State: operational_status, run_hours

**Conveyor** (4 members):
- Status: belt_speed, material_flow
- State: running

#### Gateway Scripts

**Physics Simulation**:
- Updates all 105 tags every second
- Simulates realistic equipment behavior
- Haul truck cycle: 5 minutes (loading → hauling → dumping → returning)
- Crusher: Stable operation with minor variations
- Conveyor: Constant speed with flow variations

**Fault Injection**:
- Targets CR_002 (Crusher 2)
- Starts after 30 minutes (configurable)
- Gradually increases vibration: 20 → 60 mm/s over 10 minutes
- Simulates bearing degradation pattern
- Triggers high vibration alarm at threshold (40 mm/s)

#### Perspective View

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: Mining Operations Dashboard          [Status Icons] │
├─────────────────────────────────┬───────────────────────────┤
│                                 │                           │
│  EQUIPMENT STATUS (70%)         │   GENIE CHAT (30%)        │
│                                 │                           │
│  ┌─────────────────────────┐   │  ┌─────────────────────┐  │
│  │  Crusher 1              │   │  │ Chat Interface      │  │
│  │  Vibration: 25 mm/s     │   │  │ [iframe]            │  │
│  │  Status: Normal         │   │  │                     │  │
│  └─────────────────────────┘   │  │                     │  │
│                                 │  │                     │  │
│  ┌─────────────────────────┐   │  │                     │  │
│  │  Crusher 2              │   │  │                     │  │
│  │  Vibration: 45 mm/s     │   │  │                     │  │
│  │  Status: ⚠ High Vib     │   │  │                     │  │
│  └─────────────────────────┘   │  └─────────────────────┘  │
│                                 │                           │
│  [More equipment cards...]      │                           │
│                                 │                           │
├─────────────────────────────────┴───────────────────────────┤
│ ALARMS:                                                     │
│ Crusher 2 High Vibration  |  [Ask AI]  |  10:34 AM         │
└─────────────────────────────────────────────────────────────┘
```

### UI Component

**genie_chat_perspective.html**:

- Pure HTML5/CSS/JavaScript (no framework dependencies)
- Styled to match Perspective dark theme
- Features:
  - Message input with send button
  - Chat history with user/assistant styling
  - Loading indicators
  - Error handling with retry
  - Suggested questions (context-aware)
  - SQL display toggle
  - Responsive design
- Integration:
  - URL parameters: token, workspace, space
  - Pre-filled questions via URL parameter
  - Embedded in Perspective iframe

---

## Validation

### Level 1: Component Validation

Test each component individually:

#### Ignition Tags
```bash
# In Designer Script Console
tags = system.tag.browseTags('[default]Mining/Equipment', recursive=True)
print(f"Total tags: {len(tags)}")

# Watch a tag for 10 seconds
for i in range(10):
    value = system.tag.readBlocking(['[default]Mining/Equipment/CR_002/Vibration_MM_S'])[0].value
    print(f"Vibration: {value}")
    system.util.invokeLater(lambda: None, 1000)
```

Expected: Values change every second, realistic range (20-30 mm/s)

#### Databricks Tables
```sql
-- Check data flow
SELECT
    'bronze' as layer,
    COUNT(*) as records,
    MAX(timestamp) as latest
FROM field_engineering.mining_demo.ot_telemetry_bronze
UNION ALL
SELECT 'silver', COUNT(*), MAX(timestamp)
FROM field_engineering.mining_demo.ot_telemetry_silver
UNION ALL
SELECT 'gold', COUNT(*), MAX(window_start)
FROM field_engineering.mining_demo.equipment_performance_1min;
```

Expected:
- Bronze: Thousands of records, latest within 1 minute
- Silver: Similar to bronze, <1s lag
- Gold: Aggregated records, <1s lag

#### Genie Space
Test queries in Databricks UI:
1. "Show me current crusher status"
2. "Why is Crusher 2 vibration high?"
3. "Compare Crusher 2 to other crushers"

Expected: Responses in <5s, accurate data, natural language explanations

#### Chat UI
Open URL directly in browser with parameters:
```
https://field-eng.cloud.databricks.com/files/.../genie_chat_perspective.html?token=YOUR_TOKEN&workspace=WORKSPACE_ID&space=SPACE_ID
```

Test: Type "Show me current status"
Expected: Response within 5 seconds, no errors

### Level 2: Integration Validation

Test component interactions:

#### Ignition → Databricks
1. In Ignition, set CR_002/Vibration to 50
2. Wait 10 seconds
3. Query Databricks:
```sql
SELECT * FROM field_engineering.mining_demo.equipment_performance_1min
WHERE equipment_id = 'CR_002'
ORDER BY window_start DESC
LIMIT 1;
```

Expected: Vibration value shows ~50 in latest window

#### Databricks → Genie → UI
1. Open Perspective session
2. Type question: "What is Crusher 2 vibration?"
3. Measure response time

Expected: Response within 5 seconds, shows current value

### Level 3: End-to-End Validation

Complete user workflow:

#### Scenario: High Vibration Alert

1. **Trigger**: Set CR_002/Vibration to 45 (above 40 threshold)
2. **Alert**: Alarm fires in Ignition
3. **Notification**: Alarm appears in Perspective alarm table
4. **Investigation**: Operator clicks "Ask AI" button
5. **Diagnosis**: Chat pre-fills question: "Why is Crusher 2 vibration high?"
6. **Response**: Genie responds with diagnosis and recommendations
7. **Action**: Operator follows recommendations

**Measure latency at each step**:
- Tag change → Alarm: <1s
- Alarm → UI display: <1s
- Click → Chat question: <1s
- Question → Genie: <5s
- **Total: <10s**

**Target: <15s end-to-end**

### Level 4: Performance Validation

Long-running stability test:

```bash
# Run for 1-2 hours
python build/run_stability_test.py --duration 7200 --environment dev
```

Monitors:
- Tag update frequency (should be consistent 1 Hz)
- Data flow rate (should be steady ~100 records/sec)
- DLT latency (should stay <3s)
- Query response time (should stay <5s)
- Memory usage (should be stable)
- Error rate (should be near 0%)

### Level 5: Demo Rehearsal

Practice actual demo:

1. Start with clean state (reset CR_002 vibration to normal)
2. Run physics simulation for 5 minutes (observe normal operation)
3. Enable fault injection
4. Wait 30 minutes (or adjust script for faster fault)
5. Watch vibration increase gradually
6. Alarm fires at 40 mm/s
7. Click "Ask AI" → Get instant diagnosis
8. Ask follow-up questions
9. Show latency (<15s total)
10. Explain architecture

**Record demo video** as backup in case live demo fails.

---

## Troubleshooting

### Common Issues

#### 1. No Data in Databricks

**Symptoms**:
- Bronze table empty or not updating
- Query returns 0 rows

**Diagnosis**:
```sql
SELECT COUNT(*), MAX(timestamp)
FROM field_engineering.mining_demo.ot_telemetry_bronze;
```

If timestamp is old or count is 0:

**Check Ignition**:
- Are tags updating? (watch in Tag Browser)
- Are Gateway scripts running? (Status > Gateway Scripting)
- Is Zerobus enabled? (Config > Zerobus)
- Any errors in Gateway logs? (Status > Diagnostics > Logs)

**Check Databricks**:
- Is stream created? (check Zerobus config)
- Does token have permissions? (try query manually)
- Network connectivity? (can Ignition reach Databricks?)

**Fix**:
1. Verify tag updates: `[default]Mining/Equipment/CR_001/Speed_KPH`
2. Check Zerobus logs in Gateway
3. Test connectivity: `curl https://field-eng.cloud.databricks.com`
4. Verify token: Run simple query in Databricks with token
5. Restart Zerobus: Disable → Save → Enable → Save

#### 2. DLT Pipeline Errors

**Symptoms**:
- Pipeline shows "Failed" status
- Red errors in pipeline graph

**Diagnosis**:
- Open Databricks > Workflows > Delta Live Tables
- Click pipeline name
- Check error messages

**Common errors**:

**"Table not found"**:
Fix: Deploy dimension tables: `python deploy_databricks.py --component tables`

**"Schema mismatch"**:
Fix: Check JSON format from Zerobus, adjust expectations in DLT code

**"Resource exhausted"**:
Fix: Increase cluster size in pipeline settings

**"Timeout"**:
Fix: Check if bronze table has too much data, add filters

**Fix**:
1. Stop pipeline
2. Fix underlying issue
3. Restart pipeline
4. Monitor for 5 minutes

#### 3. Genie Not Responding

**Symptoms**:
- Chat shows loading forever
- Error: "Failed to get response"

**Diagnosis**:
- Open browser dev tools (F12) > Console
- Look for error messages

**Common errors**:

**401 Unauthorized**:
Fix: Token invalid, regenerate and update

**403 Forbidden**:
Fix: Token doesn't have SQL execution permission, check token scopes

**404 Not Found**:
Fix: Space ID incorrect, verify in Databricks UI URL

**Timeout**:
Fix: Warehouse is cold, keep it running during demo

**Fix**:
1. Verify space ID: Open Genie in Databricks UI, check URL
2. Test query manually: Try same question in Databricks Genie UI
3. Check warehouse: Is it running? Start it if needed
4. Verify token: Generate new token with correct permissions

#### 4. Chat UI Not Loading in Iframe

**Symptoms**:
- Blank iframe in Perspective view
- Console error: "Refused to display in a frame"

**Diagnosis**:
- Open URL directly in browser (outside iframe)
- Check browser console for errors

**Common errors**:

**CORS error**:
Fix: Verify file is in Databricks Files (not Repos), Files allow iframe embedding

**URL not accessible**:
Fix: Check URL is correct, file was uploaded successfully

**Session property not set**:
Fix: Verify session startup script ran, check session.custom.genie_chat_url

**Fix**:
1. Test URL directly: Open in new browser tab
2. Check session property: In Designer, check session.custom.genie_chat_url value
3. Verify iframe settings: Sandbox should allow scripts and same origin
4. Re-upload UI: `python deploy_ui.py --environment dev`

#### 5. Slow Performance

**Symptoms**:
- Latency >15s end-to-end
- Queries take >10s
- UI feels sluggish

**Diagnosis**:
Measure each segment:
- Tag change → Bronze: Should be <2s
- Bronze → Gold: Should be <3s
- Query → Response: Should be <5s

**Common causes**:

**Warehouse cold start**:
- Symptom: First query slow, subsequent fast
- Fix: Keep warehouse running during demo

**DLT pipeline lagging**:
- Symptom: Bronze has recent data, gold is minutes behind
- Fix: Check pipeline graph, increase cluster size

**Network latency**:
- Symptom: Consistent delay across all operations
- Fix: Test from closer network location, check bandwidth

**Too much data**:
- Symptom: Queries slow on large tables
- Fix: Add time filters, partition tables, use liquid clustering

**Fix**:
1. Pre-warm warehouse: Run test query 5 minutes before demo
2. Monitor DLT latency: Should show <3s in pipeline UI
3. Optimize queries: Add WHERE clauses for recent data only
4. Consider serverless SQL warehouse for faster cold starts

#### 6. Fault Injection Not Working

**Symptoms**:
- CR_002 vibration stays normal
- No alarm after 30 minutes

**Diagnosis**:
```bash
# Check Gateway logs
# Look for "Fault injection" messages
```

**Common issues**:

**Script disabled**:
Fix: Gateway > Config > Scripting > Enable "Fault Injection" script

**Wrong target**:
Fix: Verify script targets [default]Mining/Equipment/CR_002/Vibration_MM_S

**Time delay too long**:
Fix: Edit script, reduce START_DELAY_MINUTES for testing

**Script error**:
Fix: Check Gateway logs for Python errors, fix syntax issues

**Fix**:
1. Verify script is enabled and running
2. Check Gateway logs for errors
3. Manually test: Set CR_002/Vibration to 45, verify alarm fires
4. For demo, consider manual fault instead of waiting 30 minutes

### Getting Help

If stuck:

1. **Check logs**:
   - Ignition: Status > Diagnostics > Logs
   - Databricks: Pipeline details page > Event logs
   - Browser: F12 > Console

2. **Review documentation**:
   - Component READMEs in each directory
   - Deployment guides in build/
   - Original prompt files in prompts/

3. **Test in isolation**:
   - Test each component separately
   - Identify where the break is
   - Fix one layer at a time

4. **Rollback if needed**:
   - See: build/rollback_procedures.md
   - Revert to last known good state
   - Rebuild incrementally

5. **Contact support**:
   - Include deployment summary
   - Include relevant log snippets
   - Describe what you've already tried

---

## Success Criteria

System is ready for demo when:

- [x] All automated deployments completed successfully
- [x] All manual configuration steps completed
- [ ] Tags updating every second with realistic values
- [ ] Data flowing Ignition → Databricks in <2s
- [ ] DLT pipeline processing in <3s total latency
- [ ] Genie responding to queries in <5s
- [ ] End-to-end latency <15s (tag change → chat response)
- [ ] Chat UI loading in Perspective view
- [ ] "Ask AI" buttons working from alarm table
- [ ] Fault injection scenario working (CR_002 degradation)
- [ ] System stable for 1+ hour continuous operation
- [ ] Demo rehearsed and timed (target: 15 minutes)
- [ ] Backup video recorded (in case live demo fails)

## Final Checklist

Before demo day:

- [ ] Run full validation: `python build/run_validation.py --environment dev`
- [ ] Rehearse demo 2-3 times
- [ ] Record backup video
- [ ] Test from demo environment (not development machine)
- [ ] Verify all credentials are current
- [ ] Keep warehouse running (avoid cold start during demo)
- [ ] Have rollback plan ready
- [ ] Brief team on demo flow
- [ ] Prepare Q&A responses for common questions
- [ ] Test projection/screen sharing

---

**You're ready! The system should work flawlessly for the demo.**
