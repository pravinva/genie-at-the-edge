"""
WebDev Module for Genie Chat Integration
This module handles the chat interface between Perspective and Databricks Genie
"""

import json
import system.util
import system.net.httpClient
from datetime import datetime

# Databricks connection settings
DATABRICKS_HOST = system.tag.read("[default]Databricks/Host").value
DATABRICKS_TOKEN = system.tag.read("[default]Databricks/Token").value
GENIE_SPACE_ID = system.tag.read("[default]Databricks/GenieSpaceId").value

def doPost(request, session):
    """
    Handle POST requests for chat messages
    """
    try:
        data = request.get("data")
        if not data:
            return {"error": "No data provided"}

        message = data.get("message", "")
        context = data.get("context", {})

        # Add operational context from tags
        context.update({
            "timestamp": datetime.now().isoformat(),
            "equipment": get_equipment_context(),
            "alerts": get_active_alerts(),
            "recent_predictions": get_recent_predictions()
        })

        # Send to Databricks Genie
        response = query_genie(message, context)

        # Store conversation in tags for history
        store_conversation(message, response)

        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def query_genie(message, context):
    """
    Query Databricks Genie with operational context
    """
    url = f"https://{DATABRICKS_HOST}/api/2.0/genie/spaces/{GENIE_SPACE_ID}/conversations/messages"

    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Format the query with operational context
    enhanced_query = format_query_with_context(message, context)

    payload = {
        "content": enhanced_query,
        "conversation_id": get_or_create_conversation_id()
    }

    # Make HTTP request to Genie
    client = system.net.httpClient()
    response = client.post(url, headers=headers, data=json.dumps(payload))

    if response.statusCode == 200:
        result = json.loads(response.text)
        return parse_genie_response(result)
    else:
        raise Exception(f"Genie API error: {response.statusCode}")

def format_query_with_context(message, context):
    """
    Enhance user query with operational context
    """
    context_str = f"""
    Current Equipment Status:
    {json.dumps(context.get('equipment', {}), indent=2)}

    Active Alerts:
    {json.dumps(context.get('alerts', []), indent=2)}

    Recent AI Predictions:
    {json.dumps(context.get('recent_predictions', []), indent=2)}

    User Query: {message}

    Please provide operational insights and recommendations based on the current plant status.
    """
    return context_str

def get_equipment_context():
    """
    Get current equipment status from tags
    """
    equipment = {}
    tag_paths = [
        "[default]Equipment/HaulTruck_001/Status",
        "[default]Equipment/Crusher_001/Status",
        "[default]Equipment/Crusher_002/Status",
        "[default]Equipment/Conveyor_001/Status",
        "[default]Equipment/Conveyor_002/Status"
    ]

    for path in tag_paths:
        try:
            value = system.tag.read(path)
            equipment_name = path.split("/")[1]
            equipment[equipment_name] = {
                "status": value.value,
                "quality": value.quality.toString(),
                "timestamp": value.timestamp
            }
        except:
            pass

    return equipment

def get_active_alerts():
    """
    Get active alerts and anomalies
    """
    alerts = []

    # Check for anomaly predictions
    anomaly_tags = system.tag.browse("[default]Predictions/Anomalies")
    for tag in anomaly_tags:
        value = system.tag.read(tag.fullPath)
        if value.value > 0.7:  # High anomaly score
            alerts.append({
                "type": "anomaly",
                "equipment": tag.name,
                "score": value.value,
                "timestamp": value.timestamp
            })

    # Check for maintenance predictions
    maintenance_tags = system.tag.browse("[default]Predictions/Maintenance")
    for tag in maintenance_tags:
        value = system.tag.read(tag.fullPath)
        if value.value == "Required":
            alerts.append({
                "type": "maintenance",
                "equipment": tag.name,
                "status": value.value,
                "timestamp": value.timestamp
            })

    return alerts

def get_recent_predictions():
    """
    Get recent AI model predictions
    """
    predictions = []

    # Read recent prediction results
    prediction_history = system.tag.readAll([
        "[default]Predictions/Latest/Timestamp",
        "[default]Predictions/Latest/Type",
        "[default]Predictions/Latest/Result",
        "[default]Predictions/Latest/Confidence"
    ])

    if prediction_history[0].value:
        predictions.append({
            "timestamp": prediction_history[0].value,
            "type": prediction_history[1].value,
            "result": prediction_history[2].value,
            "confidence": prediction_history[3].value
        })

    return predictions

def parse_genie_response(response):
    """
    Parse Genie response and extract relevant information
    """
    # Extract the main response text
    message = response.get("message", {}).get("content", "No response from Genie")

    # Check if response contains SQL or recommendations
    if "SELECT" in message.upper():
        # Genie provided a SQL query - execute it
        sql_result = execute_genie_sql(message)
        return format_sql_response(sql_result)
    elif "recommend" in message.lower() or "suggest" in message.lower():
        # Genie provided recommendations
        return format_recommendations(message)
    else:
        # General response
        return message

def execute_genie_sql(sql_query):
    """
    Execute SQL query from Genie against Delta Lake
    """
    # This would connect to Databricks SQL endpoint
    # For now, return a placeholder
    return {
        "query": sql_query,
        "results": "Query execution would happen here"
    }

def format_sql_response(sql_result):
    """
    Format SQL query results for display
    """
    return f"""
    Query Executed: {sql_result['query'][:100]}...

    Results: {sql_result['results']}
    """

def format_recommendations(message):
    """
    Format AI recommendations for operators
    """
    # Extract key recommendations
    lines = message.split('\n')
    recommendations = []

    for line in lines:
        if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'action']):
            recommendations.append(line.strip())

    if recommendations:
        return "AI Recommendations:\n" + "\n".join([f"• {r}" for r in recommendations])
    else:
        return message

def store_conversation(user_message, genie_response):
    """
    Store conversation history in tags
    """
    # Store last 10 messages in circular buffer
    history_base = "[default]Genie/ConversationHistory"

    # Read current index
    index_tag = f"{history_base}/Index"
    current_index = system.tag.read(index_tag).value or 0
    next_index = (current_index + 1) % 10

    # Store user message
    user_tag = f"{history_base}/Message_{next_index}/User"
    system.tag.write(user_tag, user_message)

    # Store Genie response
    genie_tag = f"{history_base}/Message_{next_index}/Genie"
    system.tag.write(genie_tag, genie_response)

    # Store timestamp
    time_tag = f"{history_base}/Message_{next_index}/Timestamp"
    system.tag.write(time_tag, datetime.now())

    # Update index
    system.tag.write(index_tag, next_index)

def get_or_create_conversation_id():
    """
    Get or create a conversation ID for the current session
    """
    conv_id_tag = "[default]Genie/ConversationId"
    conv_id = system.tag.read(conv_id_tag).value

    if not conv_id:
        # Create new conversation ID
        import uuid
        conv_id = str(uuid.uuid4())
        system.tag.write(conv_id_tag, conv_id)

    return conv_id

def doGet(request, session):
    """
    Handle GET requests for conversation history
    """
    try:
        history = []
        history_base = "[default]Genie/ConversationHistory"

        for i in range(10):
            user_msg = system.tag.read(f"{history_base}/Message_{i}/User").value
            genie_msg = system.tag.read(f"{history_base}/Message_{i}/Genie").value
            timestamp = system.tag.read(f"{history_base}/Message_{i}/Timestamp").value

            if user_msg and genie_msg:
                history.append({
                    "user": user_msg,
                    "genie": genie_msg,
                    "timestamp": timestamp
                })

        # Sort by timestamp
        history.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min)

        return {
            "success": True,
            "history": history[-5:]  # Return last 5 messages
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }