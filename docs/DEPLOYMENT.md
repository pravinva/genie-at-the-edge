# Genie Chat Deployment Guide

## Overview

This guide explains how to deploy the Genie AI chat interface to your Ignition Gateway, whether running in Docker or on existing edge gateways.

## Architecture

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Ignition Gateway   │────▶│  Genie Proxy     │────▶│  Databricks Genie   │
│  (Edge/Docker)      │     │  (Python Server) │     │  Conversation API   │
│                     │     │  Port 8185       │     │                     │
│  mining_genie_chat  │     │  CORS + Auth     │     │  Space ID:          │
│  /html              │     │  Token Cache     │     │  01f10a2ce1...      │
└─────────────────────┘     └──────────────────┘     └─────────────────────┘
```

## Prerequisites

- **Ignition Gateway** 8.1.x or later with Perspective module
- **Python 3.7+** on the host running the proxy
- **Databricks CLI** configured with OAuth
- **Network access** from proxy to Databricks workspace
- **Network access** from Ignition to proxy (localhost or LAN)

## Deployment Options

### Option 1: Docker Environment (Development/Testing)

Best for: Local development, testing, proof-of-concept

```bash
# 1. Start Ignition container
cd docker
docker-compose up -d ignition

# 2. Deploy chat UI
docker cp ../ui/mining_genie_chat.html genie-at-edge-ignition:/usr/local/bin/ignition/webserver/webapps/main/

# 3. Start proxy server
cd ../ignition/scripts
python3 genie_proxy.py &

# 4. Access chat
# Direct: http://localhost:8183/mining_genie_chat.html
# Perspective: http://localhost:8183/data/perspective/client/<your-project>/genie
```

### Option 2: Existing Gateway at Edge (Production)

Best for: Customer deployments, production systems

#### Step 1: Deploy Chat UI to Gateway

**Method A: Manual Copy (Windows)**
```powershell
# Copy file to Ignition webserver directory
Copy-Item mining_genie_chat.html "C:\Program Files\Inductive Automation\Ignition\webserver\webapps\main\"
```

**Method B: Manual Copy (Linux)**
```bash
# Copy file to Ignition webserver directory
sudo cp mining_genie_chat.html /usr/local/bin/ignition/webserver/webapps/main/
```

**Method C: Designer Upload**
1. Open Ignition Designer
2. Navigate to Tools → Script Console
3. Run this script to upload via Python:
```python
import system.file

# Read local file
with open('/path/to/mining_genie_chat.html', 'r') as f:
    content = f.read()

# Write to webserver directory
webserver_path = system.file.getProjectResource('webserver/mining_genie_chat.html')
with open(webserver_path, 'w') as f:
    f.write(content)
```

#### Step 2: Install Python Dependencies on Gateway Host

```bash
# Install Python 3 if not already installed
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install python3 python3-pip

# RHEL/CentOS
sudo yum install python3 python3-pip

# Verify Python version (3.7+ required)
python3 --version
```

#### Step 3: Install Databricks CLI

```bash
# Install databricks CLI
pip3 install databricks-cli

# Configure OAuth authentication
databricks configure --host https://your-workspace.cloud.databricks.com
# Follow prompts to authenticate via OAuth flow
```

#### Step 4: Deploy and Start Proxy Server

```bash
# Create service directory
sudo mkdir -p /opt/genie-proxy
sudo cp genie_proxy.py /opt/genie-proxy/

# Test proxy manually first
cd /opt/genie-proxy
python3 genie_proxy.py
# Should see: "🚀 Genie Proxy Server running on http://localhost:8185"
# Ctrl+C to stop
```

#### Step 5: Create Systemd Service (Linux) - Production

```bash
# Create service file
sudo cat > /etc/systemd/system/genie-proxy.service << 'EOF'
[Unit]
Description=Genie AI Chat Proxy Server
After=network.target

[Service]
Type=simple
User=ignition
WorkingDirectory=/opt/genie-proxy
ExecStart=/usr/bin/python3 /opt/genie-proxy/genie_proxy.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/genie-proxy.log
StandardError=append:/var/log/genie-proxy-error.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable genie-proxy
sudo systemctl start genie-proxy

# Check status
sudo systemctl status genie-proxy

# View logs
sudo journalctl -u genie-proxy -f
```

#### Step 6: Create Windows Service (Windows)

**Option A: Using NSSM (Non-Sucking Service Manager)**
```powershell
# Download NSSM from https://nssm.cc/download

# Install as service
nssm install GenieProxy "C:\Python39\python.exe" "C:\Program Files\Genie-Proxy\genie_proxy.py"
nssm set GenieProxy AppDirectory "C:\Program Files\Genie-Proxy"
nssm set GenieProxy DisplayName "Genie AI Chat Proxy"
nssm set GenieProxy Description "Databricks Genie conversation proxy for Ignition"
nssm set GenieProxy Start SERVICE_AUTO_START

# Start service
nssm start GenieProxy

# Check status
nssm status GenieProxy
```

**Option B: Using Task Scheduler**
1. Open Task Scheduler
2. Create New Task:
   - Name: "Genie Proxy Server"
   - Run whether user is logged on or not
   - Trigger: At startup
   - Action: Start program
     - Program: `C:\Python39\python.exe`
     - Arguments: `C:\Program Files\Genie-Proxy\genie_proxy.py`
     - Start in: `C:\Program Files\Genie-Proxy\`

#### Step 7: Configure Perspective View

1. Open Ignition Designer
2. Create new Perspective View (name: `genie_chat`)
3. Add **Inline Frame** component:
   - URL: `/mining_genie_chat.html` (relative path)
   - Width: `100%`
   - Height: `100%`
4. Add view to page in Page Configuration:
   - Route: `/genie` or `/mining-chat`
   - Default view: `genie_chat`

#### Step 8: Configure Firewall Rules

```bash
# Allow proxy port (if needed for remote access)
# Linux (firewalld)
sudo firewall-cmd --permanent --add-port=8185/tcp
sudo firewall-cmd --reload

# Linux (iptables)
sudo iptables -A INPUT -p tcp --dport 8185 -j ACCEPT
sudo iptables-save

# Windows Firewall
New-NetFirewallRule -DisplayName "Genie Proxy" -Direction Inbound -Port 8185 -Protocol TCP -Action Allow
```

## Configuration

### Edit Workspace and Space ID

Edit `genie_proxy.py` lines 16-17:

```python
# Databricks Configuration
WORKSPACE_URL = "https://your-workspace.cloud.databricks.com"  # ← Change this
SPACE_ID = "your_genie_space_id"  # ← Change this
```

### Change Proxy Port

Edit `genie_proxy.py` line 370 or set environment variable:

```bash
# Environment variable method
export PROXY_PORT=9000
python3 genie_proxy.py

# Or edit line 370 in code
if __name__ == '__main__':
    port = int(os.environ.get('PROXY_PORT', 9000))  # Changed from 8185
    run_proxy(port)
```

Then update `mining_genie_chat.html` line 768:

```javascript
const GENIE_PROXY_URL = 'http://localhost:9000/api/genie/query';  // Update port
```

### Remote Proxy Access

If proxy runs on different host than Ignition:

Edit `mining_genie_chat.html` line 768:

```javascript
// Before (localhost)
const GENIE_PROXY_URL = 'http://localhost:8185/api/genie/query';

// After (remote host)
const GENIE_PROXY_URL = 'http://proxy-host.local:8185/api/genie/query';
```

## Performance Optimizations

The current implementation includes these optimizations:

### 1. Token Caching (50 minutes)
- OAuth tokens cached for 50 minutes
- Eliminates repeated CLI calls
- **Speedup:** ~200ms per query

### 2. Response Caching (5 minutes)
- First-time queries cached for 5 minutes
- Instant responses for repeated questions
- **Speedup:** 8-10 seconds → 27ms (300x faster)

### 3. Fast Polling (500ms)
- Polls every 500ms instead of 1 second
- First poll is immediate (no initial delay)
- **Speedup:** ~50% faster perceived response

### 4. Cache Statistics
Check proxy logs for cache performance:
```bash
# Linux
tail -f /var/log/genie-proxy.log | grep "Cache hit"

# See timing in browser console
# Open DevTools → Console while using chat
# Shows: "Query completed in 0.03s (cached)" or "Query completed in 8.4s"
```

## Performance Benchmarks

| Scenario | First Query (Cold) | Second Query (Cached) | Speedup |
|----------|-------------------:|----------------------:|--------:|
| Simple status query | 8.4s | 0.03s | 280x |
| Chart with data | 10.9s | 0.04s | 272x |
| Follow-up question | 6.2s | 0.03s | 206x |

**Cache hit rate (typical):** 40-60% in production demos

## Troubleshooting

### Issue: Chat UI shows "Using mock data"

**Cause:** Proxy server not running or not reachable

**Solution:**
```bash
# Check if proxy is running
# Linux
sudo systemctl status genie-proxy
# or
ps aux | grep genie_proxy

# Windows
nssm status GenieProxy
# or check Task Scheduler

# Test proxy directly
curl -X POST http://localhost:8185/api/genie/query \
  -H "Content-Type: application/json" \
  -d '{"question":"test"}'
```

### Issue: "Failed to get authentication token"

**Cause:** Databricks CLI not configured or OAuth expired

**Solution:**
```bash
# Reconfigure Databricks CLI
databricks configure --host https://your-workspace.cloud.databricks.com

# Test authentication
databricks auth token --host https://your-workspace.cloud.databricks.com
```

### Issue: CORS errors in browser console

**Cause:** Proxy URL mismatch or proxy not adding CORS headers

**Solution:**
1. Check `mining_genie_chat.html` line 768 matches proxy host/port
2. Verify proxy is running (should see CORS headers in response)
3. Check browser DevTools → Network tab for actual request URL

### Issue: Slow responses (>15 seconds)

**Cause:** SQL warehouse cold start or serverless not enabled

**Solution:**
1. Use Serverless SQL warehouse (instant startup)
2. Or keep Classic warehouse always-on during demos
3. Check warehouse status in Databricks UI

### Issue: Chat not visible in Perspective

**Cause:** Page configuration missing or incorrect view path

**Solution:**
1. Designer → Page Configuration
2. Verify route `/genie` exists
3. Check default view is set to `genie_chat`
4. Verify Inline Frame URL is `/mining_genie_chat.html`

## Security Considerations

### Network Security
- Proxy runs on localhost by default (127.0.0.1)
- For remote access, use VPN or restrict firewall to known IPs
- Consider HTTPS proxy with nginx/Apache reverse proxy

### Authentication
- OAuth tokens expire after 1 hour (cached for 50 min)
- No credentials stored in chat UI (all via proxy)
- Proxy inherits databricks CLI authentication (user context)

### Production Hardening
```python
# Edit genie_proxy.py line 127
# Restrict CORS to specific origins
self.send_header('Access-Control-Allow-Origin', 'https://your-gateway.local')
# Instead of '*'
```

## Monitoring

### Proxy Health Check
```bash
# Simple health check endpoint (add to proxy if needed)
curl http://localhost:8185/health

# Or check if port is listening
netstat -an | grep 8185
```

### Performance Monitoring
```python
# Add to genie_proxy.py for metrics
METRICS = {
    'total_queries': 0,
    'cache_hits': 0,
    'cache_misses': 0,
    'avg_response_time': 0
}

# Log every 100 queries
if METRICS['total_queries'] % 100 == 0:
    print(f"Metrics: {METRICS}", file=sys.stderr)
```

## Scaling Considerations

### Multiple Gateways
- Each gateway needs its own proxy instance
- Or run single proxy on shared server (update chat UI URLs)
- Consider load balancer if >10 concurrent users

### High Availability
```bash
# Run 2 proxy instances on different ports
python3 genie_proxy.py &  # Port 8185
PROXY_PORT=8186 python3 genie_proxy.py &  # Port 8186

# Configure haproxy or nginx load balancer
# UI connects to load balancer instead of direct proxy
```

## Backup and Recovery

### Backup Proxy Configuration
```bash
# Backup proxy script and config
tar -czf genie-proxy-backup.tar.gz \
  /opt/genie-proxy/genie_proxy.py \
  /etc/systemd/system/genie-proxy.service \
  /var/log/genie-proxy.log
```

### Restore from Backup
```bash
# Extract backup
tar -xzf genie-proxy-backup.tar.gz -C /

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart genie-proxy
```

## Updates and Maintenance

### Update Chat UI
```bash
# 1. Backup current version
docker cp genie-at-edge-ignition:/usr/local/bin/ignition/webserver/webapps/main/mining_genie_chat.html \
  mining_genie_chat.html.backup

# 2. Deploy new version
docker cp ui/mining_genie_chat.html \
  genie-at-edge-ignition:/usr/local/bin/ignition/webapps/main/

# 3. Clear browser cache or force refresh (Ctrl+F5)
```

### Update Proxy
```bash
# 1. Backup current version
sudo cp /opt/genie-proxy/genie_proxy.py /opt/genie-proxy/genie_proxy.py.backup

# 2. Deploy new version
sudo cp genie_proxy.py /opt/genie-proxy/

# 3. Restart service
sudo systemctl restart genie-proxy

# 4. Verify
sudo systemctl status genie-proxy
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/pravinva/genie-at-the-edge/issues
- Documentation: See `docs/` folder
- Databricks Genie Docs: https://docs.databricks.com/genie/

## Appendix: File Locations

### Docker Environment
- Chat UI: Container path `/usr/local/bin/ignition/webserver/webapps/main/mining_genie_chat.html`
- Proxy: Host path `ignition/scripts/genie_proxy.py`

### Linux Production
- Chat UI: `/usr/local/bin/ignition/webserver/webapps/main/mining_genie_chat.html`
- Proxy: `/opt/genie-proxy/genie_proxy.py`
- Service: `/etc/systemd/system/genie-proxy.service`
- Logs: `/var/log/genie-proxy.log`

### Windows Production
- Chat UI: `C:\Program Files\Inductive Automation\Ignition\webserver\webapps\main\mining_genie_chat.html`
- Proxy: `C:\Program Files\Genie-Proxy\genie_proxy.py`
- Logs: Check Task Scheduler or NSSM logs

## License

MIT License - See LICENSE file for details
