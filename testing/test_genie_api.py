#!/usr/bin/env python3
"""
Genie API Testing Module
Validates Genie query accuracy, latency, and response quality.
"""

import os
import time
import requests
from typing import Dict, Any, List
from datetime import datetime


class GenieAPITests:
    """Test suite for Databricks Genie API validation"""

    def __init__(self):
        self.host = os.getenv("DATABRICKS_HOST")
        self.token = os.getenv("DATABRICKS_TOKEN")
        self.space_id = os.getenv("GENIE_SPACE_ID")
        self.warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")

        if not all([self.host, self.token, self.space_id]):
            raise ValueError("DATABRICKS_HOST, DATABRICKS_TOKEN, and GENIE_SPACE_ID required")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # Test questions from ralph_wiggum_10_testing.md
        self.test_questions = [
            {
                "question": "Show current status of all crushers",
                "expected_keywords": ["CR_001", "CR_002", "CR_003", "crusher"],
                "expected_type": "table"
            },
            {
                "question": "Why is Crusher 2 vibration high?",
                "expected_keywords": ["CR_002", "vibration", "high"],
                "expected_type": "explanation"
            },
            {
                "question": "Compare Crusher 2 to other crushers",
                "expected_keywords": ["CR_001", "CR_002", "CR_003", "compare"],
                "expected_type": "comparison"
            },
            {
                "question": "Show production for last hour",
                "expected_keywords": ["production", "tonnage", "hour"],
                "expected_type": "metric"
            },
            {
                "question": "Which equipment has anomalies?",
                "expected_keywords": ["anomaly", "equipment"],
                "expected_type": "list"
            },
            {
                "question": "Show fuel consumption by haul truck",
                "expected_keywords": ["HT_", "fuel", "consumption"],
                "expected_type": "comparison"
            },
            {
                "question": "What's the efficiency of Haul Truck 3?",
                "expected_keywords": ["HT_003", "efficiency"],
                "expected_type": "metric"
            },
            {
                "question": "How many hours until Crusher 2 needs maintenance?",
                "expected_keywords": ["CR_002", "maintenance", "hours"],
                "expected_type": "prediction"
            },
            {
                "question": "Show me equipment in Pit 2",
                "expected_keywords": ["pit", "equipment"],
                "expected_type": "filter"
            },
            {
                "question": "What is the average vibration across all crushers?",
                "expected_keywords": ["average", "vibration", "crusher"],
                "expected_type": "metric"
            }
        ]

    def _call_genie_api(self, question: str, timeout: int = 30) -> Dict[str, Any]:
        """Call Genie API with a question"""
        url = f"{self.host}/api/2.0/genie/spaces/{self.space_id}/start-conversation"

        payload = {
            "content": question
        }

        try:
            start_time = time.time()
            response = requests.post(url, headers=self.headers, json=payload, timeout=timeout)
            duration = time.time() - start_time

            response.raise_for_status()
            result = response.json()

            return {
                "success": True,
                "response": result,
                "duration": duration,
                "status_code": response.status_code
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout",
                "duration": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time if 'start_time' in locals() else 0
            }

    def test_genie_connectivity(self) -> Dict[str, Any]:
        """Test if Genie API is reachable"""
        url = f"{self.host}/api/2.0/genie/spaces/{self.space_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            return {
                "status": "PASS",
                "message": "Genie API is reachable",
                "details": {"space_id": self.space_id}
            }

        except requests.exceptions.HTTPError as e:
            return {
                "status": "FAIL",
                "message": f"Genie API returned error: {e.response.status_code}",
                "details": {"error": str(e)}
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Cannot reach Genie API: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_genie_space_status(self) -> Dict[str, Any]:
        """Check Genie Space status and configuration"""
        url = f"{self.host}/api/2.0/genie/spaces/{self.space_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            space_info = response.json()

            return {
                "status": "PASS",
                "message": f"Genie Space active: {space_info.get('name', 'Unknown')}",
                "details": space_info
            }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Cannot get Genie Space status: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_simple_query(self) -> Dict[str, Any]:
        """Test a simple Genie query (smoke test)"""
        question = "Show current status of all crushers"

        result = self._call_genie_api(question, timeout=15)

        if result["success"]:
            return {
                "status": "PASS",
                "message": f"Simple query successful ({result['duration']:.2f}s)",
                "details": {
                    "question": question,
                    "duration": result["duration"]
                }
            }
        else:
            return {
                "status": "FAIL",
                "message": f"Simple query failed: {result.get('error')}",
                "details": result
            }

    def test_query_accuracy_10(self) -> Dict[str, Any]:
        """Test accuracy of all 10 predefined questions"""
        passed = 0
        failed = 0
        results_detail = []

        for i, test_case in enumerate(self.test_questions, 1):
            question = test_case["question"]
            expected_keywords = test_case["expected_keywords"]

            result = self._call_genie_api(question, timeout=20)

            if result["success"]:
                # Check if response contains expected keywords
                response_text = str(result["response"]).lower()
                keywords_found = sum(1 for kw in expected_keywords if kw.lower() in response_text)
                keywords_ratio = keywords_found / len(expected_keywords)

                if keywords_ratio >= 0.5:  # At least 50% of keywords present
                    passed += 1
                    test_status = "PASS"
                else:
                    failed += 1
                    test_status = "FAIL"

                results_detail.append({
                    "question": question,
                    "status": test_status,
                    "duration": result["duration"],
                    "keywords_found": keywords_found,
                    "keywords_total": len(expected_keywords)
                })
            else:
                failed += 1
                results_detail.append({
                    "question": question,
                    "status": "FAIL",
                    "error": result.get("error")
                })

        # Pass criteria: 8/10 correct
        if passed >= 8:
            return {
                "status": "PASS",
                "message": f"Query accuracy: {passed}/10 correct",
                "details": {
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": f"{passed/10*100:.0f}%",
                    "results": results_detail
                }
            }
        elif passed >= 7:
            return {
                "status": "WARNING",
                "message": f"Query accuracy borderline: {passed}/10 correct",
                "details": {
                    "passed": passed,
                    "failed": failed,
                    "results": results_detail
                }
            }
        else:
            return {
                "status": "FAIL",
                "message": f"Query accuracy insufficient: {passed}/10 correct",
                "details": {
                    "passed": passed,
                    "failed": failed,
                    "results": results_detail
                }
            }

    def test_query_latency(self) -> Dict[str, Any]:
        """Measure Genie query response time (<5s target)"""
        question = "Show current status of all crushers"
        iterations = 5
        latencies = []

        for _ in range(iterations):
            result = self._call_genie_api(question, timeout=15)
            if result["success"]:
                latencies.append(result["duration"])
            time.sleep(1)  # Small delay between tests

        if not latencies:
            return {
                "status": "FAIL",
                "message": "No successful queries to measure latency",
                "details": {}
            }

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)

        # Target: <5s average
        if avg_latency < 5:
            return {
                "status": "PASS",
                "message": f"Query latency avg={avg_latency:.2f}s (target <5s)",
                "details": {
                    "avg_latency": avg_latency,
                    "min_latency": min_latency,
                    "max_latency": max_latency,
                    "iterations": iterations,
                    "target": 5.0
                }
            }
        elif avg_latency < 8:
            return {
                "status": "WARNING",
                "message": f"Query latency acceptable: avg={avg_latency:.2f}s",
                "details": {
                    "avg_latency": avg_latency,
                    "min_latency": min_latency,
                    "max_latency": max_latency,
                    "target": 5.0
                }
            }
        else:
            return {
                "status": "FAIL",
                "message": f"Query latency too high: avg={avg_latency:.2f}s",
                "details": {
                    "avg_latency": avg_latency,
                    "min_latency": min_latency,
                    "max_latency": max_latency,
                    "target": 5.0
                }
            }

    def test_concurrent_queries(self) -> Dict[str, Any]:
        """Test concurrent query handling (5 simultaneous users)"""
        import concurrent.futures

        question = "Show production for last hour"
        num_concurrent = 5

        def run_query():
            return self._call_genie_api(question, timeout=20)

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(run_query) for _ in range(num_concurrent)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        total_duration = time.time() - start_time

        successful = sum(1 for r in results if r["success"])
        avg_latency = sum(r["duration"] for r in results if r["success"]) / successful if successful > 0 else 0

        # Target: All queries succeed in <10s each
        if successful == num_concurrent and avg_latency < 10:
            return {
                "status": "PASS",
                "message": f"Concurrent queries: {successful}/{num_concurrent} successful, avg {avg_latency:.2f}s",
                "details": {
                    "concurrent_users": num_concurrent,
                    "successful": successful,
                    "avg_latency": avg_latency,
                    "total_duration": total_duration
                }
            }
        elif successful >= num_concurrent * 0.8:
            return {
                "status": "WARNING",
                "message": f"Some concurrent queries failed: {successful}/{num_concurrent} successful",
                "details": {
                    "concurrent_users": num_concurrent,
                    "successful": successful,
                    "avg_latency": avg_latency
                }
            }
        else:
            return {
                "status": "FAIL",
                "message": f"Concurrent queries failed: {successful}/{num_concurrent} successful",
                "details": {
                    "concurrent_users": num_concurrent,
                    "successful": successful
                }
            }

    def test_cold_start_behavior(self) -> Dict[str, Any]:
        """Test SQL Warehouse cold start behavior"""
        # This test is informational - it doesn't fail
        # It measures first query time after warehouse is stopped

        question = "Show current status of all crushers"
        result = self._call_genie_api(question, timeout=120)

        if result["success"]:
            if result["duration"] > 30:
                return {
                    "status": "WARNING",
                    "message": f"Cold start detected: {result['duration']:.2f}s (keep warehouse warm for demo)",
                    "details": {
                        "duration": result["duration"],
                        "recommendation": "Start warehouse before demo to avoid this delay"
                    }
                }
            else:
                return {
                    "status": "PASS",
                    "message": f"Warehouse is warm: {result['duration']:.2f}s",
                    "details": {"duration": result["duration"]}
                }
        else:
            return {
                "status": "WARNING",
                "message": "Could not test cold start behavior",
                "details": result
            }

    def test_alarm_integration(self) -> Dict[str, Any]:
        """Test alarm-to-chat integration (query about specific alarm)"""
        # Simulate alarm pre-filled question
        alarm_question = "Why is Crusher 2 vibration high?"

        result = self._call_genie_api(alarm_question, timeout=15)

        if result["success"]:
            response_text = str(result["response"]).lower()

            # Check if response mentions the specific equipment and issue
            mentions_equipment = "cr_002" in response_text or "crusher 2" in response_text
            mentions_issue = "vibration" in response_text

            if mentions_equipment and mentions_issue:
                return {
                    "status": "PASS",
                    "message": "Alarm integration query successful",
                    "details": {
                        "question": alarm_question,
                        "duration": result["duration"],
                        "mentions_equipment": mentions_equipment,
                        "mentions_issue": mentions_issue
                    }
                }
            else:
                return {
                    "status": "WARNING",
                    "message": "Response doesn't fully address alarm",
                    "details": {
                        "question": alarm_question,
                        "mentions_equipment": mentions_equipment,
                        "mentions_issue": mentions_issue
                    }
                }
        else:
            return {
                "status": "FAIL",
                "message": f"Alarm integration query failed: {result.get('error')}",
                "details": result
            }

    def test_warmup(self) -> Dict[str, Any]:
        """Warm up SQL Warehouse before demo"""
        # Run a simple query to ensure warehouse is started
        question = "SELECT 1"

        result = self._call_genie_api(question, timeout=120)

        if result["success"]:
            return {
                "status": "PASS",
                "message": f"Warehouse warmed up ({result['duration']:.2f}s)",
                "details": {"duration": result["duration"]}
            }
        else:
            return {
                "status": "WARNING",
                "message": "Warmup query failed",
                "details": result
            }


if __name__ == "__main__":
    # Run tests standalone
    tests = GenieAPITests()

    print("Genie API Tests")
    print("=" * 60)

    print("\n1. Genie Connectivity")
    result = tests.test_genie_connectivity()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")

    print("\n2. Simple Query")
    result = tests.test_simple_query()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")

    print("\n3. Query Accuracy (10 questions)")
    result = tests.test_query_accuracy_10()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")

    print("\n4. Query Latency")
    result = tests.test_query_latency()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")

    print("\n5. Alarm Integration")
    result = tests.test_alarm_integration()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")
