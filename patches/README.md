# OWUI Native Tool Calling Patches

These patches enable **synchronous tool execution** in OpenWebUI when native function calling is used without WebSocket metadata.

## The Problem

OpenWebUI's native function calling requires `session_id`, `chat_id`, and `message_id` to create an `event_emitter` for tool call processing. Custom frontends or API clients that don't provide these fields receive unexecuted tool calls.

## The Solution

These patches add a fallback mechanism that:
1. **Detects** tool calls in LLM responses (both streaming and non-streaming)
2. **Executes** tools synchronously using their callable
3. **Formats** tool calls with required `type: "function"` field for OpenRouter/OpenAI compatibility
4. **Makes follow-up LLM call** with tool results
5. **Returns** the final response

## Patch Files

| File | Purpose |
|------|---------|
| `apply_patch.py` | Non-streaming tool execution without event_emitter |
| `apply_streaming_patch.py` | Streaming tool execution without event_emitter |
| `fix_tool_calls_type.py` | Adds required `type: "function"` field for OpenRouter |
| `fix_streaming_section.py` | Fixes indentation in streaming patch |

## Installation

Apply patches to a running OpenWebUI container:

```bash
# 1. Copy patch files to server
scp patches/*.py user@your-server:/tmp/

# 2. Apply to container
docker cp /tmp/apply_patch.py owui-backend:/tmp/
docker cp /tmp/apply_streaming_patch.py owui-backend:/tmp/
docker cp /tmp/fix_tool_calls_type.py owui-backend:/tmp/
docker cp /tmp/fix_streaming_section.py owui-backend:/tmp/

# 3. Run patches in order
docker exec owui-backend python3 /tmp/apply_patch.py
docker exec owui-backend python3 /tmp/apply_streaming_patch.py
docker exec owui-backend python3 /tmp/fix_tool_calls_type.py
docker exec owui-backend python3 /tmp/fix_streaming_section.py

# 4. Verify syntax
docker exec owui-backend python3 -m py_compile /app/backend/open_webui/utils/middleware.py

# 5. Restart backend
docker restart owui-backend
```

## Verification

After applying patches, check for these markers in middleware.py:
```bash
docker exec owui-backend grep -n "SYNC_TOOL_PATCH\|SYNC_STREAM_TOOL_PATCH" \
  /app/backend/open_webui/utils/middleware.py
```

Expected output:
```
1825:            # SYNC_TOOL_PATCH_V1: Handle tool calls without event_emitter
1928:    # SYNC_STREAM_TOOL_PATCH_V1: Handle streaming with tool calls
```

## Important Notes

- **Not persistent**: Patches are lost on container rebuild. Add to your OWUI golden template for persistence.
- **OpenRouter compatible**: Fixes the `type: "function"` field requirement
- **Works with custom frontends**: Enables tool calling for frontends that don't send WebSocket metadata

## License

MIT - Part of the [Open-Skills](https://github.com/BandarLabs/open-skills) project.

