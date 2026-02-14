#!/usr/bin/env python3
"""
Load Testing Module
Simulates multiple concurrent users and measures system performance under load.

Usage:
    python load_testing.py --users 10 --duration 300
    python load_testing.py --users 5 --ramp 60 --duration 600
"""

import argparse
import json
import os
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import concurrent.futures
import requests


class LoadTester:
    """Load testing orchestrator for Mining Genie Demo"""

    def __init__(self, genie_space_id: str, databricks_host: str, databricks_token: str):
        self.space_id = genie_space_id
        self.host = databricks_host
        self.token = databricks_token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # Test queries representing typical operator questions
        self.test_queries = [
            "Show current status of all crushers",
            "Why is Crusher 2 vibration high?",
            "Compare Crusher 2 to other crushers",
            "Show production for last hour",
            "Which equipment has anomalies?",
            "What happened on January 15?",
            "Show fuel consumption by haul truck",
            "What's the efficiency of Haul Truck 3?",
            "How many hours until Crusher 2 needs maintenance?",
            "Show me equipment in Pit 2"
        ]

        self.results = []
        self.errors = []

    def _execute_query(self, user_id: int, query: str) -> Dict[str, Any]:
        """Execute a single query and measure performance"""
        url = f"{self.host}/api/2.0/genie/spaces/{self.space_id}/start-conversation"

        payload = {"content": query}

        start_time = time.time()
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            duration = time.time() - start_time

            return {
                "user_id": user_id,
                "query": query,
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            }

        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            return {
                "user_id": user_id,
                "query": query,
                "status": "timeout",
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                "user_id": user_id,
                "query": query,
                "status": "error",
                "error": str(e),
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            }

    def simulate_user(self, user_id: int, duration_seconds: int, think_time: int = 10) -> List[Dict]:
        """Simulate a single user's behavior over time"""
        end_time = time.time() + duration_seconds
        user_results = []

        print(f"User {user_id}: Starting simulation for {duration_seconds}s")

        while time.time() < end_time:
            # Pick random query
            query = random.choice(self.test_queries)

            # Execute query
            result = self._execute_query(user_id, query)
            user_results.append(result)

            # Log result
            if result["status"] == "success":
                print(f"User {user_id}: ✓ Query successful ({result['duration']:.2f}s)")
            else:
                print(f"User {user_id}: ✗ Query {result['status']} ({result['duration']:.2f}s)")

            # Think time (simulate user reading response)
            if time.time() < end_time:
                time.sleep(think_time)

        print(f"User {user_id}: Completed {len(user_results)} queries")
        return user_results

    def run_load_test(self, num_users: int, duration_seconds: int, ramp_time: int = 0) -> Dict[str, Any]:
        """Run load test with specified parameters"""
        print(f"\n{'=' * 60}")
        print(f"LOAD TEST: {num_users} concurrent users, {duration_seconds}s duration")
        if ramp_time > 0:
            print(f"Ramp-up: {ramp_time}s")
        print(f"{'=' * 60}\n")

        start_time = datetime.now()

        # Execute with ramp-up if specified
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = []

            for user_id in range(num_users):
                # Delay user start if ramp-up specified
                if ramp_time > 0:
                    time.sleep(ramp_time / num_users)

                future = executor.submit(self.simulate_user, user_id, duration_seconds)
                futures.append(future)

            # Collect all results
            for future in concurrent.futures.as_completed(futures):
                user_results = future.result()
                self.results.extend(user_results)

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # Calculate statistics
        stats = self._calculate_statistics(total_duration)

        print(f"\n{'=' * 60}")
        print(f"LOAD TEST COMPLETE")
        print(f"{'=' * 60}")
        print(f"Total Queries:    {stats['total_queries']}")
        print(f"Successful:       {stats['successful']} ({stats['success_rate']:.1f}%)")
        print(f"Failed:           {stats['failed']}")
        print(f"Timeouts:         {stats['timeouts']}")
        print(f"Avg Latency:      {stats['avg_latency']:.2f}s")
        print(f"Min Latency:      {stats['min_latency']:.2f}s")
        print(f"Max Latency:      {stats['max_latency']:.2f}s")
        print(f"p50 Latency:      {stats['p50_latency']:.2f}s")
        print(f"p95 Latency:      {stats['p95_latency']:.2f}s")
        print(f"p99 Latency:      {stats['p99_latency']:.2f}s")
        print(f"Throughput:       {stats['throughput_qps']:.2f} queries/sec")
        print(f"{'=' * 60}\n")

        return stats

    def _calculate_statistics(self, total_duration: float) -> Dict[str, Any]:
        """Calculate performance statistics from results"""
        successful = [r for r in self.results if r["status"] == "success"]
        failed = [r for r in self.results if r["status"] == "error"]
        timeouts = [r for r in self.results if r["status"] == "timeout"]

        durations = [r["duration"] for r in successful]
        durations.sort()

        stats = {
            "total_queries": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "timeouts": len(timeouts),
            "success_rate": (len(successful) / len(self.results) * 100) if self.results else 0,
            "total_duration": total_duration,
            "throughput_qps": len(self.results) / total_duration if total_duration > 0 else 0
        }

        if durations:
            stats.update({
                "avg_latency": sum(durations) / len(durations),
                "min_latency": min(durations),
                "max_latency": max(durations),
                "p50_latency": durations[int(len(durations) * 0.50)],
                "p95_latency": durations[int(len(durations) * 0.95)],
                "p99_latency": durations[int(len(durations) * 0.99)]
            })
        else:
            stats.update({
                "avg_latency": 0,
                "min_latency": 0,
                "max_latency": 0,
                "p50_latency": 0,
                "p95_latency": 0,
                "p99_latency": 0
            })

        return stats

    def save_results(self, output_path: Path, stats: Dict[str, Any]):
        """Save load test results to JSON file"""
        report = {
            "test_info": {
                "test_type": "load_test",
                "timestamp": datetime.now().isoformat(),
                "num_users": len(set(r["user_id"] for r in self.results))
            },
            "statistics": stats,
            "detailed_results": self.results
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Load Testing for Mining Genie Demo")
    parser.add_argument("--users", type=int, default=5, help="Number of concurrent users")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--ramp", type=int, default=0, help="Ramp-up time in seconds")
    parser.add_argument("--think-time", type=int, default=10, help="Think time between queries (seconds)")
    parser.add_argument("--output", type=str, help="Output file path")

    args = parser.parse_args()

    # Get environment variables
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    space_id = os.getenv("GENIE_SPACE_ID")

    if not all([host, token, space_id]):
        print("Error: DATABRICKS_HOST, DATABRICKS_TOKEN, and GENIE_SPACE_ID required")
        return 1

    # Create load tester
    tester = LoadTester(space_id, host, token)

    # Run load test
    stats = tester.run_load_test(args.users, args.duration, args.ramp)

    # Save results
    output_dir = Path(__file__).parent / "test_reports"
    output_dir.mkdir(exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"load_test_{args.users}users_{timestamp}.json"

    tester.save_results(output_path, stats)

    # Exit code based on success rate
    if stats["success_rate"] >= 95:
        print("\n✓ Load test PASSED (success rate >= 95%)")
        return 0
    elif stats["success_rate"] >= 80:
        print(f"\n⚠ Load test WARNING (success rate {stats['success_rate']:.1f}%)")
        return 0
    else:
        print(f"\n✗ Load test FAILED (success rate {stats['success_rate']:.1f}%)")
        return 1


if __name__ == "__main__":
    exit(main())
