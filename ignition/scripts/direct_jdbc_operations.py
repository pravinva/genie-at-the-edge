"""
Direct JDBC Operations for Lakebase
Provides <200ms write latency for operator decisions
Bypasses named queries for real-time performance
"""

import system
import time
import json
from java.sql import DriverManager, PreparedStatement, ResultSet
from java.util import Properties

class DirectJDBCManager:
    """
    Manages direct JDBC connections to Lakebase for high-performance operations.
    Achieves <200ms latency for operator decisions as specified in architecture.
    """

    def __init__(self):
        # Connection parameters (stored in Ignition tags for security)
        self.host = system.tag.readBlocking(['[default]Lakebase/Host'])[0].value
        self.port = system.tag.readBlocking(['[default]Lakebase/Port'])[0].value
        self.database = system.tag.readBlocking(['[default]Lakebase/Database'])[0].value
        self.user = system.tag.readBlocking(['[default]Lakebase/User'])[0].value
        self.password = system.tag.readBlocking(['[default]Lakebase/Password'])[0].value

        # JDBC URL for PostgreSQL
        self.jdbc_url = f"jdbc:postgresql://{self.host}:{self.port}/{self.database}"

        # Connection pool
        self.connection = None

    def get_connection(self):
        """Get or create a JDBC connection"""
        try:
            if self.connection is None or self.connection.isClosed():
                # Load PostgreSQL driver
                Class.forName("org.postgresql.Driver")

                # Set connection properties
                props = Properties()
                props.setProperty("user", self.user)
                props.setProperty("password", self.password)
                props.setProperty("ssl", "false")  # Adjust based on your setup

                # Create connection
                self.connection = DriverManager.getConnection(self.jdbc_url, props)

                # Set auto-commit for immediate writes
                self.connection.setAutoCommit(True)

                system.util.getLogger("DirectJDBC").info("Direct JDBC connection established")

            return self.connection

        except Exception as e:
            system.util.getLogger("DirectJDBC").error(f"Failed to connect: {str(e)}")
            raise

    def write_operator_decision(self, recommendation_id, decision, operator, reason=None):
        """
        Write operator decision directly to Lakebase with <200ms latency.

        Args:
            recommendation_id: UUID of the recommendation
            decision: 'approved', 'rejected', or 'deferred'
            operator: Username of the operator
            reason: Optional reason for the decision

        Returns:
            Dictionary with success status and latency metrics
        """
        start_time = system.date.now()

        try:
            conn = self.get_connection()

            # Prepare SQL based on decision type
            if decision == 'approved':
                sql = """
                    UPDATE agent_recommendations
                    SET status = 'approved',
                        approved_timestamp = CURRENT_TIMESTAMP,
                        approved_by = ?,
                        approval_reason = ?
                    WHERE recommendation_id = ?
                """
            elif decision == 'rejected':
                sql = """
                    UPDATE agent_recommendations
                    SET status = 'rejected',
                        rejected_timestamp = CURRENT_TIMESTAMP,
                        rejected_by = ?,
                        rejection_reason = ?
                    WHERE recommendation_id = ?
                """
            else:  # deferred
                sql = """
                    UPDATE agent_recommendations
                    SET status = 'deferred',
                        deferred_timestamp = CURRENT_TIMESTAMP,
                        deferred_by = ?,
                        deferral_reason = ?
                    WHERE recommendation_id = ?
                """

            # Execute with prepared statement
            stmt = conn.prepareStatement(sql)
            stmt.setString(1, operator)
            stmt.setString(2, reason or "")
            stmt.setString(3, recommendation_id)

            rows_affected = stmt.executeUpdate()
            stmt.close()

            # Calculate latency
            end_time = system.date.now()
            latency_ms = system.date.millisBetween(start_time, end_time)

            # Log performance metrics
            system.util.getLogger("DirectJDBC").info(
                f"Decision written in {latency_ms}ms: {decision} for {recommendation_id}"
            )

            # Send immediate feedback to UI
            system.perspective.sendMessage(
                "decisionConfirmed",
                payload={
                    'recommendation_id': recommendation_id,
                    'decision': decision,
                    'operator': operator,
                    'latency_ms': latency_ms,
                    'timestamp': str(end_time)
                },
                scope="session"
            )

            return {
                'success': rows_affected > 0,
                'latency_ms': latency_ms,
                'rows_affected': rows_affected,
                'decision': decision,
                'timestamp': str(end_time)
            }

        except Exception as e:
            system.util.getLogger("DirectJDBC").error(f"Write failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'latency_ms': system.date.millisBetween(start_time, system.date.now())
            }

    def batch_write_decisions(self, decisions):
        """
        Write multiple operator decisions in a single transaction.
        Optimized for bulk operations.

        Args:
            decisions: List of decision dictionaries

        Returns:
            Dictionary with batch operation results
        """
        start_time = system.date.now()
        results = []

        try:
            conn = self.get_connection()
            conn.setAutoCommit(False)  # Use transaction for batch

            for decision in decisions:
                try:
                    sql = """
                        UPDATE agent_recommendations
                        SET status = ?,
                            approved_timestamp = CASE WHEN ? = 'approved' THEN CURRENT_TIMESTAMP ELSE approved_timestamp END,
                            rejected_timestamp = CASE WHEN ? = 'rejected' THEN CURRENT_TIMESTAMP ELSE rejected_timestamp END,
                            approved_by = CASE WHEN ? = 'approved' THEN ? ELSE approved_by END,
                            rejected_by = CASE WHEN ? = 'rejected' THEN ? ELSE rejected_by END
                        WHERE recommendation_id = ?
                    """

                    stmt = conn.prepareStatement(sql)
                    stmt.setString(1, decision['status'])
                    stmt.setString(2, decision['status'])
                    stmt.setString(3, decision['status'])
                    stmt.setString(4, decision['status'])
                    stmt.setString(5, decision['operator'])
                    stmt.setString(6, decision['status'])
                    stmt.setString(7, decision['operator'])
                    stmt.setString(8, decision['recommendation_id'])

                    rows = stmt.executeUpdate()
                    stmt.close()

                    results.append({
                        'recommendation_id': decision['recommendation_id'],
                        'success': rows > 0
                    })

                except Exception as e:
                    results.append({
                        'recommendation_id': decision['recommendation_id'],
                        'success': False,
                        'error': str(e)
                    })

            # Commit batch
            conn.commit()
            conn.setAutoCommit(True)

            latency_ms = system.date.millisBetween(start_time, system.date.now())

            return {
                'success': True,
                'total_processed': len(decisions),
                'successful': sum(1 for r in results if r.get('success', False)),
                'failed': sum(1 for r in results if not r.get('success', False)),
                'latency_ms': latency_ms,
                'avg_latency_per_item': latency_ms / len(decisions) if decisions else 0,
                'results': results
            }

        except Exception as e:
            conn.rollback()
            conn.setAutoCommit(True)
            system.util.getLogger("DirectJDBC").error(f"Batch write failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'latency_ms': system.date.millisBetween(start_time, system.date.now())
            }

    def get_recommendation_details(self, recommendation_id):
        """
        Retrieve full recommendation details with direct JDBC.
        Faster than named queries for real-time UI updates.
        """
        try:
            conn = self.get_connection()

            sql = """
                SELECT r.*,
                       c.command_id, c.status as command_status
                FROM agent_recommendations r
                LEFT JOIN agent_commands c ON r.recommendation_id = c.recommendation_id
                WHERE r.recommendation_id = ?
            """

            stmt = conn.prepareStatement(sql)
            stmt.setString(1, recommendation_id)

            rs = stmt.executeQuery()

            if rs.next():
                # Build result dictionary
                result = {
                    'recommendation_id': rs.getString('recommendation_id'),
                    'equipment_id': rs.getString('equipment_id'),
                    'issue_type': rs.getString('issue_type'),
                    'severity': rs.getString('severity'),
                    'status': rs.getString('status'),
                    'temperature_reading': rs.getFloat('temperature_reading'),
                    'pressure_reading': rs.getFloat('pressure_reading'),
                    'flow_rate_reading': rs.getFloat('flow_rate_reading'),
                    'recommended_action': rs.getString('recommended_action'),
                    'confidence_score': rs.getFloat('confidence_score'),
                    'root_cause_analysis': rs.getString('root_cause_analysis'),
                    'created_timestamp': str(rs.getTimestamp('created_timestamp')),
                    'command_id': rs.getString('command_id'),
                    'command_status': rs.getString('command_status')
                }

                rs.close()
                stmt.close()
                return result

            rs.close()
            stmt.close()
            return None

        except Exception as e:
            system.util.getLogger("DirectJDBC").error(f"Query failed: {str(e)}")
            return None

    def close(self):
        """Close the JDBC connection"""
        if self.connection and not self.connection.isClosed():
            self.connection.close()
            system.util.getLogger("DirectJDBC").info("Direct JDBC connection closed")


# Gateway message handler for direct JDBC writes
def handle_direct_jdbc_message(payload):
    """
    Message handler for direct JDBC write requests from Perspective.
    Register this in the gateway message handlers.
    """
    try:
        manager = DirectJDBCManager()

        if payload.get('action') == 'write_decision':
            result = manager.write_operator_decision(
                payload['recommendation_id'],
                payload['decision'],
                payload['operator'],
                payload.get('reason')
            )

        elif payload.get('action') == 'batch_write':
            result = manager.batch_write_decisions(payload['decisions'])

        elif payload.get('action') == 'get_details':
            result = manager.get_recommendation_details(payload['recommendation_id'])

        else:
            result = {'success': False, 'error': 'Unknown action'}

        # Send result back to session
        system.perspective.sendMessage(
            'jdbcResult',
            payload=result,
            scope=payload.get('sessionId', 'session')
        )

        manager.close()

    except Exception as e:
        system.util.getLogger("DirectJDBC").error(f"Message handler error: {str(e)}")
        system.perspective.sendMessage(
            'jdbcError',
            payload={'error': str(e)},
            scope=payload.get('sessionId', 'session')
        )


# Register the message handler (add to gateway startup script)
system.perspective.addMessageHandler('directJDBCWrite', handle_direct_jdbc_message)