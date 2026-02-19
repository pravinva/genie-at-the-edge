#!/usr/bin/env python3
"""
End-to-end integration test for Agentic HMI
Workstream 13.1: E2E Integration Test
"""

import os
import sys
import uuid
import time
from datetime import datetime
from databricks import sql
from databricks.sdk import WorkspaceClient
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTest:
    """Test complete agent workflow"""

    def __init__(self):
        self.w = WorkspaceClient()
        self.test_equipment = f"TEST_REACTOR_{uuid.uuid4().hex[:8]}"
        self.results = []

        # Connect to database
        server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME", self.w.config.host)
        http_path = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/agentic_hmi")
        access_token = os.getenv("DATABRICKS_TOKEN", self.w.config.token)

        self.conn = sql.connect(
            server_hostname=server_hostname,
            http_path=http_path,
            access_token=access_token
        )
        self.cursor = self.conn.cursor()
        self.cursor.execute("USE agentic_hmi")

    def run_test(self):
        """Execute complete integration test"""
        logger.info("🧪 Starting End-to-End Integration Test")
        logger.info(f"Test equipment: {self.test_equipment}")

        # Step 1: Insert anomaly
        if self.test_insert_anomaly():
            self.results.append(("Insert Anomaly", "PASS"))
        else:
            self.results.append(("Insert Anomaly", "FAIL"))
            return False

        # Step 2: Wait for agent detection
        time.sleep(15)

        # Step 3: Verify recommendation created
        rec_id = self.test_verify_recommendation()
        if rec_id:
            self.results.append(("Verify Recommendation", "PASS"))
        else:
            self.results.append(("Verify Recommendation", "FAIL"))
            return False

        # Step 4: Approve recommendation
        if self.test_approve_recommendation(rec_id):
            self.results.append(("Approve Recommendation", "PASS"))
        else:
            self.results.append(("Approve Recommendation", "FAIL"))
            return False

        # Step 5: Wait for agent to process
        time.sleep(15)

        # Step 6: Verify command created
        cmd_id = self.test_verify_command(rec_id)
        if cmd_id:
            self.results.append(("Verify Command", "PASS"))
        else:
            self.results.append(("Verify Command", "FAIL"))
            return False

        # Step 7: Verify command execution
        if self.test_verify_execution(cmd_id):
            self.results.append(("Verify Execution", "PASS"))
        else:
            self.results.append(("Verify Execution", "FAIL"))
            return False

        # Cleanup
        self.cleanup()

        # Print results
        self.print_results()
        return True

    def test_insert_anomaly(self) -> bool:
        """Insert test anomaly into sensor_data"""
        try:
            logger.info("📝 Step 1: Inserting test anomaly...")

            self.cursor.execute("""
                INSERT INTO sensor_data (
                    reading_id,
                    equipment_id,
                    sensor_type,
                    sensor_value,
                    units,
                    quality
                ) VALUES (?, ?, 'temperature', 95.0, '°C', 'good')
            """, (str(uuid.uuid4()), self.test_equipment))

            self.conn.commit()
            logger.info(f"  ✅ Inserted temperature: 95°C for {self.test_equipment}")
            return True

        except Exception as e:
            logger.error(f"  ❌ Failed to insert anomaly: {e}")
            return False

    def test_verify_recommendation(self) -> Optional[str]:
        """Verify agent created recommendation"""
        try:
            logger.info("🔍 Step 3: Verifying recommendation creation...")

            self.cursor.execute("""
                SELECT recommendation_id, issue_type, severity, confidence_score
                FROM agent_recommendations
                WHERE equipment_id = ?
                    AND status = 'pending'
                    AND created_timestamp > CURRENT_TIMESTAMP - INTERVAL 1 MINUTE
                ORDER BY created_timestamp DESC
                LIMIT 1
            """, (self.test_equipment,))

            result = self.cursor.fetchone()
            if result:
                rec_id = result[0]
                logger.info(f"  ✅ Found recommendation: {rec_id[:8]}")
                logger.info(f"     Issue: {result[1]}, Severity: {result[2]}, Confidence: {result[3]:.2f}")
                return rec_id
            else:
                logger.error("  ❌ No recommendation found")
                return None

        except Exception as e:
            logger.error(f"  ❌ Error verifying recommendation: {e}")
            return None

    def test_approve_recommendation(self, rec_id: str) -> bool:
        """Approve the recommendation"""
        try:
            logger.info("✅ Step 4: Approving recommendation...")

            self.cursor.execute("""
                UPDATE agent_recommendations
                SET status = 'approved',
                    operator_id = 'test_operator',
                    approved_timestamp = CURRENT_TIMESTAMP,
                    operator_notes = 'Approved by integration test'
                WHERE recommendation_id = ?
            """, (rec_id,))

            self.conn.commit()
            logger.info(f"  ✅ Approved recommendation: {rec_id[:8]}")
            return True

        except Exception as e:
            logger.error(f"  ❌ Failed to approve recommendation: {e}")
            return False

    def test_verify_command(self, rec_id: str) -> Optional[str]:
        """Verify command was created"""
        try:
            logger.info("⚙️ Step 6: Verifying command creation...")

            self.cursor.execute("""
                SELECT command_id, tag_path, new_value, status
                FROM agent_commands
                WHERE recommendation_id = ?
                ORDER BY created_timestamp DESC
                LIMIT 1
            """, (rec_id,))

            result = self.cursor.fetchone()
            if result:
                cmd_id = result[0]
                logger.info(f"  ✅ Found command: {cmd_id[:8]}")
                logger.info(f"     Tag: {result[1]}, Value: {result[2]}, Status: {result[3]}")
                return cmd_id
            else:
                logger.error("  ❌ No command found")
                return None

        except Exception as e:
            logger.error(f"  ❌ Error verifying command: {e}")
            return None

    def test_verify_execution(self, cmd_id: str) -> bool:
        """Verify command was executed"""
        try:
            logger.info("⚡ Step 7: Verifying command execution...")

            # Wait for execution
            max_attempts = 10
            for attempt in range(max_attempts):
                self.cursor.execute("""
                    SELECT status, execution_result, execution_timestamp
                    FROM agent_commands
                    WHERE command_id = ?
                """, (cmd_id,))

                result = self.cursor.fetchone()
                if result and result[0] == 'executed':
                    logger.info(f"  ✅ Command executed successfully")
                    logger.info(f"     Result: {result[1]}")
                    return True
                elif result and result[0] == 'failed':
                    logger.error(f"  ❌ Command failed: {result[1]}")
                    return False

                time.sleep(2)

            logger.error("  ❌ Command not executed within timeout")
            return False

        except Exception as e:
            logger.error(f"  ❌ Error verifying execution: {e}")
            return False

    def cleanup(self):
        """Clean up test data"""
        try:
            logger.info("🧹 Cleaning up test data...")

            # Delete test sensor data
            self.cursor.execute("""
                DELETE FROM sensor_data
                WHERE equipment_id = ?
            """, (self.test_equipment,))

            # Delete test recommendations
            self.cursor.execute("""
                DELETE FROM agent_recommendations
                WHERE equipment_id = ?
            """, (self.test_equipment,))

            # Delete test commands
            self.cursor.execute("""
                DELETE FROM agent_commands
                WHERE equipment_id = ?
            """, (self.test_equipment,))

            self.conn.commit()
            logger.info("  ✅ Test data cleaned up")

        except Exception as e:
            logger.error(f"  ⚠️ Cleanup warning: {e}")

    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)

        passed = 0
        failed = 0

        for step, result in self.results:
            icon = "✅" if result == "PASS" else "❌"
            print(f"{icon} {step}: {result}")
            if result == "PASS":
                passed += 1
            else:
                failed += 1

        print("-"*60)
        print(f"Total: {passed} PASSED, {failed} FAILED")

        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Integration successful.")
        else:
            print(f"\n⚠️ {failed} tests failed. Please review.")

        print("="*60)

def main():
    """Run integration test"""
    test = IntegrationTest()

    try:
        success = test.run_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
        test.cleanup()
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        test.cleanup()
        sys.exit(1)
    finally:
        if hasattr(test, 'conn'):
            test.conn.close()

if __name__ == "__main__":
    main()