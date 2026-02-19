#!/usr/bin/env python3
"""
Setup Lakebase database and tables for Agentic HMI
Workstream 1.1: Lakebase Database Setup
"""

import os
from databricks.sdk import WorkspaceClient
from databricks import sql
import uuid
from datetime import datetime, timedelta

def setup_lakebase():
    """Create Lakebase database and tables for Agentic HMI"""

    # Initialize Databricks workspace client
    w = WorkspaceClient()

    # Get connection details
    server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME", w.config.host)
    http_path = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/agentic_hmi")
    access_token = os.getenv("DATABRICKS_TOKEN", w.config.token)

    # Connect to Databricks SQL
    with sql.connect(
        server_hostname=server_hostname,
        http_path=http_path,
        access_token=access_token
    ) as connection:
        cursor = connection.cursor()

        print("Creating Lakebase database: agentic_hmi")

        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS agentic_hmi")
        cursor.execute("USE agentic_hmi")

        # Table 1: agent_recommendations
        print("Creating table: agent_recommendations")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_recommendations (
                recommendation_id VARCHAR(36) PRIMARY KEY,
                equipment_id VARCHAR(50) NOT NULL,
                issue_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
                issue_description TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
                root_cause_analysis TEXT,
                expected_outcome TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected', 'deferred', 'executed')),
                operator_id VARCHAR(50),
                operator_notes TEXT,
                approved_timestamp TIMESTAMP,
                executed_timestamp TIMESTAMP,
                defer_until TIMESTAMP,
                rejection_reason TEXT,
                created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 2: work_orders
        print("Creating table: work_orders")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_orders (
                work_order_id VARCHAR(36) PRIMARY KEY,
                recommendation_id VARCHAR(36),
                equipment_id VARCHAR(50) NOT NULL,
                work_type VARCHAR(100) NOT NULL,
                priority INTEGER CHECK (priority BETWEEN 1 AND 5),
                description TEXT NOT NULL,
                assigned_to VARCHAR(50),
                status VARCHAR(20) NOT NULL DEFAULT 'created'
                    CHECK (status IN ('created', 'assigned', 'in_progress', 'completed', 'cancelled')),
                estimated_duration_minutes INTEGER,
                actual_duration_minutes INTEGER,
                materials_needed TEXT,
                completion_notes TEXT,
                created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_timestamp TIMESTAMP,
                started_timestamp TIMESTAMP,
                completed_timestamp TIMESTAMP,
                FOREIGN KEY (recommendation_id) REFERENCES agent_recommendations(recommendation_id)
            )
        """)

        # Table 3: equipment_setpoints
        print("Creating table: equipment_setpoints")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipment_setpoints (
                setpoint_id VARCHAR(36) PRIMARY KEY,
                equipment_id VARCHAR(50) NOT NULL,
                parameter_name VARCHAR(100) NOT NULL,
                min_value DECIMAL(10,2),
                max_value DECIMAL(10,2),
                target_value DECIMAL(10,2),
                current_value DECIMAL(10,2),
                units VARCHAR(20),
                alarm_enabled BOOLEAN DEFAULT TRUE,
                alarm_delay_seconds INTEGER DEFAULT 30,
                last_modified_by VARCHAR(50),
                last_modified_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_equipment_parameter (equipment_id, parameter_name)
            )
        """)

        # Table 4: agent_commands
        print("Creating table: agent_commands")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_commands (
                command_id VARCHAR(36) PRIMARY KEY,
                recommendation_id VARCHAR(36),
                equipment_id VARCHAR(50) NOT NULL,
                command_type VARCHAR(50) NOT NULL,
                tag_path VARCHAR(255) NOT NULL,
                current_value VARCHAR(100),
                new_value VARCHAR(100) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'executing', 'executed', 'failed', 'cancelled')),
                execution_result TEXT,
                execution_timestamp TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                created_by VARCHAR(50) DEFAULT 'agent',
                created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id) REFERENCES agent_recommendations(recommendation_id)
            )
        """)

        # Table 5: operator_sessions
        print("Creating table: operator_sessions")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operator_sessions (
                session_id VARCHAR(36) PRIMARY KEY,
                operator_id VARCHAR(50) NOT NULL,
                operator_name VARCHAR(100),
                operator_role VARCHAR(50),
                client_ip VARCHAR(45),
                client_user_agent TEXT,
                login_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_timestamp TIMESTAMP,
                last_activity_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recommendations_viewed INTEGER DEFAULT 0,
                recommendations_approved INTEGER DEFAULT 0,
                recommendations_rejected INTEGER DEFAULT 0,
                recommendations_deferred INTEGER DEFAULT 0,
                session_duration_seconds INTEGER
            )
        """)

        # Additional tables for monitoring and learning
        print("Creating table: agent_metrics")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_metrics (
                metric_id VARCHAR(36) PRIMARY KEY,
                agent_id VARCHAR(50) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                metric_value DECIMAL(10,2),
                metric_unit VARCHAR(20),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        print("Creating table: sensor_data")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                reading_id VARCHAR(36) PRIMARY KEY,
                equipment_id VARCHAR(50) NOT NULL,
                sensor_type VARCHAR(50) NOT NULL,
                sensor_value DECIMAL(10,2) NOT NULL,
                units VARCHAR(20),
                quality VARCHAR(20) DEFAULT 'good',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert sample data
        print("\nInserting sample data into agent_recommendations...")

        sample_recommendations = [
            {
                'id': str(uuid.uuid4()),
                'equipment': 'REACTOR_01',
                'issue': 'high_temperature',
                'severity': 'high',
                'description': 'Temperature exceeding normal operating range (92°C, normal: 70-80°C)',
                'action': 'Reduce feed rate by 15% and increase cooling water flow to maximum',
                'confidence': 0.87
            },
            {
                'id': str(uuid.uuid4()),
                'equipment': 'PUMP_07',
                'issue': 'vibration_anomaly',
                'severity': 'medium',
                'description': 'Vibration levels increasing trend detected (4.2 mm/s)',
                'action': 'Schedule bearing inspection within next maintenance window',
                'confidence': 0.73
            },
            {
                'id': str(uuid.uuid4()),
                'equipment': 'CONVEYOR_02',
                'issue': 'belt_tension',
                'severity': 'low',
                'description': 'Belt tension below optimal range',
                'action': 'Adjust tension to 120N using tensioning mechanism',
                'confidence': 0.91
            }
        ]

        for rec in sample_recommendations:
            cursor.execute("""
                INSERT INTO agent_recommendations (
                    recommendation_id, equipment_id, issue_type, severity,
                    issue_description, recommended_action, confidence_score,
                    root_cause_analysis, expected_outcome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rec['id'],
                rec['equipment'],
                rec['issue'],
                rec['severity'],
                rec['description'],
                rec['action'],
                rec['confidence'],
                f"Analysis: Likely caused by {rec['issue']} based on sensor patterns",
                f"Temperature/vibration should return to normal within 15 minutes"
            ))

        print(f"Inserted {len(sample_recommendations)} sample recommendations")

        # Insert sample sensor data with anomalies
        print("\nInserting sample sensor data...")

        sample_sensors = [
            ('REACTOR_01', 'temperature', 92.5, '°C'),
            ('REACTOR_01', 'pressure', 3.2, 'bar'),
            ('PUMP_07', 'vibration', 4.2, 'mm/s'),
            ('PUMP_07', 'flow_rate', 145.3, 'L/min'),
            ('CONVEYOR_02', 'belt_speed', 2.1, 'm/s'),
            ('CONVEYOR_02', 'belt_tension', 95, 'N')
        ]

        for equipment, sensor, value, unit in sample_sensors:
            cursor.execute("""
                INSERT INTO sensor_data (
                    reading_id, equipment_id, sensor_type, sensor_value, units
                ) VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), equipment, sensor, value, unit))

        print(f"Inserted {len(sample_sensors)} sensor readings")

        # Verify tables
        print("\nVerifying tables created:")
        cursor.execute("SHOW TABLES IN agentic_hmi")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  ✓ {table[0]}")

        # Count records
        print("\nRecord counts:")
        for table_name in ['agent_recommendations', 'sensor_data']:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} records")

        print("\n✅ Lakebase setup complete!")
        return True

if __name__ == "__main__":
    setup_lakebase()