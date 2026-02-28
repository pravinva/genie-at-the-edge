-- Test Unified Query Across All Three Data Sources
-- This demonstrates querying Lakebase Historian + Zerobus Streaming + SAP/MES in one query

-- ==============================================================================
-- TEST 1: Verify All Tables Have Data
-- ==============================================================================

SELECT 'Historian Tags' as source, COUNT(*) as record_count
FROM pravin_ignition_managed.public.sqlth_te

UNION ALL

SELECT 'Historian Data', COUNT(*)
FROM pravin_ignition_managed.public.sqlt_data_1_2026_02

UNION ALL

SELECT 'Zerobus Streaming', COUNT(*)
FROM field_engineering.mining_demo.zerobus_sensor_stream

UNION ALL

SELECT 'SAP Equipment', COUNT(*)
FROM field_engineering.mining_demo.sap_equipment_master

UNION ALL

SELECT 'SAP Maintenance', COUNT(*)
FROM field_engineering.mining_demo.sap_maintenance_schedule

UNION ALL

SELECT 'SAP Parts', COUNT(*)
FROM field_engineering.mining_demo.sap_spare_parts

UNION ALL

SELECT 'MES Schedule', COUNT(*)
FROM field_engineering.mining_demo.mes_production_schedule;

-- ==============================================================================
-- TEST 2: Unified Query - Real-time + Historical + Business Context
-- ==============================================================================

WITH realtime AS (
    -- Current sensor values from Zerobus
    SELECT
        equipment_id,
        sensor_name,
        AVG(sensor_value) as current_avg,
        MAX(sensor_value) as current_max,
        COUNT(*) as sample_count
    FROM field_engineering.mining_demo.zerobus_sensor_stream
    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL 10 MINUTES
    GROUP BY equipment_id, sensor_name
),
historical AS (
    -- Historical baselines from Lakebase Historian
    SELECT
        SPLIT(t.tagpath, '/')[0] as equipment_id,
        SPLIT(t.tagpath, '/')[1] as sensor_name,
        AVG(d.floatvalue) as baseline_7d,
        STDDEV(d.floatvalue) as stddev_7d,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY d.floatvalue) as p95_value
    FROM pravin_ignition_managed.public.sqlt_data_1_2026_02 d
    JOIN pravin_ignition_managed.public.sqlth_te t ON d.tagid = t.id
    WHERE d.t_stamp > UNIX_MILLIS(CURRENT_TIMESTAMP - INTERVAL 7 DAYS)
    GROUP BY SPLIT(t.tagpath, '/')[0], SPLIT(t.tagpath, '/')[1]
),
business AS (
    -- Business context from SAP/MES
    SELECT
        e.equipment_id,
        e.criticality_rating,
        e.annual_maintenance_budget,
        DATEDIFF(DAY, CURRENT_DATE(), e.warranty_expiry) as warranty_days_remaining,
        m.next_scheduled_maintenance,
        DATEDIFF(DAY, CURRENT_DATE(), m.next_scheduled_maintenance) as days_to_maintenance,
        SUM(p.quantity_on_hand) as spare_parts_available,
        SUM(CASE WHEN p.quantity_on_hand = 0 THEN 1 ELSE 0 END) as parts_out_of_stock
    FROM field_engineering.mining_demo.sap_equipment_master e
    LEFT JOIN field_engineering.mining_demo.sap_maintenance_schedule m
        ON e.equipment_id = m.equipment_id
    LEFT JOIN field_engineering.mining_demo.sap_spare_parts p
        ON e.equipment_id = p.equipment_id
    GROUP BY e.equipment_id, e.criticality_rating, e.annual_maintenance_budget,
             e.warranty_expiry, m.next_scheduled_maintenance
)
SELECT
    r.equipment_id,
    r.sensor_name,
    r.current_avg as current_value,
    h.baseline_7d,
    r.current_avg - h.baseline_7d as deviation,
    (r.current_avg - h.baseline_7d) / NULLIF(h.stddev_7d, 0) as z_score,
    CASE
        WHEN ABS((r.current_avg - h.baseline_7d) / NULLIF(h.stddev_7d, 0)) > 3 THEN 'CRITICAL ANOMALY'
        WHEN ABS((r.current_avg - h.baseline_7d) / NULLIF(h.stddev_7d, 0)) > 2 THEN 'ANOMALY'
        WHEN ABS((r.current_avg - h.baseline_7d) / NULLIF(h.stddev_7d, 0)) > 1 THEN 'WARNING'
        ELSE 'NORMAL'
    END as status,
    b.criticality_rating,
    b.warranty_days_remaining,
    b.days_to_maintenance,
    b.spare_parts_available,
    b.parts_out_of_stock,
    CASE
        WHEN b.warranty_days_remaining < 0 THEN '🔴 OUT OF WARRANTY'
        WHEN b.warranty_days_remaining < 30 THEN '🟠 EXPIRING SOON'
        ELSE '🟢 UNDER WARRANTY'
    END as warranty_status,
    CASE
        WHEN b.days_to_maintenance < 7 THEN '🔴 MAINTENANCE DUE'
        WHEN b.days_to_maintenance < 30 THEN '🟠 MAINTENANCE SOON'
        ELSE '🟢 MAINTENANCE OK'
    END as maintenance_status,
    r.sample_count as samples_in_last_10min
FROM realtime r
LEFT JOIN historical h
    ON r.equipment_id = h.equipment_id AND r.sensor_name = h.sensor_name
LEFT JOIN business b
    ON r.equipment_id = b.equipment_id
WHERE h.baseline_7d IS NOT NULL
ORDER BY ABS((r.current_avg - h.baseline_7d) / NULLIF(h.stddev_7d, 0)) DESC
LIMIT 20;

-- ==============================================================================
-- TEST 3: Equipment Health Summary
-- ==============================================================================

SELECT
    e.equipment_id,
    e.criticality_rating,
    COUNT(DISTINCT CASE WHEN z.timestamp > CURRENT_TIMESTAMP - INTERVAL 1 HOUR THEN z.sensor_name END) as active_sensors,
    AVG(CASE WHEN z.sensor_name = 'temperature' THEN z.sensor_value END) as avg_temp,
    AVG(CASE WHEN z.sensor_name = 'vibration' THEN z.sensor_value END) as avg_vibration,
    DATEDIFF(DAY, CURRENT_DATE(), m.next_scheduled_maintenance) as days_to_maintenance,
    SUM(p.quantity_on_hand) as total_spare_parts,
    CASE
        WHEN e.criticality_rating = 'A' THEN 'CRITICAL EQUIPMENT'
        WHEN e.criticality_rating = 'B' THEN 'IMPORTANT EQUIPMENT'
        ELSE 'STANDARD EQUIPMENT'
    END as priority
FROM field_engineering.mining_demo.sap_equipment_master e
LEFT JOIN field_engineering.mining_demo.zerobus_sensor_stream z
    ON e.equipment_id = z.equipment_id
    AND z.timestamp > CURRENT_TIMESTAMP - INTERVAL 1 HOUR
LEFT JOIN field_engineering.mining_demo.sap_maintenance_schedule m
    ON e.equipment_id = m.equipment_id
LEFT JOIN field_engineering.mining_demo.sap_spare_parts p
    ON e.equipment_id = p.equipment_id
GROUP BY e.equipment_id, e.criticality_rating, m.next_scheduled_maintenance
ORDER BY e.criticality_rating, e.equipment_id;

-- ==============================================================================
-- TEST 4: Historical Trend Analysis
-- ==============================================================================

SELECT
    SPLIT(t.tagpath, '/')[0] as equipment_id,
    SPLIT(t.tagpath, '/')[1] as sensor_type,
    DATE(TIMESTAMP_MILLIS(d.t_stamp)) as date,
    COUNT(*) as reading_count,
    AVG(d.floatvalue) as daily_avg,
    MIN(d.floatvalue) as daily_min,
    MAX(d.floatvalue) as daily_max,
    STDDEV(d.floatvalue) as daily_stddev
FROM pravin_ignition_managed.public.sqlt_data_1_2026_02 d
JOIN pravin_ignition_managed.public.sqlth_te t ON d.tagid = t.id
WHERE d.t_stamp > UNIX_MILLIS(CURRENT_TIMESTAMP - INTERVAL 7 DAYS)
  AND SPLIT(t.tagpath, '/')[0] IN ('HAUL-001', 'CRUSH-001')
  AND SPLIT(t.tagpath, '/')[1] IN ('temperature', 'vibration')
GROUP BY SPLIT(t.tagpath, '/')[0], SPLIT(t.tagpath, '/')[1], DATE(TIMESTAMP_MILLIS(d.t_stamp))
ORDER BY equipment_id, sensor_type, date DESC;

-- ==============================================================================
-- TEST 5: Operational Intelligence Summary
-- ==============================================================================

WITH current_shift AS (
    SELECT shift, planned_throughput_tph, product_type
    FROM field_engineering.mining_demo.mes_production_schedule
    WHERE schedule_hour <= CURRENT_TIMESTAMP
    ORDER BY schedule_hour DESC
    LIMIT 1
)
SELECT
    cs.shift as current_shift,
    cs.product_type,
    cs.planned_throughput_tph,
    COUNT(DISTINCT e.equipment_id) as total_equipment,
    SUM(CASE WHEN b.criticality_rating = 'A' THEN 1 ELSE 0 END) as critical_equipment,
    SUM(CASE WHEN DATEDIFF(DAY, CURRENT_DATE(), m.next_scheduled_maintenance) < 7 THEN 1 ELSE 0 END) as maintenance_due_soon,
    SUM(CASE WHEN DATEDIFF(DAY, CURRENT_DATE(), b.warranty_expiry) < 0 THEN 1 ELSE 0 END) as out_of_warranty,
    COUNT(DISTINCT z.equipment_id) as equipment_reporting_last_hour,
    ROUND(COUNT(DISTINCT z.equipment_id) * 100.0 / COUNT(DISTINCT e.equipment_id), 1) as availability_percent
FROM current_shift cs
CROSS JOIN field_engineering.mining_demo.sap_equipment_master b
LEFT JOIN field_engineering.mining_demo.zerobus_sensor_stream z
    ON b.equipment_id = z.equipment_id
    AND z.timestamp > CURRENT_TIMESTAMP - INTERVAL 1 HOUR
LEFT JOIN field_engineering.mining_demo.sap_maintenance_schedule m
    ON b.equipment_id = m.equipment_id
LEFT JOIN field_engineering.mining_demo.sap_equipment_master e
    ON 1=1
GROUP BY cs.shift, cs.product_type, cs.planned_throughput_tph;