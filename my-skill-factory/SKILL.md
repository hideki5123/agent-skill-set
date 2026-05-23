---
name: my-skill-factory
version: 1.1.0
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

Decide:
- **Freedom level**: High (text guidance) vs Low (exact scripts)
- **References needed?** Detailed checklists, schemas, examples → put in `references/`
- **Scripts needed?** Deterministic operations → put in `scripts/`
- **Assets needed?** Templates, images → put in `assets/`
- **Improvement loop level**: Read `references/skill-improvement-guide.md`. Assess: will this skill be used >5 times? Does it have a complex multi-phase workflow? Choose None / Observe / Full accordingly. If Observe or Full, add the Retrospective and/or Feedback Check sections from the guide's templates.
- **Token-cost contract**: estimate the SKILL.md body's load cost (always
  loaded on trigger — aim small). Mark every `references/` file with
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
description: <What it does + ALL trigger phrases. This is the only text Claude sees before loading the skill body.>
---
```

The description is critical — it controls when the skill triggers. Include:
- What the skill does (1 sentence)
- All contexts/scenarios when to use it
- Specific trigger phrases

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
4. **Edit skill files and install** — Update SKILL.md and supporting files, then always run the install script immediately (it overwrites the previous installation)
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

```gherkin
Scenario: Create a new skill from scratch
  Given the user has a clear idea for a new skill
  When the user says "create a skill for X"
  Then the skill gathers requirements, writes BDD scenarios, designs structure,
       assesses whether team orchestration is needed, includes team perspectives
       if warranted, creates files, installs, commits and pushes, and verifies

Scenario: Skill assessed as needing team orchestration
  Given the user wants a skill with a multi-phase workflow touching security and architecture
  When the assessment finds 2+ criteria are true
  Then the skill includes a "Create an agent team..." step with selected perspectives
       and a references file with detailed teammate prompts

Scenario: Skill assessed as NOT needing team orchestration
  Given the user wants a simple single-step utility skill
  When the assessment finds 0-1 criteria are true
  Then team orchestration is skipped and no team review step is included in the skill

Scenario: Update an existing skill
  Given a skill is already installed in the marketplace
  When the user says "update the X skill to add Y"
  Then the skill writes change-delta scenarios, identifies added/modified/removed behaviors, edits files, always re-installs immediately without asking, commits and pushes, and verifies

Scenario: Vague request
  Given the user provides only a one-line idea without details
  When the user says "make me a skill"
  Then the skill asks 2-3 focused questions to clarify purpose, triggers, and output format

Scenario: Skill with external dependencies
  Given the user needs a skill that relies on CLI tools or MCP servers
  When the user describes the skill's requirements
  Then the skill identifies dependencies, documents them in SKILL.md, and includes setup guidance

Scenario: Re-install without changes
  Given a skill's files have not changed
  When the user re-runs the install script
  Then the script overwrites the previous installation and the skill remains functional

Scenario: Feedback Check surfaces a recurring pattern in the factory itself
  Given my-skill-factory/feedback/log.md has 5+ entries with a common issue keyword in 3+
  When the factory is invoked
  Then it tells the user about the pattern and suggests
       /skill-improve --skill my-skill-factory, then continues normally

Scenario: Retrospective recorded after a run with corrections
  Given the user rejected the initial design and asked for a different approach mid-run
  When the workflow completes
  Then the factory asks for a 1-5 rating in Japanese, creates feedback/log.md if missing,
       and prepends an entry capturing the corrections, the user's note, and the outcome

Scenario: Retrospective skipped on a clean run
  Given the run had no corrections, no issues, and the user provides no feedback
  When the workflow completes
  Then the factory ends without writing to feedback/log.md

Scenario: New skill must not contain hardcoded absolute paths
  Given the user is creating or editing a skill
  When the factory writes any of the skill's SKILL.md, references, or scripts
  Then no operator-specific path (/Users/..., /home/..., C:\..., D:\..., /private/...)
       appears in the skill's content except as an explicit documentation example
  And before install, the path-discipline grep is run and any non-example hits are
       replaced with <repo-root>, ~, $HOME, or runtime resolution

Scenario: Improve a skill based on feedback
  Given a skill has feedback/log.md with recurring failure patterns
  When the user says "improve skill X" or "fix skill X based on feedback"
  Then the factory reads all feedback, identifies patterns, proposes targeted amendments
       with evidence, applies approved changes, records in amendments.md, and re-installs

Scenario: Evaluate previous amendments
  Given a skill has amendments with status "applied — monitoring"
  When the factory's improve workflow runs
  Then it checks post-amendment feedback, updates amendment status to effective/ineffective,
       and suggests rollback for ineffective amendments

Scenario: Skill has no feedback yet
  Given a skill's feedback/ directory does not exist or log.md is empty
  When the user asks to improve the skill
  Then the factory reports no feedback data and suggests running the skill a few times first
```

## References

- `references/skill-design-guide.md` — Quick reference for skill structure, freedom levels, patterns, and what to include/exclude
- `references/bdd-skill-scenarios.md` — Given/When/Then templates by skill type, update-delta guidance, and anti-patterns
- `references/marketplace-structure.md` — Full directory layout, JSON schemas, and config file locations for the local marketplace
- `references/skill-design-review-team.md` — Perspective catalog: available team angles, prompts, output formats, and cross-skill delegation (loaded only when assessment warrants team orchestration)
- `references/skill-improvement-guide.md` — OIAE cycle protocol, feedback log format, amendment format, pattern detection heuristics, and Retrospective/Feedback Check templates for generated skills
