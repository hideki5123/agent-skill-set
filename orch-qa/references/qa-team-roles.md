# QA Gap Analysis Team Roles

Create an agent team to analyze test gaps from different quality perspectives: one teammate focused on code quality (functional, resilience, idempotence), one on security and infrastructure (security, infra, network), and one on user experience and system health (frontend, journey, performance, observability).

Use `TeamCreate` to create the team, then `SendMessage` to spawn each teammate with their role-specific prompt below. Include the source-to-test mapping, project metadata, and relevant filter settings in each spawn prompt. Teammates will work independently on their assigned lenses and report findings back to the lead.

## Teammate Groups

Each teammate handles a thematically related subset of QA lenses from [qa-perspectives.md](qa-perspectives.md).

| Group | Teammate Name | Lenses | Gap NNN Range |
|-------|--------------|--------|---------------|
| **Code Quality** | `qa-code-quality` | Functional, Resilience, Idempotence | 001-199 |
| **Security & Infra** | `qa-security-infra` | Security, Infrastructure, Network & Integration | 200-399 |
| **User & System** | `qa-user-system` | Frontend/UX, Customer Journey, Performance, Observability | 400-599 |

## Dynamic Spawning Based on `--lens`

Not all teammates are needed for every run. Determine which groups to spawn:

- Map each `--lens` value to its group (e.g., `security` -> Security & Infra)
- Only spawn teammates for groups that have at least one active lens
- **If only 1 group has active lenses, skip team creation entirely** — run the analysis inline to avoid orchestration overhead
- If `--lens=all` (default), spawn all 3 teammates

## Context Package for Each Teammate

Every teammate receives the following in their spawn prompt:

1. **Source-to-test mapping** — list of source files with their corresponding test files (or "MISSING")
2. **Project metadata** — language, framework, test runner, source dirs, test dirs (from Phase 1-2)
3. **Active lenses** — which of their assigned lenses are active (respecting `--lens` filter)
4. **Lens definitions** — the patterns-to-grep, severity guidance, and example findings from [qa-perspectives.md](qa-perspectives.md) for their assigned lenses only
5. **Evidence directory path** — absolute path to the `gaps/` subdirectory
6. **Gap NNN range** — their assigned range to avoid collision with other teammates
7. **Filter settings** — `--severity`, `--exclude`, `--app-type`, `--base-url` values

## Code Quality Teammate

**Focus**: Internal code correctness — branching logic, error handling, retry safety

**Lenses**: Functional, Resilience, Idempotence

**Task**:
1. For each active lens, grep source files for the lens-specific patterns from [qa-perspectives.md](qa-perspectives.md)
2. For each match, check the source-to-test mapping to determine if there's a corresponding test
3. A pattern is "uncovered" if no test file explicitly references the function/class containing the pattern
4. For each finding, write a proof file `gaps/gap-<NNN>-<lens>-<severity>.md` containing the full source snippet, explanation, pattern matched, and suggested test description
5. Return the findings table to the lead

**Output Format**:
```markdown
## Gap Analysis: Code Quality

### Findings

| # | Lens | Severity | Confidence | Location | Pattern | Proof File | Suggested Test |
|---|------|----------|------------|----------|---------|------------|----------------|
| 001 | functional | critical | high | src/billing/invoice.ts:42 | 6 branches, only happy-path tested | gaps/gap-001-functional-critical.md | Test discount + tax + rounding branches |

### Summary
- Lenses analyzed: functional, resilience, idempotence
- Source files scanned: <N>
- Findings: <N> (critical: N, high: N, medium: N, low: N)
- Proof files written: <list>
```

## Security & Infra Teammate

**Focus**: External boundaries — auth, env config, API calls, DB queries, trust boundaries

**Lenses**: Security, Infrastructure, Network & Integration

**Task**:
1. For each active lens, grep source files for the lens-specific patterns from [qa-perspectives.md](qa-perspectives.md)
2. For each match, check the source-to-test mapping to determine if there's a corresponding test
3. A pattern is "uncovered" if no test file explicitly references the function/class containing the pattern
4. For each finding, write a proof file `gaps/gap-<NNN>-<lens>-<severity>.md`
5. Return the findings table to the lead

**Output Format**:
```markdown
## Gap Analysis: Security & Infra

### Findings

| # | Lens | Severity | Confidence | Location | Pattern | Proof File | Suggested Test |
|---|------|----------|------------|----------|---------|------------|----------------|
| 200 | security | critical | high | src/api/users.ts:87 | SQL string interpolation from req.params | gaps/gap-200-security-critical.md | Test SQL injection resistance |

### Summary
- Lenses analyzed: security, infrastructure, network
- Source files scanned: <N>
- Findings: <N> (critical: N, high: N, medium: N, low: N)
- Proof files written: <list>
```

## User & System Teammate

**Focus**: User-facing quality and operational health — rendering, E2E flows, response time, monitoring

**Lenses**: Frontend/UX, Customer Journey, Performance, Observability

**Task**:
1. For each active lens, grep source files for the lens-specific patterns from [qa-perspectives.md](qa-perspectives.md)
2. For each match, check the source-to-test mapping to determine if there's a corresponding test
3. A pattern is "uncovered" if no test file explicitly references the function/class containing the pattern
4. For each finding, write a proof file `gaps/gap-<NNN>-<lens>-<severity>.md`
5. **For browser apps** (`--app-type=browser`): capture a screenshot of the related UI page/component and save as `gaps/gap-<NNN>-screenshot.png`
6. Return the findings table to the lead

**Output Format**:
```markdown
## Gap Analysis: User & System

### Findings

| # | Lens | Severity | Confidence | Location | Pattern | Proof File | Suggested Test |
|---|------|----------|------------|----------|---------|------------|----------------|
| 400 | frontend | critical | high | src/components/CheckoutForm.tsx:23 | Form with 5 validation rules, no render test | gaps/gap-400-frontend-critical.md | Test form rendering and submission |

### Summary
- Lenses analyzed: frontend, journey, performance, observability
- Source files scanned: <N>
- Findings: <N> (critical: N, high: N, medium: N, low: N)
- Proof files written: <list>
```

## Synthesis Protocol

After all teammates complete their analysis, the lead performs synthesis:

1. **Collect** all findings tables from each teammate
2. **Deduplicate** — if two lenses found the same `file:line`, keep both findings but note the overlap in the report
3. **Apply filters**:
   - `--severity` — drop findings below the minimum severity
   - `--max-findings` — keep highest severity findings first, cap the total
   - `--exclude` — remove findings in excluded paths
4. **Renumber** gap files to a clean unified sequence (001, 002, ...) by renaming files from teammate ranges
5. **Clean up** the team with `TeamDelete`
6. **Output** the combined gap analysis findings list, grouped by lens, with proof links — in the same format Phase 7 expects
