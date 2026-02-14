# RALPH WIGGUM WORKSTREAM - FILE 10
## Comprehensive Testing Plan

**Purpose:** Validate system quality before customer demo
**Scope:** End-to-end functional, performance, and UX testing
**Owner:** You + QA reviewer (if available)
**Timeline:** Day 10, 4-6 hours

---

## TEST CATEGORIES

```
1. FUNCTIONAL TESTING
   > Does everything work as designed?

2. PERFORMANCE TESTING  
   > Is latency acceptable (<5s)?

3. STABILITY TESTING
   > Does it run 24 hours without crashes?

4. UX TESTING
   > Does UI match Perspective quality?

5. INTEGRATION TESTING
   > Do all components work together?

6. FAILURE TESTING
   > What happens when things break?
```

---

## TEST SUITE 1: FUNCTIONAL

**Test 1.1: Tag Simulation**

```
Objective: Verify Ignition tags update realistically

Steps:
1. Open Tag Browser, watch tags for 5 minutes
2. Verify haul truck cycle: loading → hauling → dumping → returning
3. Check crusher values are stable (if no fault)
4. Verify conveyor load oscillates
5. Check no NaN, Infinity, or nonsense values

Pass Criteria:
 All 105 tags updating every second
 Values within expected ranges
 Truck completes full cycle in 23 minutes
 No errors in Gateway logs

Fail: Values stuck, unrealistic, or errors present
```

**Test 1.2: Zerobus Ingestion**

```
Objective: Data reaches Databricks bronze table

Steps:
1. Wait 2-3 minutes after Ignition starts
2. Query bronze table:
   SELECT count(*), max(ingestion_timestamp) 
   FROM field_engineering.mining_demo.ot_telemetry_bronze;
3. Should see: Record count increasing, recent timestamp
4. Verify 15 distinct equipment IDs present
5. Check JSON structure is valid (no parse errors)

Pass Criteria:
 Records accumulating (>100/minute expected)
 All 15 equipment IDs present
 Timestamps are current (within last minute)
 JSON is valid (no _rescued_data)

Fail: No data, missing equipment, old timestamps, malformed JSON
```

**Test 1.3: DLT Real-Time Processing**

```
Objective: Pipeline processes in <3 seconds

Steps:
1. Note current time: T0
2. Manually change tag: CR_002.Vibration_MM_S = 45
3. Query gold immediately:
   SELECT * FROM field_engineering.mining_demo.equipment_performance_1min
   WHERE equipment_id = 'CR_002' 
     AND sensor_name = 'Vibration_MM_S'
   ORDER BY window_start DESC LIMIT 1;
4. Record time when new value appears: T1
5. Calculate: T1 - T0

Pass Criteria:
 Data appears in gold within 3 seconds
 Value is correct (45 or aggregated value containing 45)
 No processing errors in DLT UI

Fail: Data takes >5s, values incorrect, pipeline errors
```

**Test 1.4: Genie Query Accuracy**

```
Objective: Genie returns correct, relevant answers

Test Questions (Run all 10):

Q1: "Show current status of all crushers"
Expected: Table or list with CR_001, CR_002, CR_003 current values
Actual: ___________
PASS/FAIL: ___

Q2: "Why is Crusher 2 vibration high?"  
Expected: Mentions current value, comparison to normal, possible cause
Actual: ___________
PASS/FAIL: ___

Q3: "Compare Crusher 2 to other crushers"
Expected: Table comparing CR_001, CR_002, CR_003 metrics
Actual: ___________
PASS/FAIL: ___

Q4: "Show production for last hour"
Expected: Tonnage summary for recent period
Actual: ___________
PASS/FAIL: ___

Q5: "Which equipment has anomalies?"
Expected: Lists equipment from ml_predictions table
Actual: ___________
PASS/FAIL: ___

Q6: "What happened on January 15?"
Expected: Details from maintenance_history about past incident
Actual: ___________
PASS/FAIL: ___

Q7: "Show fuel consumption by haul truck"
Expected: Comparative data for HT_001 to HT_005
Actual: ___________
PASS/FAIL: ___

Q8: "What's the efficiency of Haul Truck 3?"
Expected: Specific metrics for HT_003
Actual: ___________
PASS/FAIL: ___

Q9: "How many hours until Crusher 2 needs maintenance?"
Expected: Prediction or calculation based on runtime/schedule
Actual: ___________
PASS/FAIL: ___

Q10: "Show me equipment in Pit 2"
Expected: Filtered list based on location dimension
Actual: ___________
PASS/FAIL: ___

Pass Criteria:
 8/10 questions answered correctly and helpfully
 Responses use proper mining terminology
 SQL generated is sensible (check query performance tab)
 No hallucinations (answers must be based on data)

Fail: <7/10 correct, nonsense answers, hallucinations
```

**Test 1.5: Alarm-to-Chat Integration**

```
Objective: "Ask AI" button pre-fills chat correctly

Steps:
1. Trigger alarm: Set CR_002.Vibration_MM_S = 50
2. Wait for alarm to appear in table
3. Click  button in alarm row
4. Verify chat input pre-fills with question
5. Press Enter, verify Genie responds relevantly
6. Response should reference the specific alarm

Pass Criteria:
 Button click pre-fills question correctly
 Question mentions correct equipment and alarm
 Genie response is relevant to alarm
 Process feels smooth (<2s to pre-fill)

Fail: Question doesn't pre-fill, wrong equipment, Genie confused
```

---

## TEST SUITE 2: PERFORMANCE

**Test 2.1: End-to-End Latency (Detailed)**

```
Measure each component:

Component 1: Tag Update → Bronze
  Method: Tag change timestamp vs bronze ingestion_timestamp
  Query: SELECT ingestion_timestamp, event_timestamp,
         TIMESTAMPDIFF(SECOND, event_timestamp, ingestion_timestamp) as latency
         FROM bronze WHERE equipment_id='CR_002' ORDER BY event_timestamp DESC LIMIT 10;
  Target: <1 second
  Actual: ___ seconds
  PASS/FAIL: ___

Component 2: Bronze → Gold (DLT latency)
  Method: Check pipeline_quality_metrics table
  Query: SELECT avg(max_latency_sec) FROM pipeline_quality_metrics
         WHERE minute > CURRENT_TIMESTAMP - INTERVAL '10 minutes';
  Target: <2 seconds
  Actual: ___ seconds
  PASS/FAIL: ___

Component 3: Genie Query Execution
  Method: Time Genie response in UI
  Use stopwatch: Question submitted → Answer displayed
  Target: <5 seconds
  Actual: ___ seconds (average of 5 tests)
  PASS/FAIL: ___

Total End-to-End:
  Sum of above: ___ seconds
  Target: <8 seconds
  PASS/FAIL: ___
```

**Test 2.2: Concurrent User Load**

```
Objective: Multiple operators asking questions simultaneously

Steps:
1. Open 3-5 browser sessions (different operators)
2. All ask questions at same time
3. Verify:
   - All get responses
   - No rate limiting errors
   - Latency doesn't spike significantly
   - Responses are correct (not mixed up between users)

Pass Criteria:
 All sessions get responses within 10s
 No errors or timeouts
 SQL Warehouse handles load without cold start

Fail: Timeouts, errors, responses take >15s
```

**Test 2.3: Cold Start Behavior**

```
Objective: Test when SQL Warehouse is stopped

Steps:
1. Stop SQL Warehouse manually
2. Wait 5 minutes
3. Open Perspective session, ask question
4. Measure time to first response (includes warehouse startup)

Expected: First query takes 30-60s (cold start)
Subsequent queries: <5s

Deliverable: Document cold start behavior, plan for demo
(Keep warehouse running during demo to avoid this)
```

---

## TEST SUITE 3: STABILITY

**Test 3.1: 24-Hour Soak Test**

```
Objective: System runs continuously without degradation

Setup:
1. Start Ignition simulation
2. Start DLT pipeline
3. Open Perspective session (keep browser open)
4. Let run for 24 hours

Monitor every 4 hours:
- Ignition Gateway: CPU, memory, logs for errors
- Databricks: DLT pipeline still processing, no errors
- Browser: Memory usage stable, no leaks

Automated checks:
- Query gold table every hour, verify recent data
- Count bronze records every hour, should be ~216,000/hour (60 records/min * 60 min * 60 records/batch)

Pass Criteria:
 Ignition runs 24 hours, <5% CPU, no errors
 DLT pipeline processes continuously, no failures
 Browser memory stable (<500MB after 24h)
 Chat still responsive after 24 hours

Fail: Crashes, memory leaks, data gaps, errors
```

**Test 3.2: Network Interruption Recovery**

```
Objective: Graceful handling of network issues

Steps:
1. Disconnect network (unplug ethernet or disable WiFi)
2. Try asking question in chat
3. Verify error message is helpful
4. Reconnect network
5. Click retry button
6. Verify recovers and works

Pass Criteria:
 Shows clear error: "Network error - check connection"
 Retry button appears
 After reconnect, retry works
 No data loss (Ignition → Databricks has buffer)

Fail: Silent failure, confusing error, data lost
```

---

## TEST SUITE 4: USER EXPERIENCE

**Test 4.1: Visual Quality Audit**

```
Comparison: Side-by-side Perspective vs Genie Chat

Checklist:
 Colors match exactly (use color picker to verify)
 Fonts are identical (Inter for body, Roboto Mono for code)
 Spacing follows 8px grid system
 Border radius matches (4px)
 Shadows are subtle and consistent
 Buttons look like Perspective buttons
 Inputs look like Perspective inputs
 Dark theme is cohesive (no light theme elements)

Get second opinion: Show to Ignition developer, ask:
"Does this look like a native Perspective component?"

Pass Criteria:
 Indistinguishable from Perspective native components
 Professional, polished appearance
 No obvious style mismatches

Fail: Looks "hacked together", colors off, unprofessional
```

**Test 4.2: Interaction Smoothness**

```
UX checklist:

Animations:
 Messages slide in smoothly (no jank)
 Typing indicator animates at 60 FPS
 Scroll is smooth (no stuttering)
 Button hovers have subtle transitions
 No layout shift when content loads

Response times:
 Button click feedback: Instant (<100ms)
 Typing shows in input: Instant
 Send button becomes disabled: Instant
 Typing indicator appears: <200ms
 Scroll to new message: <300ms

Pass Criteria:
 All interactions feel instant and smooth
 60 FPS maintained during animations
 No perceived lag or jank

Fail: Laggy, stuttering, unresponsive feeling
```

**Test 4.3: Accessibility**

```
Use browser accessibility tools:

1. Chrome DevTools > Lighthouse > Accessibility audit
   Target: Score >90
   
2. Keyboard navigation:
   - Tab through all focusable elements
   - Focus indicators clearly visible
   - Enter to send, Escape to clear
   
3. Screen reader (optional but recommended):
   - macOS: VoiceOver
   - Windows: NVDA
   - Verify messages are announced
   
4. Color contrast:
   - Text on background: Ratio >4.5:1
   - Buttons: Clear in all states

Pass Criteria:
 Lighthouse score >90
 Full keyboard navigation
 Focus states clearly visible
 Contrast ratios pass WCAG 2.1 AA

Fail: Score <80, keyboard nav broken, poor contrast
```

---

## TEST SUITE 5: INTEGRATION

**Test 5.1: Ignition ↔ Databricks Data Flow**

```
End-to-end validation:

1. Change Ignition tag: CR_002.Vibration_MM_S = 55
2. Wait 30 seconds
3. Ask Genie: "What's Crusher 2 vibration right now?"
4. Verify response mentions value close to 55

Flow traced:
 Tag change → Zerobus → Bronze (check table)
 Bronze → Silver → Gold (check DLT graph)
 Genie queries gold (check SQL in query history)
 Response reflects recent data (not stale)

Pass: Response shows recent data (<2 min old)
Fail: Response shows old data or wrong value
```

**Test 5.2: Perspective ↔ Chat Communication**

```
Alarm button integration:

1. Trigger alarm manually
2. Verify alarm appears in table
3. Click "Ask AI" button
4. Verify:
    Chat input pre-fills correctly
    Equipment ID is correct
    Alarm type is correct
    Cursor is in input field (ready to edit/send)

Test edge cases:
- Multiple alarms present: Correct alarm selected
- Special characters in alarm name: Properly escaped
- Long alarm names: Truncated or handled

Pass: Button always pre-fills correctly
Fail: Wrong equipment, missing alarm info, doesn't work sometimes
```

**Test 5.3: Real-Time Updates in Perspective**

```
Validate live tag bindings:

1. Watch crusher card in Perspective
2. Observe vibration value updating every second
3. When value crosses 40 threshold:
   - Card should turn red/yellow
   - Alarm banner should appear
   - Status indicator should change

4. Ask Genie about current value
5. Verify answer reflects most recent tag value

Pass: Perspective shows live data, matches Genie responses
Fail: Stale data, bindings not updating, mismatches
```

---

## TEST SUITE 6: FAULT SCENARIO

**Test 6.1: Fault Injection Validation**

```
Full fault scenario (30-40 minutes):

T=0: Start fresh
  - Reset CR_002 to normal (or restart Gateway)
  - Vibration should be ~20 mm/s
  - Status: RUNNING
  
T=30min: Fault begins
  - Vibration starts increasing
  - Throughput starts decreasing
  - Monitor every minute, document progression
  
T=35min: Threshold crossed
  - Vibration exceeds 40 mm/s
  - Alarm fires
  - Alarm appears in table
  
T=36min: Operator investigates
  - Click "Ask AI" button
  - Question pre-fills
  - Send to Genie
  - Measure response time
  
T=37min: Diagnosis received
  - Response should mention:
     Current vibration value (>40)
     Comparison to normal (2x baseline)
     Pattern match (Jan 15 incident if in data)
     Recommendation (inspect belt)
  
T=40min: Severe fault state
  - Vibration oscillating 55-65 mm/s
  - Status: FAULT
  - Throughput severely reduced

Pass Criteria:
 Fault progresses realistically over 10 minutes
 Alarm fires at correct threshold
 Genie diagnosis is accurate and helpful
 Complete demo story flows smoothly

Fail: Fault doesn't trigger, alarm doesn't fire, Genie gives irrelevant answer
```

---

## TEST SUITE 7: FAILURE SCENARIOS

**Test 7.1: Databricks Unavailable**

```
Simulate: Databricks workspace down

Steps:
1. Disconnect from Databricks (block network or use invalid token)
2. Open Perspective session
3. Try asking question
4. Verify error handling:
    Clear error message: "Cannot reach AI assistant"
    Retry button appears
    Perspective view still works (tags update)
    No crashes or white screens

5. Restore connection
6. Click retry
7. Verify: Works again

Pass: Graceful degradation, clear messaging, easy recovery
Fail: Crash, confusing errors, no retry option
```

**Test 7.2: Ignition Gateway Failure**

```
Simulate: Gateway restart

Steps:
1. Note current state (middle of truck cycle, fault active, etc.)
2. Restart Ignition Gateway
3. Wait for restart complete
4. Verify:
    Tags reset to initial values OR resume state (depending on config)
    Simulation resumes automatically
    Zerobus reconnects and sends data
    DLT pipeline continues processing

Pass: System recovers automatically within 2-3 minutes
Fail: Manual intervention needed, data gaps, stuck state
```

**Test 7.3: SQL Warehouse Cold Start**

```
Simulate: Warehouse stopped

Steps:
1. Stop SQL Warehouse manually (Databricks UI)
2. Wait 5 minutes
3. Ask Genie question
4. Measure time to response (includes warehouse startup)

Expected: 30-90 seconds (first query triggers cold start)
Subsequent: <5 seconds

Action Item: Keep warehouse running during demo to avoid this

Deliverable: Document cold start behavior, plan for demo
```

---

## TEST SUITE 8: DEMO REHEARSAL

**Test 8.1: Full Demo Run-Through** (15 minutes)

```
Script: Follow File 12 (Demo Script) exactly

Checklist:
 Introduction flows naturally (2 min)
 Ignition view loads without issues
 Tags are updating visibly
 Fault scenario is at right stage (or can be triggered)
 Alarm fires on cue
 "Ask AI" button works
 Chat responds in <5 seconds
 Follow-up questions work
 Drill-down into SQL/data works if shown
 Architecture explanation is clear
 Business value is compelling
 Q&A handling is confident

Time the demo: Should be 12-15 minutes (leaves buffer for Q&A)

Practice 3 times minimum:
  Run 1: ___ minutes, Issues: ___________
  Run 2: ___ minutes, Issues: ___________
  Run 3: ___ minutes, Issues: ___________

Pass: Demo flows smoothly, <15 minutes, no awkward pauses
Fail: Stumbling, takes >18 minutes, technical issues
```

**Test 8.2: Backup Plan Validation**

```
If live demo fails:

1. Test video playback:
   - Pre-recorded demo video loads
   - Audio is clear
   - Quality is professional

2. Test screenshot walkthrough:
   - All key screenshots captured
   - Readable on projector/screen share
   - Narrative makes sense without live system

3. Test offline mode (if implemented):
   - Chat UI with demo responses
   - Looks real even though not connected
   - Good enough to show UX even if backend fails

Pass: Have working backup that's 80% as compelling as live
Fail: No backup, or backup is poor quality
```

---

## TEST SUITE 9: CUSTOMER-SPECIFIC

**Test 9.1: WA Mining Customer Questions**

```
Anticipate customer questions:

Technical:
Q: "How do we integrate with our existing Ignition?"
A: [Prepare answer about Zerobus module or Lakeflow SQL]

Q: "What if we use Litmus Edge instead?"
A: [Position as complementary, works with any ingestion]

Q: "Can this work with our OSI PI data?"
A: [Yes, via your OSI PI connector]

Q: "How much does this cost?"
A: [Databricks consumption estimate: $60-100/month for pilot]

Q: "What's the latency in production?"
A: [<5s for most queries, demo shows ~4s]

Q: "Is our data secure?"
A: [Unity Catalog, encryption, compliance certifications]

Business:
Q: "What's the ROI?"
A: [30min manual → 30s with AI = 60x faster, $XX savings/year]

Q: "How long to deploy?"
A: [Pilot: 4-6 weeks, Production: 2-3 months]

Q: "Do our operators need training?"
A: [Minimal - if they can type, they can use it]

Deliverable: Confident answers to likely questions
```

---

## PERFORMANCE BENCHMARKS

**Target Metrics (Document Actuals):**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Tag update → Bronze | <1s | ___s | PASS/FAIL |
| Bronze → Gold (DLT) | <2s | ___s | PASS/FAIL |
| Genie query response | <5s | ___s | PASS/FAIL |
| **Total end-to-end** | **<8s** | **___s** | **PASS/FAIL** |
| Concurrent users (5) | <10s | ___s | PASS/FAIL |
| 24-hour uptime | 99%+ | __% | PASS/FAIL |
| Browser memory (4h) | <500MB | ___MB | PASS/FAIL |
| CPU (Ignition Gateway) | <10% | __% | PASS/FAIL |

**Overall System Grade: _____ (A/B/C/F)**
- A: All metrics pass, demo-ready
- B: Minor issues, acceptable with caveats
- C: Significant issues, needs work before demo
- F: Major failures, not ready

---

## BUG TRACKING

**Issues Found During Testing:**

| ID | Severity | Description | Component | Status | Fix |
|----|----------|-------------|-----------|--------|-----|
| 1 | High | Example: Genie timeout after 30s | Chat UI | Open | Add timeout handling |
| 2 | Medium | Example: Alarm button sometimes doesn't pre-fill | Perspective | Fixed | Updated onClick script |
| 3 | Low | Example: Suggested questions off-screen on narrow display | Chat UI | Won't Fix | Rare case |

**Severity Levels:**
- **High:** Breaks demo, must fix before presenting
- **Medium:** Noticeable but workaround exists
- **Low:** Minor polish, can defer

**Action:** Fix all High before demo, address Medium if time permits

---

## SIGN-OFF CHECKLIST

**Before demo:**

**Functional:**
- [ ] All 10 test questions answered correctly (Test 1.4)
- [ ] Alarm integration works 100% (Test 1.5)
- [ ] Fault scenario flows smoothly (Test 6.1)

**Performance:**
- [ ] End-to-end latency <8s (Test 2.1)
- [ ] Concurrent users supported (Test 2.2)
- [ ] Cold start documented, warehouse will be warm for demo

**Stability:**
- [ ] 24-hour test passed (Test 3.1)
- [ ] Network recovery works (Test 3.2)

**UX:**
- [ ] Visual quality matches Perspective (Test 4.1)
- [ ] Interactions are smooth (Test 4.2)
- [ ] Accessibility score >90 (Test 4.3)

**Demo Prep:**
- [ ] Rehearsed 3+ times successfully (Test 8.1)
- [ ] Backup plan ready (Test 8.2)
- [ ] Customer questions prepared (Test 9.1)

**Sign-off:** _____________________ Date: _____

**System is: READY / NOT READY for customer demo**

---

**Testing time:** 6-8 hours spread across Day 10 + ongoing monitoring
**Next:** File 12 - Polished demo script for customer presentation
