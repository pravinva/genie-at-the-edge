# Embed Chat UI in Ignition Perspective

## Step-by-Step Instructions

### 1. Copy Chat HTML to Ignition Webserver

**Option A: Using Ignition's Webserver Directory**
```bash
# Copy HTML file to Ignition webserver
cp ui/mining_genie_chat.html docker/data/webserver/mining_genie_chat.html
```

The file will be accessible at:
`http://localhost:8183/system/webserver/mining_genie_chat.html`

**Option B: Host Externally**
- Upload to Databricks Workspace Files
- Or host on any web server (S3, Azure Blob, etc.)

### 2. Create Perspective View in Designer

1. Open Ignition Designer
2. Navigate to: **Perspective → Views**
3. Right-click **Views** → **New View**
4. Name: `ChatAssistant`
5. Click **Create**

### 3. Add Web Browser Component

1. In the new View, open **Component Palette**
2. Find: **Embedded → Web Browser** component
3. Drag onto the canvas
4. Resize to fill the entire view

### 4. Configure Web Browser Component

**Properties:**
- **url**: `http://localhost:8183/system/webserver/mining_genie_chat.html`
- **sandbox**: Unchecked (allow scripts)
- **allowFullscreen**: true
- **style.width**: `100%`
- **style.height**: `100%`

### 5. Add to Session

1. Go to **Perspective → Pages**
2. Edit your main page configuration
3. Add new page:
   - **Path**: `/chat`
   - **View**: `ChatAssistant`
   - **Title**: `AI Assistant`
   - **Icon**: `material/chat`

### 6. Test the UI

1. Launch Perspective Session from Designer: **Tools → Launch Perspective**
2. Navigate to `/chat` page
3. Test sample questions:
   - "What is the current status of all haul trucks?"
   - "Show me crusher CR_002 performance"
   - "Which equipment has anomalies?"

### 7. Optional: Add Navigation Button

Add a navigation button to your main view:

**Component**: Button
**Properties**:
- **text**: "AI Assistant"
- **icon**: "material/chat"
- **onClick** → **Navigate To**:
  - **path**: `/chat`

## Troubleshooting

**Chat UI doesn't load:**
- Check file exists at webserver path
- Verify URL in Web Browser component is correct
- Check browser console for errors (F12)

**Sandbox errors:**
- Ensure `sandbox` property is unchecked
- May need to adjust Ignition Gateway security settings

**CSS/styling issues:**
- Verify fonts.googleapis.com is accessible
- Check CDN access for React libraries
- May need to embed fonts/libraries locally if offline

## Integration with Real Genie API

Once Genie Space is deployed in Databricks:

1. Get Genie Space ID from Databricks UI
2. Generate API token with appropriate permissions
3. Edit `mining_genie_chat.html`:
   - Replace `generateMockResponse()` with real API calls
   - Add authentication headers
   - Handle streaming responses

Example API integration:
```javascript
const GENIE_SPACE_ID = 'your-space-id';
const DATABRICKS_TOKEN = 'dapi...';
const WORKSPACE_URL = 'https://e2-demo-field-eng.cloud.databricks.com';

async function queryGenie(question) {
    const response = await fetch(
        `${WORKSPACE_URL}/api/2.0/genie/spaces/${GENIE_SPACE_ID}/query`,
        {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${DATABRICKS_TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: question })
        }
    );
    return await response.json();
}
```

## Security Considerations

- Store Databricks tokens securely (use server-side proxy)
- Implement proper authentication for production
- Consider using OAuth flows for user-specific tokens
- Restrict CORS if hosting externally

## Current Status

✅ Chat UI created with Perspective Dark Theme
✅ React-based with smooth animations
✅ Sample questions and typing indicators
✅ Ready for embedding in Ignition Perspective
⏳ Mock responses (replace with Genie API)
⏳ DLT pipeline needs debugging (tables ready)

## Next Steps

1. Copy HTML to Ignition webserver
2. Create Perspective view with Web Browser component
3. Test in Perspective session
4. Deploy Genie Space in Databricks
5. Integrate real Genie API calls
6. Test end-to-end flow
