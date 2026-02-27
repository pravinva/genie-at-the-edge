# Agentic HMI Views - Validation Checklist

Use this checklist to verify all three Perspective views are configured and working correctly.

## Pre-Deployment Validation

### JSON File Integrity
- [ ] `agent_recommendations_view.json` exists (17-18 KB)
- [ ] `recommendation_card.json` exists (21-22 KB)
- [ ] `execution_tracker_view.json` exists (19-20 KB)
- [ ] All files are valid JSON (no syntax errors)
  ```bash
  python -m json.tool agent_recommendations_view.json > /dev/null && echo "Valid"
  ```

### File Content Verification
```bash
# Check required sections in each file
grep -q '"docType"' agent_recommendations_view.json && echo "✓"
grep -q '"namedQueries"' agent_recommendations_view.json && echo "✓"
grep -q '"dialogs"' agent_recommendations_view.json && echo "✓"

grep -q '"parameterDefinitions"' recommendation_card.json && echo "✓"
grep -q '"styling"' recommendation_card.json && echo "✓"
grep -q '"interactions"' recommendation_card.json && echo "✓"

grep -q '"features"' execution_tracker_view.json && echo "✓"
grep -q '"performance"' execution_tracker_view.json && echo "✓"
```

## Database Validation

### Connection Test
```sql
-- In Lakebase, verify connectivity:
SELECT 'Connection OK' as status;
```
- [ ] Lakebase connection from Ignition works
- [ ] Authentication token valid
- [ ] Network latency acceptable (<100ms)

### Table Structure Validation
```sql
-- Verify all required columns exist:

-- agent_recommendations table
SELECT recommendation_id, equipment_id, issue_description, recommended_action,
       severity, confidence_score, created_timestamp, status, priority,
       operator_id, approved_timestamp, rejection_reason, rejected_timestamp,
       defer_until
FROM agent_recommendations
LIMIT 0;

-- agent_commands table
SELECT command_id, equipment_id, tag_path, old_value, new_value, status,
       created_timestamp, started_timestamp, completed_timestamp, execution_result
FROM agent_commands
LIMIT 0;
```
- [ ] agent_recommendations table has all 14 columns
- [ ] agent_commands table has all 10 columns
- [ ] All columns have correct data types

### Sample Data Validation
```sql
-- Insert test data
INSERT INTO agent_recommendations (
    recommendation_id, equipment_id, issue_description, recommended_action,
    severity, confidence_score, created_timestamp, status, priority
) VALUES (
    'test-rec-001', 'REACTOR_01', 'Test issue', 'Test action',
    'high', 0.85, CURRENT_TIMESTAMP, 'pending', 1
);

-- Verify it exists
SELECT COUNT(*) FROM agent_recommendations WHERE recommendation_id = 'test-rec-001';
```
- [ ] Insert test recommendation succeeds
- [ ] SELECT returns 1 row
- [ ] All fields populated correctly
- [ ] Can be updated (test UPDATE status = 'approved')
- [ ] Can be deleted (cleanup)

## Ignition Configuration Validation

### Database Connection
**In Gateway Configure → Database Connections**:
- [ ] Connection "Lakebase_Connection" exists
- [ ] Status shows "Valid" (green checkmark)
- [ ] Test Connection button succeeds
- [ ] Can execute test query: `SELECT 1`
- [ ] Timeout reasonable (<5 seconds)

### Named Queries
**In Designer → Project → Databases → Named Queries**:

**approveRecommendation**:
```bash
✓ Query exists
✓ SQL valid
✓ Parameters: recommendation_id, operator_id
✓ Manual test succeeds with sample IDs
✓ Can execute with test data
```
- [ ] All 4 named queries exist
- [ ] Each query SQL is valid
- [ ] Parameters match script references
- [ ] Each query can be tested manually
- [ ] Test data reflects in database

**Test SQL Syntax**:
```sql
-- In Designer, right-click query → Test
-- Provide test parameters:
recommendation_id = 'test-rec-001'
operator_id = 'test-operator'

-- Should show: 1 rows affected
```

### View Import
**In Designer → Views**:
- [ ] `AgentRecommendations` view exists
- [ ] `ExecutionTracker` view exists
- [ ] `RecommendationCard` component exists
- [ ] All views compile without errors
- [ ] No red X icons (broken references)

**Check View Properties**:
- [ ] Root element is flex container
- [ ] Background color is #1e1e1e
- [ ] Bindings show proper query references
- [ ] Scripts have correct syntax

## Perspective Session Validation

### View Loading
**In Perspective Client**:
- [ ] Can navigate to AgentRecommendations view
- [ ] View loads without errors
- [ ] No 404 or resource not found errors
- [ ] View displays within 5 seconds
- [ ] All UI elements visible (header, buttons, containers)

### Empty State
- [ ] Empty state shows when no pending recommendations
- [ ] Message reads "No Pending Recommendations"
- [ ] Checkmark icon visible
- [ ] "All equipment operating normally" message shown

### Data Display (with test data)
**Insert test recommendation**:
```sql
INSERT INTO agent_recommendations (
    recommendation_id, equipment_id, issue_description, recommended_action,
    severity, confidence_score, created_timestamp, status, priority
) VALUES (
    'test-card-001', 'PUMP_02', 'Vibration threshold exceeded',
    'Schedule bearing replacement', 'critical', 0.92, CURRENT_TIMESTAMP, 'pending', 1
);
```

- [ ] Recommendation appears within 2 seconds
- [ ] Equipment ID displays: "PUMP_02"
- [ ] Issue description visible
- [ ] Recommended action in dark box
- [ ] Severity badge shows "critical" in red
- [ ] Confidence shows 92%
- [ ] Three buttons visible (Approve, Defer, Reject)

### Button Functionality

**Approve Button**:
- [ ] Click shows confirmation dialog
- [ ] Dialog says "Are you sure..."
- [ ] Click "Cancel" closes dialog (no changes)
- [ ] Click "Confirm" updates database
- [ ] Toast shows "Approved! Agent will execute shortly."
- [ ] Database shows: status='approved', operator_id set
- [ ] Recommendation disappears from view (no longer pending)
- [ ] Toast notifications appear (success/error messages)

**Defer Button**:
- [ ] Click immediately defers (no dialog)
- [ ] Toast shows "Deferred for 1 hour."
- [ ] Database shows: status='deferred', defer_until set
- [ ] Recommendation disappears from view

**Reject Button**:
- [ ] Click shows reason dialog
- [ ] Can type rejection reason
- [ ] Click "Cancel" cancels (no changes)
- [ ] Click "Reject" with empty reason shows warning
- [ ] Click "Reject" with reason updates database
- [ ] Toast shows "Recommendation rejected."
- [ ] Database shows: status='rejected', rejection_reason stored

### Refresh Functionality
- [ ] "Refresh" button in header works
- [ ] Button click triggers data reload
- [ ] Toast shows "Refreshing recommendations..."
- [ ] View updates with latest data within 2 seconds
- [ ] Pending count updates correctly

### Count Badge
- [ ] Header shows "X pending" count
- [ ] Count updates automatically every 2 seconds
- [ ] Count decreases when approve/defer/reject
- [ ] Count increases when new recommendations inserted

## Execution Tracker Validation

### View Loading
**Navigate to ExecutionTracker view**:
- [ ] View loads successfully
- [ ] Title "Agent Actions" visible
- [ ] Status indicators in header
- [ ] Auto-refresh toggle button visible
- [ ] Empty state shows initially

### Live Data Display
**Insert test command**:
```sql
INSERT INTO agent_commands (
    command_id, equipment_id, tag_path, old_value, new_value,
    status, created_timestamp, started_timestamp
) VALUES (
    'cmd-test-001', 'REACTOR_01', '[default]Reactors/R1/SetPoint',
    '75', '70', 'executing', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP - INTERVAL 30 SECONDS
);
```

- [ ] Command appears in view within 1 second
- [ ] Equipment ID: "REACTOR_01"
- [ ] Tag path: "[default]Reactors/R1/SetPoint"
- [ ] Old value: "75" (dark background)
- [ ] Arrow: "→" (gray divider)
- [ ] New value: "70" (green background)
- [ ] Status badge: "EXECUTING" (green)
- [ ] Elapsed time displays and updates: "30s"

### Real-Time Updates
- [ ] Elapsed time increments every second
- [ ] Status badge shows correct state (EXECUTING/PENDING)
- [ ] Pulsing dots animation visible for executing commands
- [ ] Can toggle auto-refresh with button

### Total Counters
- [ ] Header shows "X executing • Y pending"
- [ ] Executing count updates as commands complete
- [ ] Pending count decreases as commands start

### Auto-Refresh Toggle
- [ ] Button labeled "⟳ Auto"
- [ ] Click toggles between ON (blue) and OFF (gray)
- [ ] When ON: data refreshes every 1 second
- [ ] When OFF: data frozen (no updates)
- [ ] Re-enabling resumes updates

## Styling & Appearance

### Color Scheme
- [ ] Dark background: #1e1e1e
- [ ] Card background: #2d2d2d
- [ ] Text: white (#ffffff)
- [ ] Headers: bold, 24px, white
- [ ] Secondary text: gray (#9ca3af)

### Severity Colors (in recommendations)
- [ ] Critical severity: red border (#ef4444)
- [ ] High severity: orange border (#f97316)
- [ ] Medium severity: yellow border (#eab308)
- [ ] Low severity: blue border (#3b82f6)

### Button Colors
- [ ] Approve: green (#10b981)
- [ ] Defer: yellow (#eab308)
- [ ] Reject: red (#ef4444)
- [ ] Hover states darker than normal
- [ ] Active states even darker

### Spacing & Layout
- [ ] 16px gaps between container sections
- [ ] 20px padding on main container
- [ ] 8px border-radius on cards
- [ ] 3px severity borders
- [ ] Proper alignment (left, center, right as intended)

### Icons & Animations
- [ ] Checkmark (✓) renders in empty state
- [ ] Status icons (▶ executing, ⋯ pending) visible
- [ ] Pulsing animation on executing commands smooth
- [ ] No flickering or jumping elements
- [ ] Animations performant (60fps)

## Error Handling Validation

### Network Errors
- [ ] Unplug network → views show error gracefully
- [ ] Reconnect → views resume updating
- [ ] No data loss or corruption

### Database Errors
**Simulate error** (invalid query):
```sql
-- Temporarily rename table
RENAME TABLE agent_recommendations TO agent_recommendations_backup;

-- Open view → should show error toast
-- Rename back
RENAME TABLE agent_recommendations_backup TO agent_recommendations;
```
- [ ] Error toast appears when query fails
- [ ] Message is user-friendly (not stack trace)
- [ ] Can recover by fixing issue and refreshing
- [ ] No view crash or freeze

### Script Errors
**Invalid button action** (test):
- [ ] Click button with missing parameter
- [ ] Should show error toast: "Error: Missing recommendation ID"
- [ ] View doesn't crash
- [ ] Can still interact with view

## Performance Validation

### Load Time
- [ ] View loads initial UI in <2 seconds
- [ ] First data query completes in <3 seconds
- [ ] No loading spinner stuck indefinitely

### Polling Performance
- [ ] 2-second polls on recommendations don't cause lag
- [ ] 1-second polls on execution tracker smooth
- [ ] Gateway CPU usage stays <30% during polling
- [ ] Memory usage stable (no leaks)

### Large Dataset Performance
**Insert 100 test recommendations**:
```sql
-- Load test script
INSERT INTO agent_recommendations (...) SELECT ... FROM source UNION ALL ...
-- Insert 100 rows total
```
- [ ] View renders 50 recommendations smoothly
- [ ] Scrolling is responsive
- [ ] Memory usage reasonable (<100MB)
- [ ] No jank or stuttering

### Query Performance
**Check query execution time**:
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT recommendation_id, equipment_id, issue_description, recommended_action,
       severity, confidence_score, created_timestamp, status, priority
FROM agent_recommendations
WHERE status = 'pending'
ORDER BY priority DESC, created_timestamp DESC
LIMIT 50;
```
- [ ] Query execution <500ms
- [ ] No sequential scans (should use index)
- [ ] Add index if needed:
  ```sql
  CREATE INDEX idx_recommendations_pending
  ON agent_recommendations(status, priority, created_timestamp);
  ```

## End-to-End Workflow Validation

### Complete Recommendation Cycle
1. **Setup**: Insert recommendation
   ```sql
   INSERT INTO agent_recommendations (...) VALUES (...)
   ```
   - [ ] Appears in view within 2 seconds

2. **Approve**: Click Approve button
   - [ ] Confirmation dialog appears
   - [ ] Click Confirm
   - [ ] Database updated (status='approved')
   - [ ] Recommendation disappears from view

3. **Agent Execution**: Insert command
   ```sql
   INSERT INTO agent_commands (...) VALUES (...)
   ```
   - [ ] Command appears in Execution Tracker
   - [ ] Status shows "EXECUTING"
   - [ ] Elapsed time updates

4. **Completion**: Mark command done
   ```sql
   UPDATE agent_commands SET status='executed', completed_timestamp=NOW()
   WHERE command_id='cmd-001'
   ```
   - [ ] Command disappears from Execution Tracker
   - [ ] Toast shows success

### Multiple Recommendations
- [ ] Insert 5 recommendations with different severities
  - [ ] All appear in view
  - [ ] Sorted by priority DESC
  - [ ] Color-coded by severity correctly
- [ ] Approve one → disappears, count decrements
- [ ] Defer one → disappears, count decrements
- [ ] Reject one → disappears, count decrements
- [ ] 2 remaining still show, counts correct

## Browser Compatibility

**Test on Multiple Browsers**:
- [ ] Chrome/Chromium (latest): Full functionality
- [ ] Firefox (latest): Full functionality
- [ ] Safari (latest): Full functionality, emojis render?
- [ ] Edge (latest): Full functionality

**Test Responsiveness**:
- [ ] On desktop (1920x1080): Optimal layout
- [ ] On tablet (iPad): Buttons accessible, scrolling works
- [ ] On mobile (1080x1920): Usable (may scroll more)

## Security Validation

### Authentication
- [ ] operatorId captured from session
- [ ] Approval shows operator who approved
- [ ] Tokens not visible in client code
- [ ] No credentials in view JSON

### Authorization
- [ ] Operators can only see their assigned recommendations
- [ ] No SQL injection via input fields
- [ ] Rejection reason sanitized before insert

### Audit Trail
```sql
SELECT recommendation_id, operator_id, approved_timestamp
FROM agent_recommendations
WHERE status = 'approved'
ORDER BY approved_timestamp DESC;
```
- [ ] Complete audit trail of approvals
- [ ] operator_id and timestamp recorded
- [ ] Rejection reasons logged

## Sign-Off Checklist

### Development Team
- [ ] Code review completed
- [ ] All JSON files validated
- [ ] Documentation complete
- [ ] No known bugs

### QA Team
- [ ] Tested on target Ignition version (8.3+)
- [ ] All 3 views functional
- [ ] Database connectivity verified
- [ ] Performance acceptable
- [ ] No breaking issues

### Product Owner
- [ ] Requirements met
- [ ] Meets design specifications
- [ ] User workflows validated
- [ ] Ready for production deployment

---

## Deployment Go/No-Go Decision

**Total Checks**: 150+
**Passing Checks**: ___/150
**Success Rate**: ___%

### Decision Criteria
- **GO**: ≥95% checks passing, no critical issues
- **GO WITH CAUTION**: 90-95% passing, minor issues logged
- **NO GO**: <90% passing, critical issues present

**Final Decision**: [ ] GO [ ] GO WITH CAUTION [ ] NO GO

**Approved by**: ___________________ **Date**: ___________

**Notes/Issues**:
```
[List any remaining issues and remediation plans]
```

---

## Post-Deployment Monitoring

### Daily Checks (Week 1)
- [ ] No error logs in Ignition
- [ ] Database query performance stable
- [ ] No stuck or hanging sessions
- [ ] Data accuracy verified

### Weekly Checks
- [ ] Review audit trail for issues
- [ ] Check database growth
- [ ] Monitor backup success
- [ ] Operator feedback collected

### Monthly Checks
- [ ] Reindex database as needed
- [ ] Archive old recommendations (>30 days)
- [ ] Update documentation
- [ ] Plan maintenance windows

---

**Checklist Version**: 1.0
**Last Updated**: 2026-02-19
**Status**: ACTIVE
