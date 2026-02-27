# Quick Start - Timer Script Setup

## Your Tag Structure

You're using the **Sample_Tags** tag provider (not default). Your tag paths are:

```
[Sample_Tags]Mining/
  ├── Config/
  │   ├── SimEnabled
  │   └── UpdateEveryMs
  ├── HAUL-001/
  │   ├── temperature
  │   ├── vibration
  │   ├── pressure
  │   ├── throughput
  │   └── speed
  ├── HAUL-002/
  ...
  └── CONV-002/
```

## Timer Script Setup (3 Steps)

### Step 1: Create Gateway Timer Script

**In Designer**:
1. Go to: **Project Browser** → Right-click anywhere → **Gateway Events** → **Timer Scripts**

Or **In Gateway Config**: http://localhost:8183/web/config
- Navigate to: **Scripting** → **Gateway Event Scripts**

### Step 2: Add New Timer Script

Click **Add New Timer Script** and configure:

```
Name: MiningOperationsSimulator
Execution Mode: Fixed Rate
Execution Rate: 1000  (milliseconds = 1 second)
Enabled: ✅ (checked)
```

### Step 3: Paste Script

Copy the entire contents of `timer_script_mining_operations.py` and paste into the script editor.

**Key line** (already updated for Sample_Tags provider):
```python
BASE = "[Sample_Tags]Mining"  # ✅ Correct for your setup
```

Click **Save**.

---

## Verify It's Working

### Method 1: Watch Tag Values

1. In Designer Tag Browser, expand: `[Sample_Tags] → Mining → HAUL-001`
2. Double-click `temperature`
3. Value should update every 1 second with realistic variations (70-90°C)

### Method 2: Check Gateway Logs

1. Gateway Config → **Status** → **Diagnostics** → **Logs**
2. Filter by: `mining.simulator`
3. You should see: `"Updated 50 tags successfully at <timestamp>"`

### Method 3: Check Script Status

1. Gateway Config → **Status** → **Scripting** → **Gateway Timer Scripts**
2. Find: `MiningOperationsSimulator`
3. **Last Execution** should update every second

---

## Expected Behavior

**Tag Values** (updating every second):
- **temperature**: 70-90°C (varies with shift, noise, anomalies)
- **vibration**: 2-4 mm/s
- **pressure**: 3-4 bar
- **throughput**: 900-1100 TPH
- **speed**: 90-110 RPM

**Patterns**:
- Higher production during day shift (8am-8pm): 1.2× multiplier
- Lower production at night (8pm-8am): 0.8× multiplier
- Weekend reduction: 0.7× multiplier
- ±10% Gaussian noise on all values
- 5% chance of anomaly spikes (1.3-1.5× baseline)

**Equipment Differences**:
- **Crushers**: Hotter (85-95°C), higher vibration (4-5 mm/s)
- **Conveyors**: Cooler (50-60°C), lower vibration (2-3 mm/s)
- **Haul Trucks**: Mid-range across all sensors

---

## Troubleshooting

### Tags Not Updating

**Check 1**: Is SimEnabled true?
```
Tag path: [Sample_Tags]Mining/Config/SimEnabled
Expected: true
```

**Check 2**: Is timer script enabled?
```
Gateway Config → Status → Scripting
Look for: MiningOperationsSimulator (Enabled)
```

**Check 3**: Check logs for errors
```
Gateway Logs → Filter: mining.simulator
Should see: "Updated 50 tags successfully"
```

### Script Shows Errors

**Common Error**: "Tag not found"
```
Error: [Sample_Tags]Mining/HAUL-001/temperature not found
```

**Solution**: Verify exact tag path in Tag Browser
- Provider must be: `Sample_Tags` (not `default`)
- Path must be: `Mining/HAUL-001/temperature`

**Test manually in Script Console**:
```python
# Test reading a tag
tag = "[Sample_Tags]Mining/HAUL-001/temperature"
value = system.tag.readBlocking([tag])[0].value
print "Temperature: %.2f" % value
```

---

## Zerobus Configuration

When configuring Zerobus to stream to Databricks, use:

```yaml
Tag Provider: Sample_Tags          ← Your provider name
Tag Path Pattern: Mining/*         ← No brackets in Zerobus config
Target: field_engineering.mining_demo.zerobus_sensor_stream
```

**Important**: Zerobus config doesn't use `[Sample_Tags]` prefix - just `Mining/*`

---

## Script Details

**Updated Line 8**:
```python
BASE = "[Sample_Tags]Mining"  # ✅ Uses Sample_Tags provider
```

**What happens every 1 second**:
1. Check if `[Sample_Tags]Mining/Config/SimEnabled` is true
2. For each of 50 tags (10 equipment × 5 sensors):
   - Calculate baseline value
   - Add equipment-specific adjustment
   - Apply shift multiplier (day/night)
   - Apply weekend reduction
   - Add ±10% noise
   - Maybe inject 5% anomaly
   - Clamp to realistic range
3. Batch write all 50 tag values
4. Log: "Updated 50 tags successfully"

---

## Quick Test

Run in **Script Console** (Designer → Tools → Script Console):

```python
# Test tag paths
tags = [
    "[Sample_Tags]Mining/HAUL-001/temperature",
    "[Sample_Tags]Mining/HAUL-001/vibration",
    "[Sample_Tags]Mining/Config/SimEnabled"
]

results = system.tag.readBlocking(tags)
for i, tag_path in enumerate(tags):
    value = results[i].value
    print "%s = %s" % (tag_path.split('/')[-1], value)
```

**Expected Output**:
```
temperature = 78.43
vibration = 3.21
SimEnabled = True
```

---

## Tag Path Reference

**Your Structure**:
```
Provider: Sample_Tags              ← Separate tag provider
Path: Mining/HAUL-001/temperature  ← No Sample_Tags folder
Full: [Sample_Tags]Mining/HAUL-001/temperature
```

**NOT** (this would be wrong):
```
Provider: default
Path: Sample_Tags/Mining/HAUL-001/temperature
Full: [default]Sample_Tags/Mining/HAUL-001/temperature
```

---

**Status**: ✅ Script updated for `[Sample_Tags]` provider
**Next**: Copy script into Gateway Timer Script and enable
**Expected**: 50 tags updating every second with realistic mining operations data
