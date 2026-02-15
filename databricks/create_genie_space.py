#!/usr/bin/env python3
"""
Create Databricks Genie Space for Mining Operations
"""

from databricks.sdk import WorkspaceClient
import json

w = WorkspaceClient()

print("="*80)
print("Creating Genie Space for Mining Operations")
print("="*80)

# Sample questions for mining operations
sample_questions = [
    "What is the current status of all haul trucks?",
    "Show me the average vibration levels for all crushers in the last hour",
    "Which equipment has anomalies detected in the past 24 hours?",
    "What is HT_001's current speed and load?",
    "Show crusher CR_002 performance over the last 2 hours",
    "List all equipment with high criticality sensors",
    "What is the average fuel level across all haul trucks?",
    "Show me equipment that is currently in maintenance",
    "What are the latest sensor readings for conveyor CV_001?",
    "Which haul trucks are currently hauling loaded?"
]

# Instructions for Genie
genie_instructions = """
You are an AI assistant for mining operations monitoring and analysis.

## Available Data Tables

### Bronze Layer
- **ignition_genie.mining_demo.tag_events_bronze**: Raw tag events from Ignition Gateway
  - Fields: event_id, event_time, tag_path, tag_provider, numeric_value, string_value, boolean_value, quality, source_system

### Silver Layer
- **ignition_genie.mining_demo.equipment_sensors_normalized**: Normalized sensor readings
  - Fields: event_id, event_timestamp, equipment_id, equipment_type, sensor_name, sensor_value, quality, location, criticality

### Gold Layer
- **ignition_genie.mining_demo.equipment_performance_1min**: 1-minute aggregated metrics
  - Fields: window_start, window_end, equipment_id, equipment_type, sensor_name, avg_value, min_value, max_value, stddev_value, reading_count

- **ignition_genie.mining_demo.equipment_current_status**: Latest sensor values per equipment
  - Fields: equipment_id, equipment_type, sensor_name, sensor_value, last_updated, location, criticality

- **ignition_genie.mining_demo.haul_truck_cycles**: Haul truck state tracking
  - Fields: equipment_id, current_state, state_since, location

- **ignition_genie.mining_demo.sensor_anomalies**: Detected anomalies
  - Fields: window_start, equipment_id, equipment_type, sensor_name, anomaly_type, severity, avg_value, baseline_avg, deviation_score, recommendation

## Equipment Types
- **Haul Trucks** (HT_001 to HT_005): Load-haul-dump cycles
  - States: loading, hauling_loaded, dumping, returning_empty
  - Key sensors: Speed_KPH, Load_Tonnes, Fuel_Level_Pct, Engine_Temp_C, Vibration_MM_S

- **Crushers** (CR_001 to CR_003): Ore processing
  - Key sensors: Throughput_TPH, Vibration_MM_S, Motor_Current_A, Motor_Temp_C, Bearing_Temp_C

- **Conveyors** (CV_001, CV_002): Material transport
  - Key sensors: Speed_M_S, Load_Pct, Belt_Alignment_MM, Motor_Temp_C

## Query Guidance
- For "current" status, use **equipment_current_status** table
- For trends/history, use **equipment_performance_1min** table
- For anomalies/alerts, use **sensor_anomalies** table
- For haul truck states, use **haul_truck_cycles** table
- Always filter by time ranges for performance queries
- Include equipment_type and location in groupings for better insights

## Response Format
- Provide clear, actionable insights
- Include relevant metrics and units
- Highlight critical issues (anomalies, high deviations)
- Suggest follow-up actions when appropriate
"""

try:
    # Check if Genie spaces can be listed (API may vary by workspace)
    print("\n[1/2] Creating Genie Space...")

    # Note: Genie Space creation API may not be available in all workspaces yet
    # This is a placeholder for when the API becomes available

    print("✓ Genie Space configuration prepared")
    print("\nSpace Details:")
    print(f"  Name: Mining Operations AI Assistant")
    print(f"  Catalog: ignition_genie")
    print(f"  Schema: mining_demo")
    print(f"  Sample Questions: {len(sample_questions)}")

    print("\n[2/2] Genie Space Instructions:")
    print(genie_instructions[:500] + "...")

    # Save configuration for manual setup if needed
    config = {
        "name": "Mining Operations AI Assistant",
        "description": "AI-powered assistant for mining equipment monitoring and analysis",
        "catalog": "ignition_genie",
        "schema": "mining_demo",
        "sample_questions": sample_questions,
        "instructions": genie_instructions
    }

    with open("databricks/genie_space_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("\n✓ Configuration saved to: databricks/genie_space_config.json")

except Exception as e:
    print(f"✗ Error: {str(e)}")
    print("\nNote: Genie Space API may require manual creation via UI")

print("\n" + "="*80)
print("Manual Setup Instructions (if API unavailable):")
print("="*80)
print("1. Navigate to Databricks Workspace → Genie")
print("2. Click 'Create Genie Space'")
print("3. Configure:")
print("   - Name: Mining Operations AI Assistant")
print("   - Catalog: ignition_genie")
print("   - Schema: mining_demo")
print("4. Add sample questions from genie_space_config.json")
print("5. Add instructions from genie_space_config.json")
print("6. Test with: 'What is the current status of all haul trucks?'")
print("="*80)
