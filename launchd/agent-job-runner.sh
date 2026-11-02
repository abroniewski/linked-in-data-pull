#!/bin/zsh
# Main executable of "Agent Job Runner.app". It runs one job script and nothing else: the script must be an
# executable file inside ~/CODE_Repositories. macOS permissions (for example "files managed by Google Drive")
# are granted to this app once, and every job started through it inherits them.
job=${1:A}   # absolute path with symlinks and .. resolved
case "$job" in
  "$HOME"/CODE_Repositories/*) ;;
  *) echo "agent-job-runner: refused, outside ~/CODE_Repositories: $job" >&2; exit 64 ;;
esac
[ -f "$job" ] && [ -x "$job" ] || { echo "agent-job-runner: not an executable file: $job" >&2; exit 66; }
shift
exec /bin/zsh "$job" "$@"
