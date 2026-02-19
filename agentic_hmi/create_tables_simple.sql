-- Create tables for Agentic HMI (Databricks Delta Lake compatible)
USE agentic_hmi;

-- Table 1: agent_recommendations
CREATE TABLE IF NOT EXISTS agent_recommendations (
    recommendation_id STRING,
    equipment_id STRING,
    issue_type STRING,
    severity STRING,
    issue_description STRING,
    recommended_action STRING,
    confidence_score DECIMAL(3,2),
    root_cause_analysis STRING,
    expected_outcome STRING,
    status STRING,
    operator_id STRING,
    operator_notes STRING,
    approved_timestamp TIMESTAMP,
    executed_timestamp TIMESTAMP,
    defer_until TIMESTAMP,
    rejection_reason STRING,
    created_timestamp TIMESTAMP,
    updated_timestamp TIMESTAMP
);

-- Table 2: work_orders
CREATE TABLE IF NOT EXISTS work_orders (
    work_order_id STRING,
    recommendation_id STRING,
    equipment_id STRING,
    work_type STRING,
    priority INTEGER,
    description STRING,
    assigned_to STRING,
    status STRING,
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    materials_needed STRING,
    completion_notes STRING,
    created_timestamp TIMESTAMP,
    assigned_timestamp TIMESTAMP,
    started_timestamp TIMESTAMP,
    completed_timestamp TIMESTAMP
);

-- Table 3: equipment_setpoints
CREATE TABLE IF NOT EXISTS equipment_setpoints (
    setpoint_id STRING,
    equipment_id STRING,
    parameter_name STRING,
    min_value DECIMAL(10,2),
    max_value DECIMAL(10,2),
    target_value DECIMAL(10,2),
    current_value DECIMAL(10,2),
    units STRING,
    alarm_enabled BOOLEAN,
    alarm_delay_seconds INTEGER,
    last_modified_by STRING,
    last_modified_timestamp TIMESTAMP,
    created_timestamp TIMESTAMP
);

-- Table 4: agent_commands
CREATE TABLE IF NOT EXISTS agent_commands (
    command_id STRING,
    recommendation_id STRING,
    equipment_id STRING,
    command_type STRING,
    tag_path STRING,
    current_value STRING,
    new_value STRING,
    status STRING,
    execution_result STRING,
    execution_timestamp TIMESTAMP,
    retry_count INTEGER,
    created_by STRING,
    created_timestamp TIMESTAMP
);

-- Table 5: operator_sessions
CREATE TABLE IF NOT EXISTS operator_sessions (
    session_id STRING,
    operator_id STRING,
    operator_name STRING,
    operator_role STRING,
    client_ip STRING,
    client_user_agent STRING,
    login_timestamp TIMESTAMP,
    logout_timestamp TIMESTAMP,
    last_activity_timestamp TIMESTAMP,
    recommendations_viewed INTEGER,
    recommendations_approved INTEGER,
    recommendations_rejected INTEGER,
    recommendations_deferred INTEGER,
    session_duration_seconds INTEGER
);

-- Table 6: agent_metrics
CREATE TABLE IF NOT EXISTS agent_metrics (
    metric_id STRING,
    agent_id STRING,
    metric_name STRING,
    metric_value DECIMAL(10,2),
    metric_unit STRING,
    timestamp TIMESTAMP
);

-- Table 7: sensor_data
CREATE TABLE IF NOT EXISTS sensor_data (
    reading_id STRING,
    equipment_id STRING,
    sensor_type STRING,
    sensor_value DECIMAL(10,2),
    units STRING,
    quality STRING,
    timestamp TIMESTAMP
);