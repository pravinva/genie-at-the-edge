# RALPH WIGGUM WORKSTREAM - FILE 12
## Customer Demo Script (15 Minutes)

**Audience:** WA Mining Account Teams (SA, AE, Customer)
**Format:** Live demo with architecture explanation
**Duration:** 12-15 minutes presentation + 5-10 minutes Q&A
**Backup:** Pre-recorded video if live fails

---

## PRE-DEMO CHECKLIST (30 Minutes Before)

**System Warmup:**
- [ ] Ignition Gateway running, simulation active for 30+ minutes
- [ ] SQL Warehouse started and warm (run test query)
- [ ] DLT pipeline processing (check last update time)
- [ ] Fault injection at right stage:
  - Option A: Just starting (for live progression)
  - Option B: Already active (for immediate demo)
- [ ] Browser with Perspective session open, tested
- [ ] Backup video ready (just in case)
- [ ] Screen sharing tested (Zoom/Teams)
- [ ] Audio tested (microphone, no echo)

**Environment Check:**
- [ ] Close unnecessary apps (clean desktop)
- [ ] Turn off notifications
- [ ] Full screen browser (no distractions)
- [ ] Notes/talking points open on second screen
- [ ] Stopwatch ready (to show latency)

---

## DEMO SCRIPT

### **[0:00-2:00] INTRODUCTION (2 minutes)**

**Opening:**

*"Thanks for your time today. I'm excited to show you something we've built specifically for mining operations - conversational AI that gives your operators instant insights."*

**Set Context:**

*"In a typical mining control room, when an equipment issue occurs, operators spend 20-30 minutes investigating:*
- *Checking trend charts*
- *Reviewing logs*
- *Calling maintenance*
- *Looking up past incidents*

*What if they could just ask an AI assistant and get an answer in 5 seconds?"*

**Transition:**

*"Let me show you what we've built. This is a live system - real Ignition SCADA connected to Databricks with conversational AI embedded right in the operator interface."*

**[Screen Share: Start showing Perspective view]**

---

### **[2:00-4:00] SYSTEM OVERVIEW (2 minutes)**

**Show Perspective View:**

*"This is Ignition Perspective showing a simulated mining operation - 5 haul trucks, 3 crushers, 2 conveyors."*

**Point out components (hover mouse over each):**

**Left Panel:**
- *"Here's real-time equipment status - you can see Crusher 1 and 3 are running normally"*
- *"Crusher 2 - notice the vibration is elevated and the warning indicator"*
- *"Below: Active alarms table"*
- *"Bottom: Production metrics - target vs actual for the shift"*

**Right Panel:**
- *"And here - this is the AI assistant, embedded directly in the HMI"*
- *"Operators don't switch to another app - everything is on one screen"*

**Quick Architecture:**

*"Behind the scenes:*
- *Ignition streaming sensor data to Databricks via our Zerobus connector*
- *Real-Time processing with sub-second latency*
- *Genie queries years of unified operational and business data*
- *All from Databricks lakehouse"*

---

### **[4:00-10:00] LIVE DEMO (6 minutes) - THE CORE**

**Scenario 1: Alarm-Triggered Investigation**

*"Let's say I'm an operator and I see this alarm for Crusher 2 high vibration."*

**[Click the alarm row, point to it]**

*"Instead of spending 30 minutes digging through logs and trend charts, I click this 'Ask AI' button."*

**[Click the  button]**

*"Watch what happens..."*

**[Chat pre-fills with question]**

*"The question is pre-filled based on the alarm. I can edit it if I want, or just press Enter."*

**[Press Enter, start stopwatch]**

*"Now watch the response time..."*

**[Wait for typing indicator, then response appears]**

**[Stop stopwatch]**

*"Four seconds. Let me read what the AI found:"*

**[Read response out loud]:**

*"Crusher 2 vibration increased to 42mm/s - that's 2.1 times normal baseline. The AI is telling me this pattern matches a belt misalignment incident from January 15th with 87% confidence. It's recommending immediate belt inspection."*

**Key Points:**
- *"This isn't generic - it's querying OUR operational data"*
- *"It found a historical pattern match - January 15th incident"*
- *"It's giving me a specific recommendation: inspect the belt"*
- *"All of this in 4 seconds instead of 30 minutes of manual work"*

---

**Scenario 2: Follow-Up Questions**

*"And I can ask follow-up questions naturally:"*

**[Type: "What happened on January 15?"]**

**[Send, wait for response]**

*"Now it's pulling up the historical incident - same crusher, same failure mode, 3.2 hours of downtime, $45,000 in lost production plus maintenance costs."*

*"This gives me context: Is this urgent? Yes, because last time it cost us big."*

**[Type: "Compare Crusher 2 to the other crushers"]**

**[Send, wait for response]**

*"And it can analyze across equipment - showing me Crusher 1 and 3 are running normally, only Crusher 2 has the issue."*

---

**Scenario 3: Proactive Questions**

*"Operators don't have to wait for alarms. They can ask anything:"*

**[Type: "Show me haul trucks with lowest efficiency today"]**

**[Send, show response]**

*"There - it identified Truck 3 is underperforming. Might be operator technique, might be mechanical. Worth investigating before it becomes a problem."*

**Key Points:**
- *"This is proactive, not just reactive"*
- *"Operators can explore patterns, not just respond to alarms"*
- *"Natural language - they just ask like talking to an expert"*

---

### **[10:00-12:00] TECHNICAL DEPTH (2 minutes)**

**Show the Data Flow (Optional - if audience is technical):**

*"Quickly on the architecture:"*

**[Show simple diagram or describe]:**

1. *"Ignition streams tag changes via our Zerobus connector"*
2. *"Databricks processes in real-time - we're using Spark's new Real-Time Mode for sub-second latency"*
3. *"Data lands in medallion architecture: bronze, silver, gold"*
4. *"Genie queries the gold tables - years of operational history plus real-time data"*
5. *"Response comes back through the embedded chat interface"*

**Highlight:**
- *"Real-Time Mode: Data is queryable within 1 second of the physical event"*
- *"Unified lakehouse: OT data plus business data - maintenance costs, shift schedules, everything"*
- *"Works with any integration: Our connector, Litmus Edge, DeepIQ, doesn't matter - as long as data is in Databricks"*

---

### **[12:00-14:00] BUSINESS VALUE (2 minutes)**

**Quantify Impact:**

*"Let's talk about what this means operationally:"*

**Time Savings:**
- *"Average investigation time: 30 minutes → 30 seconds"*
- *"That's 60x faster troubleshooting"*
- *"For 10 operators per shift, 5 investigations per shift: Saves ~25 hours per week"*

**Better Decisions:**
- *"Historical context: AI remembers every past incident"*
- *"Cross-equipment insights: Patterns humans might miss"*
- *"Predictive: Catch issues before they become failures"*

**Reduced Downtime:**
- *"Faster diagnosis = faster repair dispatch"*
- *"Predictive warnings: 2-4 hours early detection"*
- *"Every hour of unplanned downtime: $10-50K in lost production"*

**ROI Example:**
- *"Prevent just 2-3 unplanned downtime events per year"*
- *"Savings: $100-300K annually"*
- *"Cost: ~$60-100K for platform (conservative)"*
- *"Payback: 4-8 months"*

---

### **[14:00-15:00] WHAT MAKES THIS UNIQUE (1 minute)**

**Competitive Differentiation:**

*"You might be wondering: What about Siemens or Rockwell copilots?"*

**Key differences:**
1. *"Theirs only work with Siemens/Rockwell ecosystems - ours works with Ignition, which you already have"*
2. *"Theirs query local SCADA data - ours queries the entire lakehouse: OT plus IT plus business data unified"*
3. *"Theirs are expensive enterprise platforms - ours runs on consumption, scales with usage"*

*"And compared to Litmus or DeepIQ - they focus on data integration. We're adding the conversational layer for operators. Complementary, not competitive."*

**Unique Value:**
- *"Only solution that brings Genie to Ignition operations"*
- *"Platform-agnostic: Works with any data ingestion method"*
- *"Operator-first: Built for shop floor, not just engineering office"*

---

### **[15:00] CLOSE & NEXT STEPS**

**Call to Action:**

*"What I'd like to propose:"*

**Pilot Scope:**
- *"2-4 week pilot with your West Australia site"*
- *"Start with one pit or processing area"*
- *"5-10 operators testing"*
- *"We handle all setup and configuration"*

**Timeline:**
- *"Week 1-2: Install and configure"*
- *"Week 3-4: Operator testing and feedback"*
- *"Week 5: Review results, decide on expansion"*

**What we need from you:**
- *"Access to one Ignition gateway (read-only initially)"*
- *"Firewall rule: Outbound HTTPS to Databricks"*
- *"5-10 operators willing to test"*
- *"Feedback - tell us what works and what doesn't"*

**Open to Questions:**

*"I'll stop here and open it up - what questions do you have?"*

---

## Q&A PREPARATION

**Common Questions (Prepare Answers):**

**Q: "How accurate are the AI responses?"**
A: "Based on testing: >90% accuracy on operational questions. It only answers based on data in the lakehouse, doesn't hallucinate. If it doesn't know, it says so."

**Q: "What if the AI gives wrong advice?"**
A: "AI is a decision support tool, not autonomous control. Operators verify recommendations before acting. Plus, responses include confidence scores and show the underlying data/SQL."

**Q: "Can it control equipment?"**
A: "No - by design. It's read-only queries only. For safety, all control remains with operators and existing PLC logic. We can add optimized setpoint suggestions in future, but always requires operator approval."

**Q: "What about our existing historian (OSI PI, etc.)?"**
A: "We have connectors for OSI PI (already in Databricks product), Ignition historian (via Lakeflow SQL), and we work with Litmus/DeepIQ integrations. Your historical data can be included."

**Q: "How do you handle downtime/network issues?"**
A: "If Databricks is unreachable, Ignition continues normal operation - alarms, dashboards all work. Chat shows 'offline' and retries. No single point of failure for operations."

**Q: "What's required to deploy at our site?"**
A: "Minimal: Firewall rule for HTTPS to Databricks, Databricks workspace access, install our connector or use existing integration. We can start with read-only access to de-risk."

**Q: "How long does operator training take?"**
A: "If they can type a question, they can use it. 15-30 minute orientation, most operators are productive immediately. Interface is familiar (chat, like messaging apps)."

**Q: "Can this integrate with our CMMS?"**
A: "Yes - maintenance data can be ingested to Databricks (via Lakeflow connectors or APIs). Then Genie can query work orders, parts inventory, scheduling - complete context."

**Q: "What if we already have dashboards/BI?"**
A: "This complements, doesn't replace. Dashboards are great for monitoring. This is for investigation and troubleshooting - natural language, ad-hoc queries. Both have value."

---

## OBJECTION HANDLING

**Objection: "We're not ready for AI in operations"**

Response:
*"I understand the concern. That's why we position this as decision support, not autonomous control. Operators stay in charge - AI just helps them find information faster. Start small with a pilot, validate it works, then decide."*

**Objection: "Too expensive"**

Response:
*"Let's look at cost vs value: $60-100K annually for the platform. Prevent just 2-3 major downtime events, you've paid for it. Plus, this consumption-based - you only pay for what you use. Pilot is low risk."*

**Objection: "Our network security won't allow this"**

Response:
*"Fair concern. It only requires outbound HTTPS - same as any cloud application. We can work with your IT/OT security team on the firewall rules. Some customers deploy via VPN or Private Link for extra security. Flexible."*

**Objection: "We need to see more proof it works"**

Response:
*"Absolutely. That's why we're proposing a pilot. 4 weeks, limited scope, full evaluation. If it doesn't deliver value, no obligation. We're confident once operators try it, they'll want it expanded."*

---

## DEMO TIPS

**DO:**
-  Practice 3+ times before live demo
-  Have backup video ready
-  Keep energy high (enthusiasm is contagious)
-  Pause for questions if audience engaged
-  Show confidence in the technology
-  Relate to customer's specific pain points
-  Use their terminology (not generic "manufacturing")

**DON'T:**
-  Rush through (15 min is enough, don't compress to 8)
-  Over-explain architecture (unless asked)
-  Apologize for "just a demo" (it's production-quality)
-  Get defensive if questioned (listen, address calmly)
-  Oversell (be honest about limitations)
-  Ignore questions to stay on script (adapt to audience)

---

## FAILURE RECOVERY

**If Something Breaks During Demo:**

**Scenario 1: Genie Doesn't Respond**

Response:
*"Looks like we hit a network timeout - let me retry... [Click retry]*

*While that loads, let me show you what the response typically looks like..."*

**[Switch to backup video or screenshots]**

---

**Scenario 2: Perspective View Won't Load**

Response:
*"Ignition session isn't starting - let me show you the pre-recorded version while I troubleshoot..."*

**[Play backup video]**

*The functionality is exactly the same - I'm showing the recording to save time."*

---

**Scenario 3: Tags Aren't Updating**

Response:
*"The simulation script paused - not a problem, I can show with static data..."*

**[Use SQL queries directly to show data]**

*Or:*

*"Let me restart the simulation quickly - takes 30 seconds..."*

**[Restart Gateway script, continue talking to fill time]**

---

**Key Principle: Stay calm, have backup, keep talking**

---

## POST-DEMO FOLLOW-UP

**Immediately After (While Fresh):**

**Ask for Feedback:**
- *"What resonated with you?"*
- *"What concerns do you have?"*
- *"Is this something you'd want to pilot?"*

**Gauge Interest:**
- **High:** "This is exactly what we need, let's talk pilot scope"
  - → Schedule follow-up within 1 week
  - → Draft pilot proposal
  
- **Medium:** "Interesting, need to discuss with team"
  - → Send summary deck
  - → Offer follow-up demo for broader team
  
- **Low:** "Not a priority right now"
  - → Understand why (budget, timing, competing priorities)
  - → Stay engaged for future opportunity

**Collect Intel:**
- Who makes the decision? (Get names, titles)
- What's the approval process? (CapEx, security review, etc.)
- What's the timeline? (Budget cycles, project schedules)
- Who are the blockers? (IT, security, operations manager?)

---

## FOLLOW-UP MATERIALS

**Send Within 24 Hours:**

**1. Thank You Email:**
```
Subject: Mining Operations AI Demo - Next Steps

Hi [Name],

Thanks for your time today reviewing the conversational AI for mining operations. 

Key highlights from our demo:
• Sub-5-second operator insights (vs 30-minute manual investigation)
• Works with your existing Ignition infrastructure
• Queries unified lakehouse (OT + IT + business data)
• Compatible with Litmus, DeepIQ, or native integrations

[If interest shown]: I'd like to propose a 4-week pilot at [Site Name]:
- Week 1-2: Installation and configuration
- Week 3-4: Operator testing with 5-10 users
- Investment: [Estimate based on scope]

[If need more info]: I'm attaching:
- Architecture diagram
- ROI calculator
- Pilot proposal outline

Happy to discuss further. What's the best next step from your perspective?

Best,
Pravin
```

**2. One-Page Summary (PDF):**
- Problem: Manual investigation is slow and error-prone
- Solution: Conversational AI embedded in Ignition
- Demo Results: 4-second diagnosis, 60x faster
- Technology: Databricks + Ignition + Genie
- Next Step: 4-week pilot proposal

**3. Demo Video (If Recorded):**
- Upload to Databricks/YouTube (unlisted)
- Send link
- Allows them to show colleagues

---

## SUCCESS INDICATORS

**Demo went well if:**
-  Audience asks technical questions (shows engagement)
-  Customer mentions specific use cases ("This would help with...")
-  Discussion of pilot timeline happens naturally
-  Positive body language (nodding, taking notes)
-  Request for follow-up demo to broader team

**Demo needs work if:**
-  Audience seems confused or disengaged
-  Questions are basic ("What is Databricks?")
-  Lots of objections with no path forward
-  "We'll think about it" with no next step

**Action:** Debrief after each demo, refine script based on what works

---

## MEASURING DEMO EFFECTIVENESS

**Track Metrics:**

| Demo Date | Customer | Attendees | Interest Level | Next Step | Close Probability |
|-----------|----------|-----------|----------------|-----------|-------------------|
| Feb 18 | WA Mining Co | 5 (Ops Mgr, IT, 3 Engineers) | High | Pilot proposal in 1 week | 70% |
| Feb 20 | Example Co | 3 | Medium | Follow-up demo to CTO | 40% |

**Goal:** >5