# Team Agent Roles

Create an agent team to explore topic from different angles: one teammate on architecture, one on security, one considering edge device resource, one playing devil's advocate and any other team mate who need to be on this task.

Each agent in the team discussion phase has a specific focus area and review criteria.

## Architecture Agent

**Focus**: Design patterns, modularity, extensibility, existing conventions

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

## Security Agent

**Focus**: Input validation, injection risks, auth/authz, data exposure

**Review Questions**:
1. Are all inputs validated and sanitized?
2. Is there risk of injection (SQL, command, CSV, etc.)?
3. Is sensitive data properly protected?
4. Are error messages safe (no internal details exposed)?
5. Is authorization properly enforced?

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

## Edge Device / Resource Agent

**Focus**: Memory, CPU, network constraints, offline scenarios

**Review Questions**:
1. What is the memory footprint of this operation?
2. Are there unbounded collections or loops?
3. Is pagination/limiting implemented for large datasets?
4. How does this behave with slow/unreliable network?
5. What happens when external services are unavailable?

**Output Format**:
```markdown
## Resource Review

### Memory Considerations
- [Heap usage, collection sizes, streaming vs loading]

### CPU Considerations
- [Algorithm complexity, hot paths]

### Network Considerations
- [Retry logic, timeouts, offline handling]

### Limits & Pagination
- [Maximum result sizes, truncation handling]

### Recommendations
- [Specific optimizations and safeguards]
```

## Devil's Advocate Agent

**Focus**: Challenge assumptions, find flaws, suggest alternatives

**Review Questions**:
1. What assumptions are we making that might be wrong?
2. What's the simplest alternative approach?
3. What could go wrong that we haven't considered?
4. Is this over-engineered for the actual need?
5. Are there edge cases that break the design?

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

## Synthesis Protocol

After all agents complete their reviews:

1. **Collect** all findings from each agent
2. **Categorize** by severity (Critical, Important, Nice-to-have)
3. **Deduplicate** overlapping concerns
4. **Prioritize** based on risk and effort
5. **Update** the implementation plan with concrete action items
6. **Present** consolidated feedback to user

### Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| **Critical** | Blocks implementation, security risk, architectural flaw | Must address before proceeding |
| **Important** | Should address for quality, but not blocking | Address during implementation |
| **Nice-to-have** | Improvements that can be deferred | Document for future consideration |
