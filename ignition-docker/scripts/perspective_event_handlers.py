"""
Perspective Event Handlers for Main Operations View
These scripts handle user interactions in the HMI
"""

def onEquipmentSelect(event):
    """
    Handle equipment selection from the status panel
    """
    equipment_id = event.source.props.equipmentId

    # Update selected equipment tag
    system.tag.write("[default]HMI/SelectedEquipment", equipment_id)

    # Update detail view with equipment specifics
    if equipment_id:
        # Get equipment details
        status = system.tag.read(f"[default]Equipment/{equipment_id}/Status").value
        temperature = system.tag.read(f"[default]Equipment/{equipment_id}/Temperature").value
        flow_rate = system.tag.read(f"[default]Equipment/{equipment_id}/FlowRate").value
        last_maintenance = system.tag.read(f"[default]Equipment/{equipment_id}/LastMaintenance").value

        # Update detail panel
        detail_data = {
            "id": equipment_id,
            "status": status,
            "temperature": temperature,
            "flowRate": flow_rate,
            "lastMaintenance": last_maintenance,
            "selected": True
        }

        # Write to session props for view update
        event.session.custom.selectedEquipment = detail_data

        # Query for AI insights on this equipment
        queryAIInsights(equipment_id)

        # Log selection
        system.util.getLogger("HMI").info(f"Equipment selected: {equipment_id}")

def onRecommendationAction(event):
    """
    Handle AI recommendation approve/defer/reject actions
    """
    action = event.source.props.action  # 'approve', 'defer', or 'reject'
    recommendation_id = event.source.parent.props.recommendationId

    # Get recommendation details
    rec_path = f"[default]AI/Recommendations/Active/{recommendation_id}"
    recommendation = system.tag.read(f"{rec_path}/Content").value
    equipment = system.tag.read(f"{rec_path}/Equipment").value
    confidence = system.tag.read(f"{rec_path}/Confidence").value

    # Process action
    if action == 'approve':
        # Implement the recommendation
        implementRecommendation(recommendation_id, equipment)

        # Update status
        system.tag.write(f"{rec_path}/Status", "Approved")
        system.tag.write(f"{rec_path}/ApprovedBy", event.session.props.auth.user.userName)
        system.tag.write(f"{rec_path}/ApprovedTime", system.date.now())

        # Show confirmation
        system.perspective.showConfirm(
            "Recommendation approved and being implemented",
            "Approved",
            icon="success"
        )

        # Log to audit trail
        logAuditEvent("RECOMMENDATION_APPROVED", {
            "id": recommendation_id,
            "action": recommendation,
            "equipment": equipment,
            "user": event.session.props.auth.user.userName
        })

    elif action == 'defer':
        # Defer for later review
        system.tag.write(f"{rec_path}/Status", "Deferred")
        system.tag.write(f"{rec_path}/DeferredBy", event.session.props.auth.user.userName)
        system.tag.write(f"{rec_path}/DeferredTime", system.date.now())

        # Schedule for re-review
        scheduleReview(recommendation_id, hours=4)

        # Show notification
        system.perspective.showInfo(
            "Recommendation deferred for 4 hours",
            "Deferred"
        )

    elif action == 'reject':
        # Reject recommendation
        system.tag.write(f"{rec_path}/Status", "Rejected")
        system.tag.write(f"{rec_path}/RejectedBy", event.session.props.auth.user.userName)
        system.tag.write(f"{rec_path}/RejectedTime", system.date.now())

        # Request operator feedback
        reason = system.gui.inputBox("Please provide a reason for rejection:")
        if reason:
            system.tag.write(f"{rec_path}/RejectionReason", reason)

            # Send feedback to ML model
            sendModelFeedback(recommendation_id, "rejected", reason)

        # Show confirmation
        system.perspective.showWarning(
            "Recommendation rejected",
            "Rejected"
        )

        # Log rejection
        logAuditEvent("RECOMMENDATION_REJECTED", {
            "id": recommendation_id,
            "action": recommendation,
            "equipment": equipment,
            "user": event.session.props.auth.user.userName,
            "reason": reason
        })

def implementRecommendation(recommendation_id, equipment):
    """
    Implement an approved AI recommendation
    """
    # Get implementation details
    rec_path = f"[default]AI/Recommendations/Active/{recommendation_id}"
    action_type = system.tag.read(f"{rec_path}/ActionType").value
    parameters = system.tag.read(f"{rec_path}/Parameters").value

    try:
        if action_type == "ADJUST_SETPOINT":
            # Adjust equipment setpoint
            tag_path = f"[default]Equipment/{equipment}/Setpoint"
            new_value = parameters.get("value")

            # Validate setpoint is within limits
            min_val = system.tag.read(f"{tag_path}_Min").value
            max_val = system.tag.read(f"{tag_path}_Max").value

            if min_val <= new_value <= max_val:
                system.tag.write(tag_path, new_value)
                result = "Success"
            else:
                result = f"Value {new_value} outside limits [{min_val}, {max_val}]"

        elif action_type == "SCHEDULE_MAINTENANCE":
            # Schedule maintenance window
            maintenance_date = parameters.get("date")
            duration_hours = parameters.get("duration", 4)

            # Create maintenance schedule entry
            createMaintenanceSchedule(equipment, maintenance_date, duration_hours)
            result = "Maintenance scheduled"

        elif action_type == "CHANGE_MODE":
            # Change operational mode
            new_mode = parameters.get("mode")
            mode_tag = f"[default]Equipment/{equipment}/Mode"

            # Validate mode transition
            current_mode = system.tag.read(mode_tag).value
            if isValidModeTransition(current_mode, new_mode):
                system.tag.write(mode_tag, new_mode)
                result = "Mode changed"
            else:
                result = f"Invalid transition from {current_mode} to {new_mode}"

        elif action_type == "ALERT_OPERATOR":
            # Send alert to operator
            message = parameters.get("message")
            priority = parameters.get("priority", "MEDIUM")

            sendOperatorAlert(equipment, message, priority)
            result = "Alert sent"

        else:
            result = f"Unknown action type: {action_type}"

        # Update implementation status
        system.tag.write(f"{rec_path}/ImplementationResult", result)
        system.tag.write(f"{rec_path}/ImplementedTime", system.date.now())

        return result

    except Exception as e:
        error_msg = f"Implementation failed: {str(e)}"
        system.tag.write(f"{rec_path}/ImplementationResult", error_msg)
        system.util.getLogger("HMI").error(error_msg)
        return error_msg

def queryAIInsights(equipment_id):
    """
    Query Databricks for AI insights on selected equipment
    """
    # Prepare context for Genie
    context = {
        "equipment": equipment_id,
        "currentStatus": system.tag.read(f"[default]Equipment/{equipment_id}/Status").value,
        "temperature": system.tag.read(f"[default]Equipment/{equipment_id}/Temperature").value,
        "anomalyScore": system.tag.read(f"[default]Predictions/Anomalies/{equipment_id}").value
    }

    # Query Genie for insights
    query = f"What insights do you have about {equipment_id}? Are there any concerns or optimization opportunities?"

    # Send query through WebDev module
    client = system.net.httpClient()
    response = client.post(
        "http://localhost:8088/system/webdev/genie_chat",
        data={"message": query, "context": context}
    )

    if response.json.get("success"):
        # Update insights display
        insights = response.json.get("response")
        system.tag.write("[default]HMI/CurrentInsights", insights)

def onGenieSubmit(event):
    """
    Handle Genie chat message submission
    """
    message = event.source.props.text

    if not message:
        return

    # Add user message to chat history
    addToChatHistory("user", message)

    # Clear input
    event.source.props.text = ""

    # Show typing indicator
    event.source.parent.getChild("TypingIndicator").props.visible = True

    # Send message to Genie
    def sendAsync():
        try:
            client = system.net.httpClient()
            response = client.post(
                "http://localhost:8088/system/webdev/genie_chat",
                data={"message": message}
            )

            if response.json.get("success"):
                genie_response = response.json.get("response")

                # Add Genie response to chat
                addToChatHistory("genie", genie_response)

                # Check if response contains actionable items
                if "recommend" in genie_response.lower() or "suggest" in genie_response.lower():
                    # Parse and display as recommendation
                    createRecommendationFromChat(genie_response)

        except Exception as e:
            addToChatHistory("system", f"Error: {str(e)}")

        finally:
            # Hide typing indicator
            event.source.parent.getChild("TypingIndicator").props.visible = False

    # Run async
    system.util.invokeAsynchronous(sendAsync)

def addToChatHistory(sender, message):
    """
    Add message to chat history display
    """
    history = system.tag.read("[default]HMI/ChatHistory").value or []

    # Add new message
    history.append({
        "sender": sender,
        "message": message,
        "timestamp": system.date.now()
    })

    # Keep only last 50 messages
    if len(history) > 50:
        history = history[-50:]

    # Update tag
    system.tag.write("[default]HMI/ChatHistory", history)

def createRecommendationFromChat(genie_response):
    """
    Create an actionable recommendation from Genie chat response
    """
    import re
    import uuid

    # Generate recommendation ID
    rec_id = str(uuid.uuid4())[:8]

    # Parse recommendation from response
    # Look for action keywords
    action_patterns = [
        r"recommend\s+(.+?)(?:\.|$)",
        r"suggest\s+(.+?)(?:\.|$)",
        r"should\s+(.+?)(?:\.|$)"
    ]

    recommendation_text = ""
    for pattern in action_patterns:
        match = re.search(pattern, genie_response, re.IGNORECASE)
        if match:
            recommendation_text = match.group(1)
            break

    if recommendation_text:
        # Create recommendation tags
        rec_path = f"[default]AI/Recommendations/Active/{rec_id}"

        system.tag.write(f"{rec_path}/Id", rec_id)
        system.tag.write(f"{rec_path}/Content", recommendation_text)
        system.tag.write(f"{rec_path}/Source", "Genie Chat")
        system.tag.write(f"{rec_path}/Timestamp", system.date.now())
        system.tag.write(f"{rec_path}/Status", "Pending")
        system.tag.write(f"{rec_path}/Confidence", 0.85)  # Default confidence

        # Trigger recommendation notification
        system.tag.write("[default]HMI/NewRecommendation", True)

        # Log creation
        logAuditEvent("RECOMMENDATION_CREATED", {
            "id": rec_id,
            "source": "Genie Chat",
            "content": recommendation_text
        })

def logAuditEvent(event_type, details):
    """
    Log events to audit trail
    """
    audit_data = {
        "timestamp": system.date.now(),
        "eventType": event_type,
        "details": details,
        "user": system.security.getUsername(),
        "session": system.util.getSessionInfo().get("id")
    }

    # Write to audit database
    system.db.runNamedQuery(
        "Audit/InsertEvent",
        parameters=audit_data
    )

    # Also log to file
    logger = system.util.getLogger("AUDIT")
    logger.info(f"{event_type}: {details}")

def isValidModeTransition(current_mode, new_mode):
    """
    Validate if mode transition is allowed
    """
    valid_transitions = {
        "IDLE": ["STARTING", "MAINTENANCE"],
        "STARTING": ["RUNNING", "IDLE"],
        "RUNNING": ["STOPPING", "EMERGENCY_STOP"],
        "STOPPING": ["IDLE"],
        "EMERGENCY_STOP": ["IDLE", "MAINTENANCE"],
        "MAINTENANCE": ["IDLE"]
    }

    return new_mode in valid_transitions.get(current_mode, [])

def createMaintenanceSchedule(equipment, date, duration_hours):
    """
    Create a maintenance schedule entry
    """
    schedule_data = {
        "equipment": equipment,
        "scheduledDate": date,
        "duration": duration_hours,
        "status": "Scheduled",
        "createdBy": system.security.getUsername(),
        "createdTime": system.date.now()
    }

    # Insert into maintenance schedule
    system.db.runNamedQuery(
        "Maintenance/ScheduleEntry",
        parameters=schedule_data
    )

    # Create calendar event
    system.tag.write(
        f"[default]Maintenance/Schedule/{equipment}/{date}",
        schedule_data
    )

def sendOperatorAlert(equipment, message, priority):
    """
    Send alert to operator station
    """
    alert_data = {
        "equipment": equipment,
        "message": message,
        "priority": priority,
        "timestamp": system.date.now(),
        "acknowledged": False
    }

    # Write to alert system
    system.tag.write("[default]Alerts/New", alert_data)

    # Trigger audio/visual alert based on priority
    if priority == "HIGH":
        system.tag.write("[default]Alerts/AudioAlarm", True)
        system.tag.write("[default]Alerts/VisualAlarm", "RED")
    elif priority == "MEDIUM":
        system.tag.write("[default]Alerts/VisualAlarm", "ORANGE")

    # Send to all operator sessions
    system.perspective.broadcast({
        "type": "alert",
        "data": alert_data
    })

def sendModelFeedback(recommendation_id, action, reason):
    """
    Send feedback to ML model for continuous improvement
    """
    feedback_data = {
        "recommendationId": recommendation_id,
        "action": action,
        "reason": reason,
        "timestamp": system.date.now(),
        "user": system.security.getUsername()
    }

    # Send to Databricks for model retraining
    client = system.net.httpClient()
    client.post(
        f"https://{DATABRICKS_HOST}/api/2.0/ml/feedback",
        headers={"Authorization": f"Bearer {DATABRICKS_TOKEN}"},
        data=feedback_data
    )

def scheduleReview(recommendation_id, hours):
    """
    Schedule a recommendation for re-review
    """
    review_time = system.date.addHours(system.date.now(), hours)

    # Create scheduled task
    system.tag.write(
        f"[default]AI/Recommendations/Scheduled/{recommendation_id}",
        {
            "reviewTime": review_time,
            "originalId": recommendation_id
        }
    )