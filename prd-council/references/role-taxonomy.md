# Role Taxonomy & Agent Binding (Phase 4)

**WHEN TO READ:** Phase 4, when resolving the agent roster for the Technical PRDs.

Roster resolution is **layered and portable-first**: a stable generic taxonomy,
opportunistically bound to concrete installed subagents when the stack matches,
overridable by the user. Engineer roles are language-dependent, so the generic
layer stays the contract; concrete agents are an optimization, never a hard
dependency.

## Layer 1 — Generic capability taxonomy (stable)

Select **only the roles the PRD actually needs** — do not emit unused roles.

| Role | Responsibility | Typical inputs → outputs |
|------|----------------|--------------------------|
| **PdM** | Always present. Distributes tasks, manages dependencies, tracks done criteria. Played by this skill during doc-gen; documented as the future orchestrator. | PRD, Technical PRDs → tasks.md, assignment plan |
| **Frontend** | UI, client state, accessibility. | Designs, API contracts → components, client flows |
| **Backend** | APIs, domain logic, services. | PRD decisions, schema → endpoints, services |
| **Data** | Schema, migrations, data modeling, queries. | Domain model → migrations, data contracts |
| **QA** | Test strategy, coverage, quality gates. | UseCases, seams → test plans, tests |
| **DevOps** | CI/CD, infra, deployment, observability. | Build/run needs → pipelines, infra |
| **Security** | AuthN/Z, permissions, vulnerability review. | Threat surface → controls, review notes |
| **Docs** | User/dev documentation. | Approved PRD → docs |

## Layer 2 — Opportunistic subagent binding (stack-aware)

For each selected role, detect the project's stack (Phase 0) and bind the role to
a matching **installed** subagent if one exists; otherwise keep the generic label.

- **Detect the stack** from manifests/build files (e.g. `*.csproj`/`*.sln` → .NET;
  `package.json` → Node; `pyproject.toml` → Python; `go.mod` → Go).
- **Discover available subagents** best-effort — they are invoked as
  `@agent-<plugin>:<name>`. Look at the project's `agents/` dirs and installed
  plugins. Treat discovery as advisory; if unsure, keep the generic role.
- **Bind only when the match is clear and stack-appropriate.** Examples (illustrative,
  not exhaustive, not required to exist):
  - .NET/C# Backend → `dotnet-senior`
  - QA / test-gap analysis → `orch-qa`
  - PM/scope/risk lens → `pm-review` (as a review lens)
  - Deep codebase context for any role → `subagent-gen` profile
- **Never hard-depend** on a specific subagent. If a bound agent is absent at
  execution time, the generic role still fully specifies the work.

Record the binding in the Technical PRD roster table as either `@agent-…:…` (bound)
or "(generic <role>)" (unbound).

## Layer 3 — User override

`--agents <csv>` (e.g. `frontend,backend,qa,infra`) replaces the auto-selected
role set. Unknown names are kept as generic custom roles. The PdM role is always
included even if omitted.

## Output

The resolved roster feeds:
- `technical-prd-summary.md` → **Agent Roster** table + per-role responsibilities.
- `technical-prd-<usecase>.md` → **Assigned Agent(s)** section.
- `tasks.md` → each task's `role:` tag.
