#!/bin/bash
# Shared pre-commit hook: blocks git commit if ruff format check fails.
# Used as a Claude Code PreToolUse hook on Bash tool calls.
#
# Usage in .claude/settings.json:
#   "command": "bash /path/to/pre-commit-ruff.sh src/ tests/"
#
# Arguments: paths to check (passed to ruff format --check). If none given, checks "."
# Requires: python3 (for JSON parsing — jq is not available in Git Bash on Windows)

INPUT=$(cat)

# Extract the bash command from the hook JSON input using Python (no jq on Windows)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only intercept git commit commands
if ! echo "$COMMAND" | grep -qE 'git\s+commit'; then
  exit 0
fi

# Use provided paths or default to current directory
PATHS="${@:-.}"

RUFF_OUTPUT=$(cd "$CLAUDE_PROJECT_DIR" && ruff format --check $PATHS 2>&1)
RUFF_EXIT=$?

if [ $RUFF_EXIT -ne 0 ]; then
  REASON="ruff format check failed. Run 'ruff format $PATHS' to fix, then commit. Output: $RUFF_OUTPUT"
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
" "$REASON"
else
  exit 0
fi
