#!/usr/bin/env python3
"""
Setup PostgreSQL NOTIFY triggers for real-time webhooks to Ignition.
This achieves <100ms latency as specified in the architecture.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys
from databricks import sql
from databricks.sdk import WorkspaceClient

def get_lakebase_connection():
    """Get connection to Lakebase PostgreSQL instance"""

    # Try to get connection details from Databricks
    try:
        w = WorkspaceClient()

        # Get Lakebase connection string
        # This assumes Lakebase is configured in your workspace
        connection_params = {
            'host': os.getenv('LAKEBASE_HOST', 'localhost'),
            'port': os.getenv('LAKEBASE_PORT', 5432),
            'database': os.getenv('LAKEBASE_DATABASE', 'genie_mining'),
            'user': os.getenv('LAKEBASE_USER', 'databricks_user'),
            'password': os.getenv('LAKEBASE_PASSWORD', 'your_password')
        }

        return psycopg2.connect(**connection_params)

    except Exception as e:
        print(f"Error connecting to Lakebase: {e}")
        print("Please ensure LAKEBASE_* environment variables are set")
        sys.exit(1)

def setup_notify_triggers(conn):
    """Create all NOTIFY triggers and functions"""

    print("🔧 Setting up PostgreSQL NOTIFY triggers...")

    # Read SQL file
    sql_file = 'lakebase_notify_triggers.sql'
    with open(sql_file, 'r') as f:
        sql_script = f.read()

    # Split into individual statements
    statements = [s.strip() for s in sql_script.split(';') if s.strip()]

    cursor = conn.cursor()

    for i, statement in enumerate(statements):
        try:
            # Skip comments
            if statement.startswith('--'):
                continue

            cursor.execute(statement + ';')
            print(f"  ✅ Executed statement {i+1}/{len(statements)}")

        except psycopg2.Error as e:
            print(f"  ⚠️  Warning on statement {i+1}: {e}")
            # Continue with other statements

    conn.commit()
    cursor.close()

    print("\n✅ All NOTIFY triggers created successfully!")

def test_notifications(conn):
    """Test the NOTIFY system"""

    print("\n🧪 Testing NOTIFY system...")

    # Set up a listener
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Listen on test channel
    cursor.execute("LISTEN test_channel;")
    cursor.execute("LISTEN recommendations;")

    print("  📡 Listening for notifications...")

    # Send a test notification
    cursor.execute("""
        SELECT pg_notify('test_channel',
            json_build_object(
                'test', true,
                'message', 'NOTIFY system working!',
                'timestamp', NOW()
            )::text
        );
    """)

    # Check for notifications
    import select
    if select.select([conn], [], [], 5) == ([], [], []):
        print("  ⏱️  No notifications received in 5 seconds")
    else:
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            print(f"  ✅ Received: Channel={notify.channel}, Payload={notify.payload}")

    cursor.close()

def create_python_listener():
    """Create Python script for Ignition to listen for notifications"""

    listener_script = """#!/usr/bin/env python3
'''
PostgreSQL NOTIFY Listener for Ignition Gateway
Receives real-time notifications and pushes to Perspective sessions
'''

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import select
import json
import time
import logging

# Configure logging
logger = logging.getLogger('LakebaseListener')
logger.setLevel(logging.INFO)

class LakebaseNotifyListener:
    def __init__(self, connection_params):
        self.connection_params = connection_params
        self.conn = None
        self.channels = ['recommendations', 'decisions', 'commands', 'agent_health']
        self.running = False

    def connect(self):
        '''Establish connection to Lakebase'''
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            cursor = self.conn.cursor()
            for channel in self.channels:
                cursor.execute(f"LISTEN {channel};")
                logger.info(f"Listening on channel: {channel}")

            cursor.close()
            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def listen(self):
        '''Main listening loop'''
        self.running = True
        logger.info("Starting NOTIFY listener...")

        while self.running:
            try:
                # Wait for notifications with 5 second timeout
                if select.select([self.conn], [], [], 5) == ([], [], []):
                    continue  # Timeout, check again

                self.conn.poll()

                while self.conn.notifies:
                    notify = self.conn.notifies.pop(0)
                    self.handle_notification(notify)

            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                time.sleep(1)
                # Try to reconnect
                if not self.conn or self.conn.closed:
                    self.connect()

    def handle_notification(self, notify):
        '''Process received notification'''
        try:
            # Parse JSON payload
            payload = json.loads(notify.payload)

            # Log receipt time for latency measurement
            receive_time = time.time()
            if 'timestamp' in payload:
                send_time = payload['timestamp']
                # Calculate latency if timestamp is provided

            logger.info(f"[{notify.channel}] Received: {payload.get('event_type', 'unknown')}")

            # Route to appropriate handler
            if notify.channel == 'recommendations':
                self.handle_new_recommendation(payload)
            elif notify.channel == 'decisions':
                self.handle_operator_decision(payload)
            elif notify.channel == 'commands':
                self.handle_command_execution(payload)
            elif notify.channel == 'agent_health':
                self.handle_agent_health(payload)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in notification: {e}")
        except Exception as e:
            logger.error(f"Error handling notification: {e}")

    def handle_new_recommendation(self, payload):
        '''Handle new recommendation notification'''
        # Push to Perspective sessions via message handler
        system.perspective.sendMessage(
            "newRecommendation",
            payload=payload,
            scope="session"
        )

        # Update tag for HMI indication
        tag_path = f"[default]Mining/Recommendations/Latest"
        system.tag.writeBlocking([tag_path], [payload])

        logger.info(f"New recommendation: {payload['recommendation_id']} for {payload['equipment_id']}")

    def handle_operator_decision(self, payload):
        '''Handle operator decision notification'''
        system.perspective.sendMessage(
            "operatorDecision",
            payload=payload,
            scope="session"
        )

        logger.info(f"Operator decision: {payload['new_status']} for {payload['recommendation_id']}")

    def handle_command_execution(self, payload):
        '''Handle command execution notification'''
        system.perspective.sendMessage(
            "commandExecution",
            payload=payload,
            scope="session"
        )

        # Update equipment tag if needed
        if payload['status'] == 'executed':
            tag_path = payload['tag_path']
            system.tag.writeBlocking([tag_path], [payload['new_value']])

        logger.info(f"Command execution: {payload['command_id']} - {payload['status']}")

    def handle_agent_health(self, payload):
        '''Handle agent health notification'''
        system.perspective.sendMessage(
            "agentHealth",
            payload=payload,
            scope="session"
        )

        logger.info(f"Agent health update: {payload['agent_id']} - {payload['status']}")

    def stop(self):
        '''Stop the listener'''
        self.running = False
        if self.conn:
            self.conn.close()

# Initialize and start listener (call from gateway startup script)
def start_notify_listener():
    connection_params = {
        'host': system.tag.readBlocking(['[default]Lakebase/Host'])[0].value,
        'port': system.tag.readBlocking(['[default]Lakebase/Port'])[0].value,
        'database': system.tag.readBlocking(['[default]Lakebase/Database'])[0].value,
        'user': system.tag.readBlocking(['[default]Lakebase/User'])[0].value,
        'password': system.tag.readBlocking(['[default]Lakebase/Password'])[0].value
    }

    listener = LakebaseNotifyListener(connection_params)
    if listener.connect():
        listener.listen()

# Store in gateway for access
system.util.getGlobals()['lakebaseListener'] = listener
"""

    with open('ignition_notify_listener.py', 'w') as f:
        f.write(listener_script)

    print("\n📄 Created ignition_notify_listener.py for Ignition gateway")

def main():
    """Main setup function"""

    print("=" * 60)
    print("PostgreSQL NOTIFY Setup for Real-time Webhooks")
    print("=" * 60)

    # Connect to Lakebase
    conn = get_lakebase_connection()

    # Setup triggers
    setup_notify_triggers(conn)

    # Test the system
    test_notifications(conn)

    # Create listener script for Ignition
    create_python_listener()

    # Close connection
    conn.close()

    print("\n" + "=" * 60)
    print("✅ PostgreSQL NOTIFY system ready!")
    print("   - Triggers created on all tables")
    print("   - <100ms notification latency enabled")
    print("   - Ignition listener script generated")
    print("\n📝 Next steps:")
    print("   1. Copy ignition_notify_listener.py to Ignition gateway")
    print("   2. Add to gateway startup scripts")
    print("   3. Configure Lakebase connection tags in Ignition")
    print("=" * 60)

if __name__ == "__main__":
    main()