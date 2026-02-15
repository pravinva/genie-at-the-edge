# Genie at the Edge

**Embed Databricks Genie AI Chat in Ignition Perspective**

A production-ready solution for integrating Databricks Genie conversational AI directly into Ignition Perspective HMIs. Works with any Genie Space and any data - no domain-specific customization required.

[![Repository](https://img.shields.io/badge/GitHub-genie--at--the--edge-blue?logo=github)](https://github.com/pravinva/genie-at-the-edge)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ignition](https://img.shields.io/badge/Ignition-8.1%2B-orange)]()
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)]()

---

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Perspective Integration](#perspective-integration)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Performance](#performance)
- [Example: Mining Demo](#example-mining-demo)
- [Documentation](#documentation)

---

## Overview

This project provides a **data-agnostic** solution to embed Databricks Genie conversational AI into Ignition Perspective views. Operators can ask natural language questions about their data directly from the HMI without leaving Ignition.

### What You Get

- **Conversational AI Chat UI** - React-based interface with markdown rendering and chart visualization
- **CORS Proxy Server** - Python server handling authentication and cross-origin requests
- **Perspective Integration Guide** - Step-by-step instructions for embedding in Perspective (works on Ignition 8.1+)
- **Performance Optimizations** - Response caching, token management, fast polling (280x speedup)
- **Production-Ready** - Deployment guides for Docker, Windows, and Linux edge gateways

### Key Features

- **Data Agnostic** - Works with any Databricks Genie Space (manufacturing, energy, retail, etc.)
- **No Code Changes Required** - Just configure your workspace URL and Genie Space ID
- **Ignition 8.1+ Compatible** - Works on all modern Ignition versions with Perspective
- **Embedded in Perspective** - Native Inline Frame component integration
- **Natural Language Queries** - Leverage Genie's AI to query your lakehouse data
- **Automatic Chart Generation** - Time series and categorical data visualized automatically
- **Response Caching** - 280x faster for repeated queries (8s → 0.03s)
- **Production Deployment** - Systemd, NSSM, Docker support

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IGNITION PERSPECTIVE VIEW                        │
│                                                                     │
│  ┌───────────────┐           ┌─────────────────────────────────┐  │
│  │   Your HMI    │           │   Inline Frame Component       │  │
│  │   Dashboard   │           │                                 │  │
│  │               │           │   ┌─────────────────────────┐   │  │
│  │   Equipment   │           │   │  Genie Chat Interface   │   │  │
│  │   Alarms      │           │   │                         │   │  │
│  │   Trends      │           │   │  User: "Show trends"    │   │  │
│  │               │           │   │  AI: [Response + Chart] │   │  │
│  └───────────────┘           │   └─────────────────────────┘   │  │
│                              │   URL: /mining_genie_chat.html  │  │
│                              └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                       ↓ HTTP
                    ┌──────────────────────────────────┐
                    │     Genie Proxy Server          │
                    │     (Python, Port 8185)         │
                    │                                  │
                    │  • Handles CORS                 │
                    │  • OAuth token management       │
                    │  • Response caching (5 min)     │
                    │  • Fast polling (500ms)         │
                    └──────────────────────────────────┘
                                       ↓ HTTPS
                    ┌──────────────────────────────────┐
                    │   Databricks Genie API          │
                    │                                  │
                    │   • Conversation API            │
                    │   • Your Genie Space            │
                    │   • Your Lakehouse Data         │
                    └──────────────────────────────────┘
```

### Components

1. **Chat UI (`ui/mining_genie_chat.html`)**
   - Single HTML file with React + Chart.js
   - Served from Ignition webserver
   - No domain-specific code - works with any Genie Space

2. **Proxy Server (`ignition/scripts/genie_proxy.py`)**
   - Python HTTP server handling CORS and authentication
   - Caches responses and OAuth tokens
   - Runs on gateway host or separate server

3. **Perspective View**
   - Inline Frame component pointing to chat UI
   - Configured in Page Configuration
   - Works on Ignition 8.1, 8.2, 8.3+

---

## Quick Start

### Prerequisites

- Ignition Gateway 8.1+ with Perspective module
- Databricks workspace with Genie enabled
- Python 3.7+ on the host running the proxy
- Databricks CLI configured with OAuth

### 5-Minute Setup

```bash
# 1. Clone repository
git clone https://github.com/pravinva/genie-at-the-edge.git
cd genie-at-the-edge

# 2. Configure your Databricks workspace
# Edit ignition/scripts/genie_proxy.py lines 16-17:
#   WORKSPACE_URL = "https://your-workspace.cloud.databricks.com"
#   SPACE_ID = "your_genie_space_id"

# 3. Install Databricks CLI and authenticate
pip install databricks-cli
databricks configure --host https://your-workspace.cloud.databricks.com

# 4. Start proxy server
cd ignition/scripts
python3 genie_proxy.py
# Should see: "Genie Proxy Server running on http://localhost:8185"

# 5. Deploy chat UI to Ignition webserver
# Copy ui/mining_genie_chat.html to:
#   Linux: /usr/local/bin/ignition/webserver/webapps/main/
#   Windows: C:\Program Files\Inductive Automation\Ignition\webserver\webapps\main\

# 6. Test direct access
# Open browser: http://your-gateway:8088/mining_genie_chat.html

# 7. Create Perspective view (see next section)
```

---

## Perspective Integration

### Step 1: Deploy Chat UI to Ignition Webserver

The chat interface must be accessible from Ignition's webserver.

**Option A: Docker**
```bash
docker cp ui/mining_genie_chat.html your-container:/usr/local/bin/ignition/webserver/webapps/main/
```

**Option B: Linux**
```bash
sudo cp ui/mining_genie_chat.html /usr/local/bin/ignition/webserver/webapps/main/
```

**Option C: Windows**
```powershell
Copy-Item ui\mining_genie_chat.html "C:\Program Files\Inductive Automation\Ignition\webserver\webapps\main\"
```

**Verify deployment:**
Open browser to `http://your-gateway:8088/mining_genie_chat.html`

### Step 2: Create Perspective View

1. **Open Ignition Designer**

2. **Create New View**
   - Right-click on Views folder
   - New → View
   - Name: `genie_chat` (or any name you prefer)

3. **Add Inline Frame Component**
   - Open Component Palette (left panel)
   - Search for "Inline Frame" or find under Embedded category
   - Drag Inline Frame component onto your view
   - Set properties:
     - **URL:** `/mining_genie_chat.html` (relative path)
     - **Width:** `100%`
     - **Height:** `100%`

4. **Configure Root Container**
   - Select root container
   - Set position properties:
     - **Position:** `relative`
     - **Width:** `100%`
     - **Height:** `100%`

5. **Save View**

### Step 3: Add View to Page Configuration

1. **Open Page Configuration**
   - Designer → Project → Perspective → Page Configuration

2. **Add New Page**
   - Click "+" to add page
   - Name: `genie` (or any route you prefer)
   - Title: `AI Assistant`

3. **Configure Route**
   - Route: `/genie`
   - Default View: `genie_chat` (the view you created)

4. **Save Configuration**

5. **Test in Session**
   - Launch Perspective session
   - Navigate to: `http://your-gateway:8088/data/perspective/client/your-project/genie`

### Step 4: Add to Navigation Menu (Optional)

To make Genie chat accessible from your main HMI:

**Option A: Menu Item**
```json
{
  "label": "AI Assistant",
  "icon": "material/smart_toy",
  "route": "/genie"
}
```

**Option B: Button Navigation**
```python
# Button onActionPerformed script
system.perspective.navigate(page="/genie")
```

**Option C: Popup**
```python
# Open chat in popup window
system.perspective.openPopup(
    id="genie-chat",
    view="genie_chat",
    params={},
    title="AI Assistant",
    position={"width": 800, "height": 600},
    modal=False
)
```

---

## Configuration

### Configure Your Genie Space

Edit `ignition/scripts/genie_proxy.py` (lines 16-17):

```python
# Databricks Configuration
WORKSPACE_URL = "https://your-workspace.cloud.databricks.com"  # Your workspace
SPACE_ID = "01f10a2ce1831ea28203c2a6ce271590"  # Your Genie Space ID
```

**How to find your Genie Space ID:**
1. Open your Genie Space in Databricks
2. Look at the URL: `https://workspace.cloud.databricks.com/genie/rooms/{SPACE_ID}`
3. Copy the Space ID (long hexadecimal string)

### Change Proxy Port (Optional)

If port 8185 is already in use:

**In `genie_proxy.py` (line 370):**
```python
if __name__ == '__main__':
    port = int(os.environ.get('PROXY_PORT', 9000))  # Changed from 8185
    run_proxy(port)
```

**In `ui/mining_genie_chat.html` (line 768):**
```javascript
const GENIE_PROXY_URL = 'http://localhost:9000/api/genie/query';  // Updated port
```

### Remote Proxy Server (Optional)

If proxy runs on a different host than Ignition:

**In `ui/mining_genie_chat.html` (line 768):**
```javascript
// Change from localhost to proxy server hostname
const GENIE_PROXY_URL = 'http://proxy-server.local:8185/api/genie/query';
```

### Customize Suggested Questions (Optional)

Edit `ui/mining_genie_chat.html` (lines 759-765):

```javascript
const SAMPLE_QUESTIONS = [
    "What is the current status of equipment?",
    "Show me recent alerts",
    "What were the KPIs last hour?",
    "Show production trends",
    "Which systems have anomalies?"
];
```

---

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for comprehensive deployment instructions:

- Docker development environment
- Linux production (systemd service)
- Windows production (NSSM or Task Scheduler)
- Firewall configuration
- High availability setup
- Backup and recovery

### Production Checklist

- [ ] Configure correct Workspace URL and Space ID
- [ ] Deploy chat UI to Ignition webserver
- [ ] Install Python 3.7+ on gateway host
- [ ] Install and configure Databricks CLI
- [ ] Start proxy server as system service
- [ ] Configure firewall rules (port 8185)
- [ ] Create Perspective view with Inline Frame
- [ ] Add page to Page Configuration
- [ ] Test end-to-end with sample queries
- [ ] Monitor proxy logs for errors

---

## Performance

### Optimization Results

| Metric | Before | After | Improvement |
|--------|-------:|------:|------------:|
| **First query (cold cache)** | 8-10s | 8-10s | - |
| **Repeated query (cached)** | 8-10s | 0.03s | **280x faster** |
| **Average response time** | 8-10s | 4.7s | **47% faster** |
| **Demo wait time (12 queries)** | 102s | 41s | **60% reduction** |

### Optimizations Included

- **Response Caching** - 5-minute TTL for repeated queries
- **OAuth Token Caching** - 50-minute TTL, saves 200ms per query
- **Fast Polling** - 500ms intervals with immediate first poll
- **Thread-Safe** - Concurrent request handling
- **Auto Cache Eviction** - 100-entry limit with LRU

### Monitoring Performance

**Browser Console:**
```
Query completed in 0.03s
✓ Excellent response time: 0.03s
```

**Proxy Logs:**
```bash
# Linux
tail -f /var/log/genie-proxy.log | grep "Cache hit"

# See cache hits
✓ Cache hit for query
⏳ Polling for response (message_id: abc123)...
✓ Processed query: What is the current status...
```

See [docs/PERFORMANCE_IMPROVEMENTS.md](docs/PERFORMANCE_IMPROVEMENTS.md) for detailed benchmarks.

---

## Example: Mining Demo

This repository includes a complete mining operations demo showing:

- **Ignition Gateway** with 107 simulated equipment tags (5 haul trucks, 3 crushers, 2 conveyors)
- **Physics Simulation** with realistic operational behavior and sensor correlations
- **Databricks DLT Pipeline** ingesting real-time data via Zerobus
- **Genie Space** trained on mining equipment data
- **Fault Injection** system for demonstrating predictive analytics

### Demo Architecture

```
Ignition Gateway (Docker)
  ├── 107 Memory Tags (1 Hz updates)
  ├── Physics Simulation (haul truck cycles, crusher vibration)
  └── Fault Injection (CR_002 bearing degradation)
         ↓ Zerobus (150 tags/sec)
Databricks Lakehouse
  ├── Bronze (Raw sensor data, <1s latency)
  ├── Silver (Normalized, <500ms latency)
  └── Gold (Analytics, 1-min aggregations)
         ↓ SQL Queries
Genie Space
  └── Answers questions like:
      • "Show vibration trends for CR_002"
      • "What is the status of all haul trucks?"
      • "Which equipment has anomalies?"
```

### Running the Mining Demo

```bash
# 1. Start Ignition with simulated equipment
cd docker
docker-compose up -d ignition

# 2. Deploy Databricks DLT pipeline
python3 databricks/deploy_dlt_pipeline.py

# 3. Start Genie proxy
python3 ignition/scripts/genie_proxy.py

# 4. Open Perspective session
# Navigate to: http://localhost:8088/data/perspective/client/samplequickstart/genie

# 5. Try sample queries:
#    - "Show vibration trends for CR_002 over time"
#    - "What is the current status of all haul trucks?"
#    - "Which equipment has anomalies?"
```

### Mining Demo Files

- `ignition/udts/` - Haul Truck, Crusher, Conveyor UDT definitions
- `ignition/scripts/mining_physics_simulation_fixed.py` - Equipment behavior simulation
- `databricks/mining_realtime_dlt.py` - Delta Live Tables pipeline
- `demo/` - Demo scripts, checklists, and presentation materials

**Note:** The mining demo is just one example. The core Genie chat interface works with any Databricks Genie Space and any data domain (manufacturing, energy, logistics, retail, etc.).

---

## Documentation

### Getting Started
- [Quick Start](#quick-start) - 5-minute setup guide
- [Perspective Integration](#perspective-integration) - Step-by-step embedding instructions
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production deployment guide

### Technical Details
- [docs/PERFORMANCE_IMPROVEMENTS.md](docs/PERFORMANCE_IMPROVEMENTS.md) - Optimization details and benchmarks
- [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) - Complete project overview
- [docs/STATUS.md](docs/STATUS.md) - Development status and roadmap

### Demo Materials
- `demo/demo_script.md` - 15-minute customer demo walkthrough
- `demo/pre_demo_checklist.md` - Setup verification checklist
- `demo/qna_preparation.md` - Common questions and answers

### Troubleshooting

**Issue: Chat shows "Using mock data"**
- Proxy server not running or not reachable
- Check proxy: `curl http://localhost:8185/api/genie/query -X POST -H "Content-Type: application/json" -d '{"question":"test"}'`

**Issue: "Failed to get authentication token"**
- Databricks CLI not configured
- Run: `databricks configure --host https://your-workspace.cloud.databricks.com`

**Issue: CORS errors in browser console**
- Proxy URL mismatch in chat UI
- Check `mining_genie_chat.html` line 768 matches proxy host/port

**Issue: Slow responses (>15 seconds)**
- SQL warehouse cold start
- Use Serverless SQL warehouse for instant startup

See [docs/DEPLOYMENT.md#troubleshooting](docs/DEPLOYMENT.md#troubleshooting) for more issues.

---

## Technology Stack

### Ignition Components
- **Perspective Module** - HMI framework (8.1+ compatible)
- **Inline Frame Component** - Embeds chat UI
- **Memory Tags** - Real-time equipment data (demo only)

### Databricks Components
- **Genie Conversation API** - Natural language query engine
- **Genie Spaces** - Domain-specific AI assistants
- **Unity Catalog** - Data governance and access control
- **Delta Live Tables** - Real-time data pipelines (demo only)
- **Lakehouse** - Unified analytics platform (demo only)

### Chat Interface
- **React 18** - UI framework (via CDN)
- **Chart.js 4.4** - Visualization library
- **Marked.js** - Markdown rendering
- **Babel Standalone** - JSX transpilation

### Proxy Server
- **Python 3.7+** - Runtime
- **http.server** - Built-in HTTP server
- **urllib** - HTTP client
- **Databricks CLI** - OAuth token management

---

## Compatibility

| Component | Version | Notes |
|-----------|---------|-------|
| Ignition Gateway | 8.1+ | Perspective module required |
| Python | 3.7+ | For proxy server |
| Databricks Runtime | 13.3+ | Genie support |
| Databricks CLI | 0.18+ | OAuth authentication |
| Browsers | Modern (Chrome, Firefox, Edge) | ES6+ support |

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Support

- **GitHub Issues:** [https://github.com/pravinva/genie-at-the-edge/issues](https://github.com/pravinva/genie-at-the-edge/issues)
- **Documentation:** See `docs/` folder
- **Databricks Genie Docs:** [https://docs.databricks.com/genie/](https://docs.databricks.com/genie/)
- **Ignition Docs:** [https://docs.inductiveautomation.com/](https://docs.inductiveautomation.com/)

---

## Acknowledgments

- **Databricks** - Genie AI and lakehouse platform
- **Inductive Automation** - Ignition SCADA platform
- **Open Source Libraries** - React, Chart.js, Marked.js

---

**Made with Claude Code** - [https://claude.com/claude-code](https://claude.com/claude-code)
