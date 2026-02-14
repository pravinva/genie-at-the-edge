# Mining Operations Real-Time DLT Pipeline

Production-ready Delta Live Tables pipeline for mining equipment monitoring with sub-second latency.

## Overview

This pipeline processes streaming OT sensor data from 15 pieces of mining equipment using Databricks Delta Live Tables Real-Time Mode. It implements the medallion architecture (Bronze → Silver → Gold) with comprehensive data quality checks and optimization.

## Architecture

```
Zerobus Stream → Bronze (Raw) → Silver (Normalized) → Gold (Analytics)
                    <1s            <500ms              <500ms
```

### Performance Targets

- Bronze ingestion: Immediate (Zerobus handles)
- Bronze → Silver: <500ms
- Silver → Gold: <500ms
- Total end-to-end: <1 second from event to queryable

## Pipeline Stages

### Bronze Layer: `ot_telemetry_bronze`
- Raw JSON data from Zerobus stream
- No transformations, preserves all data
- Auto-inferred schema with schema evolution
- Retention: 30 days

### Silver Layer: `ot_sensors_normalized`
- Flattened, normalized sensor readings
- Enriched with equipment metadata
- Data quality validations (null checks, range validation)
- Liquid clustering by equipment_id
- Retention: 90 days

### Gold Layer: Analytics Tables

1. **`equipment_performance_1min`**
   - 1-minute windowed aggregates
   - Metrics: avg, min, max, stddev, count
   - Partitioned by date
   - Liquid clustering on equipment_id + date

2. **`equipment_current_status`**
   - Latest reading per equipment/sensor
   - Materialized view for fast lookups
   - Updated in real-time

3. **`ml_predictions`**
   - Simple anomaly detection using statistical methods
   - Vibration and temperature anomaly detection
   - Confidence scores and recommendations
   - Ready for MLflow model integration

4. **`pipeline_quality_metrics`**
   - Pipeline health monitoring
   - Latency tracking
   - Data quality metrics

## Files

- `mining_realtime_dlt.py` - Main DLT pipeline (Python with @dlt decorators)
- `dimension_tables.sql` - Equipment master and dimension tables
- `genie_space_setup.sql` - Genie space configuration and instructions
- `deploy_pipeline.py` - Automated deployment script
- `validation_queries.sql` - Testing and validation queries
- `monitoring_dashboard.json` - Lakehouse monitoring dashboard configuration

## Deployment

### Prerequisites

1. Databricks Runtime 16.4+ (required for Real-Time Mode)
2. Unity Catalog enabled
3. Zerobus stream active and writing data
4. SQL Warehouse (Serverless with Photon recommended)

### Quick Start

1. **Create dimension tables first:**
   ```sql
   -- Run dimension_tables.sql in SQL editor
   ```

2. **Deploy DLT pipeline:**
   ```bash
   python deploy_pipeline.py
   ```

3. **Validate deployment:**
   ```sql
   -- Run queries from validation_queries.sql
   ```

### Manual Deployment

If automated deployment fails, create pipeline via UI:

1. Go to: Workflows → Delta Live Tables → Create Pipeline
2. Configuration:
   - **Name:** `mining_operations_realtime`
   - **Target:** `field_engineering.mining_demo`
   - **Notebook:** Path to `mining_realtime_dlt.py`
   - **Cluster Mode:** Enhanced Autoscaling
   - **Runtime:** 16.4 or higher
   - **Photon:** Enabled
   - **Node Type:** i3.xlarge or similar
   - **Min Workers:** 2
   - **Max Workers:** 4

3. Advanced Configuration:
   ```json
   {
     "spark.databricks.streaming.mode": "realtime",
     "spark.sql.shuffle.partitions": "200"
   }
   ```

4. Enable Development mode for testing

## Configuration

### Real-Time Mode

Every streaming table includes:
```python
table_properties={
    "pipelines.trigger.mode": "realtime",
    "pipelines.trigger.checkpoint": "1 minute"
}
```

### Data Quality Expectations

- `@dlt.expect_or_drop` - Drops invalid records
- `@dlt.expect_or_fail` - Fails pipeline on violation
- `@dlt.expect` - Logs but continues

### Optimization

- **Liquid Clustering:** Better than partitioning for streaming
- **Broadcast Joins:** For small dimension tables
- **Watermarking:** Handles late-arriving data (30s window)
- **Z-Ordering:** Run after initial load

## Monitoring

### Pipeline Health

Check DLT UI:
- Data Quality tab - expectation pass rates
- Progress tab - real-time updates
- Lineage graph - end-to-end flow with latencies

### SQL Monitoring

```sql
-- Check recent latency
SELECT
  avg(max_latency_sec) as avg_pipeline_latency,
  max(max_latency_sec) as max_pipeline_latency
FROM field_engineering.mining_demo.pipeline_quality_metrics
WHERE minute > CURRENT_TIMESTAMP - INTERVAL '10 minutes';

-- Target: avg < 1s, max < 2s
```

## Troubleshooting

### Pipeline Won't Start

- Verify Runtime >= 16.4
- Check cluster resources
- Validate Python syntax
- Ensure Zerobus stream exists

### High Latency (>5s)

- Reduce shuffle partitions (try 50-100)
- Verify broadcast joins for dimensions
- Check warehouse warmup time
- Add liquid clustering
- Run OPTIMIZE with ZORDER

### Data Quality Issues

- Check bronze for valid JSON
- Review expectation rules (may be too strict)
- Inspect quarantine table (`_rescued_data`)
- Validate Zerobus JSON format

### Real-Time Mode Errors

- Fallback to micro-batch mode
- Verify DBR 16.4+ support
- Check Databricks docs for latest requirements

## Genie Integration

After pipeline is running and gold tables populated:

1. Run `genie_space_setup.sql` to create Genie space
2. Configure instructions for mining operations context
3. Test sample questions in validation queries
4. Integrate with chat UI (see File 08)

## Performance Benchmarks

Expected throughput:
- 15 equipment × 10 sensors = 150 updates/second
- Bronze ingestion: ~2-3MB/minute
- Silver processing: <500ms per micro-batch
- Gold aggregation: <300ms per 1-minute window

Storage growth:
- Bronze: ~4GB/month
- Silver: ~6GB/month (normalized)
- Gold: ~2GB/month (aggregated)
- Total: ~12GB/month

Cost estimate (Databricks):
- DLT Real-Time: ~$30-40/month
- Storage: <$1/month
- SQL Warehouse queries: ~$30-50/month
- **Total: ~$60-90/month**

## Next Steps

1. Validate pipeline with validation_queries.sql
2. Set up monitoring dashboard
3. Create Genie space for natural language queries
4. Integrate with Ignition Perspective UI
5. Run 24-hour soak test
6. Production readiness review

## Support

For issues:
1. Check DLT Event Log in UI
2. Review system tables: `event_log('field_engineering.mining_demo')`
3. Validate dimension tables exist
4. Check Zerobus data flow
5. Review Databricks status page

## References

- [Delta Live Tables Docs](https://docs.databricks.com/delta-live-tables/)
- [Real-Time Mode Guide](https://docs.databricks.com/delta-live-tables/real-time.html)
- [Liquid Clustering](https://docs.databricks.com/delta/clustering.html)
- [Genie Documentation](https://docs.databricks.com/genie/)
