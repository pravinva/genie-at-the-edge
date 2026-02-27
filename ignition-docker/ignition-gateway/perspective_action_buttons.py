# Perspective Component: RecommendationActions
# Path: Components/RecommendationActions
# This component handles operator actions on ML recommendations

def onActionClick(self, action, recommendation_id, equipment_id):
    """
    Handle operator action on recommendation
    Actions: approve, reject, defer, ask_ai
    """
    import system
    from java.util import Date

    operator_id = self.session.props.auth.user.name

    if action == "approve":
        # Approve and execute recommendation
        self.approveRecommendation(recommendation_id, equipment_id, operator_id)

    elif action == "reject":
        # Reject recommendation
        self.rejectRecommendation(recommendation_id, operator_id)

    elif action == "defer":
        # Defer for later review
        self.deferRecommendation(recommendation_id, operator_id)

    elif action == "ask_ai":
        # Ask Genie for more details (only when operator requests)
        self.askGenie(recommendation_id, equipment_id)

def approveRecommendation(self, recommendation_id, equipment_id, operator_id):
    """
    Approve and execute the ML recommendation
    """
    import system

    # 1. Update status in Lakebase
    query = """
        UPDATE lakebase.agentic_hmi.ml_recommendations
        SET status = 'approved',
            operator_id = ?,
            approved_timestamp = CURRENT_TIMESTAMP,
            operator_notes = ?
        WHERE recommendation_id = ?
    """

    notes = "Approved via Perspective dashboard"
    system.db.runPrepUpdate(query, [operator_id, notes, recommendation_id], "Lakebase")

    # 2. Get the action code to execute
    rec = self.getRecommendation(recommendation_id)
    action_code = rec['action_code']

    # 3. Execute the action based on code
    success = self.executeAction(action_code, equipment_id)

    if success:
        # 4. Update local view
        self.updateRecommendationStatus(recommendation_id, 'approved')

        # 5. Show success notification
        system.perspective.showNotification(
            f"Recommendation approved and executed for {equipment_id}",
            type="success",
            duration=5000
        )

        # 6. Log the action
        self.logOperatorAction(
            recommendation_id=recommendation_id,
            action="approve",
            operator_id=operator_id,
            success=True
        )

        # 7. Send feedback to ML pipeline
        self.sendMLFeedback(recommendation_id, "approve", operator_id)
    else:
        system.perspective.showNotification(
            "Failed to execute action. Please check equipment status.",
            type="error",
            duration=10000
        )

def executeAction(self, action_code, equipment_id):
    """
    Execute the approved action by writing to equipment tags
    """
    import system

    try:
        # Parse action code and execute
        if action_code == "REDUCE_SPEED_60":
            # Reduce equipment speed to 60%
            tag_path = f"[default]Equipment/{equipment_id}/Speed_SP"
            current_speed = system.tag.readBlocking([tag_path])[0].value
            new_speed = current_speed * 0.6
            system.tag.writeBlocking([tag_path], [new_speed])

            # Log the change
            system.util.getLogger("MLActions").info(
                f"Reduced {equipment_id} speed from {current_speed} to {new_speed}"
            )

        elif action_code == "SCHEDULE_MAINTENANCE":
            # Create maintenance work order
            self.createMaintenanceWorkOrder(equipment_id)

        elif action_code == "INCREASE_COOLING":
            # Increase cooling flow
            tag_path = f"[default]Equipment/{equipment_id}/Cooling_Flow_SP"
            current_flow = system.tag.readBlocking([tag_path])[0].value
            new_flow = min(current_flow * 1.2, 100)  # 20% increase, max 100
            system.tag.writeBlocking([tag_path], [new_flow])

        elif action_code == "EMERGENCY_STOP":
            # Emergency stop
            tag_path = f"[default]Equipment/{equipment_id}/Emergency_Stop"
            system.tag.writeBlocking([tag_path], [True])

            # Create high-priority alarm
            system.alarm.createAlarm(
                source=f"MLActions/{equipment_id}",
                name="ML_Emergency_Stop",
                priority=0,  # Critical
                label=f"ML initiated emergency stop for {equipment_id}"
            )

        elif action_code.startswith("CUSTOM_"):
            # Custom action - parse parameters
            self.executeCustomAction(action_code, equipment_id)

        else:
            # Unknown action code
            system.util.getLogger("MLActions").warn(
                f"Unknown action code: {action_code}"
            )
            return False

        return True

    except Exception as e:
        system.util.getLogger("MLActions").error(
            f"Error executing action {action_code}: {str(e)}"
        )
        return False

def rejectRecommendation(self, recommendation_id, operator_id):
    """
    Reject the ML recommendation
    """
    import system

    # Show reason input dialog
    reason = system.perspective.showInputDialog(
        title="Reject Recommendation",
        message="Please provide a reason for rejection:",
        defaultText="Not applicable to current situation"
    )

    if reason:
        # Update in Lakebase
        query = """
            UPDATE lakebase.agentic_hmi.ml_recommendations
            SET status = 'rejected',
                operator_id = ?,
                rejection_reason = ?,
                updated_timestamp = CURRENT_TIMESTAMP
            WHERE recommendation_id = ?
        """

        system.db.runPrepUpdate(query, [operator_id, reason, recommendation_id], "Lakebase")

        # Update local view
        self.updateRecommendationStatus(recommendation_id, 'rejected')

        # Send feedback to ML
        self.sendMLFeedback(recommendation_id, "reject", operator_id, reason)

        # Show notification
        system.perspective.showNotification(
            "Recommendation rejected. Feedback sent to ML system.",
            type="info",
            duration=3000
        )

def deferRecommendation(self, recommendation_id, operator_id):
    """
    Defer recommendation for later review
    """
    import system

    # Ask when to review
    defer_options = [
        "15 minutes",
        "1 hour",
        "Next shift",
        "Tomorrow"
    ]

    defer_time = system.perspective.showRadioDialog(
        title="Defer Recommendation",
        message="When should this be reviewed?",
        options=defer_options
    )

    if defer_time:
        # Calculate defer until timestamp
        if defer_time == "15 minutes":
            defer_until = system.date.addMinutes(system.date.now(), 15)
        elif defer_time == "1 hour":
            defer_until = system.date.addHours(system.date.now(), 1)
        elif defer_time == "Next shift":
            defer_until = self.getNextShiftTime()
        else:  # Tomorrow
            defer_until = system.date.addDays(system.date.now(), 1)

        # Update in Lakebase
        query = """
            UPDATE lakebase.agentic_hmi.ml_recommendations
            SET status = 'deferred',
                operator_id = ?,
                defer_until = ?,
                updated_timestamp = CURRENT_TIMESTAMP
            WHERE recommendation_id = ?
        """

        system.db.runPrepUpdate(query, [operator_id, defer_until, recommendation_id], "Lakebase")

        # Update local view
        self.updateRecommendationStatus(recommendation_id, 'deferred')

        # Show notification
        system.perspective.showNotification(
            f"Recommendation deferred until {defer_time}",
            type="warning",
            duration=3000
        )

def askGenie(self, recommendation_id, equipment_id):
    """
    ONLY called when operator wants more explanation
    This is when we actually use Genie
    """
    import system

    # Get the recommendation details
    rec = self.getRecommendation(recommendation_id)

    # Show input for operator question
    question = system.perspective.showInputDialog(
        title="Ask AI About This Recommendation",
        message="What would you like to know?",
        defaultText="Why is this happening? What are the alternatives?"
    )

    if question:
        # NOW we call Genie (operator initiated)
        system.perspective.showDialog(
            title="Getting AI Analysis...",
            message="Please wait while AI analyzes your question...",
            showProgressBar=True
        )

        # Call Databricks Genie via API
        genie_response = self.callDatabricksGenie(
            recommendation_id=recommendation_id,
            equipment_id=equipment_id,
            action_code=rec['action_code'],
            operator_question=question
        )

        # Show Genie's response
        system.perspective.openPopup(
            id="GenieResponse",
            view="Popups/GenieExplanation",
            params={
                'question': question,
                'response': genie_response,
                'recommendation': rec
            },
            title="AI Analysis",
            modal=True,
            resizable=True,
            width=800,
            height=600
        )

def callDatabricksGenie(self, recommendation_id, equipment_id, action_code, operator_question):
    """
    Call Databricks Genie API for detailed explanation
    This is ONLY called when operator explicitly asks
    """
    import system
    import httplib2
    import json

    # Prepare the context for Genie
    context = {
        "recommendation_id": recommendation_id,
        "equipment_id": equipment_id,
        "action_code": action_code,
        "operator_question": operator_question,
        "current_sensor_values": self.getCurrentSensorValues(equipment_id),
        "recent_history": self.getRecentHistory(equipment_id),
        "maintenance_log": self.getMaintenanceLog(equipment_id)
    }

    # Call Genie API
    h = httplib2.Http()
    databricks_url = "https://workspace.cloud.databricks.com/api/2.0/genie/query"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {system.tag.readBlocking(["[default]Config/DatabricksToken"])[0].value}'
    }

    prompt = f"""
    An operator has a question about an ML recommendation:

    ML Recommendation: {action_code} for equipment {equipment_id}

    Current Context:
    - Sensor Values: {context['current_sensor_values']}
    - Recent History: {context['recent_history']}
    - Maintenance History: {context['maintenance_log']}

    Operator Question: {operator_question}

    Please provide a detailed explanation that helps the operator understand:
    1. Why this recommendation was made
    2. What will happen if they follow it
    3. What alternatives they have
    4. Any risks to consider
    """

    body = json.dumps({
        "prompt": prompt,
        "model": "databricks-dbrx-instruct"
    })

    try:
        response, content = h.request(
            databricks_url,
            'POST',
            body=body,
            headers=headers
        )

        if response.status == 200:
            result = json.loads(content)
            return result['response']
        else:
            return "Unable to get AI analysis at this time. Please try again."

    except Exception as e:
        system.util.getLogger("Genie").error(f"Error calling Genie: {str(e)}")
        return "Error connecting to AI service."

def sendMLFeedback(self, recommendation_id, decision, operator_id, reason=None):
    """
    Send operator decision back to ML pipeline for model improvement
    """
    import system
    import httplib2
    import json

    feedback_url = "http://databricks-gateway:8080/api/ml/feedback"

    feedback_data = {
        "recommendation_id": recommendation_id,
        "operator_decision": decision,
        "operator_id": operator_id,
        "reason": reason,
        "timestamp": str(system.date.now()),
        "equipment_status": self.getEquipmentStatus(recommendation_id)
    }

    # Send feedback asynchronously
    system.util.invokeAsynchronous(
        lambda: self._sendFeedback(feedback_url, feedback_data)
    )

def updateRecommendationStatus(self, recommendation_id, new_status):
    """
    Update recommendation status in local view
    """
    recommendations = self.view.custom.recommendations or []

    for rec in recommendations:
        if rec['recommendation_id'] == recommendation_id:
            rec['status'] = new_status
            break

    self.view.custom.recommendations = recommendations
    self.view.custom.pendingCount = len([r for r in recommendations if r['status'] == 'pending'])

# Component definition for action buttons
ACTION_BUTTONS_COMPONENT = {
    "type": "flex",
    "props": {
        "direction": "row",
        "gap": "5px"
    },
    "children": [
        {
            "type": "button",
            "props": {
                "text": "Approve",
                "primary": True,
                "icon": {
                    "path": "material/check",
                    "color": "#FFFFFF"
                },
                "style": {
                    "backgroundColor": "#4CAF50"
                },
                "onClick": {
                    "type": "script",
                    "config": {
                        "script": "self.onActionClick('approve', params.recommendationId, params.equipmentId)"
                    }
                }
            }
        },
        {
            "type": "button",
            "props": {
                "text": "Defer",
                "icon": {
                    "path": "material/schedule"
                },
                "style": {
                    "backgroundColor": "#FFA500"
                },
                "onClick": {
                    "type": "script",
                    "config": {
                        "script": "self.onActionClick('defer', params.recommendationId, params.equipmentId)"
                    }
                }
            }
        },
        {
            "type": "button",
            "props": {
                "text": "Reject",
                "icon": {
                    "path": "material/close"
                },
                "style": {
                    "backgroundColor": "#FF3621"
                },
                "onClick": {
                    "type": "script",
                    "config": {
                        "script": "self.onActionClick('reject', params.recommendationId, params.equipmentId)"
                    }
                }
            }
        },
        {
            "type": "button",
            "props": {
                "text": "Ask AI",
                "icon": {
                    "path": "material/psychology"
                },
                "style": {
                    "backgroundColor": "#00A8E1"
                },
                "onClick": {
                    "type": "script",
                    "config": {
                        "script": "self.onActionClick('ask_ai', params.recommendationId, params.equipmentId)"
                    }
                }
            }
        }
    ]
}