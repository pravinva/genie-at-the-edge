# Quick Start: Deploying Agentic HMI Views to Ignition

## 5-Minute Setup

### 1. Prerequisites Check
```bash
# Verify you have:
- Ignition gateway access (admin credentials)
- Databricks workspace access
- Three JSON files:
  ✓ agent_recommendations_view.json
  ✓ recommendation_card.json
  ✓ execution_tracker_view.json
```

### 2. Create Lakebase Connection (2 minutes)

**In Ignition Gateway Web Interface**:
1. Navigate to `http://[gateway-ip]:8088`
2. Go to **Configure → Database Connections**
3. Click **Create new Database Connection**
4. Fill in:
   ```
   Name: Lakebase_Connection
   Driver: PostgreSQL
   URL: jdbc:postgresql://[workspace].cloud.databricks.com:5432/lakebase
   Username: token
   Password: [Your Databricks PAT]
   ```
5. Click **Test Connection** (should show "Success")
6. Click **Save**

### 3. Create Named Queries (2 minutes)

**In Ignition Designer**:
1. Open your project
2. Go to **Project → Databases → Named Queries**
3. Click **Create New Named Query**
4. Create 4 queries (copy/paste SQL below):

**Query 1: approveRecommendation**
```sql
UPDATE agent_recommendations
SET status = 'approved', operator_id = :operator_id, approved_timestamp = CURRENT_TIMESTAMP
WHERE recommendation_id = :recommendation_id
```

**Query 2: deferRecommendation**
```sql
UPDATE agent_recommendations
SET status = 'deferred', defer_until = CURRENT_TIMESTAMP + INTERVAL '1 HOUR'
WHERE recommendation_id = :recommendation_id
```

**Query 3: rejectRecommendation**
```sql
UPDATE agent_recommendations
SET status = 'rejected', rejection_reason = :rejection_reason, rejected_timestamp = CURRENT_TIMESTAMP
WHERE recommendation_id = :recommendation_id
```

**Query 4: countPendingRecommendations**
```sql
SELECT COUNT(*) as count FROM agent_recommendations WHERE status = 'pending'
```

### 4. Import Views (1 minute)

**In Ignition Designer**:
1. Right-click on project name → **Import Project Resource**
2. Click **Browse...** and select `agent_recommendations_view.json`
3. Choose target folder: `views/agent/` (create if needed)
4. Click **Import**
5. Repeat for other 2 JSON files:
   - `recommendation_card.json` → `components/`
   - `execution_tracker_view.json` → `views/agent/`

**Or Direct File Copy**:
```bash
# Copy files directly to project directory
cp agent_recommendations_view.json ~/Ignition/projects/AgenticHMI/views/
cp recommendation_card.json ~/Ignition/projects/AgenticHMI/components/
cp execution_tracker_view.json ~/Ignition/projects/AgenticHMI/views/
```

### 5. Test Views

**In Perspective Client**:
1. Navigate to view: `/[ProjectName]/agent/AgentRecommendations`
2. Should show empty state: "No Pending Recommendations"
3. Insert test data in Lakebase:
   ```sql
   -- Connect to Lakebase and run:
   INSERT INTO agent_recommendations
   (recommendation_id, equipment_id, issue_description, recommended_action,
    severity, confidence_score, created_timestamp, status, priority)
   VALUES
   ('test-rec-001', 'REACTOR_01', 'Temperature above threshold',
    'Reduce feed rate 10%', 'high', 0.87, CURRENT_TIMESTAMP, 'pending', 1)
   ```
4. View should refresh within 2 seconds and show the recommendation
5. Try clicking **Approve** button - should show confirmation dialog

## Minimal Configuration

### Required Tables (SQL)
```sql
-- Create minimal schema for testing
CREATE TABLE agent_recommendations (
    recommendation_id STRING PRIMARY KEY,
    equipment_id STRING,
    issue_description STRING,
    recommended_action STRING,
    severity STRING,
    confidence_score DOUBLE,
    created_timestamp TIMESTAMP,
    status STRING,
    priority INT,
    operator_id STRING,
    approved_timestamp TIMESTAMP,
    rejection_reason STRING,
    rejected_timestamp TIMESTAMP,
    defer_until TIMESTAMP
);

CREATE TABLE agent_commands (
    command_id STRING PRIMARY KEY,
    equipment_id STRING,
    tag_path STRING,
    old_value STRING,
    new_value STRING,
    status STRING,
    created_timestamp TIMESTAMP,
    started_timestamp TIMESTAMP,
    completed_timestamp TIMESTAMP,
    execution_result STRING
);
```

### Minimal Ignition Configuration
| Setting | Value |
|---------|-------|
| Database Connection | Lakebase_Connection |
| Driver | PostgreSQL |
| Schema | public (default) |
| Table Prefix | None |
| Poll Interval | 2000ms (recommendations), 1000ms (execution) |

## Troubleshooting

### "No database connection named 'Lakebase_Connection'"
- Go to Gateway Configure → Database Connections
- Verify connection exists and is tested
- Restart gateway if just created

### Views show empty/no data
- Check if tables exist in Lakebase:
  ```sql
  SELECT * FROM agent_recommendations LIMIT 1;
  ```
- Verify connection permissions:
  ```sql
  GRANT SELECT ON agent_recommendations TO token;
  ```

### Buttons don't work
- Check Designer console for JavaScript errors
- Verify named queries exist and are accessible
- Test named query manually in Designer

### Slow performance
- Check network latency to Databricks
- Verify Lakebase cluster is running
- Add database index:
  ```sql
  CREATE INDEX idx_rec_status ON agent_recommendations(status, priority);
  ```

## What Happens Next

**When Databricks Agent Runs**:
1. Agent detects equipment anomaly
2. Calls Genie AI for analysis
3. Inserts into `agent_recommendations` table
4. View auto-refreshes (2-second poll)
5. Recommendation appears on screen

**When Operator Approves**:
1. Updates status to 'approved'
2. Records operator_id and timestamp
3. Agent sees approval
4. Creates command
5. Executes command via Ignition API
6. Updates tag value

**Real-Time Monitoring**:
- Open Execution Tracker view
- Watch commands stream in live
- See elapsed time update in real-time

## Files Summary

| File | Purpose | Lines | Bindings |
|------|---------|-------|----------|
| agent_recommendations_view.json | Main recommendations panel | 550+ | 4 queries |
| recommendation_card.json | Reusable card component | 380+ | Built-in |
| execution_tracker_view.json | Live command monitor | 420+ | 3 queries |

## Next Steps

1. **Integrate with Agent**: Point Databricks agent to insert into tables
2. **Configure Tag Writeback**: Set up Ignition gateway script to execute commands
3. **Add Monitoring**: Create dashboard with health metrics
4. **Load Test**: Insert 100+ recommendations and verify performance
5. **Go Live**: Deploy to production Ignition instance

## Support

For issues or customization needs, refer to `PERSPECTIVE_VIEWS_README.md` for detailed documentation.

---

**Estimated Setup Time**: 5-10 minutes
**Success Indicator**: Approve button successfully updates database
