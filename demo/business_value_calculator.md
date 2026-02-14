# Business Value Calculator - Mining Operations Genie

**Document Version:** 1.0
**Last Updated:** 2026-02-15
**Purpose:** ROI and value justification for conversational AI in mining operations

---

## Executive Summary

**Conservative ROI Estimate:**
- **Annual Value:** $230,000 - $450,000
- **Annual Investment:** $80,000 - $120,000
- **Net Benefit:** $150,000 - $330,000
- **Payback Period:** 4-8 months
- **3-Year NPV:** $450,000 - $1,000,000

---

## Value Drivers

### 1. Operator Time Savings

**Current State:**
- Average equipment investigation: **30 minutes**
- Investigations per operator per shift: **5**
- Operators per shift: **10**
- Total investigation time per shift: **25 hours**

**Future State:**
- Average investigation with AI: **30 seconds**
- Time savings per investigation: **29.5 minutes**
- Total time saved per shift: **24.6 hours**

**Annual Value:**
```
Calculations:
- Shifts per year: 365 × 3 = 1,095 shifts
- Hours saved per year: 24.6 × 1,095 = 26,937 hours
- Operator hourly cost (loaded): $45/hour
- Annual savings: 26,937 × $45 = $1,212,165

Note: This represents CAPACITY, not direct cost savings.
Operators are not laid off - they become more productive.

Conservative value (20% of capacity): $242,433
```

**Value Realization:**
- Operators handle more tasks per shift
- Reduced overtime (fewer extended investigations)
- Faster response to production issues
- Less operator stress and burnout

---

### 2. Downtime Prevention

**Current State:**
- Unplanned equipment failures per year: **12-18**
- Average downtime per failure: **2.5 hours**
- Crushers: $30,000/hour lost production
- Haul trucks: $15,000/hour lost production
- Conveyors: $25,000/hour lost production

**Impact of AI (Early Detection):**
- Failures caught 2-4 hours early: **30% of cases** (3-5 events)
- Failures prevented entirely: **20% of cases** (2-3 events)

**Annual Value:**

**Scenario A: Early Detection**
```
- 4 failures caught early
- 2 hours earlier detection per event
- Average cost: $25,000/hour
- Value: 4 × 2 × $25,000 = $200,000
```

**Scenario B: Prevention**
```
- 3 failures prevented entirely
- 2.5 hours downtime avoided per event
- Average cost: $25,000/hour
- Value: 3 × 2.5 × $25,000 = $187,500
```

**Total Downtime Value: $387,500 annually**

**Conservative Estimate (50% achievement):** $193,750

---

### 3. Faster Diagnosis & Response

**Current State:**
- Time from alarm to maintenance dispatch: **45-90 minutes**
  - Investigation: 30 minutes
  - Discussion with maintenance: 10 minutes
  - Root cause analysis: 15-30 minutes
  - Work order creation: 10-20 minutes

**Future State:**
- Time to dispatch: **10-15 minutes**
  - AI investigation: 5 minutes
  - Verification: 5 minutes
  - Work order creation: 5 minutes

**Value:**
```
- Time saved per incident: 40 minutes average
- Incidents requiring maintenance per year: 500
- Total time saved: 20,000 minutes = 333 hours
- Production loss during diagnosis: $10,000/hour
- Value: 333 × $10,000 = $3,330,000

Conservative (10% reduction in production loss): $333,000
```

**Reasoning:** Faster diagnosis doesn't always prevent downtime, but it reduces its duration.

---

### 4. Better Decision Quality

**Current State:**
- Operators rely on memory and local knowledge
- Historical context not always accessible
- Cross-equipment patterns missed
- Reactive, not proactive

**Future State:**
- AI remembers all incidents (years of data)
- Pattern matching across 50+ assets
- Proactive warnings before critical failures
- Data-driven recommendations

**Value (Qualitative):**
- Reduced "trial and error" troubleshooting
- Fewer incorrect maintenance actions
- Less repeat failures (learn from history)
- Improved operator confidence

**Quantified Value:**
```
Assume:
- 10% reduction in repeat failures
- Repeat failures per year: 6
- Cost per failure: $60,000 (downtime + maintenance)
- Value: 0.6 × $60,000 = $36,000
```

---

### 5. Training & Knowledge Transfer

**Current State:**
- Senior operators have institutional knowledge
- Junior operators lack experience
- Knowledge lost when operators leave
- Training takes 6-12 months

**Future State:**
- AI codifies institutional knowledge
- Junior operators have "expert advisor"
- Knowledge persists even after retirements
- Training accelerated to 3-6 months

**Value:**
```
Assume:
- 2 new operators per year
- Training cost: $50,000 per operator (loaded time)
- 25% reduction in training time
- Savings: 2 × $50,000 × 0.25 = $25,000
```

---

## Total Annual Value Summary

| Value Driver | Conservative | Optimistic |
|--------------|--------------|------------|
| **Operator Time Savings** | $50,000 | $240,000 |
| **Downtime Prevention** | $190,000 | $390,000 |
| **Faster Diagnosis** | $100,000 | $330,000 |
| **Better Decisions** | $36,000 | $100,000 |
| **Training Efficiency** | $25,000 | $50,000 |
| **TOTAL** | **$401,000** | **$1,110,000** |

**Recommended Planning Number:** $230,000 - $450,000 (conservative to moderate)

---

## Investment Breakdown

### Initial Investment (One-Time)

| Item | Cost | Notes |
|------|------|-------|
| **Databricks Workspace Setup** | $5,000 | One-time provisioning |
| **Zerobus Connector Development** | $8,000 | Custom development (if not pre-built) |
| **DLT Pipeline Configuration** | $6,000 | ETL setup and testing |
| **Genie Space Setup** | $4,000 | Instructions, testing, tuning |
| **Perspective HMI Integration** | $10,000 | Iframe embedding, button logic |
| **Historical Data Migration** | $8,000 | OSI PI or historian backfill (if applicable) |
| **Training & Documentation** | $5,000 | Operator training, admin docs |
| **Testing & Validation** | $6,000 | 2-week pilot testing |
| **TOTAL INITIAL** | **$52,000** | Range: $40K - $65K |

---

### Annual Recurring Costs

| Item | Cost/Year | Notes |
|------|-----------|-------|
| **Databricks Platform** | $60,000 - $100,000 | Consumption-based (compute + storage) |
| **Ignition License (if new)** | $0 | Assumed existing |
| **Support & Maintenance** | $8,000 | 10-15% of initial investment |
| **Training (ongoing)** | $3,000 | Refreshers, new operators |
| **Enhancements** | $10,000 | New features, integrations |
| **TOTAL ANNUAL** | **$81,000 - $121,000** | |

---

### Databricks Consumption Detail

**Components:**

**DLT Pipeline (Real-Time Streaming):**
```
- Cluster size: 4 workers (i3.xlarge)
- Runtime: 24/7 (720 hours/month)
- Cost: $1.50/DBU × 4 workers × 2 DBU/hr × 720 hrs = $8,640/month
- Annual: $103,680

With commitment discount (30-50%): $52,000 - $72,000
```

**SQL Warehouse (Serverless Pro):**
```
- Queries per day: 200 (20 operators × 10 queries)
- Avg query time: 3 seconds
- Total compute: ~1.67 hours/day
- Cost: $0.70/DBU × 10 DBU/hr × 1.67 hrs × 365 days = $4,260/year

With auto-scaling and caching: $3,000 - $5,000/year
```

**Storage:**
```
- Sensor data: 10 GB/day = 3.6 TB/year
- Delta Lake compression: ~1.2 TB actual
- Cost: $0.023/GB/month × 1,200 GB = $27.60/month = $331/year
```

**Genie (Included in SQL Warehouse):**
- No separate charge for Genie queries
- Uses SQL Warehouse compute

**Total Databricks Annual:**
- Low estimate (committed, optimized): $55,000
- High estimate (on-demand, peak usage): $100,000

---

## ROI Scenarios

### Scenario 1: Conservative

**Assumptions:**
- Only count downtime prevention value
- Prevent 2 unplanned shutdowns/year
- Ignore operator time savings

**Value:**
- 2 events × 2.5 hours × $25,000/hour = **$125,000/year**

**Investment:**
- Initial: $50,000
- Annual: $80,000
- **Year 1 Total: $130,000**

**ROI:**
- Year 1: Break-even
- Year 2+: $45,000/year net benefit
- **Payback: 13 months**

---

### Scenario 2: Moderate (Recommended)

**Assumptions:**
- Downtime prevention: $190,000
- Operator time savings: $50,000
- **Total Value: $240,000/year**

**Investment:**
- Initial: $50,000
- Annual: $90,000
- **Year 1 Total: $140,000**

**ROI:**
- Year 1: $100,000 net benefit (71% ROI)
- Year 2: $150,000 net benefit (167% ROI)
- Year 3: $150,000 net benefit
- **3-Year NPV (10% discount): $360,000**
- **Payback: 7 months**

---

### Scenario 3: Optimistic

**Assumptions:**
- Downtime prevention: $390,000
- Operator time savings: $100,000
- Faster diagnosis: $100,000
- **Total Value: $590,000/year**

**Investment:**
- Initial: $50,000
- Annual: $100,000
- **Year 1 Total: $150,000**

**ROI:**
- Year 1: $440,000 net benefit (293% ROI)
- Year 2: $490,000 net benefit
- Year 3: $490,000 net benefit
- **3-Year NPV (10% discount): $1,200,000**
- **Payback: 3 months**

---

## Sensitivity Analysis

### Key Variables Impact

**If Downtime Prevention = 1 Event (Not 3):**
- Value drops to: $100,000 - $150,000
- Still positive ROI (break-even to 20%)

**If Databricks Costs = $150,000/year (50% higher):**
- Year 1 total investment: $200,000
- Moderate scenario still yields positive ROI (20%)

**If Value Realization = 50% (only half the benefits achieved):**
- Value: $120,000/year
- Investment: $140,000/year
- Payback: 14 months (still acceptable)

**Conclusion:** ROI is robust across a wide range of assumptions.

---

## Comparison to Alternatives

### Do Nothing (Status Quo)

**Cost:** $0 upfront
**Impact:**
- Continue 30-minute investigations
- 12-18 unplanned failures/year
- Institutional knowledge continues eroding
- **Opportunity Cost: $240,000 - $590,000/year**

---

### Hire More Operators

**Cost:** $150,000/year per operator (loaded)
**Impact:**
- Faster response (more people)
- Does NOT solve knowledge access problem
- Does NOT prevent failures (reactive only)
- **ROI: Negative** (cost > benefit)

---

### Deploy SCADA Historian + BI Dashboards

**Cost:** $50,000 - $100,000 upfront + $20,000/year
**Impact:**
- Better visibility into historical data
- Still requires operators to know SQL or use dashboards
- NOT conversational or context-aware
- **ROI: Moderate** (20-30% downtime reduction)

**Why Genie is Better:**
- Natural language (no SQL needed)
- Context-aware (understands equipment relationships)
- Faster (5 seconds vs 10 minutes with BI tools)

---

### Siemens Industrial Copilot

**Cost:** $200,000 - $500,000 upfront + $100,000/year
**Impact:**
- Similar conversational capabilities
- Locked to Siemens ecosystem (you use Ignition)
- Higher cost
- **ROI: Break-even to 50%** (but requires replacing existing systems)

**Why Databricks Genie is Better:**
- Platform-agnostic (works with Ignition)
- 50-70% lower cost
- Unified lakehouse (OT + IT data)

---

## Multi-Site Scaling

### 1 Site (Pilot)

**Value:** $240,000/year
**Investment:** $140,000/year (Year 1)
**ROI:** 71%

---

### 3 Sites (Production)

**Value:** $720,000/year (3 × $240K)
**Investment:**
- Initial: $50,000 (one-time, already paid)
- Databricks: $180,000/year (1.5x due to efficiency)
- Support: $20,000/year
- **Total: $200,000/year**

**ROI:** 260%
**Payback:** 3 months

---

### 10 Sites (Enterprise)

**Value:** $2,400,000/year (10 × $240K)
**Investment:**
- Databricks: $400,000/year (2x due to economies of scale)
- Support: $50,000/year
- **Total: $450,000/year**

**ROI:** 433%
**Payback:** 2 months

**Note:** Databricks costs scale sub-linearly (shared infrastructure, better pricing at volume)

---

## Non-Financial Benefits

**Not Quantified Above (But Valuable):**

1. **Operator Satisfaction**
   - Less frustration with slow investigations
   - More confidence in decisions
   - Reduced stress

2. **Safety Improvements**
   - Faster identification of hazardous conditions
   - Proactive warnings prevent unsafe situations
   - Better emergency response

3. **Environmental Compliance**
   - Detect emissions or spills earlier
   - Document incidents with AI-generated reports
   - Meet regulatory reporting requirements

4. **Competitive Advantage**
   - Cutting-edge technology attracts talent
   - Differentiation in market
   - Customer/stakeholder confidence

5. **Knowledge Retention**
   - Institutional knowledge captured in data
   - Less dependence on specific individuals
   - Faster onboarding of new staff

---

## Risk Factors

**Factors That Could Reduce ROI:**

1. **Low Adoption**
   - If operators don't use it, value = $0
   - Mitigation: Change management, training, champions

2. **Data Quality Issues**
   - Poor data → poor insights
   - Mitigation: Data cleansing in Silver layer, validation

3. **Incorrect AI Responses**
   - Operators lose trust
   - Mitigation: Human-in-the-loop, confidence scores, validation

4. **Technical Issues**
   - Downtime, latency, bugs
   - Mitigation: Rigorous testing, monitoring, support

5. **Cost Overruns**
   - Databricks consumption higher than expected
   - Mitigation: Cost monitoring, alerts, optimization

---

## Recommendations

**For Financial Approval:**

**Use Moderate Scenario:**
- Value: $240,000/year
- Investment: $140,000 Year 1, $90,000/year ongoing
- Payback: 7 months
- 3-Year NPV: $360,000

**Approval Strategy:**
1. Emphasize downtime prevention (tangible, measurable)
2. Frame operator time savings as productivity, not headcount reduction
3. Highlight platform-agnostic nature (no vendor lock-in)
4. Position as pilot with defined success criteria (low risk)

**Success Criteria for Pilot:**
- Prevent 1+ unplanned shutdown (ROI positive)
- 80%+ operator daily usage (adoption)
- 50%+ reduction in investigation time (efficiency)
- Positive operator feedback (satisfaction)

**If Pilot Succeeds:**
- Expand to additional sites
- Add more data sources (CMMS, ERP)
- Scale to full enterprise deployment

---

## Appendix: Calculation Worksheet

**Customize for Your Site:**

### Inputs (Fill in your numbers)

| Parameter | Your Value | Default |
|-----------|------------|---------|
| Operators per shift | _________ | 10 |
| Investigations per operator per shift | _________ | 5 |
| Avg investigation time (minutes) | _________ | 30 |
| Operator loaded hourly cost | $________ | $45 |
| Unplanned failures per year | _________ | 15 |
| Avg downtime per failure (hours) | _________ | 2.5 |
| Cost per downtime hour | $________ | $25,000 |
| Expected failures prevented | _________ | 3 |
| Expected failures caught early | _________ | 4 |
| Early detection time saved (hours) | _________ | 2 |

---

### Calculated Value

**Time Savings:**
```
Hours saved/shift = Operators × Investigations × (30 - 0.5) / 60
                  = _____ × _____ × 0.49
                  = _____ hours

Annual value = _____ hours × 1,095 shifts × $45
             = $________

Conservative (20%): $________
```

**Downtime Prevention:**
```
Prevention value = _____ failures × _____ hours × $_____ /hour
                 = $________

Early detection = _____ failures × _____ hours × $_____ /hour
                = $________

Total = $________
```

**Total Annual Value:** $________

---

**Investment:**
- Initial: $50,000
- Annual: $90,000
- Year 1 Total: $140,000

**ROI:** (Value - Investment) / Investment × 100% = ______%

**Payback:** Investment / (Value / 12 months) = ______ months

---

**End of Business Value Calculator**

---

## Quick Reference

**Use These Numbers in Presentations:**

- **Time savings:** 30 minutes → 30 seconds (60x faster)
- **Annual value:** $230K - $450K (conservative to moderate)
- **Investment:** $140K Year 1, $90K/year ongoing
- **Payback:** 4-8 months
- **ROI Year 1:** 65-220%
- **3-Year NPV:** $450K - $1M

**Downtime Example:**
- Prevent just 2-3 unplanned shutdowns = ROI positive
- Each 2-hour shutdown costs $50K - $100K
- AI detects issues 2-4 hours earlier

**Operator Impact:**
- 25 hours per shift saved across 10 operators
- Equivalent to 3+ additional operators without hiring
- Faster response, less stress, better decisions
