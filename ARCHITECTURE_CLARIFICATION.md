# Architecture Clarification: Data Sources

## Corrected Understanding

Based on typical industrial deployments, the data sources in our architecture should be:

### 1. IGNITION (Including Historian)
```
Ignition Gateway
├── Real-time Tags (current values via OPC UA)
├── Tag Historian Module (time-series storage)
│   ├── 90+ days of sensor history
│   ├── Automatic aggregations (hourly, daily)
│   ├── Trend data and baselines
│   └── Stored in: PostgreSQL or SQL Server
└── Alarm Journal (incident history)
```

**What Ignition Historian Provides:**
- Historical sensor trends (the "Historian" in the diagram)
- Baseline calculations (7-day, 30-day averages)
- Min/max/avg aggregations
- Alarm and event history
- Downtime tracking

### 2. MES (Manufacturing Execution System)
- **Separate System** (not part of Ignition)
- Common: SAP ME, Siemens Opcenter, Rockwell FactoryTalk
- Production schedules and work orders
- Quality management
- Batch tracking and genealogy

### 3. SAP ERP
- **Separate System** (enterprise level)
- Asset management (PM module)
- Maintenance planning (PM module)
- Spare parts inventory (MM module)
- Financial data (FI/CO modules)

## Revised Data Flow

```
┌────────────────────────────────────────┐
│           IGNITION GATEWAY             │
├────────────────┬───────────────────────┤
│ Real-time Tags │   Tag Historian       │
│   (Zerobus)    │  (90 days history)    │
└───────┬────────┴──────────┬────────────┘
        │                   │
        ▼                   ▼
    [Bronze]            [Bronze]
   (streaming)         (batch/sql)
        │                   │
        └─────────┬─────────┘
                  │
                  ▼
        ┌─────────────────┐      ┌─────┐    ┌─────┐
        │  Silver Layer   │◄─────│ MES │◄───│ SAP │
        │ (Unified View)  │      └─────┘    └─────┘
        └─────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │   Gold Layer    │
        │  (ML Features)  │
        └─────────────────┘
```

## How to Access Ignition Historian Data

### Option A: Direct SQL Query (Most Common)
```python
# In our DLT pipeline, query Ignition's historian database directly
historian_data = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://ignition-db:5432/historian") \
    .option("dbtable", """
        (SELECT
            tagpath,
            t_stamp,
            floatvalue,
            AVG(floatvalue) OVER (
                PARTITION BY tagpath
                ORDER BY t_stamp
                ROWS BETWEEN 10080 PRECEDING AND CURRENT ROW
            ) as baseline_7d
         FROM sqlt_data_1_2024_01
         WHERE t_stamp > CURRENT_DATE - INTERVAL '30 days') as hist
    """) \
    .option("user", "ignition") \
    .option("password", spark.conf.get("ignition.db.password")) \
    .load()
```

### Option B: Ignition Web Services
```python
# Query via Ignition's web API
import requests

def get_tag_history(tag_path, start_date, end_date):
    url = "http://ignition-gateway:8088/system/webdev/api/tagHistory"
    payload = {
        "tagPaths": [tag_path],
        "startDate": start_date,
        "endDate": end_date,
        "returnSize": 1000,
        "aggregationMode": "Average",
        "intervalMinutes": 60
    }
    response = requests.post(url, json=payload, auth=("api_user", "password"))
    return response.json()
```

### Option C: Ignition Tag Historian Splitter
```python
# Some setups use Ignition's "Historian Splitter" to stream to multiple destinations
# This sends historical data to both local storage AND Databricks

# In Ignition Gateway configuration:
# Tag Historian → Storage Providers → Add "Databricks Provider"
# This streams historian data directly to Delta Lake
```

## Updated Understanding for Our Implementation

For our demo, we're simulating the Ignition Historian as separate tables, but in production:

1. **Real-time data** comes via Zerobus (already implemented ✅)
2. **Historical data** would come from Ignition's Tag Historian via:
   - JDBC connection to Ignition's historian database
   - REST API calls to Ignition's WebDev module
   - Or direct streaming via Database Splitter

3. **MES and SAP** remain separate systems (correctly simulated ✅)

## Key Takeaway

The "Historian" bubble in the diagram is most likely **Ignition's own Tag Historian module**, not a separate enterprise historian. This is the most common configuration in industrial settings.

For enterprises with OSIsoft PI or other historians, Ignition can also push data there, but that's typically for:
- Multi-plant aggregation
- Long-term storage (10+ years)
- Enterprise-wide analytics
- Regulatory compliance

Our current simulation approach is still valid - we're just simulating what would normally be queried from Ignition's Tag Historian tables!