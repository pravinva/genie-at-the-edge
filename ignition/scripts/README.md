# Mining Operations Physics Simulation Scripts

## Overview

This directory contains production-ready Python scripts for simulating realistic mining equipment behavior in Ignition Gateway. The simulation is physics-based and demonstrates advanced industrial IoT patterns for the **Genie at the Edge** demo.

## Architecture

```
ignition/scripts/
 README.md                          (this file)
 mining_physics_simulation.py       (main Gateway Timer Script)
 fault_injection_cr002.py          (CR_002 degradation script)
 physics_utils.py                  (helper functions & constants)
 deployment_guide.md               (step-by-step deployment)
 testing_script.py                 (validation & testing)
```

## Components

### 1. mining_physics_simulation.py
**Purpose:** Main Gateway Timer Script (runs every 1 second)
**Updates:** 105 tags across 15 equipment instances
**Equipment:**
- 5 Haul Trucks (HT_001 to HT_005): 23-minute load-haul-dump cycles
- 3 Crushers (CR_001 to CR_003): Continuous ore processing
- 2 Conveyors (CV_001, CV_002): Material transfer

**Key Features:**
- Physics-based calculations (not random)
- Realistic correlations (speed affects fuel, load affects temperature)
- Smooth state transitions
- Operator shift management
- Performance optimized (<50ms execution time)

### 2. fault_injection_cr002.py
**Purpose:** Simulate bearing degradation for CR_002 demonstration
**Trigger:** Manual start via script console or scheduled event
**Timeline:** 48-hour degradation from normal → critical failure

**Fault Progression:**
- Hour 0-24: Normal operation (vibration 18-22 mm/s)
- Hour 24-36: Early degradation (vibration rises to 28-32 mm/s)
- Hour 36-42: Warning state (vibration 35-45 mm/s, throughput drops)
- Hour 42-48: Critical failure (vibration 55-70 mm/s, temperature spikes)

### 3. physics_utils.py
**Purpose:** Shared physics calculations and constants
**Functions:**
- Fuel consumption based on speed/load
- Engine temperature modeling
- Vibration calculations
- GPS path simulation
- Realistic noise generation

### 4. deployment_guide.md
**Purpose:** Step-by-step deployment instructions
**Covers:**
- Ignition Gateway configuration
- Timer Script setup
- Tag path validation
- Performance monitoring
- Troubleshooting

### 5. testing_script.py
**Purpose:** Validation and testing utilities
**Tests:**
- Tag read/write operations
- Physics calculation accuracy
- Cycle state transitions
- Performance benchmarks

## Quick Start

### Prerequisites
- Ignition Gateway 8.1+ installed
- UDT instances created (see `../prompts/ralph_wiggum_01_udts.md`)
- Tag structure: `[default]Mining/Equipment/`

### Deployment (5 minutes)

1. **Deploy main simulation:**
   ```
   Gateway > Config > Scripting > Timer Scripts > Add Timer Script
   Name: MiningPhysicsSimulation
   Delay: 1 second (Fixed Rate)
   Paste contents of: mining_physics_simulation.py
   ```

2. **Verify operation:**
   ```
   Tag Browser > [default]Mining/Equipment/HT_001/Speed_KPH
   Value should update every second
   ```

3. **Optional - Deploy fault injection:**
   ```
   Designer > Script Console
   Paste contents of: fault_injection_cr002.py
   Execute: start_cr002_fault_sequence()
   ```

## Physics Models

### Haul Truck Cycle (23 minutes)

| Phase | Duration | Speed | Load | Fuel Rate | Temp |
|-------|----------|-------|------|-----------|------|
| Loading | 0-5 min | 0 km/h | 0→250t | 0.02%/s | 85°C |
| Hauling | 5-13 min | 25-30 km/h | 250t | 0.08%/s | 95°C |
| Dumping | 13-16 min | 0 km/h | 250→0t | 0.02%/s | 90°C |
| Returning | 16-23 min | 45-55 km/h | 0t | 0.05%/s | 88°C |

**Key Equations:**
```python
# Load increases linearly during loading phase
load = min(250, cycle_time * 0.833)  # 250t in 300 seconds

# Fuel consumption based on speed and load
fuel_rate = 0.02 + (speed / 100) * 0.05 + (load / 250) * 0.03

# Engine temperature based on load and ambient
engine_temp = ambient_temp + (load / 250) * 15 + (speed / 50) * 5

# Vibration correlates with speed
vibration = 2.0 + (speed / 15.0) + noise(-0.3, 0.3)
```

### Crusher Operation

**Normal State:**
- Throughput: 2200-2500 t/hr (±100 t/hr variation)
- Vibration: 18-22 mm/s (correlates with throughput)
- Motor Current: 180-220 A (proportional to load)
- Motor Temp: 70-80°C

**Equations:**
```python
# Vibration correlates with throughput
base_vibration = 20.0  # mm/s nominal
throughput_factor = (throughput - 2400) / 2400 * 2
vibration = base_vibration + throughput_factor + noise(-1, 1)

# Motor current proportional to throughput
motor_current = 200 * (throughput / 2400) + noise(-5, 5)

# Chute level oscillates (material flow cycles)
chute_level = 60 + 20 * sin(runtime_hours * 10)
```

### Conveyor Operation

**Normal State:**
- Speed: 2.5 m/s (±0.05 m/s)
- Load: 40-80% (oscillates based on upstream feed)
- Motor Temp: 60-75°C (correlates with load)
- Belt Alignment: ±1 mm (slight wander, stays centered)

**Equations:**
```python
# Load oscillates based on upstream crushers
target_load = 60 + 20 * sin(time / 10)
current_load = 0.9 * current_load + 0.1 * target_load  # Smooth transition

# Motor temperature correlates with load
motor_temp = 65 + load * 0.15
```

## Performance

**Expected Performance:**
- Execution Time: 30-50ms per cycle
- CPU Usage: <1% on modern hardware
- Memory: ~10 MB (stable, no leaks)
- Tag Updates: 105 tags/second

**Optimization Techniques:**
- Batch tag reads/writes (reduce round trips)
- Pre-calculate constants
- Use try/except per equipment (isolation)
- Log summary only every 60 seconds

## Monitoring

### Gateway Diagnostics
```
Gateway > Status > Diagnostics > Timer Scripts
- MiningPhysicsSimulation should show:
  - Last Execution: <1 second ago
  - Execution Time: 30-50ms
  - Error Count: 0
```

### Tag Monitoring
```
Tag Browser > [default]Mining/Equipment/
Watch these key indicators:
- HT_001/Cycle_State (should cycle: loading → hauling → dumping → returning)
- CR_002/Vibration_MM_S (should be 18-22 mm/s in normal state)
- CV_001/Load_Pct (should oscillate 40-80%)
```

### Log Monitoring
```
Gateway > Status > Diagnostics > Logs > Wrapper.log
Search for: "MiningPhysicsSimulation"
Expected: INFO logs every 60 seconds, no ERROR logs
```

## Troubleshooting

### Tags Not Updating
**Symptom:** Values frozen in Tag Browser
**Causes:**
1. Timer Script not enabled
2. Tag path mismatch (case-sensitive)
3. Script execution error

**Solutions:**
```python
# Test tag write manually in Script Console:
system.tag.writeBlocking(["[default]Mining/Equipment/HT_001/Speed_KPH"], [50.0])

# Check for errors:
Gateway > Status > Diagnostics > Logs > Search "ERROR"

# Verify script enabled:
Gateway > Config > Scripting > Timer Scripts > MiningPhysicsSimulation
```

### Unrealistic Values
**Symptom:** Speed suddenly jumps 0→100, temperature negative, etc.
**Causes:**
1. Missing smooth transition logic
2. Incorrect equation
3. Tag initialization issue

**Solutions:**
- Add logging to debug specific equipment
- Verify physics constants in physics_utils.py
- Check cycle state transitions

### Performance Issues
**Symptom:** Execution time >100ms, Gateway slow
**Causes:**
1. Too many tag operations
2. Inefficient loops
3. Gateway resource constraints

**Solutions:**
- Increase update interval (1000ms → 2000ms)
- Optimize batch tag operations
- Remove unnecessary logger.info() calls

## Integration Points

### Zerobus MQTT (File 03)
The physics simulation writes to memory tags. A separate script (not included here) reads these tags and publishes to MQTT:
```
Topic: mining/equipment/{equipment_id}/telemetry
Payload: JSON with all tag values
Rate: 1 message/second per equipment
```

### Delta Live Tables (File 06)
MQTT messages are ingested by Databricks DLT pipeline:
```
Auto Loader → Bronze (raw MQTT) → Silver (validated) → Gold (aggregated)
```

### Genie Chat Interface (File 08)
User questions query Gold tables via SQL:
```sql
SELECT AVG(vibration_mm_s)
FROM mining_gold.crusher_telemetry
WHERE equipment_id = 'CR_002'
  AND timestamp > current_timestamp() - INTERVAL 1 HOUR
```

## Development Notes

### Python 2.7 Compatibility (Jython)
Ignition uses Jython 2.7, not Python 3. Key differences:
- Use `from java.lang import Math, System`
- No f-strings (use `.format()` or `%` formatting)
- Import `random` from Python stdlib
- Use `system.tag.*` for tag operations (Ignition API)

### State Management
Timer Scripts are stateless (each execution is isolated). To maintain state:
- **Option 1:** Use memory tags (read current value, update, write back)
- **Option 2:** Use Gateway script globals (limited, not recommended)
- **Chosen:** Memory tags for cycle time, runtime hours, fuel level

### Testing Without Gateway
The scripts require Ignition Gateway to run (no standalone execution). For development:
1. Use Ignition Designer's Script Console
2. Mock `system.tag.*` functions
3. Test physics calculations in pure Python separately

## References

- Ignition Scripting Functions: https://docs.inductiveautomation.com/
- Mining Equipment Specs: Based on Caterpillar 797F (haul truck), Metso C160 (crusher)
- Physics Models: First-principles calculations + empirical adjustments

## Authors

**Generated by:** Claude Code (Anthropic)
**Project:** Genie at the Edge - Mining Operations Demo
**Date:** 2026-02-14
**Version:** 1.0

## License

This code is part of a Databricks demonstration project for Australian Retirement Trust.
Not for production use without proper validation and safety review.
