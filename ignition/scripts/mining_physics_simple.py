# Mining Equipment Physics Simulation - Simplified Version
# Gateway Timer Script - runs every 1 second
# Based on working pattern from kredsloeb reference

import system.tag
import random

# Base paths
BASE = "[default]Mining/Equipment"

# Equipment lists
TRUCKS = ["HT_001", "HT_002", "HT_003", "HT_004", "HT_005"]
CRUSHERS = ["CR_001", "CR_002", "CR_003"]
CONVEYORS = ["CV_001", "CV_002"]

# Haul truck cycle constants (23 minutes = 1380 seconds)
CYCLE_TOTAL = 1380
LOADING_END = 300      # 0-5 min
HAULING_END = 780      # 5-13 min
DUMPING_END = 960      # 13-16 min
RETURNING_END = 1380   # 16-23 min

# ===== HAUL TRUCKS =====
for truck_id in TRUCKS:
    truck = BASE + "/" + truck_id

    # Read current cycle time
    cycle_sec = int(system.tag.readBlocking([truck + "/Cycle_Time_Sec"])[0].value or 0)

    # Increment cycle time
    cycle_sec = cycle_sec + 1
    if cycle_sec >= CYCLE_TOTAL:
        cycle_sec = 0

    # Determine state based on cycle time
    if cycle_sec < LOADING_END:
        state = "loading"
        speed = 0.0
        load = cycle_sec / float(LOADING_END) * 220.0  # Loading up to 220 tonnes
    elif cycle_sec < HAULING_END:
        state = "hauling_loaded"
        speed = 35.0 + random.uniform(-3.0, 3.0)
        load = 220.0
    elif cycle_sec < DUMPING_END:
        state = "dumping"
        speed = 0.0
        load = 220.0 - ((cycle_sec - HAULING_END) / float(DUMPING_END - HAULING_END) * 220.0)
    else:
        state = "returning_empty"
        speed = 45.0 + random.uniform(-3.0, 3.0)
        load = 0.0

    # Calculate other values based on state
    fuel = 100.0 - (cycle_sec / float(CYCLE_TOTAL) * 8.0)  # Loses 8% fuel per cycle
    fuel = max(20.0, fuel)

    if load > 100.0:
        engine_temp = 95.0 + random.uniform(-2.0, 3.0)
    elif speed > 20.0:
        engine_temp = 88.0 + random.uniform(-2.0, 2.0)
    else:
        engine_temp = 75.0 + random.uniform(-1.0, 1.0)

    tire_pressure = 100.0 + random.uniform(-2.0, 2.0)
    vibration = 3.0 + (speed / 50.0) * 2.0 + random.uniform(-0.5, 0.5)

    # GPS movement (simple)
    base_lat = -31.9505
    base_lon = 115.8605
    if state == "hauling_loaded":
        lat = base_lat + 0.001 * ((cycle_sec - LOADING_END) / float(HAULING_END - LOADING_END))
        lon = base_lon + 0.0015 * ((cycle_sec - LOADING_END) / float(HAULING_END - LOADING_END))
    elif state == "returning_empty":
        lat = base_lat + 0.001 * (1.0 - (cycle_sec - DUMPING_END) / float(RETURNING_END - DUMPING_END))
        lon = base_lon + 0.0015 * (1.0 - (cycle_sec - DUMPING_END) / float(RETURNING_END - DUMPING_END))
    else:
        lat = base_lat
        lon = base_lon

    hours = cycle_sec / 3600.0

    # Write all values
    system.tag.writeBlocking(
        [
            truck + "/Cycle_Time_Sec",
            truck + "/Cycle_State",
            truck + "/Speed_KPH",
            truck + "/Load_Tonnes",
            truck + "/Fuel_Level_Pct",
            truck + "/Engine_Temp_C",
            truck + "/Tire_Pressure_FL_PSI",
            truck + "/Tire_Pressure_FR_PSI",
            truck + "/Tire_Pressure_RL_PSI",
            truck + "/Tire_Pressure_RR_PSI",
            truck + "/Vibration_MM_S",
            truck + "/Location_Lat",
            truck + "/Location_Lon",
            truck + "/Hours_Operated"
        ],
        [
            cycle_sec,
            state,
            speed,
            load,
            fuel,
            engine_temp,
            tire_pressure,
            tire_pressure + random.uniform(-1.0, 1.0),
            tire_pressure + random.uniform(-1.0, 1.0),
            tire_pressure + random.uniform(-1.0, 1.0),
            vibration,
            lat,
            lon,
            hours
        ]
    )

# ===== CRUSHERS =====
for crusher_id in CRUSHERS:
    crusher = BASE + "/" + crusher_id

    # Read current values
    throughput = float(system.tag.readBlocking([crusher + "/Throughput_TPH"])[0].value or 2000.0)
    vibration = float(system.tag.readBlocking([crusher + "/Vibration_MM_S"])[0].value or 12.0)

    # Vary throughput
    throughput = throughput + random.uniform(-50.0, 50.0)
    throughput = max(1800.0, min(2200.0, throughput))

    # Vibration correlates with throughput
    vibration = 10.0 + (throughput - 1800.0) / 400.0 * 5.0 + random.uniform(-0.5, 0.5)

    motor_current = 160.0 + (throughput - 1800.0) / 20.0 + random.uniform(-3.0, 3.0)
    motor_temp = 60.0 + (motor_current - 160.0) / 10.0 + random.uniform(-2.0, 2.0)
    bearing_temp = 50.0 + (vibration - 10.0) * 2.0 + random.uniform(-2.0, 2.0)
    feed_level = 60.0 + random.uniform(-10.0, 10.0)

    system.tag.writeBlocking(
        [
            crusher + "/Throughput_TPH",
            crusher + "/Vibration_MM_S",
            crusher + "/Motor_Current_A",
            crusher + "/Motor_Temp_C",
            crusher + "/Bearing_Temp_C",
            crusher + "/Feed_Level_Pct",
            crusher + "/Status"
        ],
        [
            throughput,
            vibration,
            motor_current,
            motor_temp,
            bearing_temp,
            feed_level,
            "running"
        ]
    )

# ===== CONVEYORS =====
for conveyor_id in CONVEYORS:
    conveyor = BASE + "/" + conveyor_id

    # Read values
    load_pct = float(system.tag.readBlocking([conveyor + "/Load_Pct"])[0].value or 70.0)

    # Vary load
    load_pct = load_pct + random.uniform(-5.0, 5.0)
    load_pct = max(60.0, min(80.0, load_pct))

    speed = 3.5
    alignment = random.uniform(-3.0, 3.0)
    motor_temp = 58.0 + (load_pct - 60.0) / 10.0 + random.uniform(-2.0, 2.0)

    system.tag.writeBlocking(
        [
            conveyor + "/Speed_M_S",
            conveyor + "/Load_Pct",
            conveyor + "/Belt_Alignment_MM",
            conveyor + "/Motor_Temp_C"
        ],
        [
            speed,
            load_pct,
            alignment,
            motor_temp
        ]
    )

print("Mining simulation tick complete")
