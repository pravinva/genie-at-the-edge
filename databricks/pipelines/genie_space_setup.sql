-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Genie Space Configuration for Mining Operations
-- MAGIC
-- MAGIC **Purpose:** Create and configure Genie space for natural language queries on mining equipment data
-- MAGIC
-- MAGIC **Prerequisites:**
-- MAGIC - DLT pipeline running with gold tables populated
-- MAGIC - SQL Warehouse available (Serverless with Photon recommended)
-- MAGIC
-- MAGIC **Target Response Time:** <5 seconds for typical queries

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1. Create Genie Space (via UI - instructions below)
-- MAGIC
-- MAGIC **Cannot be created via SQL - must use Databricks UI:**
-- MAGIC
-- MAGIC 1. Navigate to: **AI & ML → Genie**
-- MAGIC 2. Click: **Create Genie Space**
-- MAGIC 3. Configure:
-- MAGIC    - **Name:** Mining Operations Intelligence
-- MAGIC    - **Description:** Natural language insights for mining equipment monitoring and predictive maintenance
-- MAGIC    - **SQL Warehouse:** 4b9b953939869799 (or your Serverless warehouse)
-- MAGIC    - **Default Catalog:** field_engineering
-- MAGIC    - **Default Schema:** mining_demo
-- MAGIC
-- MAGIC 4. Click: **Create**
-- MAGIC 5. Copy the Space ID from URL for chat UI integration

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2. Add Tables to Genie Space
-- MAGIC
-- MAGIC After creating the space, add these tables:
-- MAGIC
-- MAGIC **Gold Tables (Primary):**
-- MAGIC - `equipment_performance_1min` - Recent performance metrics
-- MAGIC - `equipment_current_status` - Real-time status
-- MAGIC - `ml_predictions` - Anomaly alerts
-- MAGIC - `equipment_performance_1hour` - Historical trends
-- MAGIC
-- MAGIC **Dimension Tables (Supporting):**
-- MAGIC - `equipment_master` - Equipment metadata
-- MAGIC - `sensor_definitions` - Sensor information
-- MAGIC - `location_hierarchy` - Location details
-- MAGIC - `shift_schedule` - Shift information
-- MAGIC
-- MAGIC **In Genie UI:**
-- MAGIC 1. Click "Add tables"
-- MAGIC 2. Select all tables above
-- MAGIC 3. Click "Add"

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. Configure Genie Instructions
-- MAGIC
-- MAGIC **In Genie Space Settings → Instructions:**
-- MAGIC
-- MAGIC Copy and paste this instruction set:

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ```
-- MAGIC You are an AI assistant for mining operations, specializing in equipment monitoring, predictive maintenance, and production analytics.
-- MAGIC
-- MAGIC CONTEXT:
-- MAGIC - You have access to real-time sensor data from 15 pieces of mining equipment
-- MAGIC - Data updates every minute with sub-second latency
-- MAGIC - Equipment types: Crushers, Conveyors, Stackers, Reclaimers, Ship Loaders, Screens, Feeders
-- MAGIC - Key sensors: Vibration, Temperature, Production Rate, Speed, Power
-- MAGIC - Site operates 24/7 with 3 shifts: Day (6am-2pm), Afternoon (2pm-10pm), Night (10pm-6am)
-- MAGIC
-- MAGIC PRIMARY TABLES:
-- MAGIC - equipment_performance_1min: 1-minute aggregates (use for recent trends, last hour, current performance)
-- MAGIC - equipment_current_status: Latest reading per sensor (use for "current status", "right now" questions)
-- MAGIC - ml_predictions: Anomaly alerts (use for "issues", "problems", "abnormal" queries)
-- MAGIC - equipment_performance_1hour: Hourly rollups (use for historical analysis, day/week comparisons)
-- MAGIC
-- MAGIC QUERY GUIDELINES:
-- MAGIC
-- MAGIC 1. TIME REFERENCES:
-- MAGIC    - "now", "current" → equipment_current_status
-- MAGIC    - "last hour", "recent" → equipment_performance_1min WHERE window_start > CURRENT_TIMESTAMP - INTERVAL '1 hour'
-- MAGIC    - "today" → equipment_performance_1hour WHERE date = CURRENT_DATE
-- MAGIC    - "this week" → equipment_performance_1hour WHERE date >= DATE_TRUNC('week', CURRENT_DATE)
-- MAGIC
-- MAGIC 2. EQUIPMENT REFERENCES:
-- MAGIC    - Use LIKE for partial matches: "crusher" → WHERE equipment_id LIKE 'CR_%' OR equipment_type = 'Crusher'
-- MAGIC    - Common IDs: CR_001/002 (Crushers), CV_001-004 (Conveyors), ST_001/002 (Stackers), RC_001/002 (Reclaimers), SL_001/002 (Ship Loaders)
-- MAGIC
-- MAGIC 3. SENSOR REFERENCES:
-- MAGIC    - Vibration: sensor_name LIKE '%Vibration%'
-- MAGIC    - Temperature: sensor_name LIKE '%Temperature%'
-- MAGIC    - Production: sensor_name LIKE '%Production%' OR sensor_name LIKE '%Tonnage%'
-- MAGIC    - Speed: sensor_name LIKE '%Speed%' OR sensor_name LIKE '%RPM%'
-- MAGIC
-- MAGIC 4. ANOMALY/ISSUE QUERIES:
-- MAGIC    - Always check ml_predictions table first
-- MAGIC    - Include severity, recommendation, confidence_score
-- MAGIC    - Sort by deviation_score DESC to show most critical first
-- MAGIC    - Filter: WHERE prediction_time > CURRENT_TIMESTAMP - INTERVAL '24 hours'
-- MAGIC
-- MAGIC 5. COMPARISON QUERIES:
-- MAGIC    - Use window functions for shift-over-shift, day-over-day comparisons
-- MAGIC    - Join with shift_schedule for business context
-- MAGIC    - Include percentage changes in results
-- MAGIC
-- MAGIC 6. RESPONSE FORMAT:
-- MAGIC    - Start with direct answer (yes/no, count, value)
-- MAGIC    - Provide context and explanation
-- MAGIC    - Include actionable recommendations if issues found
-- MAGIC    - Add relevant thresholds and normal ranges
-- MAGIC    - Suggest follow-up questions
-- MAGIC
-- MAGIC EXAMPLE QUERIES:
-- MAGIC
-- MAGIC Q: "What's the current status of CR_002?"
-- MAGIC A: Query equipment_current_status WHERE equipment_id = 'CR_002', show all sensors with values, highlight any out-of-range
-- MAGIC
-- MAGIC Q: "Any equipment issues right now?"
-- MAGIC A: Query ml_predictions WHERE prediction_time > CURRENT_TIMESTAMP - INTERVAL '1 hour' ORDER BY severity DESC
-- MAGIC
-- MAGIC Q: "How is crusher performance today vs yesterday?"
-- MAGIC A: Compare equipment_performance_1hour for equipment_type = 'Crusher' between CURRENT_DATE and CURRENT_DATE - 1
-- MAGIC
-- MAGIC Q: "Which equipment has highest vibration?"
-- MAGIC A: Query equipment_current_status WHERE sensor_name LIKE '%Vibration%' ORDER BY sensor_value DESC LIMIT 5
-- MAGIC
-- MAGIC IMPORTANT:
-- MAGIC - Always consider criticality when prioritizing issues (Critical > High > Medium > Low)
-- MAGIC - Include equipment_type and location in responses for context
-- MAGIC - Round numeric values appropriately (2 decimals for sensor values)
-- MAGIC - Use proper units (mm/s for vibration, °C for temperature, t/h for production)
-- MAGIC - Suggest preventive actions based on trends, not just current values
-- MAGIC - If no data found, explain possible reasons (equipment offline, sensor issue, time range)
-- MAGIC
-- MAGIC TONE:
-- MAGIC - Professional and concise
-- MAGIC - Focus on actionable insights
-- MAGIC - Assume user is operations personnel (not data scientist)
-- MAGIC - Use mining/industrial terminology appropriately
-- MAGIC - Highlight urgent issues prominently
-- MAGIC ```

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Add Sample Questions
-- MAGIC
-- MAGIC **In Genie Space → Sample Questions:**
-- MAGIC
-- MAGIC Add these frequently asked questions:

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Real-Time Status Questions:
-- MAGIC - What's the current status of all crushers?
-- MAGIC - Show me equipment with high vibration right now
-- MAGIC - Which equipment has abnormal temperature readings?
-- MAGIC - What is the current production rate across all conveyors?
-- MAGIC - Is equipment CR_002 operating normally?
-- MAGIC
-- MAGIC ### Issue Detection Questions:
-- MAGIC - Are there any equipment issues or anomalies?
-- MAGIC - What equipment needs attention today?
-- MAGIC - Show me all critical alerts in the last hour
-- MAGIC - Which sensors are showing abnormal readings?
-- MAGIC - List equipment with potential failures
-- MAGIC
-- MAGIC ### Performance Analysis Questions:
-- MAGIC - How is crusher performance today compared to yesterday?
-- MAGIC - What was the average production rate last hour?
-- MAGIC - Show equipment utilization by shift today
-- MAGIC - Which equipment has the most downtime this week?
-- MAGIC - Compare conveyor speeds across all systems
-- MAGIC
-- MAGIC ### Trend Analysis Questions:
-- MAGIC - Show vibration trends for CR_001 over the last 4 hours
-- MAGIC - How has production varied throughout the day?
-- MAGIC - What's the temperature trend for all ship loaders?
-- MAGIC - Plot power consumption by equipment type today
-- MAGIC - Show me performance degradation patterns this week
-- MAGIC
-- MAGIC ### Predictive Maintenance Questions:
-- MAGIC - Which equipment is most likely to fail soon?
-- MAGIC - Show me anomaly predictions with high confidence
-- MAGIC - What maintenance actions are recommended?
-- MAGIC - List equipment approaching maintenance intervals
-- MAGIC - Are there any recurring issues with specific equipment?
-- MAGIC
-- MAGIC ### Operational Questions:
-- MAGIC - What's the total tonnage processed today?
-- MAGIC - Which shift had the best production?
-- MAGIC - Show me equipment by criticality level
-- MAGIC - What equipment is currently offline or stale?
-- MAGIC - List all critical equipment in Port Terminal area

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 5. Test Genie Space with Validation Queries

-- COMMAND ----------

-- Test Query 1: Current status check
-- Try in Genie: "What's the current status of all crushers?"
-- Expected: Latest sensor readings for CR_001 and CR_002

SELECT
  equipment_id,
  equipment_type,
  sensor_name,
  sensor_value,
  event_timestamp,
  criticality,
  status
FROM field_engineering.mining_demo.equipment_current_status
WHERE equipment_type = 'Crusher'
ORDER BY equipment_id, sensor_name;

-- COMMAND ----------

-- Test Query 2: Recent anomalies
-- Try in Genie: "Are there any equipment issues right now?"
-- Expected: Recent anomaly predictions with recommendations

SELECT
  equipment_id,
  sensor_name,
  prediction_type,
  severity,
  current_value,
  baseline_avg,
  deviation_score,
  recommendation,
  prediction_time
FROM field_engineering.mining_demo.ml_predictions
WHERE prediction_time > CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY severity DESC, deviation_score DESC
LIMIT 10;

-- COMMAND ----------

-- Test Query 3: Performance comparison
-- Try in Genie: "How is crusher performance today vs yesterday?"
-- Expected: Comparison of production rates and key metrics

WITH today AS (
  SELECT
    equipment_id,
    AVG(avg_value) as avg_production
  FROM field_engineering.mining_demo.equipment_performance_1hour
  WHERE date = CURRENT_DATE
    AND sensor_name = 'Production_Rate_TPH'
    AND equipment_type = 'Crusher'
  GROUP BY equipment_id
),
yesterday AS (
  SELECT
    equipment_id,
    AVG(avg_value) as avg_production
  FROM field_engineering.mining_demo.equipment_performance_1hour
  WHERE date = CURRENT_DATE - INTERVAL '1 day'
    AND sensor_name = 'Production_Rate_TPH'
    AND equipment_type = 'Crusher'
  GROUP BY equipment_id
)
SELECT
  t.equipment_id,
  ROUND(t.avg_production, 2) as today_avg_tph,
  ROUND(y.avg_production, 2) as yesterday_avg_tph,
  ROUND(t.avg_production - y.avg_production, 2) as change_tph,
  ROUND(((t.avg_production - y.avg_production) / y.avg_production) * 100, 1) as change_pct
FROM today t
LEFT JOIN yesterday y ON t.equipment_id = y.equipment_id
ORDER BY change_pct DESC;

-- COMMAND ----------

-- Test Query 4: Vibration monitoring
-- Try in Genie: "Show me equipment with highest vibration right now"
-- Expected: Top 5 equipment by vibration level

SELECT
  equipment_id,
  equipment_type,
  location,
  criticality,
  sensor_value as vibration_mm_s,
  event_timestamp,
  CASE
    WHEN sensor_value > 10 THEN 'CRITICAL'
    WHEN sensor_value > 7 THEN 'HIGH'
    WHEN sensor_value > 5 THEN 'MEDIUM'
    ELSE 'NORMAL'
  END as vibration_status
FROM field_engineering.mining_demo.equipment_current_status
WHERE sensor_name LIKE '%Vibration%'
ORDER BY sensor_value DESC
LIMIT 5;

-- COMMAND ----------

-- Test Query 5: Equipment availability
-- Try in Genie: "Which equipment is currently offline or stale?"
-- Expected: Equipment not reporting recent data

SELECT
  equipment_id,
  equipment_type,
  location,
  criticality,
  MAX(event_timestamp) as last_seen,
  ROUND((UNIX_TIMESTAMP(CURRENT_TIMESTAMP()) - UNIX_TIMESTAMP(MAX(event_timestamp))) / 60, 1) as minutes_ago,
  CASE
    WHEN MAX(event_timestamp) < CURRENT_TIMESTAMP - INTERVAL '10 minutes' THEN 'OFFLINE'
    WHEN MAX(event_timestamp) < CURRENT_TIMESTAMP - INTERVAL '5 minutes' THEN 'STALE'
    ELSE 'ONLINE'
  END as connection_status
FROM field_engineering.mining_demo.equipment_current_status
GROUP BY equipment_id, equipment_type, location, criticality
HAVING MAX(event_timestamp) < CURRENT_TIMESTAMP - INTERVAL '5 minutes'
ORDER BY criticality DESC, last_seen ASC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 6. Performance Optimization

-- COMMAND ----------

-- Add liquid clustering to gold tables (if not already applied)
-- This significantly improves Genie query performance

ALTER TABLE field_engineering.mining_demo.equipment_performance_1min
CLUSTER BY (equipment_id, date);

ALTER TABLE field_engineering.mining_demo.equipment_current_status
CLUSTER BY (equipment_id, sensor_name);

ALTER TABLE field_engineering.mining_demo.ml_predictions
CLUSTER BY (equipment_id, date);

-- COMMAND ----------

-- Run OPTIMIZE to apply clustering
OPTIMIZE field_engineering.mining_demo.equipment_performance_1min;
OPTIMIZE field_engineering.mining_demo.equipment_current_status;
OPTIMIZE field_engineering.mining_demo.ml_predictions;
OPTIMIZE field_engineering.mining_demo.equipment_performance_1hour;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 7. Grant Genie Access

-- COMMAND ----------

-- Grant warehouse usage permissions
-- Replace with your actual warehouse ID if different
-- GRANT USAGE ON WAREHOUSE `4b9b953939869799` TO `account users`;

-- Grant select permissions on all tables
GRANT SELECT ON TABLE field_engineering.mining_demo.equipment_performance_1min TO `account users`;
GRANT SELECT ON TABLE field_engineering.mining_demo.equipment_current_status TO `account users`;
GRANT SELECT ON TABLE field_engineering.mining_demo.ml_predictions TO `account users`;
GRANT SELECT ON TABLE field_engineering.mining_demo.equipment_performance_1hour TO `account users`;
GRANT SELECT ON TABLE field_engineering.mining_demo.pipeline_quality_metrics TO `account users`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 8. Get Genie Space Details for Chat UI

-- COMMAND ----------

-- After creating Genie space, note these details:

-- MAGIC %md
-- MAGIC ```
-- MAGIC GENIE_SPACE_ID: [Copy from URL after creating space]
-- MAGIC WORKSPACE_URL: https://your-workspace.cloud.databricks.com
-- MAGIC SQL_WAREHOUSE_ID: 4b9b953939869799
-- MAGIC
-- MAGIC API Endpoint:
-- MAGIC POST https://your-workspace.cloud.databricks.com/api/2.0/genie/spaces/{space_id}/start-conversation
-- MAGIC
-- MAGIC Required Headers:
-- MAGIC - Authorization: Bearer {databricks_token}
-- MAGIC - Content-Type: application/json
-- MAGIC
-- MAGIC Request Body:
-- MAGIC {
-- MAGIC   "content": "What's the current status of all crushers?"
-- MAGIC }
-- MAGIC
-- MAGIC Use these values in the chat UI configuration (File 08)
-- MAGIC ```

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 9. Monitor Genie Performance

-- COMMAND ----------

-- Check most asked questions (after Genie space is used)
-- This helps optimize instructions and add more sample questions

-- Note: Query logs available in System Tables
-- SELECT * FROM system.query.history
-- WHERE warehouse_id = '4b9b953939869799'
--   AND statement_text LIKE '%mining_demo%'
-- ORDER BY start_time DESC
-- LIMIT 20;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Setup Complete
-- MAGIC
-- MAGIC Next steps:
-- MAGIC 1. Verify Genie space responds correctly to sample questions
-- MAGIC 2. Note Space ID for chat UI integration
-- MAGIC 3. Test response times (<5s target)
-- MAGIC 4. Refine instructions based on actual query patterns
-- MAGIC 5. Add more sample questions based on operator feedback
-- MAGIC
-- MAGIC Integration ready for File 08: Chat UI implementation
