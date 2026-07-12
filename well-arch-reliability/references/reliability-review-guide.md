# Reliability Review Guide (Well-Architected)

Review the input against these 8 principles from Google Cloud's
Well-Architected Framework — Reliability pillar
(https://docs.cloud.google.com/architecture/framework). For each principle,
use the review questions to guide analysis and produce findings using the
output format. Tag every finding with severity and an `R-` prefixed ID.

---

## 1. Reliability Goals Aligned to UX

**Focus**: SLOs / SLIs that reflect what users actually feel, with error
budgets that drive prioritization.

**Review Questions**:
- Are SLOs defined for this service, and do they reflect a user-visible
  experience (latency, success rate, freshness) — not just CPU / memory?
- Are SLIs measurable from a representative client position?
- Is there an error budget, and does it influence release / freeze decisions?
- Are SLOs reviewed when product behavior changes?
- Are alerts tied to SLO burn rate, not raw thresholds?

**Output Format**:
```markdown
### Reliability Goals Aligned to UX
- **SLOs defined**: [Yes — list / Partial / No]
- **User-facing SLIs**: [Yes / Internal-only / None]
- **Error budget in use**: [Yes / Defined but unused / No]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | No SLO at all on a user-facing service; alerts firing constantly with no link to SLO |
| Important | SLO exists but measured server-side only; error budget defined but never consulted |
| Nice-to-have | Add a freshness SLI for the data pipeline |

---

## 2. Realistic Recovery Targets

**Focus**: RTO and RPO that are stated, tested, and matched to investment.

**Review Questions**:
- Are RTO (recovery time) and RPO (data loss) targets explicitly stated?
- Do current backup / replication mechanisms actually meet those targets?
- When was the last restore actually tested end-to-end?
- Are recovery targets matched to the business impact, not just default?
- Is there a documented recovery runbook for the relevant failure modes?

**Output Format**:
```markdown
### Realistic Recovery Targets
- **RTO**: [Stated value / Implicit / None]
- **RPO**: [Stated value / Implicit / None]
- **Last validated restore**: [Date / Never]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | No backups, or backups never restored on a stateful production system |
| Important | RTO documented but no DR drill in the last year; targets don't match business |
| Nice-to-have | Automate restore validation in CI |

---

## 3. High Availability via Redundancy

**Focus**: Eliminating single points of failure, multi-zone / multi-region
trade-offs made deliberately.

**Review Questions**:
- Are there single points of failure (one DB writer, one VM, one external
  vendor with no fallback)?
- Is the workload zonal, regional, or multi-region — and is that aligned
  with the SLO?
- Are dependencies (databases, queues, caches) replicated to match?
- Is failover automated, manual with a runbook, or undefined?
- Is health-check granularity sufficient (no "the LB sees it as healthy but
  the app is wedged")?

**Output Format**:
```markdown
### High Availability via Redundancy
- **Topology**: [Zonal / Regional / Multi-region]
- **SPOFs**: [None identified / List]
- **Failover mode**: [Automatic / Runbook / None]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Single-zone production DB with regional SLO promised; cold standby that has never been exercised |
| Important | Multi-zone compute but single-zone storage; manual failover with stale runbook |
| Nice-to-have | Consider regional failover for the secondary service |

---

## 4. Horizontal Scalability

**Focus**: Stateless workers, autoscaling, no single fat-instance bottleneck.

**Review Questions**:
- Are services stateless enough to scale horizontally?
- Is autoscaling configured with reasonable min / max and warm-up time?
- Are there hidden serialization points (single-threaded queue, locked
  table, exclusive lease) that defeat horizontal scaling?
- Has the scaling been load-tested at projected peak + headroom?
- Is the cold-start cost acceptable for the traffic shape?

**Output Format**:
```markdown
### Horizontal Scalability
- **Stateless workers**: [Yes / Mixed / No]
- **Autoscaling**: [Configured + tested / Configured / Manual]
- **Bottlenecks**: [List]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | A single fat instance is the only path for a peak event; no autoscaling on a service that is known to spike |
| Important | Autoscaling exists but min/max guessed and never load-tested; hidden global lock |
| Nice-to-have | Reduce cold start time for better tail latency |

---

## 5. Observability for Failure Detection

**Focus**: Logs, metrics, traces — enough to detect, diagnose, and prove SLO
state.

**Review Questions**:
- Are RED / USE / golden signals captured for this service?
- Is there distributed tracing across the request path?
- Are logs structured, sampled appropriately, and searchable end-to-end?
- Are alerts SLO-burn-rate based with multiwindow / multi-burn-rate to avoid
  noise?
- Can an engineer get from "alert fired" to "likely root cause" within
  minutes using dashboards or saved queries?

**Output Format**:
```markdown
### Observability for Failure Detection
- **Golden signals**: [Complete / Partial / Missing]
- **Tracing**: [Yes / No]
- **Alerting**: [SLO-based / Threshold / Noisy]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | No alerts on a user-facing service; no way to tell if SLO is being met |
| Important | Alerts are threshold-based and noisy; no tracing across services; logs unstructured |
| Nice-to-have | Add an exemplar-linked latency dashboard |

---

## 6. Graceful Degradation

**Focus**: When a dependency fails, the system narrows scope rather than
collapsing.

**Review Questions**:
- Are timeouts and retries bounded (with jitter and budget) on every outgoing
  call?
- Are circuit breakers / bulkheads in place for critical dependencies?
- Is there a defined degraded-mode behavior (read-only, stale-cache, smaller
  feature set) and is it tested?
- Do client retries amplify load on failure ("retry storm"), or is there
  back-pressure?
- Are load-shedding policies in place at saturation?

**Output Format**:
```markdown
### Graceful Degradation
- **Timeouts / retries**: [Bounded with jitter / Bounded / Unbounded]
- **Circuit breakers**: [Yes / Some / None]
- **Degraded mode**: [Defined + tested / Defined / Undefined]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Unbounded retries causing retry storms; one slow dependency takes the whole service down |
| Important | Circuit breaker library available but not wired; degraded mode documented but never exercised |
| Nice-to-have | Add load-shedding at 90% saturation |

---

## 7. Tested Recovery

**Focus**: Restoring from failure proven by drills, not by assumption.

**Review Questions**:
- Has a chaos / GameDay exercise been run on this service?
- Are zone / region failover paths actually exercised on a schedule?
- Are backup restores verified, not just job-success-true?
- Are data-loss / corruption scenarios part of the rehearsal set, not just
  outages?
- Are findings from drills tracked and closed?

**Output Format**:
```markdown
### Tested Recovery
- **Chaos / GameDay**: [Yes — last date / No]
- **Failover exercised**: [Yes / Documented / Never]
- **Restore verified**: [Yes — last date / Job-only / Never]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Never restored from backup; never exercised failover; stateful system |
| Important | Drills happen but findings aren't tracked; only outage scenarios rehearsed |
| Nice-to-have | Add corruption-recovery scenario to next GameDay |

---

## 8. Incident Postmortems

**Focus**: Blameless review, durable learning, action items closed.

**Review Questions**:
- Is there a postmortem template / process the team follows?
- Are postmortems blameless and shared (within at least the team)?
- Are action items tracked to closure with owner and date?
- Do recurring incidents trigger a deeper investigation, not just N more
  fixes?
- Is the rate of repeat incidents declining?

**Output Format**:
```markdown
### Incident Postmortems
- **Postmortem process**: [Documented + followed / Ad hoc / None]
- **Blameless culture**: [Yes / Mixed / No]
- **Action item closure**: [Tracked + closed / Tracked / None]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | No postmortem process for a regulated / SLA-bound service |
| Important | Postmortems written but action items unowned and aging |
| Nice-to-have | Publish postmortem summaries cross-team for shared learning |
