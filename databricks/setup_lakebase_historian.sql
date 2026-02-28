-- Lakebase historian bootstrap (Postgres side)
-- Run via: databricks psql pravin-ignition -- -d historian -f setup_lakebase_historian.sql

CREATE SCHEMA IF NOT EXISTS ignition_streaming;
CREATE SCHEMA IF NOT EXISTS mining_demo;
CREATE SCHEMA IF NOT EXISTS lakebase;

-- Zerobus-compatible table (INT quality contract)
CREATE TABLE IF NOT EXISTS ignition_streaming.sensor_events (
  event_id TEXT,
  event_time TIMESTAMPTZ,
  tag_path TEXT,
  tag_provider TEXT,
  numeric_value DOUBLE PRECISION,
  string_value TEXT,
  boolean_value BOOLEAN,
  quality INTEGER,
  quality_code INTEGER,
  source_system TEXT,
  ingestion_timestamp BIGINT,
  data_type TEXT,
  alarm_state TEXT,
  alarm_priority INTEGER,
  sdt_compressed BOOLEAN,
  compression_ratio DOUBLE PRECISION,
  sdt_enabled BOOLEAN,
  batch_bytes_sent BIGINT
);

-- Serving-layer tables
CREATE TABLE IF NOT EXISTS lakebase.ml_recommendations (
  recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  equipment_id TEXT NOT NULL,
  recommendation_type TEXT NOT NULL,
  recommendation_text TEXT NOT NULL,
  priority TEXT NOT NULL,
  confidence DOUBLE PRECISION,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  status TEXT NOT NULL DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS lakebase.operator_feedback (
  feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recommendation_id UUID,
  equipment_id TEXT NOT NULL,
  operator_id TEXT,
  feedback_type TEXT NOT NULL,
  feedback_text TEXT,
  accepted BOOLEAN,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lakebase.equipment_state (
  equipment_id TEXT PRIMARY KEY,
  current_state TEXT NOT NULL,
  health_score DOUBLE PRECISION,
  last_event_time TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
