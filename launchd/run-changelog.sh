#!/bin/zsh
# The change-log job, as the launcher app runs it. Optional $1 = log file.
LOG=${1:-$HOME/Library/Logs/linkedin-changelog.log}
cd "${0:A:h}/.." || exit 1
exec /usr/bin/python3 pull_changelog.py >> "$LOG" 2>&1
