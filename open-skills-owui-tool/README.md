# Open Skills Tool for OpenWebUI

This OpenWebUI tool provides a bridge to the [Open-Skills MCP server](https://github.com/BandarLabs/open-skills), enabling sandboxed Python code execution, Claude-compatible skills, and web scraping directly from OpenWebUI.

## Features

| Tool | Description |
|------|-------------|
| `execute_python_code` | Execute Python in a sandboxed Jupyter kernel (numpy, pandas, matplotlib, fpdf2, reportlab, etc.) |
| `list_skills` | List all available skills (PDF manipulation, image processing, document creation) |
| `get_skill_info` | Get detailed documentation for a specific skill |
| `get_skill_file` | Retrieve any file from a skill's directory (scripts, examples, etc.) |
| `navigate_and_get_all_visible_text` | Scrape text content from any webpage using Playwright with Xvfb |

## Installation

### Option 1: Manual Installation (Recommended)

1. In OpenWebUI, go to **Workspace** → **Tools** → **+** (Add Tool)
2. Copy the entire contents of `open_skills_tool.py` and paste it into the tool editor
3. Click **Save**
4. Enable the tool for your desired models

### Option 2: Database Script

Use the provided script to add the tool directly to your database:
```bash
python add_tool_to_db.py /path/to/webui.db
```

## Prerequisites

The Open-Skills MCP server must be running. See the [main repository](https://github.com/BandarLabs/open-skills) for installation:

```bash
# Local installation (Mac with Apple Silicon)
git clone https://github.com/BandarLabs/open-skills.git
cd open-skills
chmod +x install.sh
./install.sh
```

### Docker Deployment

For server/VPS deployments:

```bash
# Build the image
cd open-skills
docker build -t open-skills:local .

# Run the container
docker run -d \
  --name open-skills \
  --network your-network \
  -p 8222:8222 \
  -v $(pwd)/uploads:/app/uploads \
  -e FASTMCP_HOST=0.0.0.0 \
  -e FASTMCP_PORT=8222 \
  -e DISPLAY=:99 \
  --restart unless-stopped \
  open-skills:local
```

### Initial Setup (Docker)

```bash
# Copy skills to uploads directory
cp -r skills/ uploads/skills/

# Create outputs directory for generated files
mkdir -p uploads/outputs
chmod 777 uploads/outputs
```

## Configuration

Configure via **Valves** in OpenWebUI settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `mcp_server_url` | `http://open-skills.local:8222/mcp` | URL of the MCP server |
| `timeout_seconds` | `600` | Timeout for code execution (10 minutes) |

### Environment-Specific URLs

| Environment | URL |
|-------------|-----|
| Apple Container (local) | `http://open-skills.local:8222/mcp` |
| Docker (localhost) | `http://localhost:8222/mcp` |
| Docker (internal network) | `http://open-skills:8222/mcp` |

## File Downloads

Generated files (PDFs, images, etc.) are saved to `/app/uploads/outputs/` inside the container.

**Host path**: `~/.open-skills/assets/outputs/` (local) or your mounted volume path (Docker)

For secure file serving in production, consider:
- Using an authenticated proxy route in your frontend
- Serving files through your existing web server with auth
- Using pre-signed URLs

## Example Prompts

- *"Run Python code to calculate the first 20 Fibonacci numbers"*
- *"Create a bar chart from this data and save it as a PDF"*
- *"Search GitHub for popular AI agent repos and create a summary PDF"*
- *"Extract text from this webpage: https://example.com"*

## Native Tool Calling for Custom Frontends

If you're using a **custom frontend** with OpenWebUI's API (not the native OWUI interface), tool calls may return blank responses. This happens because native function calling requires WebSocket metadata that custom frontends don't provide.

### Applying the Patches

The `patches/` directory contains fixes that enable synchronous tool execution:

```bash
# Copy and apply patches to your OpenWebUI backend
scp patches/*.py user@your-server:/tmp/
docker cp /tmp/apply_patch.py owui-backend:/tmp/
docker cp /tmp/apply_streaming_patch.py owui-backend:/tmp/
docker cp /tmp/fix_tool_calls_type.py owui-backend:/tmp/
docker cp /tmp/fix_streaming_section.py owui-backend:/tmp/

# Run patches
docker exec owui-backend python3 /tmp/apply_patch.py
docker exec owui-backend python3 /tmp/apply_streaming_patch.py
docker exec owui-backend python3 /tmp/fix_tool_calls_type.py
docker exec owui-backend python3 /tmp/fix_streaming_section.py

# Restart
docker restart owui-backend
```

See `patches/README.md` for full details.

## Troubleshooting

### "Cannot connect to MCP server"
- Verify the server is running: `docker logs open-skills` or `container logs open-skills`
- Check the URL in Valves matches your setup
- Ensure network connectivity between OpenWebUI and Open-Skills containers

### "ModuleNotFoundError"
- Some packages may need to be installed: `docker exec open-skills pip install <package>`
- Rebuild the image for persistence

### "No skills found"
- Ensure skills are copied to the uploads directory
- Restart the container: `docker restart open-skills`

### "Blank response when using tools" (Custom Frontends)
- Apply the native tool calling patches (see above)
- Ensure function calling is set to "native" in model settings
- Check backend logs for `SYNC_TOOL_PATCH` messages

## License

MIT - See the main [Open-Skills repository](https://github.com/BandarLabs/open-skills) for details.

