---
name: set-mode
description: "Set VIBESAFE_ENV for subsequent Vibesafe commands (dev|prod)."
arguments:
  - name: env
    description: "Mode to set (dev or prod)"
    required: true
---

Set the Vibesafe mode for this session by exporting `VIBESAFE_ENV`, then report the new value.

Steps (run in order):
1) `export VIBESAFE_ENV="{{ env }}"`  
2) `echo "VIBESAFE_ENV=$VIBESAFE_ENV"`  

Examples:
- `/vibesafe:set-mode dev`
- `/vibesafe:set-mode prod`
