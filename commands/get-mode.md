---
name: get-mode
description: "Show the current VIBESAFE_ENV (mode) visible to this session."
arguments: []
---

Report the Vibesafe mode for this session by reading `VIBESAFE_ENV` (falls back to config default if unset).

Steps:
1) `echo "VIBESAFE_ENV=${VIBESAFE_ENV:-<unset>}"`  
2) If unset, note that the config default (`project.env` in vibesafe.toml) will apply.

Example:
- `/vibesafe:get-mode`
