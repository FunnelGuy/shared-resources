#!/bin/bash
# Shared pre-commit hook: blocks git commit if ruff lint OR format check fails.
# Used as a Claude Code PreToolUse hook on Bash tool calls.
#
# Usage in .claude/settings.json:
#   "command": "bash /path/to/pre-commit-ruff.sh src/ tests/"
#
# Arguments: paths to check (passed to both `ruff check` and `ruff format --check`).
# If none given, checks "."
# Requires: python3 (for JSON parsing — jq is not available in Git Bash on Windows)
#
# MUST mirror CI exactly. Fleet CI runs BOTH `ruff check` (lint) AND
# `ruff format --check` (formatting). A hook that runs only one lets the other
# reach CI red (incident: agent-gateway CI F541 lint error passed this hook when
# it only ran format --check, 2026-07-06). Keep both steps here.

INPUT=$(cat)

# Extract the bash command from the hook JSON input using Python (no jq on Windows)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only intercept git commit commands
if ! echo "$COMMAND" | grep -qE 'git\s+commit'; then
  exit 0
fi

# Use provided paths or default to current directory
PATHS="${@:-.}"

deny() {
  # Return deny decision as JSON using Python (no jq)
  python3 -c "
import json, sys
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': sys.argv[1]
    }
}))
" "$1"
  exit 0
}

# 1. Lint (ruff check) — matches CI step 1
LINT_OUTPUT=$(cd "$CLAUDE_PROJECT_DIR" && ruff check $PATHS 2>&1)
if [ $? -ne 0 ]; then
  deny "ruff check (lint) failed. Run 'ruff check --fix $PATHS' (or fix manually), then commit. Output: $LINT_OUTPUT"
fi

# 2. Format (ruff format --check) — matches CI step 2
FMT_OUTPUT=$(cd "$CLAUDE_PROJECT_DIR" && ruff format --check $PATHS 2>&1)
if [ $? -ne 0 ]; then
  deny "ruff format check failed. Run 'ruff format $PATHS' to fix, then commit. Output: $FMT_OUTPUT"
fi

exit 0
