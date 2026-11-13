#!/usr/bin/env bash
# Launcher for fork_guard.py. Picks the first interpreter that is a real
# Python 3.10+ (on Windows, `python3` may be a Microsoft Store stub that exits
# 49). If none works, block the command: a guard that can't run must fail
# closed, because any exit code other than 2 lets the tool call through.
here="$(cd "$(dirname "$0")" && pwd)"
for py in python3 python py; do
  if command -v "$py" >/dev/null 2>&1 &&
    "$py" -c 'import sys; sys.exit(sys.version_info < (3, 10))' </dev/null >/dev/null 2>&1; then
    exec "$py" "$here/fork_guard.py"
  fi
done
echo "fork_guard: no working Python 3.10+ found, so the command is blocked." >&2
exit 2
