#!/bin/sh
# Install (or reinstall) the daily change-log job on macOS.
# Settings via env: LABEL (default local.linkedin-changelog), HOUR/MINUTE (default 08:30),
# PYTHON (default /usr/bin/python3), LOG (default ~/Library/Logs/<LABEL>.log).
# Where the data goes comes from LINKEDIN_OUTPUT_DIR in the repo's .env (copy .env.example first).
set -eu
REPO=$(cd "$(dirname "$0")/.." && pwd)
LABEL=${LABEL:-local.linkedin-changelog}
LOG=${LOG:-$HOME/Library/Logs/$LABEL.log}
HOUR=${HOUR:-8}; MINUTE=${MINUTE:-30}; PYTHON=${PYTHON:-/usr/bin/python3}
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
[ -f "$REPO/.env" ] || { echo "Missing $REPO/.env: copy .env.example to .env and set LINKEDIN_OUTPUT_DIR first." >&2; exit 1; }
sed -e "s|__LABEL__|$LABEL|g" -e "s|__REPO__|$REPO|g" -e "s|__LOG__|$LOG|g" \
    -e "s|__HOUR__|$HOUR|g" -e "s|__MINUTE__|$MINUTE|g" -e "s|__PYTHON__|$PYTHON|g" \
    "$REPO/launchd/linkedin-changelog.plist.template" > "$PLIST"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL ($PLIST), daily at $HOUR:$MINUTE, log $LOG"
echo "Run once now: launchctl kickstart gui/$(id -u)/$LABEL ; then: tail $LOG"
