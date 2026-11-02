#!/bin/zsh
# Permission check for the launcher app: can a job started through it read and write the output folder?
# Run: open -W -a "$HOME/Applications/Agent Job Runner.app" --args "$PWD/launchd/check-access.sh"; tail -3 ~/Library/Logs/linkedin-access-check.log
LOG=${1:-$HOME/Library/Logs/linkedin-access-check.log}
cd "${0:A:h}/.." || exit 1
{
  echo "--- $(date '+%Y-%m-%d %H:%M:%S')"
  /usr/bin/python3 - <<'PY'
import os, sys
sys.path.insert(0, os.getcwd())
import config
out = config.output_dir()
try:
    probe = os.path.join(out, ".access-check")
    with open(probe, "w") as f:
        f.write("ok\n")
    os.remove(probe)
    names = os.listdir(out)
    print(f"OK: wrote and removed a test file, and listed {len(names)} entries in the output folder")
except OSError as e:
    print(f"FAILED: {type(e).__name__}: {e.strerror}")
PY
} >> "$LOG" 2>&1
