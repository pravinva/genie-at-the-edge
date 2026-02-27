# Ignition Gateway Timer Script (Jython) - Mining Operations Simulator
# Simplified version for Sample_Tags provider
# Writes: [Sample_Tags]Mining/<equipment_id>/<sensor_name>

import random

# Main execution - super simple, no functions that could fail
try:
    BASE = "[Sample_Tags]Mining"

    # Equipment and sensors
    equipment_list = ["HAUL-001", "HAUL-002", "HAUL-003", "HAUL-004", "HAUL-005",
                      "CRUSH-001", "CRUSH-002", "CRUSH-003", "CONV-001", "CONV-002"]
    sensor_list = ["temperature", "vibration", "pressure", "throughput", "speed"]

    # Prepare tag paths and values
    paths = []
    values = []

    # Get current hour for shift adjustment
    hour = system.date.getHour24(system.date.now())
    shift_mult = 1.2 if (8 <= hour < 20) else 0.8

    # Generate values for each tag
    for equipment in equipment_list:
        for sensor in sensor_list:
            # Build tag path
            tag_path = BASE + "/" + equipment + "/" + sensor

            # Generate base value based on sensor type
            if sensor == "temperature":
                if "CRUSH" in equipment:
                    base = 85.0  # Crushers run hotter
                elif "CONV" in equipment:
                    base = 55.0  # Conveyors cooler
                else:
                    base = 75.0  # Haul trucks
            elif sensor == "vibration":
                base = 4.5 if "CRUSH" in equipment else 3.0
            elif sensor == "pressure":
                base = 5.0 if "CRUSH" in equipment else 3.5
            elif sensor == "throughput":
                base = 1000.0
            elif sensor == "speed":
                base = 450.0 if "CRUSH" in equipment else 100.0
            else:
                base = 50.0

            # Apply shift multiplier and add random variation
            value = base * shift_mult
            value = value + random.uniform(-value*0.1, value*0.1)  # ±10% variation

            # Maybe add anomaly (5% chance)
            if random.random() < 0.05:
                value = value * random.uniform(1.3, 1.5)

            # Round to 2 decimal places
            value = round(value, 2)

            # Add to lists
            paths.append(tag_path)
            values.append(value)

    # Write all tags at once
    if len(paths) > 0:
        results = system.tag.writeBlocking(paths, values)

        # Count successes
        good_count = 0
        for result in results:
            if result.isGood():
                good_count += 1

        # Log result
        timestamp = system.date.format(system.date.now(), "HH:mm:ss")
        if good_count == len(paths):
            system.util.getLogger("mining.simulator").info("OK: %d tags at %s" % (good_count, timestamp))
        else:
            system.util.getLogger("mining.simulator").warn("Updated %d of %d tags" % (good_count, len(paths)))
    else:
        system.util.getLogger("mining.simulator").error("No tags generated")

except Exception as e:
    system.util.getLogger("mining.simulator").error("ERROR: %s" % str(e))