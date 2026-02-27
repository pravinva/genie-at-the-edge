"""
PostgreSQL NOTIFY Listener for Ignition Gateway
Receives real-time notifications from Lakebase and pushes to Perspective sessions
Achieves <100ms notification latency as specified in architecture
"""

import system
import time
import json
from java.lang import Thread, Runnable
from org.postgresql import PGConnection
from java.sql import DriverManager
from java.util import Properties

class LakebaseNotifyListener(Runnable):
    """
    Real-time listener for PostgreSQL NOTIFY events.
    Runs in gateway scope and pushes notifications to Perspective sessions.
    """

    def __init__(self):
        # Connection parameters
        self.host = system.tag.readBlocking(['[default]Lakebase/Host'])[0].value or 'localhost'
        self.port = system.tag.readBlocking(['[default]Lakebase/Port'])[0].value or 5432
        self.database = system.tag.readBlocking(['[default]Lakebase/Database'])[0].value or 'genie_mining'
        self.user = system.tag.readBlocking(['[default]Lakebase/User'])[0].value or 'databricks_user'
        self.password = system.tag.readBlocking(['[default]Lakebase/Password'])[0].value

        # JDBC URL
        self.jdbc_url = f"jdbc:postgresql://{self.host}:{self.port}/{self.database}"

        # Channels to listen on
        self.channels = [
            'recommendations',
            'recommendations_critical',
            'recommendations_high',
            'recommendations_medium',
            'decisions',
            'commands',
            'agent_health'
        ]

        # Connection and state
        self.connection = None
        self.pg_connection = None
        self.running = False
        self.logger = system.util.getLogger("LakebaseListener")

        # Performance metrics
        self.notification_count = 0
        self.total_latency_ms = 0
        self.last_notification_time = None

    def connect(self):
        """Establish connection to Lakebase and set up listeners"""
        try:
            # Load PostgreSQL driver
            Class.forName("org.postgresql.Driver")

            # Connection properties
            props = Properties()
            props.setProperty("user", self.user)
            props.setProperty("password", self.password)

            # Create connection
            self.connection = DriverManager.getConnection(self.jdbc_url, props)
            self.connection.setAutoCommit(True)

            # Get PostgreSQL-specific connection for NOTIFY
            self.pg_connection = self.connection.unwrap(PGConnection)

            # Create statement for LISTEN commands
            stmt = self.connection.createStatement()

            # Listen on all channels
            for channel in self.channels:
                stmt.execute(f"LISTEN {channel}")
                self.logger.info(f"Listening on channel: {channel}")

            stmt.close()

            # Update connection status tag
            system.tag.writeBlocking(
                ['[default]Mining/NotifyListener/Status'],
                ['Connected']
            )

            self.logger.info("Lakebase NOTIFY listener connected successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect: {str(e)}")
            system.tag.writeBlocking(
                ['[default]Mining/NotifyListener/Status'],
                ['Disconnected']
            )
            return False

    def run(self):
        """Main listening loop - runs in separate thread"""
        self.running = True
        self.logger.info("Starting NOTIFY listener thread...")

        # Connect to database
        if not self.connect():
            self.logger.error("Failed to establish initial connection")
            return

        # Main loop
        while self.running:
            try:
                # Get notifications (with 1 second timeout)
                notifications = self.pg_connection.getNotifications(1000)

                if notifications:
                    for notification in notifications:
                        self.handle_notification(notification)

                # Check connection health every 10 iterations
                if self.notification_count % 10 == 0:
                    self.check_connection_health()

            except Exception as e:
                self.logger.error(f"Error in listen loop: {str(e)}")

                # Try to reconnect
                time.sleep(5)
                if not self.connect():
                    self.logger.error("Reconnection failed, will retry...")

        # Cleanup
        self.cleanup()

    def handle_notification(self, notification):
        """Process a received notification"""
        try:
            # Track receive time for latency measurement
            receive_time = system.date.now()

            # Parse notification
            channel = notification.getName()
            payload_str = notification.getParameter()

            # Parse JSON payload
            payload = system.util.jsonDecode(payload_str)

            # Add receive timestamp and channel
            payload['_received_at'] = str(receive_time)
            payload['_channel'] = channel

            # Calculate latency if timestamp in payload
            if 'timestamp' in payload:
                send_time = system.date.parse(payload['timestamp'])
                latency_ms = system.date.millisBetween(send_time, receive_time)
                payload['_latency_ms'] = latency_ms

                # Update metrics
                self.notification_count += 1
                self.total_latency_ms += latency_ms
                avg_latency = self.total_latency_ms / self.notification_count

                # Log if latency exceeds 100ms threshold
                if latency_ms > 100:
                    self.logger.warn(f"High latency detected: {latency_ms}ms for {channel}")

                # Update performance tags
                system.tag.writeBlocking(
                    [
                        '[default]Mining/NotifyListener/AvgLatency',
                        '[default]Mining/NotifyListener/LastLatency',
                        '[default]Mining/NotifyListener/NotificationCount'
                    ],
                    [avg_latency, latency_ms, self.notification_count]
                )

            self.logger.info(f"[{channel}] {payload.get('event_type', 'unknown')}: latency={payload.get('_latency_ms', 'N/A')}ms")

            # Route to appropriate handler
            if channel.startswith('recommendations'):
                self.handle_recommendation(payload)
            elif channel == 'decisions':
                self.handle_decision(payload)
            elif channel == 'commands':
                self.handle_command(payload)
            elif channel == 'agent_health':
                self.handle_agent_health(payload)

            # Store last notification time
            self.last_notification_time = receive_time

        except Exception as e:
            self.logger.error(f"Error handling notification: {str(e)}")

    def handle_recommendation(self, payload):
        """Handle new recommendation notification"""
        try:
            # Update recommendation count tag
            count_tag = '[default]Mining/Recommendations/Count'
            current_count = system.tag.readBlocking([count_tag])[0].value or 0
            system.tag.writeBlocking([count_tag], [current_count + 1])

            # Store latest recommendation
            system.tag.writeBlocking(
                ['[default]Mining/Recommendations/Latest'],
                [system.util.jsonEncode(payload)]
            )

            # Send to all Perspective sessions
            system.perspective.sendMessage(
                'newRecommendation',
                payload=payload,
                scope='session'
            )

            # Send to specific page if severity is critical
            if payload.get('severity') == 'critical':
                system.perspective.sendMessage(
                    'criticalAlert',
                    payload=payload,
                    scope='page',
                    pageId='/agent-hmi'
                )

            # Log for audit
            self.logger.info(f"New recommendation: {payload['recommendation_id']} for {payload['equipment_id']}")

        except Exception as e:
            self.logger.error(f"Error handling recommendation: {str(e)}")

    def handle_decision(self, payload):
        """Handle operator decision notification"""
        try:
            # Send to Perspective sessions
            system.perspective.sendMessage(
                'operatorDecision',
                payload=payload,
                scope='session'
            )

            # Update decision count by type
            decision_type = payload.get('new_status', 'unknown')
            tag_path = f"[default]Mining/Decisions/{decision_type.capitalize()}Count"
            current = system.tag.readBlocking([tag_path])[0].value or 0
            system.tag.writeBlocking([tag_path], [current + 1])

            self.logger.info(f"Operator decision: {payload['new_status']} for {payload['recommendation_id']}")

        except Exception as e:
            self.logger.error(f"Error handling decision: {str(e)}")

    def handle_command(self, payload):
        """Handle command execution notification"""
        try:
            # Send to Perspective
            system.perspective.sendMessage(
                'commandExecution',
                payload=payload,
                scope='session'
            )

            # If command executed successfully, update the equipment tag
            if payload.get('status') == 'executed':
                tag_path = payload.get('tag_path')
                if tag_path:
                    system.tag.writeBlocking([tag_path], [payload.get('new_value')])
                    self.logger.info(f"Tag updated: {tag_path} = {payload.get('new_value')}")

            self.logger.info(f"Command {payload['command_id']}: {payload['status']}")

        except Exception as e:
            self.logger.error(f"Error handling command: {str(e)}")

    def handle_agent_health(self, payload):
        """Handle agent health update"""
        try:
            # Update agent health tags
            agent_id = payload.get('agent_id', 'unknown')
            system.tag.writeBlocking(
                [
                    f"[default]Mining/Agents/{agent_id}/Status",
                    f"[default]Mining/Agents/{agent_id}/LastHeartbeat",
                    f"[default]Mining/Agents/{agent_id}/PollsCompleted"
                ],
                [
                    payload.get('status'),
                    payload.get('last_heartbeat'),
                    payload.get('polls_completed')
                ]
            )

            # Send to Perspective
            system.perspective.sendMessage(
                'agentHealth',
                payload=payload,
                scope='session'
            )

            self.logger.info(f"Agent health: {agent_id} - {payload.get('status')}")

        except Exception as e:
            self.logger.error(f"Error handling agent health: {str(e)}")

    def check_connection_health(self):
        """Periodic connection health check"""
        try:
            # Simple query to check connection
            stmt = self.connection.createStatement()
            rs = stmt.executeQuery("SELECT 1")
            rs.close()
            stmt.close()

            # Update health tag
            system.tag.writeBlocking(
                ['[default]Mining/NotifyListener/Healthy'],
                [True]
            )

        except Exception as e:
            self.logger.warn(f"Connection health check failed: {str(e)}")
            system.tag.writeBlocking(
                ['[default]Mining/NotifyListener/Healthy'],
                [False]
            )

    def stop(self):
        """Stop the listener"""
        self.running = False
        self.logger.info("Stopping NOTIFY listener...")

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.connection and not self.connection.isClosed():
                # Unlisten from all channels
                stmt = self.connection.createStatement()
                for channel in self.channels:
                    stmt.execute(f"UNLISTEN {channel}")
                stmt.close()

                # Close connection
                self.connection.close()

            # Update status
            system.tag.writeBlocking(
                ['[default]Mining/NotifyListener/Status'],
                ['Stopped']
            )

            self.logger.info("NOTIFY listener cleaned up successfully")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


# Gateway startup function
def start_lakebase_listener():
    """Start the Lakebase NOTIFY listener in a separate thread"""
    try:
        # Check if listener already running
        if system.util.getGlobals().get('lakebaseListener'):
            listener = system.util.getGlobals()['lakebaseListener']
            if listener.running:
                system.util.getLogger("LakebaseListener").info("Listener already running")
                return

        # Create and start listener
        listener = LakebaseNotifyListener()
        thread = Thread(listener, "LakebaseNotifyListener")
        thread.setDaemon(True)
        thread.start()

        # Store reference in globals
        system.util.getGlobals()['lakebaseListener'] = listener
        system.util.getGlobals()['lakebaseListenerThread'] = thread

        system.util.getLogger("LakebaseListener").info("Lakebase NOTIFY listener started")

    except Exception as e:
        system.util.getLogger("LakebaseListener").error(f"Failed to start listener: {str(e)}")


# Gateway shutdown function
def stop_lakebase_listener():
    """Stop the Lakebase NOTIFY listener"""
    try:
        listener = system.util.getGlobals().get('lakebaseListener')
        if listener:
            listener.stop()
            thread = system.util.getGlobals().get('lakebaseListenerThread')
            if thread:
                thread.join(5000)  # Wait up to 5 seconds

        system.util.getLogger("LakebaseListener").info("Lakebase NOTIFY listener stopped")

    except Exception as e:
        system.util.getLogger("LakebaseListener").error(f"Error stopping listener: {str(e)}")


# Add to gateway startup script:
# start_lakebase_listener()

# Add to gateway shutdown script:
# stop_lakebase_listener()