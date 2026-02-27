"""
Anomaly Detection & Predictive Maintenance Model Training
Ensemble: Isolation Forest + Random Forest

Architecture:
- Isolation Forest: Unsupervised anomaly scoring (0-1 scale)
- Random Forest: Supervised action classification (trained on operator feedback)
- Outputs: anomaly_score, action_code, confidence, recommendation_text

Model Registration:
- MLflow tracking with auto-logging
- Unity Catalog model registry: field_engineering.ml_models.equipment_anomaly_detector
- Serving endpoint for real-time inference
"""

import mlflow
import mlflow.sklearn
from databricks import feature_engineering
from databricks.feature_engineering import FeatureEngineeringClient
from pyspark.sql import functions as F
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import pandas as pd
import numpy as np

# MLflow setup
mlflow.set_registry_uri("databricks-uc")
CATALOG = "field_engineering"
SCHEMA = "ml_models"
MODEL_NAME = f"{CATALOG}.{SCHEMA}.equipment_anomaly_detector"

# Feature store client
fe = FeatureEngineeringClient()

# ============================================================================
# STEP 1: Load Training Data from Gold Layer
# ============================================================================

print("=" * 80)
print("LOADING ML FEATURES FROM GOLD LAYER")
print("=" * 80)

# For initial training, simulate historical labeled data
# In production, this comes from operator_feedback table
gold_features = spark.table(f"{CATALOG}.ml_silver.gold_ml_features")

# Sample recent data for training (last 7 days)
training_data = (
    gold_features
    .filter(F.col("window_end") >= F.date_sub(F.current_timestamp(), 7))
    .toPandas()
)

print(f"Loaded {len(training_data):,} feature records for training")
print(f"Equipment IDs: {training_data['equipment_id'].nunique()}")
print(f"Time range: {training_data['window_end'].min()} to {training_data['window_end'].max()}")

# ============================================================================
# STEP 2: Feature Engineering for ML
# ============================================================================

print("\n" + "=" * 80)
print("FEATURE ENGINEERING")
print("=" * 80)

# Select numeric features for anomaly detection
numeric_features = [
    'temp_avg_5min', 'temp_max_5min', 'temp_std_5min', 'temp_deviation_from_baseline',
    'vibration_avg_5min', 'vibration_max_5min', 'vibration_std_5min', 'vibration_deviation_from_baseline',
    'throughput_avg_5min', 'throughput_min_5min',
    'pressure_avg_5min', 'pressure_max_5min',
    'temp_vibration_interaction', 'total_variability',
    'temp_avg_15min', 'vibration_avg_15min',
    'temp_avg_1hour', 'vibration_avg_1hour',
    'days_since_maintenance', 'equipment_age_days'
]

# Handle nulls (fill with median)
for col in numeric_features:
    if col in training_data.columns:
        training_data[col] = training_data[col].fillna(training_data[col].median())
    else:
        training_data[col] = 0.0  # Default if column missing

X_train = training_data[numeric_features].values

print(f"Feature matrix shape: {X_train.shape}")
print(f"Features: {len(numeric_features)}")

# ============================================================================
# STEP 3: Train Isolation Forest (Unsupervised Anomaly Detection)
# ============================================================================

print("\n" + "=" * 80)
print("TRAINING ISOLATION FOREST")
print("=" * 80)

# Isolation Forest pipeline with scaling
isolation_forest_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('isolation_forest', IsolationForest(
        contamination=0.1,  # Expect 10% anomalies
        n_estimators=100,
        max_samples='auto',
        random_state=42,
        n_jobs=-1
    ))
])

isolation_forest_pipeline.fit(X_train)

# Generate anomaly scores (-1 = anomaly, 1 = normal)
# Convert to 0-1 scale (0 = normal, 1 = anomaly)
anomaly_predictions = isolation_forest_pipeline.predict(X_train)
anomaly_scores_raw = isolation_forest_pipeline.decision_function(X_train)

# Normalize to 0-1 range (higher = more anomalous)
anomaly_scores = 1 - (anomaly_scores_raw - anomaly_scores_raw.min()) / (anomaly_scores_raw.max() - anomaly_scores_raw.min())

training_data['anomaly_score'] = anomaly_scores
training_data['is_anomaly'] = (anomaly_predictions == -1).astype(int)

print(f"Anomalies detected: {training_data['is_anomaly'].sum():,} ({100*training_data['is_anomaly'].mean():.1f}%)")
print(f"Anomaly score range: {anomaly_scores.min():.3f} - {anomaly_scores.max():.3f}")
print(f"Mean anomaly score: {anomaly_scores.mean():.3f}")

# ============================================================================
# STEP 4: Generate Synthetic Operator Labels (Initial Training)
# ============================================================================

print("\n" + "=" * 80)
print("GENERATING SYNTHETIC OPERATOR FEEDBACK")
print("=" * 80)

"""
In production, these labels come from operator_feedback table
For initial training, simulate based on anomaly patterns and thresholds
"""

def generate_action_label(row):
    """
    Simulate operator decision based on sensor patterns
    In production: SELECT action_taken FROM operator_feedback WHERE ...
    """
    # High temperature + high vibration = reduce speed
    if row['temp_avg_5min'] > 85 and row['vibration_avg_5min'] > 4.5:
        return 'reduce_speed'

    # High vibration deviation = schedule maintenance
    elif row['vibration_deviation_from_baseline'] > 2.0:
        return 'schedule_maintenance'

    # Low throughput + normal sensors = check blockage
    elif row['throughput_avg_5min'] < 800 and row['temp_avg_5min'] < 80:
        return 'check_blockage'

    # Critical temperature = emergency shutdown
    elif row['temp_avg_5min'] > 95:
        return 'emergency_shutdown'

    # Approaching maintenance window = preventive inspection
    elif row['days_until_maintenance'] < 7 and row['days_until_maintenance'] > 0:
        return 'preventive_inspection'

    # Normal operation
    else:
        return 'continue_operation'

# Apply labeling logic
training_data['action_label'] = training_data.apply(generate_action_label, axis=1)

print("Action distribution:")
print(training_data['action_label'].value_counts())

# ============================================================================
# STEP 5: Train Random Forest Classifier (Action Recommendation)
# ============================================================================

print("\n" + "=" * 80)
print("TRAINING RANDOM FOREST ACTION CLASSIFIER")
print("=" * 80)

# Train on anomalous cases only (where operator took action)
action_training_data = training_data[training_data['action_label'] != 'continue_operation'].copy()

X_action = action_training_data[numeric_features].values
y_action = action_training_data['action_label'].values

print(f"Action training samples: {len(X_action):,}")
print(f"Action classes: {len(np.unique(y_action))}")

# Random Forest pipeline
random_forest_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('random_forest', RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'  # Handle imbalanced actions
    ))
])

random_forest_pipeline.fit(X_action, y_action)

# Evaluate on training data (in production, use holdout set)
train_accuracy = random_forest_pipeline.score(X_action, y_action)
print(f"Training accuracy: {train_accuracy:.3f}")

# ============================================================================
# STEP 6: Create Ensemble Wrapper Model
# ============================================================================

print("\n" + "=" * 80)
print("CREATING ENSEMBLE WRAPPER")
print("=" * 80)

class AnomalyActionEnsemble(mlflow.pyfunc.PythonModel):
    """
    Ensemble wrapper combining Isolation Forest + Random Forest

    Inputs: Feature vector (20 numeric features)
    Outputs: {
        'anomaly_score': 0.0-1.0,
        'is_anomaly': bool,
        'action_code': str,
        'confidence': 0.0-1.0,
        'recommendation_text': str
    }
    """

    def __init__(self, isolation_model, action_model, feature_names):
        self.isolation_model = isolation_model
        self.action_model = action_model
        self.feature_names = feature_names

        self.action_text_map = {
            'reduce_speed': 'Reduce equipment speed to 60% and monitor temperature for 30 minutes',
            'schedule_maintenance': 'Schedule bearing inspection within 24 hours - elevated vibration detected',
            'check_blockage': 'Check for material blockage - throughput below normal with stable sensors',
            'emergency_shutdown': 'CRITICAL: Emergency shutdown required - temperature exceeded safe limits',
            'preventive_inspection': 'Schedule preventive inspection - approaching maintenance window',
            'continue_operation': 'Continue normal operation - all sensors within expected range'
        }

    def predict(self, context, model_input):
        """
        Score incoming sensor features
        """
        # Ensure input is DataFrame
        if isinstance(model_input, pd.DataFrame):
            X = model_input[self.feature_names].values
        else:
            X = model_input

        # Step 1: Anomaly detection
        anomaly_raw_scores = self.isolation_model.decision_function(X)
        anomaly_scores = 1 - (anomaly_raw_scores - anomaly_raw_scores.min()) / (
            anomaly_raw_scores.max() - anomaly_raw_scores.min() + 1e-10)
        is_anomaly = (self.isolation_model.predict(X) == -1)

        # Step 2: Action recommendation (only for anomalies above threshold)
        results = []

        for i, (score, is_anom) in enumerate(zip(anomaly_scores, is_anomaly)):
            if score > 0.7:  # High anomaly score threshold
                # Predict action and get confidence
                action_proba = self.action_model.predict_proba(X[i:i+1])
                action_code = self.action_model.predict(X[i:i+1])[0]
                confidence = action_proba.max()

                # Get human-readable text
                recommendation_text = self.action_text_map.get(
                    action_code,
                    f"Action {action_code} recommended"
                )
            else:
                # Normal operation
                action_code = 'continue_operation'
                confidence = 1.0 - score  # Inverse of anomaly score
                recommendation_text = self.action_text_map['continue_operation']

            results.append({
                'anomaly_score': float(score),
                'is_anomaly': bool(is_anom),
                'action_code': action_code,
                'confidence': float(confidence),
                'recommendation_text': recommendation_text
            })

        return pd.DataFrame(results)

# Instantiate ensemble
ensemble_model = AnomalyActionEnsemble(
    isolation_model=isolation_forest_pipeline,
    action_model=random_forest_pipeline,
    feature_names=numeric_features
)

# ============================================================================
# STEP 7: Log Model to MLflow with Unity Catalog
# ============================================================================

print("\n" + "=" * 80)
print("LOGGING MODEL TO MLFLOW")
print("=" * 80)

# Create schema if not exists
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

with mlflow.start_run(run_name="anomaly_detection_v1") as run:

    # Log parameters
    mlflow.log_param("contamination", 0.1)
    mlflow.log_param("n_estimators_isolation", 100)
    mlflow.log_param("n_estimators_rf", 200)
    mlflow.log_param("training_samples", len(training_data))
    mlflow.log_param("features_count", len(numeric_features))
    mlflow.log_param("anomaly_threshold", 0.7)

    # Log metrics
    mlflow.log_metric("anomalies_detected", training_data['is_anomaly'].sum())
    mlflow.log_metric("anomaly_rate", training_data['is_anomaly'].mean())
    mlflow.log_metric("action_classifier_accuracy", train_accuracy)

    # Log model artifacts
    signature = mlflow.models.infer_signature(
        training_data[numeric_features].head(),
        ensemble_model.predict(None, training_data[numeric_features].head())
    )

    mlflow.pyfunc.log_model(
        artifact_path="model",
        python_model=ensemble_model,
        registered_model_name=MODEL_NAME,
        signature=signature,
        pip_requirements=[
            "scikit-learn==1.3.0",
            "pandas",
            "numpy"
        ]
    )

    run_id = run.info.run_id

print(f"✅ Model logged to MLflow")
print(f"   Run ID: {run_id}")
print(f"   Model name: {MODEL_NAME}")

# ============================================================================
# STEP 8: Set Model Alias for Production
# ============================================================================

print("\n" + "=" * 80)
print("SETTING MODEL ALIAS")
print("=" * 80)

# Get latest version
client = mlflow.tracking.MlflowClient()
latest_version = client.search_model_versions(f"name='{MODEL_NAME}'")[0].version

# Set @champion alias
client.set_registered_model_alias(MODEL_NAME, "champion", latest_version)

print(f"✅ Model version {latest_version} set as @champion")
print(f"   Load with: mlflow.pyfunc.load_model('models:/{MODEL_NAME}@champion')")

# ============================================================================
# STEP 9: Test Inference
# ============================================================================

print("\n" + "=" * 80)
print("TESTING MODEL INFERENCE")
print("=" * 80)

# Load model via alias
loaded_model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")

# Test on sample
test_sample = training_data[numeric_features].head(5)
predictions = loaded_model.predict(test_sample)

print("Sample predictions:")
print(predictions.to_string(index=False))

print("\n" + "=" * 80)
print("✅ MODEL TRAINING COMPLETE")
print("=" * 80)
print(f"""
Next steps:
1. Deploy real-time scoring pipeline: python databricks/deploy_scoring_pipeline.py
2. Create Lakebase serving tables: python databricks/setup_lakebase_serving.py
3. Configure Ignition webhook integration
4. Set up operator feedback loop for continuous learning
""")
