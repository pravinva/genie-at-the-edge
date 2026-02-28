# Databricks notebook source
# MAGIC %md
# MAGIC # Production ML Recommendation Pipeline with Webhooks
# MAGIC Complete implementation with realistic latencies and webhook notifications

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import *
import dlt
import mlflow
import requests
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# COMMAND ----------

# Configuration
CONFIG = {
    "catalog": "field_engineering",
    "schema": "mining_demo",
    "serving_schema": "lakebase",
    "batch_interval": "10 seconds",  # Realistic for production
    "anomaly_threshold": 0.7,
    "webhook_url": "http://ignition-gateway:8088/system/webdev/databricks/webhooks/recommendations",
    "lakebase_url": "jdbc:postgresql://workspace.cloud.databricks.com/lakebase",
    "warehouse_id": "4b9b953939869799",
    "critical_urgency_threshold": 4
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Anomaly Detection Layer (ML Model)

# COMMAND ----------

@dlt.table(
    name="anomaly_detection_silver",
    comment="ML-detected anomalies from sensor data",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.managed": "true"
    }
)
def detect_anomalies():
    """
    Detect anomalies using trained ML model
    Latency: 5-10 seconds (micro-batch processing)
    """

    # Load pre-trained anomaly detection model
    anomaly_model = mlflow.pyfunc.load_model(
        "models:/field_engineering.ml_models.equipment_anomaly_detector@champion"
    )

    # Read sensor stream with watermark for late data
    sensor_stream = (
        dlt.read_stream("sensor_stream_bronze")
        .withWatermark("timestamp", "30 seconds")  # Handle late arrivals
    )

    # Detect anomalies using ML model
    def detect_anomaly_udf(equipment_id, sensor_type, sensor_value,
                           rolling_avg, rolling_std):
        """UDF for anomaly detection"""

        features = {
            "sensor_value": float(sensor_value),
            "rolling_avg": float(rolling_avg),
            "rolling_std": float(rolling_std),
            "z_score": (float(sensor_value) - float(rolling_avg)) / max(float(rolling_std), 0.001),
            "hour_of_day": datetime.now().hour,
            "day_of_week": datetime.now().weekday()
        }

        # Model returns anomaly score and severity
        prediction = anomaly_model.predict([features])[0]

        return {
            "is_anomaly": prediction["score"] > CONFIG["anomaly_threshold"],
            "anomaly_score": float(prediction["score"]),
            "severity": prediction["severity"]  # low, medium, high, critical
        }

    # Apply anomaly detection
    anomaly_udf_spark = F.udf(detect_anomaly_udf,
        StructType([
            StructField("is_anomaly", BooleanType()),
            StructField("anomaly_score", DoubleType()),
            StructField("severity", StringType())
        ])
    )

    return (
        sensor_stream
        .groupBy(
            F.window("timestamp", CONFIG["batch_interval"]),
            "equipment_id",
            "sensor_type"
        )
        .agg(
            F.last("sensor_value").alias("sensor_value"),
            F.avg("sensor_value").alias("rolling_avg"),
            F.stddev("sensor_value").alias("rolling_std"),
            F.max("timestamp").alias("timestamp")
        )
        .withColumn("anomaly_result",
            anomaly_udf_spark(
                F.col("equipment_id"),
                F.col("sensor_type"),
                F.col("sensor_value"),
                F.col("rolling_avg"),
                F.col("rolling_std")
            )
        )
        .select(
            F.col("equipment_id"),
            F.col("sensor_type"),
            F.col("sensor_value"),
            F.col("timestamp"),
            F.col("anomaly_result.is_anomaly").alias("is_anomaly"),
            F.col("anomaly_result.anomaly_score").alias("anomaly_score"),
            F.col("anomaly_result.severity").alias("severity")
        )
        .filter(F.col("is_anomaly") == True)
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. ML Recommendation Generation (NOT Genie)

# COMMAND ----------

@dlt.table(
    name="ml_recommendations_gold",
    comment="ML-generated recommendations for anomalies",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.managed": "true"
    }
)
def generate_ml_recommendations():
    """
    Generate recommendations using ML model (NOT Genie)
    Latency: 5-10 seconds additional
    """

    # Load recommendation model
    recommendation_model = mlflow.pyfunc.load_model(
        "models:/field_engineering.ml_models.equipment_recommendation_engine@champion"
    )

    # Read anomalies
    anomalies = dlt.read_stream("anomaly_detection_silver")

    def generate_recommendation_udf(equipment_id, sensor_type, anomaly_score, severity):
        """Generate recommendation using ML model"""

        # Get equipment context (cached)
        context = get_equipment_context(equipment_id)

        # Prepare features for recommendation model
        features = {
            "equipment_id": equipment_id,
            "sensor_type": sensor_type,
            "anomaly_score": float(anomaly_score),
            "severity_encoded": {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(severity, 2),
            "days_since_maintenance": context.get("days_since_maintenance", 30),
            "production_priority": context.get("production_priority", 2),
            "similar_failures_count": context.get("similar_failures_30d", 0)
        }

        # Model predicts action code and metadata
        prediction = recommendation_model.predict([features])[0]

        return {
            "action_code": prediction["action"],  # e.g., "REDUCE_SPEED_60"
            "confidence": float(prediction["confidence"]),
            "urgency": int(prediction["urgency"]),  # 1-5 scale
            "time_to_failure": float(prediction.get("ttf_hours", 0)),
            "parts_needed": prediction.get("parts", [])
        }

    # Create UDF
    recommendation_udf_spark = F.udf(generate_recommendation_udf,
        StructType([
            StructField("action_code", StringType()),
            StructField("confidence", DoubleType()),
            StructField("urgency", IntegerType()),
            StructField("time_to_failure", DoubleType()),
            StructField("parts_needed", ArrayType(StringType()))
        ])
    )

    return (
        anomalies
        .withColumn("recommendation",
            recommendation_udf_spark(
                F.col("equipment_id"),
                F.col("sensor_type"),
                F.col("anomaly_score"),
                F.col("severity")
            )
        )
        .select(
            F.expr("uuid()").alias("recommendation_id"),
            F.col("equipment_id"),
            F.col("sensor_type"),
            F.col("sensor_value"),
            F.col("anomaly_score"),
            F.col("severity"),
            F.col("recommendation.action_code").alias("action_code"),
            F.col("recommendation.confidence").alias("confidence"),
            F.col("recommendation.urgency").alias("urgency"),
            F.col("recommendation.time_to_failure").alias("time_to_failure"),
            F.col("recommendation.parts_needed").alias("parts_list"),
            F.current_timestamp().alias("created_timestamp"),
            F.lit("pending").alias("status")
        )
        .filter(F.col("confidence") > 0.6)  # Only high-confidence recommendations
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Webhook Notification System

# COMMAND ----------

class WebhookNotifier:
    """Send webhooks to Ignition for real-time updates"""

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.session = requests.Session()

    def send_notification(self, recommendation):
        """Send webhook to Ignition"""

        payload = {
            "recommendation_id": recommendation["recommendation_id"],
            "equipment_id": recommendation["equipment_id"],
            "action_code": recommendation["action_code"],
            "confidence": float(recommendation["confidence"]),
            "urgency": int(recommendation["urgency"]),
            "time_to_failure": float(recommendation["time_to_failure"]) if recommendation["time_to_failure"] else None,
            "parts_list": recommendation["parts_list"],
            "severity": recommendation["severity"],
            "timestamp": str(recommendation["created_timestamp"])
        }

        try:
            response = self.session.post(
                self.webhook_url,
                json=payload,
                timeout=2,  # Don't block pipeline
                headers={
                    'Content-Type': 'application/json',
                    'X-Source': 'Databricks-ML-Pipeline'
                }
            )

            if response.status_code == 200:
                logger.info(f"✓ Webhook sent for {recommendation['recommendation_id']}")
                return True
            else:
                logger.warning(f"✗ Webhook failed: {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            logger.warning("Webhook timeout - Ignition may be slow")
            return False
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return False

# Initialize notifier
notifier = WebhookNotifier(CONFIG["webhook_url"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Stream to Lakebase with Webhook Trigger

# COMMAND ----------

def write_recommendations_and_notify(df, epoch_id):
    """
    Write to Lakebase and send webhooks for critical items
    This is called for each micro-batch
    """

    logger.info(f"Processing epoch {epoch_id} with {df.count()} recommendations")

    # Collect recommendations for this batch
    recommendations = df.collect()

    if len(recommendations) > 0:
        # 1. Batch write to Lakebase
        df.write \
            .mode("append") \
            .jdbc(
                url=CONFIG["lakebase_url"],
                    table="lakebase.agent_recommendations",
                properties={
                    "user": spark.conf.get("lakebase.user"),
                    "password": spark.conf.get("lakebase.password"),
                    "warehouse": CONFIG["warehouse_id"]
                }
            )

        logger.info(f"✓ Wrote {len(recommendations)} to Lakebase")

        # 2. Send webhooks for high-urgency items
        critical_count = 0
        for rec in recommendations:
            rec_dict = rec.asDict()

            # Send webhook for critical items
            if rec_dict["urgency"] >= CONFIG["critical_urgency_threshold"]:
                notifier.send_notification(rec_dict)
                critical_count += 1

        logger.info(f"✓ Sent {critical_count} critical webhooks")

        # 3. Update metrics
        update_pipeline_metrics(epoch_id, len(recommendations), critical_count)

def update_pipeline_metrics(epoch_id, total_recs, critical_recs):
    """Track pipeline performance metrics"""

    metrics_df = spark.createDataFrame([{
        "epoch_id": epoch_id,
        "timestamp": datetime.now(),
        "recommendations_generated": total_recs,
        "critical_webhooks_sent": critical_recs,
        "pipeline_stage": "ml_recommendations"
    }])

    metrics_df.write \
        .mode("append") \
        .saveAsTable(f"{CONFIG['catalog']}.{CONFIG['schema']}.pipeline_metrics")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Start Streaming Pipeline

# COMMAND ----------

# Main streaming query with webhook notifications
recommendation_stream = (
    spark.readStream
    .table(f"{CONFIG['catalog']}.{CONFIG['schema']}.ml_recommendations_gold")
    .writeStream
    .foreachBatch(write_recommendations_and_notify)
    .trigger(processingTime=CONFIG["batch_interval"])  # 10 second batches
    .option("checkpointLocation", "/tmp/checkpoints/ml_recommendations_webhook")
    .outputMode("append")
    .start()
)

logger.info(f"""
🚀 ML RECOMMENDATION PIPELINE STARTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Batch interval: {CONFIG['batch_interval']}
• Webhook URL: {CONFIG['webhook_url']}
• Critical threshold: Urgency >= {CONFIG['critical_urgency_threshold']}
• Anomaly threshold: {CONFIG['anomaly_threshold']}

Expected Latencies:
• Sensor → Anomaly: 10-15 seconds
• Anomaly → Recommendation: 10-15 seconds
• Recommendation → Lakebase: 2-5 seconds
• Webhook → Ignition: <1 second
• Total E2E: 22-36 seconds
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Edge Detection for Critical Safety (Bypass ML)

# COMMAND ----------

def setup_critical_bypass():
    """
    Setup direct path for critical safety issues
    Bypasses ML for <1 second response
    """

    # Critical thresholds (rule-based, no ML)
    CRITICAL_RULES = {
        "temperature": {"max": 95, "rate_limit": 5},  # °C and °C/min
        "vibration": {"max": 8, "rate_limit": 2},     # mm/s and mm/s/min
        "pressure": {"max": 150, "rate_limit": 10}    # bar and bar/min
    }

    def check_critical_safety(sensor_type, sensor_value, rate_of_change):
        """Simple rule-based critical detection"""

        if sensor_type in CRITICAL_RULES:
            rule = CRITICAL_RULES[sensor_type]

            if sensor_value > rule["max"] or abs(rate_of_change) > rule["rate_limit"]:
                return {
                    "is_critical": True,
                    "action": "EMERGENCY_STOP",
                    "reason": f"{sensor_type} exceeded safety limit"
                }

        return {"is_critical": False}

    # This runs at the edge (Ignition Gateway)
    # Implemented in Gateway Event Scripts
    return check_critical_safety

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Helper Functions

# COMMAND ----------

def get_equipment_context(equipment_id):
    """
    Get cached equipment context for recommendation generation
    This would normally query CMMS, MES, ERP systems
    """

    # In production, this would be a cached lookup
    # For now, return mock context
    return {
        "days_since_maintenance": 45,
        "production_priority": 3,  # 1-5 scale
        "similar_failures_30d": 2,
        "warranty_status": "active",
        "spare_parts_available": True
    }

def monitor_pipeline_health():
    """Monitor streaming pipeline health"""

    query = """
        SELECT
            MAX(timestamp) as latest_recommendation,
            COUNT(*) as recs_last_hour,
            AVG(confidence) as avg_confidence,
            SUM(CASE WHEN urgency >= 4 THEN 1 ELSE 0 END) as critical_count
        FROM field_engineering.mining_demo.ml_recommendations_gold
        WHERE created_timestamp > current_timestamp() - INTERVAL 1 HOUR
    """

    return spark.sql(query).collect()[0]

# COMMAND ----------

# Monitor stream progress
for progress in recommendation_stream.recentProgress:
    print(f"""
    Batch ID: {progress.get('id')}
    Input Rate: {progress.get('inputRowsPerSecond', 0):.2f} rows/sec
    Process Rate: {progress.get('processedRowsPerSecond', 0):.2f} rows/sec
    Latency: {progress.get('durationMs', {}).get('triggerExecution', 0)} ms
    """)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Testing Webhook Integration

# COMMAND ----------

def test_webhook_integration():
    """Test webhook connectivity to Ignition"""

    test_recommendation = {
        "recommendation_id": "test_" + str(datetime.now().timestamp()),
        "equipment_id": "TEST_EQUIPMENT",
        "action_code": "TEST_ACTION",
        "confidence": 0.95,
        "urgency": 5,
        "time_to_failure": 2.0,
        "parts_list": ["TEST_PART_001"],
        "severity": "critical",
        "created_timestamp": datetime.now()
    }

    notifier = WebhookNotifier(CONFIG["webhook_url"])
    success = notifier.send_notification(test_recommendation)

    if success:
        print("✓ Webhook test successful - Ignition received notification")
    else:
        print("✗ Webhook test failed - Check Ignition WebDev module")

    return success

# Run test
# test_webhook_integration()