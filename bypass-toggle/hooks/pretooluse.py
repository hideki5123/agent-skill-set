#!/usr/bin/env python3
"""PreToolUse hook for the bypass-toggle plugin.

Reads ~/.claude/bypass-toggle/state.json. If enabled and not expired, emits
an "allow" permission decision so the parent Claude Code session skips
permission prompts for this tool call.

Silent (exit 0, no stdout) when the flag is off, missing, expired, or
unreadable — falls back to normal permission flow.
"""
import json
import sys
import time
from pathlib import Path

STATE_FILE = Path.home() / ".claude" / "bypass-toggle" / "state.json"


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass

    if not STATE_FILE.exists():
        return 0

    try:
        state = json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return 0

    if not state.get("enabled"):
        return 0

    expires_at = state.get("expires_at")
    if expires_at is not None:
        try:
            if time.time() >= float(expires_at):
                return 0
        except (TypeError, ValueError):
            return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "bypass-toggle flag is on",
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
