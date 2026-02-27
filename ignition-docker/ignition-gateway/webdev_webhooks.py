# Ignition WebDev Module - Webhook Implementation
# Location: /system/webdev/project/databricks/webhooks/

"""
WEBHOOK ARCHITECTURE:
1. Databricks/Lakebase sends POST request to Ignition
2. WebDev module receives and processes
3. Updates tags and notifies Perspective clients
4. Returns acknowledgment to sender
"""

# ============================================
# File: /recommendations/doPost.py
# URL: http://ignition-gateway:8088/system/webdev/databricks/webhooks/recommendations
# ============================================

def doPost(request, session):
    """
    Webhook endpoint for ML recommendations from Databricks/Lakebase
    Called when new recommendations are written to Lakebase
    """
    import system
    import json
    from java.util import Date

    try:
        # Parse incoming JSON payload
        body = request['data']
        data = json.loads(body)

        # Validate required fields
        required_fields = ['recommendation_id', 'equipment_id', 'action_code', 'urgency']
        for field in required_fields:
            if field not in data:
                return {
                    'json': {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
                }

        # Log webhook receipt
        logger = system.util.getLogger("Webhook.Recommendations")
        logger.info(f"Received recommendation: {data['recommendation_id']} for {data['equipment_id']}")

        # 1. Write to memory tags for immediate access
        base_path = f"[default]MLRecommendations/Active/{data['equipment_id']}"

        tag_paths = [
            f"{base_path}/recommendation_id",
            f"{base_path}/action_code",
            f"{base_path}/confidence",
            f"{base_path}/urgency",
            f"{base_path}/time_to_failure",
            f"{base_path}/parts_list",
            f"{base_path}/timestamp",
            f"{base_path}/status"
        ]

        tag_values = [
            data.get('recommendation_id'),
            data.get('action_code'),
            float(data.get('confidence', 0)),
            int(data.get('urgency', 3)),
            float(data.get('time_to_failure', 0)) if data.get('time_to_failure') else None,
            str(data.get('parts_list', [])),
            Date(),  # Current timestamp
            'pending'
        ]

        # Write all tags at once
        system.tag.writeBlocking(tag_paths, tag_values)

        # 2. Update recommendation count for badge
        count_path = "[default]MLRecommendations/PendingCount"
        current_count = system.tag.readBlocking([count_path])[0].value or 0
        system.tag.writeBlocking([count_path], [current_count + 1])

        # 3. Send message to all Perspective sessions
        message_payload = {
            'type': 'NEW_ML_RECOMMENDATION',
            'recommendation': data,
            'timestamp': system.date.now()
        }

        # Broadcast to all sessions
        system.perspective.sendMessage(
            messageType='MLRecommendation',
            payload=message_payload,
            scope='session',  # All sessions
            sessionId='*'  # Wildcard for all
        )

        # 4. Create alarm for high urgency recommendations
        if data.get('urgency', 0) >= 4:
            # Map urgency to alarm priority
            alarm_priority = 1 if data['urgency'] == 5 else 2  # Critical or High

            # Create alarm
            system.alarm.createAlarm(
                source=f"MLRecommendations/{data['equipment_id']}",
                name=f"ML_{data['action_code']}",
                priority=alarm_priority,
                label=f"ML: {data['action_code']} ({data.get('confidence', 0):.0%} confidence)",
                notes=f"Auto-generated from ML model. Failure in {data.get('time_to_failure', 'unknown')} hours"
            )

        # 5. Store in dataset for table display
        dataset_tag = "[default]MLRecommendations/Dataset"
        existing = system.tag.readBlocking([dataset_tag])[0].value

        if existing:
            # Add to existing dataset
            rows = system.dataset.toPyDataSet(existing)
            rows.insert(0, [
                data['recommendation_id'],
                data['equipment_id'],
                data['action_code'],
                data.get('confidence', 0),
                data['urgency'],
                data.get('time_to_failure'),
                Date(),
                'pending'
            ])
            # Keep only last 100 recommendations
            rows = rows[:100]
        else:
            # Create new dataset
            headers = ['ID', 'Equipment', 'Action', 'Confidence', 'Urgency', 'TTF', 'Timestamp', 'Status']
            rows = [[
                data['recommendation_id'],
                data['equipment_id'],
                data['action_code'],
                data.get('confidence', 0),
                data['urgency'],
                data.get('time_to_failure'),
                Date(),
                'pending'
            ]]

        new_dataset = system.dataset.toDataSet(headers, rows)
        system.tag.writeBlocking([dataset_tag], [new_dataset])

        # Return success response
        return {
            'json': {
                'success': True,
                'message': f"Recommendation {data['recommendation_id']} received and processed",
                'timestamp': str(Date())
            }
        }

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {
            'json': {
                'success': False,
                'error': str(e)
            }
        }

# ============================================
# File: /alarms/doPost.py
# URL: http://ignition-gateway:8088/system/webdev/databricks/webhooks/alarms
# ============================================

def doPost(request, session):
    """
    Webhook for critical alarms that need immediate attention
    """
    import system
    import json

    try:
        data = json.loads(request['data'])

        # Create high-priority alarm immediately
        alarm_id = system.alarm.createAlarm(
            source=f"Webhooks/{data['source']}",
            name=data['alarm_name'],
            priority=0,  # Critical
            label=data['label'],
            notes=data.get('notes', ''),
            ackMode='Manual'
        )

        # Flash all operator screens
        system.perspective.sendMessage(
            messageType='CriticalAlarm',
            payload={'alarm': data, 'id': alarm_id},
            scope='page'
        )

        return {'json': {'success': True, 'alarm_id': alarm_id}}

    except Exception as e:
        return {'json': {'success': False, 'error': str(e)}}

# ============================================
# File: /operator_feedback/doPost.py
# URL: http://ignition-gateway:8088/system/webdev/databricks/webhooks/operator_feedback
# ============================================

def doPost(request, session):
    """
    Receives operator decision feedback to send back to ML training
    """
    import system
    import json

    try:
        data = json.loads(request['data'])

        # Forward to Databricks for ML model improvement
        import httplib2
        h = httplib2.Http()

        databricks_url = "https://workspace.cloud.databricks.com/api/2.0/lakebase/feedback"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {system.tag.readBlocking(["[default]Config/DatabricksToken"])[0].value}'
        }

        feedback_payload = {
            'recommendation_id': data['recommendation_id'],
            'operator_decision': data['decision'],  # approve/reject/defer
            'operator_id': data['operator_id'],
            'operator_notes': data.get('notes', ''),
            'execution_result': data.get('result', 'unknown'),
            'timestamp': str(system.date.now())
        }

        response, content = h.request(
            databricks_url,
            'POST',
            body=json.dumps(feedback_payload),
            headers=headers
        )

        return {'json': {'success': response.status == 200}}

    except Exception as e:
        return {'json': {'success': False, 'error': str(e)}}

# ============================================
# File: /test/doGet.py
# URL: http://ignition-gateway:8088/system/webdev/databricks/webhooks/test
# ============================================

def doGet(request, session):
    """
    Test endpoint to verify webhook is working
    """
    return {
        'json': {
            'status': 'Webhook system operational',
            'endpoints': [
                '/recommendations - Receive ML recommendations',
                '/alarms - Receive critical alarms',
                '/operator_feedback - Send operator decisions to ML'
            ],
            'timestamp': str(system.date.now())
        }
    }

# ============================================
# DATABRICKS SIDE - Webhook Sender
# ============================================

"""
# In Databricks notebook or Python script
import requests
import json

def send_recommendation_to_ignition(recommendation):
    '''
    Send ML recommendation to Ignition via webhook
    '''
    webhook_url = "http://ignition-gateway:8088/system/webdev/databricks/webhooks/recommendations"

    payload = {
        'recommendation_id': recommendation['id'],
        'equipment_id': recommendation['equipment_id'],
        'action_code': recommendation['action_code'],
        'confidence': float(recommendation['confidence']),
        'urgency': int(recommendation['urgency']),
        'time_to_failure': float(recommendation['time_to_failure']) if recommendation['time_to_failure'] else None,
        'parts_list': recommendation.get('parts_list', [])
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=5,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            print(f"✓ Webhook sent: {recommendation['id']}")
            return True
        else:
            print(f"✗ Webhook failed: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("✗ Webhook timeout - Ignition may be down")
        return False
    except Exception as e:
        print(f"✗ Webhook error: {str(e)}")
        return False

# Use in streaming foreachBatch
def process_batch(df, epoch_id):
    # Write to Lakebase
    df.write.jdbc(url="jdbc:postgresql://lakebase", table="ml_recommendations")

    # Send webhooks for high-urgency items
    high_urgency = df.filter(F.col("urgency") >= 4).collect()
    for row in high_urgency:
        send_recommendation_to_ignition(row.asDict())
"""

# ============================================
# IGNITION TAG STRUCTURE
# ============================================

"""
Tag Structure Created by Webhooks:

[default]
├── MLRecommendations/
│   ├── PendingCount (Integer) - Badge count
│   ├── Dataset (Dataset) - For table display
│   ├── Active/
│   │   ├── CRUSHER_01/
│   │   │   ├── recommendation_id (String)
│   │   │   ├── action_code (String)
│   │   │   ├── confidence (Float)
│   │   │   ├── urgency (Integer)
│   │   │   ├── time_to_failure (Float)
│   │   │   ├── parts_list (String)
│   │   │   ├── timestamp (DateTime)
│   │   │   └── status (String)
│   │   ├── HAUL_TRUCK_02/
│   │   │   └── ... (same structure)
│   │   └── .../
│   └── Config/
│       ├── WebhookEnabled (Boolean)
│       └── DatabricksToken (String)
"""

# ============================================
# PERSPECTIVE VIEW WEBHOOK HANDLER
# ============================================

"""
# Perspective View Script - Message Handler
def onMessageReceived(self, payload):
    '''
    Handle webhook notifications pushed from gateway
    '''
    if payload.messageType == 'MLRecommendation':
        recommendation = payload.recommendation

        # Add to view's recommendation list
        recommendations = self.custom.recommendations or []
        recommendations.insert(0, recommendation)  # Add to top
        self.custom.recommendations = recommendations[:50]  # Keep last 50

        # Update notification badge
        self.getChild("NotificationBadge").props.count += 1

        # Flash the new recommendation
        self.getChild("RecommendationTable").meta.flashRow = recommendation['recommendation_id']

        # Show popup for critical items
        if recommendation.get('urgency', 0) >= 4:
            system.perspective.openPopup(
                id='CriticalRecommendation',
                view='Popups/CriticalMLRecommendation',
                params={'data': recommendation},
                position={'x': 100, 'y': 100},
                showCloseIcon=True,
                draggable=True,
                resizable=False,
                modal=False,
                overlayDismiss=False
            )

            # Play alert sound
            self.getChild("AudioPlayer").props.source = "/audio/critical_alert.wav"
            self.getChild("AudioPlayer").play()

    elif payload.messageType == 'CriticalAlarm':
        # Handle critical alarm webhooks
        self.custom.criticalAlarm = payload.alarm
        self.getChild("AlarmBanner").props.visible = True
        self.getChild("AlarmBanner").props.message = payload.alarm['label']
"""