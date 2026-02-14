# Backup Plan - Demo Failure Recovery

**Version:** 1.0
**Purpose:** Recovery procedures for live demo failures

---

## Philosophy: Stay Calm, Have Options

**Key Principle:** Technology demos fail. It's how you handle failure that matters.

**Golden Rules:**
1. **Never apologize excessively** - "Let me switch to plan B" not "I'm so sorry this isn't working"
2. **Maintain confidence** - Your tone and body language matter more than the tech
3. **Keep talking** - Silence kills credibility, fill time while troubleshooting
4. **Have backup materials ready** - Video, screenshots, diagrams
5. **Pivot gracefully** - "Perfect, this gives me a chance to show you..."

---

## Failure Scenario 1: Genie Doesn't Respond

### Symptoms:
- Query sent, typing indicator appears, then times out
- Error message: "Query failed" or "Service unavailable"
- Response takes >30 seconds (audience getting impatient)

### Immediate Response (Say This):

*"Hmm, looks like we hit a network timeout - that happens occasionally in live demos. Let me retry..."*

**[Click retry button]**

### While Waiting (Buy Time):

*"While that loads, let me explain what's happening behind the scenes. The AI is translating my natural language question into SQL, querying years of operational data across multiple tables, and synthesizing a response. Normally this takes 3-5 seconds."*

### If Retry Succeeds:

*"There we go - 5 seconds this time. As I was saying..."*

**[Continue with demo]**

### If Retry Fails Again (30 seconds elapsed total):

**Option A: Show Pre-Recorded Response (Best):**

*"Rather than wait for the network, let me show you what the response typically looks like..."*

**[Open screenshot or video showing expected response]**

*"Here's the exact same query from yesterday. You can see the AI identified the vibration spike, matched it to the January 15th incident, and recommended belt inspection. This is what operators see in 4-5 seconds typically."*

**[Continue to next scenario or backup video]**

---

**Option B: Show SQL Query Directly (Technical Audience):**

*"Actually, this is a perfect opportunity to show you transparency. Let me show you the SQL that Genie would generate..."*

**[Open SQL editor, run pre-written query]**

```sql
SELECT
    timestamp,
    equipment_id,
    metric_value AS vibration_mm_s
FROM main.mining_ops.sensor_data_gold
WHERE equipment_id = 'Crusher_2'
    AND metric_name = 'Vibration'
    AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
ORDER BY timestamp DESC
LIMIT 10;
```

*"See - Genie translates 'Show me Crusher 2 vibration' into this SQL automatically. The AI layer interprets natural language, but underneath it's querying real data in the lakehouse."*

**[Show query results]**

*"And here's the data - vibration ramped from 20mm/s to 42mm/s over the last hour. Genie would add context like 'This is 2.1x normal baseline' and 'Similar to January 15 incident.' The intelligence layer adds that interpretation on top of the raw query."*

**[Continue with demo, skip to next scenario]**

---

**Option C: Switch to Backup Video (Non-Technical Audience):**

*"Tell you what - rather than troubleshoot live, let me show you a recording of this exact workflow from yesterday. The functionality is identical, but we'll save time."*

**[Play backup video]**

*"Here's an operator clicking the alarm, asking the AI about Crusher 2... and there's the response in 4 seconds. Everything you're seeing is real data from the system."*

**[Narrate over video, pause to explain key points]**

---

### Root Cause (Troubleshoot After Demo):

**Possible Causes:**
- SQL Warehouse stopped (auto-starts on demand, takes 1-2 min)
- Genie service timeout (retry usually works)
- Network latency spike (transient)
- Browser cache issue (refresh page)

**Prevention for Next Demo:**
- Warm SQL Warehouse 30 min before (run test queries)
- Keep backup video open in tab
- Test Genie response 5 min before demo starts

---

## Failure Scenario 2: Perspective View Won't Load

### Symptoms:
- Blank screen where Perspective HMI should be
- "Session failed to start" error
- Infinite loading spinner

### Immediate Response:

*"The Perspective session isn't starting - let me refresh..."*

**[Press F5 or click refresh]**

### While Refreshing (10-15 seconds):

*"Perspective is Ignition's web-based HMI platform. Sessions sometimes need a refresh if they've been idle."*

### If Refresh Works:

*"There we go. Now you can see the equipment status..."*

**[Continue with demo]**

### If Refresh Fails (30 seconds elapsed):

**Immediate Pivot to Backup Video:**

*"The demo environment is having a connectivity issue. Rather than troubleshoot live, let me show you the pre-recorded version. The system works exactly the same way."*

**[Open backup video]**

*"This is from yesterday's test run - same Perspective interface, same equipment, same AI queries. Let me walk you through it..."*

**[Play video, narrate key points]**

---

**Alternative: Show Screenshots with Narration:**

If video won't play either (worst case):

*"Here's what the interface looks like..."*

**[Open screenshot folder, show images in sequence]**

**Image 1:** *"This is the Perspective HMI - equipment status on left, alarms in center, AI chat on right."*

**Image 2:** *"Operator clicks the Crusher 2 alarm, hits 'Ask AI' button."*

**Image 3:** *"Chat pre-fills with the question based on alarm context."*

**Image 4:** *"And here's the AI response - 4 seconds later, full analysis with historical context."*

*"I know screenshots aren't as compelling as live demo, but this shows the actual interface and workflow. Happy to set up another session where we can show it live if you'd like."*

---

### Root Cause (Troubleshoot After):

**Possible Causes:**
- Ignition Gateway stopped/crashed
- Network issue (can't reach Gateway)
- Browser issue (cache, cookies)
- Session timeout (if left idle too long)

**Prevention:**
- Test Perspective URL 5 min before demo
- Keep Gateway monitor open (check status)
- Have backup video tested and ready

---

## Failure Scenario 3: Tags Not Updating (Stale Data)

### Symptoms:
- Tag values frozen (same number for 30+ seconds)
- Timestamps not changing
- Equipment status shows old data

### Immediate Response:

*"I notice the tags aren't updating - the simulation script must have paused. Not a problem..."*

### Option A: Restart Simulation (If Quick):

*"Give me 30 seconds to restart the data feed..."*

**[While restarting, fill time]:**

*"In production, this data is coming from real PLCs - obviously we're using a simulator for demo purposes. The data model and AI logic are identical to production."*

**[Check if tags updating]**

*"There we go - you can see vibration values changing now, timestamps updating every 5 seconds."*

**[Continue demo]**

---

### Option B: Use Static Data (If Restart Fails):

*"Actually, let's use the current snapshot - the AI can query historical data just as effectively."*

**[Proceed with demo using frozen values]**

*"Even though these values are static right now, watch what happens when I ask the AI about Crusher 2..."*

**[Send query, show response]**

*"The AI is querying the database, which has months of historical data. Real-time updates are valuable, but the intelligence layer works with any data - real-time or historical."*

**[Continue demo, emphasize historical analysis]**

---

### Option C: Switch to SQL Queries (Technical Audience):

*"Since the live tags paused, let me show you how the AI queries historical data directly..."*

**[Open Databricks SQL Editor]**

```sql
SELECT
    equipment_id,
    metric_name,
    AVG(metric_value) AS avg_value,
    MAX(metric_value) AS max_value
FROM main.mining_ops.sensor_data_gold
WHERE date = CURRENT_DATE
    AND equipment_type = 'Crusher'
GROUP BY equipment_id, metric_name;
```

*"Here's today's data - you can see Crusher 2 vibration averaging 42mm/s, much higher than Crusher 1 and 3. Genie does these queries automatically when operators ask 'Compare all crushers.'"*

**[Show results, explain]**

---

### Root Cause:

**Possible Causes:**
- Simulation script crashed (common in demos)
- Tag provider disconnected
- Gateway script execution paused

**Prevention:**
- Start simulation 30+ min before demo (warm up)
- Monitor Gateway script execution status
- Have manual script restart procedure ready

---

## Failure Scenario 4: Complete System Meltdown

### Symptoms:
- Nothing works (Gateway down, Databricks unreachable, Perspective offline)
- Multiple failures at once
- Beyond quick recovery

### Immediate Response (Stay Calm):

*"Looks like we're having technical difficulties across the board. Rather than spend your time troubleshooting, let me show you the pre-recorded walkthrough."*

**[Open backup video immediately]**

*"This is frustrating, but it happens with live demos. What you're about to see is the exact system running perfectly - same functionality, same data model, same AI responses."*

---

### Play Backup Video with Narration:

**Narrate over video (don't just let it play silently):**

*"Here's the Perspective interface I wanted to show you live..."*

*"Watch what happens when the operator clicks the alarm and asks the AI..."*

*"Notice the response time - 4 seconds from query to answer..."*

*"And here's the follow-up question - 'What happened on January 15?' - pulling complete historical context..."*

**[Pause video at key moments, explain]**

---

### After Video (Recovery):

**Option 1: Offer to Reschedule Live Demo:**

*"I apologize for the technical issues. The system works reliably in production - we've had 99.7% uptime in pilots. I'd like to offer a follow-up session where I can show you this live. Would that be valuable?"*

**If they say yes:**
- Schedule within 1 week
- Test setup 1 hour before next session
- Have backup tested again

**If they say no (not interested):**
- Gauge reason: Is it the tech failures, or disinterest in solution?
- Offer other materials: architecture docs, ROI calculator, customer references

---

**Option 2: Pivot to Q&A and Architecture Discussion:**

*"Since we have time, let's shift to Q&A. What questions do you have about how this would work in your environment?"*

**[Open architecture diagram]**

*"Let me walk through how this integrates with your existing systems..."*

**Benefits of pivot:**
- Turns failure into interactive session
- Addresses their specific concerns
- Demonstrates expertise beyond demo script

---

**Option 3: Show Databricks Platform Directly (No Ignition):**

If Databricks is accessible but Ignition is down:

*"Let me show you the Databricks side - the data lakehouse and Genie AI..."*

**[Open Databricks workspace]**

**Show:**
- Delta tables (sensor_data_gold, incidents)
- Sample queries in SQL editor
- Genie space (ask questions via web interface)
- DLT pipeline (real-time processing)

*"This is the intelligence layer. In production, this connects to your Ignition HMI like we tried to show. The AI works the same way - natural language in, insights out."*

---

### Post-Demo Actions (Damage Control):

**Within 1 Hour:**
- Send apology email
- Attach backup video
- Offer reschedule or deeper dive session

**Email Template:**

```
Subject: Follow-up: Mining Operations AI Demo + Backup Recording

Hi [Name],

I apologize for the technical difficulties during today's demo. These issues are rare (we've had 99%+ success rate in previous demos), but clearly Murphy's Law was in effect today.

To make up for it, I'm attaching:
1. Full recording of the demo (from a successful run)
2. Architecture documentation
3. ROI calculator for your site

I'd also like to offer:
- A follow-up live demo (I'll test it 3x beforehand)
- OR a deeper technical discussion with your team
- OR proceed directly to pilot (if you're confident from the video)

What would be most valuable for you?

Again, apologies for wasting your time today. The technology works reliably in production - just had a bad demo day.

Best,
Pravin
```

---

### Root Cause Analysis (After Demo):

**Document what failed:**
- Time of failure
- Symptoms
- Steps taken to recover
- What worked / didn't work

**Update procedures:**
- Add to pre-demo checklist
- Improve monitoring
- Better backup materials

**Debrief with team:**
- What would we do differently?
- How can we prevent this failure mode?

---

## Failure Scenario 5: Audio/Video Issues (Remote Demo)

### Symptoms:
- Audience can't hear you
- Screen share frozen/pixelated
- Zoom/Teams disconnected

### Immediate Actions:

**Audio Issues:**

*[Type in chat]:* "Can you hear me? If not, I'll reconnect..."

**[If no response in 10 seconds]:**
- Disconnect and rejoin meeting
- Test audio before starting again
- Offer to dial in by phone if persistent

---

**Screen Share Frozen:**

*"Looks like my screen share froze. Let me stop and restart..."*

**[Stop share, restart]**

*"Can you see this now? Please confirm in chat."*

**[If still frozen]:**
- Switch to different screen share method (app vs entire screen)
- Reduce resolution (helps with low bandwidth)
- Fallback: Email video, watch together with audio only

---

**Complete Disconnect:**

**[If you get disconnected]:**
- Rejoin immediately (within 30 seconds)
- Apologize briefly, continue where you left off
- Don't over-apologize - makes it bigger issue than it is

**[If disconnected 2+ times]:**

*"This connection is unreliable. Can we reschedule for better quality? Or I can send the video and we can discuss over phone?"*

---

### Prevention:

- Test Zoom/Teams 15 min before
- Close bandwidth-heavy apps (Spotify, Slack, etc.)
- Use wired connection (not WiFi)
- Have backup: Phone hotspot ready

---

## General Recovery Principles

### The 3-Strike Rule

**Strike 1: Technical hiccup**
- Response: "Let me retry that..."
- Tone: Casual, confident
- Action: Quick fix attempt

**Strike 2: Still not working**
- Response: "Let's try plan B..."
- Tone: Calm, professional
- Action: Switch to backup material

**Strike 3: Multiple failures**
- Response: "Rather than troubleshoot, let me show you the recording..."
- Tone: Apologetic but not panicked
- Action: Pivot completely to backup video + Q&A

---

### What NOT to Do

**Don't:**
- Spend 10+ minutes troubleshooting on camera (wastes audience time)
- Blame others ("IT must have changed something...")
- Over-apologize ("I'm so sorry, this is embarrassing...")
- Make excuses ("This worked yesterday!")
- Show frustration (sighing, swearing, negativity)

**Do:**
- Stay calm and professional
- Acknowledge briefly, move on quickly
- Offer value despite technical issues (backup materials, Q&A, reschedule)
- Focus on content, not tech
- Maintain confidence in solution (it works in production, just bad demo luck)

---

### Backup Materials Checklist (Always Ready)

**Before Every Demo:**

- [ ] **Backup video** (tested, plays without issues)
  - Location: Desktop or easily accessible folder
  - Format: MP4 (universal playback)
  - Duration: 5-8 minutes (full demo walkthrough)
  - Tested: Plays on your computer without lag

- [ ] **Screenshots** (sequence showing key moments)
  - Perspective HMI overview
  - Alarm with "Ask AI" button
  - Chat pre-filled question
  - AI response with analysis
  - Follow-up questions and answers
  - Architecture diagram

- [ ] **Architecture diagram** (PDF or image)
  - Clean, professional layout
  - Shows: Ignition → Databricks → Genie → Perspective
  - Labels clear and readable when screen-shared

- [ ] **Demo script** (this document)
  - Open on second screen for reference
  - Talking points highlighted

- [ ] **Q&A document** (qna_preparation.md)
  - Open in background tab
  - Quick reference for tough questions

- [ ] **ROI calculator** (business_value_calculator.md)
  - Ready to share if financial questions arise

---

### Recovery Success Stories

**Example 1: SQL Warehouse Timeout**

Demo: Genie query timed out
Response: "Let me show you the SQL it would have generated..."
Outcome: Technical audience loved seeing underlying SQL, became teaching moment
Result: Pilot approved

**Example 2: Perspective Crashed**

Demo: Perspective session died mid-demo
Response: Switched to backup video, narrated key points
Outcome: Saved time, audience saw full workflow
Result: "We saw enough, let's talk pilot scope"

**Example 3: Complete Network Outage**

Demo: Lost internet connection entirely
Response: "My internet is down. Let me show slides and we'll discuss architecture, then I'll send the video after."
Outcome: Architecture discussion revealed customer needs, customized solution
Result: Better outcome than generic demo - customer felt heard

---

### Post-Demo Review

**After EVERY demo (success or failure):**

**What worked well?**
- Which parts of demo resonated?
- What questions were asked?
- What surprised you?

**What failed or was awkward?**
- Technical issues?
- Pacing problems?
- Unclear explanations?

**What would you change?**
- Different order of scenarios?
- More/less technical depth?
- Better visuals?

**Action items:**
- Update pre-demo checklist
- Improve backup materials
- Refine talking points

---

### Key Takeaway

**Demos fail. It's normal. What matters:**

1. **Preparation:** Have backup materials ready BEFORE you start
2. **Composure:** Stay calm and confident, don't panic
3. **Pivot:** Switch to backup gracefully, maintain value for audience
4. **Learn:** Document failures, improve for next time

**Remember:** The worst demo is one where you give up. As long as you deliver value (via backup video, Q&A, architecture discussion), you can still win the deal.

---

**End of Backup Plan Document**

---

## Quick Reference (Print This Page)

### Failure → Action Flowchart

```
Issue Occurs
    ↓
Try Quick Fix (30 seconds)
    ↓
Fixed? YES → Continue demo
    ↓
    NO
    ↓
Show Backup Video
    ↓
Narrate Key Points
    ↓
Pivot to Q&A
    ↓
Offer Follow-up Session
```

### Emergency Contacts

**Databricks Support:** [Phone]
**Ignition Admin:** [Name/Phone]
**Your Manager:** [Name/Phone]
**Backup Presenter:** [Name/Phone] (in case you're completely blocked)

### Backup Material Locations

**Video:** `/Desktop/demo_backup_video.mp4`
**Screenshots:** `/Desktop/demo_screenshots/`
**Architecture PDF:** `/Desktop/architecture_diagram.pdf`

### One-Liner Responses

- **Genie timeout:** "Let me retry... while that loads, here's what's happening behind the scenes..."
- **Perspective crash:** "Let me switch to the pre-recorded version to save time..."
- **Tags frozen:** "The simulation paused - not a problem, let's use historical data..."
- **Complete failure:** "Technical difficulties - let me show you the recording instead..."

**Stay calm. Have backups. Deliver value.**
