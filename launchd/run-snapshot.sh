#!/bin/zsh
# The weekly full snapshot pull, as the launcher app runs it. Optional $1 = log file.
LOG=${1:-$HOME/Library/Logs/linkedin-snapshot.log}
cd "${0:A:h}/.." || exit 1
{ echo "--- $(date '+%Y-%m-%d %H:%M:%S')"; /usr/bin/python3 pull_linkedin.py; } >> "$LOG" 2>&1
