#!/usr/bin/env python3
"""
End-to-end test for real-time Agent HMI implementation.
Tests all three new components:
1. Ask AI Why button functionality
2. PostgreSQL NOTIFY webhooks (<100ms latency)
3. Direct JDBC write-back (<200ms latency)
"""

import time
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import requests
import uuid
from datetime import datetime
import threading
import select

# Configuration
LAKEBASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'genie_mining',
    'user': 'databricks_user',
    'password': 'your_password'
}

GENIE_PROXY_URL = "http://localhost:8185/genie/query"
IGNITION_URL = "http://localhost:8088"

class RealtimeAgentTester:
    """Test harness for real-time agent HMI features"""

    def __init__(self):
        self.conn = None
        self.notifications_received = []
        self.test_results = []

    def connect_lakebase(self):
        """Connect to Lakebase PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**LAKEBASE_CONFIG)
            print("✅ Connected to Lakebase")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Lakebase: {e}")
            return False

    def test_notify_latency(self):
        """Test PostgreSQL NOTIFY webhook latency"""
        print("\n" + "=" * 60)
        print("Test 1: PostgreSQL NOTIFY Latency (<100ms requirement)")
        print("=" * 60)

        # Set up listener
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = self.conn.cursor()
        cursor.execute("LISTEN recommendations;")

        # Insert test recommendation
        test_id = str(uuid.uuid4())
        insert_time = time.time()

        cursor.execute("""
            INSERT INTO agent_recommendations (
                recommendation_id, equipment_id, issue_type,
                severity, temperature_reading, recommended_action,
                confidence_score, status, created_timestamp
            ) VALUES (
                %s, 'TEST_EQUIP_001', 'High Temperature',
                'critical', 95.5, 'Reduce load immediately',
                0.92, 'pending', CURRENT_TIMESTAMP
            )
        """, (test_id,))

        # Wait for notification
        notification_received = False
        receive_time = None

        if select.select([self.conn], [], [], 1.0)[0]:
            self.conn.poll()
            while self.conn.notifies:
                notify = self.conn.notifies.pop(0)
                receive_time = time.time()
                notification_received = True
                payload = json.loads(notify.payload)
                print(f"  📨 Notification received on channel: {notify.channel}")
                print(f"  📦 Payload: {json.dumps(payload, indent=2)[:200]}...")

        if notification_received:
            latency_ms = (receive_time - insert_time) * 1000
            print(f"  ⏱️  Latency: {latency_ms:.2f}ms")

            if latency_ms < 100:
                print(f"  ✅ PASS: Latency under 100ms requirement")
                self.test_results.append(('NOTIFY Latency', 'PASS', f'{latency_ms:.2f}ms'))
            else:
                print(f"  ⚠️  FAIL: Latency exceeds 100ms requirement")
                self.test_results.append(('NOTIFY Latency', 'FAIL', f'{latency_ms:.2f}ms'))
        else:
            print("  ❌ FAIL: No notification received within 1 second")
            self.test_results.append(('NOTIFY Latency', 'FAIL', 'No notification'))

        # Cleanup
        cursor.execute("DELETE FROM agent_recommendations WHERE recommendation_id = %s", (test_id,))
        cursor.close()

    def test_direct_jdbc_write(self):
        """Test direct JDBC write-back latency"""
        print("\n" + "=" * 60)
        print("Test 2: Direct JDBC Write-back Latency (<200ms requirement)")
        print("=" * 60)

        cursor = self.conn.cursor()

        # Create test recommendation
        test_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO agent_recommendations (
                recommendation_id, equipment_id, issue_type,
                severity, temperature_reading, recommended_action,
                confidence_score, status, created_timestamp
            ) VALUES (
                %s, 'TEST_EQUIP_002', 'Pressure Anomaly',
                'high', 88.0, 'Check valve settings',
                0.85, 'pending', CURRENT_TIMESTAMP
            )
        """, (test_id,))

        # Simulate direct JDBC write (operator decision)
        write_start = time.time()

        cursor.execute("""
            UPDATE agent_recommendations
            SET status = 'approved',
                approved_timestamp = CURRENT_TIMESTAMP,
                approved_by = 'test_operator'
            WHERE recommendation_id = %s
        """, (test_id,))

        write_end = time.time()
        write_latency_ms = (write_end - write_start) * 1000

        print(f"  ⏱️  Write latency: {write_latency_ms:.2f}ms")

        if write_latency_ms < 200:
            print(f"  ✅ PASS: Write latency under 200ms requirement")
            self.test_results.append(('Direct JDBC Write', 'PASS', f'{write_latency_ms:.2f}ms'))
        else:
            print(f"  ⚠️  FAIL: Write latency exceeds 200ms requirement")
            self.test_results.append(('Direct JDBC Write', 'FAIL', f'{write_latency_ms:.2f}ms'))

        # Verify write
        cursor.execute("""
            SELECT status, approved_by, approved_timestamp
            FROM agent_recommendations
            WHERE recommendation_id = %s
        """, (test_id,))

        result = cursor.fetchone()
        if result and result[0] == 'approved':
            print(f"  ✅ Write verified: status={result[0]}, operator={result[1]}")
        else:
            print(f"  ❌ Write verification failed")

        # Cleanup
        cursor.execute("DELETE FROM agent_recommendations WHERE recommendation_id = %s", (test_id,))
        cursor.close()

    def test_ask_ai_why(self):
        """Test Ask AI Why button integration"""
        print("\n" + "=" * 60)
        print("Test 3: Ask AI Why Button Integration")
        print("=" * 60)

        # Test Genie proxy connection
        test_context = {
            'equipment_id': 'CRUSHER_01',
            'issue_type': 'Bearing Temperature High',
            'temperature': 92.5,
            'recommended_action': 'Schedule maintenance within 24 hours'
        }

        question = f"""
        Explain why {test_context['equipment_id']} is showing {test_context['issue_type']}
        with temperature at {test_context['temperature']}°C.
        Why is the recommended action: {test_context['recommended_action']}?
        """

        try:
            # Call Genie proxy
            start_time = time.time()
            response = requests.post(
                GENIE_PROXY_URL,
                json={
                    'question': question,
                    'context': test_context
                },
                timeout=5
            )
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Genie responded in {response_time_ms:.2f}ms")
                print(f"  📝 Answer preview: {result.get('answer', '')[:200]}...")
                self.test_results.append(('Ask AI Why', 'PASS', f'{response_time_ms:.2f}ms'))
            else:
                print(f"  ❌ Genie request failed: {response.status_code}")
                self.test_results.append(('Ask AI Why', 'FAIL', f'HTTP {response.status_code}'))

        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  Genie proxy not running at {GENIE_PROXY_URL}")
            print(f"     Start with: python ignition/scripts/genie_proxy.py")
            self.test_results.append(('Ask AI Why', 'SKIP', 'Proxy not running'))

        except Exception as e:
            print(f"  ❌ Error testing Genie: {e}")
            self.test_results.append(('Ask AI Why', 'FAIL', str(e)))

    def test_end_to_end_flow(self):
        """Test complete end-to-end data flow"""
        print("\n" + "=" * 60)
        print("Test 4: End-to-End Real-time Flow")
        print("=" * 60)

        # Set up notification listener in separate thread
        listener_thread = threading.Thread(target=self.notification_listener)
        listener_thread.daemon = True
        listener_thread.start()

        cursor = self.conn.cursor()
        flow_start = time.time()

        # Step 1: Insert anomaly
        test_id = str(uuid.uuid4())
        print("  1️⃣  Inserting anomaly...")
        cursor.execute("""
            INSERT INTO agent_recommendations (
                recommendation_id, equipment_id, issue_type,
                severity, temperature_reading, recommended_action,
                confidence_score, status, created_timestamp
            ) VALUES (
                %s, 'MILL_03', 'Vibration Anomaly',
                'high', 78.5, 'Inspect bearings',
                0.88, 'pending', CURRENT_TIMESTAMP
            )
        """, (test_id,))

        time.sleep(0.1)  # Wait for notification

        # Step 2: Simulate operator decision
        print("  2️⃣  Operator approving...")
        decision_start = time.time()
        cursor.execute("""
            UPDATE agent_recommendations
            SET status = 'approved',
                approved_timestamp = CURRENT_TIMESTAMP,
                approved_by = 'operator_jane'
            WHERE recommendation_id = %s
        """, (test_id,))
        decision_time = (time.time() - decision_start) * 1000

        time.sleep(0.1)  # Wait for notification

        # Step 3: Create command
        print("  3️⃣  Creating command...")
        command_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO agent_commands (
                command_id, recommendation_id, equipment_id,
                tag_path, new_value, action_description,
                severity, status, created_timestamp
            ) VALUES (
                %s, %s, 'MILL_03',
                '[default]Equipment/MILL_03/Mode', 'MAINTENANCE',
                'Switch to maintenance mode', 'high',
                'executed', CURRENT_TIMESTAMP
            )
        """, (command_id, test_id))

        time.sleep(0.1)  # Wait for notification

        # Calculate total flow time
        flow_time = (time.time() - flow_start) * 1000

        print(f"\n  ⏱️  Total flow time: {flow_time:.2f}ms")
        print(f"  📊 Decision latency: {decision_time:.2f}ms")
        print(f"  📨 Notifications received: {len(self.notifications_received)}")

        if flow_time < 500:  # Reasonable target for complete flow
            print(f"  ✅ PASS: End-to-end flow completed quickly")
            self.test_results.append(('End-to-End Flow', 'PASS', f'{flow_time:.2f}ms'))
        else:
            print(f"  ⚠️  SLOW: Flow took longer than expected")
            self.test_results.append(('End-to-End Flow', 'WARN', f'{flow_time:.2f}ms'))

        # Cleanup
        cursor.execute("DELETE FROM agent_commands WHERE command_id = %s", (command_id,))
        cursor.execute("DELETE FROM agent_recommendations WHERE recommendation_id = %s", (test_id,))
        cursor.close()

    def notification_listener(self):
        """Background thread to listen for notifications"""
        try:
            listen_conn = psycopg2.connect(**LAKEBASE_CONFIG)
            listen_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = listen_conn.cursor()

            # Listen on all channels
            for channel in ['recommendations', 'decisions', 'commands']:
                cursor.execute(f"LISTEN {channel};")

            # Listen for 1 second
            end_time = time.time() + 1.0
            while time.time() < end_time:
                if select.select([listen_conn], [], [], 0.1)[0]:
                    listen_conn.poll()
                    while listen_conn.notifies:
                        notify = listen_conn.notifies.pop(0)
                        self.notifications_received.append({
                            'channel': notify.channel,
                            'payload': notify.payload,
                            'time': time.time()
                        })

            cursor.close()
            listen_conn.close()

        except Exception as e:
            print(f"  ⚠️  Listener error: {e}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        for test_name, status, details in self.test_results:
            icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            print(f"{icon} {test_name:20} {status:6} {details}")

        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        total = len(self.test_results)

        print("\n" + "-" * 60)
        print(f"Results: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All tests passed! Real-time Agent HMI is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Review the implementation.")

    def run_all_tests(self):
        """Run all tests"""
        print("\n🚀 Starting Real-time Agent HMI Tests")
        print("=" * 60)

        if not self.connect_lakebase():
            print("❌ Cannot proceed without database connection")
            return

        # Run individual tests
        self.test_notify_latency()
        self.test_direct_jdbc_write()
        self.test_ask_ai_why()
        self.test_end_to_end_flow()

        # Print summary
        self.print_summary()

        # Cleanup
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    tester = RealtimeAgentTester()
    tester.run_all_tests()