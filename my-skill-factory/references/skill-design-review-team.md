# Skill Team Perspective Catalog

When the team orchestration assessment determines a skill needs multi-agent review, select relevant perspectives from this catalog and include them in the target skill.

## How to Use This Catalog

1. Review the available perspectives below
2. Select 3-5 that match the target skill's domain
3. Copy selected perspective prompt templates into the target skill's `references/team-roles.md` (or similar)
4. Add "Create an agent team to explore this from different angles: [selected angles]" to the target skill's SKILL.md
5. Customize review questions for the target skill's specific domain
6. Include the Synthesis Protocol Template in the target skill's reference file

## Available Perspectives

### Software Architecture

**Focus**: Design patterns, modularity, extensibility, existing conventions

**Best for**: Skills with multi-module structure, extensibility concerns, complex reference organization

**Review Questions**:
1. Does the proposed design follow existing patterns in the codebase?
2. Is the solution appropriately modular and testable?
3. Are there dependency injection points for mocking?
4. Will this scale with future requirements?
5. Are interfaces/abstractions at the right level?

**Output Format**:
```markdown
## Architecture Review

### Alignment with Existing Patterns
- [Findings about pattern consistency]

### Modularity Assessment
- [How well the design separates concerns]

### Testability
- [Dependency injection points, mockability]

### Recommendations
- [Specific actionable suggestions]

### Risks
- [Architectural concerns to address]
```

### QA/QC

**Focus**: Test coverage, quality gates, defect prevention, output validation

**Best for**: Skills producing testable output, quality-critical workflows

**Delegate to**: `orch-qa` skill for deep test coverage analysis

**Review Questions**:
1. Are all outputs validated against expected formats?
2. Are there quality gates at each workflow phase?
3. Is error detection comprehensive or are failures silent?
4. Are edge cases covered in the test strategy?
5. Is there a feedback loop for continuous quality improvement?

**Output Format**:
```markdown
## QA/QC Review

### Output Validation
- [Assessment of output quality checks]

### Quality Gates
- [Phase-by-phase quality checkpoints]

### Edge Case Coverage
- [Gaps in edge case handling]

### Recommendations
- [Specific quality improvements]

### Risks
- [Quality concerns to address]
```

### BDD / Scenario Quality

**Focus**: Behavior scenario coverage, Given/When/Then quality, anti-pattern detection

**Best for**: Skills with behavior scenarios, acceptance-criteria-driven workflows

**Review Questions**:
1. Do the scenarios cover the primary, secondary, and edge case paths?
2. Are the Given/When/Then clauses specific enough to be testable?
3. Are there anti-patterns (too vague, too implementation-specific, duplicates)?
4. Do scenarios map cleanly to SKILL.md sections?
5. Are update-delta scenarios well-defined for future modifications?

**Output Format**:
```markdown
## BDD / Scenario Quality Review

### Coverage Assessment
- [Primary, secondary, edge case coverage]

### Scenario Clarity
- [Specificity and testability of Given/When/Then]

### Anti-Patterns Detected
- [Vague, duplicate, or implementation-specific scenarios]

### Recommendations
- [Specific scenario improvements]

### Risks
- [Coverage gaps that could cause issues]
```

### TDD Discipline

**Focus**: Test-first workflow design, RED-GREEN-REFACTOR adherence, test structure

**Best for**: Skills involving code generation or test-first workflows

**Delegate to**: `dev-workflow` skill's test-design reference for detailed test category guidance

**Review Questions**:
1. Does the workflow enforce writing tests before implementation?
2. Are test categories comprehensive (happy path, edge cases, error handling, security)?
3. Is the RED-GREEN-REFACTOR cycle clearly defined?
4. Are test naming conventions specified?
5. Are anti-patterns (tests that pass immediately, testing internals) addressed?

**Output Format**:
```markdown
## TDD Discipline Review

### Test-First Enforcement
- [How well the workflow ensures tests come first]

### Test Category Coverage
- [Assessment of test categories included]

### Cycle Definition
- [Clarity of RED-GREEN-REFACTOR steps]

### Recommendations
- [Specific TDD improvements]

### Risks
- [Discipline gaps that could weaken test quality]
```

### Security

**Focus**: Input validation, injection risks, auth/authz, data exposure, credential handling

**Best for**: Skills handling credentials, user data, external auth, file writes

**Review Questions**:
1. Are all inputs validated and sanitized?
2. Is there risk of injection (SQL, command, CSV, path traversal)?
3. Is sensitive data properly protected (credentials, API keys, tokens)?
4. Are error messages safe (no internal details exposed)?
5. Is authorization properly enforced at each step?

**Output Format**:
```markdown
## Security Review

### Input Validation
- [Assessment of input handling]

### Injection Risks
- [Potential injection vectors and mitigations]

### Data Exposure
- [Sensitive data handling concerns]

### Error Handling
- [Information leakage risks]

### Recommendations
- [Specific security measures to implement]
```

### Infrastructure Design

**Focus**: External dependencies, deployment concerns, environment compatibility, tooling

**Best for**: Skills with CLI tools, MCP servers, APIs, deployment concerns

**Review Questions**:
1. Are all external dependencies documented and version-pinned?
2. What happens when a dependency is unavailable or returns errors?
3. Is the skill portable across different environments?
4. Are setup/teardown steps idempotent?
5. Are there fallback strategies for external service failures?

**Output Format**:
```markdown
## Infrastructure Review

### Dependency Inventory
- [External tools, APIs, MCP servers required]

### Availability & Resilience
- [Behavior when dependencies are unavailable]

### Portability
- [Environment compatibility concerns]

### Recommendations
- [Specific infrastructure improvements]

### Risks
- [Dependency-related concerns]
```

### Idempotence & Safety

**Focus**: Re-runnability, deterministic output, destructive operation guards, side effects

**Best for**: Skills that modify state, write files, or perform destructive operations

**Review Questions**:
1. Can the skill be re-run without causing duplicates or corruption?
2. Is the output deterministic given the same inputs?
3. Are destructive operations guarded with confirmation or dry-run options?
4. Are side effects documented and reversible where possible?
5. Does the skill handle partial failures gracefully (resume vs restart)?

**Output Format**:
```markdown
## Idempotence & Safety Review

### Re-runnability
- [Assessment of safe re-execution]

### Determinism
- [Output consistency analysis]

### Destructive Operation Guards
- [Confirmation, dry-run, backup mechanisms]

### Side Effect Management
- [Documentation and reversibility of side effects]

### Recommendations
- [Specific safety improvements]
```

### Product Management (PMBOK)

**Focus**: Scope management, stakeholder analysis, risk assessment, integration management, value delivery

**Best for**: Skills serving business processes, multi-stakeholder workflows

**Review Questions**:
1. Does this skill solve a clearly defined need? Is the scope bounded?
2. Who are the stakeholders and does the output serve them all?
3. What are the risks (technical, adoption, maintenance) and mitigations?
4. Does this overlap with or conflict with existing skills?
5. Is the value delivered proportional to the complexity introduced?

**Output Format**:
```markdown
## Product Management Review

### Scope Definition
- [Clarity and boundedness of scope]

### Stakeholder Analysis
- [Who benefits, who maintains, who is affected]

### Risk Assessment
- [Technical, adoption, and maintenance risks]

### Integration with Existing Skills
- [Overlap, conflicts, synergies]

### Recommendations
- [Scope, risk, and value improvements]
```

### Devil's Advocate

**Focus**: Challenge assumptions, find flaws, suggest simpler alternatives

**Best for**: All complex skills — applies universally as a critical thinking check

**Review Questions**:
1. What assumptions are we making that might be wrong?
2. What's the simplest alternative approach that achieves the same goal?
3. What could go wrong that we haven't considered?
4. Is this over-engineered for the actual need?
5. Could an existing skill handle this with minor modifications instead?

**Output Format**:
```markdown
## Devil's Advocate Review

### Challenged Assumptions
- [Assumptions that may not hold]

### Alternative Approaches
- [Simpler or different ways to solve this]

### Potential Failures
- [Scenarios not yet considered]

### Over-Engineering Concerns
- [Complexity that may not be needed]

### Critical Questions
- [Questions that need answers before proceeding]
```

## Synthesis Protocol Template

Copy this protocol into the target skill's reference file alongside the selected perspectives.

After all teammates complete their reviews:

1. **Collect** all findings from each teammate
2. **Categorize** by severity:
   - **Critical** — Blocks implementation, security risk, architectural flaw → Must address before proceeding
   - **Important** — Should address for quality, but not blocking → Address during implementation
   - **Nice-to-have** — Improvements that can be deferred → Document for future consideration
3. **Deduplicate** overlapping concerns across teammates
4. **Prioritize** based on risk and effort
5. **Update** the implementation plan with concrete action items
6. **Present** consolidated feedback to user for approval
7. **Clean up** the team when discussion is complete

## Cross-Skill Delegation Notes

When a perspective requires deeper analysis than the team review provides, suggest delegating to a specialized skill:

| Perspective | Can delegate to | When |
|-------------|----------------|------|
| QA/QC | `orch-qa` | Deep test coverage analysis, multi-lens quality audit needed |
| TDD | `dev-workflow` | Test-first workflow design, RED-GREEN-REFACTOR cycle definition |
| Codebase Knowledge | `subagent-gen` | Skill wraps or extends existing code, needs deep domain profiling |
| Scenario Generation | `scenario-gen` | Change-based test scenario design from git diffs |

Delegation is **advisory** — the team reviewer mentions it in their output; the orchestrating agent decides whether to act on it.
