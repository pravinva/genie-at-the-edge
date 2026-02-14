# Rollback Procedures

This document provides step-by-step procedures to rollback deployments if issues occur.

## Table of Contents

1. [Overview](#overview)
2. [Rollback Strategy](#rollback-strategy)
3. [Databricks Rollback](#databricks-rollback)
4. [Ignition Rollback](#ignition-rollback)
5. [UI Rollback](#ui-rollback)
6. [Emergency Procedures](#emergency-procedures)
7. [Recovery Validation](#recovery-validation)

---

## Overview

### When to Rollback

Rollback immediately if you encounter:

- **Critical Failures**: System crashes, data corruption, security breaches
- **Performance Degradation**: >10x slower than baseline, system unresponsive
- **Data Quality Issues**: Incorrect calculations, missing data, schema errors
- **Integration Failures**: Components can't communicate, authentication failures
- **Demo Blockers**: Any issue that prevents demo from working

### Rollback Philosophy

- **Fast Rollback**: Prioritize speed over perfection
- **Partial Rollback**: Roll back only affected components
- **Preserve Data**: Never delete production data during rollback
- **Document**: Record what happened and what was rolled back

---

## Rollback Strategy

### Backup Before Deployment

Always create backups before deployment:

```bash
# Before deploying
python build/create_backup.py --environment dev

# This creates:
# - Snapshot of dimension tables
# - DLT pipeline configuration
# - Genie space configuration
# - UI artifacts
# - Ignition export (manual)
```

### Rollback Levels

**Level 1 - Configuration Only** (5 minutes)
- Revert configuration files
- Restart services
- No data changes

**Level 2 - Component Rollback** (15 minutes)
- Rollback specific component (Databricks, Ignition, or UI)
- Restore from last known good state
- Validate integration still works

**Level 3 - Full Rollback** (30 minutes)
- Rollback all components
- Restore all configurations
- Full system validation

**Level 4 - Emergency** (60+ minutes)
- Complete rebuild from scratch
- Restore from backups
- Full testing cycle

---

## Databricks Rollback

### 1. Rollback DLT Pipeline

**Symptom**: Pipeline errors, slow processing, incorrect data

**Quick Fix** (stop pipeline):
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Stop current pipeline
pipeline_id = "YOUR_PIPELINE_ID"
w.pipelines.stop(pipeline_id)
```

**Full Rollback** (restore previous version):

```bash
# 1. Get previous pipeline configuration
cat build/deployment_state_dev.json | jq '.state.dlt_pipeline_id'

# 2. Via UI:
#    - Open Databricks > Workflows > Delta Live Tables
#    - Find pipeline by ID
#    - Click "..." > Settings
#    - Revert notebook path to previous version
#    - Or delete and recreate from backup config

# 3. Restart pipeline
python -c "
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
w.pipelines.start_update('YOUR_PIPELINE_ID')
"
```

**Validation**:
```sql
-- Check pipeline is processing
SELECT MAX(timestamp) as last_update
FROM field_engineering.mining_demo.ot_telemetry_bronze;

-- Should be within last 5 minutes
```

### 2. Rollback Dimension Tables

**Symptom**: Incorrect reference data, missing equipment records

**Rollback**:
```sql
-- Drop corrupted tables
DROP TABLE IF EXISTS field_engineering.mining_demo.equipment_master;
DROP TABLE IF EXISTS field_engineering.mining_demo.equipment_types;

-- Restore from backup (if backups exist)
-- Or redeploy from source
```

Then redeploy:
```bash
python build/deploy_databricks.py --component tables --environment dev
```

**Validation**:
```sql
-- Verify row counts
SELECT 'equipment_master' as table_name, COUNT(*) as rows
FROM field_engineering.mining_demo.equipment_master
UNION ALL
SELECT 'equipment_types', COUNT(*)
FROM field_engineering.mining_demo.equipment_types;

-- Expected:
-- equipment_master: 15 rows
-- equipment_types: 3 rows
```

### 3. Rollback Genie Space

**Symptom**: Genie gives incorrect answers, errors on queries

**Rollback**:

1. **Via UI**:
   - Open Databricks > AI & ML > Genie
   - Find "Mining Operations Intelligence" space
   - Settings > Delete (if completely broken)
   - Recreate from `databricks/pipelines/genie_space_setup.sql`

2. **Via API** (if available):
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
# Delete space
w.genie.delete_space(space_id="YOUR_SPACE_ID")

# Recreate from configuration
# (Follow genie_space_setup.sql instructions)
```

**Validation**:
- Test query: "Show me current crusher status"
- Should return results within 5 seconds
- Results should match data in gold tables

### 4. Rollback Monitoring

**Symptom**: Monitoring dashboards show errors, alerts not firing

**Rollback**:
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Delete monitor
monitor_id = "YOUR_MONITOR_ID"
w.quality_monitors.delete(table_name="field_engineering.mining_demo.ot_telemetry_gold")

# Recreate if needed
# (Manual via UI or redeploy)
```

---

## Ignition Rollback

### 1. Rollback Gateway Scripts

**Symptom**: Scripts causing errors, high CPU, incorrect simulation

**Quick Fix** (disable scripts):

1. Open Gateway webpage: Config > Scripting > Gateway Event Scripts
2. Find script: "Physics Simulation" or "Fault Injection"
3. Uncheck "Enabled"
4. Save

**Full Rollback** (restore previous version):

1. If you saved previous versions:
   - Open script in Gateway
   - Copy current code to backup file
   - Paste previous version
   - Save and enable

2. Or redeploy from source:
   - Open: `ignition/scripts/mining_physics_simulation.py`
   - Copy entire content
   - Paste into Gateway script editor
   - Save

**Validation**:
- Watch Tag Browser for 1 minute
- Tags should update every second
- Values should be realistic (no NaN, null, or extreme values)

### 2. Rollback UDTs

**Symptom**: UDT structure incorrect, tags not accessible

**Rollback**:

1. **Export current UDTs** (before deleting):
   - Right-click UDT in Designer > Export > JSON
   - Save as backup

2. **Delete problematic UDTs**:
   - Select UDT in Data Types folder
   - Right-click > Delete
   - Confirm deletion (WARNING: deletes all instances!)

3. **Import previous version**:
   - Right-click Data Types > Import > JSON
   - Select backup file or source file from `ignition/udts/`

**Validation**:
- Verify UDTs appear in Data Types folder
- Check structure matches specification
- Recreate tag instances if needed

### 3. Rollback Tag Instances

**Symptom**: Tags missing, incorrect values, wrong structure

**Quick Fix** (delete and recreate):

1. **Backup current values** (if needed):
   ```python
   # In Designer script console
   tags = system.tag.browseTags('[default]Mining/Equipment', recursive=True)
   for tag in tags:
       print(tag.path, tag.value)
   ```

2. **Delete problematic tags**:
   - Select folder: [default]Mining/Equipment
   - Right-click > Delete
   - Confirm

3. **Recreate from script**:
   ```bash
   cd ignition/udts
   python create_tag_instances.py
   ```

**Validation**:
- Count tags: Should be 105 total
- Check structure: 5 trucks, 3 crushers, 2 conveyors
- Verify tags are updating

### 4. Rollback Perspective View

**Symptom**: View not loading, errors, UI broken

**Rollback**:

1. **Restore from backup** (if you exported):
   - Designer > Perspective > Views
   - Right-click > Import
   - Select backup .zip file

2. **Or recreate from spec**:
   - Delete broken view
   - Create new view
   - Follow: `ui/perspective_view_spec.json`
   - Rebuild component by component

**Validation**:
- Open view in session
- Verify all components render
- Check tag bindings work
- Test iframe loads chat UI

### 5. Rollback Zerobus Configuration

**Symptom**: No data flowing to Databricks, errors in logs

**Quick Fix** (disable streaming):

1. Gateway > Config > Zerobus
2. Uncheck "Enabled"
3. Save

**Full Rollback** (reconfigure):

1. Delete existing connection
2. Create new connection with correct settings:
   - Workspace URL
   - Token
   - Stream name
   - Tag selection

**Validation**:
```sql
-- In Databricks, check data flow
SELECT COUNT(*) as recent_records
FROM field_engineering.mining_demo.ot_telemetry_bronze
WHERE timestamp > current_timestamp() - INTERVAL 5 MINUTES;

-- Should have hundreds of records
```

---

## UI Rollback

### 1. Rollback Chat UI

**Symptom**: Chat not loading, errors, broken functionality

**Rollback**:

1. **Upload previous version to Databricks**:
   ```bash
   # If you have backup
   python build/deploy_ui.py --environment dev --file ui/backup/genie_chat_perspective_v1.html
   ```

2. **Or manually via UI**:
   - Databricks > Data > Files
   - Delete current file
   - Upload previous version from backup

3. **Update Perspective iframe URL** to new file

**Validation**:
- Open UI URL directly in browser
- Type test question
- Verify Genie responds
- Check no console errors (F12)

### 2. Rollback Perspective Integration

**Symptom**: Iframe not loading, session properties broken

**Rollback**:

1. **Revert session startup script**:
   - Open Designer > Perspective > Session Events
   - Replace script with previous version
   - Or comment out problematic lines

2. **Revert view changes**:
   - If you made incremental changes, undo them
   - Or restore entire view from backup

**Validation**:
- Open new Perspective session
- Check session.custom properties are set
- Verify iframe URL is correct
- Test chat functionality

---

## Emergency Procedures

### Complete System Failure

If entire system is down or corrupted:

#### 1. Stop Everything

```bash
# Stop all deployments
# In Databricks: Stop DLT pipeline
# In Ignition: Disable all Gateway scripts, stop Zerobus

# This prevents further damage
```

#### 2. Assess Damage

```bash
# Check what's working and what's not
python build/system_health_check.py --environment dev

# This will report status of:
# - Databricks connection
# - DLT pipeline state
# - Genie space availability
# - Ignition connectivity
# - Data freshness
```

#### 3. Prioritize Recovery

**Critical Path** (must work for demo):
1. Tag simulation in Ignition
2. Data flowing to Databricks
3. DLT pipeline processing
4. Genie responding to queries
5. Chat UI accessible

**Nice to Have** (can demo without):
1. Fault injection
2. Monitoring dashboards
3. Advanced visualizations
4. Mobile responsiveness

#### 4. Rebuild from Scratch

If rollback fails, rebuild:

```bash
# 1. Clean environment (careful!)
python build/clean_environment.py --environment dev --confirm

# 2. Redeploy from scratch
python build/deploy_all.py --environment dev --no-interactive

# 3. Follow manual steps
# See: build/deployment_summary_dev.md

# 4. Validate
python build/run_validation.py --environment dev
```

### Data Loss Prevention

If you suspect data loss:

```sql
-- Check bronze table
SELECT
    DATE(timestamp) as date,
    COUNT(*) as records
FROM field_engineering.mining_demo.ot_telemetry_bronze
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Look for gaps (days with 0 records)
```

**Recovery**:
- Bronze data is raw from Ignition (can replay by rerunning simulation)
- Silver/Gold data can be regenerated from bronze by DLT
- Dimension tables are static (can redeploy)
- No critical data loss in demo environment

### Security Incident

If credentials compromised or security breach:

```bash
# 1. Immediately revoke token
# In Databricks: Settings > User > Access Tokens > Revoke

# 2. Generate new token
# Databricks: Settings > User > Access Tokens > Generate New Token

# 3. Update environment
export DATABRICKS_TOKEN=new_token_here

# 4. Redeploy with new credentials
python build/deploy_databricks.py --environment dev

# 5. Update Ignition Zerobus configuration with new token

# 6. Update Perspective session properties

# 7. Audit access logs
# Databricks: Settings > Usage > Audit Logs
```

---

## Recovery Validation

After rollback, validate system works:

### 1. Component-Level Tests

**Databricks**:
```sql
-- Verify tables exist
SHOW TABLES IN field_engineering.mining_demo;

-- Verify data freshness
SELECT MAX(timestamp) FROM field_engineering.mining_demo.ot_telemetry_gold;
-- Should be within last 5 minutes

-- Test Genie
-- In Genie UI: "Show me current crusher status"
```

**Ignition**:
- Open Tag Browser
- Watch tags update for 1 minute
- Verify realistic values
- Check Gateway logs for errors

**UI**:
- Open chat UI URL in browser
- Type: "Show me current status"
- Verify response within 5 seconds

### 2. Integration Tests

**End-to-End**:
1. Change tag value in Ignition: CR_002/Vibration = 45
2. Wait 10 seconds
3. Check Databricks gold table for new value
4. Ask Genie: "Why is Crusher 2 vibration high?"
5. Verify response references current data

**Target Latency**:
- Tag change → Bronze: <2s
- Bronze → Gold: <3s
- Query → Response: <5s
- **Total: <15s**

### 3. Performance Tests

**Load Test**:
- Let system run for 1 hour
- Check CPU/memory usage is stable
- Verify no data gaps
- Check all components responsive

**Stress Test** (optional):
- Increase tag update frequency to 100ms
- Monitor DLT pipeline latency
- Check if system keeps up

### 4. Documentation

After recovery, document:
1. **What went wrong**: Symptoms, root cause
2. **What was rolled back**: Components, versions
3. **How long it took**: Detection to recovery time
4. **Lessons learned**: Prevention, improvements
5. **Action items**: Follow-up tasks

Template:
```markdown
## Incident Report - [DATE]

**Summary**: [Brief description]

**Timeline**:
- [TIME] Issue detected
- [TIME] Rollback initiated
- [TIME] System restored
- [TIME] Validation complete

**Root Cause**: [What caused the issue]

**Resolution**: [What was done to fix it]

**Impact**: [What was affected, downtime]

**Prevention**: [How to prevent in future]

**Action Items**:
- [ ] [Task 1]
- [ ] [Task 2]
```

---

## Prevention Strategies

To minimize need for rollbacks:

### Pre-Deployment

1. **Test in dev first**: Never deploy directly to prod
2. **Run validation**: `python build/deploy_all.py --check-only`
3. **Create backups**: Always backup before changes
4. **Review changes**: Code review, config review
5. **Schedule wisely**: Deploy during low-usage windows

### During Deployment

1. **Deploy incrementally**: One component at a time
2. **Validate each step**: Don't proceed if validation fails
3. **Monitor logs**: Watch for errors in real-time
4. **Have rollback ready**: Keep rollback commands prepared
5. **Two-person rule**: Have someone review before proceeding

### Post-Deployment

1. **Smoke test immediately**: Test critical paths
2. **Monitor for 1 hour**: Watch for anomalies
3. **Full validation**: Run complete test suite
4. **Document changes**: Update deployment records
5. **Brief team**: Share what was deployed

### Continuous Monitoring

1. **Health checks**: Automated every 5 minutes
2. **Alerting**: Notify on errors, latency spikes
3. **Capacity planning**: Monitor resource usage trends
4. **Regular audits**: Weekly review of logs
5. **Disaster recovery drills**: Practice rollback procedures

---

## Quick Reference

### Emergency Contacts

- **Databricks Support**: [support@databricks.com](mailto:support@databricks.com)
- **Ignition Support**: [support@inductiveautomation.com](mailto:support@inductiveautomation.com)
- **Project Lead**: [Your contact info]

### Key Commands

```bash
# Stop everything
python build/emergency_stop.py --environment dev

# System health check
python build/system_health_check.py --environment dev

# Full rollback
python build/rollback_all.py --environment dev --to-version previous

# Validate system
python build/run_validation.py --environment dev
```

### Key Files

- Deployment state: `build/deployment_state_dev.json`
- Backups: `build/backups/`
- Logs: `build/logs/`
- Configuration: `build/environment_config.yaml`

### Success Criteria

System is healthy when:
-  All components accessible
-  Data flowing (check timestamps)
-  Latency targets met (<15s end-to-end)
-  No errors in logs
-  Demo scenario works

---

**Remember**: When in doubt, stop and assess. Fast rollback is better than forcing ahead with broken system.
