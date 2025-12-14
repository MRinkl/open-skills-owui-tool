#!/usr/bin/env python3
"""Fix tool_calls format to include required 'type' field for OpenRouter compatibility."""

filepath = "/app/backend/open_webui/utils/middleware.py"

with open(filepath, "r") as f:
    content = f.read()

# Fix 1: Streaming patch - tool_calls needs type field
old_streaming = 'assistant_msg = {"role": "assistant", "content": collected_content or "", "tool_calls": tool_calls}'

new_streaming = '''# Ensure each tool call has required 'type' field for OpenRouter/OpenAI
                    formatted_tool_calls = []
                    for tc in tool_calls:
                        formatted_tool_calls.append({
                            "id": tc.get("id", ""),
                            "type": "function",
                            "function": tc.get("function", {})
                        })
                    assistant_msg = {"role": "assistant", "content": collected_content or "", "tool_calls": formatted_tool_calls}'''

if old_streaming in content:
    content = content.replace(old_streaming, new_streaming)
    print("Fixed streaming patch tool_calls format")
else:
    print("Streaming patch pattern not found")

# Fix 2: Non-streaming patch - also needs type field  
old_nonstream = 'assistant_msg = choices[0]["message"].copy()'

new_nonstream = '''assistant_msg = choices[0]["message"].copy()
                            # Ensure tool_calls have required 'type' field
                            if "tool_calls" in assistant_msg:
                                for tc in assistant_msg["tool_calls"]:
                                    if "type" not in tc:
                                        tc["type"] = "function"'''

if old_nonstream in content and "Ensure tool_calls have required" not in content:
    content = content.replace(old_nonstream, new_nonstream)
    print("Fixed non-streaming patch tool_calls format")
else:
    print("Non-streaming patch already fixed or pattern not found")

with open(filepath, "w") as f:
    f.write(content)

print("Done!")

