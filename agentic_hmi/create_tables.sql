-- Create tables for Agentic HMI
USE agentic_hmi;

-- Table 1: agent_recommendations
CREATE TABLE IF NOT EXISTS agent_recommendations (
    recommendation_id VARCHAR(36) PRIMARY KEY,
    equipment_id VARCHAR(50) NOT NULL,
    issue_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    issue_description TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    confidence_score DECIMAL(3,2),
    root_cause_analysis TEXT,
    expected_outcome TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    operator_id VARCHAR(50),
    operator_notes TEXT,
    approved_timestamp TIMESTAMP,
    executed_timestamp TIMESTAMP,
    defer_until TIMESTAMP,
    rejection_reason TEXT,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: work_orders
CREATE TABLE IF NOT EXISTS work_orders (
    work_order_id VARCHAR(36) PRIMARY KEY,
    recommendation_id VARCHAR(36),
    equipment_id VARCHAR(50) NOT NULL,
    work_type VARCHAR(100) NOT NULL,
    priority INTEGER,
    description TEXT NOT NULL,
    assigned_to VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'created',
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    materials_needed TEXT,
    completion_notes TEXT,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_timestamp TIMESTAMP,
    started_timestamp TIMESTAMP,
    completed_timestamp TIMESTAMP
);

-- Table 3: equipment_setpoints
CREATE TABLE IF NOT EXISTS equipment_setpoints (
    setpoint_id VARCHAR(36) PRIMARY KEY,
    equipment_id VARCHAR(50) NOT NULL,
    parameter_name VARCHAR(100) NOT NULL,
    min_value DECIMAL(10,2),
    max_value DECIMAL(10,2),
    target_value DECIMAL(10,2),
    current_value DECIMAL(10,2),
    units VARCHAR(20),
    alarm_enabled BOOLEAN DEFAULT TRUE,
    alarm_delay_seconds INTEGER DEFAULT 30,
    last_modified_by VARCHAR(50),
    last_modified_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 4: agent_commands
CREATE TABLE IF NOT EXISTS agent_commands (
    command_id VARCHAR(36) PRIMARY KEY,
    recommendation_id VARCHAR(36),
    equipment_id VARCHAR(50) NOT NULL,
    command_type VARCHAR(50) NOT NULL,
    tag_path VARCHAR(255) NOT NULL,
    current_value VARCHAR(100),
    new_value VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    execution_result TEXT,
    execution_timestamp TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    created_by VARCHAR(50) DEFAULT 'agent',
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 5: operator_sessions
CREATE TABLE IF NOT EXISTS operator_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    operator_id VARCHAR(50) NOT NULL,
    operator_name VARCHAR(100),
    operator_role VARCHAR(50),
    client_ip VARCHAR(45),
    client_user_agent TEXT,
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
    metric_id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2),
    metric_unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 7: sensor_data
CREATE TABLE IF NOT EXISTS sensor_data (
    reading_id VARCHAR(36) PRIMARY KEY,
    equipment_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    sensor_value DECIMAL(10,2) NOT NULL,
    units VARCHAR(20),
    quality VARCHAR(20) DEFAULT 'good',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);