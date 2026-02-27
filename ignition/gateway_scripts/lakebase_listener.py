"""
Ignition Gateway Event Script - Lakebase PostgreSQL NOTIFY Listener
Purpose: Subscribe to PostgreSQL NOTIFY events and push to Perspective sessions
Target Latency: < 100ms from database event to UI update

Installation:
1. Copy to Ignition Gateway Event Scripts
2. Set as Gateway Startup Script
3. Configure Lakebase database connection in Ignition
"""

import system
import psycopg2
import select
import json
import threading
from java.lang import Thread, InterruptedException
from java.util.concurrent import Executors, TimeUnit

# Configuration
LAKEBASE_DB_NAME = "Lakebase_JDBC"  # Name of the database connection in Ignition
NOTIFY_CHANNELS = ["new_ml_recommendation", "recommendation_status_changed"]
RECONNECT_DELAY_SEC = 5
HEARTBEAT_INTERVAL_SEC = 30

class LakebaseNotifyListener:
    """
    PostgreSQL NOTIFY listener for real-time event streaming
    Replaces polling with event-driven push notifications
    """

    def __init__(self):
        self.connection = None
        self.cursor = None
        self.running = False
        self.executor = Executors.newSingleThreadExecutor()
        self.last_heartbeat = system.date.now()

    def connect(self):
        """Establish connection to Lakebase PostgreSQL"""
        try:
            # Get connection details from Ignition's database connection
            db_conn = system.db.getConnection(LAKEBASE_DB_NAME)

            # Extract connection parameters
            # Note: In production, use Ignition's connection pooling
            conn_string = db_conn.getMetaData().getURL()

            # Parse JDBC URL to psycopg2 format
            # jdbc:postgresql://host:port/database -> host, port, database
            import re
            match = re.match(r'jdbc:postgresql://([^:]+):(\d+)/(.+)', conn_string)
            if match:
                host, port, database = match.groups()
            else:
                raise ValueError("Invalid JDBC URL format")

            # Connect using psycopg2
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=system.db.getConnectionInfo(LAKEBASE_DB_NAME)["Username"],
                password=system.db.getConnectionInfo(LAKEBASE_DB_NAME)["Password"],
                connect_timeout=10
            )

            # Set to autocommit mode for LISTEN/NOTIFY
            self.connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.connection.cursor()

            # Subscribe to notification channels
            for channel in NOTIFY_CHANNELS:
                self.cursor.execute(f"LISTEN {channel};")
                system.util.getLogger("LakebaseListener").info(f"Subscribed to channel: {channel}")

            return True

        except Exception as e:
            system.util.getLogger("LakebaseListener").error(f"Connection failed: {str(e)}")
            return False

    def process_notification(self, notify):
        """Process PostgreSQL notification and push to Perspective sessions"""
        try:
            channel = notify.channel
            payload = json.loads(notify.payload)

            logger = system.util.getLogger("LakebaseListener")
            logger.info(f"Received {channel}: {payload.get('recommendation_id', 'unknown')}")

            # Track latency
            if 'timestamp' in payload:
                db_time = system.date.parse(payload['timestamp'], "yyyy-MM-dd HH:mm:ss")
                latency_ms = system.date.millisBetween(db_time, system.date.now())
                logger.info(f"End-to-end latency: {latency_ms}ms")

                # Alert if latency exceeds target
                if latency_ms > 100:
                    logger.warn(f"Latency exceeded target: {latency_ms}ms > 100ms")

            # Route based on notification type
            if channel == "new_ml_recommendation":
                self.handle_new_recommendation(payload)
            elif channel == "recommendation_status_changed":
                self.handle_status_change(payload)

        except Exception as e:
            system.util.getLogger("LakebaseListener").error(f"Error processing notification: {str(e)}")

    def handle_new_recommendation(self, payload):
        """Push new ML recommendation to all active Perspective sessions"""

        # Prepare message for Perspective
        message = {
            "type": "NEW_RECOMMENDATION",
            "data": {
                "recommendationId": payload.get("recommendation_id"),
                "equipmentId": payload.get("equipment_id"),
                "issueType": payload.get("issue_type"),
                "severity": payload.get("severity"),
                "confidenceScore": payload.get("confidence_score"),
                "recommendedAction": payload.get("recommended_action"),
                "timestamp": system.date.now()
            }
        }

        # Send to all Perspective sessions viewing the recommendations page
        system.perspective.sendMessage(
            messageType="ML_RECOMMENDATION_UPDATE",
            payload=message,
            scope="page",
            pageId="*/agent-recommendations/*"  # Target specific pages
        )

        # Also update the notification badge
        self.update_notification_badge(1)

        # Log for debugging
        logger = system.util.getLogger("LakebaseListener")
        logger.info(f"Pushed recommendation {payload.get('recommendation_id')} to UI")

        # Store in memory tags for quick access
        base_path = "[default]ML_Recommendations/Latest/"
        system.tag.writeBlocking([
            base_path + "RecommendationId",
            base_path + "EquipmentId",
            base_path + "Severity",
            base_path + "Timestamp"
        ], [
            payload.get("recommendation_id"),
            payload.get("equipment_id"),
            payload.get("severity"),
            system.date.now()
        ])

    def handle_status_change(self, payload):
        """Handle operator actions on recommendations"""

        message = {
            "type": "STATUS_UPDATE",
            "data": {
                "recommendationId": payload.get("recommendation_id"),
                "oldStatus": payload.get("old_status"),
                "newStatus": payload.get("new_status"),
                "operatorId": payload.get("operator_id"),
                "operatorNotes": payload.get("operator_notes"),
                "timestamp": system.date.now()
            }
        }

        # Send status update to UI
        system.perspective.sendMessage(
            messageType="ML_RECOMMENDATION_STATUS",
            payload=message,
            scope="session"
        )

        # Update metrics
        if payload.get("new_status") == "approved":
            self.increment_metric("recommendations_approved")
        elif payload.get("new_status") == "rejected":
            self.increment_metric("recommendations_rejected")

    def update_notification_badge(self, increment):
        """Update the notification badge count"""
        tag_path = "[default]UI/NotificationCount"
        try:
            current = system.tag.readBlocking([tag_path])[0].value or 0
            system.tag.writeBlocking([tag_path], [current + increment])
        except:
            pass  # Tag might not exist

    def increment_metric(self, metric_name):
        """Track metrics for monitoring"""
        tag_path = f"[default]Metrics/{metric_name}"
        try:
            current = system.tag.readBlocking([tag_path])[0].value or 0
            system.tag.writeBlocking([tag_path], [current + 1])
        except:
            pass

    def listen_loop(self):
        """Main listening loop - runs in background thread"""
        self.running = True
        reconnect_attempts = 0

        while self.running:
            try:
                # Connect if not connected
                if not self.connection or self.connection.closed:
                    system.util.getLogger("LakebaseListener").info("Connecting to Lakebase...")
                    if not self.connect():
                        reconnect_attempts += 1
                        delay = min(RECONNECT_DELAY_SEC * reconnect_attempts, 60)
                        Thread.sleep(delay * 1000)
                        continue
                    else:
                        reconnect_attempts = 0
                        system.util.getLogger("LakebaseListener").info("Connected successfully")

                # Wait for notifications with timeout for heartbeat
                if select.select([self.connection], [], [], HEARTBEAT_INTERVAL_SEC) == ([], [], []):
                    # Timeout - send heartbeat
                    self.cursor.execute("SELECT 1")
                    self.last_heartbeat = system.date.now()
                    continue

                # Process notifications
                self.connection.poll()
                while self.connection.notifies:
                    notify = self.connection.notifies.pop(0)
                    self.process_notification(notify)

            except InterruptedException:
                # Shutdown requested
                break
            except Exception as e:
                system.util.getLogger("LakebaseListener").error(f"Listen loop error: {str(e)}")
                # Close connection to force reconnect
                try:
                    self.connection.close()
                except:
                    pass
                Thread.sleep(RECONNECT_DELAY_SEC * 1000)

    def start(self):
        """Start the listener in a background thread"""
        self.executor.submit(self.listen_loop)
        system.util.getLogger("LakebaseListener").info("Lakebase listener started")

    def stop(self):
        """Stop the listener gracefully"""
        self.running = False
        try:
            if self.connection:
                # Unsubscribe from channels
                for channel in NOTIFY_CHANNELS:
                    self.cursor.execute(f"UNLISTEN {channel};")
                self.connection.close()
        except:
            pass

        self.executor.shutdown()
        system.util.getLogger("LakebaseListener").info("Lakebase listener stopped")

# Global instance
_listener = None

def startup():
    """Gateway startup script entry point"""
    global _listener

    system.util.getLogger("LakebaseListener").info("Initializing Lakebase NOTIFY listener...")

    # Create and start listener
    _listener = LakebaseNotifyListener()
    _listener.start()

    # Register shutdown hook
    system.util.invokeAsynchronous(lambda: register_shutdown_hook())

    system.util.getLogger("LakebaseListener").info("Lakebase listener initialized")

def shutdown():
    """Gateway shutdown script"""
    global _listener

    if _listener:
        system.util.getLogger("LakebaseListener").info("Stopping Lakebase listener...")
        _listener.stop()
        _listener = None

def register_shutdown_hook():
    """Register JVM shutdown hook for clean shutdown"""
    from java.lang import Runtime

    class ShutdownHook(Thread):
        def run(self):
            shutdown()

    Runtime.getRuntime().addShutdownHook(ShutdownHook())

# Auto-start if this script is loaded
startup()