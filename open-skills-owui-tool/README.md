# Open Skills Tool for OpenWebUI

> **Version 1.2.2** | [MIT License](LICENSE) | Part of [Open-Skills](https://github.com/BandarLabs/open-skills)

An OpenWebUI tool that enables **sandboxed Python code execution**, **document generation**, and **web scraping** through the [Open-Skills MCP server](https://github.com/BandarLabs/open-skills).

## Features

### 🐍 Sandboxed Python Execution
Execute Python code in isolated Jupyter kernels with full package support:
- **50+ pre-installed packages**: numpy, pandas, matplotlib, PIL/Pillow, fpdf2, reportlab, PyPDF2, python-docx, openpyxl, requests, beautifulsoup4, and more
- **Kernel pool management**: Automatic kernel allocation and cleanup for concurrent execution
- **File I/O support**: Read from and write to persistent storage
- **Timeout protection**: Configurable execution timeouts (default: 10 minutes)

### 📄 Document Generation
Create various document types on-the-fly:
- **PDF creation** with reportlab, fpdf2, or PyPDF2
- **Word documents** (.docx) with python-docx
- **Excel spreadsheets** (.xlsx) with openpyxl
- **Images** with PIL/Pillow and matplotlib
- **ASCII art** with guided string patterns (see tips below)

### 🌐 Web Scraping
Extract content from any webpage using Playwright:
- Headless browser automation
- JavaScript-rendered content extraction
- Full page text scraping

### 📚 Skills Library
Access Claude-compatible skills for specialized tasks:
- List available skills with `list_skills()`
- Get detailed documentation with `get_skill_info(skill_name)`
- Access skill files with `get_skill_file(skill_name, filename)`

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
| *"Create a PDF with ASCII art of a robot"* | Generates ASCII art PDF using list-of-strings pattern |
| *"Scrape the main content from https://example.com"* | Extracts and returns page text |
| *"List available skills"* | Shows all installed skills |

### File Downloads

Generated files are saved to `/app/uploads/outputs/` and accessible via:
```
/api/files/<filename>
```

---

## Tips for PDF and ASCII Art Creation

The tool includes built-in guidance for generating valid Python code. Key tips:

### PDF Creation
- Use **only ASCII characters** - no emojis, special dashes, or unicode
- Use regular hyphen (`-`) not en-dash or non-breaking hyphen
- Use asterisk (`*`) instead of star emoji

### ASCII Art (Critical)
To avoid syntax errors with complex text patterns:
- **Compose ASCII art as a list of strings** first, then join with newlines
- **Never use triple-quoted strings** with complex escape sequences

```python
# ✅ Correct pattern
art_lines = [
    "  ___  ",
    " |   | ",
    " |___| "
]
ascii_art = "\n".join(art_lines)

# ❌ Avoid this - can cause SyntaxError
ascii_art = """
  ___
 |   |
 |___|
"""
```

---

## Native Tool Calling for Custom Frontends

If you're using a **custom frontend** (not the native OpenWebUI interface), you may need to implement client-side tool execution. OpenWebUI's `/api/chat/completions` endpoint returns `finish_reason: "tool_calls"` but does not execute tools for external API clients.

### Option 1: Frontend Tool Execution Loop

Implement a tool execution loop in your frontend:
1. Detect `finish_reason: "tool_calls"` in the response
2. Execute tools via the MCP server directly
3. Send results back in a follow-up request
4. Repeat until `finish_reason: "stop"`

### Option 2: Apply Backend Patches

Apply patches to your OpenWebUI backend container for synchronous tool execution:

```bash
# Copy patches into container
docker cp patches/*.py owui-backend:/tmp/

# Apply patches
docker exec owui-backend python3 /tmp/apply_patch.py
docker exec owui-backend python3 /tmp/apply_streaming_patch.py
docker exec owui-backend python3 /tmp/fix_tool_calls_type.py
docker exec owui-backend python3 /tmp/fix_streaming_section.py

# Restart backend
docker restart owui-backend
```

> ⚠️ **Note:** Patches are not persistent across container rebuilds. Add to your deployment pipeline for persistence.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot connect to MCP server" | Check server is running: `docker logs open-skills` |
| "ModuleNotFoundError" | Install package: `docker exec open-skills pip install <pkg>` |
| SyntaxError with ASCII art | Use list-of-strings pattern (see tips above) |
| Blank response (custom frontend) | Implement frontend tool loop or apply patches |
| Tool not appearing | Ensure tool is enabled for your model |
| Timeout errors | Increase `timeout_seconds` in tool valves |

---

## Version History

| Version | Changes |
|---------|---------|
| **1.2.2** | Added ASCII art guidance, improved PDF creation tips |
| **1.2.1** | Added web scraping with Playwright |
| **1.2.0** | MCP client integration, kernel pool management |
| **1.1.0** | Skills library support |
| **1.0.0** | Initial release with code execution |

---

## License

MIT - Part of the [Open-Skills](https://github.com/BandarLabs/open-skills) project.
