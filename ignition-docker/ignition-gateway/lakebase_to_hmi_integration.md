# Lakebase to HMI Integration Guide

## Method 1: Direct JDBC Connection with Named Queries

### 1.1 Configure Database Connection in Ignition

**Gateway Configuration:**
```xml
<!-- In Ignition Gateway Config > Databases > Connections -->
<database-connection>
    <name>Lakebase_Postgres</name>
    <driver>PostgreSQL</driver>
    <connect-url>jdbc:postgresql://workspace.cloud.databricks.com/lakebase</connect-url>
    <username>${LAKEBASE_USER}</username>
    <password>${LAKEBASE_PASSWORD}</password>
    <extra-params>
        warehouse=4b9b953939869799
        catalog=lakebase
        schema=agentic_hmi
    </extra-params>
    <validation-query>SELECT 1</validation-query>
    <pool-size>10</pool-size>
</database-connection>
```

### 1.2 Create Named Query in Ignition

**Named Query: GetPendingRecommendations**
```sql
-- Location: Project > Named Queries > Lakebase > GetPendingRecommendations
SELECT
    recommendation_id,
    equipment_id,
    issue_type,
    severity,
    issue_description,
    recommended_action,
    confidence_score,
    root_cause_analysis,
    expected_outcome,
    created_timestamp
FROM
    lakebase.agentic_hmi.agent_recommendations
WHERE
    status = 'pending'
    AND created_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY
    severity DESC,
    confidence_score DESC
LIMIT :limit
```

### 1.3 Perspective View Binding

```python
# Perspective View Script (Python)
def onStartup(self):
    """Called when view loads"""
    self.refreshRecommendations()

def refreshRecommendations(self):
    """Query Lakebase for latest recommendations"""
    params = {"limit": 10}

    # Execute named query
    results = system.db.runNamedQuery(
        "Lakebase/GetPendingRecommendations",
        params
    )

    # Convert to dataset for table component
    dataset = system.dataset.toDataSet(results)

    # Bind to table component
    self.getSibling("RecommendationsTable").props.data = dataset

    # Update badge count
    self.custom.pendingCount = dataset.getRowCount()

# Timer Component - Refresh every 5 seconds
def onTimerElapsed(self):
    self.refreshRecommendations()
```

## Method 2: WebDev REST API Module

### 2.1 Create WebDev Resource in Ignition

**Location:** Gateway > Config > WebDev > Resources

```python
# WebDev Resource: /lakebase/recommendations
# File: doGet.py

def doGet(request, session):
    """REST endpoint to fetch recommendations"""
    import system
    import json

    # Parse query parameters
    status = request['params'].get('status', 'pending')
    limit = int(request['params'].get('limit', 20))

    # Query Lakebase
    query = """
        SELECT
            recommendation_id,
            equipment_id,
            issue_type,
            severity,
            issue_description,
            recommended_action,
            confidence_score,
            root_cause_analysis,
            expected_outcome,
            status,
            created_timestamp
        FROM
            lakebase.agentic_hmi.agent_recommendations
        WHERE
            status = %s
        ORDER BY
            created_timestamp DESC
        LIMIT %s
    """

    results = system.db.runPrepQuery(
        query,
        [status, limit],
        "Lakebase_Postgres"
    )

    # Convert to JSON
    recommendations = []
    for row in results:
        recommendations.append({
            "id": row["recommendation_id"],
            "equipment": row["equipment_id"],
            "issue": row["issue_type"],
            "severity": row["severity"],
            "description": row["issue_description"],
            "action": row["recommended_action"],
            "confidence": float(row["confidence_score"]),
            "rootCause": row["root_cause_analysis"],
            "expectedOutcome": row["expected_outcome"],
            "status": row["status"],
            "timestamp": str(row["created_timestamp"])
        })

    return {
        'json': {
            "success": True,
            "count": len(recommendations),
            "recommendations": recommendations
        }
    }

# File: doPost.py
def doPost(request, session):
    """Handle operator actions on recommendations"""
    import system
    import json

    # Parse JSON body
    body = request['data']
    data = json.loads(body)

    recommendation_id = data['recommendation_id']
    action = data['action']  # 'approve', 'reject', 'defer'
    operator_id = session['user']
    notes = data.get('notes', '')

    # Update Lakebase
    if action == 'approve':
        query = """
            UPDATE lakebase.agentic_hmi.agent_recommendations
            SET
                status = 'approved',
                operator_id = %s,
                operator_notes = %s,
                approved_timestamp = CURRENT_TIMESTAMP
            WHERE
                recommendation_id = %s
        """

        system.db.runPrepUpdate(
            query,
            [operator_id, notes, recommendation_id],
            "Lakebase_Postgres"
        )

        # Execute recommended action (write tags)
        executeRecommendedAction(recommendation_id)

    elif action == 'reject':
        query = """
            UPDATE lakebase.agentic_hmi.agent_recommendations
            SET
                status = 'rejected',
                operator_id = %s,
                rejection_reason = %s,
                updated_timestamp = CURRENT_TIMESTAMP
            WHERE
                recommendation_id = %s
        """

        system.db.runPrepUpdate(
            query,
            [operator_id, notes, recommendation_id],
            "Lakebase_Postgres"
        )

    return {'json': {"success": True, "message": f"Action {action} completed"}}
```

### 2.2 Perspective View with REST Calls

```javascript
// Perspective View Custom Method: fetchRecommendations()
async function fetchRecommendations() {
    const baseUrl = '/system/webdev/project/lakebase/recommendations';

    try {
        // Fetch from WebDev API
        const response = await fetch(`${baseUrl}?status=pending&limit=10`);
        const data = await response.json();

        if (data.success) {
            // Update table data
            this.custom.recommendations = data.recommendations;

            // Update notification badge
            this.custom.notificationCount = data.count;

            // Show high-severity alerts
            data.recommendations
                .filter(r => r.severity === 'critical')
                .forEach(r => {
                    system.perspective.showPopup(
                        'CriticalAlert',
                        {recommendation: r}
                    );
                });
        }
    } catch (error) {
        console.error('Failed to fetch recommendations:', error);
    }
}

// Button onClick event for approval
async function approveRecommendation(recommendationId) {
    const baseUrl = '/system/webdev/project/lakebase/recommendations';

    const response = await fetch(baseUrl, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            recommendation_id: recommendationId,
            action: 'approve',
            notes: this.props.operatorNotes
        })
    });

    if (response.ok) {
        // Refresh the list
        await this.custom.fetchRecommendations();

        // Show success message
        system.perspective.showToast('Recommendation approved and executed');
    }
}
```

## Method 3: Transaction Groups with Stored Procedures

### 3.1 Create Stored Procedure in Lakebase

```sql
-- Stored procedure in Lakebase
CREATE OR REPLACE PROCEDURE lakebase.agentic_hmi.sp_get_active_alerts()
RETURNS TABLE(
    equipment_id VARCHAR,
    alert_type VARCHAR,
    severity VARCHAR,
    message TEXT,
    timestamp TIMESTAMP
)
LANGUAGE SQL
AS $$
    SELECT
        ar.equipment_id,
        ar.issue_type as alert_type,
        ar.severity,
        ar.issue_description as message,
        ar.created_timestamp as timestamp
    FROM
        agent_recommendations ar
    WHERE
        ar.status = 'pending'
        AND ar.severity IN ('critical', 'high')
        AND ar.created_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'

    UNION ALL

    SELECT
        sd.equipment_id,
        'sensor_anomaly' as alert_type,
        CASE
            WHEN sd.quality = 'critical' THEN 'critical'
            ELSE 'high'
        END as severity,
        CONCAT('Sensor ', sd.sensor_type, ' reading: ', sd.sensor_value, ' ', sd.units) as message,
        sd.timestamp
    FROM
        sensor_data sd
    WHERE
        sd.quality IN ('critical', 'warning')
        AND sd.timestamp > CURRENT_TIMESTAMP - INTERVAL '10 minutes'

    ORDER BY
        timestamp DESC;
$$;
```

### 3.2 Configure Transaction Group in Ignition

```xml
<!-- Transaction Group Configuration -->
<transaction-group>
    <name>Lakebase_Alert_Sync</name>
    <type>Stored Procedure</type>
    <database>Lakebase_Postgres</database>
    <stored-procedure>lakebase.agentic_hmi.sp_get_active_alerts</stored-procedure>
    <trigger>
        <type>Timer</type>
        <rate>5000</rate> <!-- 5 seconds -->
    </trigger>
    <items>
        <!-- Map results to tags -->
        <item>
            <source>equipment_id</source>
            <target>[default]Alerts/Equipment</target>
        </item>
        <item>
            <source>alert_type</source>
            <target>[default]Alerts/Type</target>
        </item>
        <item>
            <source>severity</source>
            <target>[default]Alerts/Severity</target>
        </item>
        <item>
            <source>message</source>
            <target>[default]Alerts/Message</target>
        </item>
        <item>
            <source>timestamp</source>
            <target>[default]Alerts/Timestamp</target>
        </item>
    </items>
    <options>
        <store-and-forward>true</store-and-forward>
        <retry-count>3</retry-count>
    </options>
</transaction-group>
```

### 3.3 Perspective Binding to Tags

```python
# Perspective View - Bind to tags updated by transaction group
def configureBindings(self):
    """Set up tag bindings for real-time updates"""

    # Bind alert data to display components
    alertConfig = {
        'path': '[default]Alerts',
        'type': 'tag',
        'bidirectional': False
    }

    # Create indirect binding for dynamic equipment
    self.custom.alertBinding = system.tag.bindIndirect(
        self.props.selectedEquipment,
        '[default]Alerts/{equipment}/CurrentAlert',
        'equipment'
    )

    # Subscribe to changes
    def onAlertChange(event):
        if event.getValue().quality.isGood():
            alert = event.getValue().value
            if alert['severity'] == 'critical':
                # Show popup for critical alerts
                system.perspective.openPopup(
                    'CriticalAlertPopup',
                    view='Alerts/CriticalAlert',
                    params={'alert': alert}
                )

    system.tag.subscribe(
        '[default]Alerts/*/CurrentAlert',
        onAlertChange
    )
```

## Method 4: Gateway Event Scripts (Push Notifications)

### 4.1 Gateway Timer Script

```python
# Gateway Event Script - Timer (runs every 10 seconds)
def onTimer():
    """Push critical recommendations to all active sessions"""

    # Query Lakebase for critical alerts
    query = """
        SELECT * FROM lakebase.agentic_hmi.agent_recommendations
        WHERE status = 'pending'
        AND severity = 'critical'
        AND created_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 minute'
    """

    results = system.db.runQuery(query, "Lakebase_Postgres")

    if results.rowCount > 0:
        # Send to all Perspective sessions
        sessions = system.perspective.getSessionInfo()

        for session in sessions:
            # Send message to session
            system.perspective.sendMessage(
                'CriticalAlert',
                payload={
                    'recommendations': system.dataset.toPyDataSet(results),
                    'count': results.rowCount
                },
                scope='session',
                sessionId=session.id
            )
```

### 4.2 Perspective Message Handler

```python
# Perspective View - Message Handler
def onMessageReceived(self, payload):
    """Handle pushed messages from gateway"""

    if payload['type'] == 'CriticalAlert':
        # Update UI with critical alerts
        self.custom.criticalAlerts = payload['recommendations']

        # Play alert sound
        system.perspective.playSound('alert')

        # Flash the screen border
        self.props.root.style.classes = 'alert-flash'

        # Show notification
        system.perspective.showNotification(
            f"{payload['count']} Critical Alerts Require Attention!",
            type='error',
            duration=10000
        )
```

## Performance Comparison

| Method | Latency | Use Case | Pros | Cons |
|--------|---------|----------|------|------|
| **Direct JDBC** | 100-500ms | On-demand queries | Simple, reliable | Polling overhead |
| **WebDev API** | 50-200ms | REST integration | Flexible, cacheable | Requires API setup |
| **Transaction Groups** | 1-5 seconds | Continuous sync | Automatic, reliable | Fixed intervals |
| **Gateway Push** | <100ms | Critical alerts | Real-time, efficient | Complex setup |

## Recommended Architecture

For the AI-Powered Monitoring System, use a **hybrid approach**:

1. **WebDev API** for normal recommendations (5-second refresh)
2. **Gateway Push** for critical alerts (immediate)
3. **Direct JDBC** for operator-triggered reports
4. **Transaction Groups** for equipment status sync

## Example: Complete Integration Flow

```python
# Complete flow from Lakebase to HMI action
class RecommendationHandler:

    def __init__(self):
        self.db_connection = "Lakebase_Postgres"

    def fetch_pending(self):
        """Fetch pending recommendations from Lakebase"""
        query = """
            SELECT * FROM lakebase.agentic_hmi.agent_recommendations
            WHERE status = 'pending'
            ORDER BY severity DESC, confidence_score DESC
        """
        return system.db.runQuery(query, self.db_connection)

    def display_in_hmi(self, recommendations):
        """Display in Perspective view"""
        for rec in recommendations:
            # Create card component for each recommendation
            card = {
                'type': 'recommendation-card',
                'props': {
                    'title': f"{rec['equipment_id']} - {rec['issue_type']}",
                    'severity': rec['severity'],
                    'confidence': rec['confidence_score'],
                    'description': rec['issue_description'],
                    'action': rec['recommended_action'],
                    'buttons': ['APPROVE', 'DEFER', 'REJECT']
                }
            }
            self.view.props.cards.append(card)

    def handle_approval(self, recommendation_id):
        """Handle operator approval"""
        # Update Lakebase
        update_query = """
            UPDATE lakebase.agentic_hmi.agent_recommendations
            SET status = 'approved',
                operator_id = ?,
                approved_timestamp = CURRENT_TIMESTAMP
            WHERE recommendation_id = ?
        """
        system.db.runPrepUpdate(
            update_query,
            [self.session.user, recommendation_id],
            self.db_connection
        )

        # Execute recommended action (write to OPC tags)
        self.execute_action(recommendation_id)

    def execute_action(self, recommendation_id):
        """Execute the approved action by writing to equipment tags"""
        # Fetch the recommendation details
        rec = self.get_recommendation(recommendation_id)

        # Parse action and write to tags
        if "reduce throughput" in rec['recommended_action'].lower():
            # Write new setpoint to tag
            tag_path = f"[default]Equipment/{rec['equipment_id']}/Throughput_SP"
            new_value = self.calculate_reduced_throughput(rec)
            system.tag.writeBlocking([tag_path], [new_value])

            # Log action
            self.log_action(f"Reduced throughput to {new_value}% for {rec['equipment_id']}")
```

## Security Considerations

1. **Authentication**: Use OAuth2/certificates for Lakebase connection
2. **Authorization**: Role-based access to recommendations
3. **Encryption**: TLS for all database connections
4. **Audit Trail**: Log all operator actions
5. **Data Validation**: Sanitize all inputs before database operations

This is how data flows from Lakebase to the HMI, enabling operators to see and act on AI-generated recommendations in real-time!