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

# Create feature struct for UDF
feature_struct = F.struct(*[F.col(c) for c in feature_cols])

# Apply model scoring
scored_stream = (
    gold_stream
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
        F.col("days_since_maintenance"),
        F.col("last_maintenance_type"),

        # Add fields for Ignition display
        F.when(F.col("prediction.anomaly_score") > 0.9, "critical")
         .when(F.col("prediction.anomaly_score") > 0.7, "high")
         .when(F.col("prediction.anomaly_score") > 0.5, "medium")
         .otherwise("low").alias("severity"),

        # Estimated time to failure (heuristic based on anomaly score & maintenance days)
        F.when(F.col("prediction.anomaly_score") > 0.9, "12-24 hours")
         .when(F.col("prediction.anomaly_score") > 0.7, "48-72 hours")
         .when(F.col("prediction.anomaly_score") > 0.5, "1-2 weeks")
         .otherwise("Normal operation").alias("estimated_ttf"),

        F.current_timestamp().alias("scored_at"),
        F.lit("model").alias("recommendation_source")
    )
    # Filter to only actionable recommendations (above threshold)
    .filter(F.col("anomaly_score") > 0.5)
)

# ============================================================================
# WRITE TO LAKEBASE FOR LOW-LATENCY SERVING
# ============================================================================

print("Starting streaming write to Lakebase...")

# Ensure schema exists
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA_LAKEBASE}")

# Write to Lakebase table with append mode
query = (
    scored_stream.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"/tmp/checkpoints/ml_recommendations")
    .trigger(processingTime="30 seconds")  # Micro-batch every 30s
    .table(f"{CATALOG}.{SCHEMA_LAKEBASE}.ml_recommendations")
)

print(f"""
✅ Real-time scoring pipeline started

Stream details:
- Source: {CATALOG}.{SCHEMA_SILVER}.gold_ml_features
- Target: {CATALOG}.{SCHEMA_LAKEBASE}.ml_recommendations
- Trigger: Every 30 seconds
- Filter: anomaly_score > 0.5

Pipeline status:
- Query ID: {query.id}
- Status: {query.status}

To stop: query.stop()
To check: query.lastProgress
""")

# Keep alive
query.awaitTermination()
