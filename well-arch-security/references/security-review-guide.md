# Security Review Guide (Well-Architected)

Review the input against these 7 principles from Google Cloud's
Well-Architected Framework — Security, Privacy, and Compliance pillar
(https://docs.cloud.google.com/architecture/framework). For each principle,
use the review questions to guide analysis and produce findings using the
output format. Tag every finding with severity and an `S-` prefixed ID.

A baseline OWASP / input-handling checklist already lives at
`../../review-local/references/perspectives/security.md` — pull from it
rather than duplicating; cite it from the relevant principle below.

---

## 1. Security by Design

**Focus**: Threat modeling early, secure defaults, defense in depth.

**Review Questions**:
- Has a threat model been articulated for this change or system?
- Are defaults secure (deny-by-default, no public exposure unless explicit)?
- Are there layered controls, or does one bypass collapse all security?
- Is the principle of least privilege visible in IAM / network / data access?
- Are secrets stored in a secret manager rather than env vars or code?

**Output Format**:
```markdown
### Security by Design
- **Threat model**: [Present / Implicit / Missing]
- **Secure defaults**: [Yes / Partial / No — specifics]
- **Defense in depth**: [Layers present, gaps]
- **Findings**: [Details, file:line where applicable]
- **Severity**: [Critical / Important / Nice-to-have]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Public storage bucket, exposed admin endpoint, hardcoded secret |
| Important | Default IAM role used, missing threat model for new attack surface |
| Nice-to-have | Could add a deny-by-default network policy as an extra layer |

---

## 2. Zero Trust

**Focus**: Identity-based access, no implicit trust between services or
networks, continuous verification.

**Review Questions**:
- Does service-to-service auth use short-lived identity (workload identity,
  mTLS, OIDC), not shared secrets or IP allowlists alone?
- Is access scoped per-resource / per-action, not broad project-level?
- Are there network paths that assume "internal traffic is trusted"?
- Is privileged access time-bound or just-in-time, not standing?
- Are user sessions revalidated when sensitivity escalates?

**Output Format**:
```markdown
### Zero Trust
- **Identity-based access**: [Strong / Partial / Network-only]
- **Least privilege**: [Per-resource / Broad / Wildcard]
- **Implicit network trust**: [None / Some / Heavy]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Wildcard IAM, internal endpoints with no auth, shared long-lived API keys |
| Important | Network-only trust between services, broad service-account scopes |
| Nice-to-have | Could switch from API key to workload identity |

---

## 3. Shift-Left Security

**Focus**: Security checks embedded into development & CI, not bolted on
post-deploy.

**Review Questions**:
- Are SAST / dependency / secret-scanning steps part of CI?
- Is IaC scanned (e.g. Checkov, tfsec, Terrascan) before apply?
- Are container images scanned before deploy?
- Are pre-commit / pre-merge hooks blocking obvious vulnerabilities?
- Are findings actionable (assigned, SLA'd) or do they pile up?

**Output Format**:
```markdown
### Shift-Left Security
- **CI scanning coverage**: [SAST / SCA / Secret / IaC / Image — present, missing]
- **Blocking vs advisory**: [Findings block merge? Or just warn?]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | No dependency / secret scanning at all on a production service |
| Important | Findings exist but are advisory, no SLA, accumulating |
| Nice-to-have | Add SBOM generation for supply-chain transparency |

---

## 4. Preemptive Cyber Defense

**Focus**: Detection, logging, response — assume breach.

**Review Questions**:
- Are audit logs enabled and shipped to a tamper-resistant store?
- Are there detection rules / alerts for the most likely attacks on this
  surface (auth anomalies, exfiltration, privilege escalation)?
- Is there an incident response runbook, with on-call ownership?
- Are secrets rotated automatically, and is rotation tested?
- Is there honey-token / decoy coverage for high-value paths?

**Output Format**:
```markdown
### Preemptive Cyber Defense
- **Audit logging**: [Enabled & exported / Default / Missing]
- **Detection coverage**: [Key threats covered or gaps]
- **Incident response**: [Runbook + owner / Ad hoc / None]
- **Secret rotation**: [Automated / Manual / Never]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | No audit logs, no alerting on auth failures, secrets never rotated |
| Important | Logs exist but not retained long enough, no documented IR runbook |
| Nice-to-have | Add anomaly detection on egress data volume |

---

## 5. AI Used Securely & Responsibly

**Focus**: Risks unique to AI / LLM components — prompt injection, data
leakage, model abuse.

**Review Questions**:
- Are LLM inputs from untrusted sources isolated from tool / system prompts?
- Is sensitive data (PII, secrets) redacted before being sent to a model?
- Is model output validated before being executed or rendered (XSS / RCE
  via tool use)?
- Are model API keys scoped, rotated, and rate-limited?
- Is there logging of prompts/responses for abuse detection (with PII care)?

**Output Format**:
```markdown
### AI Used Securely & Responsibly
- **Prompt-injection posture**: [Isolated / Mixed / Vulnerable / N/A]
- **Sensitive-data handling**: [Redacted / Sent in clear / N/A]
- **Output trust boundary**: [Validated / Rendered raw / N/A]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | User-supplied text directly concatenated into a tool-using system prompt; PII sent to third-party LLM |
| Important | No prompt-injection mitigation on user-tool flows; model output rendered as HTML without sanitization |
| Nice-to-have | Add prompt/response logging for abuse review |

If the system does not include AI/LLM components, mark this principle as
"Not applicable" and skip findings.

---

## 6. Regulatory, Compliance & Privacy

**Focus**: PII / PHI / regulated-data handling, residency, audit, consent.

**Review Questions**:
- What regulated data classes does this touch (PII, PHI, PCI, GDPR scope)?
- Is data residency / sovereignty respected (region pinning)?
- Are retention / deletion policies implemented, not just documented?
- Is consent captured and revocable where required?
- Are audit trails sufficient for the relevant compliance regime?

**Output Format**:
```markdown
### Regulatory, Compliance & Privacy
- **Data classes touched**: [None / PII / PHI / PCI / Other]
- **Residency**: [Compliant / Unknown / Violating]
- **Retention & deletion**: [Implemented / Documented only / None]
- **Consent**: [Captured + revocable / Captured only / Missing / N/A]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | PII stored in unencrypted form, data leaving allowed region, no deletion path |
| Important | Retention longer than necessary, consent UX unclear |
| Nice-to-have | Add data-class tagging for future automation |

---

## 7. Shared Responsibility

**Focus**: Clarity on who owns each control — cloud provider, platform team,
service team, vendor.

**Review Questions**:
- Are control boundaries documented (who patches the host, the runtime, the
  app, the dependencies)?
- Are vendor / managed-service security commitments understood and
  reflected in the design?
- Are third-party SaaS dependencies inventoried with risk classification?
- Is there an owner on-call for security incidents in this component?

**Output Format**:
```markdown
### Shared Responsibility
- **Control ownership documented**: [Yes / Partial / No]
- **Vendor risk inventory**: [Maintained / Ad hoc / None]
- **Incident ownership**: [Named owner / Team / Unclear]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Unclear who responds to a vendor breach; no owner for a regulated component |
| Important | Vendor inventory exists but isn't reviewed; assumptions about provider not validated |
| Nice-to-have | Add control-ownership column to the architecture doc |
