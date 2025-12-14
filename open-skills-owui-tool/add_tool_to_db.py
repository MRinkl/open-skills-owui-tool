#!/usr/bin/env python3
"""
Script to add the Open Skills tool to an OpenWebUI SQLite database.
This makes the tool pre-installed when deploying from the golden template.

Usage:
    python add_tool_to_db.py /path/to/webui.db [admin_user_id]

If admin_user_id is not provided, it will use the first admin user found in the database.
"""

import sqlite3
import json
import sys
import time
from pathlib import Path

# Tool specifications for OpenWebUI
TOOL_SPECS = [
    {
        "name": "execute_python_code",
        "description": "Execute Python code in a sandboxed Jupyter kernel with full package support. The execution environment includes: numpy, pandas, matplotlib, PIL/Pillow, PyPDF2, python-docx, openpyxl, requests, and many other common packages. Files can be read from and written to /app/uploads/outputs/ which maps to the configured outputs directory on the host.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The Python code to execute as a string"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "list_skills",
        "description": "List all available skills in the Open-Skills system. Skills are pre-packaged tools for specialized tasks like PDF manipulation, image processing, document creation (DOCX, XLSX, PPTX), and more.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_skill_info",
        "description": "Get detailed documentation for a specific skill. Use list_skills() first to see available skills, then use this to get full documentation including usage instructions and examples.",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "The name of the skill (e.g., 'pdf-text-replace', 'image-crop-rotate')"
                }
            },
            "required": ["skill_name"]
        }
    },
    {
        "name": "get_skill_file",
        "description": "Get a specific file from a skill's directory. Some skills include additional documentation files like EXAMPLES.md, API.md, or helper scripts.",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "The name of the skill (e.g., 'pdf-text-replace')"
                },
                "filename": {
                    "type": "string",
                    "description": "The file to retrieve (e.g., 'EXAMPLES.md', 'scripts/helper.py')"
                }
            },
            "required": ["skill_name", "filename"]
        }
    },
    {
        "name": "navigate_and_get_all_visible_text",
        "description": "Scrape all visible text from a webpage using Playwright. This tool navigates to the specified URL and extracts all visible text, which can then be used for analysis, summarization, or data extraction.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the webpage to scrape"
                }
            },
            "required": ["url"]
        }
    }
]

TOOL_META = {
    "description": "Execute Python code, manage Claude-compatible skills, and scrape web content using the Open-Skills MCP server. Provides sandboxed code execution, access to document processing skills (PDF, DOCX, XLSX, images), and web scraping capabilities.",
    "manifest": {
        "title": "Open Skills",
        "author": "BandarLabs",
        "author_url": "https://github.com/BandarLabs/open-skills",
        "version": "1.0.0",
        "license": "MIT"
    }
}


def get_tool_content():
    """Read the tool Python file content."""
    tool_file = Path(__file__).parent / "open_skills_tool.py"
    if tool_file.exists():
        return tool_file.read_text()
    else:
        raise FileNotFoundError(f"Tool file not found: {tool_file}")


def get_admin_user_id(conn):
    """Get the first admin user ID from the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM user WHERE role = 'admin' LIMIT 1")
    result = cursor.fetchone()
    if result:
        return result[0]
    # Fallback: get any user
    cursor.execute("SELECT id FROM user LIMIT 1")
    result = cursor.fetchone()
    return result[0] if result else None


def add_open_skills_tool(db_path: str, user_id: str = None):
    """Add the Open Skills tool to the database."""
    conn = sqlite3.connect(db_path)

    try:
        if not user_id:
            user_id = get_admin_user_id(conn)
            if not user_id:
                print("Error: No users found in database")
                return False

        tool_content = get_tool_content()
        current_time = int(time.time())

        cursor = conn.cursor()

        # Check if tool already exists
        cursor.execute("SELECT id FROM tool WHERE id = 'open_skills'")
        if cursor.fetchone():
            print("Tool 'open_skills' already exists. Updating...")
            cursor.execute("""
                UPDATE tool SET
                    content = ?,
                    specs = ?,
                    meta = ?,
                    updated_at = ?
                WHERE id = 'open_skills'
            """, (
                tool_content,
                json.dumps(TOOL_SPECS),
                json.dumps(TOOL_META),
                current_time
            ))
        else:
            print("Adding new tool 'open_skills'...")
            cursor.execute("""
                INSERT INTO tool (id, user_id, name, content, specs, meta, created_at, updated_at, valves, access_control)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "open_skills",
                user_id,
                "Open Skills",
                tool_content,
                json.dumps(TOOL_SPECS),
                json.dumps(TOOL_META),
                current_time,
                current_time,
                None,
                None
            ))

        conn.commit()
        print(f"✅ Open Skills tool added successfully!")
        print(f"   User ID: {user_id}")
        print(f"   Tool ID: open_skills")
        return True

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_tool_to_db.py /path/to/webui.db [admin_user_id]")
        sys.exit(1)

    db_path = sys.argv[1]
    user_id = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        sys.exit(1)

    success = add_open_skills_tool(db_path, user_id)
    sys.exit(0 if success else 1)

