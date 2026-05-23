# Security Perspective

## Focus

Input validation, injection risks, authentication/authorization, data exposure, OWASP Top 10.

## Review Questions

1. Are all inputs validated and sanitized at system boundaries?
2. Is there risk of injection (SQL, command, XSS, CSV, template, etc.)?
3. Is sensitive data properly protected (secrets, PII, tokens)?
4. Are error messages safe — no internal details or stack traces exposed?
5. Is authorization properly enforced at every access point?

## Output Format

```markdown
## Security Review

### Input Validation
- [Assessment of input handling at system boundaries]

### Injection Risks
- [Potential injection vectors and current mitigations]

### Data Exposure
- [Sensitive data handling: secrets, PII, tokens, credentials]

### Error Handling Safety
- [Information leakage risks in error messages and logs]

### Auth & Access Control
- [Authentication and authorization enforcement]

### Recommendations
- [Specific security measures to implement with file:line references]
```

## Severity Guidance

| Severity | Examples from this perspective |
|----------|-------------------------------|
| **Critical** | SQL/command injection, exposed secrets, missing auth checks, XSS vectors |
| **Important** | Insufficient input validation, verbose error messages, missing rate limiting |
| **Nice-to-have** | Could add CSP headers, additional logging for audit trail |
