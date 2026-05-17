---
name: bypass-toggle
description: Toggle effective bypassPermissions for the user's Claude Code sessions via a PreToolUse hook + flag file. Use when the user wants to skip further permission prompts after approving a plan — especially when the approval came from the iPhone Claude app (Remote Control) and they don't want to attach a TTY to Shift+Tab. ONLY affects Claude Code (Cursor and other agents read their own configs). Trigger phrases include "/bypass-toggle", "bypass on", "bypass off", "bypass status", "stop asking for permission", "skip permission prompts", "no more permission asks", "バイパス on", "バイパス off", "バイパスにして", "バイパス止めて", "プロンプト止めて", "もう確認しないで", "承認スキップ".
---

# bypass-toggle

A user-level PreToolUse hook (registered by this plugin) reads `~/.claude/bypass-toggle/state.json` before every tool call. When `enabled: true` and not expired, it returns `permissionDecision: "allow"`, giving the session effective bypassPermissions behavior without changing `--permission-mode`.

## Scope

- **User-global by design.** The flag affects every Claude Code session for this user until turned off (or until TTL expires). The user accepted that trade-off when asking for the skill.
- **Claude Code only.** The hook is registered through this plugin's `hooks/hooks.json`, which is read only by Claude Code. Cursor and other agents are not affected.

## When invoked

Parse the user's intent. Map fuzzy phrasing to one of three commands:

| Intent | Command |
|--------|---------|
| Turn on (no TTL) | `on` |
| Turn on for N minutes | `on` with `ttl_minutes=N` |
| Turn off | `off` |
| Show status | `status` |

Defaults:
- "bypass on" / "バイパス on" with no duration mentioned → no TTL.
- "for a while" / "しばらく" / "ちょっとだけ" → 30 minutes.
- Numeric duration ("1時間" / "10分" / "for an hour") → parse and use.

### Doing the work

Manage the state file directly via Bash; do NOT shell out to a helper script (none is shipped — the only Python file is the hook itself).

State file path: `~/.claude/bypass-toggle/state.json`
Schema:

```json
{
  "enabled": true,
  "set_at": <unix-seconds>,
  "expires_at": <unix-seconds or null>,
  "ttl_minutes": <int or null>
}
```

#### Turn on

```bash
mkdir -p ~/.claude/bypass-toggle
python3 - <<'PY'
import json, time, pathlib
ttl = None  # set to int minutes when applicable
state = {
    "enabled": True,
    "set_at": time.time(),
    "expires_at": time.time() + ttl * 60 if ttl else None,
    "ttl_minutes": ttl,
}
p = pathlib.Path.home() / ".claude" / "bypass-toggle" / "state.json"
p.write_text(json.dumps(state, indent=2) + "\n")
print("ON" + (f" (TTL {ttl}m)" if ttl else " (no TTL)"))
PY
```

When the user requested a TTL, substitute the `ttl = None` line with `ttl = <int>` before running.

#### Turn off

```bash
rm -f ~/.claude/bypass-toggle/state.json
echo "OFF"
```

#### Status

```bash
python3 - <<'PY'
import json, time, pathlib
p = pathlib.Path.home() / ".claude" / "bypass-toggle" / "state.json"
if not p.exists():
    print("OFF")
else:
    s = json.loads(p.read_text())
    if not s.get("enabled"):
        print("OFF")
    elif s.get("expires_at") and time.time() >= s["expires_at"]:
        print("EXPIRED")
    elif s.get("expires_at"):
        print(f"ON ({int(s['expires_at'] - time.time())}s remaining)")
    else:
        print("ON (no TTL)")
PY
```

## Reporting back to the user

Match the user's language. For Japanese users (the common case), reply like:

- ON 設定 (TTL なし): 「バイパス ON。`bypass off` するまで全 Claude Code セッションで permission プロンプトをスキップ。」
- ON 設定 (TTL あり): 「バイパス ON (30 分で自動 OFF)。」
- OFF: 「バイパス OFF。通常の permission mode に戻る。」
- STATUS: 上の出力をそのまま見せる。

Warn once on ON (only if the user didn't already acknowledge in this turn):

- 「注意: この user の全 Claude Code セッションに効く。Cursor 等は影響なし。`bypass off` で解除。」

## Verifying the hook is live

If the user reports that bypass-on didn't change behavior, run:

```bash
ls ~/.claude/plugins/cache/hideki-plugins/bypass-toggle/*/hooks/hooks.json
cat ~/.claude/bypass-toggle/state.json 2>/dev/null
```

The hook only fires in NEW Claude Code sessions started after the plugin was enabled. Existing sessions need a restart.

## References

- `references/scenarios.feature` — BDD scenarios. WHEN TO READ: only when auditing or amending this skill; not needed for normal execution.
