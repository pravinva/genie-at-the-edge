# RALPH WIGGUM WORKSTREAM: MINING OPERATIONS GENIE DEMO
## Architecture Overview & System Design

**Project:** Conversational AI for Mining Operations (Genie embedded in Ignition)
**Goal:** Sub-5-second natural language insights for operators
**Timeline:** 2 weeks to working demo
**Quality Bar:** Production-ready, Databricks + Perspective native styling

---

## SYSTEM ARCHITECTURE

```

  OPERATOR WORKSTATION (Browser)                             
    
    IGNITION PERSPECTIVE SESSION                           
      
      LEFT: Equipment      RIGHT: Genie Chat           
      - Live dashboards    - Embedded iframe           
      - Tag bindings       - Calls Databricks API      
      - Alarms             - Chat interface            
      
    

                           
          
                                           
          ↓ Tag updates via Zerobus        ↓ API calls
    
  IGNITION GATEWAY             DATABRICKS WORKSPACE        
           
   Memory Tags                ZEROBUS INGESTION       
   - 15 equipment             Stream: mining_ot       
   - Real-time values > Target: bronze table    
           
                     ↓               
   Timer Scripts               
   - Physics sim              DLT REAL-TIME MODE      
   - Fault injection          Bronze→Silver→Gold      
   - 1000ms interval          Latency: <1s            
           
                     ↓               
   Zerobus Module              
   - Watches tags             DELTA TABLES (Gold)     
   - Batches events           - equipment_perf        
   - POSTs to DB              - production_metrics    
          - ml_predictions        
           
   Perspective Module                    ↓               
   - Views                     
   - Components               GENIE SPACE             
   - Session mgmt             Warehouse: 4b99...      
          Queries gold tables     
        
                                              ↓               
                                    
                                   CHAT UI (Static HTML)   
                                   Hosted in /files/       
                                   Calls Genie API         
                                    
                                
```

---

## DATA FLOW

**Generation → Insight (End-to-End):**

```
T=0.0s    Timer script updates memory tag (CR_002.Vibration = 42.3)
            ↓
T=0.5s    Zerobus module detects change, batches with other tags
            ↓ POST JSON to Databricks
T=1.0s    Zerobus writes to bronze Delta table
            ↓ DLT Real-Time Mode stream
T=1.5s    Silver table updated (normalized, enriched)
            ↓ Aggregate
T=2.0s    Gold table updated (analytics-ready)
            ↓ Available for query
          [OPERATOR NOTICES ALARM, CLICKS "ASK AI"]
            ↓
T=10.0s   Operator clicks button, question pre-filled in chat
            ↓
T=11.0s   Operator presses Enter, Genie API called
            ↓ Generate SQL
T=13.0s   SQL Warehouse executes query on gold tables
            ↓ Format response
T=15.0s   Operator sees natural language answer with context


TOTAL: ~15 seconds from physical event to operator insight
Data freshness: 2 seconds (Real-Time Mode)
Query latency: 4 seconds (Genie + warehouse)
```

---

## TECHNOLOGY STACK

**Ignition Components:**
- Platform: Ignition 8.3+
- Modules Required:
  - Perspective (HMI/visualization)
  - Tag Historian (optional, for demo can use memory tags)
  - Alarm Notification (native alarms)
  - Your Zerobus module (data egress)
- Languages: Python (Jython for scripts), JSON (config)

**Databricks Components:**
- Workspace: Field Engineering (your workspace)
- Catalog: field_engineering
- Schema: mining_demo
- SQL Warehouse: 4b9b953939869799 (Serverless, Photon-enabled)
- Runtime: DBR 16.4+ (for Real-Time Mode)
- Features Used:
  - Zerobus (streaming ingestion)
  - Delta Live Tables with Real-Time Mode
  - Unity Catalog (data governance)
  - Genie (conversational AI)
  - SQL Warehouse (query execution)

**UI Framework:**
- Chat UI: React (via CDN, no build process)
- Styling: Custom CSS matching Perspective dark theme
- Charts: Chart.js (via CDN)
- Icons: Lucide React or Unicode emojis
- Single HTML file (~300-400 lines total)

---

## COMPONENT DIAGRAM

```
IGNITION LAYER:
 Data Generation (Gateway Scripts)
   Outputs: Memory tag updates (1 Hz)
 Data Egress (Zerobus Module)
   Outputs: JSON batches to Databricks
 Visualization (Perspective Views)
   Outputs: Rendered HMI in browser
 Integration (Embedded Frame)
    Outputs: iframe loading Databricks UI

DATABRICKS LAYER:
 Ingestion (Zerobus API)
   Outputs: Bronze Delta table
 Processing (DLT Pipelines)
   Outputs: Silver + Gold Delta tables
 Intelligence (Genie + ML)
   Outputs: Natural language responses
 Interface (Static HTML)
    Outputs: Chat UI in iframe
```

---

## INTEGRATION POINTS

**1. Ignition Memory Tags → Databricks Delta:**
- Protocol: HTTPS POST
- Format: JSON batches
- Frequency: ~1-2 batches/second (500ms batching)
- Module: Zerobus connector (your existing work)

**2. Perspective View → Genie Chat:**
- Method: Embedded iframe with URL parameters
- Communication: URL params for questions, postMessage for future
- Refresh: URL update triggers iframe reload

**3. Alarms → Chat Pre-fill:**
- Trigger: Button onClick in alarm table
- Action: Update view.custom.pending_question property
- Result: iframe URL binding reacts, reloads with question

**4. Genie → Databricks Tables:**
- API: Databricks Genie REST API
- Auth: Bearer token (PAT or service principal)
- Warehouse: Executes SQL queries
- Response: Natural language + optional SQL/data/charts

---

## SECURITY MODEL

**Authentication:**
- Ignition: Standard user authentication
- Databricks: PAT token stored in Ignition session custom property
- Genie chat: Receives token via URL parameter
- Network: HTTPS only, no unencrypted traffic

**Data Flow:**
- Outbound: Ignition → Databricks (Zerobus HTTPS POST)
- Inbound: Browser → Databricks (Genie API HTTPS)
- No direct Databricks → Ignition (unidirectional for security)

**OT Network Considerations:**
- Ignition Gateway needs outbound HTTPS (443) to Databricks
- Browser needs outbound HTTPS to both Ignition and Databricks
- Firewall rule required: Allow Ignition gateway IP → *.cloud.databricks.com

---

## PERFORMANCE TARGETS

**Data Freshness:**
- Tag update → Bronze table: <1 second
- Bronze → Gold: <1 second (Real-Time Mode)
- Total: <2 seconds from tag change to queryable

**Query Latency:**
- Operator asks question → Genie responds: <5 seconds
- Breakdown:
  - Genie SQL generation: ~2s
  - SQL Warehouse execution: <1s (with Photon + optimization)
  - Response formatting: ~1s

**UI Responsiveness:**
- Tag updates in Perspective: Real-time (bound to tag changes)
- Chat message send: <100ms to show "typing" indicator
- Smooth animations: 60 FPS target

**Scalability:**
- Equipment: 15 tags × 10 sensors = 150 tag updates/second (demo scale)
- Production: Could handle 10,000+ tags with same architecture
- Concurrent operators: 10-20 asking questions simultaneously

---

## COST ESTIMATE

**Databricks Consumption (Demo):**
- Zerobus ingestion: ~$5-10/month (low volume)
- DLT Real-Time pipeline: ~$20-40/month (continuous)
- SQL Warehouse (Serverless): ~$30-50/month (queries)
- Storage: <$1/month (small dataset)
- **Total: ~$60-100/month**

**Ignition (Already Owned):**
- No additional license needed
- Uses existing modules
- Memory tags are free (no historian license if just demo)

---

## DEPLOYMENT MODELS

**Demo/POC:**
- Run on your Databricks workspace
- Single Ignition gateway (laptop or VM)
- 1-5 operators testing
- Duration: 2-4 weeks pilot

**Production:**
- Dedicated Databricks workspace (or shared production)
- Production Ignition gateway (customer's existing)
- 10-50 operators
- 24/7 availability
- Requires: SLA, support model, security review

---

## SUCCESS METRICS

**Technical:**
-  <5s end-to-end latency (event → insight)
-  <2s data freshness (tag → gold table)
-  99.9% uptime over 24-hour test
-  Zero data loss during network interruptions
-  Graceful degradation if Databricks unavailable

**Functional:**
-  Operator can diagnose issues 10x faster than manual
-  AI responses are accurate (>90% operator satisfaction)
-  Suggested questions are relevant (operator clicks them)
-  No context switching (everything on one screen)

**Business:**
-  Reduces average investigation time from 30min to 30sec
-  Catches predictive failures 2-4 hours early
-  Operators rate experience 8+/10
-  Customer requests production deployment

---

## KNOWN LIMITATIONS

**Current Demo Scope:**
- Mock data (not real PLCs/sensors)
- Simplified ML (anomaly detection, not complex models)
- Single site (doesn't demo multi-site federation)
- English only (no multilingual)
- No voice input yet (planned future)

**Production Gaps (Would Need for Real Deployment):**
- Real PLC/SCADA integration (not memory tags)
- Production ML models (trained on real historical data)
- Security hardening (SSO, network segmentation)
- High availability (failover, redundancy)
- Monitoring/alerting (observability stack)
- Support model (on-call, escalation)

---

## NEXT STEPS AFTER DEMO

**If Customer Validates (Wants Production):**

**Phase 1: Production Pilot (4-6 weeks):**
- Integrate with real Ignition tags (not memory simulation)
- Deploy on customer's network (security review)
- Train ML on real historical data
- 5-10 operator pilot group

**Phase 2: Scale (2-3 months):**
- Roll out to all shifts
- Add more equipment types
- Integrate with maintenance system (CMMS)
- Training for operators

**Phase 3: Expand (3-6 months):**
- Multi-site deployment
- Advanced ML models
- Voice interface
- Mobile app integration

---

## FILE STRUCTURE

**This Workstream Contains:**

```
00_Architecture_Overview.txt (this file)
01_Ignition_UDT_Definitions.txt
02_Ignition_Physics_Simulation_Script.txt
03_Ignition_Fault_Injection_Script.txt
04_Ignition_Perspective_View_Spec.txt
05_Databricks_Dimension_Tables.txt
06_Databricks_DLT_RealTime_Pipeline.txt
07_Databricks_Genie_Space_Setup.txt
08_Genie_Chat_UI_Perspective_Styled.txt
09_Integration_Configuration.txt
10_Testing_Plan.txt
11_Build_Sequence.txt
12_Demo_Script.txt
```

**Each file is independent and can be executed separately.**
**Feed files 01-09 to Claude Code/Cursor in sequence.**
**Use 10-12 for validation and presentation.**

---

## WORKSTREAM DEPENDENCIES

```
Day 1-2: Ignition Foundation
   01_UDT_Definitions (no dependencies)
   02_Physics_Simulation (depends on: 01)
   03_Fault_Injection (depends on: 01, 02)

Day 3-4: Databricks Processing
   05_Dimension_Tables (no dependencies, can run parallel)
   06_DLT_Pipeline (depends on: Zerobus data flowing)
   07_Genie_Setup (depends on: 06 - needs gold tables)

Day 5-7: User Interface
   08_Chat_UI (depends on: 07 - needs Genie space ID)

Day 8-9: Integration
   04_Perspective_View (depends on: 01, 08)
   09_Integration_Config (depends on: 04, 08)

Day 10: Testing
   10_Testing_Plan (depends on: all above)

Day 11-12: Demo
   12_Demo_Script (depends on: working system)
```

---

## CRITICAL SUCCESS FACTORS

**Must Have:**
1.  Professional UI quality (matches Perspective/Databricks products)
2.  Sub-5-second latency (fast enough to feel "real-time")
3.  Stable for 24+ hours (no crashes, memory leaks)
4.  Accurate responses (Genie answers are correct)
5.  Easy to demo (one-click startup, reliable)

**Nice to Have:**
- Voice input (future enhancement)
- Multi-language (future)
- Mobile optimization (future)
- Advanced ML models (can start simple)

**Must NOT Have:**
- Buggy UI (broken styling, console errors)
- Slow responses (>10s feels broken)
- Confusing UX (operators shouldn't need training)
- Vendor lock-in (should work with Litmus/DeepIQ too)

---

## RISK MITIGATION

**Risk: Genie responses are inaccurate**
- Mitigation: Well-tuned instructions, good sample questions, test extensively
- Fallback: Operator can verify data manually

**Risk: Latency too high (>10s)**
- Mitigation: Real-Time Mode, Photon, liquid clustering, materialized views
- Fallback: Set expectation that complex queries take longer

**Risk: Network connectivity issues**
- Mitigation: Retry logic, error handling, graceful degradation
- Fallback: Chat shows "Offline - retrying..." with countdown

**Risk: Demo fails during customer presentation**
- Mitigation: Pre-recorded video backup, local test environment
- Fallback: Show video, offer live demo later

**Risk: Customer says "We use Litmus/DeepIQ, not your connector"**
- Mitigation: Position as complementary (works with any ingestion)
- Opportunity: Partnership discussion with Litmus/DeepIQ

---

## INNOVATION HIGHLIGHTS

**What Makes This Novel:**

1. **First for Ignition:** No conversational AI exists for Ignition operators
2. **Lakehouse Integration:** Queries unified IT+OT data (not just local SCADA)
3. **Real-Time Mode:** Sub-second data freshness using latest Databricks capability
4. **Platform Agnostic:** Works with any ingestion (Zerobus, Litmus, DeepIQ)
5. **Production Quality:** Not a toy demo - actual product-level implementation

**Competitive Differentiation:**
- Siemens/Rockwell: Vendor-locked, local data only
- Litmus/DeepIQ: For engineers, not operators
- Us: Universal (Ignition), comprehensive (lakehouse), operator-focused

**L7-Level Indicators:**
- Product integration (OSI PI precedent)
- Partnership ecosystem (Litmus, DeepIQ, Inductive)
- Strategic thinking (platform vs point solution)
- Innovation (first in category)
- Reference architecture (reusable pattern)

---

## NEXT FILE

Proceed to: **01_Ignition_UDT_Definitions.txt**

This file contains detailed specifications for creating the Ignition tag structure that will generate realistic mining equipment data.
