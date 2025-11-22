---
name: set-mode
description: "Set VIBESAFE_ENV for subsequent Vibesafe commands (dev|prod)."
arguments:
  - name: env
    description: "Mode to set (dev or prod)"
    required: true
---

Set the Vibesafe mode persistently for this repo and session.

Steps (run in order):
1) `export VIBESAFE_ENV="{{ env }}"`  
2) `mkdir -p .vibesafe && printf "%s" "{{ env }}" > .vibesafe/mode`  
3) `echo "VIBESAFE_ENV=$VIBESAFE_ENV (persisted to .vibesafe/mode)"`  

Examples:
- `/vibesafe:set-mode dev`
- `/vibesafe:set-mode prod`
