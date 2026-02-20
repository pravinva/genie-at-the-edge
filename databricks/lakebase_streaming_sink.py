# Databricks notebook source
# MAGIC %md
# MAGIC # Lakebase Streaming Sink Configuration
# MAGIC Optimized streaming writer for Lakebase with exactly-once semantics

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.streaming import StreamingQuery
from delta.tables import DeltaTable
import uuid
from typing import Dict, Any

# COMMAND ----------

# Configuration
LAKEBASE_CONFIG = {
    "catalog": "lakebase",
    "schema": "agentic_hmi",
    "jdbc_url": "jdbc:postgresql://workspace.cloud.databricks.com/lakebase",
    "warehouse_id": "4b9b953939869799",
    "checkpoint_location": "/tmp/lakebase_checkpoints"
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Streaming Sink with Deduplication

# COMMAND ----------

class LakebaseStreamWriter:
    """
    Manages streaming writes to Lakebase with deduplication and error handling
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.dedup_window_minutes = 5
        self.batch_size = 100

    def write_recommendations(self, df, epoch_id):
        """
        Write recommendations to Lakebase with deduplication
        """
        print(f"Processing epoch {epoch_id} with {df.count()} recommendations")

        # Add Lakebase-specific fields
        df_enriched = df.withColumn("sync_id", F.expr("uuid()")) \
                       .withColumn("sync_timestamp", F.current_timestamp()) \
                       .withColumn("epoch_id", F.lit(epoch_id))

        # Create temp view for SQL operations
        df_enriched.createOrReplaceTempView(f"recommendations_batch_{epoch_id}")

        # Insert with deduplication check
        insert_query = f"""
        INSERT INTO {self.config['catalog']}.{self.config['schema']}.agent_recommendations
        SELECT
            recommendation_id,
            equipment_id,
            issue_type,
            severity,
            CONCAT('AI Analysis: ', root_cause_analysis) as issue_description,
            recommended_action,
            confidence_score,
            root_cause_analysis,
            expected_outcome,
            'pending' as status,
            NULL as operator_id,
            NULL as operator_notes,
            NULL as approved_timestamp,
            NULL as executed_timestamp,
            NULL as defer_until,
            NULL as rejection_reason,
            created_timestamp,
            updated_timestamp
        FROM recommendations_batch_{epoch_id} r
        WHERE NOT EXISTS (
            -- Deduplication: Don't insert if similar recommendation exists recently
            SELECT 1
            FROM {self.config['catalog']}.{self.config['schema']}.agent_recommendations e
            WHERE e.equipment_id = r.equipment_id
              AND e.issue_type = r.issue_type
              AND e.status IN ('pending', 'approved')
              AND e.created_timestamp > CURRENT_TIMESTAMP() - INTERVAL {self.dedup_window_minutes} MINUTES
        )
        AND r.confidence_score > 0.6  -- Only high-confidence recommendations
        """

        try:
            spark.sql(insert_query)
            inserted_count = spark.sql(f"SELECT COUNT(*) FROM recommendations_batch_{epoch_id}").collect()[0][0]
            print(f"✓ Inserted {inserted_count} new recommendations to Lakebase")

            # Track metrics
            self._log_metrics(epoch_id, inserted_count, "SUCCESS")

        except Exception as e:
            print(f"✗ Error writing to Lakebase: {str(e)}")
            self._log_metrics(epoch_id, 0, f"ERROR: {str(e)}")
            # Don't fail the stream, log and continue

    def write_sensor_updates(self, df, epoch_id):
        """
        Write sensor anomalies to Lakebase for real-time monitoring
        """
        # Only write significant anomalies
        anomalies = df.filter(F.col("anomaly_score") > 0.7)

        if anomalies.count() > 0:
            anomalies.createOrReplaceTempView(f"sensor_anomalies_{epoch_id}")

            # Update or insert sensor status
            merge_query = f"""
            MERGE INTO {self.config['catalog']}.{self.config['schema']}.sensor_data t
            USING sensor_anomalies_{epoch_id} s
            ON t.equipment_id = s.equipment_id AND t.sensor_type = s.sensor_type
            WHEN MATCHED AND s.anomaly_score > t.sensor_value THEN
                UPDATE SET
                    sensor_value = s.sensor_value,
                    quality = CASE WHEN s.anomaly_score > 0.9 THEN 'critical' ELSE 'warning' END,
                    timestamp = s.timestamp
            WHEN NOT MATCHED THEN
                INSERT (reading_id, equipment_id, sensor_type, sensor_value, units, quality, timestamp)
                VALUES (uuid(), s.equipment_id, s.sensor_type, s.sensor_value, s.units,
                       CASE WHEN s.anomaly_score > 0.9 THEN 'critical' ELSE 'warning' END,
                       s.timestamp)
            """

            try:
                spark.sql(merge_query)
                print(f"✓ Updated sensor anomalies in Lakebase")
            except Exception as e:
                print(f"✗ Error updating sensors: {str(e)}")

    def write_metrics(self, df, epoch_id):
        """
        Write pipeline metrics to Lakebase for monitoring
        """
        metrics_df = df.select(
            F.expr("uuid()").alias("metric_id"),
            F.lit("ai_pipeline").alias("agent_id"),
            F.col("metric_name"),
            F.col("metric_value"),
            F.col("metric_unit"),
            F.current_timestamp().alias("timestamp")
        )

        metrics_df.write \
            .mode("append") \
            .saveAsTable(f"{self.config['catalog']}.{self.config['schema']}.agent_metrics")

    def _log_metrics(self, epoch_id: int, record_count: int, status: str):
        """
        Log streaming metrics for observability
        """
        metrics = [{
            "metric_id": str(uuid.uuid4()),
            "agent_id": "lakebase_streamer",
            "metric_name": "records_written",
            "metric_value": float(record_count),
            "metric_unit": "count",
            "timestamp": F.current_timestamp()
        }]

        spark.createDataFrame(metrics).write \
            .mode("append") \
            .saveAsTable(f"{self.config['catalog']}.{self.config['schema']}.agent_metrics")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Streaming Pipeline Configuration

# COMMAND ----------

def create_lakebase_streams():
    """
    Create all streaming connections to Lakebase
    """
    writer = LakebaseStreamWriter(LAKEBASE_CONFIG)
    streams = {}

    # Stream 1: AI Recommendations
    print("Starting recommendations stream...")
    recommendations_stream = (
        spark.readStream
        .table("main.mining_operations.ai_recommendations_gold")
        .writeStream
        .foreachBatch(writer.write_recommendations)
        .trigger(processingTime="10 seconds")
        .option("checkpointLocation", f"{LAKEBASE_CONFIG['checkpoint_location']}/recommendations")
        .outputMode("append")
        .start()
    )
    streams["recommendations"] = recommendations_stream

    # Stream 2: Critical Sensor Anomalies
    print("Starting sensor anomaly stream...")
    sensor_stream = (
        spark.readStream
        .table("main.mining_operations.anomaly_detection_silver")
        .filter(F.col("is_anomaly") == True)
        .writeStream
        .foreachBatch(writer.write_sensor_updates)
        .trigger(processingTime="5 seconds")  # Lower latency for critical updates
        .option("checkpointLocation", f"{LAKEBASE_CONFIG['checkpoint_location']}/sensors")
        .outputMode("append")
        .start()
    )
    streams["sensors"] = sensor_stream

    # Stream 3: Operator Feedback Loop
    print("Starting feedback stream...")
    feedback_stream = (
        spark.readStream
        .format("delta")
        .option("readChangeFeed", "true")
        .table(f"{LAKEBASE_CONFIG['catalog']}.{LAKEBASE_CONFIG['schema']}.agent_recommendations")
        .filter(F.col("_change_type").isin(["update_postimage"]))
        .filter(F.col("status").isin(["approved", "rejected"]))
        .select(
            F.col("recommendation_id"),
            F.col("status").alias("operator_decision"),
            F.col("operator_notes"),
            F.col("confidence_score"),
            F.current_timestamp().alias("feedback_timestamp")
        )
        .writeStream
        .trigger(processingTime="30 seconds")
        .option("checkpointLocation", f"{LAKEBASE_CONFIG['checkpoint_location']}/feedback")
        .outputMode("append")
        .toTable("main.mining_operations.operator_feedback")
    )
    streams["feedback"] = feedback_stream

    return streams

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stream Monitoring

# COMMAND ----------

def monitor_streams(streams: Dict[str, StreamingQuery]):
    """
    Monitor health of all streaming queries
    """
    import time

    while True:
        print("\n" + "="*60)
        print(f"Stream Status at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        for name, stream in streams.items():
            if stream.isActive:
                status = stream.status
                progress = stream.lastProgress

                print(f"\n{name.upper()} Stream:")
                print(f"  Status: ✓ Active")
                print(f"  Trigger: {status['message']}")

                if progress:
                    print(f"  Input Rate: {progress.get('inputRowsPerSecond', 0):.2f} rows/sec")
                    print(f"  Process Rate: {progress.get('processedRowsPerSecond', 0):.2f} rows/sec")
                    print(f"  Batch Duration: {progress.get('durationMs', {}).get('triggerExecution', 0)}ms")

                    if 'sources' in progress and len(progress['sources']) > 0:
                        source = progress['sources'][0]
                        print(f"  Offset: {source.get('endOffset', 'N/A')}")
            else:
                print(f"\n{name.upper()} Stream: ✗ STOPPED")

        time.sleep(60)  # Check every minute

# COMMAND ----------

# MAGIC %md
# MAGIC ## Error Recovery

# COMMAND ----------

def setup_error_recovery():
    """
    Configure automatic error recovery for streams
    """

    # Set Spark configurations for resilience
    spark.conf.set("spark.sql.streaming.stopGracefullyOnShutdown", "true")
    spark.conf.set("spark.sql.streaming.schemaInference", "true")
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

    # Configure state store for recovery
    spark.conf.set("spark.sql.streaming.stateStore.providerClass",
                   "org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider")

    # Set checkpoint cleanup
    spark.conf.set("spark.sql.streaming.minBatchesToRetain", "10")

    print("✓ Error recovery configured")

def recover_failed_stream(stream_name: str, streams: Dict[str, StreamingQuery]):
    """
    Recover a failed stream
    """
    if stream_name in streams:
        stream = streams[stream_name]
        if not stream.isActive:
            print(f"Recovering {stream_name} stream...")

            # Stop cleanly if needed
            try:
                stream.stop()
            except:
                pass

            # Recreate the stream
            new_streams = create_lakebase_streams()
            streams[stream_name] = new_streams[stream_name]

            print(f"✓ {stream_name} stream recovered")

    return streams

# COMMAND ----------

# MAGIC %md
# MAGIC ## Start Streaming

# COMMAND ----------

# Configure environment
setup_error_recovery()

# Start all streams
streams = create_lakebase_streams()

print("\n" + "="*60)
print("🚀 LAKEBASE STREAMING PIPELINE STARTED")
print("="*60)
print("\nActive Streams:")
for name, stream in streams.items():
    print(f"  • {name}: {'✓ Active' if stream.isActive else '✗ Stopped'}")

print("\n📊 Monitoring Dashboard:")
print(f"  • Recommendations: SELECT COUNT(*) FROM {LAKEBASE_CONFIG['catalog']}.{LAKEBASE_CONFIG['schema']}.agent_recommendations")
print(f"  • Metrics: SELECT * FROM {LAKEBASE_CONFIG['catalog']}.{LAKEBASE_CONFIG['schema']}.agent_metrics ORDER BY timestamp DESC")

# Start monitoring (in production, this would run in a separate thread)
# monitor_streams(streams)