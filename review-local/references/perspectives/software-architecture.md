# Software Architecture Perspective

## Focus

Design patterns, modularity, SOLID principles, coupling/cohesion, existing codebase conventions.

## Review Questions

1. Does the change follow existing design patterns in the codebase?
2. Is the solution appropriately modular with proper separation of concerns?
3. Are SOLID principles respected (single responsibility, open-closed, etc.)?
4. Is coupling minimized and cohesion maximized?
5. Are interfaces and abstractions at the right level?

## Output Format

```markdown
## Architecture Review

### Pattern Alignment
- [Findings about consistency with existing codebase patterns]

### Modularity & Separation of Concerns
- [How well the change separates responsibilities]

### SOLID Compliance
- [Single responsibility, open-closed, Liskov, interface segregation, dependency inversion]

### Coupling & Cohesion
- [Assessment of dependencies and internal relatedness]

### Recommendations
- [Specific actionable suggestions with file:line references]

### Risks
- [Architectural concerns that need attention]
```

## Severity Guidance

| Severity | Examples from this perspective |
|----------|-------------------------------|
| **Critical** | Violates core architecture, creates circular dependencies, breaks existing contracts |
| **Important** | Tight coupling that should be loosened, missing abstraction layer, inconsistent patterns |
| **Nice-to-have** | Minor naming inconsistencies, could use a more elegant pattern |
