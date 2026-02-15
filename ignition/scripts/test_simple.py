# Simple test script - just increment a counter
import system.tag

TAG_PATH = "[default]Mining/Equipment/HT_001/Speed_KPH"

# Read current value
current = system.tag.readBlocking([TAG_PATH])[0].value

# Increment or start at 0
if current is None:
    new_value = 0.0
else:
    new_value = float(current) + 1.0
    if new_value > 100.0:
        new_value = 0.0

# Write it back
system.tag.writeBlocking([TAG_PATH], [new_value])

print("Updated " + TAG_PATH + " to: " + str(new_value))
