# Agentic HMI Architecture - Gap Analysis

**Date**: 2026-02-21
**Analysis**: Implementation vs Dashboard Architecture
**Scope**: What's built vs what's needed for production

---

## Executive Summary

Based on the deployed dashboard architecture and implementation review, there are **4 critical gaps** in the current system that prevent it from matching the event-driven, sub-100ms architecture shown in the demo dashboard.

**What Works**: ML model generates recommendations, stores in Lakebase, displays in Perspective
**What's Missing**: Real-time PostgreSQL NOTIFY webhooks, JDBC write-back, on-demand Genie integration

---

## Architecture: Intended vs Implemented

### Intended Architecture (From Dashboard)

```
Sensor Data → ML Model → Lakebase → PostgreSQL NOTIFY → Ignition (< 100ms)
                                        ↓
Operator Decision → JDBC Write → Lakebase → Feedback Loop
                                        ↓
"Ask AI Why" Button → Genie API → Explanation (on-demand only)
```

### Current Implementation

```
Sensor Data → ML Model → Lakebase (JDBC batch write)
                                        ↓
Ignition polls Lakebase every 2 seconds → Display
                                        ↓
Operator Decision → Named Query → Lakebase UPDATE
                                        ↓
Genie Proxy Server (separate, not integrated with recommendations)
```

---

## Gap 1: Lakebase PostgreSQL NOTIFY Webhooks (NOT IMPLEMENTED)

### What the Dashboard Shows
- "Lakebase fires PostgreSQL NOTIFY webhook to Ignition in under 100ms"
- Event-driven push notifications
- Real-time operator alerts

### Current Implementation
**File**: `/Users/pravin.varma/Documents/Demo/genie-at-the-edge/databricks/lakebase_streaming_sink.py`

```python
# Current approach: Batch write to Lakebase via JDBC
def write_recommendations(df, epoch_id):
    df.write.mode("append").jdbc(
        url=CONFIG["lakebase_url"],
        table="agentic_hmi.ml_recommendations",
        properties={...}
    )
```

**Problem**: No PostgreSQL NOTIFY trigger after insert

### What's Missing

**Lakebase Trigger Function** (NOT CREATED):
```sql
-- This does NOT exist in the codebase
CREATE OR REPLACE FUNCTION notify_new_recommendation()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'new_recommendation',
        json_build_object(
            'recommendation_id', NEW.recommendation_id,
            'equipment_id', NEW.equipment_id,
            'severity', NEW.severity,
            'urgency', NEW.urgency,
            'confidence_score', NEW.confidence_score
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER recommendation_inserted
AFTER INSERT ON lakebase.agentic_hmi.agent_recommendations
FOR EACH ROW
EXECUTE FUNCTION notify_new_recommendation();
```

**Ignition Listener** (NOT CREATED):
```python
# This gateway script does NOT exist
# Location: Ignition Gateway Event Scripts
import psycopg2
import select

def listen_for_recommendations():
    """
    Subscribe to PostgreSQL NOTIFY channel
    Push to Perspective sessions in < 100ms
    """
    conn = psycopg2.connect(LAKEBASE_CONNECTION)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Subscribe to notification channel
    cursor.execute("LISTEN new_recommendation;")

    while True:
        # Wait for notification (non-blocking)
        if select.select([conn], [], [], 5) == ([], [], []):
            continue

        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            payload = json.loads(notify.payload)

            # Push to all Perspective sessions immediately
            system.perspective.sendMessage(
                messageType='NEW_ML_RECOMMENDATION',
                payload=payload,
                scope='page'
            )
```

**Status**: ❌ NOT IMPLEMENTED
**Impact**: 2-second polling delay instead of <100ms push notifications
**Effort**: 4-8 hours to implement trigger + listener

---

## Gap 2: Operator JDBC Write-Back (PARTIALLY IMPLEMENTED)

### What the Dashboard Shows
- "Operators write decisions directly back to Lakebase via JDBC"
- Immediate feedback loop to ML model
- Real-time decision tracking

### Current Implementation
**File**: `/Users/pravin.varma/Documents/Demo/genie-at-the-edge/ignition/agent_recommendations_view.json`

```javascript
// Approve button calls named query
system.db.runNamedQuery(
    "approveRecommendation",
    {"recommendation_id": recommendationId}
)
```

**File**: `/Users/pravin.varma/Documents/Demo/genie-at-the-edge/operations_agent.py`

```python
# Agent polls for approvals (NOT direct JDBC write-back)
def process_approvals(self):
    query = """
        SELECT recommendation_id, equipment_id, recommended_action
        FROM agent_recommendations
        WHERE status = 'approved'
    """
    approved_recs = self._execute_query(query)
```

**What Works**:
✅ Operators can approve/reject via Perspective
✅ Status updates written to Lakebase
✅ Named queries execute updates

**What's Missing**:
❌ No direct JDBC connection from Perspective to Lakebase (uses named queries instead)
❌ No real-time write-back confirmation to operator
❌ No optimistic UI updates (must wait for next poll cycle)

### What Should Be Implemented

**Direct JDBC Write from Perspective**:
```python
# Perspective button script (NOT using named queries)
def onActionPerformed(self, event):
    import system.db as db

    # Direct JDBC write to Lakebase
    conn = system.db.getConnection("Lakebase_JDBC")

    try:
        # Write decision immediately
        db.runPrepUpdate(
            """
            UPDATE lakebase.agentic_hmi.agent_recommendations
            SET status = ?,
                operator_id = ?,
                approved_timestamp = NOW(),
                operator_notes = ?
            WHERE recommendation_id = ?
            """,
            ['approved', self.session.props.auth.user.username, '', self.custom.rec_id],
            "Lakebase_JDBC"
        )

        # Optimistic UI update (don't wait for poll)
        self.parent.custom.recommendations = [
            r for r in self.parent.custom.recommendations
            if r['recommendation_id'] != self.custom.rec_id
        ]

        # Show immediate feedback
        system.perspective.print("✅ Decision written to Lakebase in 150ms")

    finally:
        db.closeConnection(conn)
```

**Status**: 🟡 PARTIALLY IMPLEMENTED (via named queries, not direct JDBC)
**Impact**: Adds 2-second delay for operator feedback
**Effort**: 2-4 hours to refactor to direct JDBC

---

## Gap 3: On-Demand Genie Integration (NOT INTEGRATED)

### What the Dashboard Shows
- "Genie is the on-demand expert, called only when an operator clicks 'Ask AI Why'"
- Button-triggered AI explanations
- Context-aware answers about specific recommendations

### Current Implementation

**Genie Proxy Exists**: `/Users/pravin.varma/Documents/Demo/genie-at-the-edge/ignition/scripts/genie_proxy.py`
```python
# Standalone proxy server on port 8185
# NOT integrated with recommendation cards
def do_POST(self):
    if self.path == '/api/genie/query':
        # Handles generic Genie queries
        # No context about recommendations
```

**Perspective Views**: `/Users/pravin.varma/Documents/Demo/genie-at-the-edge/ignition/agent_recommendations_view.json`
```json
// Action buttons: Approve, Defer, Reject
// NO "Ask AI Why" button exists
{
  "children": [
    {"text": "Approve"},
    {"text": "Defer"},
    {"text": "Reject"}
    // Missing: {"text": "Ask AI Why"}
  ]
}
```

**What's Missing**:

1. **"Ask AI Why" Button** (NOT IN UI)
2. **Context-Aware Genie Queries** (NOT IMPLEMENTED)
3. **Integration with Recommendation Data** (NOT CONNECTED)

### What Should Be Implemented

**Add Button to Recommendation Card**:
```json
{
  "type": "ia.display.button",
  "props": {
    "text": "Ask AI Why",
    "style": {
      "backgroundColor": "#3b82f6",
      "color": "#ffffff"
    }
  },
  "events": {
    "onActionPerformed": {
      "script": "# Call Genie with recommendation context"
    }
  }
}
```

**Context-Aware Genie Query**:
```python
# Perspective button script
def onActionPerformed(self, event):
    import system.net.httpClient as http
    import json

    # Get recommendation details
    rec = self.parent.custom.recommendationData

    # Build context-rich question for Genie
    context = f"""
    Equipment: {rec['equipment_id']}
    Issue: {rec['issue_description']}
    ML Recommendation: {rec['recommended_action']}
    Confidence: {rec['confidence_score']:.0%}
    Sensor Value: {rec['temperature_reading']}°C
    """

    question = f"""
    Why is the AI recommending this action for {rec['equipment_id']}?

    Context:
    {context}

    Provide:
    1. Root cause explanation
    2. Why this specific action was chosen
    3. Expected outcome if followed
    4. Risks if ignored
    """

    # Call Genie proxy with context
    response = http.post(
        url="http://localhost:8185/api/genie/query",
        contentType="application/json",
        postData=json.dumps({"question": question})
    )

    # Display Genie response in popup
    result = json.loads(response)
    system.perspective.openPopup(
        id="GenieExplanation",
        view="Popups/GenieExplanation",
        params={
            'recommendation_id': rec['recommendation_id'],
            'genie_response': result['response'],
            'suggested_questions': result.get('suggestedQuestions', [])
        },
        position={'w': 800, 'h': 600}
    )
```

**Status**: ❌ NOT IMPLEMENTED
**Impact**: Operators cannot get AI explanations for recommendations
**Effort**: 6-8 hours (button + popup + integration)

---

## Gap 4: ML Model Auto-Generation Without Human Intervention (WORKING BUT UNCLEAR)

### What the Dashboard Shows
- "ML model auto-generates recommendations without human intervention"
- Continuous pipeline from anomaly → recommendation
- No manual steps

### Current Implementation

**Works**: `/Users/pravin.varma/Documents/Demo/genie-at-the-edge/databricks/ml_recommendation_pipeline_with_webhooks.py`

```python
@dlt.table(name="ml_recommendations_gold")
def generate_ml_recommendations():
    """
    Generate recommendations using ML model (NOT Genie)
    """
    recommendation_model = mlflow.pyfunc.load_model(
        "models:/equipment_recommendation_engine/production"
    )

    # Auto-generates recommendations from anomalies
    return anomalies.withColumn("recommendation",
        generate_recommendation_udf(...)
    )
```

**Confusion**: Multiple architectures documented

**File 1**: `/Users/pravin.varma/Documents/Demo/genie-at-the-edge/agentic_hmi/COMPLETE_DATA_FLOW_ARCHITECTURE.md`
```markdown
### Stage 4: ML + Genie → AI Recommendations (CRITICAL STEP)
This is where Genie transforms raw anomalies into actionable intelligence
```
**Indicates**: Genie generates recommendations

**File 2**: `/Users/pravin.varma/Documents/Demo/genie-at-the-edge/databricks/corrected_ml_driven_architecture.py`
```python
# MAGIC # CORRECTED: ML-Driven Recommendation Architecture
# MAGIC ML model generates recommendations automatically
# MAGIC Genie is ONLY used when operator explicitly asks
```
**Indicates**: ML generates recommendations, Genie is on-demand

**Status**: ✅ WORKING (ML auto-generates recommendations)
**Issue**: ⚠️ Documentation confusion (which architecture is correct?)
**Impact**: Training materials conflict with implementation
**Effort**: 1-2 hours to align documentation

---

## Summary Table: Implementation Gaps

| Feature | Dashboard Shows | Current Status | Gap | Effort |
|---------|----------------|----------------|-----|--------|
| **PostgreSQL NOTIFY** | Lakebase fires webhooks <100ms | Polling every 2 seconds | ❌ Missing trigger + listener | 4-8h |
| **JDBC Write-Back** | Direct JDBC from Perspective | Named queries (slower) | 🟡 Partial | 2-4h |
| **"Ask AI Why" Button** | On-demand Genie expert | Not in UI | ❌ Missing button + integration | 6-8h |
| **ML Auto-Generation** | ML generates recommendations | Working correctly | ⚠️ Doc confusion | 1-2h |

**Total Estimated Effort**: 13-22 hours to close all gaps

---

## Recommended Implementation Priority

### Phase 1: Quick Wins (4-6 hours)
1. **Fix Documentation** (1-2h)
   - Clarify ML vs Genie roles
   - Update COMPLETE_DATA_FLOW_ARCHITECTURE.md
   - Align all references

2. **Add "Ask AI Why" Button** (3-4h)
   - Add button to recommendation card
   - Create Genie explanation popup
   - Wire to existing Genie proxy

### Phase 2: Performance Boost (6-10 hours)
3. **Implement Direct JDBC Write** (2-4h)
   - Replace named queries with direct JDBC
   - Add optimistic UI updates
   - Show <200ms operator feedback

4. **PostgreSQL NOTIFY Triggers** (4-6h)
   - Create Lakebase trigger function
   - Build Ignition gateway listener
   - Test end-to-end <100ms delivery

### Phase 3: Polish (2-4 hours)
5. **Integration Testing** (2-3h)
   - Test complete flow under load
   - Verify sub-100ms notifications
   - Validate operator workflows

6. **Documentation Update** (1h)
   - Update architecture diagrams
   - Record actual latencies
   - Create operator training guide

---

## Files That Need Changes

### Create New Files
```
databricks/lakebase_notify_trigger.sql          (NEW - PostgreSQL trigger)
ignition/gateway_scripts/lakebase_listener.py   (NEW - NOTIFY listener)
ignition/perspective_views/genie_explanation_popup.json  (NEW - AI popup)
```

### Modify Existing Files
```
ignition/agent_recommendations_view.json         (ADD "Ask AI Why" button)
ignition/recommendation_card.json                (ADD Genie integration)
databricks/lakebase_streaming_sink.py            (ADD trigger after insert)
agentic_hmi/COMPLETE_DATA_FLOW_ARCHITECTURE.md   (FIX ML vs Genie roles)
```

---

## Critical Decision Points

### 1. Real-Time vs Polling Trade-off
**Current**: 2-second polling (simple, reliable)
**Proposed**: <100ms PostgreSQL NOTIFY (complex, faster)

**Question**: Is <100ms critical for your operators?
- If YES → Implement NOTIFY (Phase 2)
- If NO → Keep polling, focus on "Ask AI Why" (Phase 1)

### 2. Genie Usage Pattern
**Current**: Genie proxy exists but not integrated
**Proposed**: On-demand via "Ask AI Why" button

**Question**: Do operators need AI explanations?
- If YES → Implement button (high value)
- If NO → Remove Genie references (reduce confusion)

### 3. JDBC vs Named Queries
**Current**: Named queries (Ignition best practice)
**Proposed**: Direct JDBC (faster, more complex)

**Question**: Is 2-second feedback delay acceptable?
- If YES → Keep named queries
- If NO → Implement direct JDBC

---

## Testing Checklist for Gaps

Once implemented, validate with:

### PostgreSQL NOTIFY
- [ ] Trigger fires on INSERT to agent_recommendations
- [ ] Ignition listener receives notification <100ms
- [ ] Perspective session updates without polling
- [ ] No duplicate notifications
- [ ] Reconnects on connection loss

### "Ask AI Why" Button
- [ ] Button appears on all recommendation cards
- [ ] Calls Genie proxy with recommendation context
- [ ] Popup displays within 3 seconds
- [ ] Response is contextually relevant
- [ ] Suggested questions work
- [ ] Conversation history maintained

### Direct JDBC Write-Back
- [ ] Operator decision written to Lakebase
- [ ] UI updates optimistically (no wait)
- [ ] Rollback on write failure
- [ ] Audit trail captures operator_id
- [ ] Timestamp accurate to millisecond

---

## Conclusion

**Production-Ready**: ML recommendation pipeline works correctly
**Missing for Demo**: Real-time webhooks and on-demand AI explanations
**Total Effort**: 13-22 hours to match dashboard architecture
**Biggest Impact**: "Ask AI Why" button (operator value) + PostgreSQL NOTIFY (demo wow factor)

---

**Generated**: 2026-02-21
**Analyzed By**: Claude Code
**Files Reviewed**: 12+ implementation files
**Recommendation**: Implement Phase 1 first (Ask AI Why), then assess if real-time NOTIFY is needed
