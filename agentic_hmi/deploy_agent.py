#!/usr/bin/env python3
"""
Deploy Operations Agent to Databricks as a Job
Workstream 4.3: Deploy Agent
"""

import json
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

def deploy_agent():
    """Deploy operations agent as Databricks Job"""

    w = WorkspaceClient()

    # Upload the agent script to workspace
    print("Uploading agent script to Databricks workspace...")

    agent_code = open('operations_agent.py', 'r').read()

    # Write to workspace
    workspace_path = "/Workspace/Users/current/agentic_hmi/operations_agent.py"
    w.workspace.upload(
        workspace_path,
        agent_code.encode('utf-8'),
        overwrite=True
    )

    print(f"Agent script uploaded to {workspace_path}")

    # Create job configuration
    job_config = {
        "name": "AgenticHMI_OperationsAgent",
        "description": "Continuous monitoring agent for equipment anomalies and recommendations",
        "tasks": [
            {
                "task_key": "operations_agent",
                "description": "Main monitoring loop",
                "python_file": {
                    "path": workspace_path
                },
                "new_cluster": {
                    "spark_version": "13.3.x-scala2.12",
                    "node_type_id": "i3.xlarge",
                    "num_workers": 0,  # Single node for agent
                    "spark_conf": {
                        "spark.databricks.delta.preview.enabled": "true"
                    }
                },
                "libraries": [
                    {"pypi": {"package": "databricks-sdk==0.35.0"}},
                    {"pypi": {"package": "databricks-sql-connector==3.5.0"}}
                ],
                "timeout_seconds": 0,  # No timeout - runs continuously
                "max_retries": -1,  # Unlimited retries
                "retry_on_timeout": True
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 */5 * * * ?",  # Every 5 minutes
            "timezone_id": "UTC"
        },
        "max_concurrent_runs": 1,
        "email_notifications": {
            "on_failure": ["admin@company.com"],
            "no_alert_for_skipped_runs": True
        }
    }

    # Create the job
    print("Creating Databricks Job...")

    try:
        job = w.jobs.create(**job_config)
        print(f"✅ Job created successfully with ID: {job.job_id}")
        print(f"View job at: {w.config.host}/#job/{job.job_id}")

        # Run the job immediately
        print("Starting job run...")
        run = w.jobs.run_now(job_id=job.job_id)
        print(f"Job run started with ID: {run.run_id}")
        print(f"View run at: {w.config.host}/#job/{job.job_id}/run/{run.run_id}")

        return job.job_id

    except Exception as e:
        print(f"❌ Error creating job: {e}")
        return None

def check_job_status(job_id):
    """Check status of deployed job"""
    w = WorkspaceClient()

    try:
        job = w.jobs.get(job_id=job_id)
        print(f"\nJob Status for {job.settings.name}:")
        print(f"  State: {job.state}")

        # Get latest run
        runs = w.jobs.list_runs(job_id=job_id, limit=1)
        for run in runs:
            print(f"  Latest Run: {run.run_id}")
            print(f"    State: {run.state.life_cycle_state}")
            print(f"    Result: {run.state.result_state if run.state.result_state else 'Running'}")

    except Exception as e:
        print(f"Error checking job status: {e}")

if __name__ == "__main__":
    job_id = deploy_agent()
    if job_id:
        print("\n" + "="*60)
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("="*60)
        print(f"Agent is now running as Databricks Job ID: {job_id}")
        print("\nNext steps:")
        print("1. Monitor job runs in Databricks UI")
        print("2. Check agent_recommendations table for new entries")
        print("3. Run integration test: python test_integration.py")

        # Check status
        check_job_status(job_id)