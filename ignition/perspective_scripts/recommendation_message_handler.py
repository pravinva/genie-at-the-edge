"""
Perspective Session Event Script - ML Recommendation Message Handler
Purpose: Handle real-time ML recommendation updates pushed from Gateway
Installation: Add to Perspective Session Events > Message Handler

This replaces polling with event-driven updates in the UI
"""

def onMessageReceived(session, payload, messageType):
    """
    Handle incoming messages from the Gateway listener

    Args:
        session: The Perspective session
        payload: Message payload from Gateway
        messageType: Type of message (ML_RECOMMENDATION_UPDATE, ML_RECOMMENDATION_STATUS)
    """

    logger = system.util.getLogger("PerspectiveRecommendations")

    try:
        # Handle new ML recommendations
        if messageType == "ML_RECOMMENDATION_UPDATE":
            handle_new_recommendation(session, payload)

        # Handle status updates
        elif messageType == "ML_RECOMMENDATION_STATUS":
            handle_status_update(session, payload)

        # Track message received
        logger.trace(f"Processed {messageType} for session {session.id}")

    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")

def handle_new_recommendation(session, payload):
    """
    Handle new ML recommendation pushed from database
    Updates UI immediately without polling
    """

    # Check if user is on recommendations page
    current_page = session.page.primaryView
    if not current_page or "agent-recommendations" not in current_page:
        return

    # Extract recommendation data
    recommendation = payload.get("data", {})

    # Update the recommendations custom property on the view
    # This triggers UI update automatically via property binding
    view = session.getViewRoot()

    if hasattr(view, "custom") and hasattr(view.custom, "recommendations"):
        # Get current recommendations
        current_recs = view.custom.recommendations or []

        # Prepend new recommendation (newest first)
        new_rec = {
            "recommendation_id": recommendation.get("recommendationId"),
            "equipment_id": recommendation.get("equipmentId"),
            "issue_type": recommendation.get("issueType"),
            "severity": recommendation.get("severity"),
            "confidence_score": recommendation.get("confidenceScore"),
            "recommended_action": recommendation.get("recommendedAction"),
            "status": "pending",
            "timestamp": recommendation.get("timestamp"),
            "isNew": True  # Flag for animation
        }

        # Add to beginning of list
        updated_recs = [new_rec] + current_recs

        # Keep only latest 50 recommendations in UI
        if len(updated_recs) > 50:
            updated_recs = updated_recs[:50]

        # Update the property - this triggers UI refresh
        view.custom.recommendations = updated_recs

        # Show notification toast
        show_notification(session, recommendation)

        # Play sound for critical severity
        if recommendation.get("severity") == "critical":
            session.custom.playAlertSound = True

        # Update metrics
        update_session_metrics(session, "recommendations_received", 1)

        # Log latency if timestamp provided
        if recommendation.get("timestamp"):
            latency_ms = system.date.millisBetween(
                recommendation["timestamp"],
                system.date.now()
            )
            logger = system.util.getLogger("RecommendationLatency")
            logger.info(f"UI update latency: {latency_ms}ms")

            # Track if we met <100ms target
            if latency_ms <= 100:
                update_session_metrics(session, "updates_under_100ms", 1)

def handle_status_update(session, payload):
    """
    Handle recommendation status changes (approved/rejected/deferred)
    """

    data = payload.get("data", {})
    rec_id = data.get("recommendationId")
    new_status = data.get("newStatus")

    # Find and update the recommendation in the list
    view = session.getViewRoot()
    if hasattr(view, "custom") and hasattr(view.custom, "recommendations"):
        recommendations = view.custom.recommendations or []

        for i, rec in enumerate(recommendations):
            if rec.get("recommendation_id") == rec_id:
                # Update status
                rec["status"] = new_status
                rec["operator_id"] = data.get("operatorId")
                rec["operator_notes"] = data.get("operatorNotes")
                rec["status_changed_at"] = data.get("timestamp")

                # Remove from pending list if approved/rejected
                if new_status in ["approved", "rejected"]:
                    recommendations.pop(i)

                break

        # Update the property
        view.custom.recommendations = recommendations

        # Show confirmation
        if data.get("operatorId") == session.props.auth.user.name:
            show_confirmation(session, new_status, rec_id)

def show_notification(session, recommendation):
    """
    Display notification popup for new recommendation
    """

    severity = recommendation.get("severity", "medium")
    equipment = recommendation.get("equipmentId", "Unknown")
    issue = recommendation.get("issueType", "Unknown issue")

    # Determine notification style based on severity
    styles = {
        "critical": {"type": "error", "icon": "warning", "duration": 10000},
        "high": {"type": "warning", "icon": "alert-circle", "duration": 8000},
        "medium": {"type": "info", "icon": "info", "duration": 6000},
        "low": {"type": "success", "icon": "check-circle", "duration": 4000}
    }

    style = styles.get(severity, styles["medium"])

    # Create notification
    system.perspective.notify(
        message=f"New ML Recommendation: {issue} on {equipment}",
        title="AI Alert",
        type=style["type"],
        duration=style["duration"],
        icon=style["icon"],
        action={
            "text": "View",
            "onClick": {
                "type": "script",
                "script": f"""
                    # Navigate to recommendation details
                    system.perspective.navigate(
                        '/agent-recommendations/{recommendation.get("recommendationId")}'
                    )
                """
            }
        }
    )

def show_confirmation(session, status, rec_id):
    """
    Show confirmation message for operator actions
    """

    messages = {
        "approved": "Recommendation approved and queued for execution",
        "rejected": "Recommendation rejected",
        "deferred": "Recommendation deferred for later review"
    }

    system.perspective.notify(
        message=messages.get(status, f"Status updated to {status}"),
        title="Action Confirmed",
        type="success",
        duration=3000,
        icon="check"
    )

def update_session_metrics(session, metric_name, value):
    """
    Update session-level metrics for monitoring
    """

    if not hasattr(session.custom, "metrics"):
        session.custom.metrics = {}

    if metric_name not in session.custom.metrics:
        session.custom.metrics[metric_name] = 0

    session.custom.metrics[metric_name] += value

    # Also update global metrics tag
    tag_path = f"[default]Metrics/Session/{metric_name}"
    try:
        current = system.tag.readBlocking([tag_path])[0].value or 0
        system.tag.writeBlocking([tag_path], [current + value])
    except:
        pass

# Additional utility functions

def clear_new_flags(session):
    """
    Clear the 'isNew' flag from recommendations after animation
    Called via timer after 2 seconds
    """
    view = session.getViewRoot()
    if hasattr(view, "custom") and hasattr(view.custom, "recommendations"):
        recommendations = view.custom.recommendations or []
        for rec in recommendations:
            if rec.get("isNew"):
                rec["isNew"] = False
        view.custom.recommendations = recommendations

def get_recommendation_by_id(session, rec_id):
    """
    Helper to find a recommendation by ID
    """
    view = session.getViewRoot()
    if hasattr(view, "custom") and hasattr(view.custom, "recommendations"):
        for rec in view.custom.recommendations or []:
            if rec.get("recommendation_id") == rec_id:
                return rec
    return None