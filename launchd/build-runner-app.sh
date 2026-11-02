#!/bin/sh
# Build ~/Applications/Agent Job Runner.app, the launcher that scheduled jobs go through (see README).
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
APP=${APP:-$HOME/Applications/Agent Job Runner.app}
mkdir -p "$APP/Contents/MacOS"
cp "$HERE/agent-job-runner.sh" "$APP/Contents/MacOS/agent-job-runner"
chmod 755 "$APP/Contents/MacOS/agent-job-runner"
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
