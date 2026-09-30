# Ecosystem Practices

**WHEN TO READ**: in Step 2 (Design) of every factory run, and by `skill-improve` when
it audits a skill for drift. Kept deliberately compact so that reading it every time
stays cheap.

Maintained by the Ecosystem Refresh loop (`references/ecosystem-refresh.md`). Do not
hand-edit without recording an amendment — an unsourced line here is exactly the
stale knowledge this file exists to prevent.

**Item format** — one line per practice:
`- **<practice>** — <how it changes skill design>. _applies: <scope>; source: <url or CLI command>; verified: YYYY-MM-DD_`

**Size cap**: about 120 lines. Retire superseded or unverifiable items before adding.

## Models

- **Use model aliases or `inherit`, never pinned IDs, in `model:`; set `effort` explicitly on reasoning-heavy skills** — Opus 5.5 defaults to `medium` effort on the API (Fable 5.1 / Sonnet 5.5 default to `high`); after a Claude Code upgrade, run `/doctor prompt-audit` over new skills and agents to catch prompting written for older models. _applies: Claude 5.x; prompt-audit needs Claude Code >= 2.1.283; source: https://platform.claude.com/docs/en/about-claude/models/overview, Claude Code CHANGELOG 2.1.280/2.1.283; verified: 2026-09-30_

## Token efficiency

- **Measure, don't estimate: `claude plugin details <name>@hideki-plugins`** — it reports always-on and on-invoke tokens. Keep on-invoke ≤5k tokens; after auto-compaction only a skill's first 5,000 tokens are re-attached (25k shared), so standing rules go at the top of the body. _applies: Claude Code >= 2.1.278; source: `claude plugin details`, https://code.claude.com/docs/en/skills, https://agentskills.io/specification; verified: 2026-09-30_

## Agents

- **Set `background` explicitly on `context: fork` skills** — forked skills and interactive-session subagents default to background; use `background: false` when the invoking turn needs the result inline, and make fan-out skills wait for completion notifications instead of assuming synchronous results. _applies: Claude Code >= 2.1.218; source: https://code.claude.com/docs/en/skills, https://code.claude.com/docs/en/sub-agents; verified: 2026-09-30_
- **Plugin-shipped agents ignore `hooks`, `mcpServers`, `permissionMode`** — don't design around them; use `omitClaudeMd` (self-contained reviewers), `effort`, `maxTurns`, `isolation: worktree` instead, and keep agent descriptions short (startup warning above 15k combined tokens). `skills:` preloads full skill content but cannot preload `disable-model-invocation` skills. _applies: Claude Code >= 2.1.271; source: https://code.claude.com/docs/en/sub-agents; verified: 2026-09-30_

## Skill authoring

- **Description ≤1,024 chars, key use case first, third person, no XML tags** — Claude Code truncates description+`when_to_use` at 1,536 chars and drops the descriptions of rarely-used skills when the listing overflows its budget, so piling on trigger phrases loses them. _applies: all; source: https://agentskills.io/specification, https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices, https://code.claude.com/docs/en/skills; verified: 2026-09-30_
- **Choose the invocation mode in design** — side-effecting manual workflows: `disable-model-invocation: true` (also removes the always-on description cost); file-scoped skills: `paths`; reasoning-heavy: `effort`; plus `allowed-tools` / `user-invocable` / `arguments` as needed. Name rules: ≤64 chars, lowercase, no leading/trailing/double hyphens, matches the directory, no "anthropic"/"claude". Skills meant for claude.ai / Skills API upload must stick to the six spec fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). _applies: Claude Code >= 2.1.278; source: https://code.claude.com/docs/en/skills, https://agentskills.io/specification; verified: 2026-09-30_
- **Bundled scripts: relative `scripts/…` in prose, `${CLAUDE_SKILL_DIR}` only in `!` injection and `allowed-tools`** — Codex resolves relative paths against the SKILL.md dir but does not expand the variable; an injected command that fails, or is not pre-approved in `allowed-tools` outside auto mode, aborts the whole skill (append `|| true` where non-zero exits are expected). _applies: Claude Code >= 2.1.278, Codex >= 0.154; source: https://code.claude.com/docs/en/skills, `codex debug prompt-input`; verified: 2026-09-30_
- **Gate installs on `claude plugin validate --strict`** — run it on the generated plugin dir and its `skills/` dir after install and treat failures as blocking; malformed frontmatter otherwise loads silently with empty metadata, so the skill never triggers. _applies: Claude Code >= 2.1.233; source: `claude plugin validate --help`, https://code.claude.com/docs/en/skills; verified: 2026-09-30_
- **Verify behavior with `claude plugin eval --no-publish`** — turn the BDD scenarios into ≥3 eval cases scored against the automatic no-plugin baseline; a `tool_used: Skill` grader measures triggering. Always pass `--no-publish` (reports publish to claude.ai by default) and a `--max-cost-usd`. It does not replace real-service smoke for wrapper skills (un-mocked MCP servers don't start). Open: confirm `--eval-dir` works with this marketplace's `skills/<name>/` layout before standardizing. _applies: Claude Code >= 2.1.269; source: `claude plugin eval --help`, Claude Code CHANGELOG 2.1.269; verified: 2026-09-30_

## Codex compatibility

- **Codex may list skills by name only, so the name must carry the trigger** — with ~50+ synced skills the installed Codex's skill list omitted every description (list capped at 2% of context / 8,000 chars, descriptions shortened first). Make names self-describing, document `$skill-name` invocation, and check with `codex debug prompt-input` after `sync_skills.py`. The installed Codex reads `~/.codex/skills` (docs say `~/.agents/skills` — trust the CLI). Manual-only skills: `agents/openai.yaml` with `policy.allow_implicit_invocation: false`. _applies: Codex >= 0.154 with ~50+ skills; source: `codex debug prompt-input`, https://developers.openai.com/codex/skills; verified: 2026-09-30_
