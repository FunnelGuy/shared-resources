"""Bash description guardrail for Claude Code.

Blocks Bash tool calls that lack a plain-English description.
Global CLAUDE.md requires: "always include a short plain-English description
of what the action does and why, so the user can make an informed approval decision."

Called as a PreToolUse hook — reads JSON from stdin, exits 0 (allow) or 2 (block).

This is the CANONICAL copy. Referenced by ~/.claude/settings.json (user-level hook).
Do not duplicate into individual repos — the user-level hook covers all repos.
"""
import sys
import json

MIN_DESCRIPTION_LENGTH = 10  # roughly two words minimum


def block(message: str):
    print(f"Bash description guard: {message}", file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail-open

    tool = data.get("tool_name", "")
    if tool != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    description = (tool_input.get("description") or "").strip()

    if len(description) < MIN_DESCRIPTION_LENGTH:
        block(
            "Bash commands must include a 'description' parameter explaining "
            "what the command does and why, so the user can make an informed "
            "approval decision. Re-call with a clear description."
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
