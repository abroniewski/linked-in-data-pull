#!/bin/sh
# Install (or reinstall) one of the scheduled LinkedIn jobs on macOS, run through the launcher app.
#
#   JOB=changelog (default)  daily digest of new messages/invitations   default 08:30 every day
#   JOB=snapshot             full snapshot of all LinkedIn data domains  default 05:30 every Sunday
#
# Settings via env: LABEL (default local.linkedin-<job>), HOUR, MINUTE, WEEKDAY (0=Sunday .. 6; for snapshot,
# set WEEKDAY=any for daily), LOG (default ~/Library/Logs/<LABEL>.log), APP (default ~/Applications/Agent Job Runner.app).
# Build the app first with launchd/build-runner-app.sh. Where data goes comes from LINKEDIN_OUTPUT_DIR in .env.
set -eu
REPO=$(cd "$(dirname "$0")/.." && pwd)
JOB=${JOB:-changelog}
case "$JOB" in
  changelog) WRAPPER=run-changelog.sh; D_HOUR=8; D_MIN=30; D_WEEKDAY=any ;;
  snapshot)  WRAPPER=run-snapshot.sh;  D_HOUR=5; D_MIN=30; D_WEEKDAY=0 ;;
  *) echo "Unknown JOB=$JOB (use changelog or snapshot)" >&2; exit 1 ;;
esac
LABEL=${LABEL:-local.linkedin-$JOB}
LOG=${LOG:-$HOME/Library/Logs/$LABEL.log}
HOUR=${HOUR:-$D_HOUR}; MINUTE=${MINUTE:-$D_MIN}; WEEKDAY=${WEEKDAY:-$D_WEEKDAY}
APP=${APP:-$HOME/Applications/Agent Job Runner.app}
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
[ -d "$APP" ] || { echo "Missing $APP: run launchd/build-runner-app.sh first." >&2; exit 1; }
[ -f "$REPO/.env" ] || { echo "Missing $REPO/.env: copy .env.example to .env and set LINKEDIN_OUTPUT_DIR first." >&2; exit 1; }
INTERVAL="<dict><key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>$MINUTE</integer>"
[ "$WEEKDAY" = any ] || INTERVAL="$INTERVAL<key>Weekday</key><integer>$WEEKDAY</integer>"
INTERVAL="$INTERVAL</dict>"
sed -e "s|__LABEL__|$LABEL|g" -e "s|__REPO__|$REPO|g" -e "s|__LOG__|$LOG|g" \
    -e "s|__APP__|$APP|g" -e "s|__WRAPPER__|$WRAPPER|g" -e "s|__INTERVAL__|$INTERVAL|g" \
    "$REPO/launchd/job.plist.template" > "$PLIST"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
when="daily"; [ "$WEEKDAY" = any ] || when="weekly (weekday $WEEKDAY, 0=Sunday)"
echo "Installed $LABEL ($PLIST), $when at $HOUR:$MINUTE, log $LOG"
echo "Run once now: launchctl kickstart -k gui/$(id -u)/$LABEL ; then: tail $LOG"
