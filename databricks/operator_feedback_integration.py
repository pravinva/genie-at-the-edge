"""
Operator Feedback Integration
Captures operator decisions from Ignition HMI and closes the learning loop

Workflow:
1. Operator sees recommendation in Ignition Perspective panel
2. Operator clicks: Execute | Defer | Ask AI Why
3. Ignition writes decision to Lakebase (operator_feedback table)
4. Async sync (5-min) writes to Delta Lake
5. Weekly retraining incorporates feedback as labeled training data

Feedback signals:
- Executed → True positive (model was correct)
- Deferred → Uncertain (operator wants more time)
- Rejected → False positive (model was wrong)
- Ask AI Why → Genie interaction for context enrichment
"""

from databricks.sdk import WorkspaceClient
import time
from datetime import datetime
import uuid

w = WorkspaceClient(profile="DEFAULT")
warehouse_id = "4b9b953939869799"

CATALOG = "field_engineering"
SCHEMA = "lakebase"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def record_operator_feedback(
    equipment_id: str,
    recommendation_timestamp: str,
    action_code: str,
    anomaly_score: float,
    operator_action: str,
    operator_id: str,
    operator_notes: str = None,
    shift: str = None,
    session_id: str = None
):
    """
    Record operator decision from Ignition HMI

    Args:
        equipment_id: Equipment identifier (e.g., 'HAUL-001')
        recommendation_timestamp: When recommendation was generated
        action_code: Model's recommended action
        anomaly_score: Model's anomaly score
        operator_action: 'executed', 'deferred', 'rejected', 'ask_ai_why'
        operator_id: Username from Ignition session
        operator_notes: Optional notes from operator
        shift: Current shift (Day/Night/Graveyard)
        session_id: Ignition session ID for tracking

    Returns:
        feedback_id: UUID for this feedback record
    """

    feedback_id = str(uuid.uuid4())

    insert_sql = f"""
    INSERT INTO {CATALOG}.{SCHEMA}.operator_feedback (
        feedback_id,
        equipment_id,
        recommendation_timestamp,
        action_code,
        anomaly_score,
        operator_action,
        operator_id,
        action_timestamp,
        operator_notes,
        shift,
        session_id,
        asked_genie,
        was_correct,
        created_at
    ) VALUES (
        '{feedback_id}',
        '{equipment_id}',
        TIMESTAMP '{recommendation_timestamp}',
        '{action_code}',
        {anomaly_score},
        '{operator_action}',
        '{operator_id}',
        CURRENT_TIMESTAMP(),
        {f"'{operator_notes}'" if operator_notes else 'NULL'},
        {f"'{shift}'" if shift else 'NULL'},
        {f"'{session_id}'" if session_id else 'NULL'},
        {str(operator_action == 'ask_ai_why').lower()},
        NULL,  -- Will be determined later
        CURRENT_TIMESTAMP()
    )
    """

    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=insert_sql,
            wait_timeout='0s'
        )

        time.sleep(1)
        status = w.statement_execution.get_statement(result.statement_id)

        if status.status.state.value == 'SUCCEEDED':
            print(f"✅ Feedback recorded: {feedback_id}")
            print(f"   Equipment: {equipment_id}")
            print(f"   Action: {operator_action}")
            return feedback_id
        else:
            print(f"❌ Failed to record feedback")
            if status.status.error:
                print(f"   Error: {status.status.error.message}")
            return None

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None


def record_genie_interaction(
    feedback_id: str,
    genie_question: str,
    genie_response: str
):
    """
    Record Genie "Ask AI Why" interaction

    This enriches model context with:
    - Equipment-specific terminology
    - Site-specific operational patterns
    - Operator reasoning patterns
    """

    update_sql = f"""
    UPDATE {CATALOG}.{SCHEMA}.operator_feedback
    SET
        genie_question = '{genie_question.replace("'", "''")}',
        genie_response = '{genie_response.replace("'", "''")}',
        asked_genie = true
    WHERE feedback_id = '{feedback_id}'
    """

    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=update_sql,
            wait_timeout='0s'
        )

        time.sleep(1)
        status = w.statement_execution.get_statement(result.statement_id)

        if status.status.state.value == 'SUCCEEDED':
            print(f"✅ Genie interaction recorded for {feedback_id}")
            return True
        else:
            print(f"❌ Failed to record Genie interaction")
            return False

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False


def mark_outcome(
    feedback_id: str,
    was_correct: bool,
    actual_outcome: str
):
    """
    Mark actual outcome after time has passed

    This creates labeled training data:
    - was_correct=True → Recommendation prevented an issue (true positive)
    - was_correct=False → Equipment was fine, alarm was unnecessary (false positive)

    Called by weekly batch job that checks equipment state 24-72 hours after recommendation
    """

    update_sql = f"""
    UPDATE {CATALOG}.{SCHEMA}.operator_feedback
    SET
        was_correct = {str(was_correct).lower()},
        actual_outcome = '{actual_outcome.replace("'", "''")}',
        outcome_timestamp = CURRENT_TIMESTAMP()
    WHERE feedback_id = '{feedback_id}'
    """

    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=update_sql,
            wait_timeout='0s'
        )

        time.sleep(1)
        status = w.statement_execution.get_statement(result.statement_id)

        if status.status.state.value == 'SUCCEEDED':
            print(f"✅ Outcome marked for {feedback_id}: was_correct={was_correct}")
            return True
        else:
            print(f"❌ Failed to mark outcome")
            return False

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

# ============================================================================
# EXAMPLE USAGE (Called from Ignition scripting)
# ============================================================================

if __name__ == "__main__":

    print("=" * 80)
    print("OPERATOR FEEDBACK INTEGRATION TEST")
    print("=" * 80)

    # Example 1: Operator executes recommendation
    print("\n[Example 1] Operator executes recommendation")
    feedback_id_1 = record_operator_feedback(
        equipment_id="HAUL-001",
        recommendation_timestamp="2024-03-15 14:30:00",
        action_code="reduce_speed",
        anomaly_score=0.87,
        operator_action="executed",
        operator_id="john.smith",
        operator_notes="Temperature was climbing rapidly, reduced to 60% as recommended",
        shift="Day",
        session_id="ignition-session-abc123"
    )

    # Example 2: Operator asks Genie "Why?"
    print("\n[Example 2] Operator asks Genie for explanation")
    feedback_id_2 = record_operator_feedback(
        equipment_id="CRUSH-001",
        recommendation_timestamp="2024-03-15 15:45:00",
        action_code="schedule_maintenance",
        anomaly_score=0.72,
        operator_action="ask_ai_why",
        operator_id="sarah.jones",
        shift="Day",
        session_id="ignition-session-def456"
    )

    if feedback_id_2:
        record_genie_interaction(
            feedback_id=feedback_id_2,
            genie_question="Why is bearing maintenance recommended? We just serviced this crusher 2 weeks ago.",
            genie_response="Analysis shows vibration patterns consistent with bearing degradation despite recent service. The vibration frequency spectrum indicates potential misalignment during installation. Historical data shows similar patterns in CRUSH-002 led to bearing failure 3 days after preventive maintenance. Recommend inspection focusing on alignment tolerances."
        )

    # Example 3: Operator defers (wants more time to assess)
    print("\n[Example 3] Operator defers decision")
    feedback_id_3 = record_operator_feedback(
        equipment_id="CONV-001",
        recommendation_timestamp="2024-03-15 16:00:00",
        action_code="check_blockage",
        anomaly_score=0.65,
        operator_action="deferred",
        operator_id="mike.wilson",
        operator_notes="Will check during next scheduled downtime in 2 hours",
        shift="Day",
        session_id="ignition-session-ghi789"
    )

    # Example 4: Operator rejects (false positive)
    print("\n[Example 4] Operator rejects recommendation")
    feedback_id_4 = record_operator_feedback(
        equipment_id="HAUL-002",
        recommendation_timestamp="2024-03-15 16:15:00",
        action_code="emergency_shutdown",
        anomaly_score=0.91,
        operator_action="rejected",
        operator_id="lisa.chen",
        operator_notes="Temperature sensor malfunction confirmed - replaced sensor, equipment is fine",
        shift="Day",
        session_id="ignition-session-jkl012"
    )

    # Mark outcome for rejected recommendation (sensor fault, not equipment issue)
    if feedback_id_4:
        mark_outcome(
            feedback_id=feedback_id_4,
            was_correct=False,  # Model was wrong
            actual_outcome="Sensor malfunction - equipment operated normally after sensor replacement"
        )

    print("\n" + "=" * 80)
    print("✅ FEEDBACK INTEGRATION TEST COMPLETE")
    print("=" * 80)

    print("""
Ignition Integration Guide:

1. Create Named Query in Ignition (INSERT feedback):
   INSERT INTO lakebase.operator_feedback (...)
   VALUES (:feedback_id, :equipment_id, ...)

2. Bind Perspective button onClick event:
   - Execute button → system.db.runNamedQuery("RecordFeedback", {"operator_action": "executed", ...})
   - Defer button → ... {"operator_action": "deferred", ...}
   - Ask AI button → ... {"operator_action": "ask_ai_why", ...} + open Genie panel

3. Genie panel integration:
   - On "Ask AI Why" click → Send question to Databricks Genie API
   - Display response in modal
   - Record interaction via system.db.runNamedQuery("RecordGenieInteraction", ...)

4. Session props:
   - session.props.custom.currentUser → operator_id
   - session.props.custom.currentShift → shift
   - session.props.custom.sessionId → session_id

Feedback loop closure:
- Weekly job checks outcomes (48-72h after recommendations)
- Compares predicted vs actual equipment state
- Labels feedback records with was_correct=true/false
- Retraining incorporates corrected labels
- Model precision improves over time
""")
