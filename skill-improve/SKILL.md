---
name: skill-improve
version: 1.2.0
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

# Skill Improve (orchestrator)

Retrofit the OIAE (Observe/Inspect/Amend/Evaluate) self-improvement loop to existing skills and analyze accumulated feedback to propose evidence-based amendments.

## Role definition lives in the subagent

The auditor **judgment** — OIAE opt-in level assessment, retrofit content
generation, path-discipline grep, feedback pattern detection, amendment
proposal text, and previous-amendment evaluation — lives in the
`@agent-skill-improve:skill-improve` subagent.

This skill is the **orchestrator**: it resolves the target skill path,
hands the bundle (SKILL.md, references, feedback log, amendments file) to
the subagent, presents the subagent's proposals to the user for approval,
applies approved amendments, runs the install script, performs the smoke
check, and commits/pushes.

Use this skill when running the full retrofit + amendment cycle. Use
`@agent-skill-improve:skill-improve` directly when another agent just
needs the auditor judgment without the install/commit flow.

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

6. **Smoke check (REQUIRED before reporting completion).** Verify the
   retrofitted skill actually loads:
   - `claude -p` listing confirms `<skill-name>:<skill-name>` is present in
     a fresh session.
   - Frontmatter `version` field reads as the value just written.
   - Path-discipline grep over the source dir still returns no non-example
     hits.

   Code-only review is NOT sufficient — a typo in the new Retrospective
   section, a malformed frontmatter, or a missed path leak only surfaces
   when the skill is actually loaded. Treat any issue found here as a
   smoke-discovered fix to commit before reporting completion.

7. Commit and push:
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

9. **Install**:
   ```bash
   cd <repo-root>
   python my-skill-factory/scripts/install_skill.py <skill-name>
   ```

10. **Smoke check (REQUIRED before commit/push).** Verify the amended skill
    actually loads:
    - `claude -p` listing confirms `<skill-name>:<skill-name>` is present
      in a fresh session.
    - Frontmatter `version` field reads as the bumped value.
    - Path-discipline grep over the source dir returns no non-example hits.
    - For amended skills that have scripts/lib (e.g., deno-backed wrapper
      skills), the script files at least syntactically parse / type-check
      via a dry `--check` or equivalent (where the runtime supports it).

    If smoke fails, fix the underlying issue and re-install before
    committing. Never ship an amendment that fails its own smoke check —
    that's exactly the regression class AMD-003 is preventing.

11. **Commit and push**:
    ```bash
    cd <repo-root>
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
   **If the user provides a rating < 5, ALWAYS follow up** with:
   「なぜその評価ですか？ (改善のために具体的に教えてください)」
   Record the response verbatim as `Rating reason`. A rating without the
   "why" loses the strongest improvement signal — never skip this follow-up
   for ratings 1-4, even in auto-mode.
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
      - **Rating reason**: <user's verbatim response to the WHY follow-up, or "—" if rating was 5 or not provided>
      - **Corrections**: <mid-session corrections, or "none">
      - **Issues**: <specific problems, or "none">
      - **User Note**: <user's verbatim feedback, or "—">
      ---
      ```

   d. Confirm in one short Japanese sentence.
4. If the user skips AND no corrections or issues occurred, end without recording.

## Behavior Scenarios

BDD spec lives in `references/scenarios.feature`. Read only when auditing or
amending this skill (e.g., via `/skill-improve --skill skill-improve`); **not
needed for normal execution**.

## References

Read these on-demand only — they are not auto-loaded.

- `references/scenarios.feature` — Gherkin BDD spec for this skill.
  **WHEN TO READ**: only when auditing or amending the skill itself (e.g.,
  via `/skill-improve --skill skill-improve`). Never during normal execution.
- `references/retrofit-checklist.md` — Step-by-step checklist for adding OIAE
  components with placement rules. **WHEN TO READ**: only in Phase 2
  (retrofit) when OIAE components are missing from the target skill.
- `my-skill-factory/references/skill-improvement-guide.md` — OIAE protocol,
  log format, amendment format, templates, pattern detection heuristics.
  **WHEN TO READ**: in Phase 2 when looking up template wording, and in
  Phase 3 when applying pattern-detection heuristics or formatting an
  amendments.md entry.
