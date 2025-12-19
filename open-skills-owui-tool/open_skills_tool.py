"""
title: Open Skills
author: BandarLabs
author_url: https://github.com/BandarLabs/open-skills
description: Execute Python code, manage skills, and scrape web content using the Open-Skills MCP server. Provides sandboxed code execution via Jupyter kernels, access to Claude-compatible skills for document processing (PDF, DOCX, XLSX, images), and web scraping capabilities.
required_open_webui_version: 0.4.0
requirements: httpx, mcp
version: 1.2.2
licence: MIT
"""

import asyncio
from typing import Optional, Callable, Awaitable
from pydantic import BaseModel, Field

# MCP client imports
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class Tools:
    def __init__(self):
        """Initialize the Open Skills tool."""
        self.valves = self.Valves()
        self.citation = False

    class Valves(BaseModel):
        mcp_server_url: str = Field(
            default="http://open-skills:8222/mcp",
            description="URL of the Open-Skills MCP server endpoint"
        )
        timeout_seconds: int = Field(
            default=600,
            description="Timeout for code execution in seconds (default: 10 minutes)"
        )

    async def _call_mcp_tool(
        self,
        tool_name: str,
        arguments: dict,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> str:
        """
        Call a tool on the MCP server using the official MCP client.
        """
        try:
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": f"Connecting to MCP server...", "done": False}
                })

            # Use the MCP streamable HTTP client
            async with streamablehttp_client(self.valves.mcp_server_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()

                    if __event_emitter__:
                        await __event_emitter__({
                            "type": "status",
                            "data": {"description": f"Executing {tool_name}...", "done": False}
                        })

                    # Call the tool
                    result = await asyncio.wait_for(
                        session.call_tool(tool_name, arguments),
                        timeout=self.valves.timeout_seconds
                    )

                    # Extract text content from result
                    if result.content:
                        text_parts = []
                        for item in result.content:
                            if hasattr(item, 'text'):
                                text_parts.append(item.text)
                        return "\n".join(text_parts) if text_parts else str(result)

                    return str(result)

        except asyncio.TimeoutError:
            return f"Error: Request timed out after {self.valves.timeout_seconds} seconds"
        except ConnectionError as e:
            return f"Error: Cannot connect to MCP server at {self.valves.mcp_server_url}. Is the Open-Skills container running? Details: {e}"
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": "Complete", "done": True}
                })

    async def execute_python_code(
        self,
        command: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> str:
        """
        Execute Python code in a sandboxed Jupyter kernel with full package support.

        The execution environment includes: numpy, pandas, matplotlib, PIL/Pillow,
        fpdf2, reportlab, PyPDF2, python-docx, openpyxl, requests, beautifulsoup4,
        and many other common packages.

        FILE OUTPUT INSTRUCTIONS (CRITICAL - follow exactly):
        1. Save files to: /app/uploads/outputs/<filename>
        2. Provide ONLY ONE download link using this EXACT format:
           **Download:** [filename.pdf](/api/files/filename.pdf)
        3. Use ONLY the relative path /api/files/filename - NO full URLs.

        PDF CREATION TIPS (avoid common errors):
        - Use ONLY ASCII characters. NO emojis, NO special dashes, NO unicode.
        - Use regular hyphen (-) not en-dash or non-breaking hyphen.
        - Use asterisk (*) instead of star emoji.
        - For reportlab, register fonts if you need unicode support.

        ASCII ART AND COMPLEX TEXT PATTERNS (CRITICAL):
        - FIRST compose your ASCII art as a simple Python variable BEFORE writing PDF code
        - Use a LIST of strings for each line, then join with newlines
        - Example pattern:
            art_lines = [
                "  ___  ",
                " |   | ",
                " |___| "
            ]
            ascii_art = "\n".join(art_lines)
        - NEVER use triple-quoted strings with complex escape sequences
        - Avoid backslashes in the art - use simple box-drawing: | - _ / \ + *
        - Keep art simple and test it works as valid Python first

        :param command: The Python code to execute as a string.
        :return: The output from code execution, including stdout and return values.
        """
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "Executing Python code in sandbox...", "done": False}
            })

        return await self._call_mcp_tool("execute_python_code", {"command": command}, __event_emitter__)

    async def list_skills(
        self,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> str:
        """
        List all available skills in the Open-Skills system.

        Skills are pre-packaged tools for specialized tasks like PDF manipulation,
        image processing, document creation (DOCX, XLSX, PPTX), and more.

        :return: A list of available skills organized by category (public/user).
        """
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "Listing available skills...", "done": False}
            })

        return await self._call_mcp_tool("list_skills", {}, __event_emitter__)

    async def get_skill_info(
        self,
        skill_name: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> str:
        """
        Get detailed documentation for a specific skill.

        Use list_skills() first to see available skills, then use this to get
        full documentation including usage instructions and examples.

        :param skill_name: The name of the skill (e.g., 'pdf-text-replace', 'image-crop-rotate').
        :return: The skill's SKILL.md documentation with usage instructions.
        """
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"Getting info for skill: {skill_name}...", "done": False}
            })

        return await self._call_mcp_tool("get_skill_info", {"skill_name": skill_name}, __event_emitter__)

    async def get_skill_file(
        self,
        skill_name: str,
        filename: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> str:
        """
        Get a specific file from a skill's directory.

        Some skills include additional documentation files like EXAMPLES.md, API.md,
        or helper scripts. Use this to retrieve those files.

        :param skill_name: The name of the skill (e.g., 'pdf-text-replace').
        :param filename: The file to retrieve (e.g., 'EXAMPLES.md', 'scripts/helper.py').
        :return: The content of the requested file.
        """
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"Getting {filename} from skill: {skill_name}...", "done": False}
            })

        return await self._call_mcp_tool(
            "get_skill_file",
            {"skill_name": skill_name, "filename": filename},
            __event_emitter__
        )

    async def navigate_and_get_all_visible_text(
        self,
        url: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> str:
        """
        Scrape all visible text from a webpage using Playwright.

        This tool navigates to the specified URL and extracts all visible text,
        which can then be used for analysis, summarization, or data extraction.

        :param url: The URL of the webpage to scrape.
        :return: All visible text content from the webpage.
        """
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"Scraping content from {url}...", "done": False}
            })

        return await self._call_mcp_tool(
            "navigate_and_get_all_visible_text",
            {"url": url},
            __event_emitter__
        )