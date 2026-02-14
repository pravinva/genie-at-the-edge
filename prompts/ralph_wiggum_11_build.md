# RALPH WIGGUM WORKSTREAM - FILE 11
## Build Sequence & Task Breakdown

**Purpose:** Day-by-day build plan with independent tasks
**Timeline:** 10 working days to demo-ready system
**Approach:** Parallel tracks where possible, clear dependencies

---

## WORKSTREAM OVERVIEW

```
TRACK A: IGNITION (Days 1-3)
  └─> Creates data generation and visualization

TRACK B: DATABRICKS PROCESSING (Days 2-5)
  └─> Creates data pipeline and analytics

TRACK C: USER INTERFACE (Days 5-8)
  └─> Creates chat interface and integration

TRACK D: INTEGRATION (Days 8-9)
  └─> Connects all pieces

TRACK E: VALIDATION (Day 10)
  └─> End-to-end testing and demo prep
```

---

## DAY 1: IGNITION FOUNDATION

**Goal:** Tag structure created, manual test working

### TASKS (Sequential):

**Task 1.1: Create UDT Definitions** (30 min)
```
File: 01_Ignition_UDT_Definitions.txt
Tool: Ignition Designer > Tag Browser
Output: 3 UDT types created

Steps:
1. Open Ignition Designer
2. Create HaulTruck UDT (14 members)
3. Create Crusher UDT (9 members)
4. Create Conveyor UDT (4 members)
5. Validate structure

Deliverable: UDT types visible in Data Types folder
```

**Task 1.2: Create Tag Instances** (30 min)
```
File: Same as 1.1
Output: 15 equipment tag instances

Steps:
1. Create 5 haul truck instances (HT_001 to HT_005)
2. Create 3 crusher instances (CR_001 to CR_003)
3. Create 2 conveyor instances (CV_001, CV_002)
4. Verify all under [default]Mining/Equipment/

Deliverable: 105 memory tags created (15 equipment × avg 7 tags)
```

**Task 1.3: Configure Alarms** (15 min)
```
Output: High vibration alarm for crushers

Steps:
1. Navigate to CR_002/Vibration_MM_S tag
2. Add alarm: Threshold >40 mm/s, Priority: High
3. Repeat for CR_001, CR_003
4. Test: Manually set vibration to 45, verify alarm fires

Deliverable: Alarms configured and tested
```

**Task 1.4: Manual Tag Update Test** (15 min)
```
Validation test:

1. Right-click CR_001/Vibration_MM_S > Edit Tag
2. Change value from 20 to 35
3. Verify update reflects immediately in Tag Browser
4. Check alarm DOESN'T fire (below 40 threshold)
5. Change to 45, verify alarm DOES fire

Deliverable: Tag system working, alarms functional
```

**Day 1 End State:**
- ✅ Tag structure complete
- ✅ Alarms configured
- ✅ Ready for automation scripts

**Estimated time:** 90 minutes total

---

## DAY 2: IGNITION AUTOMATION + DATABRICKS START

**Goal:** Tags updating automatically, Databricks receiving data

### TRACK A: IGNITION SCRIPTS

**Task 2.1: Physics Simulation Script** (2 hours)
```
File: 02_Ignition_Physics_Simulation_Script.txt
Tool: Claude Code to generate, paste in Gateway
Output: Tags updating every second with realistic values

Steps:
1. Feed File 02 to Claude Code
2. Review generated script
3. Create Gateway Timer Script (Config > Scripting > Timer Scripts)
4. Paste code, set interval: 1000ms
5. Enable and save

Validation:
- Watch HT_001/Speed_KPH in Tag Browser
- Should see value changing every second
- After 5 minutes, should see truck cycle pattern

Deliverable: Realistic simulation running
```

**Task 2.2: Test Simulation** (30 min)
```
Validation:

1. Monitor for 10 minutes
2. Verify haul truck cycles (loading → hauling → dumping → returning)
3. Check crusher values are stable (no fault yet)
4. Verify no errors in Gateway logs
5. Check CPU usage is acceptable

Deliverable: Simulation stable and realistic
```

### TRACK B: DATABRICKS SETUP (Can run parallel to 2.1-2.2)

**Task 2.3: Create Dimension Tables** (30 min)
```
File: 05_Databricks_Dimension_Tables.txt
Tool: Databricks SQL Editor or Notebook
Output: Reference tables created with seed data

Steps:
1. Feed File 05 to Claude Code (generates SQL)
2. Open Databricks SQL Editor
3. Connect to warehouse: 4b9b953939869799
4. Execute generated DDL and INSERT statements
5. Verify tables created

Validation:
SELECT * FROM field_engineering.mining_demo.equipment_master;
-- Should return 15 rows

Deliverable: Dimension tables ready for joins
```

**Task 2.4: Configure Zerobus Stream** (30 min)
```
File: 09_Integration_Configuration.txt (section on Zerobus)
Tool: Databricks UI or API
Output: Zerobus stream endpoint created

Steps:
1. Create Zerobus stream: mining_ot_stream
2. Target table: field_engineering.mining_demo.ot_telemetry_bronze
3. Schema: Auto-infer from JSON
4. Get stream endpoint URL

Deliverable: Stream ready to receive data
```

**Task 2.5: Configure Ignition Zerobus Module** (30 min)
```
Tool: Ignition Gateway > Config > Zerobus (your module)
Output: Ignition sending data to Databricks

Steps:
1. Add Zerobus connection
2. Databricks workspace URL and token
3. Stream name: mining_ot_stream
4. Tag selection: [default]Mining/Equipment/**/* (all equipment tags)
5. Batch size: 50, interval: 500ms
6. Enable and save

Validation:
- Wait 2-3 minutes
- Check Databricks bronze table:
  SELECT count(*) FROM field_engineering.mining_demo.ot_telemetry_bronze;
- Should have hundreds of records

Deliverable: Data flowing Ignition → Databricks
```

**Day 2 End State:**
- ✅ Ignition tags updating realistically every second
- ✅ Databricks receiving data via Zerobus
- ✅ Bronze table populating
- ✅ Ready for DLT pipeline

**Estimated time:** 4-5 hours total (includes waiting for data flow)

---

## DAY 3: FAULT INJECTION + DLT PIPELINE

**Goal:** Fault scenario working, real-time processing operational

**Task 3.1: Fault Injection Script** (1 hour)
```
File: 03_Ignition_Fault_Injection_Script.txt
Tool: Claude Code + Gateway Timer Script
Output: CR_002 degradation simulation

Steps:
1. Feed File 03 to Claude Code
2. Create second Gateway Timer Script
3. Name: "FaultInjection_CR002"
4. Interval: 1000ms, offset: 500ms (runs between physics script)
5. Enable

Validation:
- Wait 30 minutes (or modify script to start at T=60s for testing)
- Watch CR_002/Vibration_MM_S increase gradually
- After fault starts, should go from 20 → 60 over 10 minutes

Deliverable: Fault injection working
```

**Task 3.2: DLT Pipeline Development** (3 hours)
```
File: 06_Databricks_DLT_RealTime_Pipeline.txt
Tool: Claude Code + Databricks Notebook
Output: Real-Time DLT pipeline deployed

Steps:
1. Feed File 06 to Claude Code
2. Review generated pipeline code
3. Create file in Databricks Repos
4. Create DLT pipeline via UI (as specified in File 06)
5. Configure Real-Time Mode

Deliverable: Pipeline created (not started yet)
```

**Task 3.3: Pipeline Testing** (2 hours)
```
Steps:
1. Start DLT pipeline in development mode
2. Watch graph: Bronze → Silver → Gold
3. Monitor latency metrics in UI
4. Run validation queries (from File 06)

Validation:
- Bronze updates: <1s after Ignition tag change
- Silver normalized: <1s after bronze
- Gold aggregated: <1s after silver
- Total: <3s event to gold

Troubleshooting:
- If latency >5s, check shuffle partitions
- If errors, review data quality expectations
- If stuck, try micro-batch mode first

Deliverable: Pipeline running with <3s latency
```

**Day 3 End State:**
- ✅ Fault scenario active (CR_002 degrading)
- ✅ Real-Time pipeline processing in <3s
- ✅ Gold tables ready for Genie queries
- ✅ Ready for Genie space creation

**Estimated time:** 6 hours

---

## DAY 4: GENIE CONFIGURATION

**Goal:** Genie space operational, test queries working

**Task 4.1: Genie Space Creation** (1 hour)
```
File: 07_Databricks_Genie_Space_Setup.txt
Tool: Databricks UI or API
Output: Genie space configured and tested

Steps:
1. Create Genie space via UI
2. Name: "Mining Operations Intelligence"
3. Add gold tables (equipment_performance_1min, ml_predictions, etc.)
4. Configure instructions (from File 07)
5. Add sample questions
6. Set warehouse: 4b9b953939869799

Deliverable: Genie space ID
```

**Task 4.2: Test Genie Queries** (2 hours)
```
Test in Databricks UI > Genie:

Test questions:
1. "Show me current status of all crushers"
2. "Why is Crusher 2 vibration high?"
3. "Compare Crusher 2 to other crushers"
4. "Show production for last hour"
5. "Which equipment has anomalies?"

For each:
- Verify SQL generated is correct
- Verify results are accurate
- Verify natural language response makes sense
- Refine instructions/sample questions if needed

Deliverable: Genie responding accurately to operator questions
```

**Task 4.3: Optimize Genie Space** (1 hour)
```
Tuning:

1. Add more sample questions based on test results
2. Refine instructions for mining terminology
3. Add business glossary terms:
   - OEE, throughput, t/hr, vibration, etc.
4. Test edge cases (unusual questions)
5. Document known limitations

Deliverable: Genie tuned for mining operations domain
```

**Day 4 End State:**
- ✅ Genie space operational
- ✅ Queries return accurate results in <5s
- ✅ Ready for UI integration

**Estimated time:** 4 hours

---

## DAY 5-7: PROFESSIONAL CHAT UI

**Goal:** Production-quality chat interface

**Task 5.1: Generate Initial UI** (2 hours - Day 5)
```
File: 08_Genie_Chat_UI_Perspective_Styled.txt
Tool: Claude Code
Output: First version of HTML file

Steps:
1. Feed entire File 08 to Claude Code
2. Review generated HTML (should be 300-400 lines)
3. Save as: genie_chat_perspective.html
4. Test standalone in browser

Deliverable: Working chat UI (basic functionality)
```

**Task 5.2: Styling Iteration** (4 hours - Day 6)
```
Refinement:

1. Compare side-by-side with Perspective view
2. Adjust colors to EXACT match (use color picker)
3. Fine-tune typography (font sizes, weights, spacing)
4. Perfect component styling (buttons, inputs, messages)
5. Test responsive behavior (resize browser 400px → 1920px)

Deliverable: UI indistinguishable from Perspective native components
```

**Task 5.3: Advanced Features** (4 hours - Day 7)
```
Enhancements:

1. Add data table rendering (if Genie returns tabular data)
2. Add SQL syntax highlighting (simple keyword coloring)
3. Add inline charts (Chart.js for trends)
4. Add copy-to-clipboard for SQL
5. Add suggested questions that make sense
6. Polish animations (smooth, 60 FPS)

Deliverable: Feature-complete, polished UI
```

**Task 5.4: Error Handling & Edge Cases** (2 hours - Day 7)
```
Robustness:

1. Test with invalid token → friendly error
2. Test with network disconnected → retry option
3. Test with malformed Genie response → graceful fallback
4. Test with very long messages → proper text wrapping
5. Add loading states for all async operations

Deliverable: Production-ready error handling
```

**Days 5-7 End State:**
- ✅ Chat UI matches Perspective quality
- ✅ All features working
- ✅ Handles errors gracefully
- ✅ Ready for embedding in Ignition

**Estimated time:** 12 hours across 3 days

---

## DAY 8-9: PERSPECTIVE INTEGRATION

**Goal:** Complete Ignition view with embedded Genie chat

**Task 8.1: Upload Chat UI to Databricks** (15 min - Day 8)
```
File: genie_chat_perspective.html
Destination: Databricks Files

Steps:
1. Databricks UI > Data > Files
2. Create folder: mining-demo
3. Upload genie_chat_perspective.html
4. Get public URL
5. Test URL in browser (should load chat)

Deliverable: Chat accessible via public URL
```

**Task 8.2: Create Perspective View** (3 hours - Day 8)
```
File: 04_Ignition_Perspective_View_Spec.txt
Tool: Ignition Designer > Perspective
Output: MiningOperationsDashboard view

Steps:
1. Create new Perspective view
2. Add containers (header, left panel, right panel)
3. Add equipment status cards (bind to memory tags)
4. Add alarm table
5. Add production metrics
6. Add Embedded Frame for chat (right panel)

Deliverable: View layout complete
```

**Task 8.3: Configure Session Properties** (30 min - Day 8)
```
Tool: Perspective > Session Events > Startup

Create session custom properties:
- databricks_token (from secure storage)
- workspace_id
- genie_space_id
- genie_chat_url (constructed from above)

Deliverable: Session initialized with Databricks config
```

**Task 8.4: Alarm Integration** (2 hours - Day 9)
```
Enhancement: "Ask AI" buttons in alarm table

Steps:
1. Add custom column to alarm table
2. Create AlarmActionsCell embedded view
3. Add button with onClick script
4. Script updates view.custom.pending_question
5. This triggers iframe URL update (via binding)
6. Test: Click button → chat pre-fills question

Deliverable: Alarm-to-chat integration working
```

**Task 8.5: Polish Perspective View** (2 hours - Day 9)
```
Final touches:

1. Adjust spacing, alignment, sizes
2. Add status indicators (online/offline for Databricks)
3. Add breadcrumbs or navigation
4. Ensure responsive (test on different screen sizes)
5. Add tooltips for clarity
6. Test all interactions

Deliverable: Professional Perspective view
```

**Days 8-9 End State:**
- ✅ Complete Ignition Perspective view
- ✅ Chat embedded seamlessly
- ✅ Alarm integration working
- ✅ UI polished and professional

**Estimated time:** 8 hours across 2 days

---

## DAY 10: END-TO-END TESTING & DEMO PREP

**Goal:** Validated system, ready to demo

**Task 10.1: End-to-End Latency Test** (1 hour)
```
Test: Physical event → Operator insight

Method:
1. Open Perspective session
2. Start stopwatch
3. Manually trigger tag change (e.g., set CR_002.Vibration to 45)
4. Watch alarm fire
5. Click "Ask AI" button
6. Wait for Genie response
7. Stop stopwatch when response appears

Target: <15 seconds total (preferably <10s)

Measure:
- Tag change → Bronze: ___ seconds
- Bronze → Gold: ___ seconds  
- Question → Response: ___ seconds
- Total: ___ seconds

Deliverable: Latency documented and acceptable
```

**Task 10.2: Stability Test** (2 hours - run overnight if needed)
```
Long-running validation:

1. Start Perspective session
2. Let run for 2-24 hours
3. Monitor:
   - No browser memory leaks (check browser task manager)
   - No Ignition errors (Gateway logs)
   - DLT pipeline continues processing
   - No data gaps in gold tables

4. Ask 20-30 questions throughout test period
5. Verify all responses are correct

Deliverable: System stable for extended operation
```

**Task 10.3: Fault Scenario Validation** (1 hour)
```
Test the demo story:

1. Start fresh (reset CR_002 to normal, or restart Gateway)
2. Watch for 30 minutes (or whatever fault injection time)
3. Observe fault progression:
   - Vibration increases gradually
   - Alarm fires at threshold (40 mm/s)
   - Operator clicks "Ask AI"
   - Gets diagnosis within 5 seconds
   - Diagnosis mentions pattern match to Jan 15

4. Verify ML predictions table shows anomaly
5. Test follow-up questions work

Deliverable: Demo story flows smoothly
```

**Task 10.4: Create Demo Script** (1 hour)
```
File: 12_Demo_Script.txt
Output: Rehearsed 15-minute demonstration

Outline:
1. Introduction (2 min): Context, problem, solution
2. Live Demo (10 min):
   - Show Perspective view with live equipment
   - Explain data flow (Ignition → Databricks → Genie)
   - Trigger fault or wait for existing fault
   - Show alarm, click "Ask AI"
   - Get instant diagnosis
   - Ask follow-up questions
   - Show latency (emphasize <5s)
3. Technical Architecture (2 min): High-level diagram
4. Business Value (1 min): ROI, time savings
5. Q&A (flexible)

Deliverable: Polished demo narrative
```

**Task 10.5: Backup Planning** (30 min)
```
Prepare for failure scenarios:

1. Record demo video (if live fails)
2. Export Perspective view as backup
3. Screenshot key moments
4. Prepare fallback talking points
5. Test in airplane mode (verify offline behavior)

Deliverable: Backup plan if live demo fails
```

**Day 10 End State:**
- ✅ System validated end-to-end
- ✅ Latency measured and documented
- ✅ Fault scenario rehearsed
- ✅ Demo script polished
- ✅ Ready for customer presentation

**Estimated time:** 5-6 hours

---

## PARALLEL TRACKS (Optional Acceleration)

**If you have help or want to go faster:**

**Track A (Ignition):** Can be done by one person
- Days 1-3: UDTs, scripts, simulation
- Day 8-9: Perspective view

**Track B (Databricks):** Can be done by another person in parallel
- Day 2: Dimension tables, Zerobus setup
- Day 3-4: DLT pipeline
- Day 4: Genie configuration

**Track C (UI):** Can be done by third person or overlap with A/B
- Day 5-7: Chat UI development

**Then converge on Day 8 for integration**

**With 2-3 people: Could compress to 6-7 days instead of 10**

---

## CRITICAL PATH

**Must be sequential (no parallelization):**

```
Day 1: UDTs → Day 2: Scripts → Day 2: Zerobus → Day 3: DLT → Day 4: Genie → Day 5-7: UI → Day 8-9: Integration → Day 10: Testing

Minimum time with perfect execution: 8 days
Realistic with iterations: 10-12 days
With issues/learning: 14 days
```

---

## QUALITY GATES

**Before proceeding to next phase, verify:**

**After Day 2:**
- ✅ Data visible in Databricks bronze table
- ✅ Ignition simulation running error-free
- ✅ Zerobus module configured correctly

**After Day 4:**
- ✅ Gold tables populating
- ✅ Genie returns accurate answers
- ✅ Latency <5s for queries

**After Day 7:**
- ✅ Chat UI matches Perspective styling
- ✅ All features working
- ✅ No console errors

**After Day 9:**
- ✅ Integration works end-to-end
- ✅ Alarm buttons trigger chat
- ✅ Professional appearance

**After Day 10:**
- ✅ Demo rehearsed successfully
- ✅ System stable for 24 hours
- ✅ Backup plan ready

**Don't skip quality gates. Fix issues before proceeding.**

---

## RISK MITIGATION

**Common Issues & Solutions:**

**"Zerobus not sending data":**
- Check: Ignition can reach Databricks (network/firewall)
- Check: Token is valid and has permissions
- Check: Tag selection pattern is correct
- Fix: Test with simpler tag pattern first ([default]Mining/Equipment/CR_001/*)

**"DLT pipeline errors":**
- Check: Runtime version ≥16.4
- Check: JSON schema matches expectation
- Fix: Start with bronze only, add silver/gold incrementally

**"Genie gives bad answers":**
- Check: Instructions are clear
- Check: Sample questions guide behavior
- Fix: Add more context in instructions, refine sample questions

**"Chat UI doesn't load in iframe":**
- Check: URL is accessible from browser (test directly)
- Check: CORS headers allow iframe embedding
- Fix: Host on Databricks Files (not Repos) for simpler access

**"Performance is slow (>10s)":**
- Check: SQL Warehouse is warm (not cold start)
- Fix: Keep warehouse running during demo
- Optimize: Add liquid clustering, materialized views

---

## COMPLETION CRITERIA

**System is demo-ready when:**

- [ ] Ignition simulation runs 24+ hours without errors
- [ ] Data flows Ignition → Databricks in <2s
- [ ] DLT pipeline processes in <1s (bronze → gold)
- [ ] Genie responds in <5s total
- [ ] Chat UI matches Perspective quality exactly
- [ ] Alarm integration works reliably
- [ ] Demo script rehearsed and timed (15 minutes)
- [ ] Backup video recorded (in case live fails)
- [ ] All stakeholders briefed on demo plan
- [ ] Customer environment tested (if demoing at customer site)

---

## HANDOFF TO PRODUCTION (Post-Demo)

**If customer wants to pilot:**

**Phase 1: Production Readiness (2-4 weeks):**
- Replace memory tags with real PLC/SCADA connections
- Train ML models on real historical data
- Security review (SSO, network segmentation)
- Deploy on customer infrastructure
- Operator training

**Phase 2: Scale (2-3 months):**
- Add more equipment types
- Multi-site deployment
- CMMS integration
- Advanced ML models
- Mobile access

---

**This build sequence is realistic, tested, and accounts for iteration time.**
**Follow it and you'll have a working demo in 10 days.**

**Next:** File 10 - Comprehensive testing plan for validation
