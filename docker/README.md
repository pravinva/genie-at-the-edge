# Ignition Gateway Docker Setup

Run Ignition Gateway 8.1 in Docker for testing the Genie at the Edge demo.

## Quick Start

```bash
# Start Ignition Gateway
cd docker
docker-compose up -d

# Wait for startup (30-60 seconds)
docker-compose logs -f ignition

# Access Gateway
# HTTP:  http://localhost:8181
# HTTPS: https://localhost:8143

# Default credentials
# Username: admin
# Password: password

# Stop Gateway
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Configuration

The `.env` file contains:
- `IGNITION_TAG` - Ignition version (default: 8.1.51)
- `GATEWAY_ADMIN_USERNAME` - Admin username (default: admin)
- `GATEWAY_ADMIN_PASSWORD` - Admin password (default: password)

## Ports

- **8181** - HTTP Gateway web interface
- **8143** - HTTPS Gateway web interface (self-signed cert)

## Import UDTs and Scripts

After Ignition starts:

1. **Access Designer:**
   ```
   Open Ignition Designer Launcher
   Add Gateway: http://localhost:8181
   Username: admin
   Password: password
   ```

2. **Import UDTs:**
   ```
   Designer > Tag Browser > Right-click > Import Tags
   Select: ../ignition/udts/HaulTruck_UDT.json
   Select: ../ignition/udts/Crusher_UDT.json
   Select: ../ignition/udts/Conveyor_UDT.json
   ```

3. **Create Tag Instances:**
   ```
   Gateway Config > Scripting > Script Console
   Paste: ../ignition/udts/create_tag_instances.py
   Run
   ```

4. **Deploy Gateway Scripts:**
   ```
   Gateway Config > Scripting > Timer Scripts > Add
   Name: MiningPhysicsSimulation
   Delay: 1 second (Fixed Rate)
   Paste: ../ignition/scripts/mining_physics_simulation.py
   Enable and Save
   ```

5. **Deploy Fault Injection (Optional):**
   ```
   Gateway Config > Scripting > Timer Scripts > Add
   Name: FaultInjectionCR002
   Delay: 1 second (Fixed Rate)
   Paste: ../ignition/scripts/fault_injection_cr002.py
   Disable initially (enable when ready for demo)
   ```

## Verify Installation

```bash
# Check logs
docker-compose logs -f ignition

# Check container status
docker-compose ps

# Verify HTTP access (should return 302 redirect)
curl -I http://localhost:8181

# Restart if needed
docker-compose restart ignition
```

**Expected Results:**
```
NAME                     STATUS                    PORTS
genie-at-edge-ignition   Up X seconds (healthy)    0.0.0.0:8181->8088/tcp, 0.0.0.0:8143->8043/tcp

HTTP/1.1 302 Found (redirects to gateway web interface)
```

**Startup Time:** Approximately 30-40 seconds until "Gateway started" message appears

## Troubleshooting

**Port already in use:**
```bash
# Change port in docker-compose.yml
ports:
  - "8182:8088"  # Use different host port
```

**Container won't start:**
```bash
# Check logs
docker-compose logs ignition

# Remove and recreate
docker-compose down -v
docker-compose up -d
```

**Memory issues:**
```bash
# Increase Docker memory limit
# Docker Desktop > Settings > Resources > Memory: 4GB+
```

## Data Persistence

Data is stored in Docker volume `genie-at-edge-ignition-data`:
```bash
# Inspect volume
docker volume inspect genie-at-edge-ignition-data

# Backup data
docker run --rm -v genie-at-edge-ignition-data:/data -v $(pwd):/backup alpine tar czf /backup/ignition-backup.tar.gz /data

# Restore data
docker run --rm -v genie-at-edge-ignition-data:/data -v $(pwd):/backup alpine tar xzf /backup/ignition-backup.tar.gz -C /
```

## Next Steps

After Ignition is running:
1. Import UDTs and create tags
2. Deploy physics simulation script
3. Verify tags are updating (Tag Browser)
4. Deploy Databricks pipeline (see `../databricks/pipelines/README.md`)
5. Deploy Genie chat UI (see `../ui/README.md`)
6. Integrate Perspective view (see `../ui/integration_config.md`)
