#!/usr/bin/env python3
"""
Patch for OWUI middleware to enable synchronous tool execution without event_emitter.

This patch modifies the non-event_emitter code path to:
1. Detect tool_calls in the LLM response
2. Execute tools synchronously
3. Make a follow-up LLM call with tool results
4. Return the final response

Usage:
    python3 sync_tool_execution_patch.py /path/to/middleware.py
"""

import sys
import re

PATCH_MARKER = "# SYNC_TOOL_EXECUTION_PATCH_v1"

# The code to insert after "return response" in the else branch (around line 1837)
SYNC_TOOL_CODE = '''
            # SYNC_TOOL_EXECUTION_PATCH_v1 - Execute tools without event_emitter
            # Check if this is a non-streaming response with tool_calls
            response_data = None
            if isinstance(response, dict):
                response_data = response
            elif isinstance(response, JSONResponse) and hasattr(response, 'body'):
                try:
                    response_data = json.loads(response.body.decode("utf-8", "replace"))
                except:
                    pass

            if response_data:
                choices = response_data.get("choices", [])
                if choices and choices[0].get("message", {}).get("tool_calls"):
                    tool_calls = choices[0]["message"]["tool_calls"]
                    tools = metadata.get("tools", {})
                    
                    log.info(f"SYNC_TOOL_EXEC: Processing {len(tool_calls)} tool calls without event_emitter")
                    
                    tool_results = []
                    for tc in tool_calls:
                        tool_call_id = tc.get("id", "")
                        func_name = tc.get("function", {}).get("name", "")
                        func_args_str = tc.get("function", {}).get("arguments", "{}")
                        
                        try:
                            func_params = json.loads(func_args_str)
                        except:
                            func_params = {}
                        
                        result = f"Tool {func_name} not found"
                        if func_name in tools:
                            tool = tools[func_name]
                            tool_callable = tool.get("callable")
                            if tool_callable:
                                try:
                                    import asyncio
                                    loop = asyncio.get_event_loop()
                                    if asyncio.iscoroutinefunction(tool_callable):
                                        result = loop.run_until_complete(tool_callable(**func_params))
                                    else:
                                        result = tool_callable(**func_params)
                                    log.info(f"SYNC_TOOL_EXEC: Tool {func_name} executed successfully")
                                except Exception as e:
                                    result = f"Error executing tool: {str(e)}"
                                    log.error(f"SYNC_TOOL_EXEC: Tool {func_name} error: {e}")
                        
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": str(result) if result else ""
                        })
                    
                    # Make follow-up LLM call with tool results
                    if tool_results:
                        try:
                            new_messages = form_data.get("messages", []) + [
                                choices[0]["message"],  # Assistant message with tool_calls
                                *tool_results  # Tool results
                            ]
                            new_form_data = {
                                **form_data,
                                "messages": new_messages,
                                "stream": False,
                            }
                            # Remove tools to prevent infinite loop
                            new_form_data.pop("tools", None)
                            new_form_data.pop("tool_ids", None)
                            
                            final_response = await generate_chat_completion(request, new_form_data, user)
                            if isinstance(final_response, JSONResponse):
                                return final_response
                            elif isinstance(final_response, dict):
                                return JSONResponse(content=final_response)
                        except Exception as e:
                            log.error(f"SYNC_TOOL_EXEC: Follow-up LLM call failed: {e}")
'''

def patch_middleware(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if PATCH_MARKER in content:
        print(f"Patch already applied (found {PATCH_MARKER})")
        return False
    
    # Find the target location: the "return response" in the else branch
    # This is after "if events and isinstance(events, list)..."
    pattern = r'(            return response\n\n    # Non standard response)'
    
    replacement = SYNC_TOOL_CODE + r'\n\n            return response\n\n    # Non standard response'
    
    new_content, count = re.subn(pattern, replacement, content, count=1)
    
    if count == 0:
        print("Could not find target location for patch")
        return False
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"Patch applied successfully to {filepath}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 sync_tool_execution_patch.py /path/to/middleware.py")
        sys.exit(1)
    
    patch_middleware(sys.argv[1])

