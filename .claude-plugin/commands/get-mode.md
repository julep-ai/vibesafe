---
name: get-mode
description: "Show the current VIBESAFE_ENV (mode) visible to this session."
arguments: []
---

Report the Vibesafe mode for this session and the persisted mode file.

Steps:
1) `echo "VIBESAFE_ENV=${VIBESAFE_ENV:-<unset>}"`  
2) `if [ -f .vibesafe/mode ]; then echo ".vibesafe/mode=$(cat .vibesafe/mode)"; else echo ".vibesafe/mode=<missing>"; fi`  
3) Note that precedence is env > .vibesafe/mode > vibesafe.toml default.

Example:
- `/vibesafe:get-mode`
