# Deployment Quick Start Guide

**Get the Mining Operations Genie Demo running in 4 hours**

---

## Prerequisites (5 minutes)

### Required

- Python 3.12+
- Databricks workspace access
- Databricks personal access token
- Ignition Gateway 8.1+ with admin access

### Setup

```bash
# 1. Navigate to build directory
cd build

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variable
export DATABRICKS_TOKEN=dapi1234567890abcdef

# 4. Verify prerequisites
python deploy_all.py --check-only
```

Expected output: All checks should show  PASS

---

## Automated Deployment (30 minutes)

### Deploy Everything

```bash
python deploy_all.py --environment dev
```

This will:
1. Deploy Databricks dimension tables (5 min)
2. Deploy DLT Real-Time pipeline (10 min)
3. Upload chat UI to Databricks Files (3 min)
4. Generate Ignition deployment checklists (2 min)
5. Generate integration guides (5 min)
6. Run validation queries (5 min)

**Important**: Save the chat UI URL from output - you'll need it later.

### Or Deploy Components Separately

```bash
# Databricks only (20 min)
python deploy_databricks.py --environment dev

# UI only (5 min)
python deploy_ui.py --environment dev

# Ignition guides only (2 min)
python deploy_ignition.py --environment dev
```

---

## Manual Configuration (2-3 hours)

### 1. Ignition Setup (2 hours)

Follow the generated checklist:
```bash
cat ignition_deployment_checklist_dev.md
```

**Key Steps**:

#### a) Import UDTs (15 min)
- Open Ignition Designer
- Tag Browser > Data Types > Import JSON
- Import: HaulTruck_UDT.json, Crusher_UDT.json, Conveyor_UDT.json

#### b) Create Tag Instances (30 min)
Option 1 - Script (recommended):
```bash
cd ../ignition/udts
python create_tag_instances.py
```

Option 2 - Manual in Designer (see checklist)

#### c) Configure Alarms (15 min)
- CR_001, CR_002, CR_003 → Vibration > 40 mm/s

#### d) Deploy Gateway Scripts (30 min)
- Gateway webpage > Config > Scripting
- Create Timer Script: "Physics Simulation" (1000ms)
  - Copy from: ignition/scripts/mining_physics_simulation.py
- Create Timer Script: "Fault Injection" (1000ms)
  - Copy from: ignition/scripts/fault_injection_cr002.py
- Enable both scripts

#### e) Configure Zerobus (30 min)
- Gateway > Config > Zerobus
- Databricks workspace URL
- Token (from environment variable)
- Stream: mining_ot_stream
- Tag path: Mining/Equipment/**/*
- Batch: 50 records, 500ms interval
- Enable streaming

**Validation**:
```sql
-- In Databricks, after 2-3 minutes
SELECT COUNT(*), MAX(timestamp)
FROM field_engineering.mining_demo.ot_telemetry_bronze;
-- Should have hundreds of records
```

### 2. Genie Space (10 minutes)

Create in Databricks UI:

1. Navigate to: AI & ML > Genie
2. Click "Create Genie Space"
3. Configure:
   - Name: Mining Operations Intelligence
   - Catalog: field_engineering
   - Schema: mining_demo
   - Warehouse: 4b9b953939869799
4. Add instructions (from: databricks/pipelines/genie_space_setup.sql)
5. Add sample questions
6. Save and test

**Copy the Space ID** from URL (you'll need it for Perspective)

### 3. Perspective Integration (30 minutes)

Follow the generated guide:
```bash
cat perspective_integration_guide_dev.md
```

**Key Steps**:

#### a) Session Properties
Add session startup script:
```python
# Set Databricks configuration
session.custom.databricks_token = system.tag.readBlocking(['[default]System/Databricks/Token'])[0].value
session.custom.workspace_id = "4b9b953939869799"
session.custom.genie_space_id = "YOUR_SPACE_ID"  # From step 2

# Construct chat URL
base_url = "YOUR_CHAT_UI_URL"  # From automated deployment
session.custom.genie_chat_url = base_url + "?token=" + session.custom.databricks_token + "&workspace=" + session.custom.workspace_id + "&space=" + session.custom.genie_space_id
```

#### b) Add Embedded Frame
- Add component to Perspective view (right panel, 30% width)
- URL: `{{session.custom.genie_chat_url}}`
- Sandbox: Allow scripts, Allow same origin

#### c) Add Equipment Cards
- Bind to tags: [default]Mining/Equipment/CR_002/Vibration_MM_S
- Color based on value (green <30, orange 30-40, red >40)

#### d) Add "Ask AI" Buttons
```python
# Button onClick
def runAction(self, event):
    equipment = "CR_002"
    question = f"Why is {equipment} vibration high?"
    self.session.custom.pending_question = question
    # Update chat URL with pre-filled question
    chat_url = self.session.custom.genie_chat_url + "&question=" + system.net.httpQuote(question)
    self.session.custom.genie_chat_url = chat_url
```

---

## Validation (30 minutes)

### Component Tests

#### Ignition
```bash
# Watch tags in Tag Browser for 1 minute
# Should see values updating every second
```

#### Databricks
```sql
-- Check data flow
SELECT 'bronze' as layer, COUNT(*) as records, MAX(timestamp) as latest
FROM field_engineering.mining_demo.ot_telemetry_bronze
UNION ALL
SELECT 'gold', COUNT(*), MAX(window_start)
FROM field_engineering.mining_demo.equipment_performance_1min;

-- Bronze: Thousands of records, latest within 1 minute
-- Gold: Aggregated records, <3s lag from bronze
```

#### Genie
```
# In Databricks Genie UI, test:
"Show me current crusher status"

# Should respond in <5 seconds
```

#### UI
```
# Open chat UI URL directly in browser
# Type: "Show me current status"
# Should respond within 5 seconds
```

### End-to-End Test

**Complete workflow** (measure latency):

1. **Trigger**: In Ignition, set CR_002/Vibration to 45
2. **Wait**: 10 seconds
3. **Verify**: Check Databricks gold table has new value
4. **Query**: In Perspective, click "Ask AI" on alarm
5. **Measure**: Time from click to response

**Target**: <15 seconds total

---

## Troubleshooting

### No Data in Databricks

**Check**:
- Ignition tags updating? (Tag Browser)
- Gateway scripts running? (Status > Gateway Scripting)
- Zerobus enabled? (Config > Zerobus)
- Gateway logs for errors? (Status > Diagnostics)

**Fix**:
```bash
# Verify tag updates
# Watch [default]Mining/Equipment/CR_001/Speed_KPH

# Restart Zerobus
# Gateway > Config > Zerobus
# Disable > Save > Enable > Save
```

### DLT Pipeline Errors

**Check**:
- Databricks > Workflows > Delta Live Tables
- Click pipeline name > Check errors

**Fix**:
```bash
# Redeploy pipeline
python deploy_databricks.py --component pipeline --environment dev
```

### Genie Not Responding

**Check**:
- Space ID correct? (check URL)
- Warehouse running?
- Token permissions?

**Fix**:
```bash
# Test in Databricks UI first
# Verify space ID
# Keep warehouse running (avoid cold start)
```

### Chat UI Not Loading

**Check**:
- URL accessible directly in browser?
- Session properties set?
- Browser console errors? (F12)

**Fix**:
```bash
# Re-upload UI
python deploy_ui.py --environment dev

# Verify session.custom.genie_chat_url
# Check iframe sandbox settings
```

---

## Success Checklist

System is ready for demo when:

- [ ] Tags update every second (1 Hz)
- [ ] Data flows Ignition → Databricks (<2s)
- [ ] DLT pipeline processes (<3s latency)
- [ ] Genie responds (<5s)
- [ ] End-to-end latency <15s
- [ ] Chat UI loads in Perspective
- [ ] "Ask AI" buttons work
- [ ] Fault scenario works (CR_002 degradation)
- [ ] System stable for 1+ hour
- [ ] Demo rehearsed

---

## Demo Preparation

### Pre-Demo Checklist (Day Before)

- [ ] Run full validation
- [ ] Rehearse demo 2-3 times
- [ ] Record backup video
- [ ] Test from demo environment
- [ ] Keep warehouse running
- [ ] Prepare Q&A responses

### Demo Day

1. **30 min before**: Start all systems
2. **15 min before**: Run smoke tests
3. **5 min before**: Open Perspective session
4. **During demo**: Follow rehearsed script
5. **After demo**: Gather feedback

---

## Quick Commands Reference

```bash
# Deploy everything
python deploy_all.py --environment dev

# Deploy Databricks only
python deploy_databricks.py --environment dev

# Deploy UI only
python deploy_ui.py --environment dev

# Check prerequisites
python deploy_all.py --check-only

# View deployment summary
cat deployment_summary_dev.md

# View Ignition checklist
cat ignition_deployment_checklist_dev.md

# View Perspective guide
cat perspective_integration_guide_dev.md

# View rollback procedures
cat rollback_procedures.md

# View complete guide
cat build_sequence.md
```

---

## Timeline Summary

| Phase | Duration | Type |
|-------|----------|------|
| Prerequisites | 5 min | Setup |
| Automated Deployment | 30 min | Automated |
| Ignition Setup | 2 hours | Manual |
| Genie Space | 10 min | Manual |
| Perspective Integration | 30 min | Manual |
| Validation | 30 min | Testing |
| **Total** | **4 hours** | |

---

## Support

**Documentation**:
- Full guide: build_sequence.md
- Rollback: rollback_procedures.md
- Configuration: environment_config.yaml
- README: README.md

**Generated Guides** (after deployment):
- deployment_summary_dev.md
- ignition_deployment_checklist_dev.md
- genie_integration_config_dev.md
- perspective_integration_guide_dev.md

**Contact**:
- Databricks Support: support@databricks.com
- Ignition Support: support@inductiveautomation.com

---

## Next Steps

1. Run prerequisites check:
   ```bash
   python deploy_all.py --check-only
   ```

2. If all checks pass, deploy:
   ```bash
   python deploy_all.py --environment dev
   ```

3. Follow generated checklists

4. Run validation

5. Rehearse demo

6. You're ready!

---

**Good luck with your deployment!**
