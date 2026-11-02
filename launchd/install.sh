#!/bin/sh
# Install (or reinstall) the daily change-log job on macOS.
# Settings via env: LABEL (default local.linkedin-changelog), DATA_DIR (default ~/linkedin-feed),
# HOUR/MINUTE (default 08:30), PYTHON (default /usr/bin/python3).
set -eu
REPO=$(cd "$(dirname "$0")/.." && pwd)
LABEL=${LABEL:-local.linkedin-changelog}
DATA_DIR=${DATA_DIR:-$HOME/linkedin-feed}
HOUR=${HOUR:-8}; MINUTE=${MINUTE:-30}; PYTHON=${PYTHON:-/usr/bin/python3}
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
mkdir -p "$DATA_DIR/changelog"; chmod 700 "$DATA_DIR" "$DATA_DIR/changelog"
sed -e "s|__LABEL__|$LABEL|g" -e "s|__REPO__|$REPO|g" -e "s|__DATA_DIR__|$DATA_DIR|g" \
    -e "s|__HOUR__|$HOUR|g" -e "s|__MINUTE__|$MINUTE|g" -e "s|__PYTHON__|$PYTHON|g" \
    "$REPO/launchd/linkedin-changelog.plist.template" > "$PLIST"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL ($PLIST), daily at $HOUR:$MINUTE, data in $DATA_DIR"
echo "Run once now: launchctl kickstart gui/$(id -u)/$LABEL ; then: tail $DATA_DIR/changelog/launchd.log"
