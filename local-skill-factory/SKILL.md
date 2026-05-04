---
name: local-skill-factory
description: >
  Create project-local Claude Code skills (.claude/commands/) in any project directory.
  Analyzes the project's tech stack, structure, and conventions, then generates
  tailored local skills (custom slash commands) scoped to that project.
  Like /my-skill-factory but output stays local — no marketplace installation.
  Trigger patterns:
  - local skill / local command / project skill / project command
  - create local skill / make local skill / add local command
  - "make a skill for this project" / "create command for this repo"
  - suggest skills / suggest commands / what skills would help
  - update local skill / edit local command / modify project skill
  - /local-skill-factory
version: 1.0.0
improvement_loop: observe
---

# Local Skill Factory

Create project-scoped Claude Code commands (`.claude/commands/`) in any project directory. Analyzes the project first, then generates tailored skills that live only in that project.

## Constraints

- Output goes to `<project-dir>/.claude/commands/<name>.md` — never to the marketplace
- Always analyze the project before creating a skill — understand the tech stack, structure, and conventions
- Use `$ARGUMENTS` placeholder in commands for user input
- Keep command files focused — one responsibility per command
- Do NOT commit or push to git unless the user asks
- Do NOT create CLAUDE.md unless the user asks or the skill specifically needs project-wide instructions
- Read `references/local-command-format.md` for the exact file format, patterns, and examples

## Path discipline (applies to every command you generate)

When writing the body of a generated `.claude/commands/<name>.md`, **never embed
hardcoded operator-specific or OS-specific absolute paths**. Generated commands are
checked into the project and run on every teammate's machine — paths like
`/Users/<your-name>/...` or `D:\Shared\...` break the moment anyone else uses them.

Forbidden in generated command bodies (and in any `references/`, `scripts/`, or
`assets/` you produce alongside them):

- Operator home paths: `/Users/<name>/...`, `/home/<name>/...`, `C:\Users\<name>\...`.
- Machine-specific roots: `D:\...`, `/private/...`, `/mnt/<host>/...`.
- Any path that assumes a specific clone location or development machine.

Use instead:

- `$ARGUMENTS` for user-supplied input.
- **Project-relative paths from the project root** (no leading `/`), e.g. `src/lib/foo.ts`.
- `~` or `$HOME` when a path inside the user's home is genuinely required.
- Runtime resolution (`git rev-parse --show-toplevel`, `$(pwd)`) when the project
  root is needed inside a script.
- Documentation examples that show a concrete path **must** be clearly framed as
  examples ("for example, on macOS this typically resolves to `~/...`"), not as
  the authoritative path.

**Pre-save verification.** Before writing the generated file, grep its contents (and
any companion files) for path leaks and clean up any non-example hits:

```bash
grep -nE '/Users/|/home/|/private/|D:\\\\|C:\\\\' \
  "<project-dir>/.claude/commands/<name>.md"
```

Each remaining hit must either be (a) a documentation example explicitly framed as
"example" or "typically", or (b) replaced with `$ARGUMENTS`, a project-relative path,
`~`/`$HOME`, or runtime resolution. Anything else is a bug — fix it before saving.

## Workflow

### Step 1: Analyze Project

Before creating any skill, understand the project:

1. **Read key files** to identify the tech stack:
   - `package.json`, `*.csproj`, `*.sln`, `Cargo.toml`, `go.mod`, `pyproject.toml`, `Gemfile`, `pom.xml`, `build.gradle`
   - `docker-compose.yml`, `Dockerfile`, `.github/workflows/`
   - Existing `CLAUDE.md`, `.claude/commands/`, `.claude/settings.json`
2. **Scan directory structure** — `ls` the top-level and key subdirectories
3. **Identify conventions** — naming patterns, test framework, linting config, CI/CD
4. **Note existing local skills** — check `.claude/commands/` to avoid duplicates

Summarize findings in 3-5 bullet points before proceeding.

### Step 2: Gather Requirements

If the user described what they want, confirm understanding. If vague, ask 2-3 focused questions:

1. What should the skill do? (give 1-2 concrete examples of use)
2. What triggers it? (example phrases or slash command name)
3. What's the output? (code changes, terminal output, report, file creation?)

Skip if the user already provided enough detail.

### Step 3: Write BDD Scenarios

Write 3-5 Given/When/Then scenarios covering:
1. Primary use case
2. One secondary path
3. An edge case

```gherkin
Scenario: <descriptive name>
  Given <project context>
  When <user invokes the command>
  Then <what the command produces>
```

### Step 4: Design the Command

Decide:
- **Command name** — short, descriptive, kebab-case (becomes `/project:<name>`)
- **Arguments** — what `$ARGUMENTS` represents
- **Complexity** — single file vs needs CLAUDE.md integration
- **Project-specific content** — what conventions, paths, tools to encode

Read `references/local-command-format.md` for format details and patterns.

### Step 5: Create Files

1. Create `.claude/commands/` directory if it doesn't exist:
   ```bash
   mkdir -p "<project-dir>/.claude/commands"
   ```

2. Write the command file at `<project-dir>/.claude/commands/<name>.md`

3. **Run the path-discipline grep** from the "Path discipline" section above on the
   newly written file (and any companion files under `.claude/`). Replace any
   non-example operator-specific or OS-specific path before continuing.

4. If the skill needs project-wide persistent instructions (rare), suggest updating CLAUDE.md

5. Confirm: "Created `/project:<name>` — try it with `/<name>` in this project."

### Step 6: Verify

List existing commands to confirm:
```bash
ls "<project-dir>/.claude/commands/"
```

Read back the created file to verify correctness.

## Suggesting Skills

When the user asks "suggest skills for this project" or isn't sure what to create:

1. Complete Step 1 (Analyze Project)
2. Based on the tech stack and structure, suggest from this catalog:

### Common Local Skill Patterns

| Project Type | Suggested Skills |
|-------------|-----------------|
| **Any project** | `review` (code review against conventions), `test` (run tests with context), `doc` (generate/update docs) |
| **Web frontend** (React, Vue, Angular, Svelte) | `component` (scaffold component), `style-guide` (enforce design system) |
| **.NET / C#** | `api-endpoint` (scaffold endpoint), `migration` (EF Core migration workflow), `build` (build + test + analyze) |
| **Node.js / TypeScript** | `api-route` (scaffold route), `lint-fix` (fix lint issues with context) |
| **Python** | `cli-command` (scaffold CLI command), `notebook` (create analysis notebook) |
| **Monorepo** | `package` (scaffold new package), `deps` (dependency analysis) |
| **DevOps / Infrastructure** | `deploy` (deployment checklist), `incident` (incident response template) |
| **API project** | `endpoint` (scaffold endpoint), `client` (generate API client), `test-api` (API integration tests) |

Present 3-5 most relevant suggestions with:
- Command name
- What it does (1 sentence)
- Example usage

Let the user pick which ones to create.

## Updating Existing Local Skills

When the user wants to modify a local skill:

1. Read the existing `.claude/commands/<name>.md`
2. Understand current behavior
3. Identify what changes (added, modified, removed)
4. Edit the file
5. Confirm changes

## Advanced: CLAUDE.md Integration

For skills that need persistent project context (not just a command):

- **CLAUDE.md** — project-wide instructions loaded every session
- **`.claude/commands/<name>.md`** — specific slash command

Example: A `review` command might need CLAUDE.md to define coding standards, while the command itself orchestrates the review workflow.

Only create/modify CLAUDE.md when:
- The skill needs conventions that apply to ALL interactions (not just this command)
- The project doesn't have a CLAUDE.md yet and would clearly benefit from one
- The user explicitly asks

## Retrospective

After completing the workflow, reflect on the execution session:

1. Consider: Were there mid-session corrections? Rejected outputs? Errors?
2. Ask the user: "Quick feedback on this run? (1-5 rating, note any issues, or press enter to skip)"
3. If the user provides feedback OR if corrections/issues occurred:
   a. Create `feedback/` directory next to this SKILL.md if it does not exist (resolve via `git rev-parse --show-toplevel` from the skill's own directory, or use the path the install script registered)
   b. Read `feedback/log.md` (create with `# Feedback Log` header if it does not exist)
   c. Prepend a new entry using the log format from the skill improvement guide
   d. Fill in: timestamp, skill version, task description, outcome, corrections, issues, user note
4. If the user skips AND no issues occurred, end without recording.

## Behavior Scenarios

```gherkin
Scenario: Create a new local skill for the current project
  Given the user is working in a project directory
  When the user describes what local skill they need
  Then analyze the project structure and tech stack,
       gather requirements, write BDD scenarios,
       create .claude/commands/<name>.md with a tailored prompt template,
       and confirm the skill is available as /project:<name>

Scenario: Suggest useful skills for the current project
  Given the user is working in a project but isn't sure what local skills would help
  When the user asks "suggest skills for this project"
  Then analyze the project type, structure, and workflows,
       and propose 3-5 relevant local skills with names, descriptions, and example usage

Scenario: Update an existing local skill
  Given a local skill already exists in .claude/commands/
  When the user wants to modify or extend it
  Then read the existing skill, identify changes needed,
       update the file, and confirm the modifications

Scenario: Project has no .claude directory yet
  Given the project directory has no .claude/commands/ structure
  When the user invokes the factory
  Then create the .claude/commands/ directory and the skill files

Scenario: Create complex skill with CLAUDE.md integration
  Given the local skill needs project-wide persistent context
  When the skill requires conventions beyond a single command file
  Then create the command file AND suggest or create relevant CLAUDE.md sections

Scenario: Generated command must not contain hardcoded absolute paths
  Given the user requests a new local skill
  When the factory writes the .claude/commands/<name>.md body or any companion file
  Then no operator-specific path (/Users/..., /home/..., C:\..., D:\..., /private/...)
       appears except as an explicit documentation example
  And before saving, the path-discipline grep is run and any non-example hits are
       replaced with $ARGUMENTS, a project-relative path, ~/$HOME, or runtime resolution
```
