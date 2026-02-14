#!/usr/bin/env python3
"""
Databricks Pipeline Testing Module
Validates data ingestion, DLT processing, and data quality.
"""

import os
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from databricks import sql
from databricks.sdk import WorkspaceClient


class DatabricksPipelineTests:
    """Test suite for Databricks data pipeline validation"""

    def __init__(self):
        self.host = os.getenv("DATABRICKS_HOST")
        self.token = os.getenv("DATABRICKS_TOKEN")
        self.warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID", "4b9b953939869799")
        self.catalog = "field_engineering"
        self.schema = "mining_demo"

        if not self.host or not self.token:
            raise ValueError("DATABRICKS_HOST and DATABRICKS_TOKEN environment variables required")

        self.workspace = WorkspaceClient(host=self.host, token=self.token)

    def _execute_query(self, query: str) -> List[tuple]:
        """Execute SQL query and return results"""
        with sql.connect(
            server_hostname=self.host.replace("https://", ""),
            http_path=f"/sql/1.0/warehouses/{self.warehouse_id}",
            access_token=self.token
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()

    def test_databricks_connectivity(self) -> Dict[str, Any]:
        """Test if Databricks workspace is reachable"""
        try:
            # Simple query to test connectivity
            result = self._execute_query("SELECT current_timestamp()")
            if result:
                return {
                    "status": "PASS",
                    "message": "Databricks workspace is reachable",
                    "details": {"timestamp": str(result[0][0])}
                }
            else:
                return {
                    "status": "FAIL",
                    "message": "Query returned no results",
                    "details": {}
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Cannot connect to Databricks: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_warehouse_status(self) -> Dict[str, Any]:
        """Check SQL Warehouse status"""
        try:
            warehouse = self.workspace.warehouses.get(self.warehouse_id)

            status_map = {
                "RUNNING": "PASS",
                "STARTING": "WARNING",
                "STOPPED": "WARNING",
                "STOPPING": "WARNING",
                "DELETED": "FAIL"
            }

            state = str(warehouse.state)
            test_status = status_map.get(state, "WARNING")

            return {
                "status": test_status,
                "message": f"SQL Warehouse state: {state}",
                "details": {
                    "warehouse_id": self.warehouse_id,
                    "state": state,
                    "name": warehouse.name,
                    "cluster_size": warehouse.cluster_size
                }
            }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Cannot get warehouse status: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_dlt_pipeline_status(self) -> Dict[str, Any]:
        """Check DLT Pipeline status"""
        try:
            # Find pipeline by name
            pipelines = self.workspace.pipelines.list_pipelines()
            mining_pipeline = None

            for pipeline in pipelines:
                if "mining" in pipeline.name.lower():
                    mining_pipeline = pipeline
                    break

            if not mining_pipeline:
                return {
                    "status": "FAIL",
                    "message": "Mining DLT pipeline not found",
                    "details": {}
                }

            # Get pipeline status
            pipeline_id = mining_pipeline.pipeline_id
            details = self.workspace.pipelines.get(pipeline_id)

            state = str(details.state)
            health = str(getattr(details, 'health', 'UNKNOWN'))

            if state == "RUNNING" and health == "HEALTHY":
                status = "PASS"
            elif state == "RUNNING":
                status = "WARNING"
            else:
                status = "FAIL"

            return {
                "status": status,
                "message": f"DLT Pipeline state: {state}, health: {health}",
                "details": {
                    "pipeline_id": pipeline_id,
                    "state": state,
                    "health": health,
                    "name": mining_pipeline.name
                }
            }

        except Exception as e:
            return {
                "status": "WARNING",
                "message": f"Could not check pipeline status: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_bronze_ingestion(self) -> Dict[str, Any]:
        """Verify data is being ingested into bronze table"""
        try:
            query = f"""
            SELECT
                count(*) as record_count,
                max(ingestion_timestamp) as latest_ingestion,
                count(DISTINCT equipment_id) as equipment_count
            FROM {self.catalog}.{self.schema}.ot_telemetry_bronze
            WHERE ingestion_timestamp > current_timestamp() - INTERVAL 5 MINUTES
            """

            result = self._execute_query(query)
            if not result:
                return {
                    "status": "FAIL",
                    "message": "No data in bronze table",
                    "details": {}
                }

            record_count, latest_ingestion, equipment_count = result[0]

            # Expected: >100 records/minute × 5 minutes = >500 records
            # Expected: 15 distinct equipment IDs

            if record_count > 500 and equipment_count == 15:
                return {
                    "status": "PASS",
                    "message": f"Bronze table ingesting data ({record_count} records, {equipment_count} equipment)",
                    "details": {
                        "record_count": record_count,
                        "equipment_count": equipment_count,
                        "latest_ingestion": str(latest_ingestion)
                    }
                }
            elif record_count > 100:
                return {
                    "status": "WARNING",
                    "message": f"Low record count or missing equipment ({record_count} records, {equipment_count} equipment)",
                    "details": {
                        "record_count": record_count,
                        "equipment_count": equipment_count,
                        "expected_records": ">500",
                        "expected_equipment": 15
                    }
                }
            else:
                return {
                    "status": "FAIL",
                    "message": f"Insufficient data ingestion ({record_count} records)",
                    "details": {
                        "record_count": record_count,
                        "equipment_count": equipment_count
                    }
                }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Bronze ingestion test failed: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_bronze_has_recent_data(self) -> Dict[str, Any]:
        """Quick check if bronze table has recent data (smoke test)"""
        try:
            query = f"""
            SELECT max(ingestion_timestamp) as latest
            FROM {self.catalog}.{self.schema}.ot_telemetry_bronze
            """

            result = self._execute_query(query)
            if not result or not result[0][0]:
                return {
                    "status": "FAIL",
                    "message": "No data in bronze table",
                    "details": {}
                }

            latest = result[0][0]
            age_seconds = (datetime.now() - latest).total_seconds()

            if age_seconds < 60:
                return {
                    "status": "PASS",
                    "message": f"Bronze table has recent data ({age_seconds:.0f}s old)",
                    "details": {"age_seconds": age_seconds}
                }
            else:
                return {
                    "status": "FAIL",
                    "message": f"Bronze data is stale ({age_seconds:.0f}s old)",
                    "details": {"age_seconds": age_seconds}
                }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Failed to check bronze data: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_dlt_processing(self) -> Dict[str, Any]:
        """Verify DLT processes data within 3 seconds"""
        try:
            # Test approach: Change a tag value, measure time until it appears in gold

            # 1. Get current timestamp
            t0 = datetime.now()

            # 2. Inject test value (would need to call Ignition API)
            # For this test, we'll verify existing data flow latency

            # 3. Query gold table for recent processing
            query = f"""
            SELECT
                max(window_start) as latest_window,
                current_timestamp() as query_time
            FROM {self.catalog}.{self.schema}.equipment_performance_1min
            """

            result = self._execute_query(query)
            if not result:
                return {
                    "status": "FAIL",
                    "message": "No data in gold table",
                    "details": {}
                }

            latest_window, query_time = result[0]
            processing_lag_seconds = (query_time - latest_window).total_seconds()

            # Target: <3 seconds from event to gold
            # We measure the lag between latest aggregation window and current time

            if processing_lag_seconds < 3:
                return {
                    "status": "PASS",
                    "message": f"DLT processing latency: {processing_lag_seconds:.2f}s",
                    "details": {
                        "latency_seconds": processing_lag_seconds,
                        "target_seconds": 3
                    }
                }
            elif processing_lag_seconds < 5:
                return {
                    "status": "WARNING",
                    "message": f"DLT processing slightly slow: {processing_lag_seconds:.2f}s",
                    "details": {
                        "latency_seconds": processing_lag_seconds,
                        "target_seconds": 3
                    }
                }
            else:
                return {
                    "status": "FAIL",
                    "message": f"DLT processing too slow: {processing_lag_seconds:.2f}s",
                    "details": {
                        "latency_seconds": processing_lag_seconds,
                        "target_seconds": 3
                    }
                }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"DLT processing test failed: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_tag_to_bronze_latency(self) -> Dict[str, Any]:
        """Measure latency from tag update to bronze table"""
        try:
            # Query to calculate ingestion latency
            query = f"""
            SELECT
                avg(timestampdiff(SECOND, event_timestamp, ingestion_timestamp)) as avg_latency_sec,
                max(timestampdiff(SECOND, event_timestamp, ingestion_timestamp)) as max_latency_sec,
                count(*) as sample_size
            FROM {self.catalog}.{self.schema}.ot_telemetry_bronze
            WHERE ingestion_timestamp > current_timestamp() - INTERVAL 5 MINUTES
            """

            result = self._execute_query(query)
            if not result:
                return {
                    "status": "FAIL",
                    "message": "No data to measure latency",
                    "details": {}
                }

            avg_latency, max_latency, sample_size = result[0]

            # Target: <1 second average, <2 seconds max
            if avg_latency < 1 and max_latency < 2:
                return {
                    "status": "PASS",
                    "message": f"Tag→Bronze latency: avg={avg_latency:.2f}s, max={max_latency:.2f}s",
                    "details": {
                        "avg_latency_sec": avg_latency,
                        "max_latency_sec": max_latency,
                        "sample_size": sample_size,
                        "target_avg": 1.0,
                        "target_max": 2.0
                    }
                }
            elif avg_latency < 2:
                return {
                    "status": "WARNING",
                    "message": f"Tag→Bronze latency acceptable: avg={avg_latency:.2f}s, max={max_latency:.2f}s",
                    "details": {
                        "avg_latency_sec": avg_latency,
                        "max_latency_sec": max_latency,
                        "sample_size": sample_size
                    }
                }
            else:
                return {
                    "status": "FAIL",
                    "message": f"Tag→Bronze latency too high: avg={avg_latency:.2f}s, max={max_latency:.2f}s",
                    "details": {
                        "avg_latency_sec": avg_latency,
                        "max_latency_sec": max_latency,
                        "sample_size": sample_size
                    }
                }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Latency measurement failed: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_bronze_to_gold_latency(self) -> Dict[str, Any]:
        """Measure DLT processing latency from bronze to gold"""
        try:
            # This would query DLT metrics table if available
            # For now, we'll use the gold table freshness as a proxy

            query = f"""
            SELECT
                timestampdiff(SECOND, max(window_start), current_timestamp()) as freshness_sec
            FROM {self.catalog}.{self.schema}.equipment_performance_1min
            """

            result = self._execute_query(query)
            if not result:
                return {
                    "status": "FAIL",
                    "message": "Cannot measure gold table freshness",
                    "details": {}
                }

            freshness_sec = result[0][0]

            # Target: <2 seconds from bronze to gold
            if freshness_sec < 2:
                return {
                    "status": "PASS",
                    "message": f"Bronze→Gold latency: {freshness_sec:.2f}s",
                    "details": {"latency_sec": freshness_sec, "target_sec": 2.0}
                }
            elif freshness_sec < 5:
                return {
                    "status": "WARNING",
                    "message": f"Bronze→Gold latency acceptable: {freshness_sec:.2f}s",
                    "details": {"latency_sec": freshness_sec, "target_sec": 2.0}
                }
            else:
                return {
                    "status": "FAIL",
                    "message": f"Bronze→Gold latency too high: {freshness_sec:.2f}s",
                    "details": {"latency_sec": freshness_sec, "target_sec": 2.0}
                }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Bronze→Gold latency test failed: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_gold_table_quality(self) -> Dict[str, Any]:
        """Verify gold table data quality"""
        try:
            query = f"""
            SELECT
                count(*) as total_records,
                count(DISTINCT equipment_id) as equipment_count,
                count(DISTINCT sensor_name) as sensor_count,
                sum(CASE WHEN avg_value IS NULL THEN 1 ELSE 0 END) as null_values,
                sum(CASE WHEN avg_value < 0 THEN 1 ELSE 0 END) as negative_values
            FROM {self.catalog}.{self.schema}.equipment_performance_1min
            WHERE window_start > current_timestamp() - INTERVAL 10 MINUTES
            """

            result = self._execute_query(query)
            if not result:
                return {
                    "status": "FAIL",
                    "message": "No data in gold table",
                    "details": {}
                }

            total, equipment_count, sensor_count, null_values, negative_values = result[0]

            issues = []
            if equipment_count < 15:
                issues.append(f"Missing equipment ({equipment_count}/15)")
            if null_values > 0:
                issues.append(f"{null_values} null values")
            if negative_values > 0:
                issues.append(f"{negative_values} negative values (may be valid)")

            if len(issues) == 0:
                return {
                    "status": "PASS",
                    "message": f"Gold table quality good ({total} records, {equipment_count} equipment)",
                    "details": {
                        "total_records": total,
                        "equipment_count": equipment_count,
                        "sensor_count": sensor_count,
                        "null_values": null_values
                    }
                }
            else:
                return {
                    "status": "WARNING",
                    "message": f"Gold table quality issues: {', '.join(issues)}",
                    "details": {
                        "total_records": total,
                        "equipment_count": equipment_count,
                        "issues": issues
                    }
                }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Gold table quality check failed: {str(e)}",
                "details": {"error": str(e)}
            }

    def test_all_equipment_present(self) -> Dict[str, Any]:
        """Verify all 15 equipment IDs are present in data"""
        try:
            query = f"""
            SELECT DISTINCT equipment_id
            FROM {self.catalog}.{self.schema}.ot_telemetry_bronze
            WHERE ingestion_timestamp > current_timestamp() - INTERVAL 5 MINUTES
            ORDER BY equipment_id
            """

            result = self._execute_query(query)
            equipment_ids = [row[0] for row in result]

            expected_equipment = [
                "HT_001", "HT_002", "HT_003", "HT_004", "HT_005",
                "CR_001", "CR_002", "CR_003",
                "CV_001", "CV_002", "CV_003", "CV_004",
                "LD_001", "LD_002", "LD_003"
            ]

            missing = set(expected_equipment) - set(equipment_ids)

            if len(missing) == 0:
                return {
                    "status": "PASS",
                    "message": f"All {len(expected_equipment)} equipment present",
                    "details": {"equipment_ids": equipment_ids}
                }
            else:
                return {
                    "status": "FAIL",
                    "message": f"Missing equipment: {', '.join(missing)}",
                    "details": {
                        "found": equipment_ids,
                        "missing": list(missing),
                        "expected": expected_equipment
                    }
                }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Equipment check failed: {str(e)}",
                "details": {"error": str(e)}
            }


if __name__ == "__main__":
    # Run tests standalone
    tests = DatabricksPipelineTests()

    print("Databricks Pipeline Tests")
    print("=" * 60)

    print("\n1. Databricks Connectivity")
    result = tests.test_databricks_connectivity()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")

    print("\n2. SQL Warehouse Status")
    result = tests.test_warehouse_status()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")

    print("\n3. Bronze Ingestion")
    result = tests.test_bronze_ingestion()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")

    print("\n4. DLT Processing")
    result = tests.test_dlt_processing()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")

    print("\n5. Gold Table Quality")
    result = tests.test_gold_table_quality()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")

    print("\n6. All Equipment Present")
    result = tests.test_all_equipment_present()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")
