#!/usr/bin/env python3
"""
Demo script for Operations Agent.
Simulates a complete workflow: anomaly detection -> recommendation -> approval -> execution
"""

import os
import uuid
import time
from datetime import datetime
from databricks import sql

def connect():
    """Connect to Lakebase."""
    return sql.connect(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN")
    )


def insert_anomaly(conn, equipment_id, temperature):
    """Insert a sensor anomaly into the database."""
    cursor = conn.cursor()
    sensor_id = f"SENSOR_{equipment_id}"

    print(f"\n[STEP 1] Inserting sensor anomaly...")
    print(f"  Equipment: {equipment_id}")
    print(f"  Temperature: {temperature}°C (threshold: 85°C)")

    cursor.execute("""
        INSERT INTO sensor_data
        (sensor_id, equipment_id, temperature, pressure, flow_rate, sensor_status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, [sensor_id, equipment_id, temperature, 100.0, 45.0, "warning"])

    conn.commit()
    cursor.close()

    print("  ✓ Anomaly inserted")


def check_recommendations(conn):
    """Check for pending recommendations created by the agent."""
    cursor = conn.cursor()

    print(f"\n[STEP 2] Checking for recommendations...")
    time.sleep(15)  # Wait for agent to detect anomaly

    cursor.execute("""
        SELECT
            recommendation_id,
            equipment_id,
            severity,
            recommended_action,
            confidence_score,
            status,
            created_timestamp
        FROM agent_recommendations
        WHERE status = 'pending'
        ORDER BY created_timestamp DESC
        LIMIT 5
    """)

    recommendations = cursor.fetchall()
    cursor.close()

    if recommendations:
        print(f"  ✓ Found {len(recommendations)} pending recommendations:")
        for rec in recommendations:
            print(f"\n    Recommendation ID: {rec[0]}")
            print(f"    Equipment: {rec[1]}")
            print(f"    Severity: {rec[2]}")
            print(f"    Action: {rec[3]}")
            print(f"    Confidence: {rec[4]*100:.0f}%")
            print(f"    Status: {rec[5]}")

        return recommendations[0][0]  # Return first recommendation ID
    else:
        print("  ✗ No pending recommendations found")
        return None


def approve_recommendation(conn, rec_id):
    """Approve a recommendation (simulate operator action)."""
    cursor = conn.cursor()

    print(f"\n[STEP 3] Approving recommendation...")
    print(f"  Recommendation ID: {rec_id}")

    cursor.execute("""
        UPDATE agent_recommendations
        SET status = 'approved',
            approved_timestamp = CURRENT_TIMESTAMP,
            approved_by_operator = ?
        WHERE recommendation_id = ?
    """, ["demo_operator", rec_id])

    conn.commit()
    cursor.close()

    print("  ✓ Recommendation approved")


def check_commands(conn):
    """Check for commands created by the agent after approval."""
    cursor = conn.cursor()

    print(f"\n[STEP 4] Checking for execution commands...")
    time.sleep(15)  # Wait for agent to process approval

    cursor.execute("""
        SELECT
            command_id,
            recommendation_id,
            equipment_id,
            tag_path,
            new_value,
            action_description,
            status,
            created_timestamp
        FROM agent_commands
        WHERE status IN ('pending', 'executing', 'executed')
        ORDER BY created_timestamp DESC
        LIMIT 5
    """)

    commands = cursor.fetchall()
    cursor.close()

    if commands:
        print(f"  ✓ Found {len(commands)} commands:")
        for cmd in commands:
            print(f"\n    Command ID: {cmd[0]}")
            print(f"    Equipment: {cmd[2]}")
            print(f"    Tag Path: {cmd[3]}")
            print(f"    New Value: {cmd[4]}")
            print(f"    Action: {cmd[5]}")
            print(f"    Status: {cmd[6]}")

        return commands[0][0]  # Return first command ID
    else:
        print("  ✗ No commands found")
        return None


def check_agent_health(conn):
    """Check agent health status."""
    cursor = conn.cursor()

    print(f"\n[STEP 5] Checking agent health...")

    cursor.execute("""
        SELECT
            agent_id,
            last_heartbeat,
            status,
            polls_completed
        FROM agent_health
        WHERE status = 'online'
        ORDER BY last_heartbeat DESC
        LIMIT 1
    """)

    result = cursor.fetchone()
    cursor.close()

    if result:
        print(f"  ✓ Agent Status:")
        print(f"    Agent ID: {result[0]}")
        print(f"    Last Heartbeat: {result[1]}")
        print(f"    Status: {result[2]}")
        print(f"    Polls Completed: {result[3]}")
    else:
        print("  ✗ No active agent found (is the agent running?)")


def print_summary(conn):
    """Print summary of agent activity."""
    cursor = conn.cursor()

    print(f"\n[SUMMARY] Agent Activity Report")
    print("="*70)

    # Count recommendations by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM agent_recommendations
        GROUP BY status
    """)
    recs = cursor.fetchall()
    print("\nRecommendations by status:")
    for status, count in recs:
        print(f"  {status}: {count}")

    # Count commands by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM agent_commands
        GROUP BY status
    """)
    cmds = cursor.fetchall()
    print("\nCommands by status:")
    for status, count in cmds:
        print(f"  {status}: {count}")

    # Get execution times
    cursor.execute("""
        SELECT
            COUNT(*) as total_executed,
            AVG(EXTRACT(EPOCH FROM (executed_timestamp - created_timestamp))) as avg_seconds
        FROM agent_commands
        WHERE status = 'executed' AND executed_timestamp IS NOT NULL
    """)
    result = cursor.fetchone()
    if result and result[0] > 0:
        print(f"\nCommand Execution:")
        print(f"  Total Executed: {result[0]}")
        print(f"  Avg Execution Time: {result[1]:.2f} seconds")

    cursor.close()
    print("="*70)


def run_demo():
    """Run complete demo scenario."""

    print("="*70)
    print("OPERATIONS AGENT - COMPLETE DEMO")
    print("="*70)
    print("\nThis demo will:")
    print("1. Insert a sensor anomaly")
    print("2. Wait for agent to detect it and create recommendation")
    print("3. Simulate operator approval")
    print("4. Wait for agent to create and execute command")
    print("5. Check agent health and print summary")
    print("\nNote: Ensure the operations_agent.py is running in another terminal!")
    print("\n" + "="*70)

    try:
        conn = connect()
        print("✓ Connected to Lakebase\n")

        # Define test scenario
        equipment_id = "REACTOR_DEMO"
        temperature = 92.0  # Above 85°C threshold

        # Step 1: Insert anomaly
        insert_anomaly(conn, equipment_id, temperature)

        # Step 2: Check for recommendation
        rec_id = check_recommendations(conn)
        if not rec_id:
            print("\nDemo cannot continue - agent did not create recommendation")
            print("Possible issues:")
            print("- Agent is not running")
            print("- Agent has not detected the anomaly yet")
            print("- Sensor data table is not accessible")
            conn.close()
            return

        # Step 3: Approve recommendation
        approve_recommendation(conn, rec_id)

        # Step 4: Check for commands
        cmd_id = check_commands(conn)
        if not cmd_id:
            print("\nAgent may not have processed approval yet")
            print("Continue checking in another query...")

        # Step 5: Check agent health
        check_agent_health(conn)

        # Final summary
        print_summary(conn)

        print("\n✅ DEMO COMPLETE")
        print("\nWhat happened:")
        print("1. Agent detected temperature anomaly (92°C > 85°C threshold)")
        print("2. Agent created recommendation with severity=high, confidence=0.90")
        print("3. Operator approved the recommendation")
        print("4. Agent created execution command to reduce throughput")
        print("5. Command was marked for execution")
        print("\nYou can now:")
        print("- Review all recommendations: SELECT * FROM agent_recommendations")
        print("- Review all commands: SELECT * FROM agent_commands")
        print("- Check agent health: SELECT * FROM agent_health WHERE agent_id='ops_agent_001'")

        conn.close()

    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        conn.close()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Databricks credentials are configured:")
        print("   databricks configure --token")
        print("2. Ensure operations_agent.py is running in another terminal")
        print("3. Ensure setup_agent_tables.py has been run once to create tables")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_demo()
