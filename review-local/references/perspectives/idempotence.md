# Idempotence Perspective

## Focus

Retry safety, duplicate handling, state consistency, at-least-once delivery, concurrent execution.

## Review Questions

1. Can this operation be safely retried without side effects (idempotent)?
2. How are duplicate requests or messages handled?
3. Is state consistent if the operation is interrupted midway?
4. Are there race conditions with concurrent execution?
5. Are external side effects (API calls, file writes, DB changes) guarded against re-execution?

## Output Format

```markdown
## Idempotence Review

### Retry Safety
- [Can operations be safely retried? What happens on re-execution?]

### Duplicate Handling
- [How are duplicate requests/events/messages detected and handled?]

### Partial Failure & State Consistency
- [What if the operation fails halfway? Is state left consistent?]

### Concurrency & Race Conditions
- [What happens with concurrent execution? Locking, optimistic concurrency?]

### External Side Effects
- [API calls, emails, file writes — are they guarded against re-execution?]

### Recommendations
- [Specific idempotence improvements with file:line references]
```

## Severity Guidance

| Severity | Examples from this perspective |
|----------|-------------------------------|
| **Critical** | Non-idempotent write operation in a retry loop, duplicate payments/emails possible |
| **Important** | Missing idempotency keys, partial failure leaves inconsistent state |
| **Nice-to-have** | Could add optimistic concurrency, idempotency tokens for future use |
