#!/usr/bin/env python3
"""Apply sync tool execution patch to OWUI middleware."""

filepath = "/app/backend/open_webui/utils/middleware.py"

with open(filepath, "r") as f:
    content = f.read()

if "SYNC_TOOL_PATCH_V1" in content:
    print("Already patched")
    exit(0)

old_code = '''        else:
            if events and isinstance(events, list) and isinstance(response, dict):
                extra_response = {}
                for event in events:
                    if isinstance(event, dict):
                        extra_response.update(event)
                    else:
                        extra_response[event] = True

                response = {
                    **extra_response,
                    **response,
                }

            return response

    # Non standard response'''

new_code = '''        else:
            # SYNC_TOOL_PATCH_V1: Handle tool calls without event_emitter
            response_data = None
            if isinstance(response, dict):
                response_data = response
            elif isinstance(response, JSONResponse) and hasattr(response, "body"):
                try:
                    response_data = json.loads(response.body.decode("utf-8", "replace"))
                except Exception:
                    pass

            if response_data:
                choices = response_data.get("choices", [])
                if choices and choices[0].get("message", {}).get("tool_calls"):
                    tool_calls_list = choices[0]["message"]["tool_calls"]
                    tools = metadata.get("tools", {})
                    log.warning(f"SYNC_TOOL_PATCH: Processing {len(tool_calls_list)} tool calls")

                    tool_results = []
                    for tc in tool_calls_list:
                        tc_id = tc.get("id", "")
                        fn_name = tc.get("function", {}).get("name", "")
                        fn_args_str = tc.get("function", {}).get("arguments", "{}")

                        try:
                            fn_params = json.loads(fn_args_str)
                        except Exception:
                            try:
                                import ast
                                fn_params = ast.literal_eval(fn_args_str)
                            except Exception:
                                fn_params = {}

                        result = f"Tool {fn_name} not found"
                        if fn_name in tools:
                            tool = tools[fn_name]
                            tool_callable = tool.get("callable")
                            if tool_callable:
                                try:
                                    import asyncio
                                    if asyncio.iscoroutinefunction(tool_callable):
                                        result = await tool_callable(**fn_params)
                                    else:
                                        result = tool_callable(**fn_params)
                                    log.warning(f"SYNC_TOOL_PATCH: Tool {fn_name} OK")
                                except Exception as e:
                                    result = f"Error: {str(e)}"
                                    log.error(f"SYNC_TOOL_PATCH: {fn_name} error: {e}")

                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "content": str(result) if result else ""
                        })

                    if tool_results:
                        try:
                            assistant_msg = choices[0]["message"].copy()
                            if assistant_msg.get("content") is None:
                                assistant_msg["content"] = ""
                            new_messages = list(form_data.get("messages", [])) + [assistant_msg] + tool_results
                            new_form_data = {**form_data, "messages": new_messages, "stream": False}
                            new_form_data.pop("tools", None)
                            new_form_data.pop("tool_ids", None)

                            log.warning(f"SYNC_TOOL_PATCH: Follow-up LLM call")
                            final_response = await generate_chat_completion(request, new_form_data, user)

                            if isinstance(final_response, StreamingResponse):
                                return final_response
                            elif isinstance(final_response, JSONResponse):
                                return final_response
                            elif isinstance(final_response, dict):
                                return JSONResponse(content=final_response)
                        except Exception as e:
                            log.error(f"SYNC_TOOL_PATCH: Follow-up failed: {e}")

            if events and isinstance(events, list) and isinstance(response, dict):
                extra_response = {}
                for event in events:
                    if isinstance(event, dict):
                        extra_response.update(event)
                    else:
                        extra_response[event] = True

                response = {
                    **extra_response,
                    **response,
                }

            return response

    # Non standard response'''

if old_code not in content:
    print("ERROR: Target code not found")
    exit(1)

new_content = content.replace(old_code, new_code, 1)

with open(filepath, "w") as f:
    f.write(new_content)

print("Patch applied successfully!")

