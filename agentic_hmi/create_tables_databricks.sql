-- Create tables for Agentic HMI (Databricks compatible)
USE agentic_hmi;

-- Table 1: agent_recommendations
CREATE TABLE IF NOT EXISTS agent_recommendations (
    recommendation_id STRING,
    equipment_id STRING NOT NULL,
    issue_type STRING NOT NULL,
    severity STRING NOT NULL,
    issue_description STRING NOT NULL,
    recommended_action STRING NOT NULL,
    confidence_score DECIMAL(3,2),
    root_cause_analysis STRING,
    expected_outcome STRING,
    status STRING NOT NULL DEFAULT 'pending',
    operator_id STRING,
    operator_notes STRING,
    approved_timestamp TIMESTAMP,
    executed_timestamp TIMESTAMP,
    defer_until TIMESTAMP,
    rejection_reason STRING,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: work_orders
CREATE TABLE IF NOT EXISTS work_orders (
    work_order_id STRING,
    recommendation_id STRING,
    equipment_id STRING NOT NULL,
    work_type STRING NOT NULL,
    priority INTEGER,
    description STRING NOT NULL,
    assigned_to STRING,
    status STRING NOT NULL DEFAULT 'created',
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    materials_needed STRING,
    completion_notes STRING,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_timestamp TIMESTAMP,
    started_timestamp TIMESTAMP,
    completed_timestamp TIMESTAMP
);

-- Table 3: equipment_setpoints
CREATE TABLE IF NOT EXISTS equipment_setpoints (
    setpoint_id STRING,
    equipment_id STRING NOT NULL,
    parameter_name STRING NOT NULL,
    min_value DECIMAL(10,2),
    max_value DECIMAL(10,2),
    target_value DECIMAL(10,2),
    current_value DECIMAL(10,2),
    units STRING,
    alarm_enabled BOOLEAN DEFAULT TRUE,
    alarm_delay_seconds INTEGER DEFAULT 30,
    last_modified_by STRING,
    last_modified_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 4: agent_commands
CREATE TABLE IF NOT EXISTS agent_commands (
    command_id STRING,
    recommendation_id STRING,
    equipment_id STRING NOT NULL,
    command_type STRING NOT NULL,
    tag_path STRING NOT NULL,
    current_value STRING,
    new_value STRING NOT NULL,
    status STRING NOT NULL DEFAULT 'pending',
    execution_result STRING,
    execution_timestamp TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    created_by STRING DEFAULT 'agent',
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 5: operator_sessions
CREATE TABLE IF NOT EXISTS operator_sessions (
    session_id STRING,
    operator_id STRING NOT NULL,
    operator_name STRING,
    operator_role STRING,
    client_ip STRING,
    client_user_agent STRING,
    login_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_timestamp TIMESTAMP,
    last_activity_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recommendations_viewed INTEGER DEFAULT 0,
    recommendations_approved INTEGER DEFAULT 0,
    recommendations_rejected INTEGER DEFAULT 0,
    recommendations_deferred INTEGER DEFAULT 0,
    session_duration_seconds INTEGER
);

-- Table 6: agent_metrics
CREATE TABLE IF NOT EXISTS agent_metrics (
    metric_id STRING,
    agent_id STRING NOT NULL,
    metric_name STRING NOT NULL,
    metric_value DECIMAL(10,2),
    metric_unit STRING,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 7: sensor_data
CREATE TABLE IF NOT EXISTS sensor_data (
    reading_id STRING,
    equipment_id STRING NOT NULL,
    sensor_type STRING NOT NULL,
    sensor_value DECIMAL(10,2) NOT NULL,
    units STRING,
    quality STRING DEFAULT 'good',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);