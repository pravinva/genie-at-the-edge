"""
Real-time ML Scoring Pipeline
Applies anomaly detection model to streaming gold features
Writes recommendations to Lakebase for sub-100ms serving to Ignition

Architecture:
- Reads: gold_ml_features (streaming)
- Scores: Using @champion model from Unity Catalog
- Writes: Lakebase table with PostgreSQL webhook (PG NOTIFY)
- Latency: ~5-8 seconds end-to-end (sensor → recommendation)
"""

from pyspark.sql import functions as F
from pyspark.sql.types import *
import mlflow

# ============================================================================
# CONFIGURATION
# ============================================================================

CATALOG = "field_engineering"
SCHEMA_SILVER = "ml_silver"
SCHEMA_LAKEBASE = "lakebase"
MODEL_NAME = f"{CATALOG}.ml_models.equipment_anomaly_detector"

def _resolve_threshold() -> float:
    # Prefer explicit notebook parameter; fall back to Spark conf/default.
    try:
        dbutils.widgets.text("anomaly_threshold", "0.5")
        return float(dbutils.widgets.get("anomaly_threshold"))
    except Exception:
        return float(spark.conf.get("ml.anomaly.threshold", "0.5"))

ANOMALY_THRESHOLD = _resolve_threshold()

def _resolve_checkpoint_location() -> str:
    try:
        dbutils.widgets.text("checkpoint_location", "/tmp/checkpoints/ml_recommendations_v2")
        return dbutils.widgets.get("checkpoint_location")
    except Exception:
        return "/tmp/checkpoints/ml_recommendations_v2"

CHECKPOINT_LOCATION = _resolve_checkpoint_location()

def _resolve_sink_mode() -> str:
    try:
        dbutils.widgets.dropdown("sink_mode", "delta", ["delta", "lakebase_jdbc"])
        return dbutils.widgets.get("sink_mode")
    except Exception:
        return "delta"

def _resolve_lakebase_jdbc_url() -> str:
    try:
        dbutils.widgets.text(
            "lakebase_jdbc_url",
            "jdbc:postgresql://instance-6fac5088-b888-45ea-8cdb-59ddb94b2a81.database.cloud.databricks.com:5432/historian?sslmode=require",
        )
        return dbutils.widgets.get("lakebase_jdbc_url")
    except Exception:
        return ""

def _resolve_lakebase_user() -> str:
    try:
        dbutils.widgets.text("lakebase_user", "ignition_historian")
        return dbutils.widgets.get("lakebase_user")
    except Exception:
        return "ignition_historian"

def _resolve_lakebase_password() -> str:
    try:
        dbutils.widgets.text("lakebase_password", "")
        return dbutils.widgets.get("lakebase_password")
    except Exception:
        return ""

def _resolve_lakebase_table() -> str:
    try:
        dbutils.widgets.text("lakebase_table", "public.ml_recommendations")
        return dbutils.widgets.get("lakebase_table")
    except Exception:
        return "public.ml_recommendations"

SINK_MODE = _resolve_sink_mode()
LAKEBASE_JDBC_URL = _resolve_lakebase_jdbc_url()
LAKEBASE_USER = _resolve_lakebase_user()
LAKEBASE_PASSWORD = _resolve_lakebase_password()
LAKEBASE_TABLE = _resolve_lakebase_table()

# Load model
print("Loading ML model from Unity Catalog...")
model_uri = f"models:/{MODEL_NAME}@champion"
loaded_model = mlflow.pyfunc.spark_udf(
    spark,
    model_uri=model_uri,
    result_type=StructType([
        StructField("anomaly_score", DoubleType()),
        StructField("is_anomaly", BooleanType()),
        StructField("action_code", StringType()),
        StructField("confidence", DoubleType()),
        StructField("recommendation_text", StringType())
    ])
)

print(f"✅ Model loaded: {model_uri}")
print(f"Using anomaly threshold: {ANOMALY_THRESHOLD}")
print(f"Using checkpoint location: {CHECKPOINT_LOCATION}")
print(f"Using sink mode: {SINK_MODE}")

# ============================================================================
# STREAMING INFERENCE QUERY
# ============================================================================

print("Setting up streaming inference pipeline...")

# Read streaming gold features
gold_stream = (
    spark.readStream
    .table(f"{CATALOG}.{SCHEMA_SILVER}.gold_ml_features")
)

# Feature columns (must match training)
feature_cols = [
    'temp_avg_5min', 'temp_max_5min', 'temp_std_5min', 'temp_deviation_from_baseline',
    'vibration_avg_5min', 'vibration_max_5min', 'vibration_std_5min', 'vibration_deviation_from_baseline',
    'throughput_avg_5min', 'throughput_min_5min',
    'pressure_avg_5min', 'pressure_max_5min',
    'temp_vibration_interaction', 'total_variability',
    'temp_avg_15min', 'vibration_avg_15min',
    'temp_avg_1hour', 'vibration_avg_1hour',
    'days_since_maintenance', 'equipment_age_days'
]

# Normalize feature columns for model inference.
# The registered IsolationForest pipeline cannot score rows with NaN/null values.
feature_ready = gold_stream
for c in feature_cols:
    if c == "equipment_age_days":
        feature_ready = feature_ready.withColumn(
            c,
            F.when(F.col(c).isNull(), F.lit(0)).otherwise(F.col(c).cast("int"))
        )
    else:
        feature_ready = feature_ready.withColumn(
            c,
            F.when(F.isnan(F.col(c).cast("double")) | F.col(c).isNull(), F.lit(0.0))
             .otherwise(F.col(c).cast("double"))
        )

# Create feature struct for UDF
feature_struct = F.struct(*[F.col(c) for c in feature_cols])

# Apply model scoring
scored_stream = (
    feature_ready
    .withColumn("prediction", loaded_model(feature_struct))
    .select(
        F.col("equipment_id"),
        F.col("window_end").alias("timestamp"),
        F.col("shift"),
        F.col("product_type"),

        # Model outputs
        F.col("prediction.anomaly_score").alias("anomaly_score"),
        F.col("prediction.is_anomaly").alias("is_anomaly"),
        F.col("prediction.action_code").alias("action_code"),
        F.col("prediction.confidence").alias("confidence"),
        F.col("prediction.recommendation_text").alias("recommendation_text"),

        # Context for operator
        F.col("temp_avg_5min"),
        F.col("vibration_avg_5min"),
        F.col("throughput_avg_5min"),
        F.col("temp_deviation_from_baseline"),
        F.col("vibration_deviation_from_baseline"),
        F.col("days_since_maintenance").cast("int").alias("days_since_maintenance"),
        F.col("last_maintenance_type"),

        # Add fields for Ignition display
        F.when(F.col("prediction.anomaly_score") > 0.9, "critical")
         .when(F.col("prediction.anomaly_score") > 0.7, "high")
         .when(F.col("prediction.anomaly_score") > ANOMALY_THRESHOLD, "medium")
         .otherwise("low").alias("severity"),

        # Estimated time to failure (heuristic based on anomaly score & maintenance days)
        F.when(F.col("prediction.anomaly_score") > 0.9, "12-24 hours")
         .when(F.col("prediction.anomaly_score") > 0.7, "48-72 hours")
         .when(F.col("prediction.anomaly_score") > ANOMALY_THRESHOLD, "1-2 weeks")
         .otherwise("Normal operation").alias("estimated_ttf"),

        F.current_timestamp().alias("scored_at"),
        F.lit("model").alias("recommendation_source")
    )
    # Filter to only actionable recommendations (above threshold)
    .filter(F.col("anomaly_score") > F.lit(ANOMALY_THRESHOLD))
)

# ============================================================================
# WRITE TO LAKEBASE FOR LOW-LATENCY SERVING
# ============================================================================

print("Starting streaming write...")

if SINK_MODE == "lakebase_jdbc":
    if not LAKEBASE_PASSWORD:
        raise ValueError("lakebase_password is required when sink_mode=lakebase_jdbc")

    def _write_to_lakebase_jdbc(batch_df, batch_id):
        (batch_df
         .select(
             "equipment_id", "timestamp", "shift", "product_type",
             "anomaly_score", "is_anomaly", "action_code", "confidence", "recommendation_text",
             "temp_avg_5min", "vibration_avg_5min", "throughput_avg_5min",
             "temp_deviation_from_baseline", "vibration_deviation_from_baseline",
             "days_since_maintenance", "last_maintenance_type",
             "severity", "estimated_ttf", "scored_at", "recommendation_source"
         )
         .write
         .format("jdbc")
         .option("url", LAKEBASE_JDBC_URL)
         .option("dbtable", LAKEBASE_TABLE)
         .option("user", LAKEBASE_USER)
         .option("password", LAKEBASE_PASSWORD)
         .option("driver", "org.postgresql.Driver")
         .mode("append")
         .save())

    query = (
        scored_stream.writeStream
        .outputMode("append")
        .option("checkpointLocation", CHECKPOINT_LOCATION)
        .trigger(processingTime="30 seconds")
        .foreachBatch(_write_to_lakebase_jdbc)
        .start()
    )
    target_display = f"JDBC::{LAKEBASE_TABLE}"
else:
    # Default sink for platform-local testing
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA_LAKEBASE}")
    query = (
        scored_stream.writeStream
        .outputMode("append")
        .option("checkpointLocation", CHECKPOINT_LOCATION)
        .trigger(processingTime="30 seconds")  # Micro-batch every 30s
        .table(f"{CATALOG}.{SCHEMA_LAKEBASE}.ml_recommendations")
    )
    target_display = f"{CATALOG}.{SCHEMA_LAKEBASE}.ml_recommendations"

print(f"""
✅ Real-time scoring pipeline started

Stream details:
- Source: {CATALOG}.{SCHEMA_SILVER}.gold_ml_features
- Target: {target_display}
- Trigger: Every 30 seconds
- Filter: anomaly_score > {ANOMALY_THRESHOLD}

Pipeline status:
- Query ID: {query.id}
- Status: {query.status}

To stop: query.stop()
To check: query.lastProgress
""")

# Keep alive
query.awaitTermination()
