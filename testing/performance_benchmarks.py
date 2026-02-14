#!/usr/bin/env python3
"""
Performance Benchmarking Module
Comprehensive performance metrics collection and validation.

Usage:
    python performance_benchmarks.py
    python performance_benchmarks.py --output benchmarks_20260215.json
    python performance_benchmarks.py --iterations 10
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import requests
from databricks import sql


class PerformanceBenchmarks:
    """Performance benchmarking suite"""

    def __init__(self):
        self.host = os.getenv("DATABRICKS_HOST")
        self.token = os.getenv("DATABRICKS_TOKEN")
        self.warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
        self.space_id = os.getenv("GENIE_SPACE_ID")
        self.catalog = "field_engineering"
        self.schema = "mining_demo"

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # Performance targets from ralph_wiggum_10_testing.md
        self.targets = {
            "tag_to_bronze_sec": 1.0,
            "bronze_to_gold_sec": 2.0,
            "genie_query_sec": 5.0,
            "end_to_end_sec": 8.0,
            "concurrent_users_sec": 10.0
        }

    def _execute_sql(self, query: str) -> List[tuple]:
        """Execute SQL query"""
        with sql.connect(
            server_hostname=self.host.replace("https://", ""),
            http_path=f"/sql/1.0/warehouses/{self.warehouse_id}",
            access_token=self.token
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()

    def _call_genie(self, question: str, timeout: int = 30) -> Dict:
        """Call Genie API"""
        url = f"{self.host}/api/2.0/genie/spaces/{self.space_id}/start-conversation"
        start_time = time.time()

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json={"content": question},
                timeout=timeout
            )
            duration = time.time() - start_time
            response.raise_for_status()

            return {
                "success": True,
                "duration": duration,
                "status_code": response.status_code
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "duration": duration,
                "error": str(e)
            }

    def benchmark_tag_to_bronze_latency(self, iterations: int = 10) -> Dict[str, Any]:
        """Measure latency from tag update to bronze table"""
        print(f"\nBenchmarking Tag → Bronze latency ({iterations} samples)...")

        query = f"""
        SELECT
            timestampdiff(SECOND, event_timestamp, ingestion_timestamp) as latency_sec
        FROM {self.catalog}.{self.schema}.ot_telemetry_bronze
        WHERE ingestion_timestamp > current_timestamp() - INTERVAL 5 MINUTES
        LIMIT {iterations * 10}
        """

        try:
            results = self._execute_sql(query)
            latencies = [r[0] for r in results if r[0] is not None][:iterations]

            if not latencies:
                return {"error": "No data available"}

            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)

            passed = avg_latency < self.targets["tag_to_bronze_sec"]

            return {
                "metric": "Tag → Bronze Latency",
                "avg_sec": avg_latency,
                "min_sec": min_latency,
                "max_sec": max_latency,
                "target_sec": self.targets["tag_to_bronze_sec"],
                "passed": passed,
                "samples": len(latencies)
            }

        except Exception as e:
            return {"metric": "Tag → Bronze Latency", "error": str(e)}

    def benchmark_bronze_to_gold_latency(self) -> Dict[str, Any]:
        """Measure DLT processing latency"""
        print("\nBenchmarking Bronze → Gold latency...")

        query = f"""
        SELECT
            timestampdiff(SECOND, max(window_start), current_timestamp()) as freshness_sec
        FROM {self.catalog}.{self.schema}.equipment_performance_1min
        """

        try:
            result = self._execute_sql(query)
            latency = result[0][0] if result else None

            if latency is None:
                return {"error": "No data available"}

            passed = latency < self.targets["bronze_to_gold_sec"]

            return {
                "metric": "Bronze → Gold Latency",
                "latency_sec": latency,
                "target_sec": self.targets["bronze_to_gold_sec"],
                "passed": passed
            }

        except Exception as e:
            return {"metric": "Bronze → Gold Latency", "error": str(e)}

    def benchmark_genie_query_latency(self, iterations: int = 5) -> Dict[str, Any]:
        """Measure Genie query response time"""
        print(f"\nBenchmarking Genie query latency ({iterations} iterations)...")

        test_question = "Show current status of all crushers"
        latencies = []

        for i in range(iterations):
            result = self._call_genie(test_question)
            if result["success"]:
                latencies.append(result["duration"])
            time.sleep(2)  # Small delay between tests

        if not latencies:
            return {"error": "No successful queries"}

        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        passed = avg_latency < self.targets["genie_query_sec"]

        return {
            "metric": "Genie Query Latency",
            "avg_sec": avg_latency,
            "min_sec": min_latency,
            "max_sec": max_latency,
            "target_sec": self.targets["genie_query_sec"],
            "passed": passed,
            "iterations": len(latencies)
        }

    def benchmark_end_to_end_latency(self) -> Dict[str, Any]:
        """Measure complete end-to-end latency"""
        print("\nBenchmarking end-to-end latency...")

        # Sum of component latencies
        tag_to_bronze = self.benchmark_tag_to_bronze_latency(iterations=1)
        bronze_to_gold = self.benchmark_bronze_to_gold_latency()
        genie_query = self.benchmark_genie_query_latency(iterations=1)

        if any("error" in b for b in [tag_to_bronze, bronze_to_gold, genie_query]):
            return {"error": "Component benchmark failed"}

        total_latency = (
            tag_to_bronze.get("avg_sec", 0) +
            bronze_to_gold.get("latency_sec", 0) +
            genie_query.get("avg_sec", 0)
        )

        passed = total_latency < self.targets["end_to_end_sec"]

        return {
            "metric": "End-to-End Latency",
            "total_sec": total_latency,
            "components": {
                "tag_to_bronze": tag_to_bronze.get("avg_sec", 0),
                "bronze_to_gold": bronze_to_gold.get("latency_sec", 0),
                "genie_query": genie_query.get("avg_sec", 0)
            },
            "target_sec": self.targets["end_to_end_sec"],
            "passed": passed
        }

    def benchmark_data_throughput(self) -> Dict[str, Any]:
        """Measure data ingestion throughput"""
        print("\nBenchmarking data throughput...")

        query = f"""
        SELECT
            count(*) as record_count,
            count(DISTINCT equipment_id) as equipment_count
        FROM {self.catalog}.{self.schema}.ot_telemetry_bronze
        WHERE ingestion_timestamp > current_timestamp() - INTERVAL 1 MINUTE
        """

        try:
            result = self._execute_sql(query)
            record_count, equipment_count = result[0]

            # Expected: ~60 records/min per equipment × 15 equipment = 900 records/min
            expected_records_per_min = 900
            throughput_ratio = record_count / expected_records_per_min

            passed = throughput_ratio >= 0.8  # 80% of expected

            return {
                "metric": "Data Throughput",
                "records_per_minute": record_count,
                "equipment_count": equipment_count,
                "expected_records_per_minute": expected_records_per_min,
                "throughput_ratio": throughput_ratio,
                "passed": passed
            }

        except Exception as e:
            return {"metric": "Data Throughput", "error": str(e)}

    def run_all_benchmarks(self, iterations: int = 5) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        print("=" * 60)
        print("PERFORMANCE BENCHMARKS")
        print("=" * 60)

        benchmarks = {}

        # Run each benchmark
        benchmarks["tag_to_bronze"] = self.benchmark_tag_to_bronze_latency(iterations)
        benchmarks["bronze_to_gold"] = self.benchmark_bronze_to_gold_latency()
        benchmarks["genie_query"] = self.benchmark_genie_query_latency(iterations)
        benchmarks["end_to_end"] = self.benchmark_end_to_end_latency()
        benchmarks["throughput"] = self.benchmark_data_throughput()

        # Calculate overall status
        passed_count = sum(1 for b in benchmarks.values() if b.get("passed", False))
        total_count = len([b for b in benchmarks.values() if "passed" in b])

        overall_status = {
            "passed": passed_count,
            "total": total_count,
            "pass_rate": (passed_count / total_count * 100) if total_count > 0 else 0
        }

        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)

        for name, result in benchmarks.items():
            if "error" in result:
                print(f"{name}: ERROR - {result['error']}")
            elif "passed" in result:
                status = "✓ PASS" if result["passed"] else "✗ FAIL"
                metric = result.get("metric", name)
                if "avg_sec" in result:
                    print(f"{metric}: {status} (avg={result['avg_sec']:.2f}s, target={result['target_sec']:.2f}s)")
                elif "latency_sec" in result:
                    print(f"{metric}: {status} (latency={result['latency_sec']:.2f}s, target={result['target_sec']:.2f}s)")
                elif "total_sec" in result:
                    print(f"{metric}: {status} (total={result['total_sec']:.2f}s, target={result['target_sec']:.2f}s)")
                else:
                    print(f"{metric}: {status}")

        print(f"\nOverall: {passed_count}/{total_count} benchmarks passed ({overall_status['pass_rate']:.0f}%)")
        print("=" * 60 + "\n")

        return {
            "timestamp": datetime.now().isoformat(),
            "targets": self.targets,
            "benchmarks": benchmarks,
            "overall": overall_status
        }


def main():
    parser = argparse.ArgumentParser(description="Performance Benchmarks for Mining Genie Demo")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations per benchmark")
    parser.add_argument("--output", type=str, help="Output file path")

    args = parser.parse_args()

    # Create benchmark runner
    benchmarks = PerformanceBenchmarks()

    # Run benchmarks
    results = benchmarks.run_all_benchmarks(args.iterations)

    # Save results
    output_dir = Path(__file__).parent / "test_reports"
    output_dir.mkdir(exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d")
        output_path = output_dir / f"benchmark_{timestamp}.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Benchmark results saved to: {output_path}")

    # Exit code based on pass rate
    pass_rate = results["overall"]["pass_rate"]
    if pass_rate >= 80:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
