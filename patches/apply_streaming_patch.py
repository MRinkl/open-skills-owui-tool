#!/usr/bin/env python3
"""Apply streaming tool execution patch to OWUI middleware."""

filepath = "/app/backend/open_webui/utils/middleware.py"

with open(filepath, "r") as f:
    content = f.read()

if "SYNC_STREAM_TOOL_PATCH_V1" in content:
    print("Streaming patch already applied")
    exit(0)

# Find the streaming passthrough section (after the if event_emitter check)
# We need to add handling for streaming responses without event_emitter

old_code = '''    _stream_dbg.warning("STREAMING_CHECK: IS a streaming response, continuing...")

    oauth_token = None'''

new_code = '''    _stream_dbg.warning("STREAMING_CHECK: IS a streaming response, continuing...")

    # SYNC_STREAM_TOOL_PATCH_V1: Handle streaming with tool calls but no event_emitter
    if not event_emitter:
        log.warning("SYNC_STREAM_TOOL_PATCH: No event_emitter, collecting stream for tool calls")
        tools = metadata.get("tools", {})
        
        async def collect_and_process_stream():
            collected_content = ""
            collected_tool_calls = []
            current_tool_call = {}
            
            async for chunk in response.body_iterator:
                if isinstance(chunk, bytes):
                    chunk = chunk.decode("utf-8", errors="replace")
                
                for line in chunk.strip().split("\\n"):
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            continue
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                if "content" in delta and delta["content"]:
                                    collected_content += delta["content"]
                                if "tool_calls" in delta:
                                    for tc in delta["tool_calls"]:
                                        idx = tc.get("index", 0)
                                        if idx >= len(collected_tool_calls):
                                            collected_tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                                        if "id" in tc:
                                            collected_tool_calls[idx]["id"] = tc["id"]
                                        if "function" in tc:
                                            if "name" in tc["function"]:
                                                collected_tool_calls[idx]["function"]["name"] = tc["function"]["name"]
                                            if "arguments" in tc["function"]:
                                                collected_tool_calls[idx]["function"]["arguments"] += tc["function"]["arguments"]
                        except json.JSONDecodeError:
                            pass
            
            return collected_content, collected_tool_calls
        
        collected_content, tool_calls = await collect_and_process_stream()
        
        if tool_calls:
            log.warning(f"SYNC_STREAM_TOOL_PATCH: Found {len(tool_calls)} tool calls in stream")
            tool_results = []
            
            for tc in tool_calls:
                tc_id = tc.get("id", "")
                fn_name = tc["function"]["name"]
                fn_args_str = tc["function"]["arguments"]
                
                try:
                    fn_params = json.loads(fn_args_str)
                except:
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
                            log.warning(f"SYNC_STREAM_TOOL_PATCH: Tool {fn_name} executed OK")
                        except Exception as e:
                            result = f"Error: {str(e)}"
                            log.error(f"SYNC_STREAM_TOOL_PATCH: Tool {fn_name} error: {e}")
                
                tool_results.append({"role": "tool", "tool_call_id": tc_id, "content": str(result) if result else ""})
            
            # Make follow-up LLM call
            try:
                assistant_msg = {"role": "assistant", "content": collected_content or "", "tool_calls": tool_calls}
                new_messages = list(form_data.get("messages", [])) + [assistant_msg] + tool_results
                new_form_data = {**form_data, "messages": new_messages, "stream": True}
                new_form_data.pop("tools", None)
                new_form_data.pop("tool_ids", None)
                
                log.warning("SYNC_STREAM_TOOL_PATCH: Making follow-up streaming LLM call")
                return await generate_chat_completion(request, new_form_data, user)
            except Exception as e:
                log.error(f"SYNC_STREAM_TOOL_PATCH: Follow-up failed: {e}")
        
        # No tool calls or failed - return simple streaming response with collected content
        if collected_content:
            async def simple_stream():
                yield f"data: {json.dumps({'choices': [{'delta': {'content': collected_content}}]})}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(simple_stream(), media_type="text/event-stream")
        
        return response

    oauth_token = None'''

if old_code not in content:
    print("ERROR: Target code not found for streaming patch")
    exit(1)

new_content = content.replace(old_code, new_code, 1)

with open(filepath, "w") as f:
    f.write(new_content)

print("Streaming patch applied successfully!")

