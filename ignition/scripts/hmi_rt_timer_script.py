import random

BASE = {
    "REACTOR_01": {"temperature": 79.0, "flow_rate": 138.0},
    "REACTOR_02": {"temperature": 92.0, "flow_rate": 125.0},
    "PUMP_07": {"temperature": 73.0, "flow_rate": 86.0},
    "PUMP_08": {"temperature": 70.5, "flow_rate": 91.0},
    "HEAT_EX_2": {"temperature": 83.0, "flow_rate": 108.0},
    "HEAT_EX_3": {"temperature": 81.0, "flow_rate": 112.0},
    "HAUL-001": {"temperature": 96.0, "flow_rate": 90.0},
}

BOUNDS = {
    "temperature": (60.0, 110.0),
    "flow_rate": (70.0, 170.0),
}

paths = []
for equipment in BASE.keys():
    paths.append("[default]HMI_RT/{0}/temperature".format(equipment))
    paths.append("[default]HMI_RT/{0}/flow_rate".format(equipment))

reads = system.tag.readBlocking(paths)

write_paths = []
write_vals = []

for idx, path in enumerate(paths):
    current = reads[idx].value
    if current is None:
        sensor = "temperature" if path.endswith("/temperature") else "flow_rate"
        equipment = path.split("/")[-2]
        current = BASE[equipment][sensor]

    sensor = "temperature" if path.endswith("/temperature") else "flow_rate"

    # Random-walk drift.
    step = random.uniform(-0.8, 0.8) if sensor == "temperature" else random.uniform(-2.5, 2.5)
    new_val = float(current) + step

    # Occasional disturbance on REACTOR_02 / HAUL-001 for demo realism.
    if ("REACTOR_02" in path or "HAUL-001" in path) and random.random() < 0.08:
        if sensor == "temperature":
            new_val += random.uniform(1.5, 3.0)
        else:
            new_val -= random.uniform(2.0, 6.0)

    low, high = BOUNDS[sensor]
    if new_val < low:
        new_val = low + random.uniform(0.0, 0.5)
    if new_val > high:
        new_val = high - random.uniform(0.0, 0.5)

    write_paths.append(path)
    write_vals.append(round(new_val, 1))

system.tag.writeBlocking(write_paths, write_vals)
