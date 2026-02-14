# Ignition Gateway Quick Setup Guide

Complete setup in 10 minutes using the web interface.

## Prerequisites

- Docker container running: `docker-compose up -d`
- Gateway accessible at: http://localhost:8181
- Login credentials: admin / password

---

## Step 1: Import Tags (5 minutes)

### Method A: Single-File Import (Recommended)

1. **Access Gateway Config:**
   - Navigate to: http://localhost:8181
   - Login: admin / password
   - Click "Config" tab

2. **Import Complete Tag Package:**
   - Go to: **Tags > Tag Browser**
   - Click **"More" menu (three dots) > Import Tags**
   - Select file: `ignition/complete_tag_import.json`
   - Click **"Import"**
   - Wait for completion (~ 30 seconds)

3. **Verify Import:**
   - Expand "default" provider in Tag Browser
   - Expand "MiningOperations" folder
   - Should see:
     - `_types_` folder (3 UDT definitions)
     - `HT_001` through `HT_005` (5 haul trucks)
     - `CR_001` through `CR_003` (3 crushers)
     - `CV_001` and `CV_002` (2 conveyors)
   - Total: **107 tags** (10 equipment × ~11 tags each)

---

## Step 2: Deploy Physics Simulation Script (3 minutes)

1. **Navigate to Gateway Scripts:**
   - Config > **Scripting > Gateway Event Scripts**
   - Click **"Add New Timer Script"**

2. **Create Simulation Script:**
   - **Name:** `MiningPhysicsSimulation`
   - **Script Type:** Timer
   - **Fixed Rate:** `1000 ms` (1 second)
   - **Enabled:** ✓ (checked)

3. **Paste Script Code:**
   - Open file: `ignition/scripts/mining_physics_simulation.py`
   - Copy entire contents
   - Paste into script editor window

4. **Save and Enable:**
   - Click **"Save"**
   - Verify "Enabled" checkbox is checked
   - Script will start executing immediately

---

## Step 3: Verify Tags Are Updating (1 minute)

1. **Open Tag Browser:**
   - Go to: **Tags > Tag Browser**
   - Expand: `default > MiningOperations`

2. **Check Haul Truck Updates:**
   - Click on `HT_001` > `Cycle_State`
   - Value should change every 1 second
   - States cycle: `stopped` → `loading` → `hauling_loaded` → `dumping` → `returning_empty`

3. **Check Crusher Updates:**
   - Click on `CR_001` > `Vibration_MM_S`
   - Value should update continuously
   - Range: 10-15 mm/s (normal operation)

4. **Monitor Live Updates:**
   - Right-click any tag folder
   - Select **"Edit in List"**
   - Watch values update in real-time (1 Hz)

---

## Step 4: Deploy Fault Injection Script (Optional - 2 minutes)

**⚠️ Only enable this when ready to demo fault scenarios**

1. **Create Fault Script:**
   - Config > **Scripting > Gateway Event Scripts**
   - Click **"Add New Timer Script"**

2. **Configure Script:**
   - **Name:** `FaultInjectionCR002`
   - **Script Type:** Timer
   - **Fixed Rate:** `1000 ms`
   - **Enabled:** ✗ (UNCHECKED initially)

3. **Paste Script Code:**
   - Open file: `ignition/scripts/fault_injection_cr002.py`
   - Copy entire contents
   - Paste into script editor

4. **Save (But Don't Enable Yet):**
   - Click **"Save"**
   - Leave "Enabled" UNCHECKED
   - Enable manually when ready for demo (checkbox → Save)

5. **Fault Timeline (When Enabled):**
   - **0-12 min:** Normal operation
   - **12-24 min:** Early degradation (vibration 15-20 mm/s)
   - **24-36 min:** Warning level (vibration 20-30 mm/s)
   - **36-48 min:** Critical level (vibration 30-45 mm/s)
   - **48 min:** Failure triggered

---

## Step 5: Create Perspective Project (Optional - 5 minutes)

1. **Create New Project:**
   - Config > **Projects > Create New Project**
   - **Name:** `GenieDemo`
   - **Type:** Perspective
   - Click **"Create"**

2. **Open Designer:**
   - Click **"Open Designer"** button
   - Designer Launcher will download and open

3. **Import View:**
   - In Designer: **View > Create New View**
   - **Name:** `GenieChat`
   - **Path:** `Views/GenieChat`
   - Click **"Create"**

4. **Add iFrame Component:**
   - Drag **"Embedded Webpage"** component to canvas
   - Set properties:
     - **url:** `https://<databricks-workspace>/files/<path-to-genie_chat_perspective.html>`
     - **width:** `100%`
     - **height:** `100%`

5. **Publish and Test:**
   - File > **Save**
   - File > **Publish**
   - Open Session: http://localhost:8181/data/perspective/client/GenieDemo

---

## Verification Checklist

### Tags (Expected: 107 total)
- [ ] 5 haul trucks (HT_001 - HT_005) = 70 tags
- [ ] 3 crushers (CR_001 - CR_003) = 27 tags
- [ ] 2 conveyors (CV_001 - CV_002) = 10 tags
- [ ] All tags updating at 1 Hz
- [ ] Haul truck cycle states transitioning

### Scripts
- [ ] MiningPhysicsSimulation enabled and running
- [ ] No errors in gateway logs (Config > Status > Logs)
- [ ] FaultInjectionCR002 saved but disabled

### Performance
- [ ] Gateway CPU usage: <10%
- [ ] Tag update rate: 1 Hz (150 tags/sec)
- [ ] No memory leaks over 1 hour runtime

---

## Troubleshooting

### Tags Not Updating

**Problem:** Tags imported but values don't change

**Solution:**
1. Check script is enabled: Config > Scripting > Gateway Event Scripts
2. Check for errors: Config > Status > Logs > Gateway
3. Verify script syntax (should be Python 2.7/Jython compatible)
4. Restart script: Disable → Save → Enable → Save

### Import Failed

**Problem:** Tag import shows errors

**Solution:**
1. Verify JSON file is valid (use https://jsonlint.com)
2. Check file path is correct
3. Try importing UDTs individually:
   - `ignition/udts/HaulTruck_UDT.json`
   - `ignition/udts/Crusher_UDT.json`
   - `ignition/udts/Conveyor_UDT.json`
4. Then run tag creation script in Script Console:
   - Config > Scripting > Script Console
   - Paste contents of `ignition/udts/create_tag_instances.py`
   - Click "Run"

### Script Errors

**Problem:** Gateway script shows errors in logs

**Solution:**
1. Check Python syntax (Jython 2.7 compatible)
2. Verify tag paths exist
3. Check imports: `system.tag`, `system.date`, `system.util`
4. Look for specific error in: Config > Status > Logs > Gateway

### Gateway Slow/Unresponsive

**Problem:** Gateway becomes slow after running scripts

**Solution:**
1. Check script execution time (should be <50ms per cycle)
2. Reduce number of tag writes per cycle
3. Increase timer delay to 2000ms (2 seconds)
4. Restart gateway: `docker-compose restart ignition`

---

## Next Steps

After successful setup:

1. **Connect to Databricks:**
   - Deploy DLT pipeline: `databricks/pipelines/mining_realtime_dlt.py`
   - Configure Zerobus connector
   - Verify data flowing to Bronze layer

2. **Deploy Genie AI:**
   - Upload chat UI to Databricks Files
   - Create Genie space with sample questions
   - Integrate into Perspective view

3. **Run Tests:**
   - Execute test suite: `./testing/run_tests.sh all`
   - Verify 24-hour stability test
   - Load test with concurrent users

4. **Demo Preparation:**
   - Follow demo script: `demo/demo_script.md`
   - Practice fault scenario 3+ times
   - Prepare customer materials

---

## Quick Commands

```bash
# Start gateway
cd docker && docker-compose up -d

# Check logs
docker-compose logs -f ignition

# Stop gateway
docker-compose down

# Reset all data (warning: destroys everything)
docker-compose down -v

# Restart gateway
docker-compose restart ignition

# Access gateway
open http://localhost:8181
```

---

## Support

- **Documentation:** `README.md` in each directory
- **Architecture:** `prompts/ralph_wiggum_00_architecture.md`
- **Testing:** `testing/README.md`
- **Build:** `build/DEPLOYMENT_QUICK_START.md`

---

**Estimated Total Setup Time:** 10-15 minutes

**Generated with Claude Code**
https://claude.com/claude-code

Co-Authored-By: Claude <noreply@anthropic.com>
