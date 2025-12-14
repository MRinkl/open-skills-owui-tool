# Open Skills Tool for OpenWebUI

An OpenWebUI tool that enables **sandboxed Python code execution**, **document generation**, and **web scraping** through the [Open-Skills MCP server](https://github.com/BandarLabs/open-skills).

## What It Does

| Capability | Description |
|------------|-------------|
| **Code Execution** | Run Python in a sandboxed Jupyter kernel with 50+ packages (numpy, pandas, matplotlib, PIL, fpdf2, reportlab, etc.) |
| **Document Generation** | Create PDFs, spreadsheets, presentations, and images on-the-fly |
| **Web Scraping** | Extract text from any webpage using Playwright |
| **Skills Library** | Access Claude-compatible skills for specialized tasks |

---

## Installation

### Step 1: Install the Tool in OpenWebUI

1. Go to **Workspace** → **Tools** → **+** (Add Tool)
2. Copy the contents of [`open_skills_tool.py`](open_skills_tool.py) into the editor
3. Click **Save**

### Step 2: Enable for Your Model

1. Go to **Workspace** → **Models** → Select your model
2. Under **Tools**, enable **Open Skills**
3. Set **Function Calling** to `Native` (recommended) or `Default`

### Step 3: Configure the MCP Server URL

1. Click the **gear icon** next to the tool to open Valves
2. Set `mcp_server_url` to your Open-Skills server:
   - Docker (same network): `http://open-skills:8222/mcp`
   - Docker (localhost): `http://localhost:8222/mcp`
   - Mac local: `http://open-skills.local:8222/mcp`

---

## Prerequisites

You need the **Open-Skills MCP server** running. Quick setup:

```bash
# Clone and run
git clone https://github.com/BandarLabs/open-skills.git
cd open-skills
docker build -t open-skills:local .
docker run -d --name open-skills -p 8222:8222 \
  -v $(pwd)/uploads:/app/uploads \
  -e FASTMCP_HOST=0.0.0.0 \
  open-skills:local

# Initialize skills and outputs
cp -r skills/ uploads/skills/
mkdir -p uploads/outputs && chmod 777 uploads/outputs
```

See the [main repository](https://github.com/BandarLabs/open-skills) for detailed installation options.

---

## Usage Examples

| Prompt | What Happens |
|--------|--------------|
| *"Calculate 15 * 23 using Python"* | Executes code, returns `345` |
| *"Create a PDF with a summary of quantum computing"* | Generates PDF, returns download link |
| *"Scrape the main content from https://example.com"* | Extracts and returns page text |
| *"List available skills"* | Shows all installed skills |

### File Downloads

Generated files are saved to `/app/uploads/outputs/` and accessible via:
```
/api/files/<filename>
```

---

## Native Tool Calling Patches (For Custom Frontends)

If you're using a **custom frontend** (not the native OpenWebUI interface), tool calls may return blank responses. This is because OpenWebUI's native function calling requires WebSocket metadata that custom frontends don't provide.

### The Fix

Apply these patches to your OpenWebUI backend container:

```bash
# 1. Copy patches to server
scp patches/*.py user@your-server:/tmp/

# 2. Copy into container
docker cp /tmp/apply_patch.py owui-backend:/tmp/
docker cp /tmp/apply_streaming_patch.py owui-backend:/tmp/
docker cp /tmp/fix_tool_calls_type.py owui-backend:/tmp/
docker cp /tmp/fix_streaming_section.py owui-backend:/tmp/

# 3. Apply patches
docker exec owui-backend python3 /tmp/apply_patch.py
docker exec owui-backend python3 /tmp/apply_streaming_patch.py
docker exec owui-backend python3 /tmp/fix_tool_calls_type.py
docker exec owui-backend python3 /tmp/fix_streaming_section.py

# 4. Restart backend
docker restart owui-backend
```

### Verify Patches Applied

```bash
docker exec owui-backend grep -n "SYNC_TOOL_PATCH" \
  /app/backend/open_webui/utils/middleware.py
```

Expected output shows line numbers where patches are active.

### What the Patches Do

1. **Detect** tool calls in LLM responses (streaming and non-streaming)
2. **Execute** tools synchronously without requiring WebSocket
3. **Format** tool calls with required `type: "function"` field for OpenRouter
4. **Make follow-up LLM call** with results and return final response

> ⚠️ **Note:** Patches are not persistent across container rebuilds. Add to your deployment pipeline for persistence.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot connect to MCP server" | Check server is running: `docker logs open-skills` |
| "ModuleNotFoundError" | Install package: `docker exec open-skills pip install <pkg>` |
| Blank response (custom frontend) | Apply native tool calling patches (see above) |
| Tool not appearing | Ensure tool is enabled for your model |

---

## License

MIT - Part of the [Open-Skills](https://github.com/BandarLabs/open-skills) project.

