# Operations Agent - Quick Start Guide

## 5-Minute Setup

### 1. Configure Databricks Connection

```bash
# Option A: Using Databricks CLI (recommended)
databricks configure --token
# Enter workspace URL and personal access token when prompted

# Option B: Using environment variables
export DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
export DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
export DATABRICKS_TOKEN=your-personal-access-token
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
python setup_agent_tables.py
```

Expected output:
```
Creating agent_recommendations table...
✓ agent_recommendations table created
Creating agent_commands table...
✓ agent_commands table created
Creating agent_health table...
✓ agent_health table created
Creating sensor_data table...
✓ sensor_data table created
Creating work_orders table...
✓ work_orders table created
Creating operator_sessions table...
✓ operator_sessions table created

✓ Inserted 5 sample sensor readings
✅ All tables verified!
================================================================
Setup complete! Ready to run operations_agent.py
================================================================
```

### 4. Start the Agent

```bash
python operations_agent.py
```

Expected output:
```
[2024-02-19 10:30:45] [INFO] Initializing Operations Agent...
[2024-02-19 10:30:46] [INFO] Connected to Lakebase successfully
[2024-02-19 10:30:46] [INFO] Agent ops_agent_001 initialized successfully
[2024-02-19 10:30:47] [INFO] [STARTUP] Agent ops_agent_001 starting monitoring loop...
[2024-02-19 10:30:47] [INFO] Poll interval: 10 seconds
[2024-02-19 10:30:47] [INFO] Detecting anomalies...
[2024-02-19 10:30:47] [INFO] Processing approvals...
[2024-02-19 10:30:47] [INFO] Executing pending commands...
[2024-02-19 10:30:47] [DEBUG] Heartbeat updated for agent ops_agent_001
[2024-02-19 10:30:47] [INFO] [CYCLE COMPLETE] Duration: 0.45s, Next poll in 10s
```

Agent is now running! Proceed to next terminal for demo.

### 5. Run Demo (in another terminal)

```bash
python demo_operations_agent.py
```

Expected output:
```
======================================================================
OPERATIONS AGENT - COMPLETE DEMO
======================================================================

This demo will:
1. Insert a sensor anomaly
2. Wait for agent to detect it and create recommendation
3. Simulate operator approval
4. Wait for agent to create and execute command
5. Check agent health and print summary

Note: Ensure the operations_agent.py is running in another terminal!

======================================================================
✓ Connected to Lakebase

[STEP 1] Inserting sensor anomaly...
  Equipment: REACTOR_DEMO
  Temperature: 92.0°C (threshold: 85°C)
  ✓ Anomaly inserted

[STEP 2] Checking for recommendations...
  ✓ Found 1 pending recommendations:

    Recommendation ID: a1b2c3d4-e5f6-4g7h-8i9j-0k1l2m3n4o5p
    Equipment: REACTOR_DEMO
    Severity: high
    Action: Reduce throughput by 25% and activate cooling system
    Confidence: 90%
    Status: pending

[STEP 3] Approving recommendation...
  Recommendation ID: a1b2c3d4-e5f6-4g7h-8i9j-0k1l2m3n4o5p
  ✓ Recommendation approved

[STEP 4] Checking for execution commands...
  ✓ Found 1 commands:

    Command ID: c3d4e5f6-g7h8-5i9j-0k1l-2m3n4o5p6q7r
    Equipment: REACTOR_DEMO
    Tag Path: [default]REACTOR_DEMO/ThroughputSetpoint
    New Value: 75
    Action: Reduce throughput by 25% and activate cooling system
    Status: executing

[STEP 5] Checking agent health...
  ✓ Agent Status:
    Agent ID: ops_agent_001
    Last Heartbeat: 2024-02-19 10:30:47
    Status: online
    Polls Completed: 42

[SUMMARY] Agent Activity Report
======================================================================

Recommendations by status:
  pending: 0
  approved: 0
  executing: 0
  executed: 1

Commands by status:
  pending: 0
  executing: 0
  executed: 1

Command Execution:
  Total Executed: 1
  Avg Execution Time: 2.34 seconds

======================================================================

✅ DEMO COMPLETE
```

## What Just Happened?

### Timeline

| Time | Action | Component |
|------|--------|-----------|
| T+0s | Inserted sensor anomaly (92°C) | Demo Script |
| T+10s | Agent detected anomaly, created recommendation | Operations Agent |
| T+10s | Demo script approved recommendation | Demo Script |
| T+20s | Agent processed approval, created command | Operations Agent |
| T+20s | Agent executed command (reduced throughput) | Operations Agent |

### Data Flow

```
1. Demo inserts anomaly
   ↓
2. Agent detects (next 10s poll)
   ↓
3. Agent creates recommendation (pending)
   ↓
4. Demo approves recommendation
   ↓
5. Agent detects approval (next 10s poll)
   ↓
6. Agent creates command
   ↓
7. Agent executes command
   ↓
8. Agent updates status to executed
```

## Key Features Demonstrated

### 1. Anomaly Detection
- Agent continuously monitors sensor_data table
- Detects temperature > 85°C
- Creates recommendation automatically

### 2. Intelligent Recommendations
- Unique UUID for each recommendation
- Severity classification (critical/high/medium/low)
- Confidence scoring (0-1)
- Root cause analysis
- Recommended action

### 3. Approval Workflow
- Operator approves via UI or direct database update
- Timestamps track when approved
- Operator ID recorded

### 4. Command Execution
- Agent creates control commands from approved recommendations
- Maps actions to equipment tag paths
- Tracks execution status
- Updates timestamps

### 5. Health Monitoring
- Agent sends heartbeat to agent_health table
- Tracks poll count
- Enables monitoring dashboard

## Verify It Works

### Check Agent Health

```bash
# Terminal 3: Query agent status
sqlite3
.open /tmp/agentic_hmi.db

SELECT * FROM agent_health
WHERE agent_id = 'ops_agent_001'
ORDER BY last_heartbeat DESC LIMIT 1;
```

Expected:
```
agent_id  | ops_agent_001
status    | online
polls_completed | 45
last_heartbeat  | 2024-02-19 10:30:47
```

### Check Recommendations

```sql
SELECT
    recommendation_id,
    equipment_id,
    severity,
    confidence_score,
    status,
    created_timestamp
FROM agent_recommendations
ORDER BY created_timestamp DESC
LIMIT 5;
```

### Check Commands

```sql
SELECT
    command_id,
    recommendation_id,
    equipment_id,
    tag_path,
    new_value,
    status,
    created_timestamp,
    executed_timestamp
FROM agent_commands
ORDER BY created_timestamp DESC
LIMIT 5;
```

## Next Steps

### 1. Integrate with Ignition
Add Ignition write-back capability:

```python
# In operations_agent.py, update _execute_single_command():
import requests

def _execute_single_command(self, command_id, equipment_id, tag_path, new_value, action):
    # Call Ignition WebDev API
    response = requests.post(
        "https://ignition-gateway:8043/api/agent/execute",
        json={
            "tagPath": tag_path,
            "value": new_value,
            "commandId": command_id
        },
        auth=("agent_user", "password"),
        verify=False
    )

    if response.json()['success']:
        return True
    return False
```

### 2. Add Genie Integration
Enhance recommendations with AI reasoning:

```python
# Add to detect_anomalies():
def analyze_with_genie(self, equipment_id, temperature):
    prompt = f"""
    Equipment {equipment_id} temperature is {temperature}°C.
    Normal range is 70-80°C.
    What is the root cause and recommended action?
    """

    # Call Genie API
    response = genie.query(prompt)
    return response
```

### 3. Create Perspective Dashboard
Build Ignition Perspective views:
- Agent Recommendations panel (see pending)
- Execution Tracker (live commands)
- Agent Health Dashboard (status indicators)

### 4. Deploy as Databricks Job
Run agent continuously:

```bash
databricks jobs create --json '{
    "name": "AgenticHMI_OperationsAgent",
    "new_cluster": {
        "spark_version": "13.3.x-scala2.12",
        "node_type_id": "i3.xlarge",
        "num_workers": 2
    },
    "python_wheel_task": {
        "package_name": "agentic_hmi",
        "entry_point": "operations_agent"
    },
    "timeout_seconds": 0,
    "max_concurrent_runs": 1
}'
```

## Files Overview

```
genie-at-the-edge/
├── operations_agent.py          # Main agent (450+ lines)
├── setup_agent_tables.py        # Database initialization
├── demo_operations_agent.py     # Demo workflow
├── requirements.txt             # Dependencies
├── AGENT_README.md              # Detailed documentation
├── QUICKSTART.md                # This file
└── README.md                    # Project README
```

## Troubleshooting

### Agent won't connect to Databricks

```bash
# Check credentials
databricks configure --token

# Verify environment variables
echo $DATABRICKS_SERVER_HOSTNAME
echo $DATABRICKS_HTTP_PATH
echo $DATABRICKS_TOKEN
```

### No anomalies detected

```bash
# Check sensor data exists
SELECT COUNT(*) FROM sensor_data
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL 10 SECONDS;

# Verify temperature values
SELECT equipment_id, temperature, timestamp
FROM sensor_data
ORDER BY timestamp DESC LIMIT 5;
```

### No recommendations created

```bash
# Check agent is running
SELECT * FROM agent_health WHERE status = 'online';

# Check recommend table is empty
SELECT COUNT(*) FROM agent_recommendations;

# Try inserting test anomaly manually
INSERT INTO sensor_data
(sensor_id, equipment_id, temperature, pressure, flow_rate, sensor_status, timestamp)
VALUES ('TEST_SENSOR', 'TEST_EQUIP', 95.0, 100.0, 45.0, 'warning', CURRENT_TIMESTAMP);
```

### Agent crashes

- Check logs for specific error message
- Verify all tables exist
- Ensure Databricks connection is stable
- Check disk space and memory

## Support

For detailed information, see **AGENT_README.md**

Key sections:
- Architecture overview
- Workflow examples
- Configuration options
- Integration points
- Performance metrics
- Error handling

## Summary

You now have:

✅ **Production-ready Operations Agent**
- Monitors equipment continuously
- Detects anomalies automatically
- Creates intelligent recommendations
- Supports approval workflow
- Executes approved commands
- Tracks agent health

✅ **Complete Implementation**
- 450+ lines of production code
- Comprehensive error handling
- Retry logic with exponential backoff
- Full audit trail in Lakebase
- Detailed logging

✅ **Ready to Extend**
- Ignition integration (add webhook calls)
- Genie integration (add AI reasoning)
- Perspective dashboard (add UI)
- Databricks job deployment (add scheduling)

**Next: Run the agent continuously and integrate with your systems!**
