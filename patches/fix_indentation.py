#!/usr/bin/env python3
"""Fix indentation in middleware.py"""

filepath = "/app/backend/open_webui/utils/middleware.py"

with open(filepath, "r") as f:
    lines = f.readlines()

# Find and fix the streaming patch indentation issue
i = 0
while i < len(lines):
    if "# Ensure each tool call has required 'type' field for OpenRouter/OpenAI" in lines[i]:
        # Found the comment, check if next lines have wrong indentation
        # They should all be at the same level as the try block (16 spaces)
        base_indent = "                "  # 16 spaces
        
        # Fix the lines from the comment until assistant_msg
        j = i
        while j < len(lines) and "new_messages = list(" not in lines[j]:
            line = lines[j]
            stripped = line.lstrip()
            if stripped and not stripped.startswith("#"):
                # Calculate current indent
                current_indent = len(line) - len(stripped)
                if current_indent > 16:
                    # Over-indented, fix it
                    lines[j] = base_indent + stripped
            j += 1
        print(f"Fixed indentation starting at line {i+1}")
        break
    i += 1

with open(filepath, "w") as f:
    f.writelines(lines)

print("Done!")

