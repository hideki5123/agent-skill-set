#!/usr/bin/env python3
"""wire_agents.py — own all filesystem mutation for the agents-init skill.

Inspects and manipulates ./AGENTS.md and ./CLAUDE.md in the current working
directory. The SKILL.md body orchestrates by reading --detect JSON output and
calling --wire with appropriate flags. See ../references/state-matrix.md for
the state-machine semantics.
"""

import argparse
import filecmp
import json
import os
import shutil
import sys
import time
from difflib import unified_diff
from pathlib import Path

CLAUDE = Path("CLAUDE.md")
AGENTS = Path("AGENTS.md")


def platform_name() -> str:
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform.startswith("win"):
        return "windows"
    return sys.platform


def is_git_repo() -> bool:
    p = Path(".git")
    return p.is_dir() or p.is_file()


def gitignore_warnings() -> list[str]:
    warnings: list[str] = []
    gi = Path(".gitignore")
    if not gi.exists():
        return warnings
    try:
        text = gi.read_text(encoding="utf-8")
    except OSError:
        return warnings
    for name in ("CLAUDE.md", "AGENTS.md"):
        for line in text.splitlines():
            stripped = line.strip()
            if stripped in (name, f"/{name}"):
                warnings.append(
                    f"WARNING: {name} is listed in .gitignore — it will not be committed"
                )
    return warnings


def claude_symlink_target() -> str | None:
    if not CLAUDE.is_symlink():
        return None
    try:
        return os.readlink(CLAUDE)
    except OSError:
        return None


def detect_state() -> tuple[str, dict]:
    claude_is_symlink = CLAUDE.is_symlink()
    target = claude_symlink_target()
    claude_real_file = CLAUDE.is_file() and not claude_is_symlink
    agents_exists = AGENTS.is_file() and not AGENTS.is_symlink()

    extra = {
        "platform": platform_name(),
        "claude_is_symlink": claude_is_symlink,
        "symlink_target": target,
        "claude_real_file": claude_real_file,
        "agents_exists": agents_exists,
    }

    if claude_is_symlink:
        if target in ("AGENTS.md", "./AGENTS.md") and agents_exists:
            return "wired", extra
        return "foreign-symlink", extra

    if not claude_real_file and not agents_exists:
        return "needs-init", extra
    if claude_real_file and not agents_exists:
        return "ready-claude", extra
    if agents_exists and not claude_real_file:
        return "ready-agents", extra

    try:
        same = filecmp.cmp(CLAUDE, AGENTS, shallow=False)
    except OSError:
        same = False
    return ("identical" if same else "conflict"), extra


def emit_diff_to_stderr() -> None:
    try:
        a = CLAUDE.read_text(encoding="utf-8").splitlines(keepends=True)
        b = AGENTS.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError:
        return
    diff = unified_diff(a, b, fromfile="CLAUDE.md", tofile="AGENTS.md")
    sys.stderr.write("".join(diff))
    sys.stderr.flush()


def link_or_copy(actions: list[str]) -> None:
    """Create CLAUDE.md as symlink → AGENTS.md (or copy on Windows)."""
    if platform_name() == "windows":
        shutil.copyfile(AGENTS, CLAUDE)
        actions.append("cp AGENTS.md CLAUDE.md  # Windows: symlink unsupported")
        actions.append(
            "WARNING: file copy used; re-run /agents-init after edits to AGENTS.md"
        )
    else:
        os.symlink("AGENTS.md", CLAUDE)
        actions.append("ln -s AGENTS.md CLAUDE.md")


def plan_actions(state: str, prefer: str | None) -> list[str]:
    if state == "ready-claude":
        return ["mv CLAUDE.md AGENTS.md", "ln -s AGENTS.md CLAUDE.md"]
    if state == "ready-agents":
        return ["ln -s AGENTS.md CLAUDE.md"]
    if state == "identical":
        return ["rm CLAUDE.md", "ln -s AGENTS.md CLAUDE.md"]
    if state == "conflict" and prefer == "agents":
        return ["rm CLAUDE.md", "ln -s AGENTS.md CLAUDE.md"]
    if state == "conflict" and prefer == "claude":
        return [
            "mv AGENTS.md AGENTS.md.bak.<ts>",
            "mv CLAUDE.md AGENTS.md",
            "ln -s AGENTS.md CLAUDE.md",
        ]
    if state == "foreign-symlink":
        return ["rm CLAUDE.md", "ln -s AGENTS.md CLAUDE.md"]
    return []


def cmd_wire(prefer: str | None, force: bool, dry_run: bool) -> int:
    state, extra = detect_state()

    if state == "wired":
        print(json.dumps({"state": state, "actions": [], "message": "already wired — no-op"}))
        return 0

    if state == "needs-init":
        print(json.dumps({
            "state": state,
            "actions": [],
            "error": "needs-init: caller must invoke /init first, then re-run --wire",
        }))
        return 2

    if state == "conflict" and prefer is None:
        emit_diff_to_stderr()
        print(json.dumps({
            "state": state,
            "actions": [],
            "error": "conflict: pass --prefer=agents or --prefer=claude",
        }))
        return 3

    if state == "foreign-symlink" and not force:
        print(json.dumps({
            "state": state,
            "actions": [],
            "symlink_target": extra["symlink_target"],
            "error": "foreign-symlink: pass --force to rewire CLAUDE.md → AGENTS.md",
        }))
        return 4

    if dry_run:
        print(json.dumps({"state": state, "dry_run": True, "actions": plan_actions(state, prefer)}))
        return 0

    actions: list[str] = []

    if state == "ready-claude":
        os.replace(CLAUDE, AGENTS)
        actions.append("mv CLAUDE.md AGENTS.md")
        link_or_copy(actions)
    elif state == "ready-agents":
        link_or_copy(actions)
    elif state == "identical":
        CLAUDE.unlink()
        actions.append("rm CLAUDE.md  # identical to AGENTS.md")
        link_or_copy(actions)
    elif state == "conflict":
        if prefer == "agents":
            CLAUDE.unlink()
            actions.append("rm CLAUDE.md  # --prefer=agents")
            link_or_copy(actions)
        elif prefer == "claude":
            backup = Path(f"AGENTS.md.bak.{int(time.time())}")
            os.replace(AGENTS, backup)
            actions.append(f"mv AGENTS.md {backup.name}")
            os.replace(CLAUDE, AGENTS)
            actions.append("mv CLAUDE.md AGENTS.md")
            link_or_copy(actions)
        else:
            print(json.dumps({"error": f"invalid --prefer={prefer}"}))
            return 5
    elif state == "foreign-symlink":
        CLAUDE.unlink()
        actions.append(f"rm CLAUDE.md  # was symlink → {extra['symlink_target']}")
        link_or_copy(actions)

    print(json.dumps({
        "state": state,
        "result": "wired",
        "actions": actions,
        "warnings": gitignore_warnings(),
        "suggested_git": 'git add AGENTS.md CLAUDE.md && git commit -m "chore: add shared agents context"',
    }))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Wire CLAUDE.md ↔ AGENTS.md")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--detect", action="store_true", help="Print current state as a JSON line")
    mode.add_argument("--wire", action="store_true", help="Perform the wiring based on current state")
    p.add_argument("--prefer", choices=["agents", "claude"], help="Required when state is 'conflict'")
    p.add_argument("--force", action="store_true", help="Required when state is 'foreign-symlink'")
    p.add_argument("--dry-run", action="store_true", help="Print what --wire would do without modifying disk")
    p.add_argument("--allow-non-git", action="store_true", help="Bypass the git-repo sanity check")
    args = p.parse_args()

    if not is_git_repo() and not args.allow_non_git:
        sys.stderr.write("Error: not a git repository. Pass --allow-non-git to override.\n")
        return 10

    if args.detect:
        state, extra = detect_state()
        print(json.dumps({"state": state, **extra}))
        if state == "conflict":
            emit_diff_to_stderr()
        return 0

    if args.wire:
        return cmd_wire(prefer=args.prefer, force=args.force, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
