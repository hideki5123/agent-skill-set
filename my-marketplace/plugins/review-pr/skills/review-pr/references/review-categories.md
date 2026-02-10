# Review Categories Reference

## Category Definitions and Severity

Each finding must be tagged with exactly one category and one severity.

### Categories

| Tag | Meaning | Requires action? |
|-----|---------|-----------------|
| `bug` | Incorrect behavior, logic error, crash, data loss, race condition | Yes |
| `security` | Vulnerability: injection, auth bypass, secrets leak, OWASP Top 10 | Yes |
| `perf` | Unnecessary allocation, O(n^2) where O(n) is possible, missing index | Usually |
| `design` | Poor abstraction, tight coupling, violation of project conventions | Usually |
| `better-to-have` | Improvement that adds value but isn't blocking (better naming, missing edge-case test, docs) | No |
| `nitpick` | Style, formatting, trivial naming preference | No |
| `question` | Something unclear — ask the author for intent before judging | No |

### Severity Levels

| Level | Description |
|-------|-------------|
| `critical` | Must fix before merge. Bugs that cause data loss, security vulnerabilities, breaking changes. |
| `major` | Should fix before merge. Logic errors, missing error handling, perf regressions. |
| `minor` | Nice to fix. Design improvements, better naming, missing tests for edge cases. |
| `trivial` | Optional. Style nits, comment typos, minor formatting. |

### Mapping Categories to Default Severity

- `bug` → critical or major (depends on impact)
- `security` → critical
- `perf` → major or minor
- `design` → major or minor
- `better-to-have` → minor
- `nitpick` → trivial
- `question` → (no severity, just a question)

## Security Checklist (OWASP + Common Issues)

When reviewing for security, check for:

1. **Injection** — SQL, NoSQL, OS command, LDAP injection via unsanitized input
2. **Broken Auth** — Hardcoded credentials, weak token generation, missing auth checks
3. **Sensitive Data Exposure** — Secrets in code, PII in logs, missing encryption
4. **XXE** — Unsafe XML parsing with external entities enabled
5. **Broken Access Control** — Missing authorization checks, IDOR, privilege escalation
6. **Security Misconfiguration** — Debug mode in prod, default credentials, overly permissive CORS
7. **XSS** — Unescaped user input rendered in HTML/JS
8. **Insecure Deserialization** — Untrusted data deserialized without validation
9. **Known Vulnerabilities** — Outdated dependencies with known CVEs
10. **Insufficient Logging** — Security events not logged, sensitive data in logs

## What Makes a Good Review Comment

### Structure of a Comment

```
[category|severity] Short summary

Detailed explanation of WHY this is an issue, not just WHAT is wrong.
Include the impact: what could go wrong if this is not addressed.

Suggested fix (code snippet when possible):
\`\`\`lang
// corrected code here
\`\`\`
```

### Examples

**Bug example:**
```
[bug|critical] Off-by-one in pagination causes skipped records

`offset = page * limit` should be `offset = (page - 1) * limit` when pages
are 1-indexed. Currently page 1 skips the first `limit` records.

Suggested fix:
\`\`\`ts
const offset = (page - 1) * limit;
\`\`\`
```

**Security example:**
```
[security|critical] SQL injection via unsanitized user input

`query = f"SELECT * FROM users WHERE name = '{name}'"` concatenates user
input directly. An attacker can inject `'; DROP TABLE users; --`.

Suggested fix:
\`\`\`python
cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
\`\`\`
```

**Better-to-have example:**
```
[better-to-have|minor] Add test for empty-array edge case

`processItems([])` isn't tested. While the current code handles it
correctly, an explicit test documents the expected behavior and guards
against regressions.
```

**Nitpick example:**
```
[nitpick|trivial] Prefer `const` over `let` for unchanging binding

`let config = loadConfig();` — `config` is never reassigned, so `const`
communicates intent more clearly.
```

**Question example:**
```
[question] Is this intentional fallthrough?

The switch statement at line 42 falls through from `case 'admin'` to
`case 'user'`. If this is intentional, add a `// fallthrough` comment.
If not, add a `break`.
```
