# Ignition Zerobus Configuration Checklist

## Current Status
- ✅ OAuth secret validated via Python CLI test
- ✅ Config database timestamp updated (11:20:40)
- ❌ Ignition still getting OAuth 401 error after restart
- ✅ All Databricks permissions granted

## Root Cause
The OAuth secret in Ignition Gateway **is NOT matching** the secret that works in Python CLI test.

## Configuration Fields to Verify

### Navigate to: http://localhost:8183/web/config/opc.ua/odbex.zerobus

Verify EXACT values in each field:

```
1. Module Name: ZerobusModule (or similar)
2. Enabled: ✓ (checkbox should be checked)

CONNECTION SETTINGS:
3. Databricks Host: e2-demo-field-eng.cloud.databricks.com
   ⚠️ Do NOT include https:// prefix
   ⚠️ Do NOT include trailing slash

4. Warehouse ID: 4b9b953939869799

5. Catalog: field_engineering

6. Schema: ignition_streaming

7. Table: sensor_events

AUTHENTICATION:
8. OAuth Client ID: 6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb
   ⚠️ This is the Application ID from service principal

9. OAuth Client Secret: <OAUTH_CLIENT_SECRET>
   ⚠️ This is the SECRET VALUE (36 characters)
   ⚠️ NOT the secret ID
   ⚠️ Make sure there are no extra spaces before/after
```

## Step-by-Step Verification

### Step 1: Check if field is password-masked
- The "OAuth Client Secret" field should show `****` if a value is saved
- Click in the field to see if you can select all text
- Press Ctrl+A (or Cmd+A) to select all
- Press Delete to clear the field completely

### Step 2: Paste the new secret
- Make sure the field is completely empty
- Paste: `<OAUTH_CLIENT_SECRET>`
- Verify it's 36 characters (no spaces, no line breaks)
- **DO NOT press Enter** - just paste and leave cursor there

### Step 3: Save configuration
- Scroll to the bottom of the page
- Click "Save Changes" button (should turn green or show "Saved")
- Wait for confirmation message

### Step 4: Verify the save worked
- DO NOT refresh the page yet
- Check if the page shows "Configuration saved successfully" or similar
- Look for any error messages

### Step 5: Restart Gateway (not just container)
Option A - Full Gateway Restart via Web UI:
- Navigate to: http://localhost:8183/web/config/system.commissionstatus
- Click "Restart Gateway" button
- Wait 30-60 seconds for full restart

Option B - Container Restart:
```bash
docker-compose -f docker/docker-compose.yml restart
```

### Step 6: Check logs immediately after restart
```bash
docker logs genie-at-edge-ignition -f | grep -i "zerobus\|oauth"
```

## Alternative: Re-configure from Scratch

If the above doesn't work, try disabling and re-enabling the module:

1. Navigate to: http://localhost:8183/web/config/system.modules
2. Find "Zerobus Module" or similar
3. Click "Disable" button
4. Wait 10 seconds
5. Click "Enable" button
6. Navigate back to: http://localhost:8183/web/config/opc.ua/odbex.zerobus
7. Enter ALL configuration fields from scratch
8. Save and restart

## Debugging Questions

1. **Is the config page showing multiple Zerobus connections?**
   - Maybe there are multiple configurations and we're editing the wrong one
   - Check if there's a dropdown or list to select the active connection

2. **Is there a "Test Connection" button?**
   - Some modules have a test button to verify credentials before saving
   - This would immediately show if OAuth is working

3. **Are there any validation errors on save?**
   - Red text showing "Invalid format" or similar
   - This would indicate the field format is wrong

4. **Can you export the configuration?**
   - Some gateways allow exporting config as JSON/XML
   - This would let us see the exact values being stored

## Expected Success Indicators

After correct configuration and restart, logs should show:
```
✅ "Zerobus client initialized successfully"
✅ "Connected to Databricks workspace"
✅ "Stream created successfully"
✅ "Subscribed to X tags"
```

NOT:
```
❌ "OAuth request failed with status 401"
❌ "Failed to get Zerobus token"
❌ "NonRetriableException"
```

## Next Steps

If OAuth 401 persists even after following ALL steps above:
1. Take a screenshot of the Zerobus configuration page
2. Check Account Console → Service Principals → pravin_zerobus → OAuth
   - Verify the secret ID matches what you generated
   - Check the "Last Used" timestamp (should update after each attempt)
3. Try generating a BRAND NEW secret and use that instead
