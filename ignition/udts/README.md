# Mining Operations UDT Tag Definitions

This directory contains User Defined Type (UDT) definitions and tag instance creation scripts for the Mining Operations Genie Demo project.

## Overview

**Purpose:** Define standardized tag structures for mining equipment (haul trucks, crushers, conveyors) to enable realistic operational data simulation and Databricks Genie AI querying.

**Equipment Types:**
- **HaulTruck**: 5 instances (HT_001 through HT_005) - 14 members each
- **Crusher**: 3 instances (CR_001 through CR_003) - 9 members each
- **Conveyor**: 2 instances (CV_001, CV_002) - 5 members each

**Total Tags:** 107 tags (70 haul truck + 27 crusher + 10 conveyor)

## Files in This Directory

### UDT Definition Files (JSON)

1. **HaulTruck_UDT.json**
   - Mining haul truck with GPS, speed, load, fuel, tire pressures, vibration
   - 14 member tags per instance
   - Used for: Vehicle tracking, payload monitoring, maintenance scheduling

2. **Crusher_UDT.json**
   - Primary ore crusher with throughput, vibration, motor current
   - 9 member tags per instance
   - Includes alarm configurations for high/critical vibration
   - Used for: Production monitoring, predictive maintenance

3. **Conveyor_UDT.json**
   - Belt conveyor system with speed, load, alignment
   - 5 member tags per instance
   - Includes alarm configurations for belt misalignment
   - Used for: Material flow tracking, belt health monitoring

### Python Scripts

4. **create_tag_instances.py**
   - Programmatically creates all tag instances from UDT definitions
   - Creates folder structure: `[default]Mining/Equipment/`
   - Configures alarms for crushers and conveyors
   - Validates tag creation
   - Run from: Ignition Designer Script Console or Gateway Script

5. **validation_tests.py**
   - Comprehensive test suite to validate tag structure
   - 8 test cases covering folders, instances, members, alarms, values
   - Generates detailed test report
   - Run from: Ignition Designer Script Console

### Documentation

6. **README.md** (this file)
   - Setup instructions and reference guide

## Installation Instructions

### Method 1: Manual UDT Creation (Recommended for Learning)

**Time Required:** 20-30 minutes

**Steps:**

1. **Open Ignition Designer**
   - Launch Ignition Designer and connect to your gateway
   - Open Tag Browser panel

2. **Create Folder Structure**
   ```
   Right-click [default] > New Folder > "Mining"
   Right-click Mining > New Folder > "Equipment"
   ```

3. **Create UDT Definitions**

   **a) HaulTruck UDT:**
   ```
   Right-click Data Types > UDT Definitions > New UDT Type
   Name: HaulTruck
   Description: Mining haul truck with realistic operational parameters

   Add 14 members (see HaulTruck_UDT.json for details):
     - Location_Lat (Float8)
     - Location_Lon (Float8)
     - Speed_KPH (Float4)
     - Load_Tonnes (Float4)
     - Fuel_Level_Pct (Float4)
     - Engine_Temp_C (Float4)
     - Tire_Pressure_FL_PSI (Float4)
     - Tire_Pressure_FR_PSI (Float4)
     - Tire_Pressure_RL_PSI (Float4)
     - Tire_Pressure_RR_PSI (Float4)
     - Vibration_MM_S (Float4)
     - Operator_ID (String)
     - Cycle_State (String)
     - Cycle_Time_Sec (Int4)
     - Hours_Operated (Float4)
   ```

   **b) Crusher UDT:**
   ```
   Right-click Data Types > UDT Definitions > New UDT Type
   Name: Crusher
   Description: Primary ore crusher with sensors

   Add 9 members (see Crusher_UDT.json for details):
     - Status (String)
     - Throughput_TPH (Float4)
     - Vibration_MM_S (Float4) - with alarms
     - Motor_Current_A (Float4)
     - Belt_Speed_M_S (Float4)
     - Chute_Level_Pct (Float4)
     - Runtime_Hours (Float4)
     - Feed_Rate_TPH (Float4)
     - Motor_Temp_C (Float4)
   ```

   **c) Conveyor UDT:**
   ```
   Right-click Data Types > UDT Definitions > New UDT Type
   Name: Conveyor
   Description: Belt conveyor system

   Add 5 members (see Conveyor_UDT.json for details):
     - Speed_M_S (Float4)
     - Load_Pct (Float4)
     - Motor_Temp_C (Float4)
     - Belt_Alignment_MM (Float4) - with alarms
     - Status (String)
   ```

4. **Create Tag Instances**

   **Haul Trucks:**
   ```
   Right-click [default]Mining/Equipment > New Tag Instance
   Type: HaulTruck
   Name: HT_001

   Repeat for: HT_002, HT_003, HT_004, HT_005
   ```

   **Crushers:**
   ```
   Right-click [default]Mining/Equipment > New Tag Instance
   Type: Crusher
   Name: CR_001

   Repeat for: CR_002, CR_003
   ```

   **Conveyors:**
   ```
   Right-click [default]Mining/Equipment > New Tag Instance
   Type: Conveyor
   Name: CV_001

   Repeat for: CV_002
   ```

5. **Configure Alarms**

   **Crusher Vibration Alarms (for each CR_001, CR_002, CR_003):**
   ```
   Navigate to: [default]Mining/Equipment/CR_001/Vibration_MM_S
   Right-click > Edit Tag > Alarms tab

   Add Alarm 1:
     Name: HIGH_VIBRATION
     Mode: Above Setpoint
     Setpoint: 40.0
     Priority: High
     Display Path: "CR_001 - High Vibration"

   Add Alarm 2:
     Name: CRITICAL_VIBRATION
     Mode: Above Setpoint
     Setpoint: 60.0
     Priority: Critical
     Display Path: "CR_001 - CRITICAL Vibration"

   Repeat for CR_002 and CR_003
   ```

   **Conveyor Alignment Alarms (for each CV_001, CV_002):**
   ```
   Navigate to: [default]Mining/Equipment/CV_001/Belt_Alignment_MM
   Right-click > Edit Tag > Alarms tab

   Add Alarm 1:
     Name: MISALIGNMENT_NEG
     Mode: Below Setpoint
     Setpoint: -5.0
     Priority: Medium
     Display Path: "CV_001 - Belt Misalignment (Left)"

   Add Alarm 2:
     Name: MISALIGNMENT_POS
     Mode: Above Setpoint
     Setpoint: 5.0
     Priority: Medium
     Display Path: "CV_001 - Belt Misalignment (Right)"

   Repeat for CV_002
   ```

6. **Validate Tag Structure**
   - Browse to `[default]Mining/Equipment/` in Tag Browser
   - Verify all 10 equipment instances are visible
   - Manually test: Right-click any tag > Edit Tag > Value
   - Change a value and verify it updates immediately
   - Test alarm: Set `CR_001/Vibration_MM_S` = 45 and verify alarm fires

### Method 2: Import JSON Definitions (Advanced)

**Note:** Ignition's JSON import format varies by version. The provided JSON files follow the standard structure but may require adjustments.

**Steps:**

1. Open Ignition Designer > Tag Browser
2. Right-click `Data Types > UDT Definitions`
3. Select `Import Tags` > Choose JSON file
4. Import `HaulTruck_UDT.json`, `Crusher_UDT.json`, `Conveyor_UDT.json`
5. Verify UDT types appear in Data Types folder
6. Proceed to create instances manually (Step 4 in Method 1)

### Method 3: Programmatic Creation (Fastest)

**Requirements:** Access to Ignition Designer Script Console or Gateway Scripting

**Steps:**

1. **Open Script Console**
   ```
   Ignition Designer > Tools > Script Console
   ```

2. **Run Instance Creator**
   ```python
   # Copy contents of create_tag_instances.py
   # Paste into Script Console
   # Execute (Ctrl+Enter or Run button)
   ```

3. **Verify Output**
   ```
   Expected output:
   ========================================================================
   MINING OPERATIONS TAG INSTANCE CREATOR
   ========================================================================

   Step 1: Creating folder structure...
   Created folder: [default]Mining
   Created folder: [default]Mining/Equipment

   Step 2: Creating haul truck instances...
   Created HaulTruck instance: HT_001
   Created HaulTruck instance: HT_002
   ...
   Created 5 haul truck instances (14 tags each = 70 total)

   ...

   SUCCESS! All tag instances created and validated.

   SUMMARY:
     Equipment Instances: 10
     Total Tags: 107

   Ready for physics simulation (File 02)!
   ```

4. **Run Validation Tests**
   ```python
   # Copy contents of validation_tests.py
   # Paste into Script Console
   # Execute
   ```

5. **Review Test Results**
   ```
   Expected output:
   ========================================================================
   MINING OPERATIONS UDT VALIDATION TEST SUITE
   ========================================================================

   Running: Test 1: Verify folder structure exists...
     Result: PASS

   Running: Test 2: Verify all 5 haul truck instances exist...
     Result: PASS

   ...

   SUMMARY
   ========================================================================
   Total Tests: 8
   Passed: 8
   Failed: 0

   SUCCESS! All validation tests passed.
   ```

## Tag Structure Reference

### Tag Paths

After setup, tags will be accessible at:

```
[default]Mining/Equipment/
 HT_001/
    Location_Lat           (Float8)  -31.9505 degrees
    Location_Lon           (Float8)  115.8605 degrees
    Speed_KPH              (Float4)  0.0 km/h
    Load_Tonnes            (Float4)  0.0 tonnes
    Fuel_Level_Pct         (Float4)  100.0 %
    Engine_Temp_C          (Float4)  85.0 °C
    Tire_Pressure_FL_PSI   (Float4)  100.0 PSI
    Tire_Pressure_FR_PSI   (Float4)  100.0 PSI
    Tire_Pressure_RL_PSI   (Float4)  100.0 PSI
    Tire_Pressure_RR_PSI   (Float4)  100.0 PSI
    Vibration_MM_S         (Float4)  3.0 mm/s
    Operator_ID            (String)  "OP_101"
    Cycle_State            (String)  "stopped"
    Cycle_Time_Sec         (Int4)    0 seconds
    Hours_Operated         (Float4)  0.0 hours
 HT_002/ ... HT_005/ (same structure)

 CR_001/
    Status                 (String)  "RUNNING"
    Throughput_TPH         (Float4)  2400.0 tonnes/hour
    Vibration_MM_S         (Float4)  20.0 mm/s [ALARMS: >40 HIGH, >60 CRITICAL]
    Motor_Current_A        (Float4)  200.0 Amps
    Belt_Speed_M_S         (Float4)  2.0 m/s
    Chute_Level_Pct        (Float4)  60.0 %
    Runtime_Hours          (Float4)  0.0 hours
    Feed_Rate_TPH          (Float4)  2500.0 tonnes/hour
    Motor_Temp_C           (Float4)  75.0 °C
 CR_002/ ... CR_003/ (same structure)

 CV_001/
    Speed_M_S              (Float4)  2.5 m/s
    Load_Pct               (Float4)  60.0 %
    Motor_Temp_C           (Float4)  65.0 °C
    Belt_Alignment_MM      (Float4)  0.0 mm [ALARMS: <-5 or >5 WARNING]
    Status                 (String)  "RUNNING"
 CV_002/ (same structure)
```

### Alarm Summary

| Equipment | Tag | Condition | Priority | Threshold |
|-----------|-----|-----------|----------|-----------|
| Crushers (all) | Vibration_MM_S | Above | High | >40 mm/s |
| Crushers (all) | Vibration_MM_S | Above | Critical | >60 mm/s |
| Conveyors (all) | Belt_Alignment_MM | Below | Medium | <-5 mm |
| Conveyors (all) | Belt_Alignment_MM | Above | Medium | >5 mm |

## Accessing Tags from Scripts

### Reading Tag Values

```python
# Single tag read
path = "[default]Mining/Equipment/HT_001/Speed_KPH"
value = system.tag.readBlocking([path])[0]
print("Truck speed: {} km/h".format(value.value))

# Multiple tag read
paths = [
    "[default]Mining/Equipment/HT_001/Speed_KPH",
    "[default]Mining/Equipment/HT_001/Load_Tonnes",
    "[default]Mining/Equipment/HT_001/Fuel_Level_Pct"
]
values = system.tag.readBlocking(paths)
for i, val in enumerate(values):
    print("{}: {}".format(paths[i].split("/")[-1], val.value))
```

### Writing Tag Values

```python
# Single tag write
path = "[default]Mining/Equipment/HT_001/Speed_KPH"
system.tag.writeBlocking([path], [25.5])

# Multiple tag write
paths = [
    "[default]Mining/Equipment/CR_001/Vibration_MM_S",
    "[default]Mining/Equipment/CR_001/Throughput_TPH"
]
values = [45.2, 2650.0]
system.tag.writeBlocking(paths, values)
```

## Use Cases for Genie Queries

Once physics simulation is running (File 02), users can ask Databricks Genie questions like:

**Fleet Management:**
- "Which haul trucks are currently loaded?"
- "What's the average fuel level across all trucks?"
- "Show me trucks with tire pressure below 95 PSI"

**Equipment Health:**
- "Is any crusher vibrating above normal levels?"
- "Which conveyors have belt alignment issues?"
- "Show equipment status for all crushers"

**Production Monitoring:**
- "What's the total throughput across all crushers?"
- "Which truck has traveled the most distance today?"
- "Show me equipment that's been running for more than 8 hours"

**Predictive Maintenance:**
- "Which equipment is due for maintenance based on runtime hours?"
- "Show me crusher motor temperatures above 80°C"
- "Alert me when any truck tire pressure drops below 90 PSI"

## Troubleshooting

### Common Issues

**1. UDT Import Fails**
- **Cause:** JSON format incompatibility with Ignition version
- **Solution:** Create UDTs manually using Method 1

**2. Tags Not Visible in Tag Browser**
- **Cause:** Provider mismatch or folder structure missing
- **Solution:** Verify `[default]` provider is active, recreate folder structure

**3. Alarms Not Firing**
- **Cause:** Alarm pipeline not configured at gateway level
- **Solution:** Configure alarm notification pipeline in Gateway > Config > Alarming

**4. Script Fails with "Tag Already Exists"**
- **Cause:** Re-running creation script
- **Solution:** This is expected behavior. Script will skip existing tags.

**5. Tag Quality Shows "Bad"**
- **Cause:** Memory tags default to "Good" quality, but may show "Bad" if never written
- **Solution:** Run physics simulation script (File 02) to populate values

### Validation Checklist

After setup, verify:

- [ ] All 10 equipment instances visible in Tag Browser
- [ ] Each haul truck has 14 member tags
- [ ] Each crusher has 9 member tags
- [ ] Each conveyor has 5 member tags
- [ ] Total: 107 tags created
- [ ] Crusher vibration alarms configured (test by setting value >40)
- [ ] Conveyor alignment alarms configured (test by setting value >5)
- [ ] Tags are readable (quality = "Good")
- [ ] Tags are writable (manual value change works)
- [ ] Folder structure: `[default]Mining/Equipment/` exists

### Support

For issues specific to:
- **Ignition configuration**: Refer to Inductive Automation documentation
- **Demo setup**: Check project documentation in `/prompts/` directory
- **Databricks Genie integration**: See main project README

## Next Steps

After completing UDT setup:

1. **Run Validation Tests** (`validation_tests.py`)
2. **Proceed to Physics Simulation** (File 02: `ralph_wiggum_02_physics_simulation.md`)
3. **Configure HMI Displays** (File 03: Mining operations dashboard)
4. **Set Up Databricks Integration** (File 04: Data pipeline to Databricks)
5. **Deploy Genie AI Interface** (File 05: Natural language query system)

## Technical Details

**Ignition Version Compatibility:** Tested with Ignition 8.1.x

**Tag Provider:** `[default]` (can be adapted to named providers)

**Tag Types:** Memory tags (no OPC/device connections required for demo)

**Update Rate:** Values updated via Gateway Timer Script (1-second default)

**Historical Data:** Optional - configure Tag Historian for time-series storage

**Performance Impact:** 107 tags at 1Hz update = negligible (<1% CPU on modern gateway)

## File Metadata

**Created:** 2026-02-14
**Version:** 1.0
**Author:** Generated for Databricks Genie Demo
**Dependencies:** Ignition 8.1+, Python 2.7 (Jython)
**License:** Demo/Educational Use
