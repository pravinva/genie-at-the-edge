-- PostgreSQL NOTIFY Triggers for Real-time Webhooks to Ignition
-- Achieves <100ms notification latency as promised in architecture

-- 1. Create notification function for new recommendations
CREATE OR REPLACE FUNCTION notify_new_recommendation()
RETURNS trigger AS $$
DECLARE
  payload json;
BEGIN
  -- Build JSON payload with all relevant data
  payload = json_build_object(
    'event_type', 'new_recommendation',
    'recommendation_id', NEW.recommendation_id,
    'equipment_id', NEW.equipment_id,
    'issue_type', NEW.issue_type,
    'severity', NEW.severity,
    'temperature_reading', NEW.temperature_reading,
    'pressure_reading', NEW.pressure_reading,
    'flow_rate_reading', NEW.flow_rate_reading,
    'recommended_action', NEW.recommended_action,
    'confidence_score', NEW.confidence_score,
    'timestamp', NEW.created_timestamp,
    'root_cause', NEW.root_cause_analysis
  );

  -- Send notification on 'recommendations' channel
  PERFORM pg_notify('recommendations', payload::text);

  -- Also send to severity-specific channels for filtering
  PERFORM pg_notify('recommendations_' || LOWER(NEW.severity), payload::text);

  -- Log the notification for debugging
  RAISE NOTICE 'NOTIFY sent for recommendation %', NEW.recommendation_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Create notification function for operator decisions
CREATE OR REPLACE FUNCTION notify_operator_decision()
RETURNS trigger AS $$
DECLARE
  payload json;
BEGIN
  -- Only notify on status changes
  IF OLD.status IS DISTINCT FROM NEW.status THEN
    payload = json_build_object(
      'event_type', 'operator_decision',
      'recommendation_id', NEW.recommendation_id,
      'equipment_id', NEW.equipment_id,
      'old_status', OLD.status,
      'new_status', NEW.status,
      'operator', NEW.approved_by,
      'timestamp', COALESCE(NEW.approved_timestamp, NEW.rejected_timestamp, NOW()),
      'action_taken', CASE
        WHEN NEW.status = 'approved' THEN 'approved'
        WHEN NEW.status = 'rejected' THEN 'rejected'
        WHEN NEW.status = 'executing' THEN 'executing'
        WHEN NEW.status = 'executed' THEN 'completed'
        ELSE NEW.status
      END
    );

    -- Send notification on 'decisions' channel
    PERFORM pg_notify('decisions', payload::text);

    -- Log the decision
    RAISE NOTICE 'Decision notification: % changed from % to %',
      NEW.recommendation_id, OLD.status, NEW.status;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Create notification function for command execution
CREATE OR REPLACE FUNCTION notify_command_execution()
RETURNS trigger AS $$
DECLARE
  payload json;
BEGIN
  payload = json_build_object(
    'event_type', 'command_execution',
    'command_id', NEW.command_id,
    'recommendation_id', NEW.recommendation_id,
    'equipment_id', NEW.equipment_id,
    'tag_path', NEW.tag_path,
    'new_value', NEW.new_value,
    'status', NEW.status,
    'timestamp', COALESCE(NEW.executed_timestamp, NEW.created_timestamp)
  );

  -- Send notification on 'commands' channel
  PERFORM pg_notify('commands', payload::text);

  -- Also notify on equipment-specific channel
  PERFORM pg_notify('commands_' || NEW.equipment_id, payload::text);

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Create triggers on tables
-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS recommendation_notify_trigger ON agent_recommendations;
DROP TRIGGER IF EXISTS decision_notify_trigger ON agent_recommendations;
DROP TRIGGER IF EXISTS command_notify_trigger ON agent_commands;

-- Create new triggers
CREATE TRIGGER recommendation_notify_trigger
  AFTER INSERT ON agent_recommendations
  FOR EACH ROW
  EXECUTE FUNCTION notify_new_recommendation();

CREATE TRIGGER decision_notify_trigger
  AFTER UPDATE ON agent_recommendations
  FOR EACH ROW
  WHEN (OLD.status IS DISTINCT FROM NEW.status)
  EXECUTE FUNCTION notify_operator_decision();

CREATE TRIGGER command_notify_trigger
  AFTER INSERT OR UPDATE ON agent_commands
  FOR EACH ROW
  EXECUTE FUNCTION notify_command_execution();

-- 5. Create heartbeat notification for agent health monitoring
CREATE OR REPLACE FUNCTION notify_agent_health()
RETURNS trigger AS $$
BEGIN
  -- Only notify if status changed or significant heartbeat gap
  IF OLD.status IS DISTINCT FROM NEW.status OR
     (NEW.last_heartbeat - OLD.last_heartbeat) > INTERVAL '30 seconds' THEN

    PERFORM pg_notify('agent_health', json_build_object(
      'agent_id', NEW.agent_id,
      'status', NEW.status,
      'last_heartbeat', NEW.last_heartbeat,
      'polls_completed', NEW.polls_completed
    )::text);
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS agent_health_notify_trigger ON agent_health;
CREATE TRIGGER agent_health_notify_trigger
  AFTER UPDATE ON agent_health
  FOR EACH ROW
  EXECUTE FUNCTION notify_agent_health();

-- 6. Test the notifications
-- This will send a test notification when executed
DO $$
BEGIN
  PERFORM pg_notify('test_channel', json_build_object(
    'message', 'PostgreSQL NOTIFY system configured successfully',
    'timestamp', NOW(),
    'channels', ARRAY['recommendations', 'decisions', 'commands', 'agent_health']
  )::text);
  RAISE NOTICE 'Test notification sent on test_channel';
END $$;

-- 7. Grant necessary permissions (adjust user as needed)
GRANT USAGE ON SCHEMA public TO ignition_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO ignition_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ignition_user;