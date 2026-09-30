---
name: my-skill-factory
version: 1.2.0
description: Create, build, and install custom Claude Code skills into Hideki's local marketplace. End-to-end workflow from requirements gathering to a fully installed and usable skill. Use when the user asks to create a new skill, build a skill, make a plugin, add a new capability, or says "make me a skill for X". Also use when updating or reinstalling an existing custom skill. Trigger phrases include "create skill", "make skill", "new skill", "build plugin", "skill for X", "update skill".
---

# Skill Factory

Create custom Claude Code skills and install them into the local `hideki-plugins` marketplace in one workflow.

## Paths

Every example below uses `<repo-root>` as a placeholder for the user's local clone of this
skill repository. Resolve it once per session:

- macOS / Linux: typically `~/private/repos/agent-skill-set`
- Windows: typically `D:\Shared\agents\my-skills`
- Otherwise: ask the user, or run `git -C <any-skill-dir> rev-parse --show-toplevel`.

The install script (`<repo-root>/my-skill-factory/scripts/install_skill.py`) auto-detects the
repo root via `git rev-parse --show-toplevel`, so when you `cd <repo-root>` first you can use
forward-slash relative paths (`my-skill-factory/scripts/install_skill.py <skill-name>`) on any
platform — that is the form used throughout this document.

## Path discipline (applies to every skill you create or edit)

When authoring a skill's `SKILL.md`, references, or scripts, **never embed hardcoded
operator-specific or OS-specific absolute paths** in the skill's content. These break the
skill on every machine other than the author's, and a generated skill that says
`/Users/alice/...` or `D:\Shared\...` is broken-by-construction.

Forbidden in skill content:

- Operator home paths: `/Users/<name>/...`, `/home/<name>/...`, `C:\Users\<name>\...`.
- Machine-specific roots: `D:\Shared\...`, `/private/...`, `/mnt/<host>/...`.
- Any path that assumes the skill repo lives at one specific location.

Use instead:

- The `<repo-root>` placeholder for this skill repo (see "Paths" above), with
  forward-slash relative paths from there.
- `~` or `$HOME` for the user's home directory.
- Runtime resolution: `git rev-parse --show-toplevel` from inside the repo, or accept
  the path as an argument from the user.
- Documentation examples that show a concrete path **must** be clearly framed as
  examples (e.g. "on Windows this typically resolves to `D:\...`"), not as the
  authoritative path.

**Pre-install verification.** Before running `install_skill.py` on any new or edited
skill, grep the skill source dir for path leaks and clean up any non-example hits:

```bash
grep -rn -e '/Users/' -e '/home/' -e '/private/' -e 'C:\\' -e 'D:\\' \
  <repo-root>/<skill-name>/ --exclude-dir=feedback
```

Each remaining hit must either be (a) a documentation example explicitly framed as
"example" or "typically", or (b) replaced with a placeholder / runtime resolution.
Anything else is a bug.

## Workflow

0. **Feedback Check + Ecosystem Check** — Inward (own feedback) and outward (Claude Code / Codex / model changes) improvement signals; research runs in the background
1. **Gather requirements** — Understand what the skill should do
2. **Design the skill** — Plan structure, references, scripts, assets, and improvement loop level
3. **Team orchestration assessment** — Decide if the skill needs multi-agent review; if so, select perspectives
4. **Create skill files and install** — Write SKILL.md, supporting resources, then always install immediately
5. **Verify** — Confirm the skill appears in a new session
6. **Improve** — Analyze feedback and amend a skill based on evidence (improvement loop)

## Feedback Check

Before starting Step 1, look for accumulated feedback on this factory skill itself:

- If `feedback/log.md` exists next to this SKILL.md and has 5 or more entries, read the
  last 10.
- If a pattern is apparent (the same issue keyword in 3+ entries, or average rating
  below 3), tell the user (in Japanese):
  「過去のフィードバックで類似パターンを検出: [簡潔に]。`/skill-improve --skill my-skill-factory` で改善案を分析できます。」
- Continue with normal execution either way.

If `feedback/log.md` does not exist, skip silently.

## Ecosystem Check

Run on every invocation, right after Feedback Check. Feedback Check only learns from
this skill's own past runs; this check notices when the *ecosystem* moved (Claude Code
or Codex releases, model launches, skill-spec changes), which no feedback entry would
ever surface.

```bash
cd <repo-root>
python my-skill-factory/scripts/ecosystem_check.py
```

- `"due": false` → continue silently. The whole check is two `--version` calls.
- `"due": true`, or the user asked to "refresh" → read `references/ecosystem-refresh.md`,
  launch its research brief as a **background** subagent, tell the user (in Japanese)
  「エコシステムの更新を検出 ([reasons])。最新の作法をバックグラウンドで調査します。」,
  and start Step 1 without waiting.
- The proposals are triaged at the start of Step 2 — **every item needs the user's
  approval, even in auto-mode** — and written back only after Step 5, as a separate
  commit. The protocol file has both procedures.

## Step 1: Gather Requirements

Ask the user in this order — **architecture before stack**:

**Architecture questions (always ask unless the user has already answered):**
- What should the skill do? Get 2-3 concrete usage examples.
- What triggers it? (e.g., "review PR", "create diagram")
- For any external API/SDK/service: which auth mode? If multiple modes exist,
  default to the one that avoids billing (e.g., subscription vs API-key).
  Surface billing implications upfront — they often drive the entire design.
- Sync (block until done) or async (return turn-id / handle quickly, observe
  progress separately)? For any operation that may exceed 2 minutes, async is
  usually right.
- Batch (one-shot) or streaming (incremental output)?
- User-facing names/labels (skill name, command name, default output path,
  default model name): always confirm before writing files. A judgment call
  about a public-facing label is never "low-risk."

**Stack/runtime questions (after architecture is clear):**
- Does it need external tools? (gh CLI, APIs, MCP servers)
- What output format? (markdown report, file creation, GitHub actions)
- Runtime preference? (deno > bun > Node+pnpm+tsx, unless the user specifies
  otherwise.)

Ask as many clarifying questions as you need. Auto-mode's "minimize
interruptions" does NOT apply to (a) user-visible names/labels and (b)
architectural Q&A — these questions are cheap and avoid expensive rework
cycles. Skip a question only when the user has explicitly answered it
in their initial request.

### Formalize as BDD scenarios

After gathering requirements, write 3-5 Given/When/Then scenarios covering:
1. Primary use case
2. One or two secondary paths
3. An edge case (missing info, invalid input)

Read `references/bdd-skill-scenarios.md` for templates by skill type and anti-patterns.

## Step 2: Design the Skill

Read `references/skill-design-guide.md` for design patterns and structure guidance.

Read `references/ecosystem-practices.md` (WHEN TO READ: every Step 2 — it is kept
compact) together with any proposals approved in this run's Ecosystem Check, and
apply the items relevant to this skill: model usage, token cost, agent usage,
authoring rules, Codex compatibility. Where a practice there contradicts older
guidance in this file, the practice wins — it carries a newer `verified` date and a
primary source.

Decide:
- **Freedom level**: High (text guidance) vs Low (exact scripts)
- **References needed?** Detailed checklists, schemas, examples → put in `references/`
- **Scripts needed?** Deterministic operations → put in `scripts/`
- **Assets needed?** Templates, images → put in `assets/`
- **Improvement loop level**: Read `references/skill-improvement-guide.md`. Assess: will this skill be used >5 times? Does it have a complex multi-phase workflow? Choose None / Observe / Full accordingly. If Observe or Full, add the Retrospective and/or Feedback Check sections from the guide's templates.
- **Token-cost contract**: plan the SKILL.md body's load cost (always
  loaded on trigger — aim for ≤5k tokens on invoke, standing rules first),
  then *measure* it after install with
  `claude plugin details <skill-name>@hideki-plugins`. Mark every `references/` file with
  explicit "WHEN TO READ: ..." guidance so it stays at 0 tokens during
  normal execution. BDD scenarios, long worked examples, and detailed
  protocol docs must NOT be auto-loaded — they live behind explicit
  WHEN TO READ gates. Before writing files, confirm: which references
  count toward routine token cost, which don't?
- **Scenario mapping**: Map each BDD scenario to SKILL.md sections (trigger context → frontmatter, workflow → body, outputs → format/references)

## Step 3: Team Orchestration Assessment

Determine whether the skill being created should have a built-in multi-agent team review step in its own workflow.

### Quick Assessment

Evaluate the target skill against these criteria:
- Does it have a multi-phase workflow where design decisions affect later phases?
- Does it touch cross-cutting concerns (security, performance, architecture)?
- Would multiple stakeholder perspectives improve its output quality?
- Does it modify code, infrastructure, or shared resources?
- Could wrong output from this skill cause significant rework?

If **2+ criteria** are true → the skill should include team orchestration. Proceed to the detailed design below.
If **0-1** → skip team orchestration for this skill. Proceed to Step 4.

### Design Team Perspectives (only when assessment warrants it)

Read `references/skill-design-review-team.md` for the full perspective catalog with prompts, output formats, and cross-skill delegation notes.

From the catalog, select which perspectives apply to the target skill. Include in the target skill's SKILL.md:
1. The sentence: "Create an agent team to explore this from different angles: [selected perspectives]"
2. A reference file under the target skill's `references/` with the detailed teammate prompts for the selected perspectives

Do NOT copy all perspectives — only include the ones relevant to the target skill's domain.

## Step 4: Create Skill Files

Create the skill directory at `<repo-root>/<skill-name>/` (see the "Paths" section above for what `<repo-root>` resolves to on each OS).

### SKILL.md frontmatter

```yaml
---
name: <skill-name>
description: <≤1,024 chars, third person. Key use case first, then the contexts that should trigger it.>
# plus the invocation fields chosen in Step 2 (see ecosystem-practices.md § Skill authoring)
---
```

The description is critical — it controls when the skill triggers, and it is the only
text Claude sees before loading the body. Keep it **≤1,024 characters**: Claude Code
truncates longer ones and drops rarely-used skills' descriptions when the listing
overflows, so extra trigger phrases get lost rather than helping. Include:
- What the skill does (1 sentence, the key use case first)
- The contexts/scenarios when to use it
- The few trigger phrases that best distinguish it from neighbouring skills

### SKILL.md body

- Use imperative form
- Keep under 500 lines (aim well under — see Token-cost contract in Step 2)
- Only include knowledge Claude doesn't already have
- Reference any `references/` files with explicit "WHEN TO READ: ..." guidance
  so they are not auto-loaded during normal execution
- **BDD scenarios default to `references/scenarios.feature`** (separate file,
  on-demand only, never auto-loaded). SKILL.md body should contain only a
  1-line pointer such as: `BDD spec lives in references/scenarios.feature.
  Read only when auditing or amending the skill; not needed for normal
  execution.` Inline BDD in the body is the exception requiring explicit
  justification (e.g., the skill itself is a 1-scenario utility).

### Supporting files

Place in subdirectories as needed:
- `references/` — Loaded by Claude on demand
- `scripts/` — Executed directly
- `assets/` — Used in output, not loaded into context

### Pre-install path-discipline check

Before installing, run the path-leak grep from the "Path discipline" section above on
the new skill's source directory. Any non-example hit (operator home, OS-specific root,
or a path assuming a particular clone location) must be replaced with a placeholder or
runtime resolution. Do this every time, including for re-installs of edited skills.

### Install into marketplace

**Always run the install script immediately after creating or updating skill files. Do not ask the user — just install.**

```bash
cd <repo-root>
python my-skill-factory/scripts/install_skill.py <skill-name>
```

For a specific version:

```bash
cd <repo-root>
python my-skill-factory/scripts/install_skill.py <skill-name> --version 1.1.0
```

The script handles everything:
- Creates marketplace plugin structure under `my-marketplace/plugins/<name>/`
- Registers in root `marketplace.json`
- Caches to `~/.claude/plugins/cache/hideki-plugins/<name>/<version>/`
- Adds entry to `installed_plugins.json`
- Enables in `settings.json`

Read `references/marketplace-structure.md` for full details on the file layout and JSON schemas.

### Commit and push

**Always commit and push immediately after installing. Do not ask the user — just do it.**

```bash
cd <repo-root>
git add <skill-name>/ my-marketplace/plugins/<skill-name>/ my-marketplace/.claude-plugin/marketplace.json
git commit -m "feat: add <skill-name> skill"
git push
```

## Step 5: Verify and Smoke Test

Also run the verification practices listed in `references/ecosystem-practices.md`
§ Skill authoring. They complement 5a/5b, not replace them.

**5a — Listing check.** Launch a new CLI session to confirm the skill is registered:

```bash
echo "List all available skills. Just list the skill names as a bullet list." | claude -p
```

The new skill should appear as `<skill-name>:<skill-name>` in the output.

**5b — Runtime smoke (REQUIRED before reporting the work complete).** Run the
skill end-to-end against real dependencies — code-only review and listing
checks miss runtime bugs in env scoping, SDK shape assumptions, regex
patterns, file system semantics, etc.

- **Wrapper skills (CLI / SDK / API):** execute at least one primary user
  flow against the actual external service. Verify the happy path returns
  expected output. Verify at least one error path produces a friendly
  message (e.g., missing auth, missing binary).
- **Pure-logic skills:** exercise the primary entry point with a
  representative input and inspect the result.
- **Utility skills:** trigger the skill via its actual invocation path and
  verify the side effect / output.

Any bug found during smoke is a "smoke-discovered fix" that should be
committed before reporting completion. Do not claim the work is done on
the strength of `claude -p` listing alone.

## Retrospective

After completing Step 5 (Verify) of either the Create or Update workflow, reflect on the
session:

1. Consider: were there mid-session corrections (rejected designs, dropped scope,
   plan changes), errors during install, missing pre-install checks, or scenarios
   discovered late?
2. Ask the user (in Japanese): 「今回の作成/更新のフィードバック (1-5の評価、気になった点、または何もなければEnter)」
   **If the user provides a rating < 5, ALWAYS follow up** with:
   「なぜその評価ですか？ (改善のために具体的に教えてください)」
   Record the response verbatim as `Rating reason`. A rating without the
   "why" loses the strongest improvement signal — never skip this followup
   for ratings 1-4, even in auto-mode.
3. If the user provides feedback OR if corrections/issues actually occurred:
   a. Create `feedback/` next to this SKILL.md if it does not exist (resolve the
      directory via `git rev-parse --show-toplevel` from this skill's source dir,
      then append `/my-skill-factory/feedback/`).
   b. Read `feedback/log.md` (create with `# Feedback Log` header followed by a
      blank line and the comment
      `<!-- Append new entries at the top. Do not edit previous entries. -->`
      if it does not exist).
   c. Prepend a new entry directly after the header, using the format from
      `references/skill-improvement-guide.md`:

      ```markdown
      ## <ISO-8601 timestamp>
      - **Skill Version**: <version from this file's frontmatter>
      - **Task**: <which target skill, create or update, brief description>
      - **Outcome**: success | partial-success | failure | error
      - **Rating**: <N>/5 (or "—" if not provided)
      - **Rating reason**: <user's verbatim response to the WHY follow-up, or "—" if rating was 5 or not provided>
      - **Corrections**: <mid-session corrections, or "none">
      - **Issues**: <specific problems, or "none">
      - **User Note**: <user's verbatim feedback, or "—">
      ---
      ```

   d. Confirm in one short Japanese sentence.
4. If the user skips AND no corrections or issues occurred, end without recording.

## Updating an Existing Skill

1. **Write scenarios for the change** — Define Given/When/Then scenarios for new or modified behavior
2. **Identify the delta** — Compare new scenarios against existing ones; classify as Added, Modified, or Removed
3. **Team assessment** — Re-evaluate if the updated skill should add, remove, or change team perspectives
4. **Edit skill files and install** — Update SKILL.md and supporting files, applying `references/ecosystem-practices.md` as in Step 2, then always run the install script immediately (it overwrites the previous installation)
5. **Commit and push** — `git add` the skill source dir, marketplace plugin dir, and marketplace.json, then `git commit -m "chore: update <skill-name> skill"` and `git push`
6. **Validate coverage** — Confirm each new scenario has corresponding content in SKILL.md
7. **Verify** — New sessions will pick up the changes automatically

If the update is motivated by feedback patterns, follow "Improving an Existing Skill" instead — it includes evidence-based analysis and amendment tracking.

## Improving an Existing Skill

Use `/skill-improve` to retrofit OIAE components and analyze feedback for existing skills. The `skill-improve` skill handles the full improvement workflow: retrofitting Retrospective/Feedback Check/version tracking, analyzing accumulated feedback, proposing evidence-based amendments, and evaluating previous amendments.

```
/skill-improve --skill <skill-name>
```

## Behavior Scenarios

BDD spec lives in `references/scenarios.feature`. Read only when auditing or amending
this skill (e.g. via `/skill-improve --skill my-skill-factory`); not needed for normal
execution.

## Deferred (tracked TODOs)

- [ ] **Impact scan of existing skills** — when a refresh retires or changes a practice
  (a deprecated model ID, a frontmatter change), grep `<repo-root>/*/SKILL.md` for the
  affected skills and suggest `/skill-improve --skill <name>` for each. Deferred: scoped
  out of v1.2.0 by the user (2026-09-30); natural home is a new write-back step in
  `references/ecosystem-refresh.md`.
- [ ] **Refresh independent of factory runs** — a scheduled routine (`/schedule`) so the
  knowledge base stays current during weeks when no skill is built. Deferred: v1.2.0
  piggybacks on factory runs only.
- [ ] **Codex-native research path** — under Codex there is no background subagent, so
  a due refresh is skipped without `record`. Deferred until Codex offers an equivalent.

## References

- `references/skill-design-guide.md` — Quick reference for skill structure, freedom levels, patterns, and what to include/exclude
- `references/bdd-skill-scenarios.md` — Given/When/Then templates by skill type, update-delta guidance, and anti-patterns
- `references/marketplace-structure.md` — Full directory layout, JSON schemas, and config file locations for the local marketplace
- `references/skill-design-review-team.md` — Perspective catalog: available team angles, prompts, output formats, and cross-skill delegation (loaded only when assessment warrants team orchestration)
- `references/skill-improvement-guide.md` — OIAE cycle protocol, feedback log format, amendment format, pattern detection heuristics, and Retrospective/Feedback Check templates for generated skills
- `references/ecosystem-practices.md` — Living knowledge base of current Claude Code / Codex / model / authoring practices, each item sourced and dated. **WHEN TO READ**: every Step 2 (and step 4 of an update)
- `references/ecosystem-refresh.md` — Ecosystem Refresh protocol: research brief, triage, write-back. **WHEN TO READ**: only when `ecosystem_check.py` reports due, or the user asks to refresh
- `references/scenarios.feature` — BDD spec for this skill. **WHEN TO READ**: only when auditing or amending the factory itself
