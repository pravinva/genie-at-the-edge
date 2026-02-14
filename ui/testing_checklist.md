# Genie Chat UI Testing Checklist

## Overview

Comprehensive testing checklist for the Genie Chat UI before production deployment.

**Tester:** _______________
**Date:** _______________
**Version:** 1.0
**Environment:** ☐ Dev ☐ Staging ☐ Production

---

## Pre-Testing Setup

### Prerequisites

- [ ] HTML file uploaded to Databricks Files
- [ ] Databricks token generated and stored
- [ ] Genie Space ID confirmed from workstream 07
- [ ] SQL Warehouse running
- [ ] Ignition Designer access
- [ ] Browser with Developer Tools (F12)

### Test URLs

**Standalone HTML:**
```
https://adb-{workspace_id}.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html?token={TOKEN}&workspace={WORKSPACE}&space={SPACE}
```

**With Pre-filled Question:**
```
...&question=Why%20is%20Crusher%202%20vibrating%3F
```

---

## Section 1: Standalone HTML Testing

Test the HTML file directly in browser before Ignition integration.

### 1.1 Basic Loading

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Page loads** | Open standalone URL | Page loads within 2 seconds | ☐ Pass ☐ Fail |
| **No console errors** | Open DevTools (F12), check Console | No errors (except informational) | ☐ Pass ☐ Fail |
| **Dark theme applied** | Visual inspection | Background #1a1d23, text white | ☐ Pass ☐ Fail |
| **Fonts loaded** | Check DevTools Network tab | Inter and Roboto Mono fonts loaded | ☐ Pass ☐ Fail |
| **Status indicator** | Check header | Green dot with "Online" text | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
___________________________________________
```

---

### 1.2 Welcome Screen

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Welcome message** | Page loads first time | Shows welcome icon, title, subtitle | ☐ Pass ☐ Fail |
| **4 suggested questions** | Visual inspection | 4 clickable question chips displayed | ☐ Pass ☐ Fail |
| **Suggestion click** | Click "Why is Crusher 2 vibrating?" | Question fills input, sends automatically | ☐ Pass ☐ Fail |
| **Welcome disappears** | After first message sent | Welcome message hidden, messages visible | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
___________________________________________
```

---

### 1.3 Input Field

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Typing works** | Type text in input field | Text appears, cursor visible | ☐ Pass ☐ Fail |
| **Placeholder text** | Empty input field | Shows "Ask about equipment..." | ☐ Pass ☐ Fail |
| **Auto-expand** | Type 2-3 lines of text | Textarea expands (max 80px height) | ☐ Pass ☐ Fail |
| **Max length** | Type 500+ characters | Stops at 500 characters | ☐ Pass ☐ Fail |
| **Enter to send** | Type question, press Enter | Message sends, input clears | ☐ Pass ☐ Fail |
| **Shift+Enter** | Type question, press Shift+Enter | New line added, doesn't send | ☐ Pass ☐ Fail |
| **Escape key** | Type text, press Escape | Input clears, height resets | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
___________________________________________
```

---

### 1.4 Sending Messages

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **User message displays** | Type and send message | Blue bubble, right-aligned, message visible | ☐ Pass ☐ Fail |
| **Typing indicator** | After sending message | Three animated dots appear | ☐ Pass ☐ Fail |
| **AI response** | Wait 3-5 seconds | AI message appears, gray bubble, left-aligned | ☐ Pass ☐ Fail |
| **Response time** | Time from send to response | <5 seconds for first message | ☐ Pass ☐ Fail |
| **Auto-scroll** | Messages fill screen | Auto-scrolls to latest message | ☐ Pass ☐ Fail |
| **Multiple messages** | Send 10+ messages | All messages render, scroll works | ☐ Pass ☐ Fail |

**Response Time Measurements:**

| Question | Time (seconds) | Notes |
|----------|----------------|-------|
| "Why is Crusher 2 vibrating?" | _____ | _____ |
| "Show production last 24 hours" | _____ | _____ |
| "Which equipment needs maintenance?" | _____ | _____ |

---

### 1.5 Response Formatting

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Text formatting** | Send simple question | Text wraps correctly, readable | ☐ Pass ☐ Fail |
| **Line breaks** | Response with \n characters | Line breaks rendered as <br> | ☐ Pass ☐ Fail |
| **Long responses** | Complex question with long answer | Text wraps, doesn't overflow | ☐ Pass ☐ Fail |
| **Special characters** | Question with &, <, > | Escaped properly, no HTML injection | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
___________________________________________
```

---

### 1.6 SQL Display

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **SQL block renders** | Question returns SQL | SQL block appears with header and content | ☐ Pass ☐ Fail |
| **Syntax highlighting** | Visual inspection | Keywords blue, strings orange, numbers green | ☐ Pass ☐ Fail |
| **Copy button** | Click "Copy" button | SQL copied to clipboard, button shows "Copied!" | ☐ Pass ☐ Fail |
| **Horizontal scroll** | Long SQL query | Scrolls horizontally, no line wrapping | ☐ Pass ☐ Fail |
| **Code formatting** | Check indentation | Proper indentation preserved | ☐ Pass ☐ Fail |

**Test SQL:**
```sql
SELECT timestamp, vibration_rms, belt_tension
FROM equipment_telemetry
WHERE equipment_id = 'CRUSHER_02'
  AND timestamp >= NOW() - INTERVAL 24 HOURS
ORDER BY timestamp DESC
```

---

### 1.7 Data Table Display

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Table renders** | Question returns data | Table appears with headers and rows | ☐ Pass ☐ Fail |
| **Headers formatted** | Visual inspection | Dark background, bold text, aligned left | ☐ Pass ☐ Fail |
| **Row hover** | Hover over table rows | Row highlights on hover | ☐ Pass ☐ Fail |
| **Border styling** | Visual inspection | Clean borders, no double borders | ☐ Pass ☐ Fail |
| **Wide tables** | Table with many columns | Horizontal scroll, no overflow | ☐ Pass ☐ Fail |
| **Long data** | Cell with 50+ characters | Wraps or scrolls, doesn't break layout | ☐ Pass ☐ Fail |

**Test Data:**

Send question: "Show me production for the last 24 hours"

Expected table with columns: `Hour`, `Throughput (t/h)`, `Downtime (min)`

---

### 1.8 Suggested Follow-ups

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Suggestions appear** | After AI response | Suggestion chips appear below messages | ☐ Pass ☐ Fail |
| **Max 4 suggestions** | Visual inspection | No more than 4 chips displayed | ☐ Pass ☐ Fail |
| **Chip styling** | Visual inspection | Rounded corners, gray background, hover effect | ☐ Pass ☐ Fail |
| **Click suggestion** | Click any suggestion chip | Question fills input and sends | ☐ Pass ☐ Fail |
| **Relevant suggestions** | Check suggestion content | Suggestions relevant to previous answer | ☐ Pass ☐ Fail |
| **Suggestions update** | Send multiple messages | Suggestions change per response | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
___________________________________________
```

---

### 1.9 Clear Chat

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Clear button works** | Click trash icon in header | Confirmation dialog appears | ☐ Pass ☐ Fail |
| **Confirmation** | Click "OK" in dialog | All messages cleared | ☐ Pass ☐ Fail |
| **Welcome returns** | After clearing | Welcome message reappears | ☐ Pass ☐ Fail |
| **New conversation** | Send message after clear | New conversation_id created | ☐ Pass ☐ Fail |
| **Cancel clear** | Click trash, then "Cancel" | Messages remain | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
___________________________________________
```

---

### 1.10 Error Handling

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Invalid token** | Use wrong token in URL | Shows "Authentication expired" error | ☐ Pass ☐ Fail |
| **Network offline** | Disable network, send message | Shows "Failed to connect" with retry button | ☐ Pass ☐ Fail |
| **Retry works** | Click retry button | Message resends | ☐ Pass ☐ Fail |
| **Invalid space ID** | Use wrong space_id in URL | Shows connection error | ☐ Pass ☐ Fail |
| **Timeout** | Simulate slow network (DevTools) | Shows timeout error after 30 seconds | ☐ Pass ☐ Fail |

**Error Messages to Verify:**

- [ ] "Authentication expired. Please refresh the page."
- [ ] "Failed to connect to AI assistant. Please check your connection."
- [ ] "Sorry, I encountered an error. Please try again."

---

### 1.11 Pre-filled Questions

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **URL parameter works** | Add `&question=Test` to URL | "Test" appears in input field | ☐ Pass ☐ Fail |
| **URL encoding** | Use encoded question with spaces | Decodes correctly | ☐ Pass ☐ Fail |
| **Special characters** | Question with &, ?, = | Handled correctly | ☐ Pass ☐ Fail |
| **Can edit** | Pre-filled question in input | Can edit before sending | ☐ Pass ☐ Fail |
| **Can send as-is** | Pre-filled question | Can send without editing | ☐ Pass ☐ Fail |
| **Empty question** | `&question=` (empty value) | Input remains empty | ☐ Pass ☐ Fail |

**Test URLs:**

```
...&question=Why%20is%20Crusher%202%20vibrating%3F
...&question=Show%20me%20production%20for%20the%20last%2024%20hours
...&question=What%20caused%20the%20alarm%20at%2014%3A23%3F
```

---

## Section 2: Responsive Design Testing

Test at various screen widths.

### 2.1 Narrow Mode (400px)

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Layout adapts** | Resize browser to 400px width | All elements visible, no overflow | ☐ Pass ☐ Fail |
| **Messages scale** | Visual inspection | Messages max-width: 95% | ☐ Pass ☐ Fail |
| **Font size** | Visual inspection | Text 12px (slightly smaller) | ☐ Pass ☐ Fail |
| **Buttons accessible** | Try clicking all buttons | All buttons clickable, no overlap | ☐ Pass ☐ Fail |
| **Suggestions wrap** | Visual inspection | Suggestion chips wrap to multiple lines | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
___________________________________________
```

---

### 2.2 Standard Mode (500px)

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Optimal layout** | Resize to 500px | Clean layout, matches screenshots | ☐ Pass ☐ Fail |
| **Messages readable** | Send multiple messages | Text clear, spacing comfortable | ☐ Pass ☐ Fail |
| **Input comfortable** | Type long message | Comfortable typing area | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
___________________________________________
```

---

### 2.3 Wide Mode (800px+)

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Messages centered** | Resize to 800px+ | Messages max-width: 75%, centered | ☐ Pass ☐ Fail |
| **More padding** | Visual inspection | Additional padding (20px) | ☐ Pass ☐ Fail |
| **No wasted space** | Visual inspection | Layout uses space efficiently | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
___________________________________________
```

---

## Section 3: Browser Compatibility

Test in all major browsers.

### 3.1 Chrome/Edge (Chromium)

**Version:** _______________

| Test | Expected Result | Status |
|------|----------------|--------|
| All functionality works | ☐ Pass ☐ Fail |
| Styling correct | ☐ Pass ☐ Fail |
| Performance smooth (60 FPS) | ☐ Pass ☐ Fail |
| No console errors | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
```

---

### 3.2 Firefox

**Version:** _______________

| Test | Expected Result | Status |
|------|----------------|--------|
| All functionality works | ☐ Pass ☐ Fail |
| Styling correct | ☐ Pass ☐ Fail |
| Performance smooth | ☐ Pass ☐ Fail |
| No console errors | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
```

---

### 3.3 Safari

**Version:** _______________

| Test | Expected Result | Status |
|------|----------------|--------|
| All functionality works | ☐ Pass ☐ Fail |
| Styling correct | ☐ Pass ☐ Fail |
| Performance smooth | ☐ Pass ☐ Fail |
| No console errors | ☐ Pass ☐ Fail |

**Notes:**
```
___________________________________________
```

---

## Section 4: Performance Testing

### 4.1 Load Time

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Initial HTML load | <1 second | _____ | ☐ Pass ☐ Fail |
| Fonts loaded | <2 seconds | _____ | ☐ Pass ☐ Fail |
| React loaded | <1 second | _____ | ☐ Pass ☐ Fail |
| Total page ready | <2 seconds | _____ | ☐ Pass ☐ Fail |

**How to measure:**
1. Open DevTools → Network tab
2. Reload page (Ctrl+Shift+R)
3. Check "Finish" time at bottom

---

### 4.2 Response Time

| Question Type | Target | Actual | Status |
|---------------|--------|--------|--------|
| Simple text question | <5 seconds | _____ | ☐ Pass ☐ Fail |
| Question with SQL | <5 seconds | _____ | ☐ Pass ☐ Fail |
| Question with data table | <8 seconds | _____ | ☐ Pass ☐ Fail |
| Subsequent question (warm) | <3 seconds | _____ | ☐ Pass ☐ Fail |

**Test questions:**
1. "Why is Crusher 2 vibrating?" (simple)
2. "Show me production for the last 24 hours" (SQL + data)
3. "Which equipment needs maintenance?" (text)
4. "Tell me more" (follow-up)

---

### 4.3 Scrolling Performance

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Smooth scrolling** | Send 20+ messages, scroll up/down | Smooth 60 FPS, no stuttering | ☐ Pass ☐ Fail |
| **Auto-scroll smooth** | Send message, watch auto-scroll | Smooth animation | ☐ Pass ☐ Fail |
| **No layout shifts** | Messages appear | No content jumping | ☐ Pass ☐ Fail |

**How to measure:**
1. DevTools → Performance tab
2. Record while scrolling
3. Check framerate (should be 60 FPS)

---

### 4.4 Memory Usage

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Initial memory** | Open page, check Task Manager | <50 MB | ☐ Pass ☐ Fail |
| **After 10 messages** | Send 10 messages, check memory | <80 MB | ☐ Pass ☐ Fail |
| **After 30 minutes** | Keep page open 30 min, check memory | <100 MB, no leaks | ☐ Pass ☐ Fail |

**Memory Measurements:**

| Time | Memory (MB) | Notes |
|------|-------------|-------|
| Initial load | _____ | _____ |
| After 10 messages | _____ | _____ |
| After 30 minutes | _____ | _____ |

---

## Section 5: Accessibility Testing

### 5.1 Keyboard Navigation

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Tab navigation** | Press Tab repeatedly | Focus moves to all interactive elements | ☐ Pass ☐ Fail |
| **Focus visible** | Tab to elements | Clear focus indicator (blue outline) | ☐ Pass ☐ Fail |
| **Enter activates** | Tab to button, press Enter | Button activates | ☐ Pass ☐ Fail |
| **Escape key works** | Focus input, type, press Escape | Input clears | ☐ Pass ☐ Fail |

**Tab order:**
1. Message input → 2. Send button → 3. Voice button → 4. Clear button → 5. Suggestion chips

---

### 5.2 Screen Reader

**Tool:** _______________

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Page title** | Navigate to page | "AI Operations Assistant" announced | ☐ Pass ☐ Fail |
| **Input labeled** | Focus input | "Type your question" label read | ☐ Pass ☐ Fail |
| **Buttons labeled** | Focus buttons | "Send message", "Clear chat" read | ☐ Pass ☐ Fail |
| **Messages announced** | Send message | AI response announced when appears | ☐ Pass ☐ Fail |
| **Errors announced** | Trigger error | Error message announced with role="alert" | ☐ Pass ☐ Fail |

---

### 5.3 WCAG 2.1 AA Compliance

| Test | Expected Result | Status |
|------|----------------|--------|
| **Color contrast** | Text on backgrounds passes 4.5:1 ratio | ☐ Pass ☐ Fail |
| **Focus indicators** | All interactive elements have visible focus | ☐ Pass ☐ Fail |
| **Alt text** | Images (if any) have alt text | ☐ Pass ☐ Fail |
| **ARIA labels** | Interactive elements properly labeled | ☐ Pass ☐ Fail |
| **Semantic HTML** | Proper heading structure, landmarks | ☐ Pass ☐ Fail |

**Tool:** Use https://wave.webaim.org/ or axe DevTools

---

## Section 6: Ignition Integration Testing

Test embedded in Perspective.

### 6.1 Session Properties

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Token loaded** | Check Designer Console | "Databricks token loaded" message | ☐ Pass ☐ Fail |
| **Workspace ID set** | Check session.custom | workspace_id populated | ☐ Pass ☐ Fail |
| **Space ID set** | Check session.custom | genie_space_id populated | ☐ Pass ☐ Fail |
| **Token not empty** | Check session.custom | databricks_token not "" | ☐ Pass ☐ Fail |

**How to check:**
```python
# In Designer Console (Ctrl+Shift+C)
print session.custom.databricks_workspace_id
print session.custom.genie_space_id
print len(session.custom.databricks_token)  # Should be >40
```

---

### 6.2 View Loading

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **View loads** | Open GenieChat view | Iframe loads within 3 seconds | ☐ Pass ☐ Fail |
| **No iframe errors** | Check Designer Output Console | No errors logged | ☐ Pass ☐ Fail |
| **Styling matches** | Visual inspection | Dark theme consistent with Perspective | ☐ Pass ☐ Fail |
| **No scrollbars** | Visual inspection | Iframe fills container, no extra scrollbars | ☐ Pass ☐ Fail |

---

### 6.3 URL Expression Binding

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **URL builds correctly** | Check iframe src in DevTools | URL has all parameters (token, workspace, space) | ☐ Pass ☐ Fail |
| **URL encoding** | Set view.custom.pending_question | Special characters encoded properly | ☐ Pass ☐ Fail |
| **Dynamic updates** | Change view.custom property | URL updates, iframe reloads | ☐ Pass ☐ Fail |

**URL format:**
```
https://adb-{workspace}.azuredatabricks.net/files/mining-demo/genie_chat_perspective.html?token={token}&workspace={workspace}&space={space}&question={encoded_question}
```

---

### 6.4 Alarm Integration

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Button visible** | Navigate to alarm table | "Ask AI" button visible in each row | ☐ Pass ☐ Fail |
| **Button click works** | Click "Ask AI" on alarm | Chat popup opens | ☐ Pass ☐ Fail |
| **Question pre-filled** | Check chat input | Alarm details in question | ☐ Pass ☐ Fail |
| **Question format** | Visual inspection | "Why did alarm '{name}' trigger at {time}? Equipment: {id}" | ☐ Pass ☐ Fail |
| **Can edit question** | Click in input, edit text | Question editable before sending | ☐ Pass ☐ Fail |
| **Can send question** | Click Send or press Enter | Question sends, response received | ☐ Pass ☐ Fail |

**Test with these alarms:**

| Alarm Name | Equipment | Expected Question |
|------------|-----------|-------------------|
| High Vibration | CRUSHER_02 | "Why did alarm 'High Vibration' trigger at {time}? Equipment: CRUSHER_02" |
| High Temperature | CONVEYOR_03 | "Why did alarm 'High Temperature' trigger at {time}? Equipment: CONVEYOR_03" |

---

### 6.5 Equipment Integration

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Button visible** | Navigate to equipment detail | "Ask AI Assistant" button visible | ☐ Pass ☐ Fail |
| **Button click** | Click button | Chat opens with equipment question | ☐ Pass ☐ Fail |
| **Question includes details** | Check question | Includes equipment name, ID, status | ☐ Pass ☐ Fail |
| **Response relevant** | Check AI response | Response addresses specific equipment | ☐ Pass ☐ Fail |

---

### 6.6 Popup Behavior

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Popup opens** | Click "Ask AI" button | Chat popup appears on right side | ☐ Pass ☐ Fail |
| **Popup positioned** | Visual inspection | Right: 0, Top: 0, Bottom: 0, Width: 500px | ☐ Pass ☐ Fail |
| **Popup not modal** | Click behind popup | Can interact with main view | ☐ Pass ☐ Fail |
| **Popup draggable** | Try dragging (if enabled) | Popup moves or stays fixed per config | ☐ Pass ☐ Fail |
| **Popup resizable** | Try resizing (if enabled) | Popup resizes or stays fixed per config | ☐ Pass ☐ Fail |
| **Close button works** | Click X in popup | Popup closes | ☐ Pass ☐ Fail |
| **Multiple opens** | Open, close, open again | Opens correctly each time | ☐ Pass ☐ Fail |

---

## Section 7: Security Testing

### 7.1 Token Security

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Token not visible** | View page source | Token not in HTML source | ☐ Pass ☐ Fail |
| **Token in URL** | Check URL bar | Token visible in URL (acceptable for iframe) | ☐ Pass ☐ Fail |
| **Token not logged** | Check DevTools Console | Token not printed in logs | ☐ Pass ☐ Fail |
| **Token encrypted** | Check Ignition tag/DB | Token stored encrypted | ☐ Pass ☐ Fail |

---

### 7.2 Input Sanitization

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **HTML injection** | Type `<script>alert('XSS')</script>` | Rendered as text, not executed | ☐ Pass ☐ Fail |
| **SQL injection** | Type `'; DROP TABLE--` | Handled safely by Genie, no SQL error | ☐ Pass ☐ Fail |
| **Special characters** | Type `<>&"'` | Escaped properly in display | ☐ Pass ☐ Fail |

---

## Section 8: Edge Cases

### 8.1 Unusual Inputs

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Empty message** | Click Send with empty input | Nothing happens or shows "Type a message" | ☐ Pass ☐ Fail |
| **Very long message** | Type 500+ characters | Stops at 500, shows warning | ☐ Pass ☐ Fail |
| **Only spaces** | Type "     ", click Send | Trimmed, treated as empty | ☐ Pass ☐ Fail |
| **Emoji input** | Type emojis | Renders correctly | ☐ Pass ☐ Fail |
| **Non-English** | Type Chinese/Arabic/etc | Renders correctly (if supported) | ☐ Pass ☐ Fail |

---

### 8.2 Network Issues

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Slow network** | Throttle network (DevTools), send message | Shows typing indicator, waits | ☐ Pass ☐ Fail |
| **Network drops** | Disconnect during message | Shows error, retry button | ☐ Pass ☐ Fail |
| **Retry works** | Click retry after network restored | Message resends successfully | ☐ Pass ☐ Fail |
| **Timeout handling** | Block response for 30+ seconds | Shows timeout error | ☐ Pass ☐ Fail |

---

### 8.3 API Issues

| Test | Steps | Expected Result | Status |
|------|-------|----------------|--------|
| **Invalid token** | Use expired/wrong token | Shows auth error | ☐ Pass ☐ Fail |
| **Space deleted** | Use deleted space_id | Shows connection error | ☐ Pass ☐ Fail |
| **Warehouse stopped** | Stop SQL warehouse | Graceful error or auto-starts | ☐ Pass ☐ Fail |
| **Rate limit** | Send 10 messages in 10 seconds | All succeed or shows rate limit message | ☐ Pass ☐ Fail |

---

## Section 9: Production Readiness

### 9.1 Documentation

- [ ] Integration guide complete
- [ ] Deployment guide complete
- [ ] Troubleshooting guide complete
- [ ] User training materials prepared
- [ ] Runbook created

---

### 9.2 Monitoring

- [ ] Usage metrics tracked
- [ ] Error rates monitored
- [ ] Performance metrics logged
- [ ] Alerts configured

---

### 9.3 Security

- [ ] Token rotation schedule set
- [ ] Audit logging enabled
- [ ] IP access lists configured (if applicable)
- [ ] Security review completed

---

### 9.4 Training

- [ ] User training session scheduled
- [ ] Demo video recorded
- [ ] Quick reference guide created
- [ ] Support contacts documented

---

## Test Summary

### Overall Results

**Total Tests:** _____
**Passed:** _____
**Failed:** _____
**Pass Rate:** _____%

### Critical Issues

List any blocking issues:

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

### Minor Issues

List non-blocking issues:

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

### Recommendations

Based on testing:

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

---

## Sign-Off

### Tester

**Name:** _______________
**Signature:** _______________
**Date:** _______________

### Project Lead

**Name:** _______________
**Signature:** _______________
**Date:** _______________

### Deployment Approval

☐ **Approved for Production**
☐ **Approved with conditions:** _______________
☐ **Not approved - requires fixes**

**Approved By:** _______________
**Date:** _______________

---

**Document Version:** 1.0
**Last Updated:** 2025-02-14
**Project:** Mining Operations Genie Demo
