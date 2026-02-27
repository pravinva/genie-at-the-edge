# Ignition Perspective Views - Complete Implementation Guide

## Overview

This document describes three production-ready Ignition Perspective view JSON files created for the Agentic Ignition HMI system. These views enable operators to interact with the Databricks agent system through a modern, dark-themed interface.

## Files Generated

### 1. `agent_recommendations_view.json` (Main Recommendations Panel)
**Purpose**: Primary interface for operators to review and act on agent recommendations

**Key Features**:
- Dark theme (#1e1e1e background) with Databricks color scheme
- Live database binding to Lakebase every 2 seconds
- Displays up to 50 pending recommendations sorted by priority
- Card-based layout with severity-based border colors
- Header with recommendation count and refresh button
- Empty state handling for zero recommendations

**Components**:
- **Header**: Title, pending count badge, refresh button
- **Recommendations Container**: Scrollable flex container with query binding
- **Repeater**: Instantiates card components for each recommendation
- **Recommendation Cards**:
  - Severity badge (critical=red, high=orange, medium=yellow, low=blue)
  - Equipment ID and timestamp
  - Issue description and recommended action
  - Confidence score (disabled slider 0-100%)
  - Three action buttons: Approve, Defer, Reject

**Database Queries**:
```sql
-- Main data query (2-second poll)
SELECT recommendation_id, equipment_id, issue_description, recommended_action,
       severity, confidence_score, created_timestamp, status, priority
FROM agent_recommendations
WHERE status = 'pending'
ORDER BY priority DESC, created_timestamp DESC
LIMIT 50

-- Approval
UPDATE agent_recommendations
SET status = 'approved', operator_id = :operator_id, approved_timestamp = CURRENT_TIMESTAMP
WHERE recommendation_id = :recommendation_id

-- Deferral (1 hour)
UPDATE agent_recommendations
SET status = 'deferred', defer_until = CURRENT_TIMESTAMP + INTERVAL '1 HOUR'
WHERE recommendation_id = :recommendation_id

-- Rejection with reason
UPDATE agent_recommendations
SET status = 'rejected', rejection_reason = :rejection_reason,
    rejected_timestamp = CURRENT_TIMESTAMP
WHERE recommendation_id = :recommendation_id
```

**Button Scripts**:
- **Approve**: Shows confirmation dialog → runs approveRecommendation query → refreshes view
- **Defer**: Immediately updates to deferred status (no dialog) → refreshes view
- **Reject**: Shows dialog to capture rejection reason → updates with reason → refreshes view

**Dialogs**:
- `ConfirmApprovalDialog`: Simple yes/no confirmation before approving
- `RejectReasonDialog`: Text area to capture reason for rejection

**Styling**:
- Severity border colors change dynamically based on data
- Buttons use Tailwind palette (green=approve, yellow=defer, red=reject)
- Confidence slider is read-only (visual only, not interactive)
- All text is white on dark backgrounds for accessibility

**Binding Configuration**:
```json
{
  "property": "data",
  "type": "query",
  "config": {
    "database": "Lakebase_Connection",
    "pollInterval": 2000,
    "mode": "asynchronous",
    "errorBehavior": "showError"
  }
}
```

---

### 2. `recommendation_card.json` (Reusable Card Component)
**Purpose**: Reusable component for displaying individual recommendation cards

**Key Features**:
- Flex container with border-radius 8px
- Severity-based 3px border (color changes by severity level)
- Expandable section for detailed information
- Complete interactive button scripts
- Hover tooltips on confidence score
- Right-click context menu support (framework)

**Component Structure**:
```
RecommendationCard (Flex Column)
├── Header Row
│   ├── Severity Badge (colored pill)
│   ├── Timestamp
│   └── Expand Button (→)
├── Equipment ID (bold, 16px)
├── Issue Description (14px gray text)
├── Recommended Action Box (dark background)
├── Confidence Meter (progress bar + percentage)
├── Action Buttons Row
│   ├── Approve (green #10b981)
│   ├── Defer (yellow #eab308)
│   └── Reject (red #ef4444)
└── Expanded Details (hidden by default)
    ├── Root Cause Analysis
    ├── Expected Outcome
    └── Similar Historical Incidents
```

**Custom Properties** (Parameters):
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| recommendationId | string | "" | Unique recommendation ID |
| equipmentId | string | "" | Equipment experiencing issue |
| severity | string | "medium" | Severity level (critical/high/medium/low) |
| timestamp | date | null | When recommendation was created |
| issueDescription | string | "" | Description of the issue |
| recommendedAction | string | "" | Recommended action to take |
| confidenceScore | double | 0.5 | Confidence 0-100 |
| operatorId | string | "" | Current operator ID |
| rootCauseAnalysis | string | "" | Genie's root cause explanation |
| expectedOutcome | string | "" | Expected outcome if action taken |
| historicalSimilarIncidents | string | "" | Similar past incidents |

**Interactive Elements**:

1. **Expand Button** (→):
   - Toggles `isExpanded` state
   - Shows/hides expanded details section
   - Reveals root cause, outcomes, and historical incidents

2. **Confidence Score Tooltip**:
   - Hover to show breakdown explanation
   - Lists components: pattern matching, Genie certainty, historical success

3. **Approve Button**:
   - Shows confirmation dialog with equipment name
   - Executes approveRecommendation named query
   - Passes operator_id from session
   - Shows success toast
   - Refreshes parent container

4. **Defer Button**:
   - Immediately defers for 1 hour
   - No confirmation needed
   - Shows info toast
   - Refreshes parent container

5. **Reject Button**:
   - Shows dialog for rejection reason
   - Text area capture
   - Updates with rejection_reason column
   - Shows warning toast
   - Refreshes parent container

**Styling**:
- Border color formula: `if(severity='critical', '#ef4444', if(severity='high', '#f97316', ...))`
- Button colors follow Databricks brand guidelines
- Dark background (#2d2d2d) with light text (#ffffff)
- Hover states with darker background colors
- Active states with even darker backgrounds

**Error Handling**:
All buttons wrapped in try/catch with:
- User-friendly toast messages on error
- Logger.error() calls for debugging
- Validation of required parameters (recommendation_id check)

**Usage in Repeater**:
```json
{
  "type": "ia.component.repeater",
  "props": {
    "instances": "{data}"
  },
  "children": [
    {
      "type": "ia.component.RecommendationCard",
      "binding": {
        "custom.recommendationId": "{instance.recommendation_id}",
        "custom.equipmentId": "{instance.equipment_id}",
        "custom.severity": "{instance.severity}",
        "custom.timestamp": "{instance.created_timestamp}",
        "custom.issueDescription": "{instance.issue_description}",
        "custom.recommendedAction": "{instance.recommended_action}",
        "custom.confidenceScore": "{instance.confidence_score}"
      }
    }
  ]
}
```

---

### 3. `execution_tracker_view.json` (Live Execution Monitor)
**Purpose**: Display currently executing and pending agent commands in real-time

**Key Features**:
- Live data polling every 1 second
- Shows both executing and pending commands
- Real-time elapsed time calculation
- Status badges with pulsing animations
- Value transformation display (old → new)
- Auto-refresh toggle button
- Total counters for executing/pending
- Empty state when no active commands

**Data Query** (1-second poll):
```sql
SELECT command_id, equipment_id, tag_path, old_value, new_value, status,
       created_timestamp, started_timestamp, completed_timestamp, execution_result
FROM agent_commands
WHERE status IN ('pending', 'executing')
ORDER BY CASE WHEN status = 'executing' THEN 0 ELSE 1 END,
         created_timestamp DESC
LIMIT 100
```

**View Layout**:
```
ExecutionTracker (Flex Column, dark background)
├── Header Row
│   ├── Title "Agent Actions"
│   ├── Status Indicators
│   │   ├── Green dot (pulsing) + "N executing"
│   │   ├── Divider
│   │   └── "N pending"
│   └── Auto-Refresh Toggle Button
├── Execution Container (scrollable)
│   ├── For Each Command (Repeater)
│   │   ├── Left Section (flex: 1)
│   │   │   ├── Status Row
│   │   │   │   ├── Status icon (▶ or ⋯)
│   │   │   │   ├── Status badge (EXECUTING/PENDING)
│   │   │   │   ├── Arrow separator
│   │   │   │   └── Created timestamp
│   │   │   ├── Equipment ID (bold)
│   │   │   ├── Tag path (monospace)
│   │   │   └── Value transformation
│   │   │       ├── Old value (dark box)
│   │   │       ├── Arrow (→)
│   │   │       └── New value (green box)
│   │   └── Right Section (min-width: 150px)
│   │       ├── Time Elapsed Counter
│   │       │   ├── Label "Time Elapsed"
│   │       │   └── Dynamic time (m's format)
│   │       └── Status Indicator
│   │           ├── Text (⟳ Executing... or Queued)
│   │           └── Pulsing dots (if executing)
│   └── Empty State (when no commands)
│       ├── Checkmark icon (✓)
│       ├── "All Caught Up"
│       └── "No pending or executing commands"
├── Footer
│   ├── Last updated timestamp
│   └── Auto-refresh status
└── Custom Properties
    ├── executionData (array)
    ├── totalExecuting (int)
    ├── totalPending (int)
    ├── autoRefreshEnabled (bool)
    └── refreshInterval (int = 1000ms)
```

**Status Indicators**:
- **Executing**:
  - Icon: ▶ (green)
  - Color: #10b981
  - Badge: "EXECUTING" with green background
  - Animation: Pulsing dots at bottom
  - Time: Real-time elapsed from started_timestamp

- **Pending**:
  - Icon: ⋯ (amber)
  - Color: #fbbf24
  - Badge: "PENDING" with amber background
  - Animation: None (static)
  - Time: "Waiting" text

**Real-Time Elapsed Time Calculation**:
```sql
-- For executing commands
FLOOR((UNIX_TIMESTAMP(CURRENT_TIMESTAMP()) - UNIX_TIMESTAMP(started_timestamp)) / 60)
+ 'm ' +
MOD((UNIX_TIMESTAMP(CURRENT_TIMESTAMP()) - UNIX_TIMESTAMP(started_timestamp)), 60) + 's'

-- For completed commands
FLOOR((UNIX_TIMESTAMP(completed_timestamp) - UNIX_TIMESTAMP(started_timestamp)) / 60)
+ 'm ' +
MOD((UNIX_TIMESTAMP(completed_timestamp) - UNIX_TIMESTAMP(started_timestamp)), 60) + 's'
```

**Value Transformation Display**:
- **Old Value**: Dark background (#1e1e1e), white text
- **Arrow**: Gray divider (→)
- **New Value**: Green background (rgba(16, 185, 129, 0.1)), green text
- All values in monospace font for clarity

**Auto-Refresh Toggle**:
- Button: "⟳ Auto" in header
- Click toggles `autoRefreshEnabled` state
- When ON: Button highlights in blue (#2563eb)
- When OFF: Button returns to gray (#374151)
- Controls polling of executionContainer binding

**Binding Configuration**:
```json
{
  "property": "data",
  "type": "query",
  "config": {
    "database": "Lakebase_Connection",
    "pollInterval": 1000,
    "mode": "asynchronous",
    "errorBehavior": "showError"
  }
}
```

**Total Counters** (separate bindings):
- `custom.totalExecuting`: Polled every 1 second from COUNT query
- `custom.totalPending`: Polled every 1 second from COUNT query
- Displayed in header as "N executing • N pending"

**Empty State**:
- Shows when `len(data) = 0`
- Large checkmark (✓)
- "All Caught Up" message
- "No pending or executing commands" subtext

**Animations**:
- Pulsing dots use CSS animation (opacity: 1 → 0.5 → 1)
- Staggered timing (0s, 0.33s, 0.66s) for wave effect
- Green dot in header pulses continuously when executing commands exist

---

## Installation & Configuration

### Prerequisites
1. Ignition gateway with Perspective module installed
2. Lakebase database connection configured as "Lakebase_Connection"
3. Required database tables:
   - `agent_recommendations` (with columns: recommendation_id, equipment_id, issue_description, recommended_action, severity, confidence_score, created_timestamp, status, priority, operator_id, approved_timestamp, rejection_reason, rejected_timestamp, defer_until)
   - `agent_commands` (with columns: command_id, equipment_id, tag_path, old_value, new_value, status, created_timestamp, started_timestamp, completed_timestamp, execution_result)

### Step 1: Create Lakebase Connection

In Ignition Gateway:
1. Go to **Configure → Database Connections**
2. Click **Create new Database Connection**
3. Configure:
   - **Name**: `Lakebase_Connection`
   - **Driver**: PostgreSQL
   - **URL**: `jdbc:postgresql://[workspace].cloud.databricks.com:5432/lakebase`
   - **Username**: `token`
   - **Password**: [Your Databricks PAT]
4. Test connection, then click Save

### Step 2: Create Named Queries

In Ignition Designer:
1. Go to **Project → Databases → Named Queries**
2. Create the following named queries:

**approveRecommendation**:
```sql
UPDATE agent_recommendations
SET status = 'approved',
    operator_id = :operator_id,
    approved_timestamp = CURRENT_TIMESTAMP
WHERE recommendation_id = :recommendation_id
```

**deferRecommendation**:
```sql
UPDATE agent_recommendations
SET status = 'deferred',
    defer_until = CURRENT_TIMESTAMP + INTERVAL '1 HOUR'
WHERE recommendation_id = :recommendation_id
```

**rejectRecommendation**:
```sql
UPDATE agent_recommendations
SET status = 'rejected',
    rejection_reason = :rejection_reason,
    rejected_timestamp = CURRENT_TIMESTAMP
WHERE recommendation_id = :recommendation_id
```

**countPendingRecommendations**:
```sql
SELECT COUNT(*) as count FROM agent_recommendations WHERE status = 'pending'
```

### Step 3: Import Views

**Option A: Manual JSON Import**
1. In Ignition Designer, right-click project → **Import Project Resource**
2. Select each `.json` file
3. Choose target folder (e.g., `views/agent/`)
4. Click Import

**Option B: Copy to Project Directory**
1. Locate Ignition project directory: `[Ignition Dir]/projects/[ProjectName]/`
2. Copy `agent_recommendations_view.json` to `views/`
3. Copy `recommendation_card.json` to `components/`
4. Copy `execution_tracker_view.json` to `views/`
5. Ignition will auto-detect and load views

### Step 4: Configure Session Properties

In the view's properties, ensure these session properties exist:
- `operatorId` (string): Set from login/session
- `databricks_workspace_id` (string): For API integration
- `databricks_token` (string): For API integration (encrypted storage)

### Step 5: Test in Perspective

1. Open Ignition Perspective client
2. Navigate to view: `/path/to/AgentRecommendations`
3. Should display empty state initially
4. Insert test data in Lakebase:
   ```sql
   INSERT INTO agent_recommendations
   (recommendation_id, equipment_id, issue_description, recommended_action,
    severity, confidence_score, created_timestamp, status, priority)
   VALUES
   ('test-001', 'REACTOR_01', 'High temperature detected',
    'Reduce feed rate by 10%', 'high', 0.85, CURRENT_TIMESTAMP, 'pending', 1)
   ```
5. Recommendation should appear in view within 2 seconds

---

## Data Model

### agent_recommendations Table
```sql
CREATE TABLE agent_recommendations (
    recommendation_id STRING NOT NULL PRIMARY KEY,
    equipment_id STRING NOT NULL,
    issue_description STRING,
    recommended_action STRING,
    severity STRING,  -- critical, high, medium, low
    confidence_score DOUBLE,  -- 0.0 to 100.0
    created_timestamp TIMESTAMP,
    status STRING,  -- pending, approved, rejected, deferred, executed
    priority INT,  -- 1-5 (1 = highest)
    operator_id STRING,
    approved_timestamp TIMESTAMP,
    rejection_reason STRING,
    rejected_timestamp TIMESTAMP,
    defer_until TIMESTAMP,
    root_cause_analysis STRING,
    expected_outcome STRING
)
```

### agent_commands Table
```sql
CREATE TABLE agent_commands (
    command_id STRING NOT NULL PRIMARY KEY,
    recommendation_id STRING,
    equipment_id STRING NOT NULL,
    tag_path STRING NOT NULL,
    old_value STRING,
    new_value STRING,
    status STRING,  -- pending, executing, executed, failed
    created_timestamp TIMESTAMP,
    started_timestamp TIMESTAMP,
    completed_timestamp TIMESTAMP,
    execution_result STRING,
    executed_by STRING
)
```

---

## Performance Tuning

### Query Optimization
1. **Add indexes** to Lakebase:
   ```sql
   CREATE INDEX idx_recommendations_status
   ON agent_recommendations(status, priority, created_timestamp);

   CREATE INDEX idx_commands_status
   ON agent_commands(status, created_timestamp);
   ```

2. **Adjust poll intervals** if needed:
   - Agent Recommendations: Default 2 seconds (can reduce to 1 if needed)
   - Execution Tracker: Default 1 second (critical for real-time feel)
   - Adjust in binding config: `"pollInterval": 2000`

3. **Limit results**:
   - Default: 50 recommendations, 100 commands
   - Adjust `LIMIT` clause in queries

### Memory Management
- Repeater components can handle 100+ items
- For 1000+ items, implement pagination instead

---

## Troubleshooting

### Views Not Showing Data
1. **Check database connection**:
   - Go to gateway → Configure → Database Connections
   - Test "Lakebase_Connection" connection
   - Verify credentials and permissions

2. **Check named queries**:
   - Go to Designer → Project → Databases → Named Queries
   - Verify all 4 queries exist
   - Test each one manually (right-click → Test)

3. **Check table permissions**:
   ```sql
   GRANT SELECT, UPDATE ON agent_recommendations TO token;
   GRANT SELECT ON agent_commands TO token;
   ```

### Buttons Not Working
1. **Check script syntax**:
   - View logs in gateway: Configure → Logging
   - Look for "script error" messages

2. **Check database connection in script**:
   - Ensure `database='Lakebase_Connection'` in all queries
   - Test named query directly in Designer

3. **Check dialogs**:
   - Verify dialog names match script references
   - Dialogs defined inline in JSON (should load automatically)

### Slow Performance
1. **Check poll interval**:
   - Reduce from 2s to 3-4s if network latency high
   - Monitor gateway CPU usage

2. **Check query performance**:
   ```sql
   EXPLAIN SELECT * FROM agent_recommendations
   WHERE status = 'pending'
   ORDER BY priority DESC, created_timestamp DESC LIMIT 50;
   ```

3. **Monitor active sessions**:
   - Gateway → Status → Security → Perspective Sessions
   - Check for long-running queries

---

## Customization

### Change Colors
All colors defined at top of JSON. Search and replace:
- `#1e1e1e` - Dark background
- `#2d2d2d` - Card background
- `#ef4444` - Critical severity (red)
- `#f97316` - High severity (orange)
- `#eab308` - Medium severity (yellow)
- `#3b82f6` - Low severity (blue)
- `#10b981` - Success/approve (green)

### Add New Severity Level
1. Update `severity_colors` in CSS section
2. Update border color expression in component
3. Add to SELECT statement filter if needed

### Add New Status
1. Update status values in queries (where `status IN (...)`)
2. Add new case to status badge color expression
3. Add icon and animation if needed

### Customize Dialogs
Modify `dialogs` section in JSON:
- Change dialog title
- Modify text prompts
- Add/remove input fields
- Update button styles

### Add Right-Click Context Menu
Extend recommendation card with:
```json
"events": {
  "onContextMenu": {
    "script": "def runAction(self, event):\n  system.perspective.openPopupMenu(\n    {'View Details': view_details, 'Escalate': escalate},\n    x=event.x, y=event.y\n  )"
  }
}
```

---

## Integration Points

### With Databricks Agent
- Agent inserts recommendations → appear in view within 2 seconds
- Agent queries approval status → sees `status='approved'`
- Agent creates commands → appear in execution tracker within 1 second

### With Ignition Tag System
- Tag path from `agent_commands` table points to real Ignition tags
- Execution tracker shows old value → new value transformation
- Completion writes to `completed_timestamp` and `execution_result`

### With Operator Session
- `operatorId` from session captured in approval
- Audit trail shows who approved each recommendation
- Session timeout clears pending dialogs

---

## Security Considerations

1. **Database Credentials**:
   - Store Databricks PAT in Ignition secrets
   - Never commit tokens to version control
   - Rotate tokens periodically

2. **Row-Level Security**:
   - Consider RLS on `agent_recommendations` by equipment_id
   - Restrict operators to their assigned equipment types

3. **Query Auditing**:
   - Enable Lakebase query logging for compliance
   - Archive audit trail to separate table monthly

4. **Dialog Validation**:
   - Client-side validation (JavaScript)
   - Server-side validation in named queries (NOT BYPASSED)

---

## API Reference

### Named Queries

#### approveRecommendation
```
Parameters:
  - recommendation_id (STRING): ID to approve
  - operator_id (STRING): Operator performing approval

Returns: 1 row affected
```

#### deferRecommendation
```
Parameters:
  - recommendation_id (STRING): ID to defer

Returns: 1 row affected
Effects: Sets defer_until = now() + 1 hour
```

#### rejectRecommendation
```
Parameters:
  - recommendation_id (STRING): ID to reject
  - rejection_reason (STRING): Reason for rejection

Returns: 1 row affected
```

#### countPendingRecommendations
```
Returns: Single row with 'count' column
Example: {count: 5}
```

---

## Deployment Checklist

- [ ] Lakebase connection "Lakebase_Connection" configured
- [ ] All 4 named queries created and tested
- [ ] Database tables exist with correct schemas
- [ ] Views imported into Ignition project
- [ ] Session property "operatorId" configured
- [ ] Test data inserted
- [ ] Views display test data within 2-4 seconds
- [ ] Approval button works (updates database)
- [ ] Defer button works
- [ ] Reject button shows dialog and works
- [ ] Execution tracker shows live commands
- [ ] Auto-refresh toggle functional
- [ ] All error toasts display correctly
- [ ] Performance acceptable (no lag)
- [ ] Database indexes created for performance

---

## File Sizes & Performance

| File | Size | Components | Bindings | Scripts |
|------|------|------------|----------|---------|
| agent_recommendations_view.json | ~18KB | 15+ | 4 | 15+ |
| recommendation_card.json | ~22KB | 20+ | 0 | 8+ |
| execution_tracker_view.json | ~19KB | 25+ | 3 | 2 |
| **Total** | **~59KB** | **60+** | **7** | **25+** |

---

## Support & Maintenance

### Version History
- v1.0 (2026-02-19): Initial release
  - agent_recommendations_view.json
  - recommendation_card.json
  - execution_tracker_view.json

### Known Limitations
1. Dialogs require browser modern JavaScript support
2. Emoji icons (✓, ✗, ⟳) may not render on all browsers
3. CSS animations not supported in older Perspective versions
4. Maximum 100 displayed items in repeaters (by design)

### Future Enhancements
1. Drag-to-reorder priorities
2. Bulk approval (select multiple)
3. Advanced filtering by equipment type
4. Real-time notification badges
5. Export audit trail to CSV
6. Mobile-responsive design

---

## License

These views are generated for use with Databricks and Ignition platforms.

---

**Generated**: 2026-02-19
**Author**: Claude Code
**Framework**: Ignition Perspective 8.3+
**Database**: Lakebase (Postgres-compatible)
