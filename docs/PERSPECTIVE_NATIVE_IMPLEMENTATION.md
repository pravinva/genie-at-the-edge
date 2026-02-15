# Perspective-Native Genie Implementation

**No External Proxy Required!**

This implementation runs the Genie API integration **entirely inside Ignition Gateway** using Perspective's native message handling. No external Python process needed.

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    IGNITION GATEWAY                           │
│                                                               │
│  ┌──────────────────┐         ┌───────────────────────────┐ │
│  │  Perspective     │         │  Gateway Script           │ │
│  │  View            │────────▶│  (genie_api module)       │ │
│  │                  │ message │                           │ │
│  │  • Chat UI       │ handler │  • Token caching          │ │
│  │  • User input    │         │  • Response caching       │ │
│  │  • Chart display │◀────────│  • Genie API calls        │ │
│  └──────────────────┘         │  • Async polling          │ │
│                                └───────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                                        ↓ HTTPS
                          ┌──────────────────────────┐
                          │  Databricks Genie API   │
                          └──────────────────────────┘
```

**Benefits:**
- No external processes to manage
- No CORS issues (server-side communication)
- Same lifecycle as Ignition
- All configuration in Designer
- Native Perspective integration
- No additional ports to open

## Implementation Steps

### Step 1: Add Gateway Script Module

1. **Open Ignition Designer**

2. **Create New Script Module:**
   - Project Browser → Scripts
   - Right-click → New Script Module
   - Name: `genie_api`
   - Location: Project Library

3. **Paste Script Content:**
   - Copy entire contents of `ignition/scripts/genie_gateway_script.py`
   - Paste into the `genie_api` module
   - Update configuration (lines 15-16):
     ```python
     WORKSPACE_URL = "https://your-workspace.cloud.databricks.com"
     SPACE_ID = "your_genie_space_id"
     ```

4. **Save Script Module**

### Step 2: Create Perspective View Components

#### Root Container Setup

1. **Create New Perspective View:**
   - Name: `genie_chat_native`
   - Path: `Views/genie_chat_native`

2. **Configure Root Container:**
   ```json
   {
     "position": {
       "width": "100%",
       "height": "100%"
     },
     "style": {
       "backgroundColor": "#e8e8e8"
     }
   }
   ```

#### Custom Properties

Add these custom properties to the view:

| Property | Type | Default Value | Description |
|----------|------|---------------|-------------|
| `messages` | array | `[]` | Chat message history |
| `inputValue` | string | `""` | Current input text |
| `isLoading` | boolean | `false` | Loading state |
| `conversationId` | string | `null` | Genie conversation ID |
| `suggestedQuestions` | array | `["What is the current status?", "Show me trends"]` | Suggested questions |
| `error` | string | `null` | Error message if any |

### Step 3: Add UI Components

#### Chat Messages Container

1. **Add Flex Container:**
   - Name: `messagesContainer`
   - Position: Top 0px, Height: `calc(100% - 150px)`, Width: 100%
   - Flex Direction: `column`
   - Overflow: `auto`

2. **Add Flex Repeater:**
   - Binding: `{view.custom.messages}`
   - Path: `Views/Components/ChatMessage`

#### Message Component (`Views/Components/ChatMessage`)

Create a separate view for message display:

**Custom Properties:**
- `messageType`: string ('user' or 'ai')
- `messageText`: string
- `messageTime`: string
- `chartData`: object (optional)

**Layout:**
```
┌────────────────────────────────┐
│  [Avatar] Message text         │
│           [Chart if present]   │
│           [Timestamp]          │
└────────────────────────────────┘
```

**Markdown Rendering Script:**
```python
# Transform → Expression
# Property: props.text (HTML display)

import re

def markdownToHtml(markdown):
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', markdown)
    # Code blocks
    html = re.sub(r'```(.+?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
    # Inline code
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    # Lists
    html = re.sub(r'^\* (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    return html

return markdownToHtml(self.custom.messageText)
```

#### Input Container

1. **Add Flex Container:**
   - Name: `inputContainer`
   - Position: Bottom 0px, Height: 100px, Width: 100%
   - Flex Direction: `row`

2. **Add Text Area:**
   - Binding: `{view.custom.inputValue}`
   - Placeholder: "Ask a question..."
   - onKeyPress event:
     ```python
     if event.key == 'Enter' and not event.shiftKey:
         self.custom.sendMessage()
     ```

3. **Add Send Button:**
   - Text: "Send"
   - onClick: `{view.custom.sendMessage}`
   - Enabled: `{view.custom.inputValue} != '' and not {view.custom.isLoading}`

#### Suggested Questions

1. **Add Flex Container:**
   - Position: Below messages, above input
   - Height: 50px

2. **Add Button Repeater:**
   - Binding: `{view.custom.suggestedQuestions}`
   - Each button onClick:
     ```python
     self.view.custom.inputValue = self.custom.questionText
     self.view.custom.sendMessage()
     ```

### Step 4: Add View Scripts

#### sendMessage Method

Create a custom method `sendMessage` on the view:

```python
def sendMessage(self):
    """Send message to Genie via gateway script"""
    if not self.custom.inputValue or self.custom.isLoading:
        return

    question = self.custom.inputValue
    conversation_id = self.custom.conversationId

    # Add user message immediately
    import time
    user_message = {
        'type': 'user',
        'text': question,
        'timestamp': system.date.format(system.date.now(), 'HH:mm:ss')
    }
    self.custom.messages = self.custom.messages + [user_message]

    # Clear input and set loading
    self.custom.inputValue = ''
    self.custom.isLoading = True
    self.custom.error = None

    # Call gateway script asynchronously
    def queryAsync():
        try:
            # Import the gateway script module
            result = shared.genie_api.queryGenie(question, conversation_id)
            return result
        except Exception as e:
            return {
                'success': False,
                'response': 'Error: ' + str(e),
                'conversationId': conversation_id,
                'suggestedQuestions': [],
                'chartData': None
            }

    # Execute async
    def callback(result):
        # Add AI response
        ai_message = {
            'type': 'ai',
            'text': result['response'],
            'timestamp': system.date.format(system.date.now(), 'HH:mm:ss'),
            'chartData': result.get('chartData')
        }
        self.custom.messages = self.custom.messages + [ai_message]

        # Update conversation ID
        if result.get('conversationId'):
            self.custom.conversationId = result['conversationId']

        # Update suggested questions
        if result.get('suggestedQuestions'):
            self.custom.suggestedQuestions = result['suggestedQuestions']

        # Clear loading
        self.custom.isLoading = False

        # Show error if failed
        if not result.get('success'):
            self.custom.error = result['response']

    # Run async with callback
    system.util.invokeAsynchronous(queryAsync, [], callback)
```

Bind this method to a custom method in the view:
- Right-click view in Project Browser
- Configure → Custom Methods
- Add method: `sendMessage`
- Paste script above

#### clearChat Method

```python
def clearChat(self):
    """Clear conversation history"""
    self.custom.messages = []
    self.custom.conversationId = None
    self.custom.suggestedQuestions = [
        "What is the current status?",
        "Show me recent trends",
        "Which systems have alerts?"
    ]
    self.custom.error = None
```

### Step 5: Test the Implementation

1. **Open Script Console:**
   - Tools → Script Console

2. **Test Gateway Script:**
   ```python
   # Import the module
   import shared.genie_api as genie

   # Test query
   result = genie.queryGenie("What is the current status?")

   print "Success:", result['success']
   print "Response:", result['response'][:100]
   print "Conversation ID:", result['conversationId']
   ```

3. **Launch Perspective Session:**
   - Navigate to your `genie_chat_native` view
   - Try asking questions
   - Verify responses appear
   - Test suggested questions

### Step 6: Add to Page Configuration

1. **Open Page Configuration:**
   - Project → Perspective → Page Configuration

2. **Add New Route:**
   - Route: `/genie-native`
   - Title: `AI Assistant (Native)`
   - Default View: `genie_chat_native`

3. **Test URL:**
   - `http://gateway:8088/data/perspective/client/your-project/genie-native`

## Deployment

### For Docker

The gateway script runs automatically when Ignition starts. No external processes needed!

### For Production

1. Deploy project to gateway (includes gateway scripts automatically)
2. No external proxy to install
3. No systemd/NSSM service configuration
4. No firewall port openings

### Backup

Gateway scripts are part of the project, so standard project backups include everything.

## Advantages Over External Proxy

| Aspect | External Proxy | Perspective Native |
|--------|---------------|-------------------|
| **Processes** | 2 (Ignition + Proxy) | 1 (Ignition only) |
| **Ports** | 2 (8088 + 8185) | 1 (8088 only) |
| **CORS Issues** | Yes, handled by proxy | No, server-side only |
| **Deployment** | Proxy + Ignition | Ignition only |
| **Backup** | Project + proxy script | Project only |
| **Monitoring** | 2 processes | 1 process |
| **Authentication** | Proxy manages tokens | Gateway script manages |
| **Caching** | Proxy cache | Gateway script cache |
| **Latency** | Browser → Proxy → Databricks | Browser → Gateway → Databricks (same) |
| **Updates** | Update proxy + restart | Update script in Designer |

## Performance

Same performance as external proxy:
- Token caching (50 minutes)
- Response caching (5 minutes)
- Fast polling (500ms)
- 280x speedup for cached queries

## Troubleshooting

### Issue: "Module 'shared.genie_api' not found"

**Solution:** Gateway script not deployed or named incorrectly
1. Check Project Browser → Scripts → genie_api exists
2. Verify script is saved
3. Try gateway restart (Config → System → Gateway Control → Restart)

### Issue: "Failed to get Databricks token"

**Solution:** Databricks CLI not configured in gateway environment
1. SSH/RDP to gateway server
2. Install databricks CLI: `pip install databricks-cli`
3. Configure: `databricks configure --host https://your-workspace.cloud.databricks.com`
4. Test: `databricks auth token --host https://your-workspace.cloud.databricks.com`

### Issue: Async callback not firing

**Solution:** Check gateway logs
1. Gateway → Status → Logs → Wrapper
2. Look for exceptions in `genie_api` logger
3. Verify Python syntax (Jython 2.7 compatible)

### Issue: Slow responses

**Solution:** Same as external proxy - warehouse cold start
- Use Serverless SQL warehouse
- Or keep Classic warehouse always-on

## Jython Compatibility Notes

Ignition uses **Jython 2.7** for gateway scripts. Some Python 3 features are not available:

**Not Available:**
- `f-strings`: Use `.format()` instead
- `async/await`: Use `system.util.invokeAsynchronous()` instead
- `typing` module: Skip type hints
- `pathlib`: Use string paths

**Available:**
- `system.net.httpGet/Post`: For API calls
- `system.util.execute`: For CLI commands
- `system.util.jsonEncode/Decode`: For JSON
- `system.util.invokeAsynchronous`: For async execution
- `time.sleep()`: For polling
- Module-level variables: For caching

## Migration from External Proxy

To migrate an existing installation:

1. **Add gateway script** as described above
2. **Update Perspective view** to use `sendMessage` method
3. **Remove old HTML file** from webserver (optional)
4. **Stop external proxy** process
5. **Remove systemd/NSSM service** (if configured)
6. **Close firewall port 8185** (if opened)
7. **Test end-to-end** with new implementation

Both implementations can coexist during migration.

## FAQ

**Q: Can I use this without Perspective?**
A: Yes! You can call `shared.genie_api.queryGenie()` from Vision, Transaction Groups, or any gateway script.

**Q: Does this work with Vision?**
A: Yes, but you'll need to use polling or timers instead of Perspective's reactive bindings.

**Q: What about scaling?**
A: Gateway scripts run in-process, so they scale with your gateway. For high concurrency, external proxy with load balancer may be better.

**Q: Can I use a PAT token instead of CLI OAuth?**
A: Yes! Modify `_get_databricks_token()` to return your PAT:
```python
def _get_databricks_token():
    return "dapi1234567890abcdef"  # Your PAT
```

**Q: How do I enable debug logging?**
A: Gateway → Config → Logging → Add logger: `genie_api` → Level: DEBUG

## Example: Full View JSON Export

See `ignition/views/genie_chat_native.json` for a complete example view that can be imported directly into your project.

## Support

For issues with Perspective-native implementation:
1. Check gateway logs for Python exceptions
2. Test gateway script directly in Script Console
3. Verify databricks CLI works from gateway terminal
4. Review Jython 2.7 compatibility if using advanced Python features

---

**Created:** February 15, 2026
**Ignition Version:** 8.1+
**Requires:** Perspective Module, Python/Jython 2.7
