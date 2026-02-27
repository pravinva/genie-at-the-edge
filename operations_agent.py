#!/usr/bin/env python3
"""
Operations Agent for Agentic HMI
Monitors equipment, detects anomalies, creates recommendations, and executes approved actions.
Connects to Lakebase using databricks.sql with default CLI credentials.
Workstream 4.1 & 12.1 Implementation
"""

import os
import uuid
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

from databricks import sql
from databricks.sdk import WorkspaceClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class OperationsAgent:
    """
    Operations Agent that monitors equipment, detects anomalies,
    creates recommendations, and executes approved actions.
    """

    def __init__(self):
        """Initialize the agent with database connection and configuration."""
        self.agent_id = "ops_agent_001"
        self.poll_interval = 10  # seconds
        self.max_retries = 3
        self.retry_backoff = 2  # exponential backoff multiplier

        # Initialize Databricks client
        try:
            self.w = WorkspaceClient()
            logger.info("Initialized Databricks WorkspaceClient")
        except Exception as e:
            logger.error(f"Failed to initialize WorkspaceClient: {e}")
            raise

        # Initialize Lakebase connection
        self.conn = self._connect_to_lakebase()
        logger.info(f"Agent {self.agent_id} initialized successfully")

    def _connect_to_lakebase(self) -> sql.Connection:
        """
        Connect to Lakebase using databricks.sql with default CLI credentials.

        Returns:
            sql.Connection: Databricks SQL connection to Lakebase
        """
        try:
            # Use default CLI credentials (from ~/.databrickscfg)
            conn = sql.connect(
                server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
                http_path=os.getenv("DATABRICKS_HTTP_PATH"),
                access_token=os.getenv("DATABRICKS_TOKEN")
            )
            logger.info("Connected to Lakebase successfully")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to Lakebase: {e}")
            raise

    def _execute_query(self, query: str, params: List[Any] = None) -> List[Dict]:
        """
        Execute a query safely with error handling.

        Args:
            query: SQL query to execute
            params: Optional query parameters

        Returns:
            List of result rows as dictionaries
        """
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}")
            raise

    def _execute_update(self, query: str, params: List[Any] = None) -> int:
        """
        Execute an update/insert query safely with error handling.

        Args:
            query: SQL update/insert query
            params: Optional query parameters

        Returns:
            Number of rows affected
        """
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            affected = cursor.rowcount
            self.conn.commit()
            cursor.close()
            logger.debug(f"Update executed: {affected} rows affected")
            return affected
        except Exception as e:
            logger.error(f"Update execution failed: {e}\nQuery: {query}")
            self.conn.rollback()
            raise

    def detect_anomalies(self) -> None:
        """
        Query sensor_data table for equipment anomalies.
        Detects temperature readings above 85°C threshold.
        Creates recommendations when anomalies are found.
        """
        try:
            logger.info("Detecting anomalies...")

            # Query sensor data from last 10 seconds
            cutoff_time = datetime.now() - timedelta(seconds=10)
            cutoff_timestamp = cutoff_time.isoformat()

            query = """
                SELECT
                    equipment_id,
                    temperature,
                    pressure,
                    flow_rate,
                    timestamp,
                    sensor_status
                FROM sensor_data
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 100
            """

            sensor_readings = self._execute_query(query, [cutoff_timestamp])

            if not sensor_readings:
                logger.debug("No recent sensor data found")
                return

            logger.info(f"Found {len(sensor_readings)} recent sensor readings")

            # Check for anomalies
            for reading in sensor_readings:
                equipment_id = reading[0]
                temperature = reading[1]

                # Anomaly threshold: temperature > 85°C
                if temperature and temperature > 85:
                    logger.warning(
                        f"ANOMALY DETECTED: {equipment_id} temperature={temperature}°C"
                    )
                    self._create_recommendation(
                        equipment_id=equipment_id,
                        temperature=temperature,
                        pressure=reading[2],
                        flow_rate=reading[3],
                        sensor_data=reading
                    )

        except Exception as e:
            logger.error(f"Error in detect_anomalies: {e}")
            raise

    def _create_recommendation(
        self,
        equipment_id: str,
        temperature: float,
        pressure: Optional[float],
        flow_rate: Optional[float],
        sensor_data: tuple
    ) -> None:
        """
        Create a recommendation in agent_recommendations table.

        Args:
            equipment_id: Equipment identifier
            temperature: Current temperature reading
            pressure: Current pressure reading
            flow_rate: Current flow rate reading
            sensor_data: Full sensor reading tuple
        """
        try:
            recommendation_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            # Determine severity and action based on temperature
            if temperature > 95:
                severity = "critical"
                issue_type = "critical_temperature"
                recommended_action = "EMERGENCY: Reduce throughput by 50% immediately"
                confidence = 0.95
            elif temperature > 90:
                severity = "high"
                issue_type = "high_temperature"
                recommended_action = "Reduce throughput by 25% and activate cooling system"
                confidence = 0.90
            else:
                severity = "medium"
                issue_type = "elevated_temperature"
                recommended_action = "Reduce throughput by 10% and monitor temperature"
                confidence = 0.85

            # Additional context for recommendations
            root_cause = self._analyze_root_cause(
                temperature=temperature,
                pressure=pressure,
                flow_rate=flow_rate
            )

            # Insert into agent_recommendations table
            insert_query = """
                INSERT INTO agent_recommendations (
                    recommendation_id,
                    equipment_id,
                    issue_type,
                    severity,
                    temperature_reading,
                    pressure_reading,
                    flow_rate_reading,
                    root_cause_analysis,
                    recommended_action,
                    confidence_score,
                    status,
                    created_timestamp,
                    created_by_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self._execute_update(
                insert_query,
                [
                    recommendation_id,
                    equipment_id,
                    issue_type,
                    severity,
                    temperature,
                    pressure,
                    flow_rate,
                    root_cause,
                    recommended_action,
                    confidence,
                    "pending",
                    now,
                    self.agent_id
                ]
            )

            logger.info(
                f"✓ RECOMMENDATION CREATED: {recommendation_id} "
                f"for {equipment_id} (severity={severity}, confidence={confidence})"
            )

        except Exception as e:
            logger.error(f"Error creating recommendation: {e}")
            raise

    def _analyze_root_cause(
        self,
        temperature: float,
        pressure: Optional[float],
        flow_rate: Optional[float]
    ) -> str:
        """
        Analyze potential root causes for the anomaly.
        Simple rule-based analysis (can be enhanced with Genie integration).

        Args:
            temperature: Current temperature reading
            pressure: Current pressure reading
            flow_rate: Current flow rate reading

        Returns:
            Root cause analysis string
        """
        causes = []

        if temperature > 95:
            causes.append("Potential cooling system failure or blockage")

        if pressure and pressure > 100:
            causes.append("High system pressure detected - possible blockage")

        if flow_rate and flow_rate < 10:
            causes.append("Low flow rate detected - possible pump degradation")

        if not causes:
            causes.append("Elevated temperature - possible thermal load increase")

        return "; ".join(causes)

    def process_approvals(self) -> None:
        """
        Query agent_recommendations for approved items.
        Create agent_commands for approved recommendations.
        """
        try:
            logger.info("Processing approvals...")

            # Query approved recommendations that haven't been executed
            query = """
                SELECT
                    recommendation_id,
                    equipment_id,
                    recommended_action,
                    severity,
                    approved_timestamp
                FROM agent_recommendations
                WHERE status = 'approved'
                  AND executed_timestamp IS NULL
                  AND rejected_timestamp IS NULL
                ORDER BY approved_timestamp ASC
                LIMIT 20
            """

            approved_recs = self._execute_query(query)

            if not approved_recs:
                logger.debug("No approved recommendations to process")
                return

            logger.info(f"Found {len(approved_recs)} approved recommendations")

            # Create commands for each approved recommendation
            for rec in approved_recs:
                recommendation_id = rec[0]
                equipment_id = rec[1]
                recommended_action = rec[2]
                severity = rec[3]

                self._create_execution_command(
                    recommendation_id=recommendation_id,
                    equipment_id=equipment_id,
                    action=recommended_action,
                    severity=severity
                )

        except Exception as e:
            logger.error(f"Error in process_approvals: {e}")
            raise

    def _create_execution_command(
        self,
        recommendation_id: str,
        equipment_id: str,
        action: str,
        severity: str
    ) -> None:
        """
        Create an execution command in agent_commands table.

        Args:
            recommendation_id: ID of approved recommendation
            equipment_id: Equipment to be controlled
            action: Action description
            severity: Severity level
        """
        try:
            command_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            # Derive tag path and value from action
            tag_path, new_value = self._parse_action_to_command(
                equipment_id=equipment_id,
                action=action
            )

            # Insert into agent_commands table
            insert_query = """
                INSERT INTO agent_commands (
                    command_id,
                    recommendation_id,
                    equipment_id,
                    tag_path,
                    new_value,
                    action_description,
                    severity,
                    status,
                    created_timestamp,
                    created_by_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self._execute_update(
                insert_query,
                [
                    command_id,
                    recommendation_id,
                    equipment_id,
                    tag_path,
                    new_value,
                    action,
                    severity,
                    "pending",
                    now,
                    self.agent_id
                ]
            )

            logger.info(
                f"✓ COMMAND CREATED: {command_id} "
                f"for {equipment_id} (tag_path={tag_path}, value={new_value})"
            )

            # Update recommendation status
            update_query = """
                UPDATE agent_recommendations
                SET status = 'executing',
                    executed_timestamp = ?
                WHERE recommendation_id = ?
            """
            self._execute_update(update_query, [now, recommendation_id])

        except Exception as e:
            logger.error(f"Error creating execution command: {e}")
            raise

    def _parse_action_to_command(
        self,
        equipment_id: str,
        action: str
    ) -> tuple:
        """
        Parse action description into tag path and value to execute.
        Maps actions to specific equipment control points.

        Args:
            equipment_id: Equipment identifier
            action: Action description

        Returns:
            Tuple of (tag_path, new_value)
        """
        # Rule-based mapping of actions to tag paths
        # This is simplified - in production would be more sophisticated

        tag_prefix = f"[default]{equipment_id}"

        if "throughput" in action.lower():
            # Extract percentage reduction
            if "50%" in action:
                return (f"{tag_prefix}/ThroughputSetpoint", 50)
            elif "25%" in action:
                return (f"{tag_prefix}/ThroughputSetpoint", 75)
            elif "10%" in action:
                return (f"{tag_prefix}/ThroughputSetpoint", 90)

        if "cooling" in action.lower():
            return (f"{tag_prefix}/CoolingSystemStatus", 1)

        if "emergency" in action.lower() or "shutdown" in action.lower():
            return (f"{tag_prefix}/EmergencyStop", 1)

        if "pump" in action.lower():
            return (f"{tag_prefix}/PumpStatus", 0)

        # Default: reduce throughput by 10%
        return (f"{tag_prefix}/ThroughputSetpoint", 90)

    def execute_commands(self) -> None:
        """
        Execute pending commands.
        In a real scenario, this would call Ignition API or write to tags.
        For this implementation, we update the command status to executed.
        """
        try:
            logger.info("Executing pending commands...")

            # Query pending commands
            query = """
                SELECT
                    command_id,
                    equipment_id,
                    tag_path,
                    new_value,
                    action_description
                FROM agent_commands
                WHERE status = 'pending'
                ORDER BY created_timestamp ASC
                LIMIT 10
            """

            pending_commands = self._execute_query(query)

            if not pending_commands:
                logger.debug("No pending commands to execute")
                return

            logger.info(f"Found {len(pending_commands)} pending commands")

            # Execute each command
            for cmd in pending_commands:
                command_id = cmd[0]
                equipment_id = cmd[1]
                tag_path = cmd[2]
                new_value = cmd[3]
                action = cmd[4]

                success = self._execute_single_command(
                    command_id=command_id,
                    equipment_id=equipment_id,
                    tag_path=tag_path,
                    new_value=new_value,
                    action=action
                )

                if success:
                    self._mark_command_executed(command_id)
                else:
                    self._mark_command_failed(command_id)

        except Exception as e:
            logger.error(f"Error in execute_commands: {e}")
            raise

    def _execute_single_command(
        self,
        command_id: str,
        equipment_id: str,
        tag_path: str,
        new_value: Any,
        action: str
    ) -> bool:
        """
        Execute a single command.
        In production, this would interface with Ignition or PLC.

        Args:
            command_id: Unique command identifier
            equipment_id: Equipment to control
            tag_path: Tag path to write
            new_value: New value to write
            action: Action description

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(
                f"Executing command {command_id}: {tag_path} = {new_value}"
            )

            # In production, would call Ignition REST API or write to tags
            # For demo purposes, simulate successful execution
            time.sleep(0.5)  # Simulate write operation

            logger.info(
                f"✓ COMMAND EXECUTED: {command_id} "
                f"({equipment_id}: {action})"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to execute command {command_id}: {e}")
            return False

    def _mark_command_executed(self, command_id: str) -> None:
        """Mark a command as executed in the database."""
        try:
            now = datetime.now().isoformat()
            query = """
                UPDATE agent_commands
                SET status = 'executed',
                    executed_timestamp = ?
                WHERE command_id = ?
            """
            self._execute_update(query, [now, command_id])
            logger.debug(f"Command {command_id} marked as executed")
        except Exception as e:
            logger.error(f"Error marking command as executed: {e}")

    def _mark_command_failed(self, command_id: str) -> None:
        """Mark a command as failed in the database."""
        try:
            query = """
                UPDATE agent_commands
                SET status = 'failed'
                WHERE command_id = ?
            """
            self._execute_update(query, [command_id])
            logger.warning(f"Command {command_id} marked as failed")
        except Exception as e:
            logger.error(f"Error marking command as failed: {e}")

    def update_heartbeat(self) -> None:
        """
        Update agent health status in agent_health table.
        Provides monitoring of agent health status.
        """
        try:
            now = datetime.now().isoformat()

            # Check if agent has heartbeat record
            check_query = """
                SELECT agent_id FROM agent_health
                WHERE agent_id = ?
                LIMIT 1
            """

            result = self._execute_query(check_query, [self.agent_id])

            if result:
                # Update existing heartbeat
                update_query = """
                    UPDATE agent_health
                    SET last_heartbeat = ?,
                        status = 'online',
                        polls_completed = polls_completed + 1
                    WHERE agent_id = ?
                """
                self._execute_update(update_query, [now, self.agent_id])
            else:
                # Create new heartbeat record
                insert_query = """
                    INSERT INTO agent_health (
                        agent_id,
                        last_heartbeat,
                        status,
                        polls_completed,
                        created_timestamp
                    ) VALUES (?, ?, ?, ?, ?)
                """
                self._execute_update(
                    insert_query,
                    [self.agent_id, now, "online", 1, now]
                )

            logger.debug(f"Heartbeat updated for agent {self.agent_id}")

        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")

    def monitor_loop(self) -> None:
        """
        Main monitoring loop that runs continuously.
        Polls every 10 seconds for anomalies and approvals.
        Includes retry logic for resilience.
        """
        logger.info(f"[STARTUP] Agent {self.agent_id} starting monitoring loop...")
        logger.info(f"Poll interval: {self.poll_interval} seconds")

        retry_count = 0
        consecutive_errors = 0

        while True:
            try:
                # Run main monitoring cycle
                cycle_start = time.time()

                # Step 1: Detect anomalies
                self.detect_anomalies()

                # Step 2: Process approvals
                self.process_approvals()

                # Step 3: Execute pending commands
                self.execute_commands()

                # Step 4: Update health status
                self.update_heartbeat()

                cycle_duration = time.time() - cycle_start

                logger.info(
                    f"[CYCLE COMPLETE] Duration: {cycle_duration:.2f}s, "
                    f"Next poll in {self.poll_interval}s"
                )

                # Reset error counters on successful cycle
                retry_count = 0
                consecutive_errors = 0

                # Wait before next poll
                time.sleep(self.poll_interval)

            except Exception as e:
                consecutive_errors += 1
                logger.error(f"[ERROR] Cycle {consecutive_errors}: {e}")

                # Exponential backoff on repeated errors
                if consecutive_errors > 5:
                    backoff_time = min(60, self.poll_interval * (2 ** (consecutive_errors - 5)))
                    logger.warning(
                        f"[BACKOFF] Too many consecutive errors. "
                        f"Backing off for {backoff_time}s"
                    )
                    time.sleep(backoff_time)
                else:
                    time.sleep(self.poll_interval)

    def verify_connection(self) -> bool:
        """
        Verify database connection is working.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            query = "SELECT 1 AS health_check"
            result = self._execute_query(query)
            if result and len(result) > 0:
                logger.info("✓ Database connection verified")
                return True
            return False
        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return False

    def print_status(self) -> None:
        """Print current agent status and recent activity."""
        try:
            logger.info("\n" + "="*70)
            logger.info("AGENT STATUS REPORT")
            logger.info("="*70)

            # Agent info
            logger.info(f"Agent ID: {self.agent_id}")
            logger.info(f"Timestamp: {datetime.now().isoformat()}")

            # Recommendation count
            rec_query = "SELECT COUNT(*) FROM agent_recommendations"
            rec_count = self._execute_query(rec_query)
            logger.info(f"Total recommendations: {rec_count[0][0] if rec_count else 0}")

            # Pending recommendations
            pending_query = """
                SELECT COUNT(*) FROM agent_recommendations
                WHERE status = 'pending'
            """
            pending_count = self._execute_query(pending_query)
            logger.info(f"Pending recommendations: {pending_count[0][0] if pending_count else 0}")

            # Commands executed
            cmd_query = """
                SELECT COUNT(*) FROM agent_commands
                WHERE status = 'executed'
            """
            cmd_count = self._execute_query(cmd_query)
            logger.info(f"Commands executed: {cmd_count[0][0] if cmd_count else 0}")

            logger.info("="*70 + "\n")

        except Exception as e:
            logger.error(f"Error printing status: {e}")


def main():
    """Main entry point for the operations agent."""
    logger.info("Initializing Operations Agent...")

    try:
        agent = OperationsAgent()

        # Verify connection before starting
        if not agent.verify_connection():
            logger.error("Failed to verify database connection. Exiting.")
            return

        # Print initial status
        agent.print_status()

        # Start monitoring loop
        agent.monitor_loop()

    except KeyboardInterrupt:
        logger.info("Agent interrupted by user. Shutting down gracefully...")
    except Exception as e:
        logger.critical(f"Fatal error in agent: {e}")
        raise


if __name__ == "__main__":
    main()
