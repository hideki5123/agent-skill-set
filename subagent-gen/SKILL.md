---
name: subagent-gen
description: >
  Generate a persistent PROJECT-KNOWLEDGE.md profile for any codebase that gives
  subagents instant deep domain expertise. Analyzes project structure, architecture,
  code conventions, tech stack, data flow, and domain concepts. The profile is
  designed to be loaded into Agent tool prompts so subagents can answer deep
  codebase questions like an expert teammate. Use when the user asks to profile
  a project, generate project knowledge, create a codebase profile, build a
  context pack, analyze a codebase for subagents, or says "profile this project".
  Trigger phrases include "profile project", "generate project knowledge",
  "codebase profile", "subagent context", "knowledge profile", "project profile",
  "profile this codebase", "build project knowledge", "create context pack",
  "generate codebase knowledge", "index this project", "make subagent",
  "generate subagent", "deep knowledge", "project expert".
---

# Subagent Knowledge Profile Generator

Generate a persistent PROJECT-KNOWLEDGE.md that captures deep domain knowledge
about a codebase, designed to fit in a subagent prompt context window.

## Arguments

Parse these from the user's invocation. All are optional with defaults:

| Argument | Default | Description |
|----------|---------|-------------|
| `--project` | cwd | Path to the project to profile |
| `--name` | (auto) | Profile name — used as filename in `~/.claude/knowledge/`. Auto-derived from manifest or directory name |
| `--output` | `~/.claude/knowledge/{name}.md` | Override the canonical output path |
| `--update` | `false` | Refresh an existing profile incrementally |
| `--depth` | `standard` | `quick` (~2K words), `standard` (~4K words), `deep` (~6K words) |
| `--focus` | `all` | Comma-separated subset: structure, architecture, conventions, domain |
| `--list` | `false` | List all available profiles in `~/.claude/knowledge/` and stop |

## Workflow

### Phase 0: List Profiles (if `--list`)

If `--list` is passed, list all `*.md` files in `~/.claude/knowledge/`:

```bash
ls -la ~/.claude/knowledge/*.md 2>/dev/null
```

For each file, parse the header line to extract project name, generation date, depth, and
source path. Display as a table:

| Profile | Generated | Depth | Source Path |
|---------|-----------|-------|-------------|
| {name} | {date} | {depth} | {path} |

Then stop — do not proceed to profiling.

### Phase 1: Identify Target Project

1. Use `--project` path or current working directory
2. Verify it contains source files (not empty or config-only)
3. **Derive `--name`** if not provided:
   - Read `package.json` → use `name` field
   - Read `pyproject.toml` → use `[project] name`
   - Read `Cargo.toml` → use `[package] name`
   - Fallback: use the directory basename, lowercased, hyphens for spaces
4. If `--update`, check for existing profile at `~/.claude/knowledge/{name}.md` first,
   then fall back to `.agent/local/PROJECT-KNOWLEDGE.md`
5. Read `.gitignore` to understand exclusion patterns

If the directory is empty or has no source files, report "No source files found" and stop.

### Phase 2: Reconnaissance (Inline)

Quick inline scan — no subagents needed. Gather metadata for Phase 3.

1. **Read root manifests**: Look for `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`,
   `pom.xml`, `build.gradle`, `*.sln`, `*.csproj`, `Gemfile`, `composer.json`, `mix.exs`,
   `CMakeLists.txt`, `Makefile`, `Dockerfile`, `docker-compose.yml`
2. **Directory tree**: Use Glob/Bash to map top 3 levels of the directory tree
3. **File census**: Count source files vs test files vs config files by extension
4. **Detect stack**: From manifests, identify:
   - Primary language(s) and version(s)
   - Framework(s)
   - Build system / package manager
   - Test runner(s)
   - Whether it's a monorepo (multiple package.json / workspace config)

Produce a **metadata block** in this format to pass to Phase 3 agents:

```
PROJECT METADATA
================
Name: {project name from manifest}
Path: {absolute path}
Language(s): {e.g., TypeScript 85%, Python 15%}
Framework(s): {e.g., Next.js 14, FastAPI}
Build: {e.g., pnpm, turborepo}
Test runner: {e.g., vitest, pytest}
Monorepo: {yes/no — packages: ...}
Source dirs: {e.g., src/, api/, packages/}
Test dirs: {e.g., __tests__/, tests/, e2e/}
File count: {e.g., 342 source, 89 test, 45 config}
```

### Phase 3: Parallel Deep Exploration

Read `references/exploration-dimensions.md` for the full pattern catalog for each dimension.

Spawn Explore-type subagents in parallel. Each agent receives:
- The project path
- The metadata block from Phase 2
- Its specific exploration instructions from the dimension catalog

#### Agent Configuration by Depth

**`--depth=quick`** — 2 agents:

| Agent | Combined Dimensions |
|-------|-------------------|
| structure-architecture | Structure + Architecture: directory layout, entry points, module boundaries, how modules connect, data flow, layering |
| conventions-domain | Conventions + Domain: naming patterns, error handling, key abstractions, API surface, config |

**`--depth=standard`** — 4 agents:

| Agent | Dimension |
|-------|-----------|
| structure-agent | Directory layout, entry points, module boundaries, build outputs |
| architecture-agent | Module connections, dependency graph, data flow, layering, state management |
| conventions-agent | Naming patterns, error handling, logging, validation, testing patterns |
| domain-agent | Business/domain concepts, key abstractions, API surface, configuration |

**`--depth=deep`** — 4 agents with expanded scope:
Same agents as standard, but each samples more files (20-30 instead of 10-15) and traces
deeper dependency chains. Architecture agent also maps middleware chains and plugin systems.

#### Agent Prompt Template

For each agent, construct a prompt like:

```
You are analyzing a codebase to build a deep knowledge profile.

PROJECT METADATA
================
{paste metadata block from Phase 2}

YOUR DIMENSION: {dimension name}
=================================
{paste the relevant section from references/exploration-dimensions.md}

INSTRUCTIONS:
- Explore the project at {project path}
- Follow the exploration patterns and grep signals listed above
- Sample {10-15 | 20-30} files across different directories
- For every finding, include the concrete file path and specific detail
- Do NOT include vague descriptions — every bullet must have a file path or function name
- Output your findings in the exact markdown format specified in the dimension catalog

Report back your findings as a structured markdown block.
```

#### Focus Filtering

If `--focus` is set to specific dimensions (e.g., `--focus=structure,domain`), only spawn agents
for those dimensions. Skip the others.

#### Monorepo Handling

If the project is a monorepo with multiple packages:
1. Ask the user which package(s) to profile, or whether to profile the root structure
2. If profiling specific packages, scope each agent's exploration to those package directories
3. If profiling root, focus on workspace config, shared utilities, and cross-package patterns

#### Large Project Handling (>5000 files)

1. Warn the user about project size
2. Suggest using `--focus` to narrow scope
3. Instruct agents to use sampling: read representative files from each directory rather than
   exhaustive scans
4. Cap the number of files each agent reads to 30

### Phase 4: Synthesize Profile

1. Collect findings from all agents
2. Read `references/profile-template.md` for the exact output structure
3. Merge agent findings into the template sections:
   - Structure agent → Identity + Structure sections
   - Architecture agent → Architecture section
   - Conventions agent → Conventions section
   - Domain agent → Domain Concepts + API Surface + Configuration sections
   - Tech Stack section is assembled from Phase 2 metadata + agent findings
4. Enforce word-count targets:
   - `quick`: ~2,000 words
   - `standard`: ~4,000 words
   - `deep`: ~6,000 words
5. Quality check — every bullet must contain at least one of:
   - A file path (e.g., `src/lib/api-client.ts`)
   - A function/class/type name (e.g., `DeviceService`)
   - A specific pattern name (e.g., "repository pattern")
   - A concrete value (e.g., "PostgreSQL 15", "port 3000")
6. Remove any vague or generic statements that Claude would already know from training

#### Update Mode Synthesis

When `--update` is active:
1. Read the existing profile
2. Identify sections marked with `<!-- USER: ... -->` — preserve these verbatim
3. Replace all other sections with fresh findings
4. Add a `Last updated:` timestamp
5. At the end, show a brief diff summary of what changed

### Phase 5: Save and Guide

#### 5a. Save to Global Store

1. Create `~/.claude/knowledge/` directory if it doesn't exist:
   ```bash
   mkdir -p ~/.claude/knowledge
   ```
2. Write the profile to `~/.claude/knowledge/{name}.md` (the canonical location)
3. If `--output` is explicitly set to a different path, write there instead

#### 5b. Create Local Symlink

1. Create `.agent/local/` in the project directory if it doesn't exist
2. Create a symlink so the profile is also accessible locally:
   ```bash
   # Unix/macOS
   ln -sf ~/.claude/knowledge/{name}.md .agent/local/PROJECT-KNOWLEDGE.md

   # Windows (requires Developer Mode)
   mklink ".agent\local\PROJECT-KNOWLEDGE.md" "%USERPROFILE%\.claude\knowledge\{name}.md"
   ```
3. If the symlink command fails (e.g., Windows without Developer Mode):
   - Fall back to copying the file
   - Warn the user: "Symlink failed — created a copy instead. Changes to
     one location won't automatically reflect in the other. Re-run with
     `--update` to refresh both."
4. Check `.gitignore` for `.agent/local/` — if missing, suggest adding:
   ```
   # AI agent local files
   .agent/local/
   ```

#### 5c. Present Summary

Show the user:
- Profile name and word count
- **Global path**: `~/.claude/knowledge/{name}.md` (accessible from any project)
- **Local path**: `.agent/local/PROJECT-KNOWLEDGE.md` (symlinked for convenience)
- 3-5 key findings highlights (most interesting/non-obvious things discovered)
- How to use the profile — read `references/prompt-integration-guide.md` and relay:
  - **Same project**: `Read .agent/local/PROJECT-KNOWLEDGE.md for context, then: <task>`
  - **Cross-project**: `Read ~/.claude/knowledge/{name}.md for context, then: <task>`
  - **List all profiles**: `/subagent-gen --list`

## Error Handling

| Situation | Behavior |
|-----------|----------|
| Empty directory / no source files | Report and stop |
| Monorepo detected | Ask user which packages to focus on |
| Very large project (>5000 files) | Warn, suggest `--focus`, use sampling |
| `--update` but no existing profile | Fall back to fresh generation |
| Agent exploration fails or times out | Report partial results, note incomplete dimensions |
| Unrecognized language/framework | Profile what can be inferred from file structure and naming |
| Symlink creation fails (Windows) | Copy the file instead, warn about manual sync |
| `--name` conflicts with existing profile | Ask user to confirm overwrite or choose a different name |
| `~/.claude/knowledge/` doesn't exist | Create it automatically |

## Behavior Scenarios

```gherkin
Scenario: Generate fresh profile for a standard project
  Given the user is in a project directory with source code and no existing profile
  When the user says "profile this project" or "generate project knowledge"
  Then the skill scans the project, launches parallel exploration agents,
  synthesizes findings into PROJECT-KNOWLEDGE.md, saves to .agent/local/,
  and shows how to use the profile in subagent prompts

Scenario: Update an existing profile after codebase changes
  Given a PROJECT-KNOWLEDGE.md already exists in .agent/local/
  When the user says "update project profile" or invokes with --update
  Then the skill reads the existing profile, focuses exploration on changed files,
  preserves user-customized sections (<!-- USER: ... -->), regenerates machine
  sections, and shows what changed

Scenario: Quick profile for a small task
  Given the user needs a lightweight profile fast
  When the user says "quick project profile" or invokes with --depth=quick
  Then the skill runs 2 combined agents, produces a ~2000-word profile,
  and completes faster than standard depth

Scenario: Profile a specific project path (not cwd)
  Given the user wants to profile a project in a different directory
  When the user says "profile project at D:\Projects\my-app"
  Then the skill uses the specified path as the project root for all exploration

Scenario: Very large monorepo project
  Given the project has over 5000 files or is a monorepo with multiple packages
  When the user invokes the skill
  Then the skill warns about size, asks which packages to focus on (if monorepo),
  uses sampling strategies to stay within token budget, and generates a profile
  scoped to the selected packages

Scenario: Use a profile from another project
  Given the user has profiled Project A and is now working in Project B
  When the user spawns a subagent with "Read ~/.claude/knowledge/project-a.md for context"
  Then the subagent has deep knowledge of Project A while working in Project B

Scenario: List all available profiles
  Given the user has generated profiles for multiple projects
  When the user says "list project profiles" or invokes with --list
  Then the skill lists all profiles in ~/.claude/knowledge/ with name, date, and source path
```

## References

- `references/exploration-dimensions.md` — Pattern catalog for each exploration dimension (what to look for, grep signals, sampling strategy, output format)
- `references/profile-template.md` — Exact PROJECT-KNOWLEDGE.md template with section specs and placeholder examples
- `references/prompt-integration-guide.md` — How to load the generated profile into subagent prompts (inclusion patterns, selective loading, examples)
