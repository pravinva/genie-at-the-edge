# Mining Operations Genie - Customer Presentation Deck

**Version:** 1.0
**Format:** Markdown (convert to PowerPoint/Google Slides as needed)
**Duration:** 15 minutes with live demo embedded
**Audience:** WA Mining Account Teams (SA, AE, Customer)

---

## SLIDE 1: TITLE SLIDE

### Conversational AI for Mining Operations
**Databricks Genie + Ignition SCADA**

*Empowering operators with instant insights*

**Presenter:** Pravin Varma
**Date:** February 2026
**Customer:** [Customer Name]

---

## SLIDE 2: THE PROBLEM

### When Equipment Alarms Go Off, Time Is Lost

**Today's Reality in Mining Control Rooms:**

**Alarm Triggers:** Crusher vibration warning at 2:23 PM

**Operator Must:**
1. Check trend charts across multiple systems (5-8 min)
2. Review alarm history logs (3-5 min)
3. Call maintenance to ask if this happened before (5-10 min)
4. Search SharePoint/paper logs for similar incidents (5-10 min)
5. Assess impact on production (2-5 min)

**Total Investigation Time: 20-30 minutes**

**Meanwhile:**
- Equipment continues degrading
- Production slows or stops
- Costs accumulate
- Operator stress increases

**Critical Question:** *What if operators could get answers in 5 seconds?*

---

## SLIDE 3: THE SOLUTION

### Conversational AI Embedded in Control Interface

**Architecture Overview:**

```
┌─────────────────┐
│  Ignition SCADA │ ─────► Real-time streaming
└─────────────────┘
         │
         │ Zerobus Connector
         ▼
┌─────────────────┐
│   Databricks    │ ─────► Real-Time Processing (< 1 sec)
│   Lakehouse     │        Medallion Architecture
└─────────────────┘        Bronze → Silver → Gold
         │
         │ Unified Data
         ▼
┌─────────────────┐
│  Genie AI       │ ─────► Natural Language Queries
│  Assistant      │        Historical Context
└─────────────────┘        Predictive Insights
         │
         │ Embedded Chat
         ▼
┌─────────────────┐
│  Perspective    │ ─────► Operators get answers
│  HMI Interface  │        No app switching
└─────────────────┘        Single pane of glass
```

**Key Innovation:** AI assistant lives IN the control interface, not as a separate tool.

---

## SLIDE 4: WHAT MAKES THIS UNIQUE

### Three Core Differentiators

**1. Real-Time Intelligence**
- Sub-second data ingestion from SCADA
- Spark Real-Time Mode (not batch, not micro-batch)
- Queryable within 1 second of physical event
- Operators act on current data, not stale snapshots

**2. Unified Lakehouse**
- Not just SCADA tags (vibration, temperature, RPM)
- PLUS maintenance work orders
- PLUS parts inventory and costs
- PLUS shift logs and operator notes
- PLUS historical incidents and root causes
- **Complete operational context in one query**

**3. Platform-Agnostic Integration**
- Works with Ignition (Inductive Automation)
- Works with Litmus Edge, DeepIQ, Databricks Lakeflow
- Not locked to Siemens or Rockwell ecosystems
- Use what you already have

---

## SLIDE 5: LIVE DEMO

### See It In Action

**Demo Environment:**
- Ignition Perspective HMI
- 5 Haul Trucks, 3 Crushers, 2 Conveyors
- Real-time sensor data streaming
- Genie AI embedded in interface

**Demo Scenarios:**

**1. Alarm Investigation (4 min)**
- Crusher 2 high vibration alarm
- Click "Ask AI" button
- Get answer in 5 seconds
- Historical context: Similar incident from January 15
- Recommendation: Inspect belt immediately

**2. Follow-Up Questions (2 min)**
- "What happened on January 15?"
- "$45K lost production + $8K maintenance"
- "Compare Crusher 2 to other crushers"
- "Only Crusher 2 affected - isolated issue"

**3. Proactive Analysis (2 min)**
- "Show me haul trucks with lowest efficiency today"
- Truck 3 underperforming at 72% vs 89% fleet average
- Catch issues before they become failures

**[PAUSE FOR LIVE DEMO - Switch to Perspective View]**

---

## SLIDE 6: QUANTIFIED BUSINESS VALUE

### ROI Calculator - Conservative Estimates

**Time Savings:**
- Investigation time: **30 minutes → 30 seconds** (60x faster)
- 10 operators × 5 investigations/shift = 50 investigations
- Time saved: **~25 hours per shift**
- Monthly: **750 hours of operator productivity**

**Downtime Prevention:**
- Unplanned crusher downtime: **$10-50K per hour**
- Prevent just **3 events per year** (2 hours each)
- Savings: **$180,000 annually**

**Decision Quality:**
- Historical context on every query (AI remembers all incidents)
- Cross-equipment pattern detection (50+ assets analyzed)
- Predictive warnings: **2-4 hours early detection**

**Total Annual Value: ~$230,000**

**Investment:**
- Databricks platform: ~$60-100K/year (consumption-based)
- Implementation: ~$20-30K one-time
- **Total Year 1: ~$110,000**

**Payback Period: 6 months**

---

## SLIDE 7: TECHNICAL ARCHITECTURE DEEP DIVE

### For Technical Stakeholders

**Data Flow:**

**Layer 1: Ingestion**
- Ignition → Zerobus Connector → Databricks
- Tag changes streamed in real-time
- Alarms, events, batch data included

**Layer 2: Processing**
- Spark Structured Streaming (Real-Time Mode)
- Medallion Architecture:
  - **Bronze:** Raw ingestion (schema validation)
  - **Silver:** Cleansed + enriched (joins, aggregations)
  - **Gold:** Business-ready (optimized for analytics)

**Layer 3: Intelligence**
- Genie AI queries Gold tables
- Natural language → SQL translation
- Context-aware (understands equipment, relationships)
- Streaming + historical unified

**Layer 4: Delivery**
- Embedded chat via Perspective WebDev
- Iframe integration (seamless UX)
- Response in 3-6 seconds typical

**Security:**
- HTTPS only (outbound to Databricks)
- Role-based access control (RBAC)
- No PLC control (read-only queries)
- Audit logs on all queries

---

## SLIDE 8: COMPETITIVE LANDSCAPE

### How We Compare

**vs Siemens Industrial Copilot:**
- **Siemens:** Locked to Siemens PLCs/SCADA ($$$)
- **Us:** Platform-agnostic, works with Ignition

**vs Rockwell FactoryTalk Hub + AI:**
- **Rockwell:** Rockwell ecosystem only
- **Us:** Any integration method (Litmus, DeepIQ, native)

**vs Litmus Edge / DeepIQ:**
- **Litmus/DeepIQ:** Data integration layer (excellent at getting data to cloud)
- **Us:** Complementary - we add conversational AI on top
- **Together:** Best of both worlds

**vs Traditional SCADA Historians (OSI PI, Ignition Historian):**
- **Historians:** Store data, require SQL/expert knowledge to query
- **Us:** Natural language queries, no technical skills needed

**Unique Position:**
- Only solution bringing **Databricks Genie to Ignition**
- Only solution with **unified OT + IT + business lakehouse**
- Only solution with **true real-time + historical unified**

---

## SLIDE 9: CUSTOMER SUCCESS STORY (PLACEHOLDER)

### Early Adoption Results

**[Note: Use actual customer data when available]**

**Pilot Site:** [Customer Name], [Location]
**Duration:** 4 weeks
**Scope:** Crushing circuit (3 crushers, 10 operators)

**Results:**

**Time Savings:**
- Average investigation: 28 min → 45 seconds
- Operator feedback: "Saves me hours every shift"

**Downtime Prevented:**
- 2 potential failures caught early
- Estimated savings: $87,000

**Adoption Rate:**
- Week 1: 3/10 operators using
- Week 4: 10/10 operators using daily
- Most common query: Equipment troubleshooting

**Operator Quotes:**
- *"It's like having a 20-year veteran on call 24/7"*
- *"I don't know how we operated without this"*
- *"The follow-up questions are a game changer"*

**Expansion Plans:**
- Expanding to haul truck fleet (Week 5-8)
- Adding predictive maintenance queries (Week 9-12)

---

## SLIDE 10: IMPLEMENTATION ROADMAP

### 4-Week Pilot Plan

**Week 1-2: Installation & Configuration**

**Tasks:**
- Install Zerobus connector on Ignition Gateway
- Configure firewall rule (outbound HTTPS)
- Set up Databricks workspace and DLT pipeline
- Configure Genie space with mining operations context
- Test end-to-end data flow

**Deliverables:**
- Live system with 1 processing area (crushers or haul trucks)
- 5-10 operators granted access
- Training materials created

**Your Investment:** Firewall access, Ignition read-only access, designated operators

---

**Week 3-4: Operator Testing**

**Activities:**
- Daily operator use in production environment
- Daily feedback sessions (15 min standup)
- Track usage metrics (queries per shift, time saved)
- Iterate on Genie instructions based on feedback

**Metrics:**
- Number of queries per operator
- Average response time
- Time saved per investigation
- Operator satisfaction score (1-10)

**Your Investment:** Operator time (minimal - using in normal workflow)

---

**Week 5: Evaluation & Decision**

**Review Session:**
- Present quantified results (time saved, incidents prevented)
- Operator testimonials
- ROI analysis (actual vs projected)
- Decision: Expand, adjust, or conclude

**Options:**
- **Expand:** Roll out to additional areas (haul trucks, conveyors, etc.)
- **Enhance:** Add more data sources (CMMS, ERP, lab data)
- **Scale:** Deploy across multiple sites

**Your Investment:** Decision on next phase

---

## SLIDE 11: WHAT WE NEED FROM YOU

### Pilot Prerequisites

**Access Requirements:**

**1. Ignition Gateway Access (Read-Only)**
- Firewall rule: Outbound HTTPS to Databricks (port 443)
- Gateway admin access for connector installation
- Tag browsing permissions
- Estimated time: 2 hours setup

**2. Stakeholder Engagement**
- 5-10 operators willing to test (your champions)
- Operations manager as sponsor
- IT/OT contact for firewall/security questions
- Weekly 30-min check-in meetings

**3. Data Sources (Initially)**
- Crusher vibration, temperature, RPM tags (20-30 tags)
- Alarm history (last 6-12 months)
- Shift logs or production reports (optional but valuable)

**4. Expectations**
- This is a pilot - learning and iteration expected
- Honest feedback (positive and negative)
- Willingness to expand if value proven

**What We Handle:**
- All technical setup and configuration
- Operator training (15-30 min sessions)
- Support during pilot period
- Results analysis and reporting

---

## SLIDE 12: RISK MITIGATION

### Addressing Common Concerns

**Concern: "What if AI gives wrong advice?"**

**Response:**
- AI is decision support, not autonomous control
- Operators verify recommendations before acting
- Responses show underlying data and confidence scores
- No PLC control - read-only queries only

**Mitigation:** Start with non-critical systems, build trust gradually

---

**Concern: "Network/system downtime - single point of failure?"**

**Response:**
- Ignition continues normal operation if Databricks unreachable
- Alarms, dashboards, control all independent
- Chat shows "offline" status, retries automatically
- Degraded mode: Everything works except AI assistant

**Mitigation:** Architecture designed for resilience, not dependency

---

**Concern: "Our IT security won't approve cloud connectivity"**

**Response:**
- Outbound HTTPS only (same as any SaaS)
- No inbound connections to OT network
- Can deploy via Private Link or VPN for extra security
- Databricks SOC 2, ISO 27001 certified

**Mitigation:** Engage IT/OT security early, provide architecture review

---

**Concern: "Operator adoption - will they actually use it?"**

**Response:**
- Interface is familiar (chat, like texting)
- Training: 15 minutes, most productive immediately
- Early pilots show 80%+ daily usage by Week 3
- Operators request it be expanded

**Mitigation:** Start with operator champions, demonstrate quick wins

---

**Concern: "Cost overrun - consumption-based pricing is unpredictable"**

**Response:**
- Consumption scales with usage (pay for what you use)
- Pilot provides real usage data for forecasting
- Can set spending alerts and limits in Databricks
- ROI positive even with conservative usage

**Mitigation:** Monitor daily during pilot, adjust if needed

---

## SLIDE 13: NEXT STEPS

### Proposed Engagement Path

**Step 1: Alignment Call (This Week)**
- Review demo feedback
- Discuss pilot scope and timeline
- Address questions and concerns
- Get stakeholder buy-in

**Step 2: Technical Validation (Week 1)**
- IT/OT security review
- Firewall rule approval
- Ignition access provisioning
- Databricks workspace setup

**Step 3: Pilot Kickoff (Week 2)**
- Install connector
- Configure data pipeline
- Train operators
- Go live with 5-10 users

**Step 4: Feedback & Iteration (Week 3-4)**
- Daily usage
- Weekly check-ins
- Adjust based on feedback
- Track metrics

**Step 5: Results Review (Week 5)**
- Present findings
- Calculate actual ROI
- Decide on expansion
- Plan next phase

**Timeline: 5 weeks from decision to results**

---

## SLIDE 14: CALL TO ACTION

### Let's Start With a Pilot

**Proposal:**
- **Scope:** 1 processing area (crushers or haul trucks)
- **Duration:** 4 weeks
- **Users:** 5-10 operators
- **Investment:** ~$15-25K pilot + platform consumption
- **Risk:** Low (read-only, isolated scope, reversible)

**What Success Looks Like:**
- 50%+ reduction in investigation time
- 1+ potential failures caught early
- 80%+ operator daily usage
- Positive feedback from operators
- Clear ROI demonstrated

**If Successful:**
- Expand to additional equipment
- Add more data sources (CMMS, ERP)
- Scale to other sites
- Become reference customer

**If Not Successful:**
- We learn what didn't work
- No long-term obligation
- Minimal sunk cost

**Question for You:**
*"Does this pilot approach make sense? What would you need to see to get started?"*

---

## SLIDE 15: THANK YOU + Q&A

### Questions?

**Topics We Can Discuss:**

**Technical:**
- Integration with existing systems
- Data architecture and security
- Performance and scalability
- Customization options

**Business:**
- ROI calculations specific to your site
- Pilot scope and timeline
- Pricing and consumption estimates
- Contract and procurement process

**Operational:**
- Operator training approach
- Change management
- Support during and after pilot
- Expansion roadmap

**Contact Information:**

**Pravin Varma**
Solutions Architect, Databricks
Email: [email]
Phone: [phone]

**We'll follow up within 24 hours with:**
- Summary of today's discussion
- Detailed pilot proposal
- ROI calculator customized to your numbers
- Technical architecture document

**Thank you for your time!**

---

## APPENDIX SLIDES (Available on Request)

### A1: Detailed Technical Specifications

**Zerobus Connector:**
- Protocol: HTTPS
- Port: 443 outbound only
- Latency: <500ms tag-to-lakehouse
- Throughput: 10,000+ tags/sec

**Databricks Platform:**
- Spark version: 14.3+ (Real-Time Mode)
- SQL Warehouse: Serverless Pro
- Genie: Latest version with custom instructions
- Unity Catalog: For governance

**Perspective Integration:**
- WebDev module: Iframe embed
- API: REST for Genie queries
- Auth: OAuth 2.0 or service principal

---

### A2: Data Model Example

**Tables in Lakehouse:**

**main.mining_ops.sensor_data_gold**
- Columns: timestamp, equipment_id, metric_name, metric_value, unit
- Partitioned by: date
- Optimized: Z-order on equipment_id

**main.mining_ops.incidents**
- Columns: incident_id, equipment_id, timestamp, description, root_cause, downtime_hours, cost_usd
- Historical: 3-5 years typically

**main.mining_ops.work_orders** (if CMMS integrated)
- Columns: wo_id, equipment_id, date, type, technician, parts_used, labor_hours

**Genie instructions reference these tables automatically**

---

### A3: Sample Genie Instructions

```
You are an AI assistant for mining operations control room operators.

CONTEXT:
- Equipment: Haul trucks, crushers, conveyors
- Normal baselines: Crusher vibration 18-25 mm/s, conveyor motor temp 60-75°C
- Critical thresholds: Vibration >40 mm/s, temp >85°C

DATA SOURCES:
- main.mining_ops.sensor_data_gold (real-time metrics)
- main.mining_ops.incidents (historical failures)
- main.mining_ops.work_orders (maintenance records)

INSTRUCTIONS:
1. Always show timestamp when referencing sensor data
2. Compare current values to normal baselines
3. Search for historical patterns with >80% similarity
4. Provide specific recommendations, not generic advice
5. Include confidence scores on pattern matches
6. Show units (mm/s, °C, kW, etc.)

EXAMPLES:
- "Crusher 2 vibration 42mm/s (2.1x normal). Similar pattern Jan 15 (belt misalignment). Recommend inspect belt."
- "Truck 3 efficiency 72% vs fleet avg 89%. Last 3 shifts below target. Check operator logs."
```

---

### A4: Security Architecture

**Network:**
- Outbound HTTPS only (443)
- No inbound OT connections
- Optional: Private Link, VPN, or AWS Direct Connect

**Authentication:**
- SSO via Azure AD / Okta
- Service principal for connector
- MFA enforced

**Authorization:**
- Unity Catalog RBAC
- Operators: Read-only on Gold tables
- Admins: Full access
- Auditing: All queries logged

**Data Privacy:**
- No PII in operational data (equipment IDs, not personnel)
- Audit logs: 90-day retention
- Compliance: SOC 2, ISO 27001, GDPR (if applicable)

---

**End of Presentation Deck**

---

## DECK DELIVERY NOTES

**Slide Timing (15-minute version):**
- Slides 1-4 (Problem + Solution): 4 minutes
- Slide 5 (Live Demo): 6 minutes
- Slides 6-8 (Value + Architecture): 3 minutes
- Slides 9-14 (Implementation + CTA): 2 minutes
- Slide 15 (Q&A): Remaining time

**Adaptation Tips:**

**For Executive Audience (10 minutes):**
- Slides 1-2 (Problem): 2 min
- Slide 5 (Quick Demo): 3 min
- Slide 6 (ROI): 3 min
- Slide 14 (CTA): 2 min
- Skip technical deep dives

**For Technical Audience (20 minutes):**
- Keep all slides
- Add Appendix slides
- Spend more time on Slide 7 (Architecture)
- Live Q&A on integration details

**Visual Design:**
- Use Databricks brand colors (navy, cyan, lava)
- Include screenshots from actual demo
- Architecture diagrams clean and simple
- Minimal text, maximum visuals
- Professional but not overly formal
