"""ThreatLocker guardrail for Claude Code.

Blocks creation/execution of script files outside GitHub repo folders.
Called as a PreToolUse hook — reads JSON from stdin, exits 0 (allow) or 2 (block).

This is the CANONICAL copy. Referenced by ~/.claude/settings.json (user-level hook).
Do not duplicate into individual repos — the user-level hook covers all repos.
"""
import sys
import json
import re

ALLOWED_PREFIXES = [
    "c:/users/hughmacfarlane/github/",
    "/c/users/hughmacfarlane/github/",
    "c:/users/hughmacfarlane/.claude/",
    "/c/users/hughmacfarlane/.claude/",
]

SCRIPT_EXT = re.compile(r"\.(ps1|py|bat|sh|cmd|vbs)$", re.IGNORECASE)

# Regex to find absolute paths with script extensions in bash commands
ABS_PATH_RE = re.compile(
    r"[a-zA-Z]:[/\\][^ \"'|;&>\n]+\.(?:ps1|py|bat|sh|cmd|vbs)"
    r"|"
    r"/[a-zA-Z][^ \"'|;&>\n]*\.(?:ps1|py|bat|sh|cmd|vbs)",
    re.IGNORECASE,
)


def normalize(path: str) -> str:
    return path.replace("\\", "/").lower()


def is_absolute(path: str) -> bool:
    n = normalize(path)
    return n.startswith("/") or (len(n) > 2 and n[1] == ":")


def is_allowed(path: str) -> bool:
    if not is_absolute(path):
        return True  # relative paths are within the project dir
    n = normalize(path)
    return any(n.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def block(message: str):
    print(f"ThreatLocker guard: {message}", file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail-open

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    command = tool_input.get("command", "")

    # Write / Edit: check file_path directly
    if tool in ("Write", "Edit") and file_path:
        if SCRIPT_EXT.search(file_path) and not is_allowed(file_path):
            block(f"Cannot create/edit script file outside GitHub repos: {file_path}")

    # Bash: scan command for absolute paths to script files
    if tool == "Bash" and command:
        for path in ABS_PATH_RE.findall(command):
            if not is_allowed(path):
                block(f"Cannot create/execute script outside GitHub repos: {path}")

    sys.exit(0)


if __name__ == "__main__":
    main()
