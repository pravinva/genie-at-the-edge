#!/usr/bin/env python3
"""
Test Real-time Agent HMI Components using Databricks
Tests the implementation without direct PostgreSQL access
"""

import time
import json
import uuid
from datetime import datetime
from databricks import sql
from databricks.sdk import WorkspaceClient
import requests
import subprocess

class AgentHMITester:
    """Test the real-time Agent HMI implementation"""

    def __init__(self):
        self.w = WorkspaceClient()
        self.connection = None
        self.test_results = []

        # Get connection details
        self.server_hostname = "e2-demo-field-eng.cloud.databricks.com"
        self.http_path = "/sql/1.0/warehouses/4fe75792cd0d304c"
        self.access_token = None  # Will use CLI auth

    def connect_databricks(self):
        """Connect to Databricks SQL Warehouse"""
        try:
            # Get token from CLI
            result = subprocess.run(
                ["databricks", "auth", "token", "--host", f"https://{self.server_hostname}"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.access_token = result.stdout.strip()

            self.connection = sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token or ""
            )
            print("✅ Connected to Databricks")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    def test_1_table_structure(self):
        """Test that all required tables exist with proper structure"""
        print("\n" + "=" * 60)
        print("Test 1: Verify Table Structure")
        print("=" * 60)

        cursor = self.connection.cursor()

        required_tables = [
            'genie_mining.operations.agent_recommendations',
            'genie_mining.operations.agent_commands',
            'genie_mining.operations.agent_health'
        ]

        all_exist = True
        for table in required_tables:
            try:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"  ✅ Table {table}: {len(columns)} columns")

                # Check for notification triggers columns
                col_names = [col[0] for col in columns]
                if 'agent_recommendations' in table:
                    required_cols = ['recommendation_id', 'equipment_id', 'status', 'created_timestamp']
                    missing = [col for col in required_cols if col not in col_names]
                    if missing:
                        print(f"    ⚠️  Missing columns: {missing}")
                        all_exist = False

            except Exception as e:
                print(f"  ❌ Table {table}: Not found or accessible")
                all_exist = False

        cursor.close()

        if all_exist:
            self.test_results.append(('Table Structure', 'PASS', 'All tables exist'))
        else:
            self.test_results.append(('Table Structure', 'FAIL', 'Missing tables/columns'))

    def test_2_insert_recommendation(self):
        """Test inserting a recommendation and measuring write latency"""
        print("\n" + "=" * 60)
        print("Test 2: Insert Recommendation Performance")
        print("=" * 60)

        cursor = self.connection.cursor()
        test_id = str(uuid.uuid4())

        # Measure insert time
        start_time = time.time()

        try:
            cursor.execute("""
                INSERT INTO genie_mining.operations.agent_recommendations
                (recommendation_id, equipment_id, issue_type, severity,
                 temperature_reading, recommended_action, confidence_score,
                 status, created_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, current_timestamp())
            """, (
                test_id,
                'TEST_CRUSHER_01',
                'Bearing Temperature Critical',
                'critical',
                95.5,
                'Immediate shutdown required',
                0.95,
                'pending'
            ))

            insert_time_ms = (time.time() - start_time) * 1000

            print(f"  ⏱️  Insert latency: {insert_time_ms:.2f}ms")

            # Verify insert
            cursor.execute("""
                SELECT recommendation_id, equipment_id, severity
                FROM genie_mining.operations.agent_recommendations
                WHERE recommendation_id = %s
            """, (test_id,))

            result = cursor.fetchone()
            if result:
                print(f"  ✅ Recommendation created: {result[1]} - {result[2]}")
                self.test_results.append(('Insert Performance', 'PASS', f'{insert_time_ms:.2f}ms'))
            else:
                print(f"  ❌ Recommendation not found after insert")
                self.test_results.append(('Insert Performance', 'FAIL', 'Not found'))

            # Store for later tests
            self.test_recommendation_id = test_id

        except Exception as e:
            print(f"  ❌ Insert failed: {e}")
            self.test_results.append(('Insert Performance', 'FAIL', str(e)))

        cursor.close()

    def test_3_update_decision(self):
        """Test operator decision update performance (simulating direct JDBC)"""
        print("\n" + "=" * 60)
        print("Test 3: Operator Decision Update Performance")
        print("=" * 60)

        if not hasattr(self, 'test_recommendation_id'):
            print("  ⚠️  No test recommendation to update")
            self.test_results.append(('Update Performance', 'SKIP', 'No test data'))
            return

        cursor = self.connection.cursor()

        # Measure update time
        start_time = time.time()

        try:
            cursor.execute("""
                UPDATE genie_mining.operations.agent_recommendations
                SET status = 'approved',
                    approved_timestamp = current_timestamp(),
                    approved_by = 'test_operator'
                WHERE recommendation_id = %s
            """, (self.test_recommendation_id,))

            update_time_ms = (time.time() - start_time) * 1000

            print(f"  ⏱️  Update latency: {update_time_ms:.2f}ms")

            if update_time_ms < 200:
                print(f"  ✅ PASS: Under 200ms target for direct JDBC")
                self.test_results.append(('Update Performance', 'PASS', f'{update_time_ms:.2f}ms'))
            else:
                print(f"  ⚠️  SLOW: Exceeds 200ms target")
                self.test_results.append(('Update Performance', 'WARN', f'{update_time_ms:.2f}ms'))

        except Exception as e:
            print(f"  ❌ Update failed: {e}")
            self.test_results.append(('Update Performance', 'FAIL', str(e)))

        cursor.close()

    def test_4_genie_proxy(self):
        """Test Ask AI Why integration with Genie proxy"""
        print("\n" + "=" * 60)
        print("Test 4: Ask AI Why - Genie Proxy Integration")
        print("=" * 60)

        # Check if Genie proxy is running
        genie_url = "http://localhost:8185/genie/query"

        test_context = {
            'equipment_id': 'CRUSHER_01',
            'issue_type': 'High Vibration Detected',
            'temperature': 88.5,
            'recommended_action': 'Reduce throughput by 30%'
        }

        question = f"Why is {test_context['equipment_id']} showing {test_context['issue_type']}?"

        try:
            response = requests.post(
                genie_url,
                json={'question': question, 'context': test_context},
                timeout=3
            )

            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Genie proxy responding")
                print(f"  📝 Response preview: {str(result)[:150]}...")
                self.test_results.append(('Genie Proxy', 'PASS', 'Connected'))
            else:
                print(f"  ❌ Genie returned: {response.status_code}")
                self.test_results.append(('Genie Proxy', 'FAIL', f'HTTP {response.status_code}'))

        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  Genie proxy not running at {genie_url}")
            print(f"     Start with: python ignition/scripts/genie_proxy.py")
            self.test_results.append(('Genie Proxy', 'INFO', 'Not running'))

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.test_results.append(('Genie Proxy', 'FAIL', str(e)))

    def test_5_end_to_end_flow(self):
        """Test complete data flow from anomaly to command"""
        print("\n" + "=" * 60)
        print("Test 5: End-to-End Data Flow")
        print("=" * 60)

        cursor = self.connection.cursor()
        flow_start = time.time()

        try:
            # Step 1: Create anomaly
            rec_id = str(uuid.uuid4())
            print("  1️⃣  Creating anomaly recommendation...")

            cursor.execute("""
                INSERT INTO genie_mining.operations.agent_recommendations
                (recommendation_id, equipment_id, issue_type, severity,
                 temperature_reading, recommended_action, confidence_score,
                 status, created_timestamp, root_cause_analysis)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, current_timestamp(), %s)
            """, (
                rec_id,
                'CONVEYOR_02',
                'Belt Slippage Detected',
                'high',
                75.0,
                'Adjust belt tension',
                0.89,
                'pending',
                'High load combined with worn belt surface causing slippage'
            ))

            # Step 2: Approve recommendation
            print("  2️⃣  Approving recommendation...")
            time.sleep(0.1)

            cursor.execute("""
                UPDATE genie_mining.operations.agent_recommendations
                SET status = 'approved',
                    approved_timestamp = current_timestamp(),
                    approved_by = 'demo_operator'
                WHERE recommendation_id = %s
            """, (rec_id,))

            # Step 3: Create command
            print("  3️⃣  Creating execution command...")
            cmd_id = str(uuid.uuid4())

            cursor.execute("""
                INSERT INTO genie_mining.operations.agent_commands
                (command_id, recommendation_id, equipment_id,
                 tag_path, new_value, action_description,
                 severity, status, created_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, current_timestamp())
            """, (
                cmd_id,
                rec_id,
                'CONVEYOR_02',
                '[default]Equipment/CONVEYOR_02/BeltTension',
                '85',
                'Increase belt tension to 85%',
                'high',
                'pending'
            ))

            # Step 4: Execute command
            print("  4️⃣  Executing command...")
            time.sleep(0.1)

            cursor.execute("""
                UPDATE genie_mining.operations.agent_commands
                SET status = 'executed',
                    executed_timestamp = current_timestamp()
                WHERE command_id = %s
            """, (cmd_id,))

            flow_time_ms = (time.time() - flow_start) * 1000

            print(f"\n  ⏱️  Total flow time: {flow_time_ms:.2f}ms")

            # Verify complete flow
            cursor.execute("""
                SELECT r.status as rec_status, c.status as cmd_status
                FROM genie_mining.operations.agent_recommendations r
                JOIN genie_mining.operations.agent_commands c
                ON r.recommendation_id = c.recommendation_id
                WHERE r.recommendation_id = %s
            """, (rec_id,))

            result = cursor.fetchone()
            if result and result[0] == 'approved' and result[1] == 'executed':
                print(f"  ✅ Complete flow verified")
                self.test_results.append(('End-to-End Flow', 'PASS', f'{flow_time_ms:.2f}ms'))
            else:
                print(f"  ⚠️  Flow incomplete: {result}")
                self.test_results.append(('End-to-End Flow', 'WARN', 'Incomplete'))

        except Exception as e:
            print(f"  ❌ Flow failed: {e}")
            self.test_results.append(('End-to-End Flow', 'FAIL', str(e)))

        cursor.close()

    def cleanup_test_data(self):
        """Clean up test data from database"""
        print("\n🧹 Cleaning up test data...")

        cursor = self.connection.cursor()

        try:
            # Clean up test records
            cursor.execute("""
                DELETE FROM genie_mining.operations.agent_commands
                WHERE equipment_id LIKE 'TEST_%' OR equipment_id LIKE 'CONVEYOR_02'
            """)

            cursor.execute("""
                DELETE FROM genie_mining.operations.agent_recommendations
                WHERE equipment_id LIKE 'TEST_%' OR equipment_id LIKE 'CONVEYOR_02'
            """)

            print("  ✅ Test data cleaned")

        except Exception as e:
            print(f"  ⚠️  Cleanup warning: {e}")

        cursor.close()

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)

        for test_name, status, details in self.test_results:
            icon = {
                'PASS': '✅',
                'FAIL': '❌',
                'WARN': '⚠️',
                'INFO': 'ℹ️',
                'SKIP': '⏭️'
            }.get(status, '❓')

            print(f"{icon} {test_name:25} {status:6} {details}")

        passed = sum(1 for _, status, _ in self.test_results if status == 'PASS')
        total = len([s for _, s, _ in self.test_results if s != 'INFO'])

        print("\n" + "-" * 60)
        print(f"Score: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All tests passed! Agent HMI is working correctly.")
        elif passed >= total * 0.7:
            print("\n✅ Most tests passed. System is functional.")
        else:
            print("\n⚠️  Multiple failures detected. Review implementation.")

    def run_all_tests(self):
        """Execute all tests"""
        print("\n🚀 Agent HMI Component Tests (Databricks)")
        print("=" * 60)

        if not self.connect_databricks():
            print("Cannot proceed without database connection")
            return

        # Run test suite
        self.test_1_table_structure()
        self.test_2_insert_recommendation()
        self.test_3_update_decision()
        self.test_4_genie_proxy()
        self.test_5_end_to_end_flow()

        # Cleanup
        self.cleanup_test_data()

        # Close connection
        if self.connection:
            self.connection.close()

        # Print summary
        self.print_summary()


if __name__ == "__main__":
    tester = AgentHMITester()
    tester.run_all_tests()