# Genie at the Edge - Quick Reference Summary

## System At a Glance

| Aspect | Details |
|--------|---------|
| **Project Name** | Mining Operations Genie Demo |
| **Repository** | github.com/pravinva/genie-at-the-edge |
| **Current Branch** | feature/perspective-native-genie |
| **Status** | Production Ready |
| **Use Case** | Mining operations with AI insights (2.4M+ member scale potential) |
| **Architecture** | Ignition Gateway + Databricks Genie (no external proxy) |
| **Deployment** | Docker container (Ignition) + Databricks workspace |

---

## Component Matrix

### 1. IGNITION GATEWAY (Docker Container)

| Component | Spec | Performance |
|-----------|------|-------------|
| **Image** | inductiveautomation/ignition:8.1.51 | ~30-40s startup |
| **HTTP Port** | 8183 (host) / 8088 (container) | <10ms internal |
| **HTTPS Port** | 8144 (host) / 8043 (container) | <10ms internal |
| **Memory** | 250-350MB (sessions active) | Stable, no leaks |
| **CPU** | 2-3% idle, 5-8% active | Linear scaling |
| **Storage** | 2GB Docker volume | Persistent |
| **Admin** | admin / password | Configurable |

#### Ignition Tags (107 Total)
```
5 Haul Trucks    (HT_001-HT_005):     14 tags each  = 70 tags
3 Crushers       (CR_001-CR_003):     9 tags each   = 27 tags
2 Conveyors      (CV_001-CV_002):     5 tags each   = 10 tags
                                              Total = 107 tags
```

#### Gateway Scripts
1. **mining_physics_simulation.py** - Timer (1sec), <1% CPU, 10MB RAM
2. **genie_gateway_script.py** - Async, caches tokens & responses, 280x speedup
3. **fault_injection_cr002.py** - Manual trigger, 48-hour bearing sim

---

### 2. DATABRICKS WORKSPACE

| Component | Config | Scale |
|-----------|--------|-------|
| **DLT Pipeline** | mining_operations_realtime (REAL_TIME mode) | 2 workers (i3.xlarge) |
| **Ingest Throughput** | 150 events/sec (107 tags × 1.4 Hz) | Sustained |
| **Latency (end-to-end)** | <2 seconds (event → gold table) | <1% jitter |
| **Storage/Day** | ~2.1GB (compressed: ~1GB) | 30-90 day retention |
| **Total Storage** | ~70GB (30-90 day window) | Auto-purge old partitions |
| **Cost** | $2-3/hour DLT + $0.30-1.50/DBU Genie | Autoscale enabled |
| **Catalog** | ignition_genie (primary) | UC enabled |
| **Schema** | mining_demo (dev), mining_demo_prod | Isolated envs |

#### DLT Tables (7 Total)
```
Bronze:  tag_events_bronze (raw Zerobus stream)
Silver:  equipment_sensors_normalized (parsed & enriched)
Gold:    - equipment_performance_1min (1min aggregates)
         - equipment_current_status (latest per equipment)
         - haul_truck_cycles (state tracking)
         - sensor_anomalies (threshold-based detection)
Metrics: pipeline_quality_metrics (pipeline health)
```

#### Genie Space Config
```
Name: Mining Operations Intelligence
Warehouse: SQL (auto-start, 5min shutdown)
Timeout: 30 seconds per query
Available Tables: All 7 from DLT + dimension tables
SQL Display: Enabled for learning
```

---

### 3. PERSPECTIVE UI (Browser)

| Component | Spec | Performance |
|-----------|------|-------------|
| **HTML File** | genie_chat_perspective.html | ~94KB, single-file |
| **Architecture** | Embedded Frame (iframe) in Perspective view | Lazy load |
| **Browser Support** | Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ | Cross-platform |
| **Load Time** | <2 seconds | Cached |
| **Chat Response** | 6-10s (cold), 0.03s (cached) | 280x speedup |
| **Memory** | 78MB after 30 min | Stable |
| **FPS** | 60 FPS scrolling | GPU accelerated |

#### Custom Properties
```
messages: array of {type, text, chartData}
inputValue: string (user input)
conversationId: string (Genie conversation ID)
pending_question: string (pre-filled from alarm/equipment)
suggestedQuestions: array (follow-ups)
```

---

## Request Flow Deep Dive

### User Query → Response (9 Steps)

```
Step 1: User types question + hits Enter
Step 2: Perspective receives via WebSocket (0.01s)
Step 3: Invoke async gateway script (0.05s)
Step 4: Check response cache (0.001s) → HIT = END (0.03s total) ✓
        OR MISS → Continue...
Step 5: Get Databricks token (0.2s if cache miss)
Step 6: Call Genie API start-conversation (1.5s)
Step 7: Poll for completion (5-8s, 500ms intervals)
Step 8: Extract response + fetch chart data (0.5s)
Step 9: Render in Perspective (0.1s)
        User sees response: 6-10s (cold) or 0.03s (cached)
```

### Latency Breakdown
- **Cache Hit:** 30ms (instant)
- **Token Cache Hit:** 1.5-2s
- **Token Cache Miss:** 1.7-2.2s (adds 200ms CLI)
- **SQL Execution:** 5-8s (warehouse startup: +20-30s if cold)
- **Average Demo:** 4.7s (mix of cold & cached)

---

## Performance Benchmarks

### Throughput & Latency

| Metric | Value | Notes |
|--------|-------|-------|
| Tag ingestion | 150 events/sec | From Ignition |
| Bronze latency | <1 sec | Zerobus → Delta |
| Silver latency | <500ms | Parse + enrich |
| Gold latency | <300ms | 1-min windows |
| Anomaly latency | <1 sec | Threshold detection |
| Genie response | 6-10s | SQL query + AI |
| Genie cached | 30ms | Module-level cache |
| UI rendering | 60 FPS | DOM updates |

### Load Testing Results

| Concurrent Users | CPU | Memory | Response Time | Success |
|------------------|-----|--------|---------------|---------|
| 1 | 5% | 250MB | 6-8s | 100% |
| 5 | 8% | 350MB | 6-10s | 100% |
| 10 | 15% | 500MB | 8-12s | 98% |
| 20 | 25% | 750MB | 12-20s | 95% |
| 50 | 45% | 1.2GB | 30-45s | 90% |

**Recommendations:** 5-10 concurrent users per gateway (scale horizontally for more)

---

## Storage Consumption

### Daily Ingestion & Retention

| Table | Records/Min | Size/Day | Retention | Running Total |
|-------|------------|---------|-----------|---------------|
| tag_events_bronze | 9,000 | 1.2GB | 30d | 36GB |
| equipment_sensors_normalized | 9,000 | 800MB | 30d | 24GB |
| equipment_performance_1min | 500 | 50MB | 90d | 4.5GB |
| equipment_current_status | 107 | 1MB | Current | 1MB |
| haul_truck_cycles | 50 | 5MB | 30d | 150MB |
| sensor_anomalies | 10-50 | 10MB | 30d | 300MB |
| pipeline_quality_metrics | 500 | 50MB | 90d | 4.5GB |
| **TOTAL** | 19,000+ | 2.1GB | Mixed | **~70GB** |

*Compression: ~50% with Delta encoding*

---

## Key Dependencies

### Python Runtime (3.7+, for Databricks CLI only)
```
databricks-sdk==0.35.0
requests==2.31.0
pyyaml==6.0.1
python-dotenv==1.0.1
jinja2==3.1.4
click==8.1.7
rich==13.7.1
pydantic==2.9.2
```

### Ignition Runtime (Built-In Jython 2.7)
```
system.*                    # Ignition namespace
system.tag                  # Tag read/write
system.util                 # HTTP, JSON, logging
system.net                  # HTTP client
system.perspective          # Messaging
datetime, time, json, re    # Standard lib
```

### Browser (No External Dependencies!)
```
Native: Fetch API, DOM, WebSocket, LocalStorage
Included: Markdown-it, Prism, Chart.js (embedded)
```

---

## Security Checklist

| Item | Status | Notes |
|------|--------|-------|
| **Token Auth** | ✅ OAuth 2.0 via Databricks CLI | 60min lifespan |
| **Token Cache** | ✅ 50-minute TTL | Refresh before expiry |
| **Token Storage** | ✅ Encrypted tag in Ignition | Not in code/logs |
| **Network** | ✅ TLS 1.3 for all external calls | No CORS issues |
| **Firewall** | ✅ 8043 inbound (users), 443 outbound (Databricks) | Locked down |
| **Data Privacy** | ✅ No PII in responses | AI-generated insights only |
| **Audit Logging** | ✅ All queries logged | Conversation ID tracked |

---

## Configuration Quick Links

### MUST UPDATE Before Deployment

**File:** `ignition/scripts/genie_gateway_script.py` (lines 20-21)
```python
WORKSPACE_URL = "https://YOUR-WORKSPACE.cloud.databricks.com"  # Update!
SPACE_ID = "01f10a2ce1831ea28203c2a6ce271590"                # Update!
```

**How to Find:**
- WORKSPACE_URL: From Databricks URL bar
- SPACE_ID: Open Genie Space → Copy from room/{SPACE_ID}

**File:** `build/environment_config.yaml` (databricks section)
```yaml
workspace_url: https://your-workspace.cloud.databricks.com
workspace_id: your_workspace_id_from_url
catalog: your_catalog_name
schema: your_schema_name
warehouse_id: your_warehouse_id
```

---

## Common Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Module 'shared.genie_api' not found | Gateway script not deployed | Designer → Project → Scripts → Add genie_api module |
| Failed to get token | Databricks CLI not installed | `pip install databricks-cli && databricks configure` |
| Genie timeout (>30s) | Warehouse cold start | Use Serverless SQL or pre-warm before demo |
| Slow response (>15s) | Warehouse scaled down | Check warehouse size, increase if needed |
| Physics tags not updating | Timer script disabled | Gateway → Config → Scripting → Timer Scripts → Enable |
| Chat won't load | HTML file not uploaded | `databricks fs cp genie_chat_perspective.html dbfs:/FileStore/...` |

---

## Deployment Command Reference

```bash
# Start local Ignition
cd docker
docker-compose up -d
docker-compose logs -f ignition

# Stop Ignition
docker-compose down

# Deploy all components
python build/deploy_all.py

# Deploy just Databricks
python build/deploy_databricks.py

# Deploy just Ignition
python build/deploy_ignition.py

# Run test suite
cd testing
python test_suite.py

# Load test (10 concurrent users, 5 min)
python load_testing.py --users 10 --duration 300

# Performance benchmark
python performance_benchmarks.py
```

---

## Production Checklist

### Pre-Flight (1 hour)
- [ ] Databricks workspace accessible
- [ ] Ignition gateway running
- [ ] Network connectivity verified
- [ ] Credentials (OAuth token) ready

### Deployment (30 min)
- [ ] DLT pipeline created & running
- [ ] Genie Space configured
- [ ] Gateway scripts deployed
- [ ] HTML chat interface uploaded
- [ ] Perspective views created

### Validation (30 min)
- [ ] Test suite passing (7 suites)
- [ ] Load test acceptable (<20s at 10 users)
- [ ] Memory stable (no leaks over 30 min)
- [ ] Errors <5%, response time <10s

### Go-Live (Ongoing)
- [ ] Monitor response times (alert >15s)
- [ ] Monitor cache hit rate (target >50%)
- [ ] Monitor error rate (target <2%)
- [ ] Rotate token every 90 days
- [ ] Backup DLT pipeline config monthly

---

## Resource Requirements Summary

### Minimum (Single User, Dev)
```
Ignition:    Docker with 1GB RAM
DLT:         1 worker (i3.large minimum)
Warehouse:   1 cluster (Serverless recommended)
Cost:        ~$3-5/day total
```

### Recommended (5-10 Users, Prod)
```
Ignition:    Docker with 2GB RAM (or VM)
DLT:         2 workers (i3.xlarge)
Warehouse:   2-4 clusters (auto-scale)
Cost:        ~$40-60/day total
```

### Enterprise (50+ Users, Multi-Site)
```
Ignition:    HA pair (2x VM or containers)
DLT:         4 workers (i3.xlarge), autoscale to 8
Warehouse:   Multiple endpoints, load-balanced
Cost:        ~$200-300/day total
Licensing:   Databricks + Ignition enterprise
```

---

## Key Metrics to Monitor

### Daily Dashboard

```
1. Pipeline Health
   - Ingestion latency (target: <1s)
   - Processing latency (target: <500ms)
   - Data quality % (target: >99%)

2. Genie Performance
   - Average response time (target: <10s)
   - Cache hit rate (target: >50%)
   - Error rate (target: <5%)

3. System Health
   - Ignition CPU (target: <20%)
   - Ignition memory (target: <500MB)
   - Network latency (target: <100ms)
```

### Monthly Review

```
1. Cost Analysis
   - Databricks spend vs budget
   - Ignition licensing
   - Network bandwidth

2. Performance Trends
   - Response time trend (should be stable)
   - Cache effectiveness (should improve)
   - User satisfaction scores

3. Capacity Planning
   - User growth
   - Data growth rate
   - Compute scaling needs
```

---

## Support & Documentation

| Resource | Link | Purpose |
|----------|------|---------|
| **Full Analysis** | ARCHITECTURE_ANALYSIS.md | Complete 1200+ line doc |
| **README** | README.md | 400+ line overview |
| **Implementation** | docs/PERSPECTIVE_NATIVE_IMPLEMENTATION.md | Step-by-step guide |
| **Deployment** | build/DEPLOYMENT_QUICK_START.md | Quick reference |
| **Testing** | testing/TESTING_SUMMARY.md | Test procedures |
| **Demo** | demo/DEMO_SUMMARY.md | Demo walkthroughs |

---

## Technology Stack At a Glance

```
┌─────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER                                      │
│ ├─ Web Browser (Chrome/Firefox/Safari/Edge 90+)        │
│ └─ Single HTML file (94KB, no build)                   │
├─────────────────────────────────────────────────────────┤
│ APPLICATION LAYER                                       │
│ ├─ Ignition Gateway 8.1+ (Docker)                      │
│ ├─ Jython 2.7 Scripts                                  │
│ └─ Perspective Module (HMI)                            │
├─────────────────────────────────────────────────────────┤
│ STREAMING LAYER                                         │
│ ├─ Apache Spark Streaming                              │
│ ├─ Delta Live Tables (Real-Time)                       │
│ └─ Zerobus (Ignition → Kafka → Delta)                  │
├─────────────────────────────────────────────────────────┤
│ AI/ML LAYER                                             │
│ ├─ Databricks Genie (Natural Language SQL)             │
│ ├─ Unity Catalog (Data Governance)                     │
│ └─ Anomaly Detection (Statistical)                     │
├─────────────────────────────────────────────────────────┤
│ INFRASTRUCTURE                                          │
│ ├─ Docker Compose (Ignition)                           │
│ ├─ AWS/Azure (Databricks)                              │
│ └─ Python 3.7+ (CLI, Deployment)                       │
└─────────────────────────────────────────────────────────┘
```

---

**Last Updated:** 2026-02-19
**Status:** Production Ready
**Version:** 1.0 (Perspective-Native Implementation)

