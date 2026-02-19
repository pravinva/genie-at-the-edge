#!/usr/bin/env python3
"""
Operations Agent for Agentic HMI
Monitors equipment, creates recommendations, executes approved actions
Workstreams 4.1, 12.1
"""

import os
import sys
import uuid
import time
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from databricks import sql
from databricks.sdk import WorkspaceClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class OperationsAgent:
    """Production Operations Agent for equipment monitoring and control"""

    def __init__(self, agent_id: str = "ops_agent_001"):
        """Initialize agent with database connections"""
        self.agent_id = agent_id
        self.w = WorkspaceClient()
        self.retry_count = 0
        self.max_retries = 3
        self.last_heartbeat = datetime.now()

        # Get connection details
        self.server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME", self.w.config.host)
        self.http_path = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/4b9b953939869799")
        self.access_token = os.getenv("DATABRICKS_TOKEN", self.w.config.token)

        # Initialize connection
        self.connect_database()

    def connect_database(self):
        """Establish database connection with retry logic"""
        try:
            self.conn = sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token
            )
            self.cursor = self.conn.cursor()
            self.cursor.execute("USE agentic_hmi")
            logger.info(f"✅ Connected to Lakebase database")
            self.retry_count = 0
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def monitor_loop(self):
        """Main monitoring loop with error handling"""
        logger.info(f"🚀 Agent {self.agent_id} starting monitoring loop...")

        while True:
            try:
                # Detect anomalies in sensor data
                anomalies = self.detect_anomalies()
                if anomalies:
                    logger.info(f"🔍 Detected {len(anomalies)} anomalies")
                    for anomaly in anomalies:
                        self.create_recommendation(anomaly)

                # Process approved recommendations
                approved = self.get_approved_recommendations()
                if approved:
                    logger.info(f"✓ Processing {len(approved)} approved recommendations")
                    for rec in approved:
                        self.create_command(rec)

                # Execute pending commands
                commands = self.get_pending_commands()
                if commands:
                    logger.info(f"⚡ Executing {len(commands)} commands")
                    for cmd in commands:
                        self.execute_command(cmd)

                # Update heartbeat
                self.update_heartbeat()

                # Reset retry count on successful iteration
                self.retry_count = 0
                time.sleep(10)

            except sql.DatabaseError as e:
                self.handle_database_error(e)
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                time.sleep(30)

    def detect_anomalies(self) -> List[Dict]:
        """Query sensor data for anomalies"""
        try:
            # Check for high temperatures (> 85°C)
            query = """
                SELECT DISTINCT
                    equipment_id,
                    sensor_type,
                    sensor_value,
                    units,
                    timestamp
                FROM sensor_data
                WHERE sensor_type = 'temperature'
                    AND sensor_value > 85
                    AND timestamp > CURRENT_TIMESTAMP - INTERVAL 30 SECONDS
                    AND equipment_id NOT IN (
                        SELECT equipment_id
                        FROM agent_recommendations
                        WHERE status IN ('pending', 'approved')
                            AND created_timestamp > CURRENT_TIMESTAMP - INTERVAL 5 MINUTES
                    )
                ORDER BY sensor_value DESC
                LIMIT 10
            """

            self.cursor.execute(query)
            results = self.cursor.fetchall()

            anomalies = []
            for row in results:
                anomalies.append({
                    'equipment_id': row[0],
                    'sensor_type': row[1],
                    'value': float(row[2]),
                    'units': row[3],
                    'timestamp': row[4]
                })

            # Also check for high vibration (> 4 mm/s)
            vibration_query = """
                SELECT DISTINCT
                    equipment_id,
                    sensor_type,
                    sensor_value,
                    units,
                    timestamp
                FROM sensor_data
                WHERE sensor_type = 'vibration'
                    AND sensor_value > 4.0
                    AND timestamp > CURRENT_TIMESTAMP - INTERVAL 30 SECONDS
                    AND equipment_id NOT IN (
                        SELECT equipment_id
                        FROM agent_recommendations
                        WHERE status IN ('pending', 'approved')
                            AND issue_type = 'vibration_anomaly'
                            AND created_timestamp > CURRENT_TIMESTAMP - INTERVAL 5 MINUTES
                    )
                LIMIT 5
            """

            self.cursor.execute(vibration_query)
            vib_results = self.cursor.fetchall()

            for row in vib_results:
                anomalies.append({
                    'equipment_id': row[0],
                    'sensor_type': row[1],
                    'value': float(row[2]),
                    'units': row[3],
                    'timestamp': row[4]
                })

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    def create_recommendation(self, anomaly: Dict):
        """Create recommendation for detected anomaly"""
        try:
            rec_id = str(uuid.uuid4())

            # Determine severity and action based on anomaly type
            if anomaly['sensor_type'] == 'temperature':
                if anomaly['value'] > 95:
                    severity = 'critical'
                    action = 'Emergency cooling required. Switch to backup cooling system immediately.'
                    confidence = 0.95
                elif anomaly['value'] > 90:
                    severity = 'high'
                    action = 'Reduce throughput by 20% and increase cooling water flow to maximum.'
                    confidence = 0.87
                else:
                    severity = 'medium'
                    action = 'Reduce throughput by 10% and monitor temperature trend.'
                    confidence = 0.75

                issue_type = 'high_temperature'
                issue_desc = f"Temperature {anomaly['value']:.1f}{anomaly['units']} exceeds threshold (85°C)"

            elif anomaly['sensor_type'] == 'vibration':
                if anomaly['value'] > 6:
                    severity = 'high'
                    action = 'Stop equipment immediately for inspection. Possible bearing failure.'
                    confidence = 0.90
                else:
                    severity = 'medium'
                    action = 'Schedule bearing inspection at next maintenance window.'
                    confidence = 0.73

                issue_type = 'vibration_anomaly'
                issue_desc = f"Vibration {anomaly['value']:.1f}{anomaly['units']} above normal range"
            else:
                return  # Skip unknown sensor types

            # Get historical context (simplified - would use Genie in production)
            root_cause = self.analyze_root_cause(anomaly)
            expected_outcome = "Parameter should return to normal range within 15-30 minutes after action"

            # Insert recommendation
            insert_query = """
                INSERT INTO agent_recommendations (
                    recommendation_id,
                    equipment_id,
                    issue_type,
                    severity,
                    issue_description,
                    recommended_action,
                    confidence_score,
                    root_cause_analysis,
                    expected_outcome,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """

            self.cursor.execute(insert_query, (
                rec_id,
                anomaly['equipment_id'],
                issue_type,
                severity,
                issue_desc,
                action,
                confidence,
                root_cause,
                expected_outcome
            ))

            self.conn.commit()
            logger.info(f"📝 Created {severity} recommendation {rec_id[:8]} for {anomaly['equipment_id']}")

        except Exception as e:
            logger.error(f"Error creating recommendation: {e}")

    def analyze_root_cause(self, anomaly: Dict) -> str:
        """Analyze root cause (simplified - would integrate Genie here)"""
        if anomaly['sensor_type'] == 'temperature':
            causes = [
                "Cooling system efficiency degraded",
                "Increased load/throughput beyond design",
                "Ambient temperature increase",
                "Fouling in heat exchanger"
            ]
        elif anomaly['sensor_type'] == 'vibration':
            causes = [
                "Bearing wear or damage",
                "Misalignment of rotating components",
                "Imbalance in rotating mass",
                "Loosened mounting bolts"
            ]
        else:
            causes = ["Unknown root cause - requires investigation"]

        # In production, would call Genie API here for sophisticated analysis
        return f"Probable cause: {causes[0]}. Alternative causes: {', '.join(causes[1:])}"

    def get_approved_recommendations(self) -> List[Dict]:
        """Get recommendations approved by operators"""
        try:
            query = """
                SELECT
                    recommendation_id,
                    equipment_id,
                    issue_type,
                    recommended_action,
                    operator_id
                FROM agent_recommendations
                WHERE status = 'approved'
                    AND recommendation_id NOT IN (
                        SELECT recommendation_id
                        FROM agent_commands
                        WHERE recommendation_id IS NOT NULL
                    )
                ORDER BY approved_timestamp ASC
                LIMIT 10
            """

            self.cursor.execute(query)
            results = self.cursor.fetchall()

            recommendations = []
            for row in results:
                recommendations.append({
                    'recommendation_id': row[0],
                    'equipment_id': row[1],
                    'issue_type': row[2],
                    'action': row[3],
                    'operator_id': row[4]
                })

            return recommendations

        except Exception as e:
            logger.error(f"Error getting approved recommendations: {e}")
            return []

    def create_command(self, recommendation: Dict):
        """Create execution command from approved recommendation"""
        try:
            cmd_id = str(uuid.uuid4())

            # Map recommendation to specific tag path and value
            tag_mapping = self.get_tag_mapping(recommendation)

            if not tag_mapping:
                logger.warning(f"No tag mapping for {recommendation['issue_type']}")
                return

            # Insert command
            insert_query = """
                INSERT INTO agent_commands (
                    command_id,
                    recommendation_id,
                    equipment_id,
                    command_type,
                    tag_path,
                    current_value,
                    new_value,
                    status,
                    created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """

            self.cursor.execute(insert_query, (
                cmd_id,
                recommendation['recommendation_id'],
                recommendation['equipment_id'],
                tag_mapping['command_type'],
                tag_mapping['tag_path'],
                tag_mapping['current_value'],
                tag_mapping['new_value'],
                f"agent_{self.agent_id}"
            ))

            self.conn.commit()
            logger.info(f"⚙️ Created command {cmd_id[:8]} for {recommendation['equipment_id']}")

        except Exception as e:
            logger.error(f"Error creating command: {e}")

    def get_tag_mapping(self, recommendation: Dict) -> Optional[Dict]:
        """Map recommendation to Ignition tag path and value"""
        equipment = recommendation['equipment_id']
        issue = recommendation['issue_type']

        # Base tag paths (would be configured in database in production)
        base_paths = {
            'REACTOR_01': '[default]Reactors/R01/',
            'REACTOR_02': '[default]Reactors/R02/',
            'PUMP_07': '[default]Pumps/P07/',
            'CONVEYOR_02': '[default]Conveyors/C02/'
        }

        if equipment not in base_paths:
            return None

        base = base_paths[equipment]

        # Map issue type to control action
        if issue == 'high_temperature':
            return {
                'command_type': 'setpoint_change',
                'tag_path': f"{base}Throughput_SP",
                'current_value': '100',
                'new_value': '80'  # Reduce by 20%
            }
        elif issue == 'vibration_anomaly':
            return {
                'command_type': 'alarm_acknowledge',
                'tag_path': f"{base}Vibration_Alarm_Ack",
                'current_value': '0',
                'new_value': '1'
            }
        else:
            return None

    def get_pending_commands(self) -> List[Dict]:
        """Get commands ready for execution"""
        try:
            query = """
                SELECT
                    command_id,
                    equipment_id,
                    tag_path,
                    new_value,
                    retry_count
                FROM agent_commands
                WHERE status = 'pending'
                    AND retry_count < 3
                ORDER BY created_timestamp ASC
                LIMIT 10
            """

            self.cursor.execute(query)
            results = self.cursor.fetchall()

            commands = []
            for row in results:
                commands.append({
                    'command_id': row[0],
                    'equipment_id': row[1],
                    'tag_path': row[2],
                    'new_value': row[3],
                    'retry_count': row[4]
                })

            return commands

        except Exception as e:
            logger.error(f"Error getting pending commands: {e}")
            return []

    def execute_command(self, command: Dict):
        """Execute command via Ignition REST API (or simulation)"""
        try:
            # Update status to executing
            self.cursor.execute(
                "UPDATE agent_commands SET status = 'executing' WHERE command_id = ?",
                (command['command_id'],)
            )
            self.conn.commit()

            # In production, would call Ignition REST API here
            # For now, simulate execution
            success = self.simulate_tag_write(command['tag_path'], command['new_value'])

            if success:
                # Mark as executed
                self.cursor.execute("""
                    UPDATE agent_commands
                    SET status = 'executed',
                        execution_result = 'Success',
                        execution_timestamp = CURRENT_TIMESTAMP
                    WHERE command_id = ?
                """, (command['command_id'],))

                # Update recommendation status
                self.cursor.execute("""
                    UPDATE agent_recommendations
                    SET status = 'executed',
                        executed_timestamp = CURRENT_TIMESTAMP
                    WHERE recommendation_id = (
                        SELECT recommendation_id
                        FROM agent_commands
                        WHERE command_id = ?
                    )
                """, (command['command_id'],))

                self.conn.commit()
                logger.info(f"✅ Executed command {command['command_id'][:8]}: {command['tag_path']} = {command['new_value']}")

            else:
                # Mark as failed and increment retry
                self.cursor.execute("""
                    UPDATE agent_commands
                    SET status = 'failed',
                        execution_result = 'Simulation failed',
                        retry_count = retry_count + 1
                    WHERE command_id = ?
                """, (command['command_id'],))
                self.conn.commit()
                logger.warning(f"⚠️ Failed to execute command {command['command_id'][:8]}")

        except Exception as e:
            logger.error(f"Error executing command: {e}")

    def simulate_tag_write(self, tag_path: str, value: str) -> bool:
        """Simulate writing to Ignition tag"""
        # In production, this would call Ignition REST API
        # For simulation, randomly succeed 90% of the time
        import random
        success = random.random() < 0.9

        if success:
            logger.debug(f"Simulated write: {tag_path} = {value}")

        return success

    def update_heartbeat(self):
        """Update agent heartbeat for monitoring"""
        try:
            # Calculate uptime
            uptime_seconds = (datetime.now() - self.last_heartbeat).total_seconds()

            # Insert heartbeat metric
            self.cursor.execute("""
                INSERT INTO agent_metrics (
                    metric_id,
                    agent_id,
                    metric_name,
                    metric_value,
                    metric_unit
                ) VALUES (?, ?, 'heartbeat', ?, 'seconds')
            """, (str(uuid.uuid4()), self.agent_id, uptime_seconds))

            # Get and log statistics
            stats = self.get_agent_statistics()
            if stats:
                logger.debug(f"📊 Stats - Recommendations: {stats['recommendations']}, Commands: {stats['commands']}, Success Rate: {stats['success_rate']:.1%}")

            self.conn.commit()
            self.last_heartbeat = datetime.now()

        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")

    def get_agent_statistics(self) -> Dict:
        """Get agent performance statistics"""
        try:
            stats = {}

            # Count recommendations created today
            self.cursor.execute("""
                SELECT COUNT(*) FROM agent_recommendations
                WHERE DATE(created_timestamp) = CURRENT_DATE
            """)
            stats['recommendations'] = self.cursor.fetchone()[0]

            # Count commands executed today
            self.cursor.execute("""
                SELECT COUNT(*) FROM agent_commands
                WHERE DATE(created_timestamp) = CURRENT_DATE
                    AND status = 'executed'
            """)
            stats['commands'] = self.cursor.fetchone()[0]

            # Calculate success rate
            self.cursor.execute("""
                SELECT
                    SUM(CASE WHEN status = 'executed' THEN 1 ELSE 0 END) as success,
                    COUNT(*) as total
                FROM agent_commands
                WHERE DATE(created_timestamp) = CURRENT_DATE
            """)
            result = self.cursor.fetchone()
            stats['success_rate'] = result[0] / result[1] if result[1] > 0 else 0

            return stats

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def handle_database_error(self, error):
        """Handle database connection errors with retry logic"""
        self.retry_count += 1

        if self.retry_count <= self.max_retries:
            sleep_time = 2 ** self.retry_count  # Exponential backoff
            logger.warning(f"🔄 Retry {self.retry_count}/{self.max_retries} - Database error: {error}")
            logger.info(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)

            # Try to reconnect
            if self.connect_database():
                logger.info("✅ Reconnected to database")
                self.retry_count = 0
        else:
            logger.error(f"❌ Max retries exceeded. Database connection failed.")
            logger.info("Waiting 60 seconds before retry...")
            self.retry_count = 0
            time.sleep(60)
            self.connect_database()

def main():
    """Main entry point"""
    agent = OperationsAgent()

    try:
        agent.monitor_loop()
    except KeyboardInterrupt:
        logger.info("\n👋 Agent shutdown requested")
        if hasattr(agent, 'conn'):
            agent.conn.close()
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()