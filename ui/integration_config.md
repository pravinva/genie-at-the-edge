# Genie Chat UI Integration Configuration

## Overview

This document provides configuration details for integrating the Genie Chat UI into Ignition Perspective views for the Mining Operations Demo.

## Architecture

```
Ignition Perspective View
    └── Embedded Frame Component
            └── genie_chat_perspective.html (hosted on Databricks)
                    └── Databricks Genie API
                            └── Lakehouse Data (equipment, production, alarms)
```

## Prerequisites

1. **Databricks Setup Complete** (from Workstream 07)
   - Genie Space created and configured
   - SQL Warehouse running
   - Tables connected to Genie Space
   - Personal Access Token generated

2. **HTML File Deployed** (from this workstream)
   - `genie_chat_perspective.html` uploaded to Databricks Files
   - File accessible at: `https://adb-{workspace_id}.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html`

3. **Ignition Gateway** (8.1.17+)
   - Perspective Module enabled
   - Internet access to Databricks (outbound HTTPS)

---

## Step 1: Session Property Configuration

Add these custom session properties in Perspective:

### Session Properties

| Property Name | Type | Default Value | Description |
|---------------|------|---------------|-------------|
| `databricks_workspace_id` | String | `"1234567890123456"` | Your Databricks workspace ID |
| `databricks_token` | String | `""` | Personal Access Token (encrypted) |
| `genie_space_id` | String | `"01abc123-4567-89de-f012-3456789abcde"` | Genie Space ID from workstream 07 |

### How to Add Session Properties

1. Open Perspective project in Designer
2. Navigate to **Project Browser** → **Session Events**
3. Add `configure` event script:

```python
# Session startup script
def configure(self, session):
    """Initialize Databricks connection parameters"""

    # Set workspace ID (get from Databricks URL)
    session.custom.databricks_workspace_id = "YOUR_WORKSPACE_ID"

    # Set Genie Space ID (from workstream 07)
    session.custom.genie_space_id = "YOUR_SPACE_ID"

    # Load token from secure storage (encrypted)
    # Option A: From gateway tag
    token = system.tag.readBlocking(["[default]Configuration/Databricks/Token"])[0].value
    session.custom.databricks_token = token

    # Option B: From database (more secure)
    # token = system.db.runPrepQuery("SELECT token FROM databricks_config WHERE active=1", "YourDatabase")[0]['token']
    # session.custom.databricks_token = token
```

**Security Note:** Never hardcode tokens in scripts. Use encrypted storage.

---

## Step 2: Create Chat View

Create a new Perspective view for the chat interface.

### View Configuration

**View Name:** `MiningOperations/GenieChat`

**Root Container:**
- Type: `Flex Container`
- Direction: `column`
- Height: `100%`
- Width: `500px`

### Component Tree

```
View Root (Flex Container)
  └── Embedded Frame
        └── props.url = [Expression Binding]
```

### Embedded Frame Configuration

**Component:** `Embedded Frame`

**Properties:**

```json
{
  "style": {
    "width": "100%",
    "height": "100%",
    "border": "none"
  },
  "props": {
    "url": "[Expression - see below]"
  }
}
```

**URL Expression Binding:**

```python
concat(
  "https://adb-",
  {session.custom.databricks_workspace_id},
  ".azuredatabricks.net/files/mining-demo/genie_chat_perspective.html",
  "?token=", {session.custom.databricks_token},
  "&workspace=", {session.custom.databricks_workspace_id},
  "&space=", {session.custom.genie_space_id},
  if(len({view.custom.pending_question}) > 0,
    concat("&question=", urlEncode({view.custom.pending_question})),
    ""
  )
)
```

**Custom View Properties:**

Add to the view:

| Property Name | Type | Default | Description |
|---------------|------|---------|-------------|
| `pending_question` | String | `""` | Pre-filled question from other views |
| `visible` | Boolean | `false` | Chat panel visibility |

---

## Step 3: Alarm Integration

Add "Ask AI" button to alarm displays.

### Alarm Table Configuration

Add a column to your alarm table with a button:

**Button Script (onClick):**

```python
def runAction(self, event):
    """Send alarm info to Genie Chat"""

    # Get alarm details
    alarm_name = self.parent.custom.alarm_name
    alarm_time = system.date.format(self.parent.custom.alarm_time, "yyyy-MM-dd HH:mm:ss")
    equipment_id = self.parent.custom.equipment_id
    alarm_value = self.parent.custom.alarm_value

    # Format question for Genie
    question = f"Why did alarm '{alarm_name}' trigger at {alarm_time}? Equipment: {equipment_id}, Value: {alarm_value}"

    # Send message to chat view
    system.perspective.sendMessage(
        messageType='genie-chat',
        payload={
            'action': 'setQuestion',
            'question': question
        },
        scope='page'
    )

    # Open chat panel (if using popup or docked view)
    system.perspective.openPopup(
        id='genieChat',
        view='MiningOperations/GenieChat',
        params={'pending_question': question},
        position={'left': 'auto', 'right': 0, 'top': 0, 'bottom': 0},
        modal=False,
        draggable=False,
        resizable=False
    )
```

---

## Step 4: Equipment View Integration

Add "Ask About This Equipment" button to equipment detail views.

### Equipment Detail Button

**Button Text:** "Ask AI Assistant"

**Button Script:**

```python
def runAction(self, event):
    """Open chat with equipment-specific question"""

    # Get equipment details from view params
    equipment_name = self.view.params.equipment_name
    equipment_id = self.view.params.equipment_id

    # Get current status
    current_status = self.getSibling("StatusLabel").props.text
    current_alarm_count = self.getSibling("AlarmCountLabel").props.text

    # Format question
    question = f"What is the current status of {equipment_name} (ID: {equipment_id})? Current alarms: {current_alarm_count}"

    # Open chat with pre-filled question
    system.perspective.openPopup(
        id='genieChat',
        view='MiningOperations/GenieChat',
        params={'pending_question': question},
        position={'right': 0, 'top': 0, 'bottom': 0, 'width': 500},
        modal=False
    )
```

---

## Step 5: Trend Chart Integration

Add context menu to trend charts for AI analysis.

### Trend Chart Context Menu

**Context Menu Item:** "Analyze with AI"

**Script:**

```python
def runAction(self, event):
    """Send trend data to Genie for analysis"""

    # Get chart properties
    tag_name = self.parent.props.series[0].tagPath
    start_time = self.parent.props.range.startDate
    end_time = self.parent.props.range.endDate

    # Format dates
    start_str = system.date.format(start_time, "yyyy-MM-dd HH:mm")
    end_str = system.date.format(end_time, "yyyy-MM-dd HH:mm")

    # Create question
    question = f"Analyze the trend for {tag_name} from {start_str} to {end_str}. What patterns or anomalies do you see?"

    # Open chat
    system.perspective.openPopup(
        id='genieChat',
        view='MiningOperations/GenieChat',
        params={'pending_question': question},
        position={'right': 0, 'top': 0, 'bottom': 0, 'width': 500},
        modal=False
    )
```

---

## Step 6: Message Handler Configuration

Enable bi-directional messaging between views and chat.

### Global Message Handler

Add to **Project Browser** → **Message Handlers**:

**Handler ID:** `genie-chat`

**Handler Script:**

```python
def messageHandler(self, payload):
    """
    Handle messages sent to Genie Chat

    Supported actions:
    - setQuestion: Pre-fill question in chat
    - clearChat: Clear conversation history
    """

    action = payload.get('action')

    if action == 'setQuestion':
        question = payload.get('question', '')

        # Find chat view and update
        chat_view = self.getView('MiningOperations/GenieChat')
        if chat_view:
            chat_view.custom.pending_question = question

    elif action == 'clearChat':
        # Reset chat
        chat_view = self.getView('MiningOperations/GenieChat')
        if chat_view:
            chat_view.custom.pending_question = ''
```

---

## Step 7: Layout Patterns

Choose a layout pattern for the chat interface.

### Option A: Docked Right Panel (Recommended)

**Use Case:** Always-available chat that doesn't interrupt workflow

**Implementation:**

1. Add `GenieChat` view to main page template
2. Set width: `500px`
3. Add collapse/expand button
4. Position: `position: fixed; right: 0; top: 48px; bottom: 0;`

**CSS:**

```css
.chat-panel {
  position: fixed;
  right: 0;
  top: 48px; /* Below header */
  bottom: 0;
  width: 500px;
  z-index: 1000;
  box-shadow: -4px 0 16px rgba(0,0,0,0.3);
  transition: transform 300ms ease;
}

.chat-panel.collapsed {
  transform: translateX(500px);
}
```

### Option B: Popup Modal

**Use Case:** On-demand chat that maximizes main view space

**Implementation:**

```python
# Open chat as popup
system.perspective.openPopup(
    id='genieChat',
    view='MiningOperations/GenieChat',
    params={},
    position={'right': 0, 'top': 0, 'bottom': 0, 'width': 500},
    modal=False,
    draggable=False,
    resizable=True,
    showCloseIcon=True
)
```

### Option C: Tab View

**Use Case:** Chat as one of several tabs in a multi-function panel

**Implementation:**

Add `GenieChat` view as a tab in a Tab Container alongside:
- Alarm List
- Trend Charts
- Equipment Status

---

## Step 8: Testing Checklist

### Standalone Testing (Before Integration)

1. **Direct URL Access:**
   ```
   https://adb-{workspace}.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html?token={TOKEN}&workspace={WORKSPACE}&space={SPACE}
   ```
   - Chat loads without errors
   - Dark theme applied correctly
   - Typing and sending messages works
   - Responses render properly

2. **Pre-filled Questions:**
   ```
   ...&question=Why%20is%20Crusher%202%20vibrating%3F
   ```
   - Question appears in input field
   - Can be edited before sending

### Integrated Testing (In Perspective)

3. **Session Properties:**
   - [ ] Token loaded correctly (check browser console)
   - [ ] Workspace ID populated
   - [ ] Space ID populated

4. **Embedding:**
   - [ ] Iframe loads within Perspective view
   - [ ] No CORS errors
   - [ ] Styling matches Perspective theme
   - [ ] No layout issues or scrollbars

5. **Alarm Integration:**
   - [ ] Click "Ask AI" on alarm
   - [ ] Chat opens with pre-filled question
   - [ ] Can send or edit question
   - [ ] Response relevant to alarm

6. **Equipment Integration:**
   - [ ] Click equipment detail button
   - [ ] Chat opens with equipment question
   - [ ] Response includes equipment data

7. **Performance:**
   - [ ] Chat loads in <2 seconds
   - [ ] Messages render smoothly
   - [ ] Scrolling is smooth (60 FPS)
   - [ ] No memory leaks after 30 minutes

---

## Troubleshooting

### Issue: Iframe Won't Load

**Symptoms:** Blank iframe or "Cannot connect" error

**Causes & Solutions:**

1. **CORS Error:**
   - Check browser console (F12)
   - Verify URL is correct
   - Ensure Databricks Files allows embedding

2. **Token Invalid:**
   - Test token with curl:
     ```bash
     curl -H "Authorization: Bearer YOUR_TOKEN" \
       https://adb-WORKSPACE.azuredatabricks.net/api/2.0/workspace/list
     ```
   - If 401 error, regenerate token

3. **File Not Found:**
   - Verify file uploaded to correct path
   - Check: `https://adb-WORKSPACE.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html`

### Issue: Chat Shows "Demo Mode"

**Cause:** Token or workspace ID not set correctly

**Solution:**
1. Check session properties in Perspective
2. Verify token is not empty string
3. Check browser network tab for API calls
4. Look for 401/403 errors

### Issue: Responses Are Slow

**Cause:** Genie API latency or SQL warehouse cold start

**Solution:**
1. Ensure SQL warehouse is running (not auto-stopped)
2. Optimize Genie Space instructions (workstream 07)
3. Pre-warm warehouse before demo
4. Consider caching frequently asked questions

### Issue: Pre-filled Questions Don't Work

**Cause:** URL encoding or special characters

**Solution:**
1. Use `urlEncode()` function in expression binding
2. Test with simple question first
3. Check browser console for errors
4. Verify `view.custom.pending_question` is set

---

## Security Best Practices

1. **Token Storage:**
   - Never hardcode tokens in scripts
   - Use encrypted session properties
   - Rotate tokens every 90 days
   - Use service account tokens (not personal)

2. **Network Security:**
   - Restrict Databricks workspace to known IPs
   - Use HTTPS only
   - Enable Databricks IP Access Lists
   - Monitor access logs

3. **User Permissions:**
   - Limit Genie Space access to authorized users
   - Use Unity Catalog permissions
   - Audit queries executed by Genie
   - Set row-level security on sensitive tables

4. **Data Privacy:**
   - Review Genie responses for PII
   - Mask sensitive data in Databricks tables
   - Log all AI interactions
   - Implement data retention policies

---

## Performance Optimization

1. **Preload Warehouse:**
   ```python
   # Session startup script
   def configure(self, session):
       # Pre-warm SQL warehouse
       system.util.invokeAsynchronous(warmupWarehouse, [session.custom.workspace_id])
   ```

2. **Cache Common Questions:**
   - Store frequently asked questions and responses
   - Return cached response if question matches
   - Refresh cache daily

3. **Lazy Load Chat:**
   - Don't load iframe until user clicks "Ask AI"
   - Use `visible` property to control loading

4. **Connection Pooling:**
   - Reuse conversation ID across multiple questions
   - Only start new conversation when session expires

---

## Deployment Checklist

- [ ] HTML file uploaded to Databricks Files
- [ ] Genie Space configured and tested (workstream 07)
- [ ] Session properties added to Perspective
- [ ] Token stored securely (encrypted)
- [ ] Chat view created
- [ ] Alarm integration tested
- [ ] Equipment integration tested
- [ ] Standalone HTML tested
- [ ] Embedded iframe tested
- [ ] Pre-filled questions tested
- [ ] Error handling verified
- [ ] Performance acceptable (<3s responses)
- [ ] Security review completed
- [ ] User training materials prepared

---

## Support & Maintenance

### Monitoring

1. **Track Usage:**
   - Log all Genie API calls
   - Monitor response times
   - Track error rates
   - Measure user satisfaction

2. **Alert on Issues:**
   - API failures > 5%
   - Response time > 10s
   - Token expiration warnings
   - SQL warehouse downtime

### Updates

1. **HTML File Updates:**
   - Version files (e.g., `genie_chat_v1.2.html`)
   - Test in dev before production
   - Update URL in Perspective views
   - Clear browser cache

2. **Genie Space Updates:**
   - Refine instructions based on usage patterns
   - Add new data sources
   - Optimize SQL queries
   - Update demo responses

---

## Example Usage Scenarios

### Scenario 1: Investigating High Vibration Alarm

**User Action:** Clicks "Ask AI" on vibration alarm for Crusher 2

**Pre-filled Question:**
```
Why did alarm 'High Vibration' trigger at 2025-02-14 14:23:00?
Equipment: CRUSHER_02, Value: 42.3mm/s
```

**Expected Response:**
```
Crusher 2 vibration increased to 42.3mm/s at 14:23 (2.1x normal baseline).
Pattern matches belt misalignment from Jan 15 incident (87% confidence).
Recommend immediate belt inspection.
```

**Follow-up Questions (Auto-suggested):**
- Show Jan 15 incident details
- Compare to other crushers
- What maintenance is recommended?

### Scenario 2: Production Analysis

**User Action:** Types question in chat

**Question:**
```
Show me production for the last 24 hours
```

**Expected Response:**
```
Last 24 hours production summary: 2,847 tonnes processed (94% of target).
Peak throughput at 08:00-12:00 (142 t/h).
Downtime: 37 minutes due to Conveyor 3 jam.

[Data Table with hourly breakdown]
[SQL Query displayed]
```

**Follow-up Questions:**
- Show trend graph
- What caused the jam?
- Compare to yesterday

### Scenario 3: Maintenance Planning

**User Action:** Clicks equipment detail button

**Pre-filled Question:**
```
What is the current status of Crusher 2 (ID: CRUSHER_02)? Current alarms: 3
```

**Expected Response:**
```
Crusher 2 Status:
- Operational: 87.2% uptime this week
- Active Alarms: 3 (High Vibration, Belt Temperature, Low Lubrication)
- Maintenance Due: Belt alignment (overdue 2 days)
- Predicted Failure: 12% risk within 7 days if not serviced
```

---

## API Reference

### Databricks Genie API Endpoints

**Start Conversation:**
```
POST /api/2.0/genie/spaces/{space_id}/start-conversation
Authorization: Bearer {token}

Response:
{
  "conversation_id": "01abc123-4567-89de-f012-3456789abcde"
}
```

**Send Message:**
```
POST /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "content": "Why is Crusher 2 vibrating?"
}

Response:
{
  "message_id": "msg_123",
  "attachments": [
    {
      "text": {
        "content": "Crusher 2 vibration increased..."
      },
      "query": {
        "query": "SELECT ...",
        "result": {
          "data_array": [...]
        }
      }
    }
  ]
}
```

**Get Conversation History:**
```
GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}
Authorization: Bearer {token}

Response:
{
  "conversation_id": "...",
  "messages": [...]
}
```

---

## Additional Resources

- **Databricks Genie Documentation:** https://docs.databricks.com/genie/
- **Ignition Perspective Guide:** https://docs.inductiveautomation.com/display/DOC81/Perspective
- **Demo Video:** (Record after deployment)
- **Training Materials:** (Create after deployment)

---

**Last Updated:** 2025-02-14
**Version:** 1.0
**Author:** Pravin Varma
**Project:** Mining Operations Genie Demo
