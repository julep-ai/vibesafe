---
name: init
description: "Initialize the Vibesafe plugin session: report mode, list commands, and verify MCP connectivity."
arguments: []
---

Run a quick readiness check:
- Show current mode (`VIBESAFE_ENV` or config default)
- List available Vibesafe commands
- Confirm MCP server connectivity
- Ensure vibesafe.toml exists with minimal defaults

Example:
- `/vibesafe:init`

Steps:
1) `echo "VIBESAFE_ENV=${VIBESAFE_ENV:-<unset>}"`  
2) `if [ -f .vibesafe/mode ]; then echo ".vibesafe/mode=$(cat .vibesafe/mode)"; else echo ".vibesafe/mode=<missing>"; fi`
3) `if [ ! -f vibesafe.toml ]; then cat > vibesafe.toml <<'EOF'\n[project]\npython = ">=3.12"\nenv = "dev"\n\n[provider.default]\nkind = "openai-compatible"\nmodel = "gpt-5-mini"\nseed = 42\nbase_url = "https://api.openai.com/v1"\napi_key_env = "OPENAI_API_KEY"\n\n[paths]\ncheckpoints = ".vibesafe/checkpoints"\ncache = ".vibesafe/cache"\nindex = ".vibesafe/index.toml"\n\n[sandbox]\nenabled = false\ntimeout = 10\nmemory_mb = 256\nEOF\nfi`  
4) `vibesafe status || true`  # harmless status check  
5) `echo "Commands: scan, compile, test, save, diff, status, mcp, set-mode, get-mode, init"`  
