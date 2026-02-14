#!/usr/bin/env python3
"""
Mining Operations Genie Demo - Comprehensive Test Suite
Automated testing framework for all system components.

Usage:
    python test_suite.py --all                    # Run all tests
    python test_suite.py --functional             # Functional tests only
    python test_suite.py --performance            # Performance tests only
    python test_suite.py --stability              # Stability tests (long-running)
    python test_suite.py --smoke                  # Quick smoke test (5 min)
    python test_suite.py --health-check           # System health verification
    python test_suite.py --ci                     # CI/CD mode (non-interactive)
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

# Test imports
try:
    from test_ignition_tags import IgnitionTagTests
    from test_databricks_pipeline import DatabricksPipelineTests
    from test_genie_api import GenieAPITests
    from test_chat_ui import ChatUITests
    from test_integration_e2e import IntegrationE2ETests
except ImportError:
    print("Warning: Some test modules not found. Run with --generate-modules first.")


class TestResult:
    """Container for individual test results"""
    def __init__(self, name: str, status: str, duration: float, message: str = "", details: Dict = None):
        self.name = name
        self.status = status  # PASS, FAIL, SKIP, WARNING
        self.duration = duration
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status,
            "duration": self.duration,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


class TestSuite:
    """Main test suite orchestrator"""

    def __init__(self, output_dir: Path = None, verbose: bool = True):
        self.output_dir = output_dir or Path(__file__).parent / "test_reports"
        self.output_dir.mkdir(exist_ok=True)
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None

    def log(self, message: str, level: str = "INFO"):
        """Print log message if verbose"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")

    def run_test(self, test_func, name: str, category: str) -> TestResult:
        """Execute a single test function and capture result"""
        self.log(f"Running: {name}", "TEST")
        start = time.time()

        try:
            result = test_func()
            duration = time.time() - start

            if result.get("status") == "PASS":
                self.log(f"✓ {name} - PASS ({duration:.2f}s)", "PASS")
                return TestResult(name, "PASS", duration, result.get("message", ""), result.get("details"))
            elif result.get("status") == "WARNING":
                self.log(f"⚠ {name} - WARNING ({duration:.2f}s): {result.get('message')}", "WARN")
                return TestResult(name, "WARNING", duration, result.get("message", ""), result.get("details"))
            else:
                self.log(f"✗ {name} - FAIL ({duration:.2f}s): {result.get('message')}", "FAIL")
                return TestResult(name, "FAIL", duration, result.get("message", ""), result.get("details"))

        except Exception as e:
            duration = time.time() - start
            self.log(f"✗ {name} - ERROR ({duration:.2f}s): {str(e)}", "ERROR")
            return TestResult(name, "FAIL", duration, f"Exception: {str(e)}", {"exception": str(e)})

    def run_functional_tests(self) -> List[TestResult]:
        """Execute all functional validation tests"""
        self.log("=" * 60, "INFO")
        self.log("FUNCTIONAL TESTS", "INFO")
        self.log("=" * 60, "INFO")

        results = []

        # Ignition Tag Tests
        tag_tests = IgnitionTagTests()
        results.append(self.run_test(tag_tests.test_tags_updating, "Ignition Tags Updating", "functional"))
        results.append(self.run_test(tag_tests.test_tag_values_realistic, "Tag Values Realistic", "functional"))
        results.append(self.run_test(tag_tests.test_haul_truck_cycle, "Haul Truck Cycle", "functional"))
        results.append(self.run_test(tag_tests.test_no_invalid_values, "No Invalid Values", "functional"))

        # Databricks Pipeline Tests
        db_tests = DatabricksPipelineTests()
        results.append(self.run_test(db_tests.test_bronze_ingestion, "Bronze Table Ingestion", "functional"))
        results.append(self.run_test(db_tests.test_dlt_processing, "DLT Real-Time Processing", "functional"))
        results.append(self.run_test(db_tests.test_gold_table_quality, "Gold Table Data Quality", "functional"))
        results.append(self.run_test(db_tests.test_all_equipment_present, "All Equipment Present", "functional"))

        # Genie API Tests
        genie_tests = GenieAPITests()
        results.append(self.run_test(genie_tests.test_genie_connectivity, "Genie API Connectivity", "functional"))
        results.append(self.run_test(genie_tests.test_query_accuracy_10, "Genie Query Accuracy (10 questions)", "functional"))
        results.append(self.run_test(genie_tests.test_alarm_integration, "Alarm-to-Chat Integration", "functional"))

        return results

    def run_performance_tests(self) -> List[TestResult]:
        """Execute all performance benchmarking tests"""
        self.log("=" * 60, "INFO")
        self.log("PERFORMANCE TESTS", "INFO")
        self.log("=" * 60, "INFO")

        results = []

        # End-to-end latency
        db_tests = DatabricksPipelineTests()
        results.append(self.run_test(db_tests.test_tag_to_bronze_latency, "Tag → Bronze Latency (<1s)", "performance"))
        results.append(self.run_test(db_tests.test_bronze_to_gold_latency, "Bronze → Gold Latency (<2s)", "performance"))

        # Genie query performance
        genie_tests = GenieAPITests()
        results.append(self.run_test(genie_tests.test_query_latency, "Genie Query Latency (<5s)", "performance"))
        results.append(self.run_test(genie_tests.test_concurrent_queries, "Concurrent Query Load (5 users)", "performance"))
        results.append(self.run_test(genie_tests.test_cold_start_behavior, "SQL Warehouse Cold Start", "performance"))

        # System resource usage
        tag_tests = IgnitionTagTests()
        results.append(self.run_test(tag_tests.test_cpu_memory_usage, "Ignition CPU/Memory Usage", "performance"))

        return results

    def run_stability_tests(self, duration_seconds: int = 86400) -> List[TestResult]:
        """Execute stability and reliability tests (long-running)"""
        self.log("=" * 60, "INFO")
        self.log(f"STABILITY TESTS ({duration_seconds}s = {duration_seconds/3600:.1f}h)", "INFO")
        self.log("=" * 60, "INFO")

        results = []

        # 24-hour soak test (or specified duration)
        integration_tests = IntegrationE2ETests()
        results.append(self.run_test(
            lambda: integration_tests.test_soak_test(duration_seconds),
            f"Soak Test ({duration_seconds/3600:.1f}h)",
            "stability"
        ))

        # Network recovery
        results.append(self.run_test(integration_tests.test_network_recovery, "Network Interruption Recovery", "stability"))

        # Component failure recovery
        results.append(self.run_test(integration_tests.test_gateway_restart_recovery, "Gateway Restart Recovery", "stability"))

        return results

    def run_integration_tests(self) -> List[TestResult]:
        """Execute integration and end-to-end tests"""
        self.log("=" * 60, "INFO")
        self.log("INTEGRATION TESTS", "INFO")
        self.log("=" * 60, "INFO")

        results = []

        integration_tests = IntegrationE2ETests()
        results.append(self.run_test(integration_tests.test_ignition_to_databricks_flow, "Ignition → Databricks Data Flow", "integration"))
        results.append(self.run_test(integration_tests.test_perspective_to_chat, "Perspective → Chat Communication", "integration"))
        results.append(self.run_test(integration_tests.test_realtime_tag_bindings, "Real-Time Tag Bindings", "integration"))
        results.append(self.run_test(integration_tests.test_fault_scenario_e2e, "Fault Scenario End-to-End", "integration"))

        return results

    def run_ui_tests(self) -> List[TestResult]:
        """Execute UI and UX tests"""
        self.log("=" * 60, "INFO")
        self.log("USER INTERFACE TESTS", "INFO")
        self.log("=" * 60, "INFO")

        results = []

        ui_tests = ChatUITests()
        results.append(self.run_test(ui_tests.test_visual_quality, "Visual Quality (Perspective match)", "ui"))
        results.append(self.run_test(ui_tests.test_interaction_smoothness, "Interaction Smoothness (60 FPS)", "ui"))
        results.append(self.run_test(ui_tests.test_accessibility, "Accessibility (Lighthouse >90)", "ui"))
        results.append(self.run_test(ui_tests.test_responsive_design, "Responsive Design", "ui"))

        return results

    def run_smoke_tests(self) -> List[TestResult]:
        """Quick smoke test - verify basic functionality (5 minutes)"""
        self.log("=" * 60, "INFO")
        self.log("SMOKE TESTS (Quick Validation)", "INFO")
        self.log("=" * 60, "INFO")

        results = []

        # Basic connectivity
        tag_tests = IgnitionTagTests()
        results.append(self.run_test(tag_tests.test_gateway_connectivity, "Ignition Gateway Reachable", "smoke"))

        db_tests = DatabricksPipelineTests()
        results.append(self.run_test(db_tests.test_databricks_connectivity, "Databricks Workspace Reachable", "smoke"))
        results.append(self.run_test(db_tests.test_bronze_has_recent_data, "Bronze Table Has Recent Data", "smoke"))

        genie_tests = GenieAPITests()
        results.append(self.run_test(genie_tests.test_genie_connectivity, "Genie API Reachable", "smoke"))
        results.append(self.run_test(genie_tests.test_simple_query, "Simple Genie Query Works", "smoke"))

        ui_tests = ChatUITests()
        results.append(self.run_test(ui_tests.test_chat_ui_loads, "Chat UI Loads Successfully", "smoke"))

        return results

    def run_health_check(self) -> List[TestResult]:
        """System health verification - all components operational"""
        self.log("=" * 60, "INFO")
        self.log("SYSTEM HEALTH CHECK", "INFO")
        self.log("=" * 60, "INFO")

        results = []

        # Check all critical components
        tag_tests = IgnitionTagTests()
        results.append(self.run_test(tag_tests.test_gateway_status, "Ignition Gateway Status", "health"))

        db_tests = DatabricksPipelineTests()
        results.append(self.run_test(db_tests.test_warehouse_status, "SQL Warehouse Status", "health"))
        results.append(self.run_test(db_tests.test_dlt_pipeline_status, "DLT Pipeline Status", "health"))

        genie_tests = GenieAPITests()
        results.append(self.run_test(genie_tests.test_genie_space_status, "Genie Space Status", "health"))

        return results

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARNING")
        skipped = sum(1 for r in self.results if r.status == "SKIP")

        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0

        # Calculate grade
        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        if pass_rate >= 95 and failed == 0:
            grade = "A"
        elif pass_rate >= 85 and failed <= 2:
            grade = "B"
        elif pass_rate >= 70:
            grade = "C"
        else:
            grade = "F"

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "skipped": skipped,
                "pass_rate": f"{pass_rate:.1f}%",
                "grade": grade,
                "duration_seconds": total_duration,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None
            },
            "results": [r.to_dict() for r in self.results],
            "failures": [r.to_dict() for r in self.results if r.status == "FAIL"],
            "warnings": [r.to_dict() for r in self.results if r.status == "WARNING"]
        }

        return report

    def print_summary(self):
        """Print test summary to console"""
        report = self.generate_report()
        summary = report["summary"]

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests:   {summary['total_tests']}")
        print(f"Passed:        {summary['passed']} ✓")
        print(f"Failed:        {summary['failed']} ✗")
        print(f"Warnings:      {summary['warnings']} ⚠")
        print(f"Skipped:       {summary['skipped']} ○")
        print(f"Pass Rate:     {summary['pass_rate']}")
        print(f"Grade:         {summary['grade']}")
        print(f"Duration:      {summary['duration_seconds']:.1f}s")
        print("=" * 60)

        if summary["failed"] > 0:
            print("\nFAILURES:")
            for failure in report["failures"]:
                print(f"  ✗ {failure['name']}: {failure['message']}")

        if summary["warnings"] > 0:
            print("\nWARNINGS:")
            for warning in report["warnings"]:
                print(f"  ⚠ {warning['name']}: {warning['message']}")

        print("\n")

        # Demo readiness assessment
        if summary["grade"] == "A":
            print("✓ SYSTEM IS DEMO-READY")
        elif summary["grade"] == "B":
            print("⚠ SYSTEM IS MOSTLY READY - Review warnings before demo")
        elif summary["grade"] == "C":
            print("⚠ SYSTEM NEEDS WORK - Address failures before demo")
        else:
            print("✗ SYSTEM NOT READY - Major issues must be fixed")

        print("=" * 60 + "\n")

    def save_report(self, filename: Optional[str] = None):
        """Save test report to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_run_{timestamp}.json"

        report_path = self.output_dir / filename
        report = self.generate_report()

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.log(f"Test report saved: {report_path}", "INFO")
        return report_path


def main():
    parser = argparse.ArgumentParser(description="Mining Operations Genie Demo - Test Suite")
    parser.add_argument("--all", action="store_true", help="Run all tests (functional + performance + integration)")
    parser.add_argument("--functional", action="store_true", help="Run functional tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--stability", action="store_true", help="Run stability tests (long-running)")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--ui", action="store_true", help="Run UI tests only")
    parser.add_argument("--smoke", action="store_true", help="Quick smoke test (5 min)")
    parser.add_argument("--health-check", action="store_true", help="System health verification")
    parser.add_argument("--duration", type=int, default=86400, help="Stability test duration (seconds, default 24h)")
    parser.add_argument("--report", action="store_true", help="Generate JSON report")
    parser.add_argument("--ci", action="store_true", help="CI/CD mode (non-interactive, exit code)")
    parser.add_argument("--verbose", action="store_true", default=True, help="Verbose output")

    args = parser.parse_args()

    # Create test suite
    suite = TestSuite(verbose=args.verbose)
    suite.start_time = datetime.now()

    # Determine which tests to run
    if args.smoke:
        suite.results.extend(suite.run_smoke_tests())
    elif args.health_check:
        suite.results.extend(suite.run_health_check())
    elif args.functional:
        suite.results.extend(suite.run_functional_tests())
    elif args.performance:
        suite.results.extend(suite.run_performance_tests())
    elif args.stability:
        suite.results.extend(suite.run_stability_tests(args.duration))
    elif args.integration:
        suite.results.extend(suite.run_integration_tests())
    elif args.ui:
        suite.results.extend(suite.run_ui_tests())
    elif args.all:
        suite.results.extend(suite.run_functional_tests())
        suite.results.extend(suite.run_performance_tests())
        suite.results.extend(suite.run_integration_tests())
        suite.results.extend(suite.run_ui_tests())
    else:
        # Default: run smoke tests
        print("No test category specified. Running smoke tests...")
        suite.results.extend(suite.run_smoke_tests())

    suite.end_time = datetime.now()

    # Print summary
    suite.print_summary()

    # Save report if requested
    if args.report or args.ci:
        suite.save_report()

    # Exit code for CI/CD
    if args.ci:
        failures = sum(1 for r in suite.results if r.status == "FAIL")
        sys.exit(1 if failures > 0 else 0)


if __name__ == "__main__":
    main()
