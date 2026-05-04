---
name: skill-improve
version: 1.0.0
description: >
  Retrofit the OIAE self-improvement loop to existing skills and analyze feedback
  to propose evidence-based amendments. Adds Retrospective, Feedback Check, and
  version tracking to skills that lack them. Reads feedback/log.md to identify
  recurring issues and propose targeted skill improvements. Use when the user
  asks to improve a skill, retrofit feedback to a skill, add the improvement loop,
  fix a skill based on feedback, or analyze skill performance. Trigger phrases
  include "improve skill", "retrofit skill", "add feedback loop", "skill keeps failing",
  "fix skill", "analyze skill feedback", "skill performance", "add retrospective",
  "skill improvement".
---

# Skill Improve

Retrofit the OIAE (Observe/Inspect/Amend/Evaluate) self-improvement loop to existing skills and analyze accumulated feedback to propose evidence-based amendments.

## Paths

Examples below use `<repo-root>` for the user's local clone of the skill repository.
Resolve once per session:

- macOS / Linux: typically `~/private/repos/agent-skill-set`
- Windows: typically `D:\Shared\agents\my-skills`
- Otherwise: ask the user, or run `git -C <any-skill-dir> rev-parse --show-toplevel`.

`install_skill.py` auto-detects the repo via `git rev-parse --show-toplevel`, so once you
`cd <repo-root>` you can invoke it with forward-slash relative paths on any platform.

## Path discipline (applies to every retrofit and amendment)

When this skill writes new content into an existing skill (Retrospective, Feedback Check,
amendments, file-path references), **never introduce hardcoded operator-specific or
OS-specific absolute paths**. Forbidden patterns: `/Users/<name>/...`, `/home/<name>/...`,
`C:\Users\<name>\...`, `D:\Shared\...`, `/private/...`, or any path that assumes the skill
repo lives at one specific location.

Use `<repo-root>` (the skill repo root, see "Paths" above), `~` / `$HOME`, or runtime
resolution (`git rev-parse --show-toplevel`) instead. Concrete paths are allowed only as
explicitly-framed documentation examples ("on Windows this typically resolves to `D:\...`").

**Pre-install verification.** Before running `install_skill.py` after a retrofit or
amendment, grep the modified skill's source for path leaks:

```bash
grep -rn -e '/Users/' -e '/home/' -e '/private/' -e 'C:\\' -e 'D:\\' \
  <repo-root>/<skill-name>/ --exclude-dir=feedback
```

Each remaining hit must be either an example explicitly framed as such, or replaced with
a placeholder / runtime resolution. Apply this check whether the change came from the
retrofit Phase 2 or from an evidence-driven amendment in Phase 3.

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--skill` | (required) | Skill name or path to the skill directory |
| `--retrofit-only` | `false` | Only add OIAE components, skip feedback analysis |
| `--analyze-only` | `false` | Only analyze feedback, skip retrofit |

## Workflow

### Feedback Check

Before starting Phase 1, look for accumulated feedback on this skill itself:

- If `feedback/log.md` exists next to this SKILL.md and has 5 or more entries, read the
  last 10.
- If a pattern is apparent (the same issue keyword in 3+ entries, or average rating
  below 3), tell the user (in Japanese):
  「過去のフィードバックで類似パターンを検出: [簡潔に]。`/skill-improve --skill skill-improve` で改善案を分析できます (=自分自身を分析)。」
- Continue with normal execution either way.

If `feedback/log.md` does not exist, skip silently.

### Phase 1: Locate and Read the Skill

1. Resolve skill path:
   - If a name is given, check `<repo-root>/<skill-name>/`
   - If a path is given, use it directly
   - Read the skill's SKILL.md

2. Check for existing OIAE components:
   - `version:` field in frontmatter
   - `### Retrospective` section in body
   - `### Feedback Check` section in body
   - `feedback/` directory existence

3. Check for existing feedback:
   - `feedback/log.md` — does it exist? How many entries?
   - `feedback/amendments.md` — any pending amendments?

4. Report current state to user:
   > "Skill `<name>`: version [present/missing], Retrospective [present/missing], Feedback Check [present/missing], feedback entries: N"

### Phase 2: Retrofit (if components missing)

Skip this phase if `--analyze-only` is set or all OIAE components are already present.

Read `references/retrofit-checklist.md` for the step-by-step process and placement rules.

1. Assess opt-in level (None / Observe / Full):
   - **Full**: Skill has a multi-phase workflow, expected >5 uses, complex output
   - **Observe**: Uncertain usage frequency, simpler workflow
   - **None**: One-shot skill, CLI wrapper, deterministic utility

2. Present assessment to user:
   > "I recommend [level] for this skill because [reason]. Proceed?"

3. Add missing components using templates from `my-skill-factory/references/skill-improvement-guide.md`:
   - Add `version: 1.0.0` to frontmatter if missing
   - Add `### Feedback Check` section (Full level only)
   - Add `### Retrospective` section (Observe or Full level)

4. Run the path-discipline grep from "Path discipline" above on the skill's source dir
   and replace any non-example hits with placeholders or runtime resolution.

5. Run the install script:
   ```bash
   cd <repo-root>
   python my-skill-factory/scripts/install_skill.py <skill-name>
   ```

6. Commit and push:
   ```bash
   cd <repo-root>
   git add <skill-name>/ my-marketplace/plugins/<skill-name>/ my-marketplace/.claude-plugin/marketplace.json
   git commit -m "chore: retrofit OIAE improvement loop to <skill-name> skill"
   git push
   ```

### Phase 3: Analyze Feedback (if log.md exists)

Skip this phase if `--retrofit-only` is set or no `feedback/log.md` exists.

Read `my-skill-factory/references/skill-improvement-guide.md` for pattern detection heuristics and amendment format.

1. **Evaluate previous amendments** — If `feedback/amendments.md` exists with entries in `applied — monitoring` status:
   - Read log entries dated after the amendment
   - Check if the specific issue pattern recurred
   - Check if ratings improved
   - Update status to `effective`, `ineffective`, or `insufficient data`
   - For ineffective amendments, suggest `git revert <commit>`

2. **Read all feedback** — Read `feedback/log.md` in full

3. **Identify patterns** using these heuristics:
   - Same issue keyword in Corrections/Issues across 3+ entries → recurring problem
   - Average rating below 3.0 over last 10 entries → general underperformance
   - Declining ratings over time → skill degrading
   - Outcome distribution >30% partial-success or failure → structural issues
   - Issues clustering after a version bump → recent amendment may have caused problems

4. **Read current skill** — SKILL.md + relevant references to understand current instructions

5. **Propose amendments** — For each identified pattern:
   - What to change (file path, section)
   - Why (cite specific feedback entries by date as evidence)
   - The proposed text change
   - Suggested version bump (patch or minor)

6. **Present to user** — Show all proposed amendments with supporting evidence for approval

7. **Apply approved changes**:
   - Edit the skill files
   - Bump version in frontmatter
   - Run the path-discipline grep from "Path discipline" above on the modified skill;
     replace any non-example hits with placeholders or runtime resolution.

8. **Record amendment** — Append to `feedback/amendments.md` using format from `my-skill-factory/references/skill-improvement-guide.md`

9. **Install and commit**:
   ```bash
   cd <repo-root>
   python my-skill-factory/scripts/install_skill.py <skill-name>
   git add <skill-name>/ my-marketplace/plugins/<skill-name>/ my-marketplace/.claude-plugin/marketplace.json
   git commit -m "fix: improve <skill-name> skill based on feedback (AMD-NNN)"
   git push
   ```

### Phase 4: Report

Summarize what was done:
- OIAE components retrofitted (if any)
- Previous amendments evaluated (status updates)
- Patterns found in feedback (if any)
- Amendments applied (if any)
- Current skill version

### Retrospective

After Phase 4 (Report) completes, reflect on this run of skill-improve itself:

1. Consider: were there mid-session corrections (rejected amendments, scope changes,
   wrong target skill, install/commit failures, missed path leaks)?
2. Ask the user (in Japanese): 「今回の改善作業のフィードバック (1-5の評価、気になった点、または何もなければEnter)」
3. If the user provides feedback OR if corrections/issues actually occurred:
   a. Create `feedback/` next to this SKILL.md if it does not exist (resolve the
      directory via `git rev-parse --show-toplevel` from this skill's source dir,
      then append `/skill-improve/feedback/`).
   b. Read `feedback/log.md` (create with `# Feedback Log` header followed by a
      blank line and the comment
      `<!-- Append new entries at the top. Do not edit previous entries. -->`
      if it does not exist).
   c. Prepend a new entry directly after the header, using the format from
      `my-skill-factory/references/skill-improvement-guide.md`:

      ```markdown
      ## <ISO-8601 timestamp>
      - **Skill Version**: <version from this file's frontmatter>
      - **Task**: <which target skill, retrofit / analyze / both>
      - **Outcome**: success | partial-success | failure | error
      - **Rating**: <N>/5 (or "—" if not provided)
      - **Corrections**: <mid-session corrections, or "none">
      - **Issues**: <specific problems, or "none">
      - **User Note**: <user's verbatim feedback, or "—">
      ---
      ```

   d. Confirm in one short Japanese sentence.
4. If the user skips AND no corrections or issues occurred, end without recording.

## Behavior Scenarios

```gherkin
Scenario: Retrofit OIAE to skill without feedback loop
  Given an existing skill has no Retrospective, Feedback Check, or version field
  When /skill-improve --skill <name> is invoked
  Then assess opt-in level, present to user, add missing OIAE components,
       install, commit, and push

Scenario: Analyze feedback and propose amendments
  Given a skill has feedback/log.md with recurring issues
  When /skill-improve --skill <name> is invoked
  Then read all feedback, identify patterns, propose amendments with evidence,
       apply approved changes, record in amendments.md, install, commit, and push

Scenario: Skill already has OIAE and no feedback yet
  Given a skill has Retrospective and Feedback Check but no feedback/log.md
  When /skill-improve --skill <name> is invoked
  Then report that OIAE components are present but no feedback data exists yet,
       and suggest running the skill a few times to collect data

Scenario: Evaluate previous amendments
  Given a skill has amendments in "applied — monitoring" status
  When /skill-improve --skill <name> is invoked
  Then check post-amendment feedback entries, update amendment status
       to effective or ineffective, and suggest rollback if ineffective

Scenario: Retrofit-only mode
  Given --retrofit-only flag is set
  When /skill-improve --skill <name> --retrofit-only is invoked
  Then only add missing OIAE components, skip feedback analysis

Scenario: Analyze-only mode
  Given --analyze-only flag is set and feedback exists
  When /skill-improve --skill <name> --analyze-only is invoked
  Then only analyze feedback and propose amendments, skip retrofit

Scenario: Feedback Check surfaces a recurring pattern in skill-improve itself
  Given skill-improve/feedback/log.md has 5+ entries with a common issue keyword in 3+
  When /skill-improve is invoked on any target
  Then it tells the user about the pattern and suggests
       /skill-improve --skill skill-improve, then continues normally on the requested target

Scenario: Retrospective recorded after a run with corrections
  Given the user rejected a proposed amendment or course-corrected mid-run
  When Phase 4 (Report) completes
  Then skill-improve asks for a 1-5 rating in Japanese, creates feedback/log.md if missing,
       and prepends an entry capturing the corrections, the user's note, and the outcome

Scenario: Retrospective skipped on a clean run
  Given the run had no corrections, no issues, and the user provides no feedback
  When Phase 4 (Report) completes
  Then skill-improve ends without writing to feedback/log.md

Scenario: Retrofits and amendments must not introduce hardcoded paths
  Given the skill is being retrofitted with OIAE components or amended based on feedback
  When new content is written into the target skill's SKILL.md, references, or scripts
  Then no operator-specific path (/Users/..., /home/..., C:\..., D:\..., /private/...)
       appears in the new content except as an explicit documentation example
  And before install, the path-discipline grep is run and any non-example hits are
       replaced with <repo-root>, ~, $HOME, or runtime resolution
```

## References

- `references/retrofit-checklist.md` — Step-by-step checklist for adding OIAE components with placement rules
- `my-skill-factory/references/skill-improvement-guide.md` — OIAE protocol, log format, amendment format, templates, pattern detection heuristics
