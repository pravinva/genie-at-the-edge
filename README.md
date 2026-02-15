# Genie at the Edge - Perspective Native

**Embed Databricks Genie AI Chat in Ignition Perspective (No External Proxy)**

A production-ready solution that runs **entirely inside Ignition Gateway** - no external Python proxy required. Integrates Databricks Genie conversational AI directly into Perspective HMIs using native Gateway scripts. Works with any Genie Space and any data.

[![Repository](https://img.shields.io/badge/GitHub-genie--at--the--edge-blue?logo=github)](https://github.com/pravinva/genie-at-the-edge)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ignition](https://img.shields.io/badge/Ignition-8.1%2B-orange)]()
[![Branch](https://img.shields.io/badge/Branch-Perspective--Native-purple)]()

---

> **🔀 Alternative Implementation Available**
>
> This branch uses **Perspective-native** approach (no external proxy, everything inside Ignition).
>
> For the **external proxy** implementation (Python 3, independent updates), see the [`main`](https://github.com/pravinva/genie-at-the-edge/tree/main) branch.
>
> **Comparison:** See [docs/IMPLEMENTATION_COMPARISON.md](docs/IMPLEMENTATION_COMPARISON.md) to understand the differences.

---

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Implementation Guide](#implementation-guide)
- [Configuration](#configuration)
- [Performance](#performance)
- [Documentation](#documentation)
- [Migration](#migration)

---

## Overview

This **Perspective-native implementation** eliminates the external Python proxy entirely. Everything runs inside Ignition Gateway using Jython scripts and Perspective's native capabilities.

### What You Get

- **Gateway Script Module** - Jython code running inside Ignition
- **Perspective View Components** - Native Perspective UI (no HTML/React)
- **No External Processes** - Everything managed in Designer
- **No CORS Issues** - Server-side communication only
- **Performance Optimizations** - Same 280x speedup as external proxy
- **Single Process** - Only Ignition Gateway

### Key Advantages

- ✅ **No External Proxy** - Runs entirely in Ignition Gateway
- ✅ **No CORS Issues** - Server-side communication only
- ✅ **Single Process** - Only Ignition, no external services
- ✅ **Single Port** - Only gateway port (8088), no additional ports
- ✅ **Designer-Managed** - All configuration in Designer
- ✅ **Unified Backup** - Gateway script included in project backup
- ✅ **Auto-Start** - Starts automatically with Ignition
- ✅ **Data Agnostic** - Works with any Genie Space
- ✅ **Ignition 8.1+ Compatible** - Works on all modern versions

### Trade-offs vs External Proxy

- ⚠️ **Jython 2.7** - No Python 3 features (f-strings, async/await)
- ⚠️ **Coupled Updates** - Must update Ignition project to change script
- ⚠️ **Harder Debugging** - Limited to gateway logs and Script Console
- ⚠️ **Perspective-Specific** - Tightly coupled to Perspective

**Use this if:** You want minimal infrastructure, simplified deployment, or can't run external processes.

**Use external proxy if:** You need Python 3 features, independent updates, or multi-gateway architecture.

---

## How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                       IGNITION GATEWAY                           │
│                                                                  │
│  ┌─────────────────────┐        ┌──────────────────────────┐  │
│  │  Perspective View   │        │  Gateway Script          │  │
│  │                     │        │  (genie_api module)      │  │
│  │  • Chat messages    │───────▶│                          │  │
│  │  • User input       │ script │  • Token caching         │  │
│  │  • Chart display    │  call  │  • Response caching      │  │
│  │  • Native bindings  │        │  • Genie API calls       │  │
│  │                     │◀───────│  • Async polling         │  │
│  │                     │callback│                          │  │
│  └─────────────────────┘        └──────────────────────────┘  │
│                                                                  │
│  Custom Methods:                 Module Functions:              │
│  • sendMessage()                 • queryGenie()                 │
│  • clearChat()                   • _get_databricks_token()     │
│                                  • _fetch_chart_data()          │
└──────────────────────────────────────────────────────────────────┘
                                    ↓ HTTPS
                    ┌────────────────────────────────┐
                    │   Databricks Genie API        │
                    │                                │
                    │   • Conversation API          │
                    │   • Your Genie Space          │
                    │   • Your Lakehouse Data       │
                    └────────────────────────────────┘
```

### Architecture Benefits

**No Browser-to-External-Proxy Hops:**
- External Proxy: Browser → Ignition Webserver → Proxy (port 8185) → Databricks
- **This Approach:** Browser → Perspective View → Gateway Script → Databricks

**No CORS:**
- External Proxy: Must add CORS headers for browser security
- **This Approach:** Server-side only, no CORS needed

**No Service Management:**
- External Proxy: Systemd/NSSM service, monitoring, logs
- **This Approach:** Starts with Ignition automatically

---

## Quick Start

### Prerequisites

- Ignition Gateway 8.1+ with Perspective module
- Databricks workspace with Genie enabled
- Python 3.7+ on gateway host (for databricks CLI only)
- Databricks CLI configured with OAuth

### 5-Minute Setup

```bash
# 1. Clone repository and switch to this branch
git clone https://github.com/pravinva/genie-at-the-edge.git
cd genie-at-the-edge
git checkout feature/perspective-native-genie

# 2. Install Databricks CLI on gateway host
pip install databricks-cli

# 3. Configure Databricks authentication
databricks configure --host https://your-workspace.cloud.databricks.com

# 4. Test CLI authentication
databricks auth token --host https://your-workspace.cloud.databricks.com
```

**Then in Ignition Designer:**

1. Open your Ignition project
2. Add gateway script module (see [Implementation Guide](#implementation-guide))
3. Create Perspective view with custom methods
4. Configure workspace URL and Space ID
5. Test from Designer

**No external processes to start!**

---

## Implementation Guide

See **[docs/PERSPECTIVE_NATIVE_IMPLEMENTATION.md](docs/PERSPECTIVE_NATIVE_IMPLEMENTATION.md)** for complete step-by-step instructions:

1. **Add Gateway Script Module**
   - Copy `ignition/scripts/genie_gateway_script.py`
   - Add to Project → Scripts → genie_api module
   - Update workspace URL and Space ID

2. **Create Perspective View**
   - Add custom properties (messages, inputValue, conversationId, etc.)
   - Add UI components (message container, input, buttons)
   - Configure bindings

3. **Add View Scripts**
   - `sendMessage()` - Calls gateway script asynchronously
   - `clearChat()` - Resets conversation
   - Message rendering with markdown support

4. **Add to Page Configuration**
   - Create route (e.g., `/genie-native`)
   - Assign view
   - Test in session

### Code Example

**Gateway Script Call (in Perspective view):**
```python
def sendMessage(self):
    """Send message to Genie via gateway script"""
    question = self.custom.inputValue

    # Call gateway script asynchronously
    def queryAsync():
        return shared.genie_api.queryGenie(question, self.custom.conversationId)

    def callback(result):
        # Add AI response to messages
        self.custom.messages = self.custom.messages + [{
            'type': 'ai',
            'text': result['response'],
            'chartData': result.get('chartData')
        }]
        self.custom.conversationId = result['conversationId']

    system.util.invokeAsynchronous(queryAsync, [], callback)
```

**Gateway Script (Project Scripts → genie_api):**
```python
def queryGenie(question, conversationId=None):
    """Query Databricks Genie API"""
    # Get token (cached)
    token = _get_databricks_token()

    # Call Genie API
    response = system.net.httpPost(url=..., headers=...)

    # Poll for completion
    # ... polling logic ...

    return {
        'response': text,
        'conversationId': id,
        'chartData': data
    }
```

---

## Configuration

### Update Workspace and Space ID

Edit gateway script module (Project → Scripts → genie_api), lines 15-16:

```python
# Databricks Configuration
WORKSPACE_URL = "https://your-workspace.cloud.databricks.com"  # Your workspace
SPACE_ID = "your_genie_space_id"  # Your Genie Space ID
```

**How to find your Genie Space ID:**
1. Open your Genie Space in Databricks
2. Look at URL: `https://workspace.cloud.databricks.com/genie/rooms/{SPACE_ID}`
3. Copy the Space ID (hexadecimal string)

### Customize Suggested Questions

In Perspective view custom properties, set default `suggestedQuestions`:

```json
[
    "What is the current status of equipment?",
    "Show me recent alerts",
    "What were the KPIs last hour?",
    "Show production trends"
]
```

---

## Performance

### Optimization Results

Identical performance to external proxy approach:

| Metric | Before | After | Improvement |
|--------|-------:|------:|------------:|
| **First query (cold cache)** | 8-10s | 8-10s | - |
| **Repeated query (cached)** | 8-10s | 0.03s | **280x faster** |
| **Average response time** | 8-10s | 4.7s | **47% faster** |
| **Demo wait time (12 queries)** | 102s | 41s | **60% reduction** |

### Optimizations Included

- **Response Caching** - 5-minute TTL, module-level cache
- **OAuth Token Caching** - 50-minute TTL, saves 200ms per query
- **Fast Polling** - 500ms intervals with immediate first poll
- **Thread-Safe** - Concurrent request handling with locks
- **Auto Cache Eviction** - 100-entry limit with LRU

### Monitoring Performance

**Gateway Logs:**
```
Config → Logging → Add logger: "genie_api"
Level: DEBUG or INFO
```

**Script Console Testing:**
```python
import shared.genie_api as genie

# Test query
result = genie.queryGenie("What is the current status?")
print "Response:", result['response'][:100]
print "Conversation ID:", result['conversationId']
```

---

## Documentation

### Complete Guides
- **[docs/PERSPECTIVE_NATIVE_IMPLEMENTATION.md](docs/PERSPECTIVE_NATIVE_IMPLEMENTATION.md)** - Full implementation steps
- **[docs/IMPLEMENTATION_COMPARISON.md](docs/IMPLEMENTATION_COMPARISON.md)** - Compare with external proxy approach
- **[docs/PERFORMANCE_IMPROVEMENTS.md](docs/PERFORMANCE_IMPROVEMENTS.md)** - Performance details

### Key Scripts
- **`ignition/scripts/genie_gateway_script.py`** - Gateway script module (copy to Designer)

### Demo Materials
- `demo/` - Demo scripts, checklists (same as main branch)

### Troubleshooting

**Issue: "Module 'shared.genie_api' not found"**
- Gateway script not deployed or named incorrectly
- Check Project Browser → Scripts → genie_api exists
- Try gateway restart

**Issue: "Failed to get Databricks token"**
- Databricks CLI not configured on gateway host
- SSH/RDP to gateway server
- Run: `databricks configure --host https://your-workspace.cloud.databricks.com`

**Issue: Async callback not firing**
- Check gateway logs for exceptions
- Verify Python syntax (Jython 2.7 compatible)
- Test in Script Console first

**Issue: Slow responses**
- Same as external proxy - warehouse cold start
- Use Serverless SQL warehouse for instant startup

---

## Migration

### From External Proxy → This Branch

1. ✅ Add gateway script module to project
2. ✅ Create Perspective view with native components
3. ✅ Test new implementation
4. ✅ Switch Page Configuration to new view
5. ✅ Stop external proxy process
6. ✅ Remove systemd/NSSM service
7. ✅ Close firewall port 8185

**Both can run simultaneously during migration.**

### From This Branch → External Proxy

Switch to `main` branch and follow its README.

---

## Technology Stack

### Ignition Components
- **Perspective Module** - HMI framework (8.1+)
- **Gateway Scripts** - Jython 2.7 modules
- **Project Library** - Shared script modules

### Databricks Components
- **Genie Conversation API** - Natural language engine
- **Unity Catalog** - Data governance
- **Databricks CLI** - OAuth token management

### Programming
- **Jython 2.7** - Python for Ignition Gateway
- **Perspective Scripting** - View custom methods
- **system.util.invokeAsynchronous** - Non-blocking calls
- **system.net.httpGet/Post** - HTTP client

---

## Deployment Checklist

- [ ] Install Python 3.7+ on gateway host (for databricks CLI)
- [ ] Install databricks-cli: `pip install databricks-cli`
- [ ] Configure databricks CLI with OAuth
- [ ] Add `genie_api` gateway script module to project
- [ ] Update workspace URL and Space ID in script
- [ ] Create Perspective view with custom components and methods
- [ ] Add view scripts (sendMessage, clearChat)
- [ ] Add custom properties (messages, conversationId, etc.)
- [ ] Add page to Page Configuration
- [ ] Test in Designer Script Console
- [ ] Test in Perspective session
- [ ] Deploy project to gateway

**No external proxy deployment needed!**

---

## Compatibility

| Component | Version | Notes |
|-----------|---------|-------|
| Ignition Gateway | 8.1+ | Perspective module required |
| Python (CLI only) | 3.7+ | Only for databricks CLI |
| Jython (Gateway) | 2.7 | Built into Ignition |
| Databricks Runtime | 13.3+ | Genie support |
| Databricks CLI | 0.18+ | OAuth authentication |

---

## Support

- **GitHub Issues:** [https://github.com/pravinva/genie-at-the-edge/issues](https://github.com/pravinva/genie-at-the-edge/issues)
- **Implementation Guide:** [docs/PERSPECTIVE_NATIVE_IMPLEMENTATION.md](docs/PERSPECTIVE_NATIVE_IMPLEMENTATION.md)
- **Comparison:** [docs/IMPLEMENTATION_COMPARISON.md](docs/IMPLEMENTATION_COMPARISON.md)

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

**Made with Claude Code** - [https://claude.com/claude-code](https://claude.com/claude-code)
