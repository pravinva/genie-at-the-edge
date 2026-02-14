#!/usr/bin/env python3
"""
Mining Operations Genie Demo - UI Deployment Automation
Deploys chat UI to Databricks Files and configures access
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

try:
    from databricks.sdk import WorkspaceClient
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError as e:
    print(f"Error: Missing required dependencies. Run: pip install -r requirements.txt")
    print(f"Details: {e}")
    sys.exit(1)

console = Console()


class UIDeployer:
    """Handles deployment of chat UI to Databricks"""

    def __init__(self, config_path: str = "environment_config.yaml", environment: str = "dev"):
        """Initialize deployer with configuration"""
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.workspace_client: Optional[WorkspaceClient] = None
        self.deployment_state: Dict[str, Any] = {}

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = self.project_root / "build" / config_path
        if not config_file.exists():
            console.print(f"[red]Error: Configuration file not found: {config_file}[/red]")
            sys.exit(1)

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def initialize_client(self) -> None:
        """Initialize Databricks workspace client"""
        console.print("[yellow]Initializing Databricks connection...[/yellow]")

        token = os.environ.get("DATABRICKS_TOKEN")
        if not token:
            console.print("[red]Error: DATABRICKS_TOKEN environment variable not set[/red]")
            console.print("Set it with: export DATABRICKS_TOKEN=your_token_here")
            sys.exit(1)

        db_config = self.config["databricks"][self.environment]
        workspace_url = db_config["workspace_url"]

        try:
            self.workspace_client = WorkspaceClient(
                host=workspace_url,
                token=token
            )
            self.workspace_client.current_user.me()
            console.print(f"[green]✓ Connected to Databricks workspace: {workspace_url}[/green]")
        except Exception as e:
            console.print(f"[red]Error connecting to Databricks: {e}[/red]")
            sys.exit(1)

    def validate_ui_files(self) -> bool:
        """Validate UI files exist"""
        console.print("\n[bold blue]Validating UI Files[/bold blue]")

        ui_dir = self.project_root / "ui"
        required_files = [
            "genie_chat_perspective.html"
        ]

        missing_files = []
        for file_name in required_files:
            file_path = ui_dir / file_name
            if file_path.exists():
                file_size = file_path.stat().st_size
                console.print(f"[green]✓ Found: {file_name} ({file_size:,} bytes)[/green]")
            else:
                console.print(f"[red]✗ Missing: {file_name}[/red]")
                missing_files.append(file_name)

        if missing_files:
            console.print(f"\n[red]Error: Missing required files: {missing_files}[/red]")
            return False

        return True

    def upload_to_databricks_files(self) -> Optional[str]:
        """Upload UI files to Databricks Files"""
        console.print("\n[bold blue]Uploading UI to Databricks Files[/bold blue]")

        ui_file = self.project_root / "ui" / "genie_chat_perspective.html"

        # Create target directory in DBFS
        target_dir = "/Volumes/field_engineering/mining_demo/files/ui"
        target_path = f"{target_dir}/genie_chat_perspective.html"

        try:
            # Read file content
            with open(ui_file, 'rb') as f:
                file_content = f.read()

            console.print(f"[yellow]Uploading to: {target_path}[/yellow]")

            # Upload using Files API
            try:
                # Create directory first
                self.workspace_client.files.create_directory(target_dir)
                console.print(f"[green]✓ Created directory: {target_dir}[/green]")
            except Exception:
                # Directory might already exist
                pass

            # Upload file
            self.workspace_client.files.upload(
                file_path=target_path,
                contents=file_content,
                overwrite=True
            )

            console.print(f"[green]✓ Uploaded successfully[/green]")

            # Construct public URL
            db_config = self.config["databricks"][self.environment]
            workspace_url = db_config["workspace_url"]
            public_url = f"{workspace_url}/files{target_path}"

            self.deployment_state["ui_url"] = public_url
            return public_url

        except Exception as e:
            console.print(f"[red]Error uploading file: {e}[/red]")
            console.print(f"\n[yellow]Alternative: Manual upload instructions[/yellow]")
            self._show_manual_upload_instructions()
            return None

    def _show_manual_upload_instructions(self) -> None:
        """Show manual upload instructions"""
        ui_file = self.project_root / "ui" / "genie_chat_perspective.html"

        console.print(f"""
[cyan]Manual Upload Instructions:[/cyan]

1. Open Databricks workspace
2. Navigate to: Data > Files
3. Create folder: mining-demo
4. Upload file: {ui_file}
5. Click on uploaded file to get public URL
6. Copy URL for use in Perspective view

[yellow]The URL will look like:[/yellow]
  https://your-workspace.cloud.databricks.com/files/...

Use this URL in the Perspective Embedded Frame component.
        """)

    def configure_genie_integration(self) -> bool:
        """Generate Genie integration configuration"""
        console.print("\n[bold blue]Configuring Genie Integration[/bold blue]")

        db_config = self.config["databricks"][self.environment]
        genie_config = self.config["components"]["genie"]

        workspace_url = db_config["workspace_url"]
        workspace_id = db_config["workspace_id"]

        # Note: Actual Genie space ID would be retrieved from deployment state
        genie_space_id = self.deployment_state.get("genie_space_id", "YOUR_GENIE_SPACE_ID")

        config_content = f"""# Genie Integration Configuration

## Databricks Settings

- **Workspace URL**: `{workspace_url}`
- **Workspace ID**: `{workspace_id}`
- **Genie Space ID**: `{genie_space_id}`
- **Warehouse ID**: `{db_config['warehouse_id']}`
- **Catalog**: `{db_config['catalog']}`
- **Schema**: `{db_config['schema']}`

## Authentication

Set the following environment variable in Ignition session:

```python
# In Perspective Session Startup Script
session.custom.databricks_token = system.tag.readBlocking(['[default]System/Databricks/Token'])[0].value
session.custom.workspace_id = "{workspace_id}"
session.custom.genie_space_id = "{genie_space_id}"
```

## Embedded Frame Configuration

Add Embedded Frame component with URL:

```
{self.deployment_state.get('ui_url', 'UPLOAD_UI_FIRST')}?token={{{{session.custom.databricks_token}}}}&workspace={{{{session.custom.workspace_id}}}}&space={{{{session.custom.genie_space_id}}}}
```

## Chat URL Construction

The chat UI expects these URL parameters:

- `token`: Databricks personal access token
- `workspace`: Workspace ID
- `space`: Genie space ID (get from Databricks UI after creating space)

Example full URL:
```
{self.deployment_state.get('ui_url', 'UPLOAD_UI_FIRST')}?token=dapi...&workspace={workspace_id}&space=01abc123
```

## Testing

1. Create test URL with your credentials
2. Open in browser directly (outside Ignition)
3. Verify chat loads and responds
4. Then embed in Perspective view

## Security Notes

- Store Databricks token in Ignition system tags (encrypted)
- Use session custom properties, not view parameters
- Enable HTTPS for production deployments
- Restrict network access to Databricks workspace

## Troubleshooting

**Chat doesn't load:**
- Verify URL is accessible from browser
- Check CORS settings in Databricks
- Verify token has correct permissions

**Genie doesn't respond:**
- Verify space ID is correct
- Check warehouse is running
- Verify token permissions include SQL execution

**Slow responses:**
- Keep warehouse running (avoid cold starts)
- Consider serverless SQL warehouse
- Check network latency to Databricks

"""

        config_file = self.project_root / "build" / f"genie_integration_config_{self.environment}.md"
        with open(config_file, 'w') as f:
            f.write(config_content)

        console.print(f"[green]✓ Configuration saved to: {config_file}[/green]")
        return True

    def create_perspective_integration_guide(self) -> None:
        """Create detailed Perspective integration guide"""
        console.print("\n[bold blue]Creating Integration Guide[/bold blue]")

        ui_url = self.deployment_state.get('ui_url', 'UPLOAD_UI_FIRST')
        db_config = self.config["databricks"][self.environment]

        guide_content = f"""# Perspective Integration Guide

Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
Environment: {self.environment.upper()}

## Overview

This guide walks through integrating the Genie chat UI into your Perspective view.

## Prerequisites

- [x] UI uploaded to Databricks: `{ui_url}`
- [ ] Genie space created in Databricks
- [ ] Perspective project created: MiningOperations
- [ ] View created: MiningOperationsDashboard

## Step 1: Configure Session Properties

In Perspective project, add session startup script:

```python
# Session Startup Script

def onStartup(session):
    # Get Databricks token from secure storage
    token_path = '[default]System/Databricks/Token'
    token = system.tag.readBlocking([token_path])[0].value

    # Set session custom properties
    session.custom.databricks_token = token
    session.custom.workspace_id = "{db_config['workspace_id']}"
    session.custom.genie_space_id = "GET_FROM_DATABRICKS_UI"  # Update after creating Genie space
    session.custom.workspace_url = "{db_config['workspace_url']}"

    # Construct chat URL
    base_url = "{ui_url}"
    chat_url = base_url + "?token=" + token + "&workspace=" + session.custom.workspace_id + "&space=" + session.custom.genie_space_id

    session.custom.genie_chat_url = chat_url

    # Initialize pending question (for "Ask AI" buttons)
    session.custom.pending_question = ""
```

## Step 2: Add Embedded Frame

In your MiningOperationsDashboard view:

1. Add **Embedded Frame** component (right panel)
2. Set dimensions: 30% width, full height
3. Configure URL property:

```
{{{{session.custom.genie_chat_url}}}}
```

4. Enable these settings:
   - Allow same origin: Yes
   - Sandbox: Allow scripts, Allow same origin
   - Border: None

## Step 3: Add "Ask AI" Buttons

In alarm table or equipment cards, add buttons with onClick script:

```python
# Button onClick Script

def runAction(self, event):
    # Get alarm or equipment context
    alarm_name = self.getSibling("AlarmName").text
    equipment_id = self.getSibling("EquipmentID").text

    # Construct question
    question = "Why is " + equipment_id + " showing alarm: " + alarm_name + "?"

    # Update session property (triggers URL update via binding)
    self.session.custom.pending_question = question

    # Trigger iframe reload with pre-filled question
    chat_url = self.session.custom.genie_chat_url + "&question=" + system.net.httpQuote(question)
    self.session.custom.genie_chat_url = chat_url
```

## Step 4: Add Real-Time Equipment Status

Bind equipment status cards to tags:

```python
# Equipment Card - Crusher Status

# Tag binding for vibration
{{{{[default]Mining/Equipment/CR_002/Vibration_MM_S}}}}

# Color binding (changes based on value)
if {{{{[default]Mining/Equipment/CR_002/Vibration_MM_S}}}} > 40:
    return "red"
elif {{{{[default]Mining/Equipment/CR_002/Vibration_MM_S}}}} > 30:
    return "orange"
else:
    return "green"
```

## Step 5: Test Integration

1. Open Perspective session in browser
2. Verify equipment status displays
3. Verify chat UI loads in iframe
4. Type test question: "Show me current crusher status"
5. Verify Genie responds within 5 seconds
6. Click "Ask AI" button on alarm
7. Verify question pre-fills in chat

## Step 6: Production Checklist

- [ ] Replace test token with production token
- [ ] Store token in encrypted tag
- [ ] Enable HTTPS on Ignition Gateway
- [ ] Configure firewall rules (Ignition ↔ Databricks)
- [ ] Test from multiple clients
- [ ] Verify performance under load
- [ ] Document any customizations
- [ ] Train operators on chat functionality

## Troubleshooting

### Chat UI doesn't load

Check:
1. UI URL is accessible: {ui_url}
2. Session property is set: `session.custom.genie_chat_url`
3. Databricks token is valid
4. Browser console for errors (F12)

Solution:
- Test URL directly in browser with token
- Check iframe sandbox permissions
- Verify CORS headers

### Genie doesn't respond

Check:
1. Genie space ID is correct
2. Warehouse is running: {db_config['warehouse_id']}
3. Token has SQL execution permissions
4. Gold tables have recent data

Solution:
- Test Genie in Databricks UI directly
- Verify DLT pipeline is processing
- Check warehouse query history

### Slow response times

Check:
1. Warehouse state (cold vs warm)
2. Network latency
3. Query complexity

Solution:
- Keep warehouse running during demo
- Use serverless SQL warehouse
- Pre-warm with test queries

### "Ask AI" button doesn't work

Check:
1. Button onClick script is configured
2. Session custom properties are accessible
3. URL encoding is correct

Solution:
- Test script in Designer script console
- Verify session.custom.pending_question updates
- Check browser network tab for URL changes

## Advanced Customization

### Add suggested questions

Modify chat UI to show context-aware suggestions:

```javascript
// In genie_chat_perspective.html

const suggestedQuestions = [
    "Show me current status of all crushers",
    "Why is Crusher 2 vibration high?",
    "Compare Crusher 2 to other crushers",
    "Show production for last hour",
    "Which equipment has anomalies?"
];
```

### Add data visualizations

Integrate Chart.js for inline charts:

```javascript
// Parse Genie response for tabular data
// Render as chart if data is numeric time series
```

### Add conversation history

Store chat history in Ignition database:

```python
# After each Genie response
system.db.runPrepUpdate(
    "INSERT INTO chat_history (timestamp, question, answer, user) VALUES (?, ?, ?, ?)",
    [system.date.now(), question, answer, session.props.auth.user.userName]
)
```

## Support

- Deployment issues: See build/rollback_procedures.md
- UI customization: See ui/README.md
- Databricks integration: See databricks/pipelines/README.md
- Testing procedures: See build/build_sequence.md

"""

        guide_file = self.project_root / "build" / f"perspective_integration_guide_{self.environment}.md"
        with open(guide_file, 'w') as f:
            f.write(guide_content)

        console.print(f"[green]✓ Integration guide saved to: {guide_file}[/green]")

    def deploy_all(self) -> bool:
        """Deploy all UI components"""
        console.print(Panel.fit(
            f"[bold green]Mining Operations Genie Demo[/bold green]\n"
            f"UI Deployment - Environment: {self.environment.upper()}",
            border_style="green"
        ))

        # Initialize
        self.initialize_client()

        # Validate files
        if not self.validate_ui_files():
            return False

        # Upload to Databricks
        ui_url = self.upload_to_databricks_files()

        # Generate configuration
        self.configure_genie_integration()

        # Create integration guide
        self.create_perspective_integration_guide()

        # Summary
        if ui_url:
            console.print(Panel.fit(
                f"[bold green]✓ UI Deployment Complete![/bold green]\n\n"
                f"Chat UI URL:\n{ui_url}\n\n"
                f"Next steps:\n"
                f"1. Create Genie space in Databricks UI\n"
                f"2. Get Genie space ID from UI\n"
                f"3. Follow integration guide to embed in Perspective\n"
                f"4. Test chat functionality\n\n"
                f"See: build/perspective_integration_guide_{self.environment}.md",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                "[yellow]UI Upload Failed - Manual Steps Required[/yellow]\n\n"
                "Follow manual upload instructions above.\n"
                "Then proceed with integration guide.",
                border_style="yellow"
            ))

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy UI components")
    parser.add_argument(
        "--environment",
        choices=["dev", "prod"],
        default="dev",
        help="Deployment environment"
    )

    args = parser.parse_args()

    deployer = UIDeployer(environment=args.environment)
    success = deployer.deploy_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
