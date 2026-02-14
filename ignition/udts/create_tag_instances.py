"""
Ignition Tag Instance Creator for Mining Operations Demo
=========================================================

This script programmatically creates tag instances from UDT definitions.
Run this script from an Ignition Gateway Script or Perspective Session Script.

Equipment Instances:
- 5 Haul Trucks: HT_001 through HT_005 (14 tags each = 70 total)
- 3 Crushers: CR_001 through CR_003 (9 tags each = 27 total)
- 2 Conveyors: CV_001 through CV_002 (5 tags each = 10 total)
Total: 107 tags

Author: Generated for Databricks Genie Demo
Date: 2026-02-14
"""

import system.tag as tag


def create_folder_structure():
    """
    Create the folder structure for mining equipment tags.
    Creates: [default]Mining/Equipment/
    """
    provider = "[default]"
    base_path = provider + "Mining"
    equipment_path = base_path + "/Equipment"

    try:
        # Create Mining folder if it doesn't exist
        if not system.tag.exists(base_path):
            system.tag.addTag(
                parentPath=provider,
                name="Mining",
                tagType="Folder"
            )
            print("Created folder: {}".format(base_path))
        else:
            print("Folder already exists: {}".format(base_path))

        # Create Equipment subfolder if it doesn't exist
        if not system.tag.exists(equipment_path):
            system.tag.addTag(
                parentPath=base_path,
                name="Equipment",
                tagType="Folder"
            )
            print("Created folder: {}".format(equipment_path))
        else:
            print("Folder already exists: {}".format(equipment_path))

        return equipment_path

    except Exception as e:
        print("ERROR creating folder structure: {}".format(str(e)))
        raise


def create_haul_truck_instances(equipment_path, truck_ids):
    """
    Create haul truck tag instances.

    Args:
        equipment_path (str): Parent path for equipment tags
        truck_ids (list): List of truck IDs (e.g., ['HT_001', 'HT_002', ...])

    Returns:
        int: Number of instances created
    """
    udt_type = "HaulTruck"
    created_count = 0

    for truck_id in truck_ids:
        tag_path = "{}/{}".format(equipment_path, truck_id)

        try:
            if not system.tag.exists(tag_path):
                system.tag.addTag(
                    parentPath=equipment_path,
                    name=truck_id,
                    tagType="UdtInstance",
                    typeId=udt_type,
                    attributes={
                        "description": "Haul Truck {} - Mining operations vehicle".format(truck_id)
                    }
                )
                print("Created HaulTruck instance: {}".format(truck_id))
                created_count += 1
            else:
                print("HaulTruck instance already exists: {}".format(truck_id))

        except Exception as e:
            print("ERROR creating HaulTruck {}: {}".format(truck_id, str(e)))

    return created_count


def create_crusher_instances(equipment_path, crusher_ids):
    """
    Create crusher tag instances with alarm configurations.

    Args:
        equipment_path (str): Parent path for equipment tags
        crusher_ids (list): List of crusher IDs (e.g., ['CR_001', 'CR_002', ...])

    Returns:
        int: Number of instances created
    """
    udt_type = "Crusher"
    created_count = 0

    for crusher_id in crusher_ids:
        tag_path = "{}/{}".format(equipment_path, crusher_id)

        try:
            if not system.tag.exists(tag_path):
                system.tag.addTag(
                    parentPath=equipment_path,
                    name=crusher_id,
                    tagType="UdtInstance",
                    typeId=udt_type,
                    attributes={
                        "description": "Crusher {} - Primary ore crusher with vibration monitoring".format(crusher_id)
                    }
                )
                print("Created Crusher instance: {}".format(crusher_id))
                created_count += 1

                # Configure alarms on vibration tag
                configure_crusher_alarms(tag_path, crusher_id)
            else:
                print("Crusher instance already exists: {}".format(crusher_id))

        except Exception as e:
            print("ERROR creating Crusher {}: {}".format(crusher_id, str(e)))

    return created_count


def configure_crusher_alarms(crusher_path, crusher_id):
    """
    Configure vibration alarms for crusher instances.

    Args:
        crusher_path (str): Full path to crusher instance
        crusher_id (str): Crusher identifier
    """
    vibration_tag = "{}/Vibration_MM_S".format(crusher_path)

    try:
        # Configure HIGH_VIBRATION alarm (>40 mm/s)
        system.tag.configure(
            vibration_tag,
            {
                "alarms": {
                    "HIGH_VIBRATION": {
                        "enabled": True,
                        "mode": "AboveValue",
                        "setpoint": 40.0,
                        "priority": "High",
                        "displayPath": "{} - High Vibration".format(crusher_id),
                        "label": "High Vibration",
                        "notes": "Vibration exceeds normal operating threshold"
                    },
                    "CRITICAL_VIBRATION": {
                        "enabled": True,
                        "mode": "AboveValue",
                        "setpoint": 60.0,
                        "priority": "Critical",
                        "displayPath": "{} - CRITICAL Vibration".format(crusher_id),
                        "label": "Critical Vibration",
                        "notes": "Vibration at dangerous levels - immediate action required"
                    }
                }
            }
        )
        print("  - Configured alarms for {} vibration tag".format(crusher_id))

    except Exception as e:
        print("  - ERROR configuring alarms for {}: {}".format(crusher_id, str(e)))


def create_conveyor_instances(equipment_path, conveyor_ids):
    """
    Create conveyor tag instances with alignment alarms.

    Args:
        equipment_path (str): Parent path for equipment tags
        conveyor_ids (list): List of conveyor IDs (e.g., ['CV_001', 'CV_002'])

    Returns:
        int: Number of instances created
    """
    udt_type = "Conveyor"
    created_count = 0

    for conveyor_id in conveyor_ids:
        tag_path = "{}/{}".format(equipment_path, conveyor_id)

        try:
            if not system.tag.exists(tag_path):
                system.tag.addTag(
                    parentPath=equipment_path,
                    name=conveyor_id,
                    tagType="UdtInstance",
                    typeId=udt_type,
                    attributes={
                        "description": "Conveyor {} - Belt conveyor system with tracking".format(conveyor_id)
                    }
                )
                print("Created Conveyor instance: {}".format(conveyor_id))
                created_count += 1

                # Configure alarms on belt alignment tag
                configure_conveyor_alarms(tag_path, conveyor_id)
            else:
                print("Conveyor instance already exists: {}".format(conveyor_id))

        except Exception as e:
            print("ERROR creating Conveyor {}: {}".format(conveyor_id, str(e)))

    return created_count


def configure_conveyor_alarms(conveyor_path, conveyor_id):
    """
    Configure belt alignment alarms for conveyor instances.

    Args:
        conveyor_path (str): Full path to conveyor instance
        conveyor_id (str): Conveyor identifier
    """
    alignment_tag = "{}/Belt_Alignment_MM".format(conveyor_path)

    try:
        # Configure belt misalignment alarms (<-5mm or >5mm)
        system.tag.configure(
            alignment_tag,
            {
                "alarms": {
                    "MISALIGNMENT_NEG": {
                        "enabled": True,
                        "mode": "BelowValue",
                        "setpoint": -5.0,
                        "priority": "Medium",
                        "displayPath": "{} - Belt Misalignment (Left)".format(conveyor_id),
                        "label": "Belt Tracking Left",
                        "notes": "Belt tracking too far left of center"
                    },
                    "MISALIGNMENT_POS": {
                        "enabled": True,
                        "mode": "AboveValue",
                        "setpoint": 5.0,
                        "priority": "Medium",
                        "displayPath": "{} - Belt Misalignment (Right)".format(conveyor_id),
                        "label": "Belt Tracking Right",
                        "notes": "Belt tracking too far right of center"
                    }
                }
            }
        )
        print("  - Configured alarms for {} alignment tag".format(conveyor_id))

    except Exception as e:
        print("  - ERROR configuring alarms for {}: {}".format(conveyor_id, str(e)))


def validate_tag_structure():
    """
    Validate that all expected tags exist and are accessible.

    Returns:
        dict: Validation results with counts and any errors
    """
    provider = "[default]"
    equipment_path = provider + "Mining/Equipment"

    validation = {
        "folders": {"exists": False, "path": equipment_path},
        "haul_trucks": {"expected": 5, "found": 0, "instances": []},
        "crushers": {"expected": 3, "found": 0, "instances": []},
        "conveyors": {"expected": 2, "found": 0, "instances": []},
        "total_tags": 0,
        "errors": []
    }

    try:
        # Check folder structure
        if system.tag.exists(equipment_path):
            validation["folders"]["exists"] = True
        else:
            validation["errors"].append("Equipment folder does not exist: {}".format(equipment_path))
            return validation

        # Check haul trucks
        for i in range(1, 6):
            truck_id = "HT_{:03d}".format(i)
            truck_path = "{}/{}".format(equipment_path, truck_id)
            if system.tag.exists(truck_path):
                validation["haul_trucks"]["found"] += 1
                validation["haul_trucks"]["instances"].append(truck_id)
                # Count member tags (14 per truck)
                validation["total_tags"] += 14

        # Check crushers
        for i in range(1, 4):
            crusher_id = "CR_{:03d}".format(i)
            crusher_path = "{}/{}".format(equipment_path, crusher_id)
            if system.tag.exists(crusher_path):
                validation["crushers"]["found"] += 1
                validation["crushers"]["instances"].append(crusher_id)
                # Count member tags (9 per crusher)
                validation["total_tags"] += 9

        # Check conveyors
        for i in range(1, 3):
            conveyor_id = "CV_{:03d}".format(i)
            conveyor_path = "{}/{}".format(equipment_path, conveyor_id)
            if system.tag.exists(conveyor_path):
                validation["conveyors"]["found"] += 1
                validation["conveyors"]["instances"].append(conveyor_id)
                # Count member tags (5 per conveyor)
                validation["total_tags"] += 5

    except Exception as e:
        validation["errors"].append("Validation error: {}".format(str(e)))

    return validation


def main():
    """
    Main execution function to create all tag instances.
    """
    print("=" * 70)
    print("MINING OPERATIONS TAG INSTANCE CREATOR")
    print("=" * 70)
    print("")

    # Step 1: Create folder structure
    print("Step 1: Creating folder structure...")
    equipment_path = create_folder_structure()
    print("")

    # Step 2: Create haul truck instances
    print("Step 2: Creating haul truck instances...")
    truck_ids = ["HT_{:03d}".format(i) for i in range(1, 6)]
    trucks_created = create_haul_truck_instances(equipment_path, truck_ids)
    print("Created {} haul truck instances (14 tags each = {} total)".format(
        trucks_created, trucks_created * 14
    ))
    print("")

    # Step 3: Create crusher instances
    print("Step 3: Creating crusher instances...")
    crusher_ids = ["CR_{:03d}".format(i) for i in range(1, 4)]
    crushers_created = create_crusher_instances(equipment_path, crusher_ids)
    print("Created {} crusher instances (9 tags each = {} total)".format(
        crushers_created, crushers_created * 9
    ))
    print("")

    # Step 4: Create conveyor instances
    print("Step 4: Creating conveyor instances...")
    conveyor_ids = ["CV_{:03d}".format(i) for i in range(1, 3)]
    conveyors_created = create_conveyor_instances(equipment_path, conveyor_ids)
    print("Created {} conveyor instances (5 tags each = {} total)".format(
        conveyors_created, conveyors_created * 5
    ))
    print("")

    # Step 5: Validate tag structure
    print("Step 5: Validating tag structure...")
    validation = validate_tag_structure()
    print("")
    print("VALIDATION RESULTS:")
    print("-" * 70)
    print("Folder structure: {}".format("OK" if validation["folders"]["exists"] else "MISSING"))
    print("Haul Trucks: {}/{}".format(
        validation["haul_trucks"]["found"],
        validation["haul_trucks"]["expected"]
    ))
    print("Crushers: {}/{}".format(
        validation["crushers"]["found"],
        validation["crushers"]["expected"]
    ))
    print("Conveyors: {}/{}".format(
        validation["conveyors"]["found"],
        validation["conveyors"]["expected"]
    ))
    print("Total tags created: {}".format(validation["total_tags"]))
    print("")

    if validation["errors"]:
        print("ERRORS DETECTED:")
        for error in validation["errors"]:
            print("  - {}".format(error))
    else:
        print("SUCCESS! All tag instances created and validated.")

    print("=" * 70)
    print("")

    # Summary
    total_instances = trucks_created + crushers_created + conveyors_created
    total_tags = (trucks_created * 14) + (crushers_created * 9) + (conveyors_created * 5)

    print("SUMMARY:")
    print("  Equipment Instances: {}".format(total_instances))
    print("  Total Tags: {}".format(total_tags))
    print("")
    print("Ready for physics simulation (File 02)!")


# Entry point
if __name__ == "__main__":
    main()
elif __name__ == "__builtin__":
    # Running in Ignition Designer Script Console
    main()
