#!/bin/sh
# Build ~/Applications/Agent Job Runner.app, the launcher that scheduled jobs go through (see README).
# Compiles launchd/agent-job-runner.c with the Xcode command line tools (cc).
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
APP=${APP:-$HOME/Applications/Agent Job Runner.app}
mkdir -p "$APP/Contents/MacOS"
command -v cc >/dev/null 2>&1 || { echo "No C compiler: run xcode-select --install first." >&2; exit 1; }
cc -O2 -Wall -o "$APP/Contents/MacOS/agent-job-runner" "$HERE/agent-job-runner.c"
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleIdentifier</key><string>local.agent-job-runner</string>
  <key>CFBundleName</key><string>Agent Job Runner</string>
  <key>CFBundleExecutable</key><string>agent-job-runner</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>LSUIElement</key><true/>
</dict>
</plist>
PLIST
codesign --force --sign - "$APP"   # ad-hoc signature gives macOS a stable identity to attach permissions to
echo "Built $APP"
echo "Next: run the permission test once, in Terminal, and click Allow if macOS asks about Google Drive:"
echo "  open -W -a \"$APP\" --args \"$HERE/run-changelog.sh\""
