# Build Automation - Mining Operations Genie Demo

Production-ready deployment automation for the complete Mining Operations Genie Demo system.

## Quick Start

```bash
# 1. Install dependencies
cd build
pip install -r requirements.txt

# 2. Set environment variables
export DATABRICKS_TOKEN=your_token_here

# 3. Check prerequisites
python deploy_all.py --check-only

# 4. Deploy everything
python deploy_all.py --environment dev
```

## What This Does

Automated deployment of:
-  Databricks DLT pipeline and dimension tables
-  Genie chat UI upload and configuration
-  Integration guides for Ignition components

Manual configuration required for:
- Ignition UDTs, tags, and Gateway scripts (2-3 hours)
- Genie space creation in Databricks UI (10 minutes)
- Perspective view integration (30 minutes)

## Directory Structure

```
build/
 README.md                              # This file
 requirements.txt                       # Python dependencies
 environment_config.yaml                # Environment configuration

 deploy_all.py                          # Master deployment orchestrator
 deploy_databricks.py                   # Databricks component deployment
 deploy_ignition.py                     # Ignition deployment instructions
 deploy_ui.py                           # Chat UI deployment

 build_sequence.md                      # Complete step-by-step guide
 rollback_procedures.md                 # Rollback and recovery procedures

 [Generated during deployment]
     deployment_summary_dev.md          # Deployment results summary
     deployment_state_dev.json          # Deployment state for rollback
     ignition_deployment_checklist_dev.md
     genie_integration_config_dev.md
     perspective_integration_guide_dev.md
```

## Deployment Scripts

### Master Deployment

**`deploy_all.py`** - Orchestrates complete deployment

```bash
# Deploy to dev (interactive)
python deploy_all.py --environment dev

# Deploy to prod (non-interactive for CI/CD)
python deploy_all.py --environment prod --no-interactive

# Check prerequisites only
python deploy_all.py --check-only
```

**What it does**:
1. Validates prerequisites (Python, dependencies, credentials)
2. Runs Databricks deployment
3. Runs UI deployment
4. Generates Ignition deployment instructions
5. Creates comprehensive deployment summary
6. Provides next steps and validation procedures

**Duration**: ~30 minutes for automated steps

### Databricks Deployment

**`deploy_databricks.py`** - Deploys all Databricks components

```bash
# Full deployment
python deploy_databricks.py --environment dev

# Deploy specific component
python deploy_databricks.py --component tables --environment dev
python deploy_databricks.py --component pipeline --environment dev
python deploy_databricks.py --component genie --environment dev
```

**Components deployed**:
- Dimension tables (equipment_master, equipment_types, etc.)
- DLT Real-Time pipeline (bronze → silver → gold)
- Pipeline notebooks and configuration
- Monitoring setup (manual via UI)
- Genie space instructions

**Duration**: ~20 minutes

### UI Deployment

**`deploy_ui.py`** - Deploys chat UI to Databricks Files

```bash
python deploy_ui.py --environment dev
```

**What it does**:
1. Validates UI files exist
2. Uploads HTML to Databricks Files
3. Generates public URL
4. Creates Genie integration configuration
5. Creates Perspective integration guide

**Duration**: ~5 minutes

**Output**: Public URL for chat UI (use in Perspective iframe)

### Ignition Deployment

**`deploy_ignition.py`** - Generates Ignition deployment instructions

```bash
python deploy_ignition.py --environment dev
```

**What it does**:
1. Validates Ignition connectivity
2. Generates step-by-step deployment checklist
3. Creates UDT import instructions
4. Creates Gateway script deployment guide
5. Creates Zerobus configuration instructions
6. Creates Perspective view integration guide

**Duration**: ~2 minutes (to generate instructions)

**Manual work required**: 2-3 hours to complete checklist

## Configuration

### Environment Configuration

**`environment_config.yaml`** - Central configuration for all environments

```yaml
databricks:
  dev:
    workspace_url: "https://field-eng.cloud.databricks.com"
    workspace_id: "4b9b953939869799"
    catalog: "field_engineering"
    schema: "mining_demo"
    warehouse_id: "4b9b953939869799"

ignition:
  dev:
    gateway_url: "http://localhost:8088"
    project_name: "MiningOperations"

components:
  dlt_pipeline:
    name: "mining_realtime_pipeline"
    mode: "REAL_TIME"
    min_workers: 1
    max_workers: 4

  genie:
    space_name: "Mining Operations Intelligence"
    max_query_timeout_seconds: 30
```

**Customize** for your environment before deployment.

### Environment Variables

Required:
```bash
export DATABRICKS_TOKEN=dapi1234567890abcdef
```

Optional:
```bash
export IGNITION_USERNAME=admin
export IGNITION_PASSWORD=password
```

## Prerequisites

### Software Requirements

- **Python 3.12+**: Automation scripts
- **Ignition 8.1+**: Edge gateway and HMI
- **Databricks**: Runtime 16.4+ recommended
- **Modern web browser**: Chrome, Edge, Firefox

### Access Requirements

- Databricks workspace access with admin privileges
- Personal access token with SQL execution permissions
- Ignition Gateway with admin credentials
- Network connectivity: Ignition ↔ Databricks

### Python Dependencies

Install from `requirements.txt`:
- databricks-sdk==0.35.0 (Databricks API client)
- rich==13.7.1 (Beautiful terminal output)
- pyyaml==6.0.1 (Configuration parsing)
- requests==2.31.0 (HTTP client)
- typer[all]==0.12.5 (CLI framework)

## Deployment Sequence

### Phase 1: Automated Deployment (30 min)

```bash
python deploy_all.py --environment dev
```

Deploys:
1. Databricks dimension tables
2. DLT Real-Time pipeline
3. Chat UI to Databricks Files
4. Generates all configuration guides

### Phase 2: Manual Configuration (2-3 hours)

Follow generated checklists:

1. **Ignition** (~2 hours):
   - Import UDTs
   - Create tag instances (105 tags)
   - Deploy Gateway scripts
   - Configure Zerobus streaming
   - Create Perspective view

2. **Genie Space** (~10 minutes):
   - Create space in Databricks UI
   - Configure tables and instructions
   - Test sample queries

3. **Integration** (~30 minutes):
   - Embed chat UI in Perspective
   - Configure session properties
   - Add "Ask AI" buttons
   - Test end-to-end flow

### Phase 3: Validation (1 hour)

Run comprehensive validation:
```bash
python run_validation.py --environment dev
```

Tests:
- Component functionality
- Integration points
- End-to-end latency
- Stability over time

## Validation

### Quick Validation

```bash
# Check Databricks connection
python -c "
from databricks.sdk import WorkspaceClient
import os
w = WorkspaceClient(token=os.environ['DATABRICKS_TOKEN'])
print(w.current_user.me())
"

# Check data flow
# In Databricks SQL Editor:
SELECT COUNT(*), MAX(timestamp)
FROM field_engineering.mining_demo.ot_telemetry_bronze;
```

### Full Validation

See: **`build_sequence.md`** Section: Validation

Tests:
1. **Component level**: Each component works independently
2. **Integration level**: Components communicate correctly
3. **End-to-end level**: Complete user workflow functions
4. **Performance level**: Meets latency targets (<15s)
5. **Stability level**: Runs for 1+ hours without issues

### Success Criteria

System is ready when:
-  Tags update every second (1 Hz)
-  Data flows to Databricks in <2s
-  DLT pipeline processes in <3s
-  Genie responds in <5s
-  End-to-end latency <15s
-  System stable for 1+ hour
-  Demo rehearsed successfully

## Rollback

If deployment fails or issues occur:

```bash
# Stop everything
python emergency_stop.py --environment dev

# Check system health
python system_health_check.py --environment dev

# Rollback specific component
python rollback.py --component databricks --environment dev

# Full rollback to previous state
python rollback_all.py --environment dev --to-version previous
```

See: **`rollback_procedures.md`** for detailed rollback procedures.

## Troubleshooting

### Common Issues

#### 1. Prerequisites Check Fails

**Issue**: Missing dependencies or invalid credentials

**Fix**:
```bash
# Install dependencies
pip install -r requirements.txt

# Verify token
echo $DATABRICKS_TOKEN | head -c 20

# Test connection
python -c "from databricks.sdk import WorkspaceClient; import os; w = WorkspaceClient(token=os.environ['DATABRICKS_TOKEN']); print(w.current_user.me())"
```

#### 2. Databricks Deployment Fails

**Issue**: Tables not created, pipeline errors

**Check**:
```bash
# View deployment state
cat deployment_state_dev.json

# Check Databricks manually
# Open Workflows > Delta Live Tables
# Check pipeline status
```

**Fix**:
```bash
# Retry specific component
python deploy_databricks.py --component tables --environment dev
```

#### 3. No Data Flowing

**Issue**: Bronze table empty or not updating

**Check**:
- Are Ignition tags updating? (Tag Browser)
- Is Zerobus enabled? (Gateway Config)
- Any errors in Gateway logs?

**Fix**:
1. Verify tags: Watch `[default]Mining/Equipment/CR_001/Speed_KPH`
2. Check Zerobus logs in Gateway
3. Restart Zerobus: Disable → Save → Enable → Save
4. Verify network connectivity

#### 4. Slow Performance

**Issue**: Queries take >10s, latency >15s end-to-end

**Check**:
- Is warehouse running? (not cold start)
- Is DLT pipeline keeping up? (<3s latency)
- Network latency?

**Fix**:
1. Keep warehouse running during demo
2. Pre-warm with test queries
3. Increase DLT cluster size if needed

#### 5. Chat UI Not Loading

**Issue**: Blank iframe or errors

**Check**:
- Test URL directly in browser (outside iframe)
- Check browser console (F12)
- Verify session properties set

**Fix**:
1. Verify iframe URL: `{{session.custom.genie_chat_url}}`
2. Check session startup script ran
3. Re-upload UI: `python deploy_ui.py --environment dev`

### Getting Help

1. **Check logs**: Component logs, Gateway logs, browser console
2. **Review docs**: build_sequence.md, rollback_procedures.md
3. **Test isolated**: Identify which component is failing
4. **Rollback**: Revert to last known good state
5. **Contact support**: Include deployment_summary and logs

## Advanced Usage

### CI/CD Integration

```bash
# In CI/CD pipeline
export DATABRICKS_TOKEN=${DATABRICKS_TOKEN_SECRET}
python deploy_all.py --environment prod --no-interactive

# Check exit code
if [ $? -ne 0 ]; then
    echo "Deployment failed"
    exit 1
fi
```

### Custom Configuration

```bash
# Use custom config file
python deploy_all.py --config my_custom_config.yaml --environment dev

# Deploy to custom workspace
export DATABRICKS_WORKSPACE_URL=https://my-workspace.cloud.databricks.com
python deploy_databricks.py --environment dev
```

### Parallel Deployment

If you have multiple people:

**Track A** (Person 1): Databricks
```bash
python deploy_databricks.py --environment dev
```

**Track B** (Person 2): Ignition
```bash
# Follow generated checklist
cat ignition_deployment_checklist_dev.md
```

**Track C** (Person 3): UI
```bash
python deploy_ui.py --environment dev
# Then integrate in Perspective
```

**Converge**: Integration testing

### Backup and Restore

```bash
# Before deployment, create backup
python create_backup.py --environment dev

# Restore from backup
python restore_from_backup.py --environment dev --backup-id 20250215_103045

# List backups
python list_backups.py --environment dev
```

## Architecture

### Data Flow

```
Ignition Tags (105 tags, 1 Hz)
    ↓
Zerobus Module (500ms batches)
    ↓
Databricks Streaming (Autoloader)
    ↓
DLT Pipeline Real-Time
     Bronze (Raw JSON)
     Silver (Normalized)
     Gold (Aggregated 1-min windows)
        ↓
Genie Space (Natural Language SQL)
    ↓
Chat UI (HTML5 in Perspective iframe)
```

### Component Relationships

```

                     DEPLOYMENT SCOPE                         
                                                              
      
   Automated (30 min)                                     
    - Databricks tables, pipeline                         
    - UI upload                                           
    - Configuration generation                            
      
                                                              
      
   Manual (2-3 hours)                                     
    - Ignition UDTs, tags, scripts                        
    - Genie space creation                                
    - Perspective view integration                        
      
                                                              
      
   Validation (1 hour)                                    
    - Component tests                                     
    - Integration tests                                   
    - End-to-end tests                                    
    - Performance tests                                   
      

```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Edge | Ignition 8.1+ | Tag management, HMI, Perspective |
| Streaming | Zerobus | Real-time data ingestion |
| Processing | Databricks DLT | ETL pipeline (bronze → silver → gold) |
| Storage | Delta Lake | ACID-compliant data lake |
| Analytics | Databricks SQL | Query engine |
| AI | Genie | Natural language interface |
| UI | HTML5/JS | Chat interface |
| Deployment | Python 3.12 | Automation scripts |

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Tag update frequency | 1 Hz | 1 Hz |
| Zerobus batch interval | 500ms | 500ms |
| Tag → Bronze latency | <2s | ~1s |
| Bronze → Gold latency | <3s | ~2s |
| Genie query response | <5s | ~3s |
| End-to-end latency | <15s | ~10s |
| System uptime | >99% | - |
| Data loss rate | 0% | - |

## Scale Metrics

| Metric | Development | Production |
|--------|-------------|------------|
| Equipment count | 15 | 100+ |
| Tag count | 105 | 700+ |
| Data points/second | 105 | 700+ |
| Daily data volume | ~9M records | ~60M records |
| DLT cluster size | 1-4 workers | 4-16 workers |
| Storage | <10 GB | 100s of GB |

## Cost Optimization

### Development Environment

- **Compute**: Auto-scaling clusters (1-4 workers)
- **Storage**: Delta Lake with retention (7 days)
- **Warehouse**: Start/stop with demo
- **Estimated**: $5-10/day when running

### Production Environment

- **Compute**: Right-sized clusters based on load
- **Storage**: Delta Lake with retention (90 days)
- **Warehouse**: Serverless SQL for instant start
- **Estimated**: $50-100/day at 100 equipment scale

### Cost Reduction Tips

1. **Stop warehouse when not in use**
2. **Use auto-scaling clusters**
3. **Implement data retention policies**
4. **Monitor with Databricks usage dashboards**
5. **Use spot instances for non-critical workloads**

## Security

### Authentication

- **Databricks**: Personal access token (rotate every 90 days)
- **Ignition**: Admin credentials (change from defaults)
- **Network**: Private networking recommended for production

### Authorization

- **Databricks**: Unity Catalog with RBAC
- **Ignition**: Role-based access control
- **Genie**: Inherit Databricks permissions

### Data Protection

- **Encryption at rest**: Delta Lake default
- **Encryption in transit**: HTTPS/TLS
- **PII handling**: Mask sensitive fields in logs

### Best Practices

1. **Rotate credentials regularly**
2. **Use least privilege principle**
3. **Audit access logs**
4. **Enable MFA for admin accounts**
5. **Network segmentation in production**

## Support

### Documentation

- **Build Sequence**: build_sequence.md (complete step-by-step guide)
- **Rollback**: rollback_procedures.md (recovery procedures)
- **Configuration**: environment_config.yaml (all settings)
- **Component Docs**: See README in each directory (databricks/, ignition/, ui/)

### Generated Guides

After deployment, see:
- deployment_summary_dev.md (deployment results)
- ignition_deployment_checklist_dev.md (Ignition steps)
- genie_integration_config_dev.md (Genie configuration)
- perspective_integration_guide_dev.md (Perspective integration)

### Contact

- **Project Repository**: [Link to repository]
- **Issues**: [Link to issue tracker]
- **Databricks Support**: support@databricks.com
- **Ignition Support**: support@inductiveautomation.com

## License

[Your license here]

---

**Ready to deploy?** Start with:

```bash
python deploy_all.py --check-only
```

Then proceed with:

```bash
python deploy_all.py --environment dev
```

**Good luck with your demo!**
