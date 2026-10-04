#!/usr/bin/env bash
# SessionStart hook: set up a Python venv in Claude Code cloud sessions only.
# Local sessions exit immediately. stdout is added to Claude's context, so keep it to one line.
[ "$CLAUDE_CODE_REMOTE" = "true" ] || exit 0
cd "$CLAUDE_PROJECT_DIR" || exit 0
# Put the venv first on PATH for every later Bash command in the session.
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo "export PATH=\"$CLAUDE_PROJECT_DIR/.venv/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi
if [ -x .venv/bin/python ]; then
  echo "cloud-setup: .venv present, skipped install"
  exit 0
fi
if python3 -m venv .venv >&2 \
  && .venv/bin/pip install --quiet --disable-pip-version-check -r requirements.txt >&2 \
  && .venv/bin/playwright install --with-deps chromium >&2; then
  echo "cloud-setup: .venv ready (on PATH)"
else
  echo "cloud-setup: install FAILED, run it manually before tests"
fi
