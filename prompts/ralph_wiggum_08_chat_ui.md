# RALPH WIGGUM WORKSTREAM - FILE 08
## Genie Chat UI - Perspective Dark Theme Styling

**Purpose:** Professional chat interface matching Ignition Perspective design language
**Format:** Single HTML file with embedded React, CSS, JavaScript
**Host:** Databricks Workspace Files or Repos
**Dependencies:** File 07 (Genie space must exist)

---

## CLAUDE CODE PROMPT

```
Create a production-quality, single-file HTML chat application for mining operations AI assistant.

CRITICAL REQUIREMENTS:

1. SINGLE FILE ARCHITECTURE:
   - All HTML, CSS, JavaScript in ONE file
   - Use React via CDN (no build process)
   - Use Chart.js via CDN (for data visualization)
   - No external dependencies except CDN libraries
   - File size target: <100KB
   - Works offline-first (CDN failover to local fallback)

2. EXACT PERSPECTIVE DARK THEME COLORS:

```css
/* Copy these EXACT color values */
:root {
  /* Backgrounds - Match Perspective precisely */
  --bg-primary: #1a1d23;      /* Main background */
  --bg-secondary: #242830;    /* Panel background */
  --bg-tertiary: #2a2e38;     /* Input/button background */
  --bg-hover: #343841;        /* Hover states */
  
  /* Ignition/Databricks Blue Accent */
  --accent-primary: #0084ff;
  --accent-hover: #0073e6;
  --accent-active: #0062cc;
  
  /* Status Colors */
  --success: #00cc66;
  --warning: #ff9500;
  --danger: #ff3b30;
  --info: #0084ff;
  
  /* Text */
  --text-primary: #ffffff;
  --text-secondary: #a0a0a0;
  --text-tertiary: #6b6b6b;
  --text-disabled: #4a4a4a;
  
  /* Borders */
  --border-color: rgba(255,255,255,0.1);
  --border-focus: rgba(0,132,255,0.4);
  
  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.2);
  --shadow-md: 0 2px 8px rgba(0,0,0,0.3);
  --shadow-lg: 0 4px 16px rgba(0,0,0,0.4);
}
```

3. TYPOGRAPHY (Match Perspective):

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap');

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  font-size: 13px;
  line-height: 1.5;
  letter-spacing: -0.01em;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.monospace {
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
}

h1, h2, h3 { font-weight: 600; letter-spacing: -0.02em; }
h1 { font-size: 18px; }
h2 { font-size: 16px; }
h3 { font-size: 14px; }
```

4. LAYOUT (Flex column, fills container):

```html
<div id="app" style="display: flex; flex-direction: column; height: 100vh;">
  
  <!-- Header (48px fixed) -->
  <header class="chat-header">
    <div class="header-left">
      <div class="robot-icon"></div>
      <h1>AI Operations Assistant</h1>
    </div>
    <div class="header-right">
      <div class="status-indicator online"></div>
      <span class="status-text">Online</span>
      <button class="btn-icon" onclick="clearChat()"></button>
    </div>
  </header>
  
  <!-- Messages Area (flex-grow, scrollable) -->
  <div class="messages-container" id="messagesContainer">
    <!-- Messages rendered here -->
  </div>
  
  <!-- Suggested Questions (conditional, 56px when visible) -->
  <div class="suggestions-container" id="suggestionsContainer">
    <!-- Chips rendered here when available -->
  </div>
  
  <!-- Input Area (72px fixed) -->
  <div class="input-container">
    <textarea 
      id="messageInput"
      placeholder="Ask about equipment, production, or maintenance..."
      rows="1"
      maxlength="500"
    ></textarea>
    <button class="btn-send" onclick="handleSend()">
      <span class="send-icon"></span>
    </button>
    <button class="btn-voice" onclick="handleVoice()" disabled title="Voice input coming soon">
      <span class="voice-icon"></span>
    </button>
  </div>
  
</div>
```

5. MESSAGE COMPONENTS:

**User Message:**
```css
.message-user {
  align-self: flex-end;
  max-width: 85%;
  background: linear-gradient(135deg, #0084ff 0%, #0073e6 100%);
  color: white;
  padding: 10px 14px;
  border-radius: 12px 12px 4px 12px;
  margin: 6px 0;
  box-shadow: var(--shadow-sm);
  animation: slideInRight 200ms ease-out;
}
```

**AI Message:**
```css
.message-ai {
  align-self: flex-start;
  max-width: 85%;
  background: var(--bg-secondary);
  color: var(--text-primary);
  padding: 12px 16px;
  border-radius: 12px 12px 12px 4px;
  border-left: 3px solid var(--success);
  margin: 6px 0;
  box-shadow: var(--shadow-sm);
  animation: slideInLeft 200ms ease-out;
}

/* Typing indicator */
.message-ai.typing {
  padding: 16px;
  border-left-color: var(--text-tertiary);
}

.typing-dots {
  display: inline-flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  background: var(--text-secondary);
  border-radius: 50%;
  animation: typingDot 1.4s infinite;
}

.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingDot {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-8px); opacity: 1; }
}
```

**Data Display (if Genie returns tabular data):**
```css
.data-table {
  margin: 12px 0;
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.data-table th {
  background: var(--bg-tertiary);
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid var(--border-color);
}

.data-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
}

.data-table tr:hover {
  background: rgba(255,255,255,0.03);
}
```

**SQL Display (code block with copy button):**
```css
.sql-block {
  background: #16181d;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  margin: 8px 0;
  overflow: hidden;
}

.sql-header {
  display: flex;
  justify-content: space-between;
  padding: 6px 12px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.sql-content {
  padding: 12px;
  font-family: 'Roboto Mono', monospace;
  font-size: 11px;
  overflow-x: auto;
  color: #e6e6e6;
}

/* Simple syntax highlighting */
.keyword { color: #569cd6; }  /* Blue for SELECT, FROM, WHERE */
.string { color: #ce9178; }   /* Orange for strings */
.number { color: #b5cea8; }   /* Green for numbers */
```

6. SUGGESTED QUESTIONS (Chips):

```css
.suggestion-chip {
  display: inline-block;
  padding: 8px 14px;
  margin: 4px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 200ms ease;
}

.suggestion-chip:hover {
  background: var(--bg-hover);
  border-color: var(--accent-primary);
  color: var(--text-primary);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.suggestion-chip:active {
  transform: translateY(0);
}
```

7. DATABRICKS GENIE API INTEGRATION:

```javascript
// Configuration from URL parameters
const urlParams = new URLSearchParams(window.location.search);
const CONFIG = {
  workspace: urlParams.get('workspace') || 'YOUR_WORKSPACE_ID',
  spaceId: urlParams.get('space') || 'YOUR_SPACE_ID',
  token: urlParams.get('token') || localStorage.getItem('db_token'),
  apiBase: `https://adb-${urlParams.get('workspace')}.azuredatabricks.net`
};

let conversationId = null;

async function startConversation() {
  /**
   * Initialize Genie conversation
   * Returns: conversation_id for subsequent messages
   */
  try {
    const response = await fetch(
      `${CONFIG.apiBase}/api/2.0/genie/spaces/${CONFIG.spaceId}/start-conversation`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${CONFIG.token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    conversationId = data.conversation_id;
    return conversationId;
    
  } catch (error) {
    console.error('Error starting conversation:', error);
    showError('Failed to connect to AI assistant. Please check your connection.');
    return null;
  }
}

async function sendMessage(question, context = {}) {
  /**
   * Send message to Genie and get response
   * question: User's natural language question
   * context: Optional metadata (equipment_id, alarm_info, etc.)
   */
  
  // Ensure conversation exists
  if (!conversationId) {
    await startConversation();
  }
  
  try {
    const response = await fetch(
      `${CONFIG.apiBase}/api/2.0/genie/spaces/${CONFIG.spaceId}/conversations/${conversationId}/messages`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${CONFIG.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content: question
          // Context could be added here if Genie API supports it
        })
      }
    );
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return parseGenieResponse(data);
    
  } catch (error) {
    console.error('Error sending message:', error);
    return {
      text: 'Sorry, I encountered an error. Please try again.',
      error: true
    };
  }
}

function parseGenieResponse(response) {
  /**
   * Parse Genie API response into renderable format
   * Handles: text, SQL, data tables, follow-up suggestions
   */
  const result = {
    text: '',
    sql: null,
    data: null,
    suggestions: []
  };
  
  // Extract text from attachments
  if (response.attachments && response.attachments.length > 0) {
    for (const attachment of response.attachments) {
      if (attachment.text && attachment.text.content) {
        result.text += attachment.text.content + '\n';
      }
      
      // Extract SQL if present
      if (attachment.query && attachment.query.query) {
        result.sql = attachment.query.query;
      }
      
      // Extract data if present
      if (attachment.query && attachment.query.result) {
        result.data = attachment.query.result.data_array;
      }
    }
  }
  
  // Generate follow-up suggestions (simple heuristic)
  result.suggestions = generateFollowUps(result.text, response);
  
  return result;
}

function generateFollowUps(responseText, rawResponse) {
  /**
   * Generate relevant follow-up questions
   */
  const suggestions = [];
  
  // If mentions equipment, suggest trend
  if (responseText.includes('Crusher') || responseText.includes('equipment')) {
    suggestions.push('Show me the trend for this equipment');
  }
  
  // If mentions failure or issue, suggest history
  if (responseText.includes('failure') || responseText.includes('issue') || responseText.includes('problem')) {
    suggestions.push('Show similar past incidents');
  }
  
  // If mentions vibration/temperature, suggest comparison
  if (responseText.includes('vibration') || responseText.includes('temperature')) {
    suggestions.push('Compare to other equipment');
  }
  
  // Generic helpful suggestions
  suggestions.push('What caused this?');
  suggestions.push('What should I do?');
  
  return suggestions.slice(0, 4);  // Max 4 suggestions
}
```

8. RESPONSIVE DESIGN (Works 400px to 1920px):

```css
/* Base: Optimized for 500px (Perspective right panel) */
.chat-container {
  width: 100%;
  height: 100%;
}

/* Narrow mode (<450px) */
@media (max-width: 450px) {
  .message-user, .message-ai {
    max-width: 95%;
    font-size: 12px;
  }
  
  .suggestion-chip {
    font-size: 11px;
    padding: 6px 10px;
  }
}

/* Wide mode (>800px) */
@media (min-width: 800px) {
  .messages-container {
    padding: 20px;
  }
  
  .message-user, .message-ai {
    max-width: 75%;
  }
}
```

9. ANIMATIONS (Smooth, professional):

```css
@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* All transitions smooth */
* {
  transition: background-color 200ms ease,
              border-color 200ms ease,
              color 200ms ease,
              transform 200ms ease;
}
```

10. ACCESSIBILITY:

```html
<!-- Proper ARIA labels -->
<button aria-label="Send message" class="btn-send">
<textarea aria-label="Type your question" placeholder="...">
<div role="log" aria-live="polite" aria-atomic="false">
  <!-- Messages appear here, screen reader announces -->
</div>
```

11. ERROR STATES (User-friendly):

```javascript
function showError(message) {
  const errorDiv = `
    <div class="message-error" role="alert">
      <div class="error-icon"></div>
      <div class="error-text">${message}</div>
      <button class="btn-retry" onclick="retryLastMessage()">Retry</button>
    </div>
  `;
  appendMessage(errorDiv);
}

// Network error handling
async function fetchWithRetry(url, options, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) return response;
      if (response.status === 401) {
        showError('Authentication expired. Please refresh the page.');
        throw new Error('Auth error');
      }
      if (response.status === 429) {
        showError('Too many requests. Please wait a moment.');
        await sleep(2000 * (i + 1));  // Exponential backoff
        continue;
      }
    } catch (error) {
      if (i === retries - 1) throw error;
      await sleep(1000 * (i + 1));
    }
  }
}
```

12. SPECIAL FEATURES:

**Auto-scroll to latest message:**
```javascript
function scrollToBottom(smooth = true) {
  const container = document.getElementById('messagesContainer');
  container.scrollTo({
    top: container.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto'
  });
}
```

**Textarea auto-expand:**
```javascript
const textarea = document.getElementById('messageInput');
textarea.addEventListener('input', function() {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 80) + 'px';  // Max 3 lines
});
```

**Keyboard shortcuts:**
```javascript
textarea.addEventListener('keydown', function(e) {
  // Enter to send (Shift+Enter for newline)
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
  
  // Escape to clear input
  if (e.key === 'Escape') {
    this.value = '';
    this.style.height = 'auto';
  }
});
```

**Read pre-filled question from URL:**
```javascript
// On page load
window.addEventListener('DOMContentLoaded', function() {
  const question = urlParams.get('question');
  if (question) {
    const decoded = decodeURIComponent(question);
    document.getElementById('messageInput').value = decoded;
    document.getElementById('messageInput').focus();
    // Optionally auto-send after 500ms
    // setTimeout(() => handleSend(), 500);
  }
});
```

13. TESTING DATA (Embedded for offline demo):

```javascript
// Fallback responses if Databricks unavailable
const DEMO_RESPONSES = {
  'why is crusher 2 vibrating': {
    text: 'Crusher 2 vibration increased to 42.3mm/s at 14:23 (2.1x normal baseline). Pattern matches belt misalignment from Jan 15 incident (87% confidence). Recommend immediate belt inspection.',
    suggestions: ['Show Jan 15 incident details', 'Compare to other crushers']
  },
  // More demo responses...
};
```

FINAL REQUIREMENTS:
- File must be <100KB (no large libraries bundled)
- Works in Chrome, Firefox, Safari, Edge
- No console errors or warnings
- Passes accessibility audit (WCAG 2.1 AA)
- 60 FPS scrolling performance
- Looks indistinguishable from Databricks/Perspective product UI

Generate complete, production-ready HTML file.
Include comprehensive comments explaining each section.
```

---

## HOSTING OPTIONS

**Option A: Databricks Repos (Recommended for development):**

```
1. Create Repo: mining-genie-demo
2. Add file: ui/genie_chat_perspective.html
3. Get URL: 
   https://{workspace}.cloud.databricks.com/?o={workspace_id}#repos/{user}/mining-genie-demo/ui/genie_chat_perspective.html

Note: Repos URLs require authentication
```

**Option B: Databricks Files (Better for embedding):**

```
1. Upload file via UI or CLI:
   databricks fs cp genie_chat_perspective.html dbfs:/FileStore/mining-demo/

2. Access via:
   https://{workspace}.cloud.databricks.com/files/mining-demo/genie_chat_perspective.html

Note: Files are publicly accessible (no auth required)
Security: Token passed as URL parameter
```

**Option C: Databricks Apps (If using):**

```
1. Create Databricks App
2. Serve HTML as static file
3. Get app URL
4. More control over auth/routing
```

**For demo: Use Option B (Files) - simplest**

---

## CONFIGURATION IN IGNITION

**Embed in Perspective:**

```
Component: Embedded Frame
URL Expression:
  concat(
    "https://adb-",
    {session.custom.workspace_id},
    ".azuredatabricks.net/files/mining-demo/genie_chat_perspective.html",
    "?token=", {session.custom.databricks_token},
    "&workspace=", {session.custom.workspace_id},
    "&space=", {session.custom.genie_space_id},
    "&question=", {view.custom.pending_question}
  )
```

---

## VALIDATION

**Standalone testing (before embedding):**

1. **Open in browser directly:**
   ```
   https://your-workspace.cloud.databricks.com/files/.../genie_chat.html?token=XXX&workspace=YYY&space=ZZZ
   ```

2. **Verify UI renders:**
   - Dark theme applied correctly
   - No console errors (F12 developer tools)
   - Layout matches Perspective aesthetic

3. **Test chat functionality:**
   - Type question, press Enter
   - Should show typing indicator
   - Should receive response in 3-5 seconds
   - Response should be formatted nicely

4. **Test suggested questions:**
   - Click a suggestion chip
   - Should auto-fill and send
   - Should get relevant answer

5. **Test error handling:**
   - Enter invalid token → Should show auth error
   - Disconnect network → Should show retry option
   - Enter nonsense question → Genie should handle gracefully

**Embedded testing (in Perspective):**

6. **Load in Ignition session:**
   - Chat iframe loads without errors
   - Styling matches surrounding Perspective view
   - No scrollbar issues or layout breaks

7. **Test alarm integration:**
   - Click "Ask AI" on alarm
   - Question pre-fills in chat
   - Can send or edit before sending

8. **Test performance:**
   - Messages render smoothly (60 FPS)
   - Scroll is smooth
   - No lag when typing
   - No memory leaks (test for 30+ minutes)

---

## COMPLETION CHECKLIST

- [ ] HTML file generated by Claude Code
- [ ] Styled exactly like Perspective dark theme
- [ ] Uploaded to Databricks Files
- [ ] URL accessible from browser
- [ ] Calls Genie API successfully (test standalone)
- [ ] Handles errors gracefully
- [ ] Suggested questions work
- [ ] Data tables render correctly (if Genie returns data)
- [ ] SQL blocks display nicely (if Genie shows SQL)
- [ ] Responsive (works 400px to 1920px)
- [ ] No console errors
- [ ] Passes accessibility check
- [ ] Ready for Perspective embedding (File 04)

---

**Estimated time:** 4-6 hours (Claude Code generation + iteration for perfect styling)
**Critical:** Get UI quality right - this is what customers see and judge
**Next:** File 04 - Perspective view that embeds this chat UI
