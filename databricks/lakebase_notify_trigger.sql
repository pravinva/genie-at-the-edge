-- PostgreSQL NOTIFY Trigger for Lakebase
-- Purpose: Enable event-driven notifications when ML recommendations are inserted
-- This replaces polling with sub-100ms push notifications to Ignition

-- Create notification function
CREATE OR REPLACE FUNCTION lakebase.agentic_hmi.notify_new_recommendation()
RETURNS TRIGGER AS $$
BEGIN
    -- Send PostgreSQL NOTIFY with recommendation details
    PERFORM pg_notify(
        'new_ml_recommendation',
        json_build_object(
            'recommendation_id', NEW.recommendation_id,
            'equipment_id', NEW.equipment_id,
            'issue_type', NEW.issue_type,
            'severity', NEW.severity,
            'confidence_score', NEW.confidence_score,
            'recommended_action', NEW.recommended_action,
            'timestamp', NEW.created_timestamp
        )::text
    );

    -- Log for debugging
    RAISE NOTICE 'NOTIFY sent for recommendation % on equipment %',
        NEW.recommendation_id, NEW.equipment_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on agent_recommendations table
DROP TRIGGER IF EXISTS recommendation_inserted ON lakebase.agentic_hmi.agent_recommendations;
CREATE TRIGGER recommendation_inserted
AFTER INSERT ON lakebase.agentic_hmi.agent_recommendations
FOR EACH ROW
EXECUTE FUNCTION lakebase.agentic_hmi.notify_new_recommendation();

-- Create trigger for status updates (operator actions)
CREATE OR REPLACE FUNCTION lakebase.agentic_hmi.notify_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify if status actually changed
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        PERFORM pg_notify(
            'recommendation_status_changed',
            json_build_object(
                'recommendation_id', NEW.recommendation_id,
                'equipment_id', NEW.equipment_id,
                'old_status', OLD.status,
                'new_status', NEW.status,
                'operator_id', NEW.operator_id,
                'operator_notes', NEW.operator_notes,
                'timestamp', NEW.updated_timestamp
            )::text
        );

        RAISE NOTICE 'Status change NOTIFY: % -> % for recommendation %',
            OLD.status, NEW.status, NEW.recommendation_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for status updates
DROP TRIGGER IF EXISTS recommendation_status_changed ON lakebase.agentic_hmi.agent_recommendations;
CREATE TRIGGER recommendation_status_changed
AFTER UPDATE ON lakebase.agentic_hmi.agent_recommendations
FOR EACH ROW
EXECUTE FUNCTION lakebase.agentic_hmi.notify_status_change();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA lakebase.agentic_hmi TO PUBLIC;
GRANT SELECT ON lakebase.agentic_hmi.agent_recommendations TO PUBLIC;

-- Test the triggers
-- SELECT pg_notify('new_ml_recommendation', '{"test": "message"}');

-- To listen in psql:
-- LISTEN new_ml_recommendation;
-- LISTEN recommendation_status_changed;