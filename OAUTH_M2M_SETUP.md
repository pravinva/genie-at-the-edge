# OAuth M2M Setup for Zerobus

**Date**: February 27, 2026
**Status**: Requires account-level OAuth configuration

---

## Option 1: Use Personal Access Token (Easier)

Zerobus should support **personal access token** authentication. This is simpler:

### Configuration
```yaml
Authentication Type: Token / Personal Access Token
Host: e2-demo-field-eng.cloud.databricks.com
HTTP Path: /sql/1.0/warehouses/4b9b953939869799
Token: <DATABRICKS_TOKEN>

Catalog: field_engineering
Schema: mining_demo
Table: zerobus_sensor_stream
```

**Token is already created and saved in**: `.databricks_zerobus_token`

---

## Option 2: Create OAuth M2M Credentials (If Required)

If Zerobus **requires** OAuth client credentials (not token), follow these steps:

### Step 1: Access Databricks Account Console
```
URL: https://accounts.cloud.databricks.com/
Login with your Databricks account admin credentials
```

### Step 2: Create Service Principal
1. Navigate to: **User management → Service principals**
2. Click **Add service principal**
3. Name: `zerobus-ignition-connector`
4. Click **Add**

### Step 3: Generate OAuth Secret
1. Select the service principal you just created
2. Go to **OAuth** tab
3. Click **Generate secret**
4. **Save these credentials** (shown only once):
   - **Client ID** (UUID format): `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - **Client Secret**: `dapixxxxxxxxxxxxxxxxxxx`

### Step 4: Grant Workspace Access
1. Still in the service principal page
2. Go to **Workspaces** tab
3. Add workspace: `e2-demo-field-eng`
4. Save

### Step 5: Grant Permissions via SQL
Run in Databricks SQL Editor:
```sql
-- Grant catalog permissions
GRANT USE CATALOG ON CATALOG field_engineering
TO SERVICE PRINCIPAL `zerobus-ignition-connector`;

-- Grant schema permissions
GRANT USE SCHEMA ON SCHEMA field_engineering.mining_demo
TO SERVICE PRINCIPAL `zerobus-ignition-connector`;

-- Grant table permissions
GRANT SELECT, INSERT, MODIFY ON TABLE field_engineering.mining_demo.zerobus_sensor_stream
TO SERVICE PRINCIPAL `zerobus-ignition-connector`;

-- Grant warehouse usage
GRANT USAGE ON WAREHOUSE `4b9b953939869799`
TO SERVICE PRINCIPAL `zerobus-ignition-connector`;
```

### Step 6: Configure Zerobus
In Ignition Gateway (http://localhost:8183):

**Config → Zerobus → Connections**

```yaml
Authentication Type: OAuth M2M
Host: e2-demo-field-eng.cloud.databricks.com
HTTP Path: /sql/1.0/warehouses/4b9b953939869799

OAuth Client ID: <client_id_from_step_3>
OAuth Client Secret: <client_secret_from_step_3>

Catalog: field_engineering
Schema: mining_demo
Table: zerobus_sensor_stream
```

---

## Option 3: Quick Test with Databricks CLI Token

If you have account admin access, get the OAuth credentials:

```bash
# Login to account
databricks auth login --host https://accounts.cloud.databricks.com/

# Create service principal (if not exists)
databricks service-principals create \
  --display-name "zerobus-ignition-connector"

# Get service principal ID
databricks service-principals list | grep zerobus

# Generate OAuth secret (requires account admin)
# This must be done through Account Console UI
```

---

## Recommended Approach

**For fastest setup, use Option 1 (Token)**:
- Already created ✅
- No account-level access needed ✅
- Permissions already granted ✅

If Zerobus UI doesn't have "Token" option, then OAuth M2M is required (Option 2).

---

## Verification After Configuration

1. In Ignition Gateway, click **"Test Connection"**
   - Should show: ✅ "Connected"

2. Enable the connection

3. Check logs:
   ```bash
   docker logs genie-at-edge-ignition --tail 50 | grep -i "success\|connected"
   ```

4. Check data in Databricks:
   ```sql
   SELECT COUNT(*)
   FROM field_engineering.mining_demo.zerobus_sensor_stream;
   ```

---

## Current Status

- ✅ Table schema fixed
- ✅ Permissions granted (to `account users`)
- ✅ Personal access token created
- ⏱️ **Awaiting**: Token/OAuth configuration in Zerobus

**Next**: Try Option 1 (Token) first. If Zerobus requires OAuth, use Option 2.
