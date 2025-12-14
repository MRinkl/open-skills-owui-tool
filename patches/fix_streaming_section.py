#!/usr/bin/env python3
"""Fix the streaming section properly"""

filepath = "/app/backend/open_webui/utils/middleware.py"

with open(filepath, "r") as f:
    content = f.read()

# The broken code
old_code = '''            # Make follow-up LLM call
            try:
                # Ensure each tool call has required 'type' field for OpenRouter/OpenAI
                formatted_tool_calls = []
                for tc in tool_calls:
                formatted_tool_calls.append({
                "id": tc.get("id", ""),
                "type": "function",
                "function": tc.get("function", {})
                })
                assistant_msg = {"role": "assistant", "content": collected_content or "", "tool_calls": formatted_tool_calls}
                new_messages = list(form_data.get("messages", [])) + [assistant_msg] + tool_results'''

# Fixed code with proper indentation
new_code = '''            # Make follow-up LLM call
            try:
                # Ensure each tool call has required 'type' field for OpenRouter/OpenAI
                formatted_tool_calls = []
                for tc in tool_calls:
                    formatted_tool_calls.append({
                        "id": tc.get("id", ""),
                        "type": "function",
                        "function": tc.get("function", {})
                    })
                assistant_msg = {"role": "assistant", "content": collected_content or "", "tool_calls": formatted_tool_calls}
                new_messages = list(form_data.get("messages", [])) + [assistant_msg] + tool_results'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(filepath, "w") as f:
        f.write(content)
    print("Fixed streaming section indentation")
else:
    print("Pattern not found")

# Verify syntax
import subprocess
result = subprocess.run(["python3", "-m", "py_compile", filepath], capture_output=True, text=True)
if result.returncode == 0:
    print("Syntax OK!")
else:
    print(f"Syntax error: {result.stderr}")

