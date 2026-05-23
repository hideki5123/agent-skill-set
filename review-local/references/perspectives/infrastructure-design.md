# Infrastructure Design Perspective

## Focus

Scalability, deployment readiness, resource constraints, resilience, observability.

## Review Questions

1. What is the memory footprint — are there unbounded collections or streams?
2. What is the CPU complexity — any hot paths or expensive algorithms?
3. How does this behave under network constraints (slow, unreliable, offline)?
4. What happens when external services are unavailable?
5. Is there adequate observability (logging, metrics, health checks)?

## Output Format

```markdown
## Infrastructure Design Review

### Memory & Storage
- [Heap usage, collection sizes, streaming vs loading, disk usage]

### CPU & Compute
- [Algorithm complexity, hot paths, parallelism opportunities]

### Network & External Dependencies
- [Retry logic, timeouts, circuit breakers, offline handling]

### Resilience & Fault Tolerance
- [Graceful degradation, fallback behavior, recovery paths]

### Observability
- [Logging adequacy, metrics, alerting hooks, health endpoints]

### Recommendations
- [Specific optimizations and safeguards with file:line references]
```

## Severity Guidance

| Severity | Examples from this perspective |
|----------|-------------------------------|
| **Critical** | Unbounded memory growth, missing timeouts on external calls, no error recovery |
| **Important** | O(n²) where O(n) is feasible, missing retry logic, no pagination for large datasets |
| **Nice-to-have** | Could add metrics, connection pooling optimization, caching opportunities |
