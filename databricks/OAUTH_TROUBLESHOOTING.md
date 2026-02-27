# OAuth 401 Troubleshooting Guide

## Current Status
- **Service Principal**: pravin_zerobus ✅
- **Service Principal ID**: 75698179574031 ✅
- **OAuth Client ID (Application ID)**: 6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb ✅
- **Warehouse Permissions**: GRANTED ✅
- **Catalog Permissions**: GRANTED ✅
- **Schema Permissions**: GRANTED ✅
- **Table Permissions**: ALL PRIVILEGES ✅
- **OAuth Error**: 401 invalid_authorization_details ❌

## Root Cause Analysis

The OAuth 401 error "User is not authorized to the requested authorizations" means:

1. **OAuth Client Secret Mismatch** (Most Likely)
   - The secret in Ignition doesn't match the current secret in Account Console
   - When you regenerate a secret, the OLD secret is immediately invalidated

2. **Missing OAuth Scopes**
   - The OAuth application needs 'all-apis' or 'sql' scope granted

## Step-by-Step Fix

### 1. Verify OAuth Application in Account Console

Go to: **Account Console → User Management → Service Principals → pravin_zerobus → OAuth**

Check:
- OAuth Client ID: `6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb`
- OAuth Secrets: Should show secret IDs (values are hidden)
- API Scopes: Should have `all-apis` or at minimum `sql` scope

### 2. Generate NEW OAuth Client Secret

In Account Console:
```
1. Click "Generate Secret" button
2. Copy the SECRET VALUE immediately (it's only shown once!)
3. Note down the Secret ID for reference
```

**IMPORTANT**: The secret VALUE is different from the secret ID!
- Secret ID: `6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb` (this is just an identifier)
- Secret VALUE: A long random string like `dapixxx...` (this is what you paste in Ignition)

### 3. Update OAuth Secret in Ignition Gateway

Go to: **http://localhost:8183/web/config/opc.ua/odbex.zerobus**

Configuration values:
```
Databricks Host: e2-demo-field-eng.cloud.databricks.com
Warehouse ID: 4b9b953939869799
Catalog: field_engineering
Schema: ignition_streaming
Table: sensor_events

OAuth Client ID: 6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb
OAuth Client Secret: <PASTE THE NEW SECRET VALUE HERE>
```

**Steps:**
1. Click "Edit" on Zerobus Module
2. Find "OAuth Client Secret" field
3. Clear the old value
4. Paste the NEW secret VALUE (not the ID!)
5. Click "Save Changes" at the bottom
6. You should see "Configuration Saved Successfully"

### 4. Restart Ignition Container

```bash
docker-compose -f docker/docker-compose.yml restart
```

### 5. Verify Connection

After restart, check logs:
```bash
docker logs genie-at-edge-ignition --tail 50 | grep -i "zerobus\|oauth"
```

Success indicators:
- ✅ "Zerobus stream initialized"
- ✅ "Connected to Databricks"
- ✅ No OAuth 401 errors

Failure indicators:
- ❌ "OAuth request failed with status 401"
- ❌ "Failed to get Zerobus token"

### 6. Check Data Ingestion

Query the table:
```sql
SELECT COUNT(*) as row_count,
       MAX(ingestion_timestamp) as latest
FROM field_engineering.ignition_streaming.sensor_events
```

Expected:
- Row count increasing over time
- Latest timestamp within last few seconds

## Common Mistakes

1. **Using Secret ID instead of Secret VALUE**
   - ❌ Wrong: Pasting `6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb` as secret
   - ✅ Right: Pasting the actual secret value like `dapixxx...`

2. **Not saving after editing**
   - Must click "Save Changes" button at bottom of config page

3. **Not restarting after config change**
   - Ignition caches OAuth credentials, must restart to pick up new secret

4. **Wrong OAuth application**
   - Make sure you're using pravin_zerobus OAuth secret, not a different SP

## Debug Commands

```bash
# Check Ignition logs
docker logs genie-at-edge-ignition -f | grep -i oauth

# Check if table exists
python3 databricks/get_sp_by_name.py

# Check data ingestion
python3 databricks/quick_verify.py

# Restart Ignition
docker-compose -f docker/docker-compose.yml restart
```

## Next Steps

The OAuth client secret is encrypted in Ignition's database, so I cannot verify what's currently stored there.

You need to:
1. Go to Account Console and generate a NEW secret
2. Copy the secret VALUE (shown only once!)
3. Paste it into Ignition Gateway → Zerobus Module → OAuth Client Secret
4. Save and restart

Would you like me to help check data ingestion after you've updated the secret?
