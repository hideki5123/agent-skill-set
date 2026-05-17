---
name: auto-mode
description: Switch the user's Claude Code session back to classifier-guided auto mode by clearing the bypass-toggle flag. Use after approving a plan from the iPhone Claude app (or anywhere bypass-toggle is on) when you want subsequent tool calls to go through the auto-mode classifier instead of being auto-allowed. Companion to bypass-toggle. Only affects Claude Code (Cursor and other agents are not touched). Trigger phrases include "/auto-mode", "auto on", "auto モード", "auto に戻して", "オートに戻して", "オート", "classifier に戻して", "クラシファイアに戻して", "bypass やめて", "bypass 解除", "switch to auto", "back to auto", "leave bypass mode".
---

# auto-mode

Companion skill to `bypass-toggle`. Clears the shared flag at `~/.claude/bypass-toggle/state.json` so the PreToolUse hook stops returning `permissionDecision: "allow"` and the session falls through to whatever permission mode it was started with.

This skill registers NO hook of its own. It is purely a user-facing toggle that manipulates `bypass-toggle`'s flag file.

## When invoked

| Intent | Action |
|--------|--------|
| Switch to auto / "auto on" / "auto に戻して" | Delete `~/.claude/bypass-toggle/state.json` |
| Status | Read the flag and report which mode is effectively active |

### Switch to auto

```bash
rm -f ~/.claude/bypass-toggle/state.json
```

### Status

```bash
python3 - <<'PY'
import json, time, pathlib
p = pathlib.Path.home() / ".claude" / "bypass-toggle" / "state.json"
if not p.exists():
    print("MODE: auto / native (no bypass flag)")
else:
    try:
        s = json.loads(p.read_text())
    except Exception:
        print("MODE: auto / native (bypass flag unreadable, hook will fall through)")
        raise SystemExit
    if not s.get("enabled"):
        print("MODE: auto / native (bypass disabled)")
    elif s.get("expires_at") and time.time() >= s["expires_at"]:
        print("MODE: auto / native (bypass TTL expired)")
    elif s.get("expires_at"):
        print(f"MODE: BYPASS ({int(s['expires_at'] - time.time())}s remaining)")
    else:
        print("MODE: BYPASS (no TTL)")
PY
```

## Reporting back to the user

Match the user's language. Common Japanese replies:

- 切替後 (flag があった場合): 「auto モードに戻した。今後の tool 呼び出しは session 起動時の `--permission-mode` (= auto の想定) に従う。classifier がガード。」
- すでに auto: 「すでに auto モード (bypass フラグなし)。何もしなかった。」
- Status: 上の出力をそのまま見せる。

## Important caveat

This skill clears the bypass flag — it does NOT force the session's nominal `--permission-mode` to `auto`. The actual post-clear mode is whatever the session was launched with:

- `ccob` / `ccsb` / `ccwb` / `ccb` / `cchb` (background, `--permission-mode auto`) → returns to **auto** ✓
- `ccyb` (background, `--dangerously-skip-permissions`) → returns to **bypass** anyway (no effective change)
- `cc` / `cco` etc. (foreground, `--permission-mode plan`) → returns to **plan**, which will stall on Bash/Edit without an interactive Shift+Tab

For the iPhone workflow the user actually cares about (`cc*b` sessions reachable via Remote Control), the assumption holds: bypass off → auto.

## Why a separate skill from bypass-toggle?

Semantic clarity. The user (especially from iPhone) wants to think in three states: `bypass on`, `plan` (built-in, via EnterPlanMode), `auto`. Having `/auto-mode` as a distinct command makes the intent obvious in the chat log. Mechanically it could have been a `bypass off` alias, but the dedicated skill is easier to discover and trigger.

## References

- `references/scenarios.feature` — BDD scenarios. WHEN TO READ: only when auditing or amending; not needed for normal execution.
