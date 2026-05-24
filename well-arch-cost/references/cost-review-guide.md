# Cost Optimization Review Guide (Well-Architected)

Review the input against these 6 principles from Google Cloud's
Well-Architected Framework — Cost Optimization pillar
(https://docs.cloud.google.com/architecture/framework). For each principle,
use the review questions to guide analysis and produce findings using the
output format. Tag every finding with severity and a `C-` prefixed ID.

---

## 1. Spend Aligned to Business Value

**Focus**: Spend traceable to a business outcome, ROI visible.

**Review Questions**:
- Can each significant cost line be tied to a feature, team, or customer
  segment (via labels / tags / projects)?
- Is unit economics tracked (cost per request, per active user, per GB
  processed) for the workloads it matters for?
- Are there cost drivers where the value is unclear or assumed?
- Is there a budget for this workload, and is overage understood?
- Are experimental / R&D costs visibly separated from production?

**Output Format**:
```markdown
### Spend Aligned to Business Value
- **Tagging / labeling**: [Complete / Partial / None]
- **Unit economics**: [Tracked / Estimated / Unknown]
- **Budget**: [Set / Implicit / None]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Major new spend with no budget, no ownership, and no value link |
| Important | Resources untagged, so spend can't be attributed; experimental and prod mixed |
| Nice-to-have | Add a unit-economics dashboard for the top 3 workloads |

---

## 2. Cost-Aware Culture

**Focus**: Engineers see and care about cost — visibility, accountability,
chargeback / showback.

**Review Questions**:
- Do engineers have access to a cost dashboard for their service?
- Is there a regular cost review cadence (monthly or sprintly)?
- Are budgets / alerts wired to owners, not a generic mailbox?
- Is cost a normal topic in design reviews, or only when finance asks?
- Are wins from cost optimization celebrated / shared?

**Output Format**:
```markdown
### Cost-Aware Culture
- **Engineer visibility**: [Yes / Finance-only / None]
- **Review cadence**: [Regular / Ad hoc / None]
- **Budget alerts**: [Owner-routed / Generic / None]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | No one notices when monthly spend doubles |
| Important | Engineers can't see their own service's cost; budget alerts go to a generic mailbox |
| Nice-to-have | Add a cost slide to the regular service review |

---

## 3. Resource Utilization Efficiency

**Focus**: Rightsizing, idle elimination, autoscaling tuned to actual demand.

**Review Questions**:
- Are compute instances / containers sized to actual usage (not 2× headroom
  "just in case")?
- Are idle / over-provisioned resources identified and cleaned up (orphaned
  disks, dev environments left running, oversized DBs)?
- Is autoscaling configured with sensible bounds, or is it static?
- Are environments shut down when not in use (dev, staging off-hours)?
- Are GPU / accelerator resources shared or fractional where possible?

**Output Format**:
```markdown
### Resource Utilization Efficiency
- **Rightsizing**: [Data-driven / Estimated / Default]
- **Idle resources**: [Reviewed / Suspected / Unknown]
- **Autoscaling**: [Dynamic / Static / None]
- **Off-hours shutdown**: [Yes / No / N/A]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Production DB sized for 100× current peak; large GPU pool reserved but mostly idle |
| Important | Static instance sizes never reviewed; dev environments left on 24/7 |
| Nice-to-have | Fractional GPUs for inference where supported |

---

## 4. Continuous Optimization

**Focus**: Commitment discounts, sustained use, storage lifecycle, regular
review.

**Review Questions**:
- Are committed-use / reserved-capacity discounts used where the workload is
  stable enough to justify?
- Are storage classes matched to access pattern (hot vs nearline vs
  archive), with lifecycle policies that demote / delete?
- Are spot / preemptible / interruptible resources used for fault-tolerant
  workloads (batch, CI, training)?
- Is there a regular pruning of unused resources (snapshots, old images,
  abandoned projects)?
- Are licensing / SaaS commitments reviewed for fit?

**Output Format**:
```markdown
### Continuous Optimization
- **Commitments / discounts**: [Used / Considered / Not used]
- **Storage lifecycle**: [Policies in place / Manual / None]
- **Spot / preemptible**: [Used for batch / Considered / Not used]
- **Pruning cadence**: [Regular / Ad hoc / None]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Long-running predictable workload paying full on-demand for a year |
| Important | Logs / backups kept in hot storage indefinitely; batch jobs on on-demand instances |
| Nice-to-have | Set up automated snapshot pruning |

---

## 5. Architectural Cost Drivers

**Focus**: Design choices that quietly drive bills — egress, cross-region,
chatty services, NAT.

**Review Questions**:
- Is data egress (internet or cross-region) understood and minimized?
- Is the service avoiding cross-zone / cross-region chatter where not
  required?
- Is NAT / load-balancer / managed-service per-request pricing accounted for
  in high-RPS designs?
- Is data movement (especially analytics extracts) sized and scheduled?
- Are caches / CDNs in use where they would meaningfully reduce origin cost?

**Output Format**:
```markdown
### Architectural Cost Drivers
- **Egress**: [Minimized / Acceptable / Large unknown]
- **Cross-zone / region traffic**: [Minimized / Default / Heavy]
- **Per-request priced services**: [Sized / Unknown]
- **Caching / CDN**: [Used / Considered / Not used]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Huge cross-region egress on a hot path; NAT-routed traffic that could be private; no CDN on a static-heavy public site |
| Important | Microservices chatty within the request path across zones; analytics extract pulls full table daily |
| Nice-to-have | Cache the catalog endpoint at the CDN edge |

---

## 6. Workload-Specific Cost Patterns

**Focus**: Pattern fit — serverless vs containers vs VMs; batch vs always-on;
AI/ML inference vs training cost shape.

**Review Questions**:
- Is the runtime model (serverless, containers, VMs, managed service)
  matched to traffic shape (bursty, steady, batch)?
- For batch workloads, is preemptible / spot capacity used and is the job
  idempotent enough to survive?
- For AI/ML, is training cost separated from inference, and is inference
  right-sized per traffic (batch, real-time, async)?
- For data: is processing pushed to the data (BigQuery / Spark) instead of
  shuttling data to compute?
- Are managed services chosen where the operational savings outweigh the
  premium (and vice versa)?

**Output Format**:
```markdown
### Workload-Specific Cost Patterns
- **Runtime fit**: [Matches traffic / Acceptable / Mismatched]
- **Batch capacity**: [Preemptible / On-demand / N/A]
- **AI/ML cost split**: [Tracked / Mixed / N/A]
- **Data locality**: [Pushed to data / Mixed / Shuttled]
- **Findings**: [Details]
- **Severity**: [...]
```

**Severity Guidance**:
| Severity | Examples |
|----------|----------|
| Critical | Always-on cluster for a low-traffic API that could be serverless; training and inference on the same expensive GPU pool |
| Important | Batch on on-demand instances; data extracted from warehouse for processing that could happen in warehouse |
| Nice-to-have | Consider async inference for non-interactive paths |
