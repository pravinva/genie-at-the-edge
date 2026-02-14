# Genie Chat UI Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Genie Chat UI to Databricks and integrating it with Ignition Perspective.

**Estimated Time:** 30-45 minutes

**Prerequisites:**
- Databricks workspace access (admin or contributor)
- Genie Space created (workstream 07 completed)
- Databricks CLI installed (optional but recommended)
- Ignition Gateway with Perspective module

---

## Phase 1: Databricks Deployment

### Step 1: Verify Prerequisites

**1.1 Verify Genie Space Exists**

```bash
# Using Databricks CLI
databricks genie spaces list

# Or via API
curl -X GET \
  https://adb-{workspace_id}.azuredatabricks.net/api/2.0/genie/spaces \
  -H "Authorization: Bearer {token}"
```

Expected output: You should see your Genie Space ID from workstream 07.

**1.2 Verify SQL Warehouse is Running**

```bash
databricks warehouses list --output json

# Check if warehouse is RUNNING
databricks warehouses get {warehouse_id}
```

If warehouse is STOPPED, start it:

```bash
databricks warehouses start {warehouse_id}
```

**1.3 Create Personal Access Token (if not done)**

1. Go to Databricks workspace
2. Click user icon (top right) → **Settings**
3. Navigate to **Developer** → **Access Tokens**
4. Click **Generate New Token**
5. Set comment: "Genie Chat UI - Mining Demo"
6. Set lifetime: 90 days
7. Click **Generate**
8. **COPY TOKEN IMMEDIATELY** (won't be shown again)

---

### Step 2: Upload HTML File to Databricks Files

**Method A: Using Databricks UI (Easiest)**

1. Open Databricks workspace
2. Navigate to **Data** (left sidebar)
3. Click **Create Table** → **Upload File**
4. Select `genie_chat_perspective.html`
5. Upload to: `/FileStore/mining-demo/`
6. Click **Upload**

**Verify:** Navigate to `https://adb-{workspace_id}.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html`

**Method B: Using Databricks CLI (Recommended for automation)**

```bash
# Ensure you're in the ui/ directory
cd /Users/pravin.varma/Documents/Demo/genie-at-the-edge/ui

# Upload file
databricks fs cp genie_chat_perspective.html dbfs:/FileStore/mining-demo/genie_chat_perspective.html --overwrite

# Verify upload
databricks fs ls dbfs:/FileStore/mining-demo/

# Test access
curl https://adb-{workspace_id}.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html
```

**Method C: Using REST API**

```bash
# Base64 encode the file
base64 genie_chat_perspective.html > genie_chat_base64.txt

# Upload via API
curl -X POST \
  https://adb-{workspace_id}.azuredatabricks.net/api/2.0/dbfs/put \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d "{
    \"path\": \"/FileStore/mining-demo/genie_chat_perspective.html\",
    \"contents\": \"$(cat genie_chat_base64.txt)\",
    \"overwrite\": true
  }"
```

---

### Step 3: Test Standalone Access

**3.1 Construct Test URL**

```
https://adb-{workspace_id}.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html?token={token}&workspace={workspace_id}&space={space_id}
```

**Example:**
```
https://adb-1234567890123456.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html?token=dapi1234567890abcdef&workspace=1234567890123456&space=01abc123-4567-89de-f012-3456789abcde
```

**3.2 Open URL in Browser**

Expected results:
-  Chat UI loads with dark theme
-  Header shows "Online" status (green indicator)
-  Welcome message with 4 suggested questions
-  Input field active and ready

**3.3 Test Functionality**

1. Type: "Why is Crusher 2 vibrating?"
2. Press Enter
3. Observe:
   - User message appears (blue bubble, right-aligned)
   - Typing indicator appears (3 dots)
   - AI response appears within 3-5 seconds
   - Suggested follow-up questions appear below

**3.4 Check Browser Console (F12)**

Expected: No errors

Common issues:
- `401 Unauthorized`: Token invalid or expired
- `404 Not Found`: Space ID incorrect or doesn't exist
- `CORS error`: Databricks Files not accessible (check network settings)

---

### Step 4: Test with Pre-filled Question

**4.1 Test URL Parameter**

```
https://adb-{workspace_id}.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html?token={token}&workspace={workspace_id}&space={space_id}&question=Show%20me%20production%20for%20the%20last%2024%20hours
```

Expected:
-  Question appears in input field
-  Can edit or send as-is

---

## Phase 2: Ignition Perspective Integration

### Step 5: Configure Session Properties

**5.1 Open Ignition Designer**

1. Launch Ignition Designer
2. Open your Perspective project

**5.2 Add Session Properties**

1. Navigate to **Project Browser** → **Perspective** → **Session Events**
2. Right-click **Session Events** → **Configure Events**
3. Add `startup` event:

```python
# Session startup event
def startup(self, session):
    """
    Initialize Databricks connection parameters
    """
    import system

    # REPLACE THESE VALUES WITH YOUR ACTUAL VALUES
    session.custom.databricks_workspace_id = "1234567890123456"
    session.custom.genie_space_id = "01abc123-4567-89de-f012-3456789abcde"

    # Load token from secure storage
    # Option A: From Gateway Tag (encrypted)
    try:
        token_tag = "[default]Configuration/Databricks/Token"
        token = system.tag.readBlocking([token_tag])[0].value
        session.custom.databricks_token = token
        system.perspective.print("Databricks token loaded successfully", session.page.id)
    except:
        system.perspective.print("ERROR: Failed to load Databricks token", session.page.id)
        session.custom.databricks_token = ""

    # Option B: From Database (alternative)
    # try:
    #     result = system.db.runPrepQuery(
    #         "SELECT token FROM config WHERE service='databricks' AND active=1",
    #         database="ConfigDB"
    #     )
    #     session.custom.databricks_token = result[0]['token']
    # except:
    #     system.perspective.print("ERROR: Failed to load token from database")
    #     session.custom.databricks_token = ""

    # For testing only (REMOVE IN PRODUCTION)
    # session.custom.databricks_token = "dapi1234567890abcdef..."
```

**5.3 Create Gateway Tag for Token (Option A)**

1. Navigate to **Tag Browser**
2. Create folder: `Configuration/Databricks`
3. Create tag:
   - Name: `Token`
   - Type: `String`
   - Value: (paste your Databricks token)
   - History: Disabled
   - Security: Encrypted (check box)

---

### Step 6: Create Chat View

**6.1 Create New View**

1. Right-click **Views** → **New View**
2. Name: `MiningOperations/GenieChat`
3. Root container: Flex Container
   - Direction: `column`
   - Height: `100%`
   - Width: `500px`

**6.2 Add Embedded Frame Component**

1. Drag **Embedded Frame** onto view
2. Set properties:
   ```json
   {
     "style": {
       "width": "100%",
       "height": "100%",
       "border": "none",
       "background": "#1a1d23"
     }
   }
   ```

**6.3 Bind URL Property**

1. Select Embedded Frame
2. Right-click `props.url` → **Add Binding** → **Expression**
3. Expression:

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

4. Click **Commit**

**6.4 Add Custom View Properties**

1. Right-click view root → **Customizers** → **Custom Properties**
2. Add property:
   - Name: `pending_question`
   - Type: `String`
   - Default: `""`
3. Add property:
   - Name: `visible`
   - Type: `Boolean`
   - Default: `false`

**6.5 Save View**

Press `Ctrl+S` (or `Cmd+S` on Mac)

---

### Step 7: Test in Session

**7.1 Launch Session**

1. Click **Tools** → **Launch Perspective Session**
2. Or click **Preview** button (top right)

**7.2 Navigate to Chat View**

1. Manually navigate to: `MiningOperations/GenieChat`
2. Expected: Chat UI loads within iframe

**7.3 Verify Functionality**

-  Chat loads without errors
-  Dark theme matches Perspective
-  Can type and send messages
-  Responses appear
-  No layout issues or scrollbars

**7.4 Check Output Console**

1. In Designer: **Tools** → **Console**
2. Look for: "Databricks token loaded successfully"
3. If errors, check session properties and token

---

### Step 8: Add to Main Page

**8.1 Option A: Docked Right Panel (Recommended)**

Add to your main page template:

```xml
<!-- In your main page view -->
<Container>
  <!-- Existing content -->
  <FlexContainer direction="row" style:height="100%">
    <!-- Main content area -->
    <FlexContainer flex="1">
      <!-- Your existing views -->
    </FlexContainer>

    <!-- Chat panel (collapsible) -->
    <FlexContainer
      style:width="500px"
      style:height="100%"
      custom:collapsed="{page.custom.chat_collapsed}"
      style:transform="if({page.custom.chat_collapsed}, 'translateX(500px)', 'translateX(0)')"
      style:transition="transform 300ms ease"
    >
      <EmbeddedView path="MiningOperations/GenieChat" />
    </FlexContainer>
  </FlexContainer>

  <!-- Chat toggle button -->
  <Button
    text="AI Assistant"
    style:position="fixed"
    style:right="0"
    style:top="50%"
    onClick="self.page.custom.chat_collapsed = not self.page.custom.chat_collapsed"
  />
</Container>
```

**8.2 Option B: Popup Modal**

Add button to header/toolbar:

```python
# Button onClick script
def runAction(self, event):
    """Open chat as popup"""
    import system

    system.perspective.openPopup(
        id='genieChat',
        view='MiningOperations/GenieChat',
        params={},
        position={
            'right': 0,
            'top': 0,
            'bottom': 0,
            'width': 500
        },
        modal=False,
        draggable=False,
        resizable=True,
        showCloseIcon=True
    )
```

---

## Phase 3: Alarm Integration

### Step 9: Add "Ask AI" to Alarms

**9.1 Locate Alarm Table Component**

Find your existing alarm table view (e.g., `Alarms/AlarmTable`)

**9.2 Add Button Column**

1. Add new column to alarm table
2. Type: `Button`
3. Text: "Ask AI"
4. Style:
   ```json
   {
     "background": "#0084ff",
     "color": "white",
     "padding": "6px 12px",
     "borderRadius": "4px"
   }
   ```

**9.3 Configure Button Script**

```python
def runAction(self, event):
    """
    Send alarm info to Genie Chat
    """
    import system

    # Get alarm details from table row
    row_data = self.parent.custom.row_data

    alarm_name = row_data['alarm_name']
    alarm_time = row_data['alarm_time']
    equipment_id = row_data['equipment_id']
    alarm_value = row_data['current_value']
    alarm_setpoint = row_data['setpoint']

    # Format question
    question = "Why did alarm '{}' trigger at {}? Equipment: {}, Value: {} (setpoint: {})".format(
        alarm_name,
        system.date.format(alarm_time, "yyyy-MM-dd HH:mm:ss"),
        equipment_id,
        alarm_value,
        alarm_setpoint
    )

    # Open chat with pre-filled question
    system.perspective.openPopup(
        id='genieChat',
        view='MiningOperations/GenieChat',
        params={'pending_question': question},
        position={'right': 0, 'top': 0, 'bottom': 0, 'width': 500},
        modal=False,
        draggable=False,
        resizable=False,
        showCloseIcon=True
    )
```

**9.4 Test Alarm Integration**

1. Launch session
2. Navigate to alarm table
3. Click "Ask AI" on an alarm
4. Verify:
   -  Chat popup opens
   -  Question pre-filled with alarm details
   -  Can send or edit question
   -  Response is relevant

---

## Phase 4: Equipment Integration

### Step 10: Add to Equipment Views

**10.1 Locate Equipment Detail View**

Find equipment detail view (e.g., `Equipment/Detail`)

**10.2 Add "Ask AI Assistant" Button**

1. Add button to view
2. Position: Top-right corner or bottom toolbar
3. Text: " Ask AI Assistant"
4. Style:
   ```json
   {
     "background": "linear-gradient(135deg, #0084ff 0%, #0073e6 100%)",
     "color": "white",
     "padding": "10px 20px",
     "borderRadius": "8px",
     "fontWeight": "600"
   }
   ```

**10.3 Configure Button Script**

```python
def runAction(self, event):
    """
    Open chat with equipment-specific question
    """
    import system

    # Get equipment details from view params
    equipment_name = self.view.params.equipment_name
    equipment_id = self.view.params.equipment_id

    # Get current status from view components
    try:
        status_label = self.getSibling("StatusLabel")
        current_status = status_label.props.text
    except:
        current_status = "Unknown"

    try:
        alarm_count_label = self.getSibling("AlarmCountLabel")
        current_alarm_count = alarm_count_label.props.text
    except:
        current_alarm_count = "0"

    # Format question
    question = "What is the current status of {} (ID: {})? Current status: {}, Active alarms: {}".format(
        equipment_name,
        equipment_id,
        current_status,
        current_alarm_count
    )

    # Open chat
    system.perspective.openPopup(
        id='genieChat',
        view='MiningOperations/GenieChat',
        params={'pending_question': question},
        position={'right': 0, 'top': 0, 'bottom': 0, 'width': 500},
        modal=False
    )
```

**10.4 Test Equipment Integration**

1. Launch session
2. Navigate to equipment detail view
3. Click "Ask AI Assistant"
4. Verify chat opens with equipment question

---

## Phase 5: Validation & Testing

### Step 11: Comprehensive Testing

**11.1 Functionality Tests**

| Test | Expected Result | Status |
|------|----------------|--------|
| Chat loads standalone | UI renders correctly |  |
| Chat loads in iframe | No errors, proper styling |  |
| Send simple question | Response within 5 seconds |  |
| Send complex question | Detailed response with data |  |
| Pre-filled question works | Question appears in input |  |
| Suggested questions clickable | Question sent when clicked |  |
| Clear chat button works | Conversation resets |  |
| Alarm integration | Opens with alarm details |  |
| Equipment integration | Opens with equipment details |  |
| SQL query displays | Properly formatted with syntax highlighting |  |
| Data table displays | Properly formatted and scrollable |  |
| Copy SQL button works | SQL copied to clipboard |  |

**11.2 Error Handling Tests**

| Test | Expected Result | Status |
|------|----------------|--------|
| Invalid token | Shows "Authentication expired" error |  |
| Network disconnected | Shows retry option |  |
| Genie Space deleted | Shows connection error |  |
| SQL warehouse stopped | Graceful error message |  |
| Invalid question | Genie handles gracefully |  |

**11.3 Performance Tests**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Initial load time | <2 seconds | _____ |  |
| First message response | <5 seconds | _____ |  |
| Subsequent responses | <3 seconds | _____ |  |
| Scrolling framerate | 60 FPS | _____ |  |
| Memory usage (30 min) | <100 MB | _____ |  |

**11.4 Cross-Browser Tests**

Test in these browsers:

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

**11.5 Responsive Design Tests**

Test at these widths:

- [ ] 400px (narrow mobile)
- [ ] 500px (Perspective right panel)
- [ ] 800px (tablet)
- [ ] 1920px (desktop)

---

## Phase 6: Production Deployment

### Step 12: Security Hardening

**12.1 Token Rotation**

1. Generate production token with 90-day expiration
2. Store in encrypted Gateway tag or database
3. Set calendar reminder for rotation (75 days)
4. Document rotation procedure

**12.2 IP Access Lists (Optional but Recommended)**

1. In Databricks: **Settings** → **Network**
2. Click **IP Access Lists**
3. Add your Ignition Gateway IPs
4. Click **Save**

**12.3 Audit Logging**

Add logging to session startup script:

```python
def startup(self, session):
    import system

    # ... existing code ...

    # Log session start
    system.db.runPrepUpdate(
        "INSERT INTO chat_session_log (session_id, user_id, timestamp, workspace_id) VALUES (?, ?, ?, ?)",
        [session.props.id, session.props.user.username, system.date.now(), session.custom.databricks_workspace_id],
        database="AuditDB"
    )
```

**12.4 Rate Limiting**

Add to prevent abuse:

```python
# In button onClick scripts
def runAction(self, event):
    import system

    # Check rate limit
    last_request_time = self.session.custom.get('last_genie_request', 0)
    current_time = system.date.toMillis(system.date.now())

    if (current_time - last_request_time) < 2000:  # 2 second cooldown
        system.perspective.print("Rate limit: Please wait before sending another message")
        return

    self.session.custom.last_genie_request = current_time

    # ... continue with existing code ...
```

---

### Step 13: Monitoring & Alerts

**13.1 Create Monitoring Dashboard**

Track these metrics:

1. **Usage Metrics:**
   - Questions asked per day
   - Average response time
   - Most common questions
   - Active users

2. **Error Metrics:**
   - API failure rate
   - Token expiration events
   - Network timeouts
   - Invalid questions

3. **Performance Metrics:**
   - Genie API latency (p50, p95, p99)
   - SQL warehouse utilization
   - Conversation duration

**13.2 Set Up Alerts**

Configure alerts for:

- API failure rate > 10%
- Average response time > 10 seconds
- Token expiring in <7 days
- SQL warehouse offline

**Example Alert Script:**

```python
# Tag change script on error rate tag
def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
    import system

    if currentValue.value > 0.10:  # 10% error rate
        # Send alert email
        system.net.sendEmail(
            smtp="smtp.company.com",
            fromAddr="alerts@company.com",
            subject="Genie Chat Alert: High Error Rate",
            body="Error rate: {}%".format(currentValue.value * 100),
            to=["admin@company.com"]
        )
```

---

### Step 14: User Training

**14.1 Create Quick Reference Guide**

Document:

1. **How to Ask Questions:**
   - Use natural language
   - Be specific (include equipment names, time ranges)
   - Examples of good questions

2. **Understanding Responses:**
   - Text explanations
   - Data tables
   - SQL queries (what they mean)

3. **Common Questions:**
   - Equipment status
   - Production metrics
   - Alarm investigation
   - Maintenance scheduling

**14.2 Record Demo Video**

Create 5-minute video showing:

1. Opening chat from alarm
2. Asking follow-up questions
3. Interpreting responses
4. Using suggested questions

**14.3 Conduct Training Session**

1. Schedule 30-minute session with operators
2. Live demo of all features
3. Q&A session
4. Collect feedback

---

### Step 15: Documentation & Handoff

**15.1 Update Project Documentation**

Document these in your project wiki/docs:

1. **Architecture Diagram:**
   ```
   Ignition Perspective → Databricks Files (HTML) → Genie API → Lakehouse Data
   ```

2. **Configuration Details:**
   - Databricks workspace ID
   - Genie Space ID
   - Token location (tag path or DB table)
   - HTML file location

3. **Troubleshooting Guide:**
   - Common issues and solutions
   - Support contact information

**15.2 Create Runbook**

Include procedures for:

- Token rotation
- HTML file updates
- Genie Space configuration changes
- Emergency troubleshooting

**15.3 Handoff Checklist**

- [ ] Documentation complete
- [ ] Training conducted
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Credentials secured
- [ ] Backup/DR plan documented
- [ ] Support contacts listed
- [ ] Runbook reviewed

---

## Troubleshooting Guide

### Issue: Chat Won't Load in Iframe

**Symptoms:**
- Blank iframe
- "Failed to load resource" error in console

**Diagnosis:**

```javascript
// Check browser console (F12)
// Look for errors like:
// - CORS policy blocked
// - 404 Not Found
// - 401 Unauthorized
```

**Solutions:**

1. **Verify HTML file exists:**
   ```bash
   curl https://adb-{workspace}.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html
   ```

2. **Check session properties:**
   - Open Designer Console: `Tools` → `Console`
   - Look for "Databricks token loaded" message
   - Verify workspace ID and space ID are set

3. **Test standalone access:**
   - Copy iframe URL from Designer
   - Open in browser
   - Check if it loads outside Perspective

---

### Issue: Responses Are Slow (>10 seconds)

**Diagnosis:**

Check SQL warehouse status:

```bash
databricks warehouses get {warehouse_id}
```

**Solutions:**

1. **Warehouse cold start:** Start warehouse before demo
2. **Optimize Genie instructions:** Simplify queries in Genie Space
3. **Increase warehouse size:** Use Medium instead of Small
4. **Enable serverless:** Faster cold starts

---

### Issue: Invalid or Irrelevant Responses

**Diagnosis:**

- Questions don't match available data
- Genie Space instructions unclear
- Data schema not optimized

**Solutions:**

1. **Refine Genie Space instructions** (see workstream 07)
2. **Add more context to questions:**
   ```python
   # Instead of: "Show production"
   # Use: "Show production tonnage for Crusher 2 in the last 24 hours"
   ```
3. **Review Unity Catalog permissions:** Ensure Genie can access necessary tables

---

### Issue: Token Expired

**Symptoms:**
- "Authentication expired" error
- 401 Unauthorized in console

**Solutions:**

1. **Generate new token:**
   - Databricks → Settings → Access Tokens
   - Generate new token
   - Update Gateway tag or database

2. **Update session property:**
   ```python
   # In Designer Console
   session.custom.databricks_token = "NEW_TOKEN_HERE"
   ```

3. **Restart session** for changes to take effect

---

## Maintenance Schedule

### Daily
- Monitor error rates
- Check SQL warehouse status
- Review usage metrics

### Weekly
- Review most common questions
- Optimize Genie Space instructions based on usage
- Check performance metrics

### Monthly
- Review audit logs
- Update demo responses if needed
- Train new users

### Quarterly
- Rotate Databricks token (90 days)
- Review and update documentation
- Conduct user feedback session
- Update HTML file if needed

---

## Rollback Plan

If critical issues arise in production:

**Immediate Rollback (5 minutes):**

1. In Ignition Designer, navigate to chat view
2. Set `view.custom.visible = false` in all parent views
3. Or: Delete `EmbeddedFrame` component temporarily

**Disable via Session Property (2 minutes):**

```python
# Add to session startup script
session.custom.genie_chat_enabled = False

# In chat view, add conditional rendering
if session.custom.genie_chat_enabled:
    # Show chat
else:
    # Show "Feature temporarily unavailable" message
```

**Full Rollback (10 minutes):**

1. Remove chat view from all parent views
2. Remove "Ask AI" buttons from alarms/equipment
3. Deploy previous project version

---

## Success Metrics

Track these KPIs after deployment:

### Adoption
- Unique users per week
- Questions asked per day
- % of alarms investigated with AI

### User Satisfaction
- Average session duration
- Repeat usage rate
- Feedback survey scores (NPS)

### Business Value
- Time saved per investigation (vs manual)
- Faster alarm resolution time
- Reduced downtime due to proactive insights

### Technical Performance
- Average response time
- Error rate
- Uptime percentage

---

## Next Steps

After successful deployment:

1. **Expand Data Sources:**
   - Add maintenance logs
   - Add work order history
   - Add shift reports

2. **Enhance Instructions:**
   - Refine Genie Space based on usage patterns
   - Add domain-specific knowledge
   - Improve response templates

3. **Add Features:**
   - Voice input (future enhancement)
   - Multi-language support
   - Export conversation history
   - Share insights with team

4. **Integrate with Other Systems:**
   - Send findings to CMMS
   - Create work orders from chat
   - Log insights to historian

---

## Support Contacts

- **Databricks Support:** support.databricks.com
- **Ignition Support:** support.inductiveautomation.com
- **Project Lead:** Pravin Varma
- **Internal IT Support:** [Your contact info]

---

## Appendix: CLI Commands Reference

### Databricks CLI

```bash
# List Genie Spaces
databricks genie spaces list

# Get Space details
databricks genie spaces get {space_id}

# List SQL Warehouses
databricks warehouses list

# Start warehouse
databricks warehouses start {warehouse_id}

# Stop warehouse
databricks warehouses stop {warehouse_id}

# Upload file to DBFS
databricks fs cp local_file.html dbfs:/FileStore/path/file.html

# List files
databricks fs ls dbfs:/FileStore/mining-demo/

# Download file
databricks fs cp dbfs:/FileStore/mining-demo/file.html local_file.html
```

### Testing with cURL

```bash
# Test Genie API
curl -X POST \
  https://adb-{workspace}.azuredatabricks.net/api/2.0/genie/spaces/{space_id}/start-conversation \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"

# Send message
curl -X POST \
  https://adb-{workspace}.azuredatabricks.net/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"content": "Show me Crusher 2 status"}'
```

---

**Deployment Guide Version:** 1.0
**Last Updated:** 2025-02-14
**Author:** Pravin Varma
**Status:** Production Ready
