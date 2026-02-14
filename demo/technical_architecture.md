# Technical Architecture - Mining Operations Genie

**Document Version:** 1.0
**Last Updated:** 2026-02-15
**Audience:** Technical stakeholders (IT, OT, Solutions Architects)

---

## Executive Summary

This document provides detailed technical architecture for the Mining Operations Genie solution - conversational AI embedded in Ignition SCADA powered by Databricks.

**Key Technical Capabilities:**
- Real-time data ingestion (<1 second latency)
- Unified lakehouse (OT + IT + business data)
- Natural language queries via Genie AI
- Embedded chat in Ignition Perspective
- Enterprise security and governance

---

## Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                    IGNITION SCADA LAYER                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   PLC    │  │  Tags    │  │ Alarms   │  │ Scripts  │  │
│  │ Drivers  │  │ 5,000+   │  │  Engine  │  │  Python  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Perspective HMI (Operator Interface)        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │  │
│  │  │  Equipment   │  │    Alarms    │  │    AI     │  │  │
│  │  │  Dashboard   │  │    Table     │  │   Chat    │  │  │
│  │  └──────────────┘  └──────────────┘  └───────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ Zerobus Connector
                             │ (HTTPS, Port 443 Outbound)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  DATABRICKS LAKEHOUSE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │             Delta Live Tables Pipeline                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │  Bronze  │→ │  Silver  │→ │   Gold   │          │  │
│  │  │   Raw    │  │ Cleansed │  │ Business │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                Unity Catalog                          │  │
│  │   - Governance & Access Control                       │  │
│  │   - Schema: main.mining_ops.*                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 Genie AI Space                        │  │
│  │   - Natural Language Processing                       │  │
│  │   - SQL Generation                                    │  │
│  │   - Context-Aware Responses                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            SQL Warehouse (Serverless)                 │  │
│  │   - Query Engine                                      │  │
│  │   - Auto-scaling                                      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ REST API
                             │ (HTTPS)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              PERSPECTIVE WEBDEV MODULE                      │
│   - Iframe embedding                                        │
│   - API calls to Genie                                      │
│   - Response rendering                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Deep Dive

### 1. Ignition SCADA Layer

**Purpose:** Industrial automation platform providing HMI, data collection, and SCADA capabilities

**Components:**

**Gateway:**
- Version: Ignition 8.1.30+ recommended
- Modules Required:
  - Perspective (for HMI)
  - WebDev (for iframe embedding)
  - Scripting (Python for Zerobus connector)
- Resources: 4-8 GB RAM, 4+ CPU cores recommended

**Tag System:**
- Total Tags: 5,000+ (crushers, trucks, conveyors)
- Update Rate: 1-5 seconds per tag
- Historical Storage: 30 days local (for backup)
- Example Tags:
  - `Crusher_1/Vibration` (REAL, mm/s)
  - `Crusher_2/BearingTemp` (REAL, °C)
  - `HaulTruck_3/FuelLevel` (REAL, liters)

**Alarm System:**
- Active Alarms: 50-100 typical
- Alarm Priority: Low / Medium / High / Critical
- Alarm Enrichment: Each alarm has context (equipment, timestamp, value)

**Perspective HMI:**
- Session Type: Mobile/Desktop responsive
- Components:
  - Equipment status cards
  - Real-time trend charts
  - Alarm table with "Ask AI" button
  - Embedded chat interface (right panel)

---

### 2. Zerobus Connector

**Purpose:** Stream tag changes from Ignition to Databricks in real-time

**Implementation:**

**Connector Type:** Native Python script in Ignition Gateway

**Data Flow:**
1. Ignition Tag Change Event triggers script
2. Script packages tag data (name, value, timestamp, quality)
3. Data sent to Databricks via HTTPS POST
4. Databricks Autoloader ingests to Bronze table

**Configuration:**
```python
# Connector config (Ignition script)
config = {
    "databricks_endpoint": "https://[workspace].databricks.com/api/2.0/zerobus/ingest",
    "auth_token": "[service_principal_token]",
    "batch_size": 100,  # Tags per batch
    "batch_interval": 1000,  # Milliseconds
    "retry_count": 3,
    "timeout": 5000  # Milliseconds
}
```

**Network Requirements:**
- Protocol: HTTPS (TLS 1.2+)
- Port: 443 outbound
- Firewall Rule: Allow `[workspace].databricks.com` on port 443
- Bandwidth: ~50-100 KB/s for 5,000 tags at 5-second update rate

**Reliability:**
- Local queue: Buffers 10,000 messages if network down
- Retry logic: Exponential backoff (1s, 2s, 4s)
- Health monitoring: Status tag updates every 60 seconds

**Alternative Integrations:**
- Litmus Edge: Use Litmus → Databricks connector
- DeepIQ: Use DeepIQ → Databricks integration
- Lakeflow SQL: Direct JDBC connection from Ignition

---

### 3. Databricks Lakehouse

**Purpose:** Unified data platform for ingestion, processing, storage, and AI

**Architecture:**

**Storage:**
- Format: Delta Lake (ACID transactions, time travel)
- Location: Cloud object storage (AWS S3 / Azure ADLS / GCP GCS)
- Partitioning: By date for time-series data
- Optimization: Z-order on equipment_id for fast queries

**Compute:**
- DLT Pipeline: 2-4 worker nodes (i3.xlarge or equivalent)
- SQL Warehouse: Serverless Pro (auto-scaling 2-16 clusters)
- Genie: Uses SQL Warehouse compute

**Catalog Structure:**
```
main (catalog)
└── mining_ops (schema)
    ├── sensor_data_bronze (raw ingestion)
    ├── sensor_data_silver (cleansed)
    ├── sensor_data_gold (business-ready)
    ├── incidents (historical failures)
    ├── work_orders (maintenance data)
    ├── equipment_metadata (asset registry)
    └── production_metrics (shift reports)
```

---

### 4. Delta Live Tables Pipeline

**Purpose:** Real-time streaming ETL from Bronze → Silver → Gold

**Pipeline Configuration:**

**Bronze Layer (Raw Ingestion):**
```python
@dlt.table(
    name="sensor_data_bronze",
    comment="Raw sensor data from Ignition"
)
def bronze():
    return (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "json")
            .load("/landing/ignition/")
            .select(
                col("tag_name"),
                col("value").cast("double"),
                col("timestamp").cast("timestamp"),
                col("quality")
            )
    )
```

**Silver Layer (Cleansing + Enrichment):**
```python
@dlt.table(
    name="sensor_data_silver",
    comment="Cleansed sensor data with equipment context"
)
@dlt.expect_or_drop("valid_quality", "quality = 'Good'")
@dlt.expect_or_drop("valid_value", "value IS NOT NULL")
def silver():
    return (
        dlt.read_stream("sensor_data_bronze")
            .join(
                spark.table("main.mining_ops.equipment_metadata"),
                on=expr("tag_name LIKE CONCAT(equipment_id, '/%')")
            )
            .select(
                col("equipment_id"),
                col("equipment_type"),
                col("tag_name"),
                col("value"),
                col("timestamp"),
                col("site_name")
            )
    )
```

**Gold Layer (Business-Ready Metrics):**
```python
@dlt.table(
    name="sensor_data_gold",
    comment="Business-ready sensor metrics"
)
def gold():
    return (
        dlt.read_stream("sensor_data_silver")
            .withColumn("metric_name", split(col("tag_name"), "/")[1])
            .withColumn("metric_value", col("value"))
            .withColumn("unit",
                when(col("metric_name") == "Vibration", "mm/s")
                .when(col("metric_name") == "Temperature", "°C")
                .otherwise("N/A")
            )
            .select(
                "timestamp",
                "equipment_id",
                "equipment_type",
                "metric_name",
                "metric_value",
                "unit",
                "site_name"
            )
    )
```

**Performance:**
- Latency: <1 second end-to-end (tag change → queryable)
- Throughput: 10,000+ records/second
- Mode: Spark Structured Streaming (continuous)

---

### 5. Genie AI Space

**Purpose:** Natural language query interface for operational data

**Configuration:**

**Space Setup:**
- Name: "Mining Operations"
- Description: "AI assistant for mining control room operators"
- Warehouse: Serverless Pro SQL Warehouse
- Tables: All tables in `main.mining_ops.*`

**Custom Instructions:**
```
You are an AI assistant for mining operations control room operators.

CONTEXT:
- Equipment: Haul trucks (5), crushers (3), conveyors (2)
- Normal operating ranges:
  - Crusher vibration: 18-25 mm/s
  - Crusher bearing temp: 60-75°C
  - Conveyor motor temp: 55-70°C
  - Haul truck efficiency: 85-95%
- Critical thresholds:
  - Vibration >40 mm/s: Inspect immediately
  - Temperature >85°C: Risk of failure
  - Efficiency <75%: Investigate cause

DATA SOURCES:
- main.mining_ops.sensor_data_gold (real-time sensor metrics)
- main.mining_ops.incidents (historical equipment failures and root causes)
- main.mining_ops.work_orders (maintenance records and technician notes)
- main.mining_ops.production_metrics (shift production targets and actuals)

RESPONSE GUIDELINES:
1. Always include timestamps when referencing data
2. Compare current values to normal baselines
3. Search for historical patterns with similarity >80%
4. Provide specific, actionable recommendations (not generic advice)
5. Include confidence scores on pattern matches (e.g., "87% confidence")
6. Always show units (mm/s, °C, kW, tonnes/hr)
7. If no data found, say so explicitly (don't guess)
8. For equipment comparisons, show all relevant equipment side-by-side
9. For historical incidents, include date, root cause, downtime, and cost

EXAMPLE RESPONSES:

Query: "Why is Crusher 2 vibrating high?"
Response: "Crusher 2 vibration increased to 42 mm/s at 2:23 PM (2.1x normal baseline of 20 mm/s). This pattern matches a belt misalignment incident from January 15, 2026 with 87% confidence. That incident resulted in 3.2 hours downtime and $53,000 in costs. Recommendation: Inspect belt alignment immediately before shutdown required."

Query: "Compare all crushers right now"
Response: "Current crusher vibration levels:
- Crusher 1: 21 mm/s (normal, last updated 2:28 PM)
- Crusher 2: 42 mm/s (elevated, last updated 2:28 PM) ⚠️
- Crusher 3: 19 mm/s (normal, last updated 2:28 PM)
Only Crusher 2 shows elevated vibration. Other crushers operating normally."

Query: "What haul trucks have low efficiency today?"
Response: "Haul truck efficiency analysis for February 15, 2026:
- Truck 3: 72% (below fleet average of 89%) ⚠️
- Truck 1: 91% (normal)
- Truck 2: 88% (normal)
- Truck 4: 90% (normal)
- Truck 5: 87% (normal)
Truck 3 has been consistently below target for the last 3 shifts. Recommend checking operator logs or scheduling maintenance inspection."
```

**Model:**
- LLM: GPT-4 or Claude (configurable)
- Temperature: 0.2 (for consistency and accuracy)
- Max Tokens: 500 (concise responses)

**SQL Generation:**
- Genie automatically converts natural language to SQL
- Uses table schemas and instructions for context
- Validates queries before execution
- Shows SQL in response (for transparency)

---

### 6. Perspective WebDev Integration

**Purpose:** Embed Genie chat interface in Ignition Perspective HMI

**Implementation:**

**Chat Component (iframe):**
```html
<!-- Perspective Embedded View -->
<iframe
    id="genie-chat"
    src="https://[workspace].databricks.com/genie/spaces/[space_id]/embed"
    width="100%"
    height="600px"
    style="border: none; border-radius: 8px;"
    allow="clipboard-write"
></iframe>
```

**Context Injection (JavaScript Bridge):**
```javascript
// Ignition script: Pre-fill chat based on alarm context
function askAIAboutAlarm(alarmRow) {
    const equipment = alarmRow.equipment_id;
    const metric = alarmRow.metric_name;
    const value = alarmRow.value;
    const timestamp = alarmRow.timestamp;

    const question = `Why is ${equipment} ${metric} at ${value}? Check historical patterns.`;

    // Send to iframe
    document.getElementById('genie-chat')
        .contentWindow.postMessage({
            action: 'prefill',
            question: question
        }, '*');
}
```

**Authentication:**
- Method: OAuth 2.0 or Service Principal
- Token stored in Perspective session
- Passed to Databricks API on each query

**UI/UX:**
- Chat opens in right panel (400px width)
- Typing indicator during query execution
- Markdown rendering for formatted responses
- Copy-to-clipboard for SQL queries
- Chat history persists during session

---

## Data Model

### Table Schemas

**sensor_data_gold:**
```sql
CREATE TABLE main.mining_ops.sensor_data_gold (
    timestamp TIMESTAMP NOT NULL,
    equipment_id STRING NOT NULL,
    equipment_type STRING,
    metric_name STRING NOT NULL,
    metric_value DOUBLE NOT NULL,
    unit STRING,
    site_name STRING,
    CONSTRAINT valid_value CHECK (metric_value IS NOT NULL)
)
PARTITIONED BY (DATE(timestamp))
CLUSTER BY (equipment_id)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);
```

**incidents:**
```sql
CREATE TABLE main.mining_ops.incidents (
    incident_id STRING NOT NULL PRIMARY KEY,
    equipment_id STRING NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    description STRING,
    root_cause STRING,
    downtime_hours DOUBLE,
    cost_usd DOUBLE,
    resolution STRING,
    technician STRING,
    severity STRING
)
PARTITIONED BY (DATE(timestamp))
CLUSTER BY (equipment_id);
```

**work_orders:**
```sql
CREATE TABLE main.mining_ops.work_orders (
    wo_id STRING NOT NULL PRIMARY KEY,
    equipment_id STRING NOT NULL,
    created_date DATE NOT NULL,
    wo_type STRING,
    status STRING,
    technician STRING,
    parts_used STRING,
    labor_hours DOUBLE,
    cost_usd DOUBLE,
    notes STRING
)
PARTITIONED BY (created_date)
CLUSTER BY (equipment_id);
```

---

## Performance Specifications

### Latency Targets

| Component | Target | Actual (Pilot) |
|-----------|--------|----------------|
| Ignition tag change → Bronze table | <1 sec | 0.4 sec |
| Bronze → Silver → Gold processing | <1 sec | 0.6 sec |
| Genie query execution (cold) | <10 sec | 6-8 sec |
| Genie query execution (warm) | <5 sec | 3-4 sec |
| Total: Alarm → AI response | <15 sec | 4-5 sec |

### Throughput

| Metric | Specification |
|--------|---------------|
| Tags ingested per second | 10,000+ |
| Concurrent Genie queries | 50+ |
| DLT pipeline records/sec | 50,000+ |
| SQL Warehouse QPS | 100+ |

### Availability

| Component | SLA | Redundancy |
|-----------|-----|------------|
| Ignition Gateway | 99.5% | HA pair (optional) |
| Databricks Lakehouse | 99.95% | Multi-AZ, auto-failover |
| Genie AI | 99.9% | Serverless, auto-scaling |
| SQL Warehouse | 99.9% | Auto-restart on failure |

---

## Security Architecture

### Network Security

**Connectivity:**
- Direction: Outbound only from OT network
- Protocol: HTTPS (TLS 1.3)
- Port: 443
- Destination: `*.databricks.com`

**Firewall Rules:**
```
# Allow outbound to Databricks
Source: Ignition Gateway IP (10.1.2.3)
Destination: *.databricks.com
Port: 443
Protocol: TCP
Action: Allow

# Block all inbound to OT network (default deny)
Source: Any
Destination: OT Network (10.1.0.0/16)
Action: Deny
```

**VPN/Private Link (Optional for High Security):**
- AWS PrivateLink: Direct connection bypassing public internet
- Azure Private Link: Similar capability for Azure
- VPN Tunnel: Encrypted tunnel if PrivateLink not available

---

### Authentication & Authorization

**User Authentication:**
- Method: SSO via Azure AD / Okta
- MFA: Required for all users
- Session Timeout: 8 hours

**Service Principal (for Connector):**
```python
# Databricks service principal for Zerobus connector
{
    "application_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "secret": "[stored in Ignition secure credential store]",
    "tenant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "scope": "write:bronze_tables"
}
```

**Unity Catalog RBAC:**
```sql
-- Operators: Read-only on Gold tables
GRANT SELECT ON SCHEMA main.mining_ops TO role_operator;
GRANT SELECT ON TABLE main.mining_ops.sensor_data_gold TO role_operator;
GRANT SELECT ON TABLE main.mining_ops.incidents TO role_operator;

-- Engineers: Read on all, write on Silver/Gold
GRANT SELECT, MODIFY ON SCHEMA main.mining_ops TO role_engineer;

-- Admins: Full access
GRANT ALL PRIVILEGES ON CATALOG main TO role_admin;
```

---

### Data Security

**Encryption:**
- At Rest: AES-256 encryption (cloud provider default)
- In Transit: TLS 1.3 (HTTPS)
- Backups: Encrypted with customer-managed keys (optional)

**Data Masking:**
```sql
-- Example: Mask sensitive columns for certain roles
CREATE VIEW main.mining_ops.work_orders_masked AS
SELECT
    wo_id,
    equipment_id,
    created_date,
    wo_type,
    status,
    CASE
        WHEN is_member('role_admin') THEN technician
        ELSE 'REDACTED'
    END AS technician,
    CASE
        WHEN is_member('role_admin') THEN cost_usd
        ELSE NULL
    END AS cost_usd
FROM main.mining_ops.work_orders;
```

**Audit Logging:**
- All SQL queries logged to `system.access.audit`
- Retention: 90 days
- Includes: User, timestamp, query, tables accessed, results returned

---

### Compliance

**Certifications:**
- SOC 2 Type II
- ISO 27001
- GDPR compliant (if EU data)
- HIPAA compliant (if healthcare data)

**Data Residency:**
- Australia: Databricks deployed in ap-southeast-2 (Sydney) region
- Data never leaves Australia

---

## Scalability & Growth Path

### Pilot Phase (Week 1-4)

**Scope:**
- 1 processing area (crushers)
- 500 tags
- 5-10 users
- 1 site

**Infrastructure:**
- DLT Pipeline: 2 workers (i3.xlarge)
- SQL Warehouse: Small (2 min clusters)
- Cost: ~$500-1,000/month compute

---

### Production Phase (Month 2-6)

**Scope:**
- 3 processing areas (crushers, haul trucks, conveyors)
- 2,000 tags
- 30-50 users
- 1 site

**Infrastructure:**
- DLT Pipeline: 4 workers (i3.xlarge)
- SQL Warehouse: Medium (4-8 clusters, auto-scaling)
- Cost: ~$2,000-4,000/month compute

---

### Enterprise Phase (Month 6+)

**Scope:**
- Full site integration (pit to port)
- 5,000+ tags
- 100+ users
- Multiple sites (2-5)

**Infrastructure:**
- DLT Pipeline: 8 workers (i3.2xlarge)
- SQL Warehouse: Large (8-16 clusters, serverless)
- Additional data sources: CMMS, ERP, lab systems
- Cost: ~$8,000-15,000/month compute

**Scaling Considerations:**
- Auto-scaling enabled (costs scale with usage)
- Partition strategy optimized for large datasets
- Query caching reduces repeated query costs
- Data lifecycle management (archive old data to cheaper storage)

---

## Integration Points

### Existing Systems

**ERP (SAP, Oracle):**
- Integration: Lakeflow connectors or REST APIs
- Data: Parts inventory, procurement costs, labor hours
- Frequency: Daily batch (overnight sync)

**CMMS (Maximo, SAP PM):**
- Integration: ODBC/JDBC or REST APIs
- Data: Work orders, maintenance schedules, technician assignments
- Frequency: Hourly incremental sync

**OSI PI Historian:**
- Integration: Databricks PI connector (native)
- Data: Historical tag data (years of history)
- Frequency: One-time backfill + ongoing incremental

**Litmus Edge / DeepIQ:**
- Integration: Native Databricks output
- Data: OT data from edge devices
- Frequency: Real-time streaming

---

## Disaster Recovery

### Backup Strategy

**Data Backups:**
- Delta Lake: Time travel (30-day retention default)
- Snapshots: Daily automated to separate storage account
- Retention: 90 days

**Configuration Backups:**
- DLT Pipeline: JSON definitions in Git
- Genie Instructions: Versioned in Git
- Ignition Project: Exported weekly to file share

**Recovery Time Objective (RTO):**
- Data: <1 hour (restore from snapshot)
- Pipeline: <30 minutes (redeploy from Git)
- Genie: <15 minutes (reconfigure space)

**Recovery Point Objective (RPO):**
- Data: <1 minute (real-time replication)
- Configurations: <24 hours (daily backups)

---

### Failure Scenarios

**Scenario 1: Databricks Unavailable**
- Impact: Genie chat offline, historical queries fail
- Mitigation: Ignition continues operating (alarms, control, dashboards)
- Recovery: Databricks auto-fails over to redundant AZ

**Scenario 2: Ignition Gateway Down**
- Impact: No new data ingestion, HMI offline
- Mitigation: HA Gateway pair (if configured)
- Recovery: Failover to secondary gateway (automatic)

**Scenario 3: Network Outage**
- Impact: Data buffered locally on Ignition
- Mitigation: 10,000-message local queue
- Recovery: Auto-resumes when network restored

**Scenario 4: SQL Warehouse Terminated**
- Impact: Queries fail temporarily
- Mitigation: Auto-restart on demand
- Recovery: <2 minutes to warm start

---

## Monitoring & Observability

### System Health Dashboards

**Databricks Monitoring:**
- DLT Pipeline: Execution time, record counts, failures
- SQL Warehouse: Query latency, cluster utilization, costs
- Genie: Query volume, response times, error rates

**Ignition Monitoring:**
- Gateway: CPU, memory, script execution times
- Tags: Update frequency, quality (good/bad/uncertain)
- Connector: Messages sent, retry counts, queue depth

**Alerts:**
- DLT Pipeline failure: Email to on-call engineer
- Connector queue >80% full: Investigate network
- Genie response time >10 sec: Scale SQL Warehouse

---

### Cost Monitoring

**Daily Cost Report:**
```sql
SELECT
    date,
    SUM(cost_usd) AS total_cost,
    SUM(CASE WHEN component = 'DLT' THEN cost_usd END) AS dlt_cost,
    SUM(CASE WHEN component = 'SQL_Warehouse' THEN cost_usd END) AS warehouse_cost,
    SUM(CASE WHEN component = 'Storage' THEN cost_usd END) AS storage_cost
FROM system.billing.usage
WHERE date >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY date
ORDER BY date DESC;
```

**Budget Alerts:**
- Warning: 80% of monthly budget consumed
- Critical: 100% of monthly budget exceeded
- Action: Throttle non-critical queries, optimize pipelines

---

## Appendix

### Glossary

**DLT:** Delta Live Tables - Databricks' declarative ETL framework
**Genie:** Databricks' natural language query interface (AI assistant)
**Unity Catalog:** Databricks' data governance layer
**Medallion Architecture:** Bronze (raw) → Silver (cleansed) → Gold (business-ready)
**Lakehouse:** Unified platform combining data lake + data warehouse capabilities

### Reference Documents

- Databricks Real-Time Mode: https://docs.databricks.com/structured-streaming/real-time-mode.html
- Unity Catalog RBAC: https://docs.databricks.com/data-governance/unity-catalog/manage-privileges/
- Genie Spaces: https://docs.databricks.com/genie/
- Ignition Perspective: https://docs.inductiveautomation.com/docs/8.1/getting-started/perspective/perspective-overview

---

**End of Technical Architecture Document**
