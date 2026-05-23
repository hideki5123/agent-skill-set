# PMBOK Review Guide

Review local git changes against these 7 PMBOK knowledge areas. For each area, use the review questions to guide analysis, then produce findings using the output format.

---

## 1. Scope Management

**Focus**: Alignment with project scope, feature creep detection, requirement traceability.

**Review Questions**:
- Does this change implement defined requirements, or does it introduce unplanned scope?
- Is there evidence of feature creep (functionality beyond what was requested)?
- Can this change be traced back to a user story, issue, or requirement?
- Does the change modify or extend the project's boundaries?
- Are there any "while I'm here" changes mixed in?

**Output Format**:
```markdown
### Scope Management
- **Scope alignment**: [In scope / Partial / Out of scope]
- **Feature creep risk**: [None / Low / Medium / High]
- **Findings**: [Details about scope alignment or creep concerns]
- **Recommendations**: [Actions to take]
```

---

## 2. Risk Management

**Focus**: New risks introduced, risks mitigated, risk response strategies.

**Review Questions**:
- What new technical risks does this change introduce?
- Does this change mitigate any existing risks?
- What is the blast radius if this change fails in production?
- Are there rollback or recovery strategies?
- Does this change affect any critical paths?

**Output Format**:
```markdown
### Risk Management
- **New risks**: [List of risks introduced]
- **Risks mitigated**: [List of risks addressed]
- **Blast radius**: [Low / Medium / High — what breaks if this fails]
- **Rollback strategy**: [How to undo if needed]
- **Recommendations**: [Risk response actions]
```

---

## 3. Stakeholder Impact

**Focus**: Who is affected, communication needs, user-facing changes.

**Review Questions**:
- Which stakeholders are affected (end users, ops team, other devs, QA)?
- Are there user-facing changes that need documentation or communication?
- Does this change affect any APIs consumed by other teams?
- Is training or documentation update needed?
- Should any stakeholder be notified before deployment?

**Output Format**:
```markdown
### Stakeholder Impact
- **Affected stakeholders**: [List with impact description]
- **User-facing changes**: [Yes/No — details if yes]
- **Communication needed**: [Who needs to know, and when]
- **Documentation updates**: [What docs need updating]
- **Recommendations**: [Communication and documentation actions]
```

---

## 4. Quality Management

**Focus**: Quality standards, acceptance criteria, definition of done.

**Review Questions**:
- Does this change meet the project's quality standards?
- Are acceptance criteria defined and met?
- Does it pass the definition of done (tests, docs, review)?
- Are there quality metrics that should be tracked?
- Does this change maintain or improve code quality baselines?

**Output Format**:
```markdown
### Quality Management
- **Quality standards met**: [Yes / Partially / No]
- **Acceptance criteria**: [Defined and met / Missing / Partially met]
- **Definition of done**: [Complete / Gaps identified]
- **Findings**: [Quality assessment details]
- **Recommendations**: [Actions to meet quality standards]
```

---

## 5. Integration Management

**Focus**: Component integration, system-level impacts, dependency coordination.

**Review Questions**:
- How does this change integrate with existing components?
- Are there upstream or downstream dependencies affected?
- Does this change require coordinated deployment with other changes?
- Are integration points properly tested?
- Does it affect shared configuration, databases, or infrastructure?

**Output Format**:
```markdown
### Integration Management
- **Integration points**: [Components/systems affected]
- **Dependency impacts**: [Upstream and downstream effects]
- **Coordinated deployment needed**: [Yes/No — details]
- **Findings**: [Integration assessment]
- **Recommendations**: [Integration actions]
```

---

## 6. Schedule Impact

**Focus**: Timeline effects, dependency chains, critical path impact.

**Review Questions**:
- Does this change add to the project timeline?
- Are there downstream tasks that depend on this change?
- Does this change block or unblock other work?
- Is this change time-sensitive (security fix, deadline, dependency)?
- Does the complexity suggest the estimate needs revision?

**Output Format**:
```markdown
### Schedule Impact
- **Timeline effect**: [None / Adds time / Saves time]
- **Blocking/unblocking**: [What this enables or blocks]
- **Time sensitivity**: [Low / Medium / High — why]
- **Findings**: [Schedule assessment]
- **Recommendations**: [Schedule actions]
```

---

## 7. Resource Management

**Focus**: Team capacity, skill requirements, tooling and infrastructure needs.

**Review Questions**:
- Does this change require specialized knowledge to maintain?
- Are there new tooling or infrastructure requirements?
- Does it increase operational burden (monitoring, on-call, maintenance)?
- Is the change well-documented enough for team handoff?
- Does it affect team capacity or require additional resources?

**Output Format**:
```markdown
### Resource Management
- **Specialized knowledge needed**: [Yes/No — what kind]
- **New tooling/infrastructure**: [Requirements if any]
- **Operational burden**: [Increases / Neutral / Decreases]
- **Team readiness**: [Assessment of team ability to maintain this]
- **Recommendations**: [Resource actions]
```
