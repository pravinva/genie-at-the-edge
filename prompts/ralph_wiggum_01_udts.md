# RALPH WIGGUM WORKSTREAM - FILE 01
## Ignition UDT Definitions for Mining Equipment

**Purpose:** Create User Defined Types (UDTs) and tag instances for mining equipment simulation
**Tool:** Ignition Designer > Tag Browser
**Time:** 30 minutes
**Dependencies:** None (start here)

---

## INSTRUCTIONS FOR IGNITION DESIGNER

**Location:** Tag Browser > [default] > Right-click > New Folder: "Mining"
**Under Mining:** Create subfolder "Equipment"

---

## UDT TYPE 1: HaulTruck

**Path:** Tag Browser > Data Types > UDT Definitions > New UDT Type

```
Name: HaulTruck
Description: Mining haul truck with realistic operational parameters

MEMBERS (all Memory Tag type):

Location_Lat
  - Data Type: Float8
  - Value: -31.9505
  - Tooltip: "GPS Latitude (West Australia)"
  - Engineering Units: "degrees"

Location_Lon
  - Data Type: Float8
  - Value: 115.8605
  - Tooltip: "GPS Longitude (West Australia)"
  - Engineering Units: "degrees"

Speed_KPH
  - Data Type: Float4
  - Value: 0.0
  - Tooltip: "Current speed"
  - Engineering Units: "km/h"
  - Display Format: "0.0"

Load_Tonnes
  - Data Type: Float4
  - Value: 0.0
  - Tooltip: "Current payload"
  - Engineering Units: "tonnes"
  - Range: 0 to 250

Fuel_Level_Pct
  - Data Type: Float4
  - Value: 100.0
  - Tooltip: "Fuel tank level"
  - Engineering Units: "%"
  - Range: 0 to 100

Engine_Temp_C
  - Data Type: Float4
  - Value: 85.0
  - Tooltip: "Engine coolant temperature"
  - Engineering Units: "°C"
  - Range: 0 to 120

Tire_Pressure_FL_PSI
  - Data Type: Float4
  - Value: 100.0
  - Tooltip: "Front Left tire pressure"
  - Engineering Units: "PSI"

Tire_Pressure_FR_PSI
  - Data Type: Float4
  - Value: 100.0
  - Tooltip: "Front Right tire pressure"
  - Engineering Units: "PSI"

Tire_Pressure_RL_PSI
  - Data Type: Float4
  - Value: 100.0
  - Tooltip: "Rear Left tire pressure"
  - Engineering Units: "PSI"

Tire_Pressure_RR_PSI
  - Data Type: Float4
  - Value: 100.0
  - Tooltip: "Rear Right tire pressure"
  - Engineering Units: "PSI"

Vibration_MM_S
  - Data Type: Float4
  - Value: 3.0
  - Tooltip: "Chassis vibration"
  - Engineering Units: "mm/s"
  - Range: 0 to 20

Operator_ID
  - Data Type: String
  - Value: "OP_101"
  - Tooltip: "Current operator badge ID"

Cycle_State
  - Data Type: String
  - Value: "stopped"
  - Tooltip: "Current cycle state"
  - Options: stopped, loading, hauling_loaded, dumping, returning_empty

Cycle_Time_Sec
  - Data Type: Int4
  - Value: 0
  - Tooltip: "Seconds elapsed in current cycle"
  - Range: 0 to 1380 (23 minute cycle)

Hours_Operated
  - Data Type: Float4
  - Value: 0.0
  - Tooltip: "Cumulative operating hours"
  - Engineering Units: "hours"
```

---

## UDT TYPE 2: Crusher

```
Name: Crusher
Description: Primary ore crusher with sensors

MEMBERS:

Status
  - Data Type: String
  - Value: "RUNNING"
  - Tooltip: "Operational status"
  - Options: STOPPED, STARTING, RUNNING, DEGRADED, FAULT

Throughput_TPH
  - Data Type: Float4
  - Value: 2400.0
  - Tooltip: "Current throughput"
  - Engineering Units: "tonnes/hour"
  - Range: 0 to 3000
  - Display Format: "0"

Vibration_MM_S
  - Data Type: Float4
  - Value: 20.0
  - Tooltip: "Crusher body vibration"
  - Engineering Units: "mm/s"
  - Range: 0 to 100
  - Display Format: "0.0"
  - Alarm: >40 HIGH, >60 CRITICAL

Motor_Current_A
  - Data Type: Float4
  - Value: 200.0
  - Tooltip: "Drive motor current draw"
  - Engineering Units: "Amps"
  - Range: 0 to 300

Belt_Speed_M_S
  - Data Type: Float4
  - Value: 2.0
  - Tooltip: "Conveyor belt speed"
  - Engineering Units: "m/s"
  - Range: 0 to 3

Chute_Level_Pct
  - Data Type: Float4
  - Value: 60.0
  - Tooltip: "Input chute fill level"
  - Engineering Units: "%"
  - Range: 0 to 100

Runtime_Hours
  - Data Type: Float4
  - Value: 0.0
  - Tooltip: "Cumulative runtime since last maintenance"
  - Engineering Units: "hours"

Feed_Rate_TPH
  - Data Type: Float4
  - Value: 2500.0
  - Tooltip: "Incoming material feed rate"
  - Engineering Units: "tonnes/hour"

Motor_Temp_C
  - Data Type: Float4
  - Value: 75.0
  - Tooltip: "Motor winding temperature"
  - Engineering Units: "°C"
  - Range: 0 to 150
```

---

## UDT TYPE 3: Conveyor

```
Name: Conveyor
Description: Belt conveyor system

MEMBERS:

Speed_M_S
  - Data Type: Float4
  - Value: 2.5
  - Tooltip: "Belt speed"
  - Engineering Units: "m/s"

Load_Pct
  - Data Type: Float4
  - Value: 60.0
  - Tooltip: "Belt loading percentage"
  - Engineering Units: "%"
  - Range: 0 to 100

Motor_Temp_C
  - Data Type: Float4
  - Value: 65.0
  - Tooltip: "Drive motor temperature"
  - Engineering Units: "°C"

Belt_Alignment_MM
  - Data Type: Float4
  - Value: 0.0
  - Tooltip: "Belt tracking offset from center"
  - Engineering Units: "mm"
  - Range: -10 to 10
  - Alarm: <-5 or >5 WARNING

Status
  - Data Type: String
  - Value: "RUNNING"
  - Options: STOPPED, RUNNING, FAULT
```

---

## CREATE TAG INSTANCES

**Under [default]Mining/Equipment/, create instances:**

**Haul Trucks:**
```
Right-click Equipment folder > New Tag Instance
  - Type: HaulTruck
  - Name: HT_001
  - Repeat for: HT_002, HT_003, HT_004, HT_005
```

**Crushers:**
```
Right-click Equipment folder > New Tag Instance
  - Type: Crusher
  - Name: CR_001
  - Repeat for: CR_002, CR_003
```

**Conveyors:**
```
Right-click Equipment folder > New Tag Instance
  - Type: Conveyor
  - Name: CV_001
  - Repeat for: CV_002
```

**Total Tags Created:**
- 5 haul trucks × 14 members = 70 tags
- 3 crushers × 9 members = 27 tags
- 2 conveyors × 4 members = 8 tags
- **Total: 105 tags**

---

## CONFIGURE ALARMS

**Create alarm pipeline for high vibration:**

**Path:** Tag Browser > [default]Mining/Equipment/CR_002/Vibration_MM_S

```
Right-click > Edit Tag > Alarms tab > Add Alarm

Alarm Configuration:
  Name: HIGH_VIBRATION
  Enabled: True
  Mode: Above Setpoint
  Setpoint: 40.0
  Priority: High
  Display Path: "Crusher 2 - High Vibration"
  
  Notification:
    - Enabled: True
    - Send to: Active alarms display
    - Audio: (optional) play alarm tone
    
  Properties (custom):
    - Add: "suggested_genie_question"
    - Value: "Why is Crusher 2 vibrating excessively?"
```

**Repeat for CR_001, CR_003 with same threshold**

---

## VALIDATION STEPS

**After creating tags:**

1. **Browse tag structure:**
   ```
   [default]Mining/Equipment/
      HT_001/
        Location_Lat = -31.9505
        Speed_KPH = 0.0
        ... (12 more)
      HT_002/
      ... (3 more trucks)
      CR_001/
        Status = "RUNNING"
        Vibration_MM_S = 20.0
        ... (7 more)
      CR_002/
      CR_003/
      CV_001/
      CV_002/
   ```

2. **Manual test:**
   - Right-click any tag > Edit Tag > Value
   - Change value manually
   - Verify update reflects immediately
   - Test alarm: Set CR_002.Vibration_MM_S = 45
   - Verify alarm fires in Gateway > Status > Alarms

3. **Export for backup:**
   - Right-click [default]Mining folder
   - Export Tags > JSON
   - Save as: mining_tags_backup.json

---

## NOTES FOR CLAUDE CODE

**If generating UDT definitions programmatically:**

You cannot create Ignition UDTs via code/script - they must be created in Designer GUI.
However, you CAN export existing UDTs as JSON and import them.

**Alternative approach:**
1. Create one UDT manually in Designer
2. Export as JSON
3. Modify JSON for other UDT types
4. Import back into Designer

**JSON structure (reference):**
```json
{
  "name": "HaulTruck",
  "tagType": "UdtType",
  "tags": [
    {
      "name": "Location_Lat",
      "tagType": "AtomicTag",
      "dataType": "Float8",
      "value": -31.9505
    },
    // ... more members
  ]
}
```

But for this workstream: **Create manually in Designer - it's faster for 3 UDT types.**

---

## COMPLETION CHECKLIST

- [ ] HaulTruck UDT defined with 14 members
- [ ] Crusher UDT defined with 9 members
- [ ] Conveyor UDT defined with 4 members
- [ ] 5 haul truck instances created (HT_001 to HT_005)
- [ ] 3 crusher instances created (CR_001 to CR_003)
- [ ] 2 conveyor instances created (CV_001, CV_002)
- [ ] Alarms configured for crusher vibration (>40 threshold)
- [ ] All tags browseable under [default]Mining/Equipment/
- [ ] Tag structure exported as backup JSON
- [ ] Ready for scripts to update values (next file: 02_Physics_Simulation)

---

**Time to complete:** 20-30 minutes for experienced Ignition user
**Next:** Feed File 02 to Claude Code to generate physics simulation script
