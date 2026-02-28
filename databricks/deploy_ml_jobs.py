#!/usr/bin/env python3
"""
Automated ML Jobs Deployment
Creates all ML pipeline jobs with proper clusters and scheduling
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs
import time
import os

w = WorkspaceClient(profile="DEFAULT")

# Notebook paths in workspace (after repo/workspace import)
# Override with: export GENIE_DATABRICKS_NOTEBOOK_PATH="..."
REPO_PATH = os.getenv(
    "GENIE_DATABRICKS_NOTEBOOK_PATH",
    "/Users/pravin.varma@databricks.com/genie-at-the-edge/databricks"
)
TRAIN_NOTEBOOK = f"{REPO_PATH}/train_anomaly_detection_model"
SCORING_NOTEBOOK = f"{REPO_PATH}/realtime_scoring_pipeline"
RETRAIN_NOTEBOOK = f"{REPO_PATH}/weekly_model_retraining"

# Cluster configuration - ML Runtime 15.4 LTS
CLUSTER_CONFIG = jobs.JobCluster(
    job_cluster_key="ml_cluster",
    new_cluster=jobs.ClusterSpec(
        spark_version="15.4.x-cpu-ml-scala2.12",
        node_type_id="i3.xlarge",
        num_workers=2,
        spark_conf={
            "spark.databricks.delta.preview.enabled": "true"
        }
    )
)

print("=" * 80)
print("ML JOBS DEPLOYMENT")
print("=" * 80)
print(f"Notebook base path: {REPO_PATH}")

for nb in [TRAIN_NOTEBOOK, SCORING_NOTEBOOK, RETRAIN_NOTEBOOK]:
    try:
        w.workspace.get_status(nb)
        print(f"  ✓ Found notebook: {nb}")
    except Exception:
        print(f"  ⚠ Notebook not found: {nb}")

def create_or_update_job(job_name, task_config, schedule=None, continuous=False):
    """Create or update a Databricks job"""
    print(f"\n[Job: {job_name}]")
    
    # Check if job exists
    existing_jobs = w.jobs.list(name=job_name)
    existing_job_id = None
    
    for job in existing_jobs:
        if job.settings.name == job_name:
            existing_job_id = job.job_id
            print(f"  ✅ Found existing job: {existing_job_id}")
            break
    
    # Job settings
    job_settings = jobs.JobSettings(
        name=job_name,
        job_clusters=[CLUSTER_CONFIG],
        tasks=[task_config],
        timeout_seconds=0 if continuous else 7200,  # No timeout for continuous
        max_concurrent_runs=1
    )
    
    if schedule:
        job_settings.schedule = schedule
    
    if continuous:
        job_settings.continuous = jobs.Continuous(pause_status="UNPAUSED")
    
    try:
        if existing_job_id:
            # Update existing job
            w.jobs.update(
                job_id=existing_job_id,
                new_settings=job_settings
            )
            print(f"  ✅ Job updated: {existing_job_id}")
            return existing_job_id
        else:
            # Create new job
            response = w.jobs.create(
                name=job_name,
                job_clusters=[CLUSTER_CONFIG],
                tasks=[task_config],
                timeout_seconds=job_settings.timeout_seconds,
                max_concurrent_runs=1,
                schedule=schedule,
                continuous=job_settings.continuous if continuous else None
            )
            print(f"  ✅ Job created: {response.job_id}")
            return response.job_id
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

# ============================================================================
# JOB 1: Initial ML Training (Run once)
# ============================================================================

print("\n" + "=" * 80)
print("[1/3] INITIAL ML MODEL TRAINING")
print("=" * 80)

train_task = jobs.Task(
    task_key="train_model",
    job_cluster_key="ml_cluster",
    notebook_task=jobs.NotebookTask(
        notebook_path=TRAIN_NOTEBOOK,
        base_parameters={}
    ),
    timeout_seconds=3600
)

train_job_id = create_or_update_job(
    job_name="ml_anomaly_detection_initial_training",
    task_config=train_task,
    schedule=None,
    continuous=False
)

if train_job_id:
    print(f"\n  ℹ️  To run initial training:")
    print(f"     databricks jobs run-now --job-id {train_job_id}")

# ============================================================================
# JOB 2: Real-time Scoring Pipeline (Continuous)
# ============================================================================

print("\n" + "=" * 80)
print("[2/3] REAL-TIME SCORING PIPELINE (CONTINUOUS)")
print("=" * 80)

scoring_task = jobs.Task(
    task_key="realtime_scoring",
    job_cluster_key="ml_cluster",
    notebook_task=jobs.NotebookTask(
        notebook_path=SCORING_NOTEBOOK,
        base_parameters={}
    )
)

scoring_job_id = create_or_update_job(
    job_name="ml_realtime_scoring_continuous",
    task_config=scoring_task,
    schedule=None,
    continuous=True
)

if scoring_job_id:
    print(f"\n  ℹ️  Continuous job will start automatically")
    print(f"     Or run manually: databricks jobs run-now --job-id {scoring_job_id}")

# ============================================================================
# JOB 3: Weekly Model Retraining (Scheduled)
# ============================================================================

print("\n" + "=" * 80)
print("[3/3] WEEKLY MODEL RETRAINING (SCHEDULED)")
print("=" * 80)

retrain_task = jobs.Task(
    task_key="retrain_model",
    job_cluster_key="ml_cluster",
    notebook_task=jobs.NotebookTask(
        notebook_path=RETRAIN_NOTEBOOK,
        base_parameters={}
    ),
    timeout_seconds=3600
)

# Schedule: Every Sunday at 2 AM PST
weekly_schedule = jobs.CronSchedule(
    quartz_cron_expression="0 0 2 ? * SUN",
    timezone_id="America/Los_Angeles",
    pause_status="UNPAUSED"
)

retrain_job_id = create_or_update_job(
    job_name="ml_weekly_retraining",
    task_config=retrain_task,
    schedule=weekly_schedule,
    continuous=False
)

if retrain_job_id:
    print(f"\n  ℹ️  Scheduled: Every Sunday 2 AM PST")
    print(f"     Test run: databricks jobs run-now --job-id {retrain_job_id}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("✅ ML JOBS DEPLOYMENT COMPLETE")
print("=" * 80)
print(f"""
Jobs Created:

1. Initial Training (Run once)
   ID: {train_job_id}
   Purpose: Train first version of anomaly detection model
   Trigger: Manual
   Runtime: ~15 minutes
   
2. Real-time Scoring (Continuous)
   ID: {scoring_job_id}
   Purpose: Stream ML inference on gold features
   Trigger: Continuous (always running)
   Latency: 30-second micro-batches
   
3. Weekly Retraining (Scheduled)
   ID: {retrain_job_id}
   Purpose: Retrain with operator feedback
   Trigger: Every Sunday 2 AM PST
   Runtime: ~20 minutes

Cluster Configuration:
- Spark Version: 15.4.x ML Runtime
- Node Type: i3.xlarge
- Workers: 2

Next Steps:
1. Run initial training job to create @champion model:
   databricks jobs run-now --job-id {train_job_id}
   
2. Wait for training to complete (~15 min)
   
3. Real-time scoring will start automatically after deployment
   
4. Monitor jobs:
   https://e2-demo-field-eng.cloud.databricks.com/#job/list
""")
