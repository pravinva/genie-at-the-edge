# UDT Quick Start Guide

## 30-Second Overview

This workstream creates 107 tags for mining equipment simulation:
- **5 Haul Trucks** (HT_001 to HT_005): GPS, speed, load, fuel, tires, vibration
- **3 Crushers** (CR_001 to CR_003): Throughput, vibration, motor current, alarms
- **2 Conveyors** (CV_001, CV_002): Speed, load, alignment, alarms

## Fastest Setup (5 Minutes)

### Option 1: Import JSON Files

1. Open Ignition Designer
2. Tag Browser > Data Types > UDT Definitions > Right-click > Import
3. Import each JSON file:
   - `HaulTruck_UDT.json`
   - `Crusher_UDT.json`
   - `Conveyor_UDT.json`
4. Tools > Script Console > Copy/paste `create_tag_instances.py` > Run
5. Done! Tags created at `[default]Mining/Equipment/`

### Option 2: Run Python Script Only

1. Open Ignition Designer
2. Tools > Script Console
3. Copy/paste entire contents of `create_tag_instances.py`
4. Click Run (or Ctrl+Enter)
5. Verify output shows "SUCCESS! All tag instances created"

## Validation (1 Minute)

Run validation tests to confirm everything works:

1. Tools > Script Console
2. Copy/paste entire contents of `validation_tests.py`
3. Click Run
4. Expected: "Total Tests: 8, Passed: 8, Failed: 0"

## Tag Access Examples

```python
# Read truck speed
speed = system.tag.readBlocking(["[default]Mining/Equipment/HT_001/Speed_KPH"])[0].value

# Write crusher vibration
system.tag.writeBlocking(["[default]Mining/Equipment/CR_001/Vibration_MM_S"], [45.0])

# Test alarm (set vibration >40 to trigger HIGH alarm)
system.tag.writeBlocking(["[default]Mining/Equipment/CR_002/Vibration_MM_S"], [50.0])
```

## What's Next?

After UDT setup is complete:

1. **File 02**: Physics simulation (makes equipment move/operate realistically)
2. **File 03**: HMI dashboard (visual displays)
3. **File 04**: Databricks data pipeline
4. **File 05**: Genie AI natural language queries

## File Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| `HaulTruck_UDT.json` | Haul truck definition | Import into Ignition Designer |
| `Crusher_UDT.json` | Crusher definition | Import into Ignition Designer |
| `Conveyor_UDT.json` | Conveyor definition | Import into Ignition Designer |
| `create_tag_instances.py` | Auto-create all tags | Run in Script Console |
| `validation_tests.py` | Verify setup correct | Run after tag creation |
| `README.md` | Full documentation | Reference guide |
| `QUICK_START.md` | This file | Fast setup |

## Common Questions

**Q: Can I use a different tag provider?**
A: Yes, edit the `provider = "[default]"` line in Python scripts.

**Q: Do I need to create UDTs manually?**
A: No, the Python script creates instances automatically. Just run `create_tag_instances.py`.

**Q: How do I test if alarms work?**
A: Set `CR_001/Vibration_MM_S` to 45 (>40 threshold). Check Gateway > Status > Alarms.

**Q: Why are my tag values all zero?**
A: Normal! Values get populated when you run the physics simulation script (File 02).

**Q: Can I add more trucks/crushers?**
A: Yes, edit the `truck_ids`, `crusher_ids`, `conveyor_ids` lists in `create_tag_instances.py`.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Script fails with "UDT type not found" | Import JSON files first, OR create UDTs manually |
| Tags not visible | Check Tag Browser provider is `[default]` |
| Alarms don't fire | Configure alarm pipeline in Gateway > Config > Alarming |
| Quality shows "Bad" | Normal for new memory tags, run physics simulation |

## Support

- Full docs: See `README.md` in this directory
- Ignition help: https://docs.inductiveautomation.com/
- Demo context: See `/prompts/ralph_wiggum_01_udts.md`

---

**Time to Complete:** 5-10 minutes
**Difficulty:** Beginner
**Prerequisites:** Ignition 8.1+ Designer access
