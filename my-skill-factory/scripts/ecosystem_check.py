#!/usr/bin/env python3
"""Cheap gate for my-skill-factory's Ecosystem Refresh loop.

Runs on every factory invocation. Costs two `--version` calls and one small JSON
read, and decides whether the expensive web research (references/ecosystem-refresh.md)
is due. Never blocks the factory: it always exits 0 and prints a JSON verdict.

Usage (from <repo-root>):
    python my-skill-factory/scripts/ecosystem_check.py          # check -> JSON verdict
    python my-skill-factory/scripts/ecosystem_check.py record   # after a refresh: stamp versions + date

State lives in my-skill-factory/feedback/ecosystem-state.json — git-tracked, so a refresh
done on one machine counts for every machine the repo syncs to.
"""

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

# Tool name -> command that prints its version. A missing binary is not an error:
# the skill is also synced to hosts that have only one of the two CLIs.
TOOLS = {
    "claude": ["claude", "--version"],
    "codex": ["codex", "--version"],
}

VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def skill_dir() -> Path:
    """Resolve the *source* skill dir, never the installed cache copy.

    The factory runs this from <repo-root>, so prefer the git toplevel of the cwd;
    fall back to this file's location. Reading state from the plugin cache would
    report "never refreshed" forever, since feedback/ is not copied there.
    """
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        if top and (Path(top) / "my-skill-factory" / "SKILL.md").is_file():
            return Path(top) / "my-skill-factory"
    except (OSError, subprocess.SubprocessError):
        pass
    return Path(__file__).resolve().parents[1]


def state_file() -> Path:
    return skill_dir() / "feedback" / "ecosystem-state.json"


def installed_version(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = VERSION_RE.search(out)
    return ".".join(m.groups()) if m else None


def parse_version(v: str | None) -> tuple[int, int, int] | None:
    """'2.1.278' -> (2, 1, 278). None stays None (tool absent or never recorded)."""
    if not v:
        return None
    m = VERSION_RE.search(v)
    return tuple(int(x) for x in m.groups()) if m else None


def refresh_reasons(
    recorded: dict[str, str | None],
    current: dict[str, str | None],
    days_since: int,
) -> list[str]:
    """Decide whether the expensive web research is due.

    Returns human-readable reasons, e.g. ["claude 2.1.278 -> 2.2.0"]; an empty
    list means "not due". Only called when a previous refresh exists (the
    first-ever run is always due and handled by the caller).

    recorded / current: {"claude": "2.1.278", "codex": "0.154.0"}. A value is None
        when that CLI is absent on this machine, or was absent when recorded.
    days_since: whole days since the last recorded refresh.

    This is the knob that trades freshness against token cost:
      - Claude Code bumps its *patch* number almost daily (2.1.278 -> 2.1.285 within
        a week), and Codex bumps its *minor* every few days (0.154 -> 0.159). A bare
        "any version differs" rule would fire on nearly every factory run.
      - A machine synced via git (e.g. tail-dgx) may run an OLDER version than the one
        recorded here. That machine has nothing new to learn and should not trigger.
      - Practice changes can ship without any CLI release (a new model launch, an
        updated best-practices page), so some upper bound on days_since is needed.

    Helpers: parse_version("2.1.278") -> (2, 1, 278); tuples compare element-wise.
    """
    # TODO(user): implement the due policy (5-10 lines).
    raise NotImplementedError("refresh_reasons: due policy not implemented yet")


def load_state() -> dict | None:
    path = state_file()
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def check() -> dict:
    current = {name: installed_version(cmd) for name, cmd in TOOLS.items()}
    verdict = {"due": False, "reasons": [], "current": current,
               "recorded": None, "last_refresh": None, "state_file": str(state_file())}
    try:
        state = load_state()
    except (OSError, ValueError) as e:
        # A corrupt state file must not wedge the loop shut: refresh and rewrite it.
        verdict.update(due=True, reasons=[f"unreadable state file ({e})"])
        return verdict
    if state is None:
        verdict.update(due=True, reasons=["no refresh recorded yet (first run)"])
        return verdict
    recorded = state.get("versions", {})
    last = state.get("last_refresh")
    days_since = (date.today() - date.fromisoformat(last)).days if last else 10**6
    verdict.update(recorded=recorded, last_refresh=last, days_since=days_since)
    reasons = refresh_reasons(recorded, current, days_since)
    verdict.update(due=bool(reasons), reasons=reasons)
    return verdict


def record() -> dict:
    """Stamp a completed refresh. Keeps the `declined` list the triage step maintains."""
    path = state_file()
    try:
        state = load_state() or {}
    except (OSError, ValueError):
        state = {}
    state["last_refresh"] = date.today().isoformat()
    state["versions"] = {name: installed_version(cmd) for name, cmd in TOOLS.items()}
    state.setdefault("declined", [])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"recorded": state, "state_file": str(path)}


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode == "check":
        result = check()
    elif mode == "record":
        result = record()
    else:
        print(__doc__, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
