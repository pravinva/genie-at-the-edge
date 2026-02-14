# Deployment Guide - Mining Physics Simulation

## Overview

This guide provides step-by-step instructions for deploying the mining equipment physics simulation to Ignition Gateway. The simulation provides realistic behavior for 15 equipment instances across a 23-minute haul truck cycle.

**Time to Deploy:** 15-20 minutes
**Skill Level:** Intermediate Ignition experience required

---

## Prerequisites

### 1. Ignition Gateway Requirements
- **Version:** Ignition 8.1+ (tested on 8.1.17+)
- **License:** Edge or Standard license
- **Modules Required:**
  - Tag Historian (optional, for historical data)
  - Alarm Notification (optional, for vibration alarms)
- **Resources:**
  - Java Heap: Minimum 2GB recommended
  - CPU: 2+ cores
  - Memory: 4GB+ RAM

### 2. Tag Structure Prerequisites
**CRITICAL:** UDT definitions and tag instances MUST exist before deploying scripts.

Complete these steps first:
1. Create UDT types: `HaulTruck`, `Crusher`, `Conveyor`
2. Create tag instances under `[default]Mining/Equipment/`:
   - HT_001, HT_002, HT_003, HT_004, HT_005 (Haul Trucks)
   - CR_001, CR_002, CR_003 (Crushers)
   - CV_001, CV_002 (Conveyors)

**Reference:** See `../prompts/ralph_wiggum_01_udts.md` for complete UDT definitions.

### 3. Verify Tag Structure
Before proceeding, verify tags exist in Designer:

```
Designer > Tag Browser > [default] > Mining > Equipment
  ├─ HT_001/
  │  ├─ Location_Lat
  │  ├─ Speed_KPH
  │  ├─ Load_Tonnes
  │  └─ ... (12 more tags)
  ├─ HT_002/ ... HT_005/
  ├─ CR_001/
  │  ├─ Status
  │  ├─ Throughput_TPH
  │  ├─ Vibration_MM_S
  │  └─ ... (6 more tags)
  ├─ CR_002/ ... CR_003/
  ├─ CV_001/
  └─ CV_002/
```

**Expected Tag Count:** 105 tags minimum

---

## Deployment Steps

### Step 1: Deploy Main Physics Simulation Script

**Location:** Ignition Gateway Web Interface

1. **Navigate to Timer Scripts:**
   ```
   Gateway Webpage > Config > Scripting > Gateway Event Scripts
   Click: "Timer Scripts" tab
   ```

2. **Create New Timer Script:**
   ```
   Click: "Add Timer Script" button
   ```

3. **Configure Timer Script:**
   ```
   Name: MiningPhysicsSimulation
   Description: Realistic mining equipment behavior simulation (15 equipment instances)
   Enabled: ☑ (checked)
   ```

4. **Set Execution Timing:**
   ```
   Execution: Fixed Rate
   Delay (seconds): 1
   Initial Delay (seconds): 0
   ```

5. **Paste Script Code:**
   ```
   - Open file: mining_physics_simulation.py
   - Copy entire contents
   - Paste into script editor
   ```

6. **Save Configuration:**
   ```
   Click: "Save Changes" button
   Wait for confirmation message
   ```

7. **Verify Script is Running:**
   ```
   Gateway > Status > Diagnostics > Timer Scripts

   Look for:
   - Script Name: MiningPhysicsSimulation
   - Status: Running
   - Last Execution: <1 second ago (updates continuously)
   - Execution Time: 30-50ms (should be <100ms)
   - Error Count: 0
   ```

### Step 2: Verify Tag Updates

**Location:** Ignition Designer

1. **Open Tag Browser:**
   ```
   Designer > Tag Browser > [default] > Mining > Equipment
   ```

2. **Monitor Live Updates:**
   ```
   Select: HT_001 > Speed_KPH
   Watch value update every second

   Expected behavior:
   - Value changes continuously
   - No "Bad Quality" indicators
   - Smooth transitions (no sudden jumps)
   ```

3. **Verify Cycle Progression:**
   ```
   Watch: HT_001 > Cycle_State

   Over 23 minutes, should cycle through:
   1. "loading" (5 minutes)
   2. "hauling_loaded" (8 minutes)
   3. "dumping" (3 minutes)
   4. "returning_empty" (7 minutes)
   5. Repeat
   ```

4. **Check Multiple Equipment:**
   ```
   Verify updates for:
   - HT_002, HT_003 (other haul trucks)
   - CR_001 (crusher throughput, vibration)
   - CV_001 (conveyor load)
   ```

### Step 3: Create Fault State Tags for CR_002 (Optional)

These tags enable the fault injection script for demonstrating bearing failure.

**Location:** Ignition Designer Tag Browser

1. **Navigate to CR_002:**
   ```
   Designer > Tag Browser > [default] > Mining > Equipment > CR_002
   ```

2. **Add Fault State Tags:**

   **Tag 1: Fault_Enabled**
   ```
   Right-click CR_002 > New Tag > Memory Tag
   Name: Fault_Enabled
   Data Type: Boolean
   Value: False
   Tooltip: "Is fault injection active?"
   ```

   **Tag 2: Fault_Start_Time**
   ```
   Right-click CR_002 > New Tag > Memory Tag
   Name: Fault_Start_Time
   Data Type: Int8 (Long)
   Value: 0
   Tooltip: "Timestamp when fault started (milliseconds)"
   ```

   **Tag 3: Fault_Elapsed_Hours**
   ```
   Right-click CR_002 > New Tag > Memory Tag
   Name: Fault_Elapsed_Hours
   Data Type: Float4
   Value: 0.0
   Tooltip: "Hours elapsed since fault started"
   ```

   **Tag 4: Fault_Phase**
   ```
   Right-click CR_002 > New Tag > Memory Tag
   Name: Fault_Phase
   Data Type: String
   Value: "normal"
   Tooltip: "Current fault phase (normal, early, warning, critical, failed)"
   ```

3. **Commit Changes:**
   ```
   Designer > Save Project
   ```

### Step 4: Test Fault Injection (Optional)

**Location:** Ignition Designer Script Console

1. **Open Script Console:**
   ```
   Designer > Tools > Script Console
   ```

2. **Load Fault Injection Script:**
   ```
   - Open file: fault_injection_cr002.py
   - Copy entire contents
   - Paste into Script Console
   - Click: "Execute" button
   ```

3. **Start Fault Sequence (Accelerated Mode):**
   ```python
   # In Script Console, execute:
   start_cr002_fault_sequence(accelerated=True)
   ```

   **Result:** CR_002 will degrade over 48 minutes (instead of 48 hours)

4. **Monitor Fault Progression:**
   ```
   Watch: CR_002/Vibration_MM_S

   Timeline (accelerated):
   - 0-24 min: Normal (18-22 mm/s)
   - 24-36 min: Early degradation (28-32 mm/s)
   - 36-42 min: Warning (35-45 mm/s)
   - 42-48 min: Critical (55-70 mm/s)
   ```

5. **Check Fault Status:**
   ```python
   # In Script Console:
   get_fault_status()
   ```

6. **Stop Fault Sequence:**
   ```python
   # In Script Console:
   stop_cr002_fault_sequence()
   ```

   **Result:** CR_002 returns to normal operation

---

## Validation

### Automated Testing

Run the validation script to verify correct deployment:

1. **Load Testing Script:**
   ```
   Designer > Tools > Script Console
   - Open file: testing_script.py
   - Copy contents
   - Paste into Script Console
   - Click: "Execute"
   ```

2. **Run All Tests:**
   ```python
   # In Script Console:
   run_all_tests()
   ```

3. **Expected Results:**
   ```
   [PASS] Tag Structure Validation
   [PASS] Physics Calculations
   [PASS] Cycle State Transitions
   [PASS] Performance Benchmarking
   [PASS] Data Quality Checks
   [PASS] Fault Injection Validation

   RESULTS: 6/6 tests passed
   ```

### Manual Validation Checklist

- [ ] Timer script shows "Running" status in Gateway diagnostics
- [ ] Execution time is 30-50ms (acceptable up to 100ms)
- [ ] Error count is 0 in Gateway diagnostics
- [ ] HT_001 Speed_KPH updates every second
- [ ] HT_001 Cycle_State progresses: loading → hauling → dumping → returning
- [ ] CR_001 Vibration_MM_S varies between 18-22 mm/s
- [ ] CR_002 Throughput_TPH varies around 2400 t/hr
- [ ] CV_001 Load_Pct oscillates between 40-80%
- [ ] No "Bad Quality" indicators on any tags
- [ ] Gateway log shows INFO messages every 60 seconds (no ERRORs)

---

## Monitoring

### Gateway Diagnostics

**Check Script Health:**
```
Gateway > Status > Diagnostics > Timer Scripts

Monitor:
- Last Execution: Should be <1 second ago
- Execution Time: Should be 30-50ms
- Error Count: Should remain 0
```

**Check Gateway Logs:**
```
Gateway > Status > Diagnostics > Logs > Wrapper.log

Search for: "MiningPhysicsSimulation"

Expected logs:
[INFO] Physics simulation running - 60 executions completed
[INFO] Sample: HT_001 speed = 27.3 km/h
```

### Performance Metrics

**Normal Operating Ranges:**
- **CPU Usage:** <1% sustained, <5% peak
- **Memory Usage:** ~10MB for script
- **Execution Time:** 30-50ms per cycle
- **Tag Updates:** 105 tags/second

**Performance Thresholds:**
- ⚠️ Warning: Execution time >100ms
- ❌ Critical: Execution time >500ms (cannot keep up with 1s interval)
- ❌ Critical: Error count >0

**If Performance Issues Occur:**
1. Increase timer delay from 1s to 2s
2. Reduce tag update frequency
3. Check Gateway resource utilization
4. Review logs for errors

---

## Troubleshooting

### Issue: Tags Not Updating

**Symptoms:**
- Tag values frozen in Tag Browser
- No errors in Gateway logs
- Timer script shows "Running"

**Diagnosis:**
```python
# In Script Console:
system.tag.readBlocking(["[default]Mining/Equipment/HT_001/Speed_KPH"])
```

**Solutions:**
1. Verify tag path case-sensitivity (exact match required)
2. Check tag quality (should be "Good")
3. Manually write to tag to verify write permissions:
   ```python
   system.tag.writeBlocking(["[default]Mining/Equipment/HT_001/Speed_KPH"], [50.0])
   ```
4. Restart Gateway if tag provider is unresponsive

---

### Issue: Script Not Running

**Symptoms:**
- "Last Execution" timestamp not updating
- Timer script shows "Stopped" or no status

**Solutions:**
1. Check script is enabled (checkbox in configuration)
2. Verify no syntax errors in script
3. Check Gateway logs for errors:
   ```
   Gateway > Status > Diagnostics > Logs
   Search: "ERROR"
   ```
4. Restart Gateway Event Script system:
   ```
   Gateway > Config > Scripting > Gateway Event Scripts
   Click: "Restart Scripts" button
   ```

---

### Issue: Unrealistic Values

**Symptoms:**
- Speed suddenly jumps 0 → 100 km/h
- Temperature is negative or >200°C
- Load exceeds 250 tonnes

**Diagnosis:**
```python
# In Script Console:
quick_diagnostic()
```

**Solutions:**
1. Verify physics constants in script (check HAUL_CYCLE_TOTAL_SEC, etc.)
2. Check for missing smooth_transition() calls
3. Verify cycle_time calculation and wrap-around logic
4. Review add_noise() amplitude values

---

### Issue: High CPU Usage

**Symptoms:**
- Gateway CPU usage >10%
- Execution time >100ms
- Gateway becomes sluggish

**Diagnosis:**
```
Gateway > Status > Diagnostics > Performance
Check: CPU usage, thread counts, tag update rate
```

**Solutions:**
1. Increase timer delay from 1s to 2s:
   ```
   Gateway > Config > Scripting > Timer Scripts > MiningPhysicsSimulation
   Delay: 2 seconds
   ```
2. Reduce logging frequency (change 60s interval to 300s)
3. Optimize tag writes (batch more efficiently)
4. Check for other Gateway scripts consuming resources

---

### Issue: Fault Injection Not Working

**Symptoms:**
- CR_002 vibration stays at 20 mm/s
- Fault_Enabled tag is True but no degradation occurs
- get_fault_status() shows error

**Solutions:**
1. Verify fault state tags exist:
   ```python
   system.tag.readBlocking([
       "[default]Mining/Equipment/CR_002/Fault_Enabled",
       "[default]Mining/Equipment/CR_002/Fault_Elapsed_Hours"
   ])
   ```
2. Check if main physics script is overwriting fault values (fault script must run separately)
3. Manually set vibration to verify tag is writable:
   ```python
   system.tag.writeBlocking(
       ["[default]Mining/Equipment/CR_002/Vibration_MM_S"],
       [50.0]
   )
   ```
4. Review fault injection script logs for errors

---

## Advanced Configuration

### Adjusting Simulation Parameters

Edit the main script to customize behavior:

**Change Haul Truck Cycle Duration:**
```python
# In mining_physics_simulation.py
HAUL_CYCLE_TOTAL_SEC = 1380  # 23 minutes (default)
HAUL_CYCLE_TOTAL_SEC = 900   # 15 minutes (faster demo)
```

**Change Crusher Throughput Range:**
```python
# In mining_physics_simulation.py, simulate_crusher() function
nominal_throughput = 2400.0  # Default
target_throughput = nominal_throughput + add_noise(0, 100.0)

# Increase variation:
target_throughput = nominal_throughput + add_noise(0, 200.0)
```

**Change Update Interval:**
```python
# In Gateway Timer Script configuration
Delay: 1 second   # Default (fast, realistic)
Delay: 2 seconds  # Slower (reduces load)
Delay: 0.5 seconds  # Faster (requires high performance)
```

### Adding Custom Equipment

To add additional equipment instances:

1. **Create Tag Instance:**
   ```
   Designer > Tag Browser > [default] > Mining > Equipment
   Right-click > New Tag Instance
   Type: HaulTruck (or Crusher, Conveyor)
   Name: HT_006 (or CR_004, CV_003)
   ```

2. **Update Script:**
   ```python
   # In mining_physics_simulation.py
   HAUL_TRUCKS = ["HT_001", "HT_002", "HT_003", "HT_004", "HT_005", "HT_006"]
   ```

3. **Save and Monitor:**
   - Check execution time (may increase)
   - Verify new equipment updates correctly

---

## Integration with MQTT (Zerobus)

After deploying the physics simulation, integrate with MQTT for Databricks streaming:

**Next Steps:**
1. Deploy MQTT publisher script (separate script, not included here)
2. Configure MQTT broker connection
3. Publish equipment telemetry at 1Hz:
   ```
   Topic: mining/equipment/{equipment_id}/telemetry
   Payload: JSON with all tag values
   ```

**Reference:** See workstream File 03 for Zerobus integration.

---

## Backup and Recovery

### Export Tag Configuration

Before making changes, export tag structure:

```
Designer > Tag Browser > [default] > Mining
Right-click > Export Tags
Format: JSON
Save as: mining_tags_backup_YYYY-MM-DD.json
```

### Export Scripts

Gateway scripts are stored in Gateway configuration. To backup:

```
Gateway > Config > Backup
Create Gateway Backup
Download .gwbk file
Store in secure location
```

### Restore from Backup

If deployment fails or tags are corrupted:

```
Gateway > Config > Restore
Upload .gwbk file
Select: Restore scripts and tags
Click: Restore
```

---

## Production Deployment Notes

⚠️ **Important:** This simulation is designed for demonstration purposes. For production use:

1. **Performance Testing:**
   - Test with full equipment count
   - Monitor for 24+ hours
   - Verify no memory leaks
   - Check CPU usage patterns

2. **Error Handling:**
   - Add comprehensive try/except blocks
   - Implement tag quality checks
   - Add dead-man switches (detect script crashes)
   - Configure alarm notifications for script failures

3. **Logging:**
   - Reduce INFO log frequency (every 5-10 minutes)
   - Add structured logging (JSON format)
   - Integrate with external monitoring (Prometheus, Grafana)

4. **Security:**
   - Restrict script editing to administrators
   - Audit log access to Gateway diagnostics
   - Use separate tag providers for simulation vs. real data

5. **High Availability:**
   - Configure Gateway redundancy
   - Test failover scenarios
   - Document recovery procedures

---

## Support and Documentation

**Reference Materials:**
- `README.md` - Project overview and architecture
- `physics_utils.py` - Physics calculation reference
- `testing_script.py` - Validation utilities
- `fault_injection_cr002.py` - Fault simulation details

**Ignition Documentation:**
- [Timer Scripts](https://docs.inductiveautomation.com/display/DOC81/Gateway+Event+Scripts)
- [Tag System](https://docs.inductiveautomation.com/display/DOC81/Tag+System)
- [Scripting Functions](https://docs.inductiveautomation.com/display/DOC81/Scripting+Functions)

**Project Context:**
- Genie at the Edge - Mining Operations Demo
- Databricks integration for real-time ML inference
- Predictive maintenance use case (CR_002 bearing failure)

---

## Completion Checklist

Deployment is complete when:

- [ ] Main physics simulation script deployed and running
- [ ] Timer script execution time <100ms
- [ ] All 105 tags updating every second
- [ ] Haul truck cycles progress correctly (23-minute pattern)
- [ ] Crusher throughput varies realistically (2200-2500 t/hr)
- [ ] No errors in Gateway logs
- [ ] Validation tests pass (6/6)
- [ ] Fault injection tags created (optional)
- [ ] Fault sequence tested successfully (optional)
- [ ] Performance monitoring in place
- [ ] Backup created
- [ ] Documentation reviewed by team

**Estimated Total Deployment Time:** 15-20 minutes

---

**Deployed by:** _________________
**Date:** _________________
**Gateway Version:** _________________
**Notes:** _________________

---

**Generated by:** Claude Code (Anthropic)
**Project:** Genie at the Edge - Mining Operations Demo
**Version:** 1.0
**Last Updated:** 2026-02-14
