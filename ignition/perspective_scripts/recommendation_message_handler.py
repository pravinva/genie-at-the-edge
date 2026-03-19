"""
Perspective Session Event Script - ML + Genie event handler.
Installation: Perspective Session Events -> Message Handler.
"""

import system


MAX_RECOMMENDATIONS = 50
MAX_COMMANDS = 100


def handleMessage(session, payload):
    """
    Perspective Message Handler entrypoint.
    Expected by Designer message scripts as: def handleMessage(session, payload)
    """
    messageType = _extract_message_type(payload)
    _dispatch_message(session, payload, messageType)


def onMessageReceived(session, payload, messageType):
    """
    Backward-compatible entrypoint for older integrations.
    """
    _dispatch_message(session, payload, messageType)


def _dispatch_message(session, payload, messageType):
    logger = system.util.getLogger("PerspectiveRecommendations")
    try:
        _ensure_session_state(session)
        session.custom.lastNotifyTs = str(system.date.now())

        if messageType in ["ML_RECOMMENDATION_UPDATE", "newRecommendation"]:
            handle_new_recommendation(session, payload)
        elif messageType in ["ML_RECOMMENDATION_STATUS", "operatorDecision"]:
            handle_status_update(session, payload)
        elif messageType == "criticalAlert":
            handle_critical_alert(session, payload)
        elif messageType == "commandExecution":
            handle_command_execution(session, payload)
        elif messageType == "agentHealth":
            handle_agent_health(session, payload)
        elif messageType in ["jdbcResult", "decisionConfirmed"]:
            handle_jdbc_result(session, payload)
        elif messageType == "jdbcError":
            handle_jdbc_error(session, payload)

        update_session_metrics(session, "messages_received", 1)
        logger.trace("Processed {0} for session {1}".format(messageType, session.id))
    except Exception as e:
        logger.error("Error handling message: {0}".format(str(e)))


def _extract_message_type(payload):
    if not isinstance(payload, dict):
        return None

    # Preferred explicit keys.
    message_type = payload.get("messageType") or payload.get("message_type") or payload.get("type")
    if message_type:
        return message_type

    # Fallback heuristics for payload-only handlers.
    if payload.get("health_status") is not None or payload.get("agent_id") is not None or payload.get("agentId") is not None:
        return "agentHealth"
    if payload.get("command_id") is not None or payload.get("commandId") is not None:
        return "commandExecution"
    if payload.get("error") is not None and payload.get("success") is False:
        return "jdbcError"
    if payload.get("decision") is not None and payload.get("recommendation_id") is not None:
        return "jdbcResult"
    if payload.get("newStatus") is not None or payload.get("new_status") is not None:
        return "ML_RECOMMENDATION_STATUS"
    if payload.get("severity") is not None and (
        payload.get("recommendation_id") is not None or payload.get("recommendationId") is not None
    ):
        return "ML_RECOMMENDATION_UPDATE"
    return None


def _ensure_session_state(session):
    if not hasattr(session.custom, "recommendations") or session.custom.recommendations is None:
        session.custom.recommendations = []
    if not hasattr(session.custom, "commands") or session.custom.commands is None:
        session.custom.commands = []
    if not hasattr(session.custom, "agentHealth") or session.custom.agentHealth is None:
        session.custom.agentHealth = {}
    if not hasattr(session.custom, "metrics") or session.custom.metrics is None:
        session.custom.metrics = {}
    if not hasattr(session.custom, "connectionStatus"):
        session.custom.connectionStatus = "connected"
    if not hasattr(session.custom, "lastNotifyTs"):
        session.custom.lastNotifyTs = None
    if not hasattr(session.custom, "playAlertSound"):
        session.custom.playAlertSound = False


def _normalize_recommendation(data):
    return {
        "recommendation_id": data.get("recommendationId") or data.get("recommendation_id"),
        "equipment_id": data.get("equipmentId") or data.get("equipment_id"),
        "issue_type": data.get("issueType") or data.get("issue_type"),
        "severity": (data.get("severity") or "medium").lower(),
        "confidence_score": data.get("confidenceScore") or data.get("confidence_score"),
        "recommended_action": data.get("recommendedAction") or data.get("recommended_action"),
        "status": data.get("status") or "pending",
        "timestamp": data.get("timestamp"),
        "isNew": True
    }


def handle_new_recommendation(session, payload):
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    rec = _normalize_recommendation(data)
    rec_id = rec.get("recommendation_id")
    if not rec_id:
        return

    recommendations = list(session.custom.recommendations or [])
    recommendations = [r for r in recommendations if r.get("recommendation_id") != rec_id]
    recommendations.insert(0, rec)
    if len(recommendations) > MAX_RECOMMENDATIONS:
        recommendations = recommendations[:MAX_RECOMMENDATIONS]
    session.custom.recommendations = recommendations

    if rec.get("severity") == "critical":
        session.custom.playAlertSound = True
    show_notification(session, rec)
    update_session_metrics(session, "recommendations_received", 1)


def handle_status_update(session, payload):
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    rec_id = data.get("recommendationId") or data.get("recommendation_id")
    new_status = data.get("newStatus") or data.get("new_status")
    if not rec_id:
        return

    recommendations = list(session.custom.recommendations or [])
    for rec in recommendations:
        if rec.get("recommendation_id") == rec_id:
            rec["status"] = new_status
            rec["operator_id"] = data.get("operatorId") or data.get("operator_id")
            rec["operator_notes"] = data.get("operatorNotes") or data.get("operator_notes")
            rec["status_changed_at"] = data.get("timestamp")
            rec["isNew"] = False
            break

    session.custom.recommendations = recommendations

    session_user = None
    try:
        session_user = session.props.auth.user.userName
    except Exception:
        session_user = None
    actor = data.get("operatorId") or data.get("operator_id")
    if session_user and actor and session_user == actor:
        show_confirmation(session, new_status, rec_id)

    update_session_metrics(session, "status_updates_received", 1)


def handle_critical_alert(session, payload):
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    equipment = data.get("equipmentId") or data.get("equipment_id") or "Unknown"
    issue = data.get("issueType") or data.get("issue_type") or "Critical issue"
    session.custom.playAlertSound = True
    system.perspective.notify(
        title="Critical AI Alert",
        message="{0} on {1}".format(issue, equipment),
        type="error",
        duration=10000
    )
    update_session_metrics(session, "critical_alerts_received", 1)


def handle_command_execution(session, payload):
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    command_id = data.get("command_id") or data.get("commandId")
    if not command_id:
        command_id = "cmd-{0}".format(system.date.toMillis(system.date.now()))

    commands = list(session.custom.commands or [])
    commands = [c for c in commands if (c.get("command_id") or c.get("commandId")) != command_id]
    commands.insert(0, data)
    if len(commands) > MAX_COMMANDS:
        commands = commands[:MAX_COMMANDS]
    session.custom.commands = commands
    update_session_metrics(session, "commands_received", 1)


def handle_agent_health(session, payload):
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    agent_id = data.get("agent_id") or data.get("agentId") or "unknown"
    health = dict(session.custom.agentHealth or {})
    health[str(agent_id)] = data
    session.custom.agentHealth = health
    update_session_metrics(session, "agent_health_updates_received", 1)


def handle_jdbc_result(session, payload):
    data = payload if isinstance(payload, dict) else {}
    if data.get("success") is False:
        system.perspective.notify(
            title="Action Failed",
            message=data.get("error", "Unknown JDBC error"),
            type="error",
            duration=5000
        )
        return

    decision = data.get("decision")
    rec_id = data.get("recommendation_id")
    if decision and rec_id:
        show_confirmation(session, decision, rec_id)
    update_session_metrics(session, "jdbc_success", 1)


def handle_jdbc_error(session, payload):
    data = payload if isinstance(payload, dict) else {}
    system.perspective.notify(
        title="Database Error",
        message=data.get("error", "Unknown JDBC error"),
        type="error",
        duration=6000
    )
    update_session_metrics(session, "jdbc_errors", 1)


def show_notification(session, recommendation):
    severity = recommendation.get("severity", "medium")
    equipment = recommendation.get("equipment_id") or "Unknown"
    issue = recommendation.get("issue_type") or "Unknown issue"

    styles = {
        "critical": {"type": "error", "duration": 10000},
        "high": {"type": "warning", "duration": 8000},
        "medium": {"type": "info", "duration": 6000},
        "low": {"type": "success", "duration": 4000}
    }
    style = styles.get(severity, styles["medium"])

    system.perspective.notify(
        title="AI Recommendation",
        message="New recommendation: {0} on {1}".format(issue, equipment),
        type=style["type"],
        duration=style["duration"]
    )


def show_confirmation(session, status, rec_id):
    messages = {
        "approved": "Recommendation approved and queued for execution",
        "rejected": "Recommendation rejected",
        "deferred": "Recommendation deferred for later review"
    }
    system.perspective.notify(
        title="Action Confirmed",
        message=messages.get(status, "Status updated to {0}".format(status)),
        type="success",
        duration=3000
    )


def update_session_metrics(session, metric_name, value):
    metrics = dict(session.custom.metrics or {})
    metrics[metric_name] = int(metrics.get(metric_name, 0)) + int(value)
    session.custom.metrics = metrics


def clear_new_flags(session):
    recommendations = list(session.custom.recommendations or [])
    for rec in recommendations:
        if rec.get("isNew"):
            rec["isNew"] = False
    session.custom.recommendations = recommendations


def get_recommendation_by_id(session, rec_id):
    for rec in (session.custom.recommendations or []):
        if rec.get("recommendation_id") == rec_id:
            return rec
    return None