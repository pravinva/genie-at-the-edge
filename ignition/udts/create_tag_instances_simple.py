"""
Simple Tag Instance Creator for Ignition Designer Script Console
Run this in Designer: Tools > Script Console
"""

# Create folder structure
provider = "[default]"
base_path = provider + "Mining"
equipment_path = base_path + "/Equipment"

print("Creating folder structure...")

# Create Mining folder
if not system.tag.exists(base_path):
    system.tag.addTag(parentPath=provider, name="Mining", tagType="Folder")
    print("Created: " + base_path)

# Create Equipment folder
if not system.tag.exists(equipment_path):
    system.tag.addTag(parentPath=base_path, name="Equipment", tagType="Folder")
    print("Created: " + equipment_path)

print("\nCreating equipment instances...")

# Create 5 Haul Trucks
for i in range(1, 6):
    truck_id = "HT_%03d" % i
    tag_path = equipment_path + "/" + truck_id
    if not system.tag.exists(tag_path):
        system.tag.addTag(
            parentPath=equipment_path,
            name=truck_id,
            tagType="UdtInstance",
            typeId="HaulTruck"
        )
        print("Created: " + truck_id)
    else:
        print("Already exists: " + truck_id)

# Create 3 Crushers
for i in range(1, 4):
    crusher_id = "CR_%03d" % i
    tag_path = equipment_path + "/" + crusher_id
    if not system.tag.exists(tag_path):
        system.tag.addTag(
            parentPath=equipment_path,
            name=crusher_id,
            tagType="UdtInstance",
            typeId="Crusher"
        )
        print("Created: " + crusher_id)
    else:
        print("Already exists: " + crusher_id)

# Create 2 Conveyors
for i in range(1, 3):
    conveyor_id = "CV_%03d" % i
    tag_path = equipment_path + "/" + conveyor_id
    if not system.tag.exists(tag_path):
        system.tag.addTag(
            parentPath=equipment_path,
            name=conveyor_id,
            tagType="UdtInstance",
            typeId="Conveyor"
        )
        print("Created: " + conveyor_id)
    else:
        print("Already exists: " + conveyor_id)

print("\n" + "="*60)
print("COMPLETE!")
print("Created 10 equipment instances:")
print("  - 5 Haul Trucks (70 tags)")
print("  - 3 Crushers (27 tags)")
print("  - 2 Conveyors (10 tags)")
print("Total: 107 tags")
print("="*60)
