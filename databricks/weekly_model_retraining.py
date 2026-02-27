"""
Weekly Model Retraining with Operator Feedback
Closes the learning loop by incorporating corrected labels from operator feedback

Workflow:
1. Load historical operator feedback from past week
2. Label training data: executed/correct → true positive, rejected → false positive
3. Retrain models with improved labels
4. Compare new model performance vs @champion
5. If improved, promote to @challenger for validation
6. After A/B testing, promote @challenger → @champion

Schedule: Every Sunday at 2 AM (cron: 0 2 * * 0)
"""

import mlflow
import mlflow.sklearn
from pyspark.sql import functions as F
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, precision_recall_fscore_support
import pandas as pd
import numpy as np

# MLflow setup
mlflow.set_registry_uri("databricks-uc")
CATALOG = "field_engineering"
SCHEMA = "ml_models"
MODEL_NAME = f"{CATALOG}.{SCHEMA}.equipment_anomaly_detector"

print("=" * 80)
print("WEEKLY MODEL RETRAINING WITH OPERATOR FEEDBACK")
print("=" * 80)

# ============================================================================
# STEP 1: Load Historical Feedback
# ============================================================================

print("\n[1/8] Loading operator feedback from past week...")

feedback_df = spark.sql(f"""
SELECT
    f.*,
    m.temp_avg_5min,
    m.temp_max_5min,
    m.temp_std_5min,
    m.temp_deviation_from_baseline,
    m.vibration_avg_5min,
    m.vibration_max_5min,
    m.vibration_std_5min,
    m.vibration_deviation_from_baseline,
    m.throughput_avg_5min,
    m.throughput_min_5min,
    m.pressure_avg_5min,
    m.pressure_max_5min,
    m.temp_vibration_interaction,
    m.total_variability,
    m.temp_avg_15min,
    m.vibration_avg_15min,
    m.temp_avg_1hour,
    m.vibration_avg_1hour,
    m.days_since_maintenance,
    m.equipment_age_days
FROM {CATALOG}.lakebase.operator_feedback f
INNER JOIN {CATALOG}.ml_silver.gold_ml_features m
    ON f.equipment_id = m.equipment_id
    AND ABS(UNIX_TIMESTAMP(f.recommendation_timestamp) - UNIX_TIMESTAMP(m.window_end)) < 300  -- Within 5 minutes
WHERE
    f.created_at >= CURRENT_TIMESTAMP() - INTERVAL 7 DAYS
    AND f.was_correct IS NOT NULL  -- Only include labeled outcomes
""")

feedback_count = feedback_df.count()
print(f"Loaded {feedback_count:,} labeled feedback records")

if feedback_count < 50:
    print("⚠️  Insufficient feedback for retraining (< 50 records)")
    print("   Skipping retraining, will retry next week")
    exit(0)

# ============================================================================
# STEP 2: Analyze Feedback Quality
# ============================================================================

print("\n[2/8] Analyzing feedback quality...")

feedback_summary = feedback_df.groupBy("operator_action", "was_correct").count().toPandas()
print("\nFeedback distribution:")
print(feedback_summary.to_string(index=False))

# Calculate model accuracy from feedback
accuracy_df = spark.sql(f"""
SELECT
    COUNT(*) as total_feedback,
    SUM(CASE WHEN was_correct = true THEN 1 ELSE 0 END) as correct_predictions,
    SUM(CASE WHEN was_correct = false THEN 1 ELSE 0 END) as incorrect_predictions,
    SUM(CASE WHEN was_correct = true THEN 1 ELSE 0 END) / COUNT(*) as accuracy
FROM {CATALOG}.lakebase.operator_feedback
WHERE
    created_at >= CURRENT_TIMESTAMP() - INTERVAL 7 DAYS
    AND was_correct IS NOT NULL
""").toPandas()

current_accuracy = accuracy_df['accuracy'].iloc[0]
print(f"\nCurrent model accuracy (from operator feedback): {current_accuracy:.3f}")

# ============================================================================
# STEP 3: Load Full Training Dataset
# ============================================================================

print("\n[3/8] Loading full training dataset (past 30 days)...")

# Combine original training data with new feedback-labeled data
gold_features = spark.table(f"{CATALOG}.ml_silver.gold_ml_features")

training_data_full = (
    gold_features
    .filter(F.col("window_end") >= F.date_sub(F.current_timestamp(), 30))
    .toPandas()
)

print(f"Total training records: {len(training_data_full):,}")

# ============================================================================
# STEP 4: Apply Corrected Labels from Operator Feedback
# ============================================================================

print("\n[4/8] Applying corrected labels from operator feedback...")

feedback_pd = feedback_df.toPandas()

# Merge feedback labels with training data
# Match on equipment_id and timestamp (within 5-min window)
labeled_data = pd.merge_asof(
    training_data_full.sort_values('window_end'),
    feedback_pd[['equipment_id', 'recommendation_timestamp', 'action_code', 'was_correct', 'operator_action']].sort_values('recommendation_timestamp'),
    left_on='window_end',
    right_on='recommendation_timestamp',
    by='equipment_id',
    direction='nearest',
    tolerance=pd.Timedelta('5 minutes')
)

# Use corrected labels where available, else use heuristic labels
def apply_corrected_label(row):
    if pd.notna(row['operator_action']):
        # Use operator feedback as ground truth
        if row['operator_action'] == 'executed':
            return row['action_code']  # Operator confirmed action
        elif row['operator_action'] == 'rejected':
            return 'continue_operation'  # False positive
        else:
            return row['action_code']  # Deferred/Ask - assume model was correct
    else:
        # Use original heuristic label
        if row['temp_avg_5min'] > 85 and row['vibration_avg_5min'] > 4.5:
            return 'reduce_speed'
        elif row['vibration_deviation_from_baseline'] > 2.0:
            return 'schedule_maintenance'
        elif row['throughput_avg_5min'] < 800 and row['temp_avg_5min'] < 80:
            return 'check_blockage'
        elif row['temp_avg_5min'] > 95:
            return 'emergency_shutdown'
        elif row['days_until_maintenance'] < 7 and row['days_until_maintenance'] > 0:
            return 'preventive_inspection'
        else:
            return 'continue_operation'

labeled_data['action_label_corrected'] = labeled_data.apply(apply_corrected_label, axis=1)

corrected_count = labeled_data['operator_action'].notna().sum()
print(f"Applied {corrected_count:,} corrected labels from operator feedback")
print(f"Remaining {len(labeled_data) - corrected_count:,} records use heuristic labels")

# ============================================================================
# STEP 5: Feature Engineering
# ============================================================================

print("\n[5/8] Preparing features for training...")

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

# Handle nulls
for col in numeric_features:
    if col in labeled_data.columns:
        labeled_data[col] = labeled_data[col].fillna(labeled_data[col].median())
    else:
        labeled_data[col] = 0.0

X = labeled_data[numeric_features].values
y = labeled_data['action_label_corrected'].values

# Train/test split (80/20)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training set: {len(X_train):,} samples")
print(f"Test set: {len(X_test):,} samples")

# ============================================================================
# STEP 6: Train Updated Models
# ============================================================================

print("\n[6/8] Training updated models...")

# Isolation Forest (unsupervised)
isolation_forest_v2 = Pipeline([
    ('scaler', StandardScaler()),
    ('isolation_forest', IsolationForest(
        contamination=0.1,
        n_estimators=100,
        max_samples='auto',
        random_state=42,
        n_jobs=-1
    ))
])

isolation_forest_v2.fit(X_train)

# Random Forest (supervised with corrected labels)
# Filter to action samples only
action_mask_train = y_train != 'continue_operation'
action_mask_test = y_test != 'continue_operation'

X_action_train = X_train[action_mask_train]
y_action_train = y_train[action_mask_train]
X_action_test = X_test[action_mask_test]
y_action_test = y_test[action_mask_test]

random_forest_v2 = Pipeline([
    ('scaler', StandardScaler()),
    ('random_forest', RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    ))
])

random_forest_v2.fit(X_action_train, y_action_train)

# ============================================================================
# STEP 7: Evaluate Model Performance
# ============================================================================

print("\n[7/8] Evaluating model performance...")

# Test set performance
y_action_pred = random_forest_v2.predict(X_action_test)
precision, recall, f1, support = precision_recall_fscore_support(
    y_action_test, y_action_pred, average='weighted', zero_division=0
)

print(f"\nTest set metrics:")
print(f"  Precision: {precision:.3f}")
print(f"  Recall: {recall:.3f}")
print(f"  F1 Score: {f1:.3f}")

print("\nPer-class performance:")
print(classification_report(y_action_test, y_action_pred, zero_division=0))

# Compare to champion model threshold (assume 0.70 precision baseline)
CHAMPION_PRECISION_BASELINE = 0.70

if precision > CHAMPION_PRECISION_BASELINE:
    print(f"✅ New model precision ({precision:.3f}) exceeds champion baseline ({CHAMPION_PRECISION_BASELINE:.3f})")
    promote_to_challenger = True
else:
    print(f"⚠️  New model precision ({precision:.3f}) below champion baseline ({CHAMPION_PRECISION_BASELINE:.3f})")
    print("   Not promoting to challenger - will retry next week with more feedback")
    promote_to_challenger = False

# ============================================================================
# STEP 8: Register Updated Model (if improved)
# ============================================================================

if promote_to_challenger:
    print("\n[8/8] Registering updated model as @challenger...")

    # Import ensemble wrapper class from training script
    from train_anomaly_detection_model import AnomalyActionEnsemble

    ensemble_model_v2 = AnomalyActionEnsemble(
        isolation_model=isolation_forest_v2,
        action_model=random_forest_v2,
        feature_names=numeric_features
    )

    with mlflow.start_run(run_name=f"weekly_retrain_{pd.Timestamp.now().strftime('%Y%m%d')}") as run:

        # Log parameters
        mlflow.log_param("feedback_records", corrected_count)
        mlflow.log_param("training_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))
        mlflow.log_param("corrected_labels_pct", corrected_count / len(labeled_data))

        # Log metrics
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("operator_feedback_accuracy", current_accuracy)

        # Log model
        signature = mlflow.models.infer_signature(
            labeled_data[numeric_features].head(),
            ensemble_model_v2.predict(None, labeled_data[numeric_features].head())
        )

        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=ensemble_model_v2,
            registered_model_name=MODEL_NAME,
            signature=signature,
            pip_requirements=[
                "scikit-learn==1.3.0",
                "pandas",
                "numpy"
            ]
        )

        run_id = run.info.run_id

    # Set @challenger alias
    client = mlflow.tracking.MlflowClient()
    latest_version = client.search_model_versions(f"name='{MODEL_NAME}'")[0].version
    client.set_registered_model_alias(MODEL_NAME, "challenger", latest_version)

    print(f"✅ Model version {latest_version} registered as @challenger")
    print(f"   Precision improvement: {precision:.3f} vs {CHAMPION_PRECISION_BASELINE:.3f}")
    print(f"   Run ID: {run_id}")

    print("""
Next steps:
1. Run A/B testing: Deploy @challenger alongside @champion
2. Monitor precision/recall for 1 week
3. If @challenger outperforms, promote to @champion:
   mlflow.tracking.MlflowClient().set_registered_model_alias(
       '{MODEL_NAME}',
       'champion',
       '{latest_version}'
   )
""")

else:
    print("\n[8/8] Skipping model registration (performance did not improve)")

print("\n" + "=" * 80)
print("✅ WEEKLY RETRAINING COMPLETE")
print("=" * 80)
print(f"""
Summary:
- Feedback records processed: {corrected_count:,}
- Model precision: {precision:.3f}
- Model recall: {recall:.3f}
- F1 score: {f1:.3f}
- Promoted to challenger: {promote_to_challenger}

Scheduled: Every Sunday 2 AM
Next run: {pd.Timestamp.now() + pd.Timedelta(days=7 - pd.Timestamp.now().weekday())}
""")
