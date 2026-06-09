# Brief Review Team

Before the Codex loop, create a small agent team to harden the DRAFT brief from
angles Codex (a single external reviewer) covers unevenly. Run them in parallel,
then synthesize. Skip entirely if `--no-team`.

"Create an agent team to explore this from different angles: **Brief Fidelity,
Implementability, Idempotence & Safety**."

Give each teammate: the draft brief, and a summary of the grilled session's
decisions (sections 2 and 4 of the brief, plus anything from the grill not yet in
the brief).

## Perspective 1 — Brief Fidelity

**Focus:** Does the brief faithfully capture EVERYTHING decided during the grill?

Review questions:
1. Is every locked decision from the grill present in §4, unaltered?
2. Is every non-goal / exclusion in §2? (Dropped non-goals are the worst failure.)
3. Were any decisions softened, contradicted, or silently "improved"?
4. Are file/line anchors and constraints carried over, not lost in summarization?
5. Is the original intent (incl. non-English framing) preserved?

```markdown
## Brief Fidelity Review
### Dropped / altered decisions
- [decision in grill → how the brief differs, or "none"]
### Missing non-goals or constraints
- [...]
### Recommendations
- [exact text to restore]
### Risks
- [what the spawned agent would get wrong from these gaps]
```

## Perspective 2 — Implementability

**Focus:** Can a COLD autonomous agent (zero prior context) execute this?

Review questions:
1. Does every step have a real, navigable path/symbol anchor?
2. Are there unstated assumptions (env, tooling, access, prior state)?
3. Are acceptance criteria observable and checkable?
4. Is the branch/setup section complete for every repo, with order?
5. Where would the agent have to guess? Name each ambiguity.

```markdown
## Implementability Review
### Missing anchors / ambiguous steps
- [...]
### Unstated assumptions
- [...]
### Unverifiable acceptance criteria
- [...]
### Recommendations
- [...]
```

## Perspective 3 — Idempotence & Safety

**Focus:** The brief launches an autonomous, permission-bypassing agent. Is that safe?

Review questions:
1. Is scope bounded so the agent won't wander beyond the feature?
2. Is the branch setup safe (fresh feature branch, never main/integration/doc/PR branch)?
3. Are destructive or irreversible operations called out and guarded?
4. Can the work be re-run / resumed without duplication or corruption?
5. Are external side effects (pushes, external services, spawned sub-sessions) explicit?

```markdown
## Idempotence & Safety Review
### Scope-bounding gaps
- [...]
### Branch / write safety
- [...]
### Destructive ops without guards
- [...]
### Recommendations
- [...]
```

## Synthesis Protocol

1. **Collect** findings from all three teammates.
2. **Categorize**: Critical (blocks safe execution) / Important (quality) / Nice-to-have.
3. **Deduplicate** overlaps.
4. **Fold** Critical + Important findings back into the brief BEFORE the Codex loop.
5. **Note** unresolved Nice-to-haves in the brief's Risks (§8).
6. Proceed to the Codex review loop with the hardened brief.
