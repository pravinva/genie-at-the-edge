#!/usr/bin/env python3
"""
Setup script to create Lakebase tables for Operations Agent.
Run this once to initialize the database schema.
"""

import os
from databricks import sql

def create_tables():
    """Create all required tables in Lakebase."""

    # Connect to Lakebase
    conn = sql.connect(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN")
    )

    cursor = conn.cursor()

    print("Creating agent_recommendations table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_recommendations (
            recommendation_id VARCHAR(36) PRIMARY KEY,
            equipment_id VARCHAR(100) NOT NULL,
            issue_type VARCHAR(100) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            temperature_reading FLOAT,
            pressure_reading FLOAT,
            flow_rate_reading FLOAT,
            root_cause_analysis TEXT,
            recommended_action TEXT NOT NULL,
            confidence_score FLOAT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_timestamp TIMESTAMP NOT NULL,
            created_by_agent VARCHAR(100),
            approved_timestamp TIMESTAMP,
            approved_by_operator VARCHAR(100),
            operator_notes TEXT,
            rejected_timestamp TIMESTAMP,
            executed_timestamp TIMESTAMP,
            execution_result TEXT
        )
    """)
    print("✓ agent_recommendations table created")

    print("Creating agent_commands table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_commands (
            command_id VARCHAR(36) PRIMARY KEY,
            recommendation_id VARCHAR(36),
            equipment_id VARCHAR(100) NOT NULL,
            tag_path VARCHAR(200) NOT NULL,
            new_value VARCHAR(100),
            action_description TEXT,
            severity VARCHAR(20),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_timestamp TIMESTAMP NOT NULL,
            created_by_agent VARCHAR(100),
            executed_timestamp TIMESTAMP,
            execution_result TEXT,
            FOREIGN KEY (recommendation_id) REFERENCES agent_recommendations(recommendation_id)
        )
    """)
    print("✓ agent_commands table created")

    print("Creating agent_health table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_health (
            agent_id VARCHAR(100) PRIMARY KEY,
            last_heartbeat TIMESTAMP NOT NULL,
            status VARCHAR(20) NOT NULL,
            polls_completed INTEGER DEFAULT 0,
            created_timestamp TIMESTAMP NOT NULL
        )
    """)
    print("✓ agent_health table created")

    print("Creating sensor_data table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            sensor_id VARCHAR(100) PRIMARY KEY,
            equipment_id VARCHAR(100) NOT NULL,
            temperature FLOAT,
            pressure FLOAT,
            flow_rate FLOAT,
            sensor_status VARCHAR(20),
            timestamp TIMESTAMP NOT NULL,
            recorded_by VARCHAR(100)
        )
    """)
    print("✓ sensor_data table created")

    print("Creating work_orders table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            work_order_id VARCHAR(36) PRIMARY KEY,
            recommendation_id VARCHAR(36),
            equipment_id VARCHAR(100),
            description TEXT,
            status VARCHAR(20),
            assigned_to VARCHAR(100),
            created_timestamp TIMESTAMP,
            completed_timestamp TIMESTAMP,
            FOREIGN KEY (recommendation_id) REFERENCES agent_recommendations(recommendation_id)
        )
    """)
    print("✓ work_orders table created")

    print("Creating operator_sessions table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operator_sessions (
            session_id VARCHAR(36) PRIMARY KEY,
            operator_id VARCHAR(100) NOT NULL,
            login_timestamp TIMESTAMP NOT NULL,
            logout_timestamp TIMESTAMP,
            status VARCHAR(20),
            approved_recommendations INTEGER DEFAULT 0,
            rejected_recommendations INTEGER DEFAULT 0
        )
    """)
    print("✓ operator_sessions table created")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ All tables created successfully!")


def insert_sample_data():
    """Insert sample sensor data for testing."""

    conn = sql.connect(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN")
    )

    cursor = conn.cursor()

    print("\nInserting sample sensor data...")

    # Insert sample sensor readings with some anomalies
    sample_data = [
        ("SENSOR_REACTOR_01", "REACTOR_01", 75.5, 85.0, 50.0, "good"),
        ("SENSOR_REACTOR_02", "REACTOR_02", 92.0, 95.0, 48.0, "warning"),
        ("SENSOR_PUMP_01", "PUMP_01", 68.0, 70.0, 55.0, "good"),
        ("SENSOR_PUMP_02", "PUMP_02", 88.5, 92.0, 45.0, "warning"),
        ("SENSOR_VALVE_01", "VALVE_01", 70.0, 65.0, 60.0, "good"),
    ]

    for sensor_id, equipment_id, temp, pressure, flow, status in sample_data:
        cursor.execute("""
            INSERT INTO sensor_data
            (sensor_id, equipment_id, temperature, pressure, flow_rate, sensor_status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, [sensor_id, equipment_id, temp, pressure, flow, status])

    conn.commit()
    cursor.close()
    conn.close()

    print(f"✓ Inserted {len(sample_data)} sample sensor readings")
    print("✅ Sample data inserted successfully!")


def verify_tables():
    """Verify all tables were created correctly."""

    conn = sql.connect(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN")
    )

    cursor = conn.cursor()

    tables = [
        'agent_recommendations',
        'agent_commands',
        'agent_health',
        'sensor_data',
        'work_orders',
        'operator_sessions'
    ]

    print("\nVerifying tables...")

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"✓ {table}: {count} rows")

    cursor.close()
    conn.close()

    print("\n✅ All tables verified!")


if __name__ == "__main__":
    print("="*70)
    print("OPERATIONS AGENT - TABLE SETUP")
    print("="*70)

    create_tables()
    insert_sample_data()
    verify_tables()

    print("\n" + "="*70)
    print("Setup complete! Ready to run operations_agent.py")
    print("="*70)
