# Ignition Gateway Setup - Correct Method

## Important: Tag Import Requires Designer

Tag import is done through **Ignition Designer**, not the Gateway web interface.

---

## Quick Setup (15 minutes)

### Step 1: Access Ignition Gateway (1 min)

1. Open browser: http://localhost:8181
2. Login: **admin** / **password**
3. Gateway should show "Gateway Status: Running"

---

### Step 2: Download Designer Launcher (2 min)

1. From Gateway home page, click **"Get Designer"**
2. Download **Designer Launcher** for your OS
3. Install Designer Launcher
4. Launch the application

---

### Step 3: Add Gateway Connection (1 min)

1. Open Designer Launcher
2. Click **"Add Designer"**
3. Configure:
   - **Gateway URL:** `http://localhost:8181`
   - **Name:** `Genie Demo Local`
4. Click **"Add"**

---

### Step 4: Import Tags via Designer (5 min)

1. **Open Designer:**
   - In Designer Launcher, select the gateway
   - Click **"Open Designer"**
   - Login: admin / password

2. **Import Tag Package:**
   - In Designer, open **Tag Browser** panel (left side)
   - Right-click on **"default"** provider
   - Select **"Import Tags..."**
   - Browse to: `ignition/complete_tag_import.json`
   - Click **"Import"**
   - Wait for completion (~ 30 seconds)

3. **Verify Import:**
   - Expand "default" provider in Tag Browser
   - Should see "MiningOperations" folder
   - Expand to verify:
     - `_types_` folder (3 UDTs)
     - `HT_001` through `HT_005` (5 haul trucks)
     - `CR_001` through `CR_003` (3 crushers)
     - `CV_001` and `CV_002` (2 conveyors)
   - Total: **107 tags**

4. **Save:**
   - File > **Save**
   - Changes are committed to Gateway

---

### Step 5: Deploy Gateway Scripts (5 min)

**Deploy Physics Simulation:**

1. In Gateway web interface: http://localhost:8181
2. Navigate to: **Config > Scripting > Gateway Event Scripts**
3. Click **"+"** to add new script
4. Configure:
   - **Name:** `MiningPhysicsSimulation`
   - **Event:** Timer (Fixed Rate)
   - **Delay:** `1000 ms`
5. **Script Code:**
   - Open file: `ignition/scripts/mining_physics_simulation.py`
   - Copy **entire contents**
   - Paste into script editor
6. **Enable:** Check the "Enabled" checkbox
7. Click **"Save"**

**Deploy Fault Injection (Optional):**

1. Click **"+"** to add another script
2. Configure:
   - **Name:** `FaultInjectionCR002`
   - **Event:** Timer (Fixed Rate)
   - **Delay:** `1000 ms`
3. **Script Code:**
   - Open file: `ignition/scripts/fault_injection_cr002.py`
   - Copy entire contents
   - Paste into script editor
4. **Enable:** **UNCHECK** (keep disabled for now)
5. Click **"Save"**
6. Enable manually when ready for demo

---

### Step 6: Verify Tags Are Updating (2 min)

**In Designer Tag Browser:**

1. In Designer, open Tag Browser
2. Expand: `default > MiningOperations > HT_001`
3. Watch values updating in real-time
4. Check:
   - `Cycle_State` - Should cycle through states
   - `Speed_KPH` - Should change based on state
   - `Load_Tonnes` - Should be 0 when empty, 220 when loaded
   - `Cycle_Time_Sec` - Should increment every second

**In Gateway Status:**

1. In Gateway web: **Config > Status > Tags**
2. Should see **107 tags** listed
3. Check "Update Rate" column - should show activity

**In Gateway Logs:**

1. Go to: **Config > Status > Logs > Gateway**
2. Should see no errors
3. Look for "MiningPhysicsSimulation" execution logs

---

## Alternative: Script Console Method (Faster)

If you prefer scripting over manual tag import:

### Option A: Use Script Console for Tag Creation

1. **Import UDTs First (Designer Required):**
   - Import individual UDT files in Designer:
     - `ignition/udts/HaulTruck_UDT.json`
     - `ignition/udts/Crusher_UDT.json`
     - `ignition/udts/Conveyor_UDT.json`

2. **Create Instances via Script Console:**
   - In Gateway web: **Config > Scripting > Script Console**
   - Open file: `ignition/udts/create_tag_instances.py`
   - Copy entire contents
   - Paste into Script Console
   - Click **"Run Script"**
   - Should output: "Created 10 equipment tags (107 total tags)"

---

## File Locations Reference

| Component | File Path |
|-----------|-----------|
| **Complete Tag Import (Designer)** | `ignition/complete_tag_import.json` |
| **Individual UDTs (Designer)** | `ignition/udts/HaulTruck_UDT.json`<br>`ignition/udts/Crusher_UDT.json`<br>`ignition/udts/Conveyor_UDT.json` |
| **Tag Creation Script (Console)** | `ignition/udts/create_tag_instances.py` |
| **Physics Simulation (Gateway)** | `ignition/scripts/mining_physics_simulation.py` |
| **Fault Injection (Gateway)** | `ignition/scripts/fault_injection_cr002.py` |

---

## Gateway Web Interface vs Designer

| Task | Tool | Location |
|------|------|----------|
| **Import Tags** | Designer | Tag Browser > Right-click > Import Tags |
| **Create Tags Manually** | Designer | Tag Browser > Right-click > New Tag |
| **View Tag Values** | Designer | Tag Browser (live view) |
| **Gateway Scripts** | Gateway Web | Config > Scripting > Gateway Event Scripts |
| **Script Console** | Gateway Web | Config > Scripting > Script Console |
| **Status/Logs** | Gateway Web | Config > Status > Logs |
| **Configuration** | Gateway Web | Config tab |

---

## Verification Checklist

After completing setup:

- [ ] Designer Launcher installed and configured
- [ ] Gateway connection added (http://localhost:8181)
- [ ] Designer opened successfully
- [ ] Tags imported via Designer Tag Browser
- [ ] 107 tags visible under MiningOperations folder
- [ ] MiningPhysicsSimulation script deployed and enabled
- [ ] FaultInjectionCR002 script deployed but disabled
- [ ] Tags updating at 1 Hz in Designer Tag Browser
- [ ] HT_001 Cycle_State cycling through states
- [ ] No errors in Gateway logs

---

## Troubleshooting

### Can't Open Designer

**Problem:** Designer won't launch or connect

**Solution:**
1. Verify gateway is running: http://localhost:8181
2. Check firewall allows port 8181
3. Try HTTPS: https://localhost:8143
4. Check Designer Launcher logs
5. Reinstall Designer Launcher if needed

### Import Failed in Designer

**Problem:** Tag import shows errors

**Solution:**
1. Verify JSON file is valid
2. Check file path is correct (use absolute path)
3. Try importing UDTs individually first
4. Check Designer console for specific errors
5. Verify provider "default" exists

### Tags Not Updating

**Problem:** Tags imported but not changing values

**Solution:**
1. Check script is enabled in Gateway web interface
2. Config > Status > Logs > Gateway (check for errors)
3. Verify script saved correctly
4. Restart gateway: `docker-compose restart ignition`
5. Check tag quality (should be "Good", not "Bad")

---

## Next Steps After Setup

1. **Watch Tags for 5 Minutes:**
   - Verify haul trucks cycle through all states
   - Check crushers maintain steady operation
   - Monitor conveyors for realistic load variations

2. **Test Fault Injection:**
   - Enable FaultInjectionCR002 script
   - Watch CR_002 Vibration_MM_S increase over time
   - Should progress from 12 → 45 mm/s over 48 minutes

3. **Connect to Databricks:**
   - Deploy DLT pipeline
   - Configure Zerobus connector
   - Verify data flowing to Bronze layer

4. **Create Perspective Project:**
   - In Designer: File > New Project
   - Type: Perspective
   - Name: GenieDemo
   - Add Genie chat view

---

## Docker Commands

```bash
# Check if container is running
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f ignition

# Restart gateway
docker-compose -f docker/docker-compose.yml restart ignition

# Stop gateway
docker-compose -f docker/docker-compose.yml down

# Start gateway
docker-compose -f docker/docker-compose.yml up -d
```

---

**Estimated Total Time:** 15 minutes

**Tools Required:**
- Web browser (for Gateway config)
- Ignition Designer Launcher (for tag import)

**Generated with Claude Code**
https://claude.com/claude-code

Co-Authored-By: Claude <noreply@anthropic.com>
