# Implementation Comparison

## External Proxy vs Perspective-Native

This project offers **two implementations** for integrating Databricks Genie with Ignition Perspective. Choose the one that fits your requirements.

---

## Option 1: External Proxy (Main Branch)

**Current default implementation**

### Architecture
```
Browser → Ignition Webserver (HTML) → External Python Proxy → Databricks Genie
```

### Components
- **Chat UI:** Single HTML file with React (served from Ignition webserver)
- **Proxy Server:** Python 3.7+ HTTP server running on host (port 8185)
- **Perspective Integration:** Inline Frame component

### Setup Complexity
**Moderate** - Requires deploying two components

### Pros
- ✅ **Modern Python 3** - Use latest Python features
- ✅ **Independent updates** - Update proxy without touching Ignition
- ✅ **Better debugging** - Standard Python debugging tools
- ✅ **Simpler HTML** - No Perspective/Jython constraints
- ✅ **Works standalone** - Can test proxy without Ignition
- ✅ **Multiple gateways** - One proxy can serve multiple gateways

### Cons
- ❌ **Extra process** - Separate process to manage
- ❌ **Port management** - Need to open/manage port 8185
- ❌ **CORS handling** - Must add CORS headers
- ❌ **Service management** - Systemd/NSSM configuration
- ❌ **Two points of failure** - Proxy and Ignition

### When to Choose
- You prefer Python 3.x features
- You want to update proxy without touching Ignition project
- You're comfortable managing system services
- You need to serve multiple Ignition gateways
- You want standalone testing capabilities

---

## Option 2: Perspective-Native (Feature Branch)

**Alternative implementation - no external dependencies**

### Architecture
```
Browser → Perspective View → Gateway Script (Jython) → Databricks Genie
```

### Components
- **Gateway Script:** Python module in Ignition project (Jython 2.7)
- **Perspective View:** Native Perspective components with scripting
- **No External Process:** Everything inside Ignition

### Setup Complexity
**Simple** - All configuration in Designer

### Pros
- ✅ **No external process** - Everything in Ignition
- ✅ **No CORS issues** - Server-side communication only
- ✅ **Single port** - Only Ignition gateway port (8088)
- ✅ **No service management** - Starts with Ignition automatically
- ✅ **Designer-managed** - All updates in Designer
- ✅ **Unified backup** - Gateway script included in project backup
- ✅ **Single point of failure** - Only Ignition gateway

### Cons
- ❌ **Jython 2.7 limitations** - No Python 3 features (f-strings, async/await, etc.)
- ❌ **Coupled updates** - Must update Ignition project to change script
- ❌ **Harder debugging** - Limited to gateway logs and Script Console
- ❌ **Perspective-specific** - Tightly coupled to Perspective

### When to Choose
- You want minimal infrastructure
- You prefer single-process architecture
- You don't want to manage external services
- You're comfortable with Jython 2.7 limitations
- You want everything in Ignition Designer

---

## Feature Comparison

| Feature | External Proxy | Perspective-Native |
|---------|---------------|-------------------|
| **Deployment** | ⚠️ Two components | ✅ One component |
| **Processes** | ⚠️ Ignition + Proxy | ✅ Ignition only |
| **Ports** | ⚠️ 8088 + 8185 | ✅ 8088 only |
| **Python Version** | ✅ 3.7+ | ⚠️ 2.7 (Jython) |
| **CORS Handling** | ⚠️ Proxy adds headers | ✅ Not needed |
| **Service Management** | ⚠️ Systemd/NSSM | ✅ Auto with Ignition |
| **Debugging** | ✅ Standard Python tools | ⚠️ Gateway logs only |
| **Updates** | ✅ Independent | ⚠️ Requires project update |
| **Backup** | ⚠️ Two components | ✅ Project only |
| **Monitoring** | ⚠️ Two processes | ✅ One process |
| **Standalone Testing** | ✅ Yes | ❌ No |
| **Multi-Gateway** | ✅ Yes | ⚠️ One per gateway |
| **Response Caching** | ✅ 5 min TTL | ✅ 5 min TTL |
| **Token Caching** | ✅ 50 min TTL | ✅ 50 min TTL |
| **Performance** | ✅ 280x speedup | ✅ 280x speedup |
| **Ignition Versions** | ✅ 8.1+ | ✅ 8.1+ |

---

## Performance

**Both implementations have identical performance:**
- Token caching: 50 minutes
- Response caching: 5 minutes
- Fast polling: 500ms intervals
- Cold query: ~8-10 seconds
- Cached query: ~0.03 seconds (280x faster)

---

## Code Examples

### External Proxy Approach

**Frontend (HTML/React):**
```javascript
const response = await fetch('http://localhost:8185/api/genie/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question: "What is the status?"})
});
const data = await response.json();
```

**Backend (Python 3):**
```python
# ignition/scripts/genie_proxy.py
def do_POST(self):
    # Get token from databricks CLI
    token = get_databricks_token()

    # Call Genie API
    response = urllib.request.urlopen(genie_request)

    # Add CORS headers
    self.send_header('Access-Control-Allow-Origin', '*')
    self.wfile.write(json.dumps(result).encode())
```

### Perspective-Native Approach

**Frontend (Perspective View Script):**
```python
# View custom method
def sendMessage(self):
    question = self.custom.inputValue

    def queryAsync():
        result = shared.genie_api.queryGenie(question)
        return result

    def callback(result):
        self.custom.messages = self.custom.messages + [result]

    system.util.invokeAsynchronous(queryAsync, [], callback)
```

**Backend (Gateway Script):**
```python
# Project Scripts → genie_api module
def queryGenie(question, conversationId=None):
    # Get token from databricks CLI
    token = _get_databricks_token()

    # Call Genie API
    response = system.net.httpPost(url=..., headers=...)

    # Poll for completion
    # Return result
    return {'response': text, 'conversationId': id}
```

---

## Migration Path

### From External Proxy → Perspective-Native

1. Add gateway script module to project
2. Create new Perspective view with native components
3. Test new implementation
4. Switch Page Configuration to new view
5. Stop external proxy process
6. Remove systemd/NSSM service
7. Close firewall port 8185

**Can run both simultaneously during migration.**

### From Perspective-Native → External Proxy

1. Deploy external proxy script
2. Start proxy as system service
3. Deploy HTML chat file to webserver
4. Create Inline Frame view
5. Switch Page Configuration to Inline Frame view
6. Remove gateway script module (optional)

---

## Deployment Checklist

### External Proxy

- [ ] Install Python 3.7+ on gateway host
- [ ] Install databricks-cli: `pip install databricks-cli`
- [ ] Configure databricks CLI authentication
- [ ] Deploy `genie_proxy.py` to host
- [ ] Create systemd/NSSM service for proxy
- [ ] Start proxy service
- [ ] Configure firewall for port 8185
- [ ] Deploy `mining_genie_chat.html` to Ignition webserver
- [ ] Create Perspective view with Inline Frame
- [ ] Add page to Page Configuration
- [ ] Test end-to-end

### Perspective-Native

- [ ] Install Python 3.7+ on gateway host (for databricks CLI only)
- [ ] Install databricks-cli: `pip install databricks-cli`
- [ ] Configure databricks CLI authentication
- [ ] Add `genie_api` gateway script module to project
- [ ] Configure workspace URL and Space ID in script
- [ ] Create Perspective view with custom components
- [ ] Add view scripts (sendMessage, clearChat)
- [ ] Add page to Page Configuration
- [ ] Test end-to-end

---

## Recommendation by Use Case

### Choose External Proxy If:
- 🏢 **Enterprise with centralized IT** - Separate proxy server serving multiple gateways
- 🔧 **Frequent updates** - You'll iterate on proxy logic frequently
- 🐍 **Python 3 features needed** - Want modern Python syntax
- 🧪 **Standalone testing** - Need to test proxy without Ignition running
- 🔄 **Multi-gateway** - One proxy serving N gateways

### Choose Perspective-Native If:
- 🏭 **Edge deployment** - Single gateway at remote site
- 🚀 **Simplicity** - Minimal infrastructure and fewer moving parts
- 🔒 **Locked-down environment** - Can't run external processes or open ports
- 📦 **Unified management** - Everything in Designer
- 🎯 **Single gateway** - Dedicated Genie integration per gateway

---

## Quick Start

### External Proxy
```bash
git clone https://github.com/pravinva/genie-at-the-edge.git
cd genie-at-the-edge
# Follow README.md on main branch
```

### Perspective-Native
```bash
git clone https://github.com/pravinva/genie-at-the-edge.git
cd genie-at-the-edge
git checkout feature/perspective-native-genie
# Follow docs/PERSPECTIVE_NATIVE_IMPLEMENTATION.md
```

---

## Support

Both implementations are production-ready and fully supported.

**Documentation:**
- External Proxy: `README.md`, `docs/DEPLOYMENT.md`
- Perspective-Native: `docs/PERSPECTIVE_NATIVE_IMPLEMENTATION.md`

**Issues:** https://github.com/pravinva/genie-at-the-edge/issues

---

**Updated:** February 15, 2026
