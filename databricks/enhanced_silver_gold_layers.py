"""
Enhanced Silver and Gold Layers with Enterprise Data Integration
This implements the full architecture from the diagram with Historian, MES, and SAP enrichment
"""

import dlt
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Configuration
CATALOG = "field_engineering"
SCHEMA = "mining_demo"

# ============================================================================
# ENHANCED SILVER LAYER - Unified Business Context
# ============================================================================

@dlt.table(
    name="silver_unified_context",
    comment="Sensor data enriched with Historian, MES, and SAP context",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.managed": "true"
    }
)
@dlt.expect_all({
    "valid_sensor": "sensor_value IS NOT NULL",
    "has_equipment": "equipment_id IS NOT NULL"
})
def silver_unified_context():
    """
    Silver layer that combines real-time sensor data with enterprise context
    This is what makes recommendations intelligent and actionable
    """

    # Real-time sensor data
    sensors = dlt.read_stream("ot_sensors_normalized")

    # Historical baselines from Historian
    historian = spark.read.table(f"{CATALOG}.{SCHEMA}.historian_baselines") \
        .filter(col("date") == current_date()) \
        .select(
            "equipment_id",
            "baseline_temp_7d",
            "baseline_temp_30d",
            "baseline_vibration_7d",
            "baseline_vibration_30d",
            "anomaly_count"
        )

    # Current production context from MES
    mes_schedule = spark.read.table(f"{CATALOG}.{SCHEMA}.mes_production_schedule") \
        .filter(col("schedule_hour").between(
            current_timestamp(),
            current_timestamp() + expr("INTERVAL 1 HOUR")
        )) \
        .select(
            "shift",
            "planned_throughput_tph",
            "product_type",
            "quality_target",
            "crew_size",
            "priority"
        ).limit(1)

    # Asset and maintenance data from SAP
    sap_assets = spark.read.table(f"{CATALOG}.{SCHEMA}.sap_asset_registry") \
        .select(
            "equipment_id",
            "criticality_rating",
            "annual_maintenance_budget",
            "warranty_expiry",
            datediff(col("warranty_expiry"), current_date()).alias("days_until_warranty_expiry")
        )

    # Recent maintenance history
    sap_maintenance = spark.read.table(f"{CATALOG}.{SCHEMA}.sap_maintenance_history") \
        .groupBy("equipment_id") \
        .agg(
            max("maintenance_date").alias("last_maintenance_date"),
            max("next_scheduled").alias("next_scheduled_maintenance"),
            sum(when(col("maintenance_type") == "breakdown", 1).otherwise(0)).alias("breakdown_count_ytd")
        )

    # Spare parts availability
    sap_parts = spark.read.table(f"{CATALOG}.{SCHEMA}.sap_spare_parts") \
        .groupBy("equipment_id") \
        .agg(
            sum("quantity_on_hand").alias("total_spare_parts"),
            sum(when(col("quantity_on_hand") == 0, 1).otherwise(0)).alias("parts_out_of_stock"),
            min("lead_time_days").alias("min_part_lead_time")
        )

    # Join everything together
    enriched = (
        sensors
        # Add historian baselines
        .join(broadcast(historian), on="equipment_id", how="left")
        # Add MES production context (cartesian but small)
        .crossJoin(broadcast(mes_schedule))
        # Add SAP asset data
        .join(broadcast(sap_assets), on="equipment_id", how="left")
        # Add maintenance history
        .join(broadcast(sap_maintenance), on="equipment_id", how="left")
        # Add spare parts
        .join(broadcast(sap_parts), on="equipment_id", how="left")
        # Calculate intelligent features
        .withColumn("temp_deviation_from_baseline",
            when(col("sensor_name") == "temperature",
                 col("sensor_value") - coalesce(col("baseline_temp_7d"), lit(75.0))
            ).otherwise(lit(0))
        )
        .withColumn("vibration_deviation_from_baseline",
            when(col("sensor_name") == "vibration",
                 col("sensor_value") - coalesce(col("baseline_vibration_7d"), lit(3.0))
            ).otherwise(lit(0))
        )
        .withColumn("maintenance_urgency_score",
            when(datediff(col("next_scheduled_maintenance"), current_date()) < 7, 3)
            .when(datediff(col("next_scheduled_maintenance"), current_date()) < 30, 2)
            .otherwise(1)
        )
        .withColumn("operational_risk_score",
            (
                when(col("criticality_rating") == "A", 3).otherwise(1) +
                when(col("days_until_warranty_expiry") < 0, 2).otherwise(0) +
                when(col("parts_out_of_stock") > 0, 1).otherwise(0) +
                when(col("breakdown_count_ytd") > 2, 2).otherwise(0)
            )
        )
        .withColumn("business_context",
            concat(
                lit("Shift: "), col("shift"),
                lit(", Product: "), col("product_type"),
                lit(", Criticality: "), col("criticality_rating"),
                lit(", Warranty: "),
                when(col("days_until_warranty_expiry") < 0, "EXPIRED")
                .when(col("days_until_warranty_expiry") < 30, "EXPIRING SOON")
                .otherwise("ACTIVE")
            )
        )
    )

    return enriched

# ============================================================================
# ENHANCED GOLD LAYER - Intelligent Analytics
# ============================================================================

@dlt.table(
    name="gold_intelligent_anomalies",
    comment="ML-ready anomaly detection with full business context",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.managed": "true"
    }
)
def gold_intelligent_anomalies():
    """
    Gold layer that detects anomalies with business awareness
    Not just "temperature is high" but "temperature is high during critical production with no spare parts"
    """

    silver = dlt.read_stream("silver_unified_context")

    anomalies = (
        silver
        # Detect contextual anomalies
        .withColumn("is_contextual_anomaly",
            # Temperature anomaly considering shift and baseline
            when(
                (col("sensor_name") == "temperature") &
                (col("temp_deviation_from_baseline") > 10) &
                (col("shift") == "Night"),  # Worse at night with reduced crew
                lit(True)
            )
            # Vibration anomaly considering maintenance schedule
            .when(
                (col("sensor_name") == "vibration") &
                (col("vibration_deviation_from_baseline") > 1.0) &
                (col("maintenance_urgency_score") >= 2),  # Near maintenance window
                lit(True)
            )
            .otherwise(lit(False))
        )
        # Calculate business impact
        .withColumn("estimated_impact_usd",
            when(col("is_contextual_anomaly"),
                col("planned_throughput_tph") * 100 * # $/ton
                when(col("criticality_rating") == "A", 5.0)
                .when(col("criticality_rating") == "B", 2.0)
                .otherwise(1.0)
            ).otherwise(lit(0))
        )
        # Generate intelligent alert priority
        .withColumn("alert_priority",
            when(
                (col("is_contextual_anomaly")) &
                (col("operational_risk_score") > 5) &
                (col("estimated_impact_usd") > 10000),
                "CRITICAL"
            )
            .when(
                (col("is_contextual_anomaly")) &
                (col("operational_risk_score") > 3),
                "HIGH"
            )
            .when(col("is_contextual_anomaly"), "MEDIUM")
            .otherwise("LOW")
        )
        # Only keep anomalies
        .filter(col("is_contextual_anomaly") == True)
    )

    return anomalies

@dlt.table(
    name="gold_predictive_maintenance",
    comment="Predictive maintenance recommendations with parts availability",
    table_properties={
        "quality": "gold"
    }
)
def gold_predictive_maintenance():
    """
    Combine sensor trends with maintenance history and parts availability
    Produces actionable maintenance recommendations
    """

    # Get equipment performance trends
    performance = spark.sql(f"""
        SELECT
            equipment_id,
            sensor_name,
            AVG(sensor_value) as avg_value_24h,
            STDDEV(sensor_value) as stddev_value_24h,
            MAX(sensor_value) as max_value_24h,
            -- Trend analysis
            CASE
                WHEN AVG(sensor_value) > LAG(AVG(sensor_value), 7) OVER (PARTITION BY equipment_id, sensor_name ORDER BY date)
                THEN 'INCREASING'
                ELSE 'STABLE'
            END as trend_7d
        FROM {CATALOG}.{SCHEMA}.silver_unified_context
        WHERE event_timestamp > current_timestamp() - INTERVAL 24 HOURS
        GROUP BY equipment_id, sensor_name, date(event_timestamp)
    """)

    # Join with maintenance and parts data
    maintenance_insights = (
        performance
        .join(
            spark.read.table(f"{CATALOG}.{SCHEMA}.sap_maintenance_history"),
            on="equipment_id"
        )
        .join(
            spark.read.table(f"{CATALOG}.{SCHEMA}.sap_spare_parts"),
            on="equipment_id"
        )
        .withColumn("maintenance_recommendation",
            when(
                (col("trend_7d") == "INCREASING") &
                (col("sensor_name") == "vibration") &
                (col("part_number").contains("BRG")) &
                (col("quantity_on_hand") > 0),
                concat(
                    lit("Schedule bearing replacement. Part "),
                    col("part_number"),
                    lit(" available ("), col("quantity_on_hand"), lit(" units). "),
                    lit("Estimated downtime: 4 hours. "),
                    lit("Next maintenance window: "), col("next_scheduled")
                )
            )
            .when(
                (col("trend_7d") == "INCREASING") &
                (col("sensor_name") == "temperature") &
                (col("quantity_on_hand") == 0),
                concat(
                    lit("ORDER PARTS IMMEDIATELY. "),
                    col("description"),
                    lit(" out of stock. Lead time: "),
                    col("lead_time_days"), lit(" days. "),
                    lit("Risk of unplanned downtime: HIGH")
                )
            )
            .otherwise(lit("Continue monitoring"))
        )
        .filter(col("maintenance_recommendation") != "Continue monitoring")
    )

    return maintenance_insights

@dlt.table(
    name="gold_production_optimization",
    comment="Production optimization insights combining OT and IT data",
    table_properties={
        "quality": "gold"
    }
)
def gold_production_optimization():
    """
    Optimize production based on equipment health, quality metrics, and schedules
    This is where OT meets IT for business value
    """

    return spark.sql(f"""
        WITH equipment_health AS (
            SELECT
                equipment_id,
                AVG(operational_risk_score) as avg_risk_score,
                MAX(CASE WHEN sensor_name = 'throughput' THEN sensor_value END) as actual_throughput,
                FIRST(planned_throughput_tph) as planned_throughput
            FROM {CATALOG}.{SCHEMA}.silver_unified_context
            WHERE event_timestamp > current_timestamp() - INTERVAL 1 HOUR
            GROUP BY equipment_id
        ),
        quality_impact AS (
            SELECT
                AVG(quality_score) as avg_quality,
                MIN(quality_score) as min_quality,
                quality_target
            FROM {CATALOG}.{SCHEMA}.mes_quality_metrics
            WHERE sample_timestamp > current_timestamp() - INTERVAL 24 HOURS
            GROUP BY quality_target
        )
        SELECT
            e.equipment_id,
            e.actual_throughput,
            e.planned_throughput,
            (e.actual_throughput / e.planned_throughput * 100) as efficiency_percent,
            e.avg_risk_score,
            q.avg_quality,
            CASE
                WHEN e.actual_throughput < e.planned_throughput * 0.8 THEN
                    'UNDERPERFORMING: Investigate ' || e.equipment_id
                WHEN e.avg_risk_score > 5 THEN
                    'AT RISK: Reduce load on ' || e.equipment_id
                WHEN q.avg_quality < q.quality_target THEN
                    'QUALITY ISSUE: Adjust processing parameters'
                ELSE 'OPTIMAL'
            END as optimization_action,
            -- Calculate financial impact
            (e.planned_throughput - e.actual_throughput) * 100 as lost_revenue_per_hour_usd
        FROM equipment_health e
        CROSS JOIN quality_impact q
        WHERE e.actual_throughput IS NOT NULL
    """)

# ============================================================================
# INTELLIGENT ML RECOMMENDATIONS
# ============================================================================

@dlt.table(
    name="gold_ml_recommendations_enhanced",
    comment="AI recommendations with full enterprise context",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.managed": "true"
    }
)
def gold_ml_recommendations_enhanced():
    """
    Generate recommendations that consider:
    - Real-time sensor anomalies
    - Historical patterns
    - Production schedules
    - Maintenance windows
    - Parts availability
    - Financial impact
    """

    anomalies = dlt.read_stream("gold_intelligent_anomalies")
    maintenance = dlt.read("gold_predictive_maintenance")
    optimization = dlt.read("gold_production_optimization")

    recommendations = (
        anomalies
        .join(maintenance, on=["equipment_id"], how="left")
        .join(optimization, on=["equipment_id"], how="left")
        .withColumn("recommendation_id", expr("uuid()"))
        .withColumn("recommendation_text",
            when(col("alert_priority") == "CRITICAL",
                concat(
                    lit("🔴 CRITICAL ACTION REQUIRED\n"),
                    lit("Equipment: "), col("equipment_id"), lit("\n"),
                    lit("Issue: "), col("sensor_name"), lit(" deviation of "),
                    round(col("temp_deviation_from_baseline"), 1), lit("°C\n"),
                    lit("Business Context: "), col("business_context"), lit("\n"),
                    lit("Financial Impact: $"), round(col("estimated_impact_usd"), 0), lit("/hour\n"),
                    lit("Action: "), coalesce(col("maintenance_recommendation"), lit("Immediate inspection required")), lit("\n"),
                    lit("Parts Status: "),
                    when(col("total_spare_parts") > 0, concat(col("total_spare_parts"), lit(" parts available")))
                    .otherwise(lit("CHECK INVENTORY"))
                )
            )
            .otherwise(
                concat(
                    lit("⚠️ Maintenance Planning\n"),
                    lit("Equipment: "), col("equipment_id"), lit("\n"),
                    lit("Recommended Action: "), col("maintenance_recommendation"), lit("\n"),
                    lit("Schedule During: Next maintenance window or weekend shift\n"),
                    lit("Business Impact: Minimal if planned")
                )
            )
        )
        .withColumn("recommendation_metadata",
            to_json(struct(
                col("equipment_id"),
                col("alert_priority"),
                col("estimated_impact_usd"),
                col("operational_risk_score"),
                col("days_until_warranty_expiry"),
                col("total_spare_parts"),
                col("shift"),
                col("product_type"),
                col("criticality_rating")
            ))
        )
        .select(
            "recommendation_id",
            "equipment_id",
            col("alert_priority").alias("severity"),
            "recommendation_text",
            "recommendation_metadata",
            col("estimated_impact_usd").alias("financial_impact"),
            current_timestamp().alias("created_timestamp")
        )
    )

    return recommendations

# ============================================================================
# SUMMARY
# ============================================================================

"""
This enhanced Silver/Gold architecture implements the full vision from the diagram:

SILVER LAYER (Unified Context):
✅ Real-time sensor data (Ignition)
✅ Historical baselines (Historian)
✅ Production schedules (MES)
✅ Asset & maintenance data (SAP)
✅ Spare parts availability (SAP)
✅ Contextual risk scoring

GOLD LAYER (Intelligent Analytics):
✅ Context-aware anomaly detection
✅ Predictive maintenance with parts availability
✅ Production optimization insights
✅ Financial impact calculations
✅ ML recommendations with full business context

The recommendations now include:
- "Temperature 8°C above baseline during night shift"
- "Critical equipment, warranty expired, $15K/hour impact"
- "Schedule bearing replacement, part available, 4-hour window on Sunday"
- "Order hydraulic filter now, 14-day lead time, high failure risk"

This is the difference between:
❌ OLD: "Temperature is 85°C" (so what?)
✅ NEW: "Temperature 10°C above baseline on critical crusher during peak production.
         $15K/hour revenue at risk. Spare cooling pump available.
         Recommend immediate inspection and standby crew for replacement."
"""