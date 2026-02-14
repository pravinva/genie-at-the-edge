# RALPH WIGGUM WORKSTREAM - FILE 02
## Ignition Gateway Timer Script: Physics Simulation

**Purpose:** Realistic mining equipment behavior simulation
**Location:** Ignition Gateway > Config > Scripting > Timer Scripts
**Trigger:** Fixed Rate, 1000ms (every 1 second)
**Language:** Python (Jython 2.7 in Ignition)
**Dependencies:** File 01 (UDT instances must exist)

---

## CLAUDE CODE PROMPT

```
Create an Ignition Gateway Timer Script that simulates realistic mining equipment physics and behavior.

CONTEXT:
This script runs every 1 second in Ignition Gateway and updates memory tags to simulate:
- 5 haul trucks executing realistic load-haul-dump cycles
- 3 crushers processing ore with realistic throughput/vibration
- 2 conveyors transferring material
- Environmental sensors (dust, noise, weather)

The simulation should be physics-based, not random:
- Haul trucks follow 23-minute cycles
- Loaded trucks are slower than empty trucks
- Engine temperature correlates with load
- Fuel consumption varies by speed and load
- Vibration correlates with speed and condition

REQUIREMENTS:

1. USE IGNITION'S TAG SYSTEM:
   - Read tags: system.tag.readBlocking([paths])
   - Write tags: system.tag.writeBlocking([paths], [values])
   - All paths start with: "[default]Mining/Equipment/"

2. REALISTIC PHYSICS:
   - Use proper equations, not just random numbers
   - Values should correlate (speed affects fuel, load affects temp)
   - Smooth transitions (no sudden jumps)
   - Realistic ranges (don't exceed equipment specs)

3. HAUL TRUCK CYCLE (23 minutes total):
   - Loading (0-5 min): Stopped, load increases 0→250t gradually
   - Hauling (5-13 min): Speed 25-30 km/h, load=250t, high fuel consumption
   - Dumping (13-16 min): Stopped, load decreases 250→0t gradually
   - Returning (16-23 min): Speed 45-55 km/h, load=0t, medium fuel
   - Reset: Cycle repeats

4. CRUSHER OPERATION:
   - Normal: Throughput 2200-2500 t/hr, vibration 18-22 mm/s
   - Vibration varies with throughput (higher throughput = slightly higher vib)
   - Motor current correlates with load
   - Runtime hours increment continuously when running

5. STATE MANAGEMENT:
   - Use each equipment's Cycle_Time_Sec tag to track state
   - Increment every second
   - Reset cycles appropriately
   - Maintain smooth continuity (no glitches)

6. REALISTIC VARIATION:
   - Add small random noise (±2-5% of nominal)
   - Simulate operator variability (different operators = slight performance difference)
   - Weather effects on dust/noise
   - Time-of-day effects (temperature)

7. ERROR HANDLING:
   - Try/except for tag reads/writes
   - Log errors to: system.util.getLogger("PhysicsSimulation")
   - Continue running even if one equipment fails to update
   - Every 60 seconds, log summary statistics

SCRIPT STRUCTURE:

```python
import system.tag
import system.util
import random
from java.lang import Math, System

# Logger for debugging
logger = system.util.getLogger("MiningPhysicsSimulation")

# Global state (persists across executions in Gateway memory)
# Use Gateway script globals or tags for state persistence

def simulate_haul_truck(truck_id):
    """
    Simulate realistic haul truck cycle
    23-minute cycle: Load(5m) → Haul(8m) → Dump(3m) → Return(7m)
    """
    base_path = f"[default]Mining/Equipment/{truck_id}/"
    
    try:
        # Read current state
        tag_paths = [
            base_path + "Cycle_Time_Sec",
            base_path + "Fuel_Level_Pct",
            base_path + "Hours_Operated"
        ]
        values = system.tag.readBlocking(tag_paths)
        cycle_time = values[0].value
        fuel = values[1].value
        hours = values[2].value
        
        # Increment cycle (wraps at 1380 = 23 minutes)
        cycle_time = (cycle_time + 1) % 1380
        
        # Determine state based on cycle time
        if cycle_time < 300:  # 0-5 min: Loading
            state = "loading"
            speed = 0
            load = min(250, cycle_time * 0.833)  # Linear load: 0→250 in 300s
            fuel_delta = -0.02  # Low consumption when stationary
            engine_temp = 85 + random.uniform(-1, 1)
            
        elif cycle_time < 780:  # 5-13 min: Hauling loaded
            state = "hauling_loaded"
            speed = 27 + random.uniform(-2, 2)  # Slower when loaded
            load = 250
            fuel_delta = -0.08  # High consumption
            engine_temp = 95 + random.uniform(-2, 2)  # Hot when working hard
            
        elif cycle_time < 960:  # 13-16 min: Dumping
            state = "dumping"
            speed = 0
            load = max(0, 250 - (cycle_time - 780) * 1.389)  # Linear dump
            fuel_delta = -0.02
            engine_temp = 90 + random.uniform(-1, 1)  # Cooling down
            
        else:  # 16-23 min: Returning empty
            state = "returning_empty"
            speed = 50 + random.uniform(-3, 3)  # Faster when empty
            load = 0
            fuel_delta = -0.05  # Medium consumption
            engine_temp = 88 + random.uniform(-2, 2)
        
        # Refuel when low
        new_fuel = fuel + fuel_delta
        if new_fuel < 20:
            new_fuel = 100  # Instant refuel for demo simplicity
        
        # Vibration correlates with speed
        vibration = 2.0 + (speed / 15.0) + random.uniform(-0.3, 0.3)
        
        # Location changes during cycle (simple linear path for demo)
        location_offset = cycle_time / 1380.0 * 0.02  # Moves in pattern
        location_lat = -31.9505 + location_offset * Math.sin(cycle_time / 100.0)
        location_lon = 115.8605 + location_offset * Math.cos(cycle_time / 100.0)
        
        # Tire pressure (slight variation, occasional low tire)
        tire_base = 100
        tire_var = random.uniform(-1, 1)
        
        # Runtime hours (increment when moving)
        hours_delta = 1.0/3600 if speed > 0 else 0  # 1 second = 1/3600 hour
        new_hours = hours + hours_delta
        
        # Write all updates
        write_paths = [
            base_path + "Cycle_Time_Sec",
            base_path + "Cycle_State",
            base_path + "Speed_KPH",
            base_path + "Load_Tonnes",
            base_path + "Fuel_Level_Pct",
            base_path + "Engine_Temp_C",
            base_path + "Vibration_MM_S",
            base_path + "Location_Lat",
            base_path + "Location_Lon",
            base_path + "Tire_Pressure_FL_PSI",
            base_path + "Tire_Pressure_FR_PSI",
            base_path + "Tire_Pressure_RL_PSI",
            base_path + "Tire_Pressure_RR_PSI",
            base_path + "Hours_Operated"
        ]
        
        write_values = [
            cycle_time,
            state,
            speed,
            load,
            new_fuel,
            engine_temp,
            vibration,
            location_lat,
            location_lon,
            tire_base + tire_var,
            tire_base + random.uniform(-1, 1),
            tire_base + random.uniform(-1, 1),
            tire_base + random.uniform(-1, 1),
            new_hours
        ]
        
        system.tag.writeBlocking(write_paths, write_values)
        
    except Exception as e:
        logger.error(f"Error simulating {truck_id}: {str(e)}")

def simulate_crusher(crusher_id, is_fault=False):
    """
    Simulate crusher operation
    is_fault: Set True for CR_002 to simulate degradation (File 03 handles this)
    """
    base_path = f"[default]Mining/Equipment/{crusher_id}/"
    
    try:
        # Read current state
        tag_paths = [
            base_path + "Runtime_Hours",
            base_path + "Throughput_TPH",
            base_path + "Vibration_MM_S"
        ]
        values = system.tag.readBlocking(tag_paths)
        runtime = values[0].value
        current_throughput = values[1].value
        current_vibration = values[2].value
        
        # Normal operation (if not in fault state)
        if not is_fault:
            # Target throughput with slight variation
            target_throughput = 2400
            throughput = target_throughput + random.uniform(-100, 100)
            
            # Normal vibration (correlates with throughput)
            base_vibration = 20
            throughput_factor = (throughput - 2400) / 2400 * 2  # ±2 mm/s based on load
            vibration = base_vibration + throughput_factor + random.uniform(-1, 1)
            
            # Motor current correlates with throughput
            motor_current = 200 * (throughput / 2400) + random.uniform(-5, 5)
            
            # Belt speed relatively constant
            belt_speed = 2.0 + random.uniform(-0.05, 0.05)
            
            # Chute level oscillates
            chute_level = 60 + 20 * Math.sin(runtime * 10)  # Oscillates over time
            
            # Motor temp correlates with load
            motor_temp = 75 + (throughput - 2400) / 100
            
            status = "RUNNING"
            
        # Fault state handled by File 03 (fault injection script)
        # This script just does normal operation
        
        # Feed rate (input to crusher, slightly higher than throughput)
        feed_rate = throughput * 1.05
        
        # Increment runtime
        new_runtime = runtime + (1.0/3600)  # 1 second in hours
        
        # Write updates
        write_paths = [
            base_path + "Status",
            base_path + "Throughput_TPH",
            base_path + "Vibration_MM_S",
            base_path + "Motor_Current_A",
            base_path + "Belt_Speed_M_S",
            base_path + "Chute_Level_Pct",
            base_path + "Runtime_Hours",
            base_path + "Feed_Rate_TPH",
            base_path + "Motor_Temp_C"
        ]
        
        write_values = [
            status,
            throughput,
            vibration,
            motor_current,
            belt_speed,
            chute_level,
            new_runtime,
            feed_rate,
            motor_temp
        ]
        
        system.tag.writeBlocking(write_paths, write_values)
        
    except Exception as e:
        logger.error(f"Error simulating {crusher_id}: {str(e)}")

def simulate_conveyor(conveyor_id):
    """
    Simulate conveyor belt operation
    """
    base_path = f"[default]Mining/Equipment/{conveyor_id}/"
    
    try:
        # Read current
        current_load = system.tag.readBlocking([base_path + "Load_Pct"])[0].value
        
        # Target load oscillates (material flow varies)
        import time
        time_factor = time.time() / 10  # Slow oscillation
        target_load = 60 + 20 * Math.sin(time_factor)
        
        # Smooth transition to target
        load = current_load * 0.9 + target_load * 0.1  # 10% step toward target
        
        # Motor temp correlates with load
        motor_temp = 65 + load * 0.15
        
        # Belt alignment (slight wander, stays centered)
        alignment = random.uniform(-1, 1)
        
        # Speed constant
        speed = 2.5 + random.uniform(-0.05, 0.05)
        
        # Status
        status = "RUNNING"
        
        # Write
        system.tag.writeBlocking([
            base_path + "Speed_M_S",
            base_path + "Load_Pct",
            base_path + "Motor_Temp_C",
            base_path + "Belt_Alignment_MM",
            base_path + "Status"
        ], [
            speed,
            load,
            motor_temp,
            alignment,
            status
        ])
        
    except Exception as e:
        logger.error(f"Error simulating {conveyor_id}: {str(e)}")

# ============================================
# MAIN EXECUTION (Runs every 1 second)
# ============================================

def execute_simulation():
    """
    Main execution function called by Timer Script
    """
    try:
        # Simulate all haul trucks
        for i in range(1, 6):
            truck_id = f"HT_{i:03d}"
            simulate_haul_truck(truck_id)
        
        # Simulate all crushers
        # Note: CR_002 fault is handled by separate script (File 03)
        # This script does normal operation for all
        for i in range(1, 4):
            crusher_id = f"CR_{i:03d}"
            simulate_crusher(crusher_id, is_fault=False)
        
        # Simulate conveyors
        for i in range(1, 3):
            conveyor_id = f"CV_{i:03d}"
            simulate_conveyor(conveyor_id)
        
        # Every 60 seconds, log summary
        # Get current time from system
        current_millis = System.currentTimeMillis()
        if current_millis % 60000 < 1000:  # Approximately every 60 seconds
            logger.info("Physics simulation running - all equipment updated")
            
    except Exception as e:
        logger.error(f"Physics simulation error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

# Execute
execute_simulation()
```

---

## ADDITIONAL FEATURES (Optional Enhancements)

**Add operator shift changes:**

```python
def get_current_shift_operator():
    """
    Return operator ID based on time of day
    Day shift (06:00-18:00): OP_101 to OP_110
    Night shift (18:00-06:00): OP_111 to OP_120
    """
    from datetime import datetime
    hour = datetime.now().hour
    
    if 6 <= hour < 18:  # Day shift
        operator_pool = range(101, 111)
    else:  # Night shift
        operator_pool = range(111, 121)
    
    # Rotate operators (simple hash based on hour)
    operator_index = hour % len(operator_pool)
    return f"OP_{operator_pool[operator_index]}"

# In simulate_haul_truck, update operator assignment:
operator = get_current_shift_operator()
# Write to Operator_ID tag
```

**Add weather simulation:**

```python
def simulate_weather():
    """
    Environmental conditions affecting operations
    """
    import time
    time_of_day = (time.time() % 86400) / 86400  # 0-1 for 24 hours
    
    # Temperature: Cooler at night, hotter at 2pm
    base_temp = 30
    daily_variation = 8 * Math.sin((time_of_day - 0.25) * 2 * Math.pi)  # Peak at 2pm
    temp = base_temp + daily_variation + random.uniform(-1, 1)
    
    # Dust: Higher when crushers running high throughput
    # Read all crusher throughputs
    crusher_total = 0
    for i in range(1, 4):
        path = f"[default]Mining/Equipment/CR_{i:03d}/Throughput_TPH"
        crusher_total += system.tag.readBlocking([path])[0].value
    
    # More throughput = more dust
    base_dust = 15
    crusher_dust = (crusher_total / 7200) * 30  # Max 30 when all running full
    dust = base_dust + crusher_dust + random.uniform(-3, 3)
    
    # Wind (random walk)
    # Would need persistent state - use tag or global variable
    
    # Write to environmental tags (if created)
    # system.tag.writeBlocking([...], [temp, dust, ...])
```

---

## DEPLOYMENT STEPS

**In Ignition Gateway:**

1. Navigate to: Config > Scripting > Gateway Event Scripts
2. Click: Timer Scripts > Add Timer Script
3. Configure:
   - Name: "MiningPhysicsSimulation"
   - Description: "Realistic equipment behavior simulation"
   - Enabled: ✓ (checked)
   - Execution: Fixed Rate
   - Delay (seconds): 1 (run every 1 second)
   - Initial Delay: 0
   
4. Paste the script code (generated by Claude Code above)
5. Save
6. Monitor: Gateway > Status > Diagnostics > Timer Scripts
   - Should show: Last run time updating every second
   - Errors: 0

---

## VALIDATION

**After deploying script:**

1. **Tag updates visible:**
   ```
   Tag Browser > [default]Mining/Equipment/HT_001/Speed_KPH
   - Value should be changing every second
   - Watch for 2-3 minutes
   - Should see cycle: 0 (loading) → 27 (hauling) → 50 (returning) → 0 (repeat)
   ```

2. **Realistic values:**
   ```
   Check correlations:
   - When Speed high → Fuel decreasing faster
   - When Load_Tonnes high → Engine_Temp_C higher
   - Cycle_State matches Cycle_Time_Sec
   ```

3. **No errors:**
   ```
   Gateway > Status > Diagnostics > Logs > Wrapper.log
   - Search for "PhysicsSimulation"
   - Should see INFO logs every 60s, no ERRORs
   ```

4. **Performance:**
   ```
   Gateway > Status > Diagnostics > Performance
   - Timer script execution time should be <50ms
   - CPU usage should be negligible (<1%)
   ```

---

## TROUBLESHOOTING

**Tags not updating:**
- Check script is enabled and running (Gateway > Config > Scripting)
- Check for errors in logs (Gateway > Status > Diagnostics > Logs)
- Verify tag paths are correct (case-sensitive)
- Test tag writes manually in script console

**Values are unrealistic:**
- Review physics equations
- Check for typos in calculations
- Verify random.uniform ranges are appropriate
- Add logger.info() to debug specific equipment

**Performance issues:**
- Reduce update frequency if needed (1000ms → 2000ms)
- Optimize tag writes (batch more efficiently)
- Remove unnecessary logger.info() calls

**Script stops running:**
- Check for uncaught exceptions
- Add try/except around entire execute_simulation()
- Review Java heap settings (Gateway > Config > Gateway Settings)

---

## COMPLETION CHECKLIST

- [ ] Script created in Gateway Timer Scripts
- [ ] Enabled and running every 1 second
- [ ] All 15 equipment instances updating (105 tags total)
- [ ] Values are realistic (correlations make sense)
- [ ] Haul truck cycles visible (23-minute pattern)
- [ ] Crusher throughput varies realistically
- [ ] No errors in Gateway logs
- [ ] CPU usage acceptable (<5%)
- [ ] Ready for Zerobus integration (File 03)

---

**Estimated time:** 2-3 hours (including Claude Code generation + testing)
**Next:** File 03 - Fault injection for CR_002 demonstration
