# Pre-Demo Checklist - Mining Operations Genie

**Complete this checklist 30 minutes before your scheduled demo.**

**Purpose:** Ensure all systems are warm, tested, and ready for a flawless live demonstration.

---

## TIMING: T-30 MINUTES (30 Minutes Before Demo)

### System Warmup

**Ignition Gateway:**

- [ ] **Gateway Running**
  - Navigate to http://localhost:8088
  - Verify Gateway webpage loads
  - Check status: Should show "RUNNING"

- [ ] **Simulation Active**
  - Open Gateway > Scripting > System
  - Check last execution time of simulation script
  - Verify tags are updating (not stale)
  - Minimum: 30 minutes of simulation history before demo

- [ ] **Tag Values Realistic**
  - Check Crusher 1: Vibration ~20-22 mm/s (normal)
  - Check Crusher 2: Vibration ~40-45 mm/s (elevated - for demo)
  - Check Crusher 3: Vibration ~19-21 mm/s (normal)
  - Verify timestamps are current (within last 5 seconds)

**Action if failed:** Restart simulation script, wait 5 minutes for data to populate

---

**Databricks Workspace:**

- [ ] **SQL Warehouse Running**
  - Open Databricks workspace
  - Navigate to SQL Warehouses
  - Start your assigned warehouse (if stopped)
  - Wait until status = "Running" (can take 3-5 minutes)

- [ ] **Test Query Warm**
  - Open SQL Editor
  - Run test query: `SELECT COUNT(*) FROM main.mining_ops.sensor_data_gold`
  - First execution: May take 10-15 seconds (cold start)
  - Second execution: Should be <2 seconds (warm)
  - Run 2-3 test queries to ensure cache is warm

**Action if failed:** Start warehouse earlier, run multiple test queries

---

**DLT Pipeline:**

- [ ] **Pipeline Status**
  - Navigate to Delta Live Tables
  - Find "Mining Operations Real-Time" pipeline
  - Check status: Should be "Running" or "Idle"
  - Check last update time: Should be within last 2 minutes

- [ ] **Data Freshness**
  - Open pipeline graph
  - Click on "sensor_data_gold" table
  - Check "Last updated" timestamp
  - Should be within last 60 seconds

- [ ] **No Errors**
  - Check for any red error indicators
  - Review logs if any warnings

**Action if failed:** Restart pipeline, allow 5 minutes to stabilize

---

**Genie Space:**

- [ ] **Genie Accessible**
  - Navigate to Genie in Databricks workspace
  - Open "Mining Operations" space
  - Verify you can see the space (permissions OK)

- [ ] **Test Query**
  - Type: "How many crusher records are in the last hour?"
  - Press Enter
  - Response time: Should be 3-6 seconds
  - Response should show actual number (not error)

- [ ] **Instruction Set Active**
  - Check Genie Space Settings
  - Verify custom instructions are loaded
  - Review instruction content (should reference mining operations context)

**Action if failed:** Refresh browser, check permissions, verify space configuration

---

**Perspective HMI:**

- [ ] **Perspective Session Open**
  - Navigate to Perspective URL (get from project config)
  - Session should load within 5 seconds
  - Verify all components visible (no blank panels)

- [ ] **Real-Time Updates**
  - Watch equipment status values
  - Should see tag values changing every 5-10 seconds
  - Verify timestamps updating

- [ ] **Chat Interface**
  - Click on chat icon/panel
  - Verify chat interface loads
  - Test sending a message: "Hello"
  - Should get response (even if generic)

- [ ] **Alarm Table Populated**
  - Check active alarms section
  - Should see at least 1-2 alarms (including Crusher 2 high vibration)
  - Verify "Ask AI" button visible next to each alarm

**Action if failed:** Refresh Perspective session, check browser console for errors

---

## TIMING: T-20 MINUTES

### Fault Injection Setup

**Choose Your Demo Strategy:**

**Option A: Live Fault Progression** (More impressive but riskier)
- Inject fault NOW (T-20)
- By demo time (T-0), fault will have progressed
- Shows real-time evolution
- Risk: Timing might not align perfectly

**Option B: Pre-Staged Fault** (Safer, more controlled)
- Inject fault 1-2 hours before demo
- Fault is stable and visible immediately
- Guaranteed to have historical data
- Risk: Less "wow factor" on progression

**Recommended: Option B for first few demos, Option A once confident**

---

**Inject Crusher 2 Fault:**

- [ ] **Access Fault Injection Script**
  - Open Ignition Designer (if local script)
  - Or open Python script (if external injection)

- [ ] **Set Fault Parameters**
  ```python
  fault_config = {
      "equipment": "Crusher_2",
      "fault_type": "vibration_increase",
      "baseline": 20,  # mm/s
      "target": 42,    # mm/s
      "ramp_time": 600  # 10 minutes
  }
  ```

- [ ] **Execute Fault**
  - Run fault injection
  - Verify tags start ramping up
  - Monitor for 2-3 minutes to confirm trend

- [ ] **Verify Alarm Triggered**
  - Check that Crusher 2 High Vibration alarm appears
  - Verify alarm timestamp
  - Confirm alarm visible in Perspective HMI

**Action if failed:** Manually set tag values via Ignition Gateway

---

## TIMING: T-15 MINUTES

### Demo Environment Setup

**Computer Preparation:**

- [ ] **Close Unnecessary Applications**
  - Close Slack, email, messaging apps
  - Close any non-essential browser tabs
  - Keep only: Browser with demo tabs, this checklist, notes

- [ ] **Turn Off Notifications**
  - macOS: Do Not Disturb mode ON
  - Windows: Focus Assist ON
  - Browser: Notification settings OFF
  - Phone: Silent mode

- [ ] **Clean Up Desktop**
  - Hide desktop icons (if presenting desktop)
  - Close any personal or confidential windows
  - Professional background/wallpaper

- [ ] **Open Required Tabs**
  - Tab 1: Perspective HMI (full screen ready)
  - Tab 2: Databricks workspace (optional, for deep dive)
  - Tab 3: Architecture diagram (if showing)
  - Tab 4: Backup video (just in case)

**Action:** Arrange tabs in order you'll present them

---

**Screen Sharing Setup:**

- [ ] **Test Screen Share**
  - Open Zoom/Teams/WebEx
  - Start a test meeting (with yourself or colleague)
  - Share screen and verify:
    - Resolution looks good (not pixelated)
    - All content visible (not cut off)
    - Frame rate smooth (not laggy)

- [ ] **Audio Test**
  - Test microphone
  - Speak and listen to playback
  - Check for echo (disable speaker output if needed)
  - Verify volume level (not too quiet or too loud)

- [ ] **Camera Test** (if using video)
  - Check camera angle and lighting
  - Professional background
  - Camera at eye level

**Action if issues:** Restart Zoom/Teams, check system audio settings

---

**Presentation Materials:**

- [ ] **Second Screen Setup**
  - Open demo_script.md on second screen
  - Font size large enough to read quickly
  - Position for easy glancing (don't look like you're reading)

- [ ] **Backup Materials Ready**
  - Backup video downloaded and tested
  - Screenshots in easily accessible folder
  - Architecture diagrams ready to share
  - ROI calculator file ready

- [ ] **Timing Device**
  - Stopwatch app open (for showing latency)
  - Timer app set for 15 minutes (to track overall timing)
  - Clock visible (to not run over time)

**Action:** Practice transitioning between materials smoothly

---

## TIMING: T-10 MINUTES

### Final Verification

**End-to-End Test:**

- [ ] **Run Complete User Journey**
  - Open Perspective HMI
  - Click on Crusher 2 alarm
  - Click "Ask AI" button
  - Verify question pre-fills
  - Send question
  - Verify response within 5 seconds
  - Ask follow-up: "What happened on January 15?"
  - Verify follow-up response

- [ ] **Check Response Quality**
  - Response mentions specific vibration values
  - Response references historical incident
  - Response gives actionable recommendation
  - Response includes confidence level

- [ ] **Verify Performance**
  - Response time: 3-6 seconds (acceptable)
  - No errors or timeouts
  - Chat UI smooth and responsive

**Action if failed:** See backup_plan.md for recovery steps

---

**Data Verification:**

- [ ] **Historical Data Exists**
  - Query: `SELECT COUNT(*) FROM main.mining_ops.incidents WHERE equipment = 'Crusher_2' AND date >= '2025-01-01'`
  - Should return at least 5-10 historical incidents
  - Verify January 15th incident exists specifically

- [ ] **Real-Time Data Flowing**
  - Query: `SELECT MAX(timestamp) FROM main.mining_ops.sensor_data_gold`
  - Timestamp should be within last 60 seconds

- [ ] **Genie Can Access Data**
  - Ask Genie: "How many crushers are currently operating?"
  - Should return 3
  - Ask Genie: "Show me Crusher 2 vibration right now"
  - Should return current value (~42 mm/s)

**Action if failed:** Check pipeline, check table permissions

---

## TIMING: T-5 MINUTES

### Pre-Demo Mental Preparation

**Presenter Readiness:**

- [ ] **Review Key Points**
  - Problem: 30 min manual investigation
  - Solution: 5 second AI response
  - Value: 60x faster, $230K annual savings
  - Differentiator: Platform-agnostic, unified lakehouse

- [ ] **Practice Opening**
  - Say your opening line out loud
  - Practice transition to screen share
  - Visualize first 2 minutes

- [ ] **Deep Breath**
  - Take 3 deep breaths
  - Shake out any nervous energy
  - Smile (helps vocal tone)

- [ ] **Confidence Check**
  - You've tested everything
  - You have backup plans
  - You know the content
  - You're ready

**Mindset:** You're showing something genuinely valuable that solves real problems.

---

**Final Environment Check:**

- [ ] **Browser Ready**
  - Perspective HMI tab in foreground
  - Full screen mode ON (F11 or browser full screen)
  - Zoom level: 100% (not zoomed in/out)

- [ ] **Meeting Ready**
  - Meeting link open
  - 5 minutes early to join
  - Camera/audio working
  - Screen share ready (but not started yet)

- [ ] **Support Resources**
  - Demo script open on second screen
  - qna_preparation.md open in background tab
  - backup_plan.md open in background tab
  - Phone nearby (in case computer fails completely)

**Action:** Join meeting 3-5 minutes early

---

## TIMING: T-0 (DEMO TIME)

### Go Time Checklist

**Right Before You Start:**

- [ ] **Welcome Everyone**
  - Greet attendees as they join
  - Small talk while waiting for everyone
  - Professional and friendly

- [ ] **Check Attendance**
  - Note who is in the meeting
  - Identify decision makers
  - Adjust tone/depth accordingly

- [ ] **Final Tech Check**
  - Audio: "Can everyone hear me OK?"
  - Verify attendee count matches expected
  - Check time: Start on time (respect their schedule)

- [ ] **Begin Screen Share**
  - "Let me share my screen..."
  - Verify they can see it: "Can everyone see the Ignition interface?"
  - Start with confidence

---

**During Demo:**

- [ ] **Watch for Engagement**
  - Are they asking questions? (good)
  - Are they taking notes? (good)
  - Are they looking at phones? (bad - adjust)

- [ ] **Track Timing**
  - Glance at timer periodically
  - Adjust pace if ahead or behind
  - Hit key checkpoints (see demo_script.md)

- [ ] **Handle Issues Calmly**
  - If something breaks, stay calm
  - Use backup plan (see backup_plan.md)
  - Never apologize excessively - maintain confidence

---

## CONTINGENCY CHECKLIST

**If Something Goes Wrong:**

**Scenario: Genie Response Slow/Timeout**
- [ ] Click retry button
- [ ] While waiting, explain what response typically shows
- [ ] If still fails, switch to backup video
- [ ] Say: "Let me show you a pre-recorded version of the exact same query"

**Scenario: Perspective Won't Load**
- [ ] Refresh browser (F5)
- [ ] If still fails, switch to backup video immediately
- [ ] Say: "The demo environment is having a connectivity issue - let me show the pre-recorded session"

**Scenario: Tags Not Updating**
- [ ] Check Gateway status quickly
- [ ] If stopped, say: "The simulation paused - not a problem, I can show with the current data"
- [ ] Or restart simulation: "Give me 30 seconds to restart the data feed"

**See backup_plan.md for full recovery procedures**

---

## POST-DEMO CHECKLIST

**Immediately After:**

- [ ] **Thank Everyone**
  - Thank them for their time
  - Ask what resonated most
  - Gauge interest level

- [ ] **Schedule Follow-Up**
  - Propose next steps based on interest
  - Get calendar invite sent before you leave the call

- [ ] **Send Follow-Up Email**
  - Within 24 hours
  - Include customer handout
  - Include ROI calculator if discussed

- [ ] **Debrief Yourself**
  - What went well?
  - What would you change?
  - Update demo script with learnings

---

## QUICK REFERENCE

**Emergency Contacts:**
- Technical Support: [Phone]
- Databricks Admin: [Name/Contact]
- Account Executive: [Name/Contact]

**Key URLs:**
- Ignition Gateway: http://localhost:8088
- Perspective HMI: [URL]
- Databricks Workspace: [URL]
- Backup Video: [URL or local path]

**Key Credentials:**
- Databricks: [User]
- Ignition: [User]

---

## CHECKLIST SUMMARY

**30 Min Before:**
- [ ] All systems warm and tested
- [ ] Fault injected and visible
- [ ] End-to-end test completed successfully

**15 Min Before:**
- [ ] Computer prepared (notifications off, apps closed)
- [ ] Screen share tested
- [ ] Backup materials ready

**5 Min Before:**
- [ ] Mental preparation
- [ ] Final environment check
- [ ] Join meeting early

**0 Min (Go Time):**
- [ ] Start with confidence
- [ ] Track timing
- [ ] Handle issues calmly

---

**You're ready. Good luck with your demo!**
