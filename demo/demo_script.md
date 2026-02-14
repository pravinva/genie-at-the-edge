# Mining Operations Genie - 15-Minute Demo Script

**Version:** 1.0
**Duration:** 15 minutes presentation + 5-10 minutes Q&A
**Format:** Live demo with architecture explanation
**Backup:** Pre-recorded video if live system fails

---

## Pre-Demo Setup (Do This Before Meeting)

- [ ] Complete **pre_demo_checklist.md** 30 minutes before
- [ ] All systems warm and tested
- [ ] Screen sharing configured
- [ ] Backup materials ready
- [ ] Second screen with this script open
- [ ] Stopwatch ready for timing

---

## SECTION 1: INTRODUCTION [0:00-2:00] - 2 Minutes

### Opening (0:00-0:30)

**Say:**

*"Thanks for your time today. I'm excited to show you something we've built specifically for mining operations - conversational AI that gives your operators instant insights without leaving their control interface."*

**Tone:** Confident, enthusiastic, professional

---

### Context Setting (0:30-1:30)

**Say:**

*"Let me set the scene. In a typical mining control room, when an equipment alarm goes off - let's say a crusher with high vibration - the operator has to:"*

**List out slowly (pause between each):**

1. *"Check multiple trend charts to see vibration history"*
2. *"Review alarm logs to find similar patterns"*
3. *"Call maintenance to ask if this has happened before"*
4. *"Look through paper logs or SharePoint documents for past incidents"*
5. *"Check if other equipment is affected"*

*"This entire process takes 20 to 30 minutes. And during that time, the equipment might be degrading further, production is impacted, and the operator is stressed."*

**Pause for effect**

*"What if instead, they could just ask an AI assistant and get the answer in 5 seconds?"*

---

### Transition to Demo (1:30-2:00)

**Say:**

*"That's what we've built. This is a live system - real Ignition SCADA connected to Databricks with conversational AI embedded right in the operator interface. Let me show you."*

**Action:** Start screen share, show Perspective view

---

## SECTION 2: SYSTEM OVERVIEW [2:00-4:00] - 2 Minutes

### Show Perspective Interface (2:00-3:00)

**Say while pointing to screen:**

*"This is Ignition Perspective showing a simulated mining operation. We have 5 haul trucks, 3 crushers, 2 conveyors - similar to what you'd see in a typical pit-to-plant operation."*

**Point to LEFT PANEL:**

*"Here's real-time equipment status..."*

**Hover over each component:**
- *"Crusher 1 - running normally, vibration at 22mm/s"*
- *"Crusher 2 - notice the vibration is elevated at 42mm/s and there's a warning indicator"*
- *"Crusher 3 - also running normally"*

**Point lower:**
- *"Below here: Active alarms table showing that Crusher 2 high vibration alarm"*
- *"And at the bottom: Production metrics - we're tracking target versus actual tonnes per hour for the shift"*

**Point to RIGHT PANEL:**

*"And here's the key innovation - the AI assistant, embedded directly in the HMI."*

*"Operators don't have to switch to another application, open a browser, or leave their workflow. Everything is on one screen."*

---

### Quick Architecture (3:00-4:00)

**Say:**

*"Behind the scenes, here's what's happening:"*

**List quickly (don't over-explain):**

1. *"Ignition is streaming sensor data to Databricks using our Zerobus connector"*
2. *"Databricks processes it in real-time with sub-second latency"*
3. *"When an operator asks a question, Genie queries years of unified operational and business data"*
4. *"All from the Databricks lakehouse - not just SCADA tags, but maintenance records, work orders, shift logs, everything"*

**Transition:**

*"Now let me show you how operators actually use this."*

---

## SECTION 3: LIVE DEMO [4:00-10:00] - 6 Minutes (THE CORE)

### Scenario 1: Alarm-Triggered Investigation (4:00-6:30)

**Say:**

*"Let's say I'm an operator and I see this alarm for Crusher 2 high vibration."*

**Action:** Click on the alarm row to highlight it

*"Instead of spending 30 minutes digging through logs and trend charts, I click this 'Ask AI' button right next to the alarm."*

**Action:** Click the chat icon button next to alarm

**Say:**

*"Watch what happens..."*

**Action:** Chat panel opens with pre-filled question

**Say:**

*"The question is automatically pre-filled based on the alarm context. I can edit it if I want to be more specific, or I can just press Enter."*

**Action:** Press Enter, immediately start stopwatch visibly

**Say:**

*"I'm timing this... watch the response time..."*

**Action:** Wait for typing indicator, then response appears (should be 3-5 seconds)

**Action:** Stop stopwatch dramatically

**Say with emphasis:**

*"Four seconds. Let me read what the AI found."*

**Action:** Read the AI response out loud slowly and clearly

**Example response:**

*"Crusher 2 vibration increased to 42mm/s at 2:23 PM - that's 2.1 times normal baseline of 20mm/s. The AI is telling me this pattern matches a belt misalignment incident from January 15th with 87% confidence. It's recommending immediate belt inspection before shutdown."*

---

#### Key Points Explanation (6:30-7:00)

**Say with emphasis on each point:**

*"Notice a few things here:"*

1. *"This isn't generic AI - it's querying OUR specific operational data"*
2. *"It found a historical pattern match from January 15th - months of data analyzed instantly"*
3. *"It's giving me a specific, actionable recommendation: inspect the belt"*
4. *"And it showed me the confidence level - 87% - so I know how reliable this insight is"*

*"All of this in 4 seconds instead of 30 minutes of manual investigation."*

---

### Scenario 2: Follow-Up Questions (7:00-8:30)

**Say:**

*"And the operator can ask natural follow-up questions. Watch this..."*

**Action:** Type in chat: "What happened on January 15?"

**Action:** Press Enter, wait for response

**Say while waiting:**

*"I just asked in plain English - no special syntax, no query language."*

**Action:** Response appears

**Say while reading:**

*"Now it's pulling up the complete historical incident - same crusher, same failure mode, resulted in 3.2 hours of unplanned downtime, $45,000 in lost production plus $8,000 in maintenance costs."*

*"This gives the operator critical context: Is this urgent? Yes, because last time it cost us $53,000."*

---

**Next Follow-Up:**

**Action:** Type: "Compare Crusher 2 to the other crushers right now"

**Action:** Send, wait for response

**Say:**

*"And it can analyze across equipment in real-time..."*

**Action:** Response appears with comparison

**Say:**

*"There - showing me Crusher 1 and 3 are running normally at 20-22mm/s, only Crusher 2 has the elevated vibration. So this is isolated, not a systemic issue."*

---

### Scenario 3: Proactive Questions (8:30-10:00)

**Say:**

*"Operators don't have to wait for alarms. They can ask anything proactively:"*

**Action:** Type: "Show me haul trucks with lowest efficiency today"

**Action:** Send, wait for response

**Say:**

*"Maybe they're curious which trucks are underperforming..."*

**Action:** Response appears

**Say:**

*"There - it identified Truck 3 is running at 72% efficiency compared to fleet average of 89%. Might be operator technique, might be a mechanical issue starting to develop. Worth investigating before it becomes a problem."*

---

**Another Example:**

**Action:** Type: "What was our average crusher throughput last Tuesday?"

**Action:** Send, show response

**Say:**

*"Or asking about historical performance for shift reports..."*

*"The point is: This is a conversational interface to all your operational data. Operators explore, investigate, and understand - all in natural language."*

---

## SECTION 4: TECHNICAL DEPTH [10:00-12:00] - 2 Minutes

### Architecture Deep Dive (10:00-11:30)

**Say:**

*"Let me quickly explain the technical architecture for those interested."*

**Action:** Show architecture diagram if available, or describe

**Describe the flow:**

1. **Ignition to Databricks:**
   *"Ignition streams tag changes using our Zerobus connector - essentially a native Databricks data source for Ignition. Every tag change, alarm, event flows in real-time."*

2. **Real-Time Processing:**
   *"Databricks processes this using Spark's new Real-Time Mode - not traditional batch, not micro-batch. True real-time streaming with sub-second latency. Data is queryable within 1 second of the physical event."*

3. **Medallion Architecture:**
   *"Data lands in our medallion architecture: Bronze layer for raw ingestion, Silver for cleansing and enrichment, Gold for business-ready datasets. This is best practice for data lakehouses."*

4. **Genie Integration:**
   *"Genie queries the Gold tables - years of operational history plus real-time data, all unified. It understands the schema, relationships, and can write SQL automatically from natural language."*

5. **Embedded Chat:**
   *"The response comes back through the embedded chat interface using Ignition's WebDev module and iframes. Seamless integration."*

---

### Key Technical Highlights (11:30-12:00)

**Say:**

*"Three things that make this unique technically:"*

1. **Real-Time Mode:**
   *"Data is queryable in under 1 second. Previous solutions had 5-15 minute delays. We can act on data while it's still operationally relevant."*

2. **Unified Lakehouse:**
   *"Not just OT data - we're combining operational data with business data. Maintenance costs, shift schedules, work orders, parts inventory. Complete context for decision-making."*

3. **Integration Flexibility:**
   *"Works with our Zerobus connector, Litmus Edge, DeepIQ, Databricks Lakeflow SQL - doesn't matter. As long as data flows to Databricks, Genie can query it."*

---

## SECTION 5: BUSINESS VALUE [12:00-14:00] - 2 Minutes

### Quantify Impact (12:00-13:00)

**Say:**

*"Let's talk about what this means for your operations in dollars and hours."*

---

**Time Savings:**

*"Average equipment investigation time goes from 30 minutes down to 30 seconds. That's 60 times faster."*

*"For a site with 10 operators per shift, each investigating 5 issues per shift - that's 50 investigations. You're saving approximately 25 hours per shift."*

*"Over a month: 750 hours of operator time saved. That's productivity gains without hiring more people."*

---

**Better Decisions:**

*"Beyond speed, this is about quality of decisions:"*

- *"Historical context: The AI remembers every past incident - humans forget or weren't there"*
- *"Cross-equipment insights: It can spot patterns across 50 assets that one operator might miss"*
- *"Predictive warnings: Catch issues 2-4 hours before they become critical failures"*

---

**Reduced Downtime:**

*"Faster, better diagnosis means faster repair dispatch and less downtime."*

*"For every hour of unplanned downtime on a crusher, you're losing $10,000 to $50,000 in production depending on the site."*

*"If this system helps you prevent just 2 or 3 unplanned shutdowns per year, you've justified the investment."*

---

### ROI Example (13:00-14:00)

**Say:**

*"Let me give you a conservative ROI scenario:"*

**Write these numbers on whiteboard or show in deck:**

**Savings:**
- Prevent 3 unplanned downtime events per year (2 hours each) = 6 hours saved
- At $30,000/hour lost production = $180,000 saved
- Operator productivity gains = $50,000/year value
- **Total Annual Value: ~$230,000**

**Investment:**
- Databricks platform: ~$60-100K annually (consumption-based)
- Implementation: ~$20-30K one-time
- **Total Cost Year 1: ~$110,000**

**Payback: 6 months**

**Say:**

*"And remember, this is consumption-based pricing - you only pay for what you use. It scales with your needs."*

---

## SECTION 6: DIFFERENTIATION [14:00-15:00] - 1 Minute

### Competitive Positioning (14:00-14:30)

**Say:**

*"You might be wondering: What about Siemens Industrial Copilot or Rockwell's AI offerings?"*

**Key differences:**

1. **Ecosystem Lock-In:**
   *"Theirs only work with Siemens or Rockwell ecosystems - expensive, proprietary. Ours works with Ignition, which you already have and is platform-agnostic."*

2. **Data Scope:**
   *"Their copilots query local SCADA historian data - limited scope. Ours queries the entire lakehouse: OT data plus IT systems plus business data, all unified."*

3. **Cost Model:**
   *"They're expensive enterprise platforms with large upfront costs. Ours runs on consumption - pay for what you use, scale as needed."*

---

### Unique Value (14:30-15:00)

**Say:**

*"And compared to Litmus or DeepIQ - they're excellent at data integration, getting OT data to the cloud. We're complementary, not competitive."*

*"We're adding the conversational intelligence layer that makes that data actionable for operators on the floor."*

**Unique value proposition:**

- *"Only solution bringing Databricks Genie to Ignition operations"*
- *"Platform-agnostic - works with any data ingestion method"*
- *"Operator-first design - built for the shop floor, not just engineering offices"*

---

## CLOSING & NEXT STEPS [15:00] - 1 Minute

### Call to Action

**Say:**

*"So here's what I'd like to propose..."*

---

**Pilot Scope:**

*"A 2 to 4 week pilot at one of your West Australia sites:"*

- *"Start with one processing area - maybe the crushing circuit or haul truck fleet"*
- *"5 to 10 operators testing in their daily workflow"*
- *"We handle all setup, configuration, and training"*
- *"At the end, you evaluate: Did it deliver value? Do we expand?"*

---

**Timeline:**

- *"Week 1-2: Install Zerobus connector, configure data pipeline, set up Genie"*
- *"Week 3-4: Operator testing with daily feedback sessions"*
- *"Week 5: Review results, measure time savings, decide on next steps"*

---

**What We Need:**

- *"Access to one Ignition gateway - read-only access initially to de-risk"*
- *"One firewall rule: Outbound HTTPS to Databricks (same security as any cloud app)"*
- *"5 to 10 operators willing to test and give honest feedback"*

---

**Open to Questions:**

**Say:**

*"That's the overview. I'll stop here and open it up - what questions do you have?"*

---

## TIMING CHECKPOINTS

**Track your time during demo:**

| Checkpoint | Time | If Behind | If Ahead |
|------------|------|-----------|----------|
| After Introduction | 2:00 | Skip some context bullets | Add more context about pain points |
| After System Overview | 4:00 | Skip architecture details | Show more Perspective features |
| After Scenario 1 | 6:30 | Go straight to Scenario 3 | Add more follow-up questions |
| After All Scenarios | 10:00 | Skip technical section | Deep dive on Real-Time Mode |
| After Business Value | 14:00 | Quick differentiation | Detailed ROI examples |
| Closing | 15:00 | Done! | Open to questions |

---

## DELIVERY TIPS

**Energy & Pacing:**
- Speak clearly and slower than normal (excitement makes us rush)
- Pause after key points to let them sink in
- Smile and maintain enthusiasm - it's contagious
- Watch audience body language - adjust pace accordingly

**Interaction:**
- Encourage questions throughout (don't wait until end)
- If someone asks mid-demo, pause and answer
- Engage with names: "Great question, John..."
- Relate to their specific pain points if known

**Technical Depth:**
- Default to business value, go technical if asked
- Match audience expertise level
- Don't apologize for technical details - own it
- If you don't know something: "Great question - let me get back to you with the exact answer"

---

## SUCCESS INDICATORS

**Demo is going well if:**
- Audience is taking notes
- Multiple questions are asked
- Someone says "This would help with [specific problem]..."
- Discussion of pilot timeline starts naturally
- Positive body language (nodding, leaning forward)

**Demo needs adjustment if:**
- Lots of confused looks
- No questions at all
- Checking phones/laptops
- "We'll think about it" with no follow-up

**Adjust on the fly:**
- More confused → Slow down, simplify
- Very technical audience → Skip business section, go deeper on architecture
- Executive in room → Front-load ROI, demo shorter

---

## POST-DEMO ACTIONS

**Immediately After:**
1. Thank everyone for their time
2. Ask: "What resonated with you most?"
3. Gauge interest level (High / Medium / Low)
4. Schedule next step based on interest
5. Get contact info for follow-up

**Within 24 Hours:**
1. Send thank you email with summary
2. Attach customer handout document
3. Include ROI calculator if discussed
4. Propose pilot scope if interest shown
5. Schedule follow-up call

---

**End of Script**

*Good luck with your demo! Remember: Stay calm, be confident, and adapt to your audience.*
