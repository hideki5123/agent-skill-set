# Grill Protocol (Phase 1)

**WHEN TO READ:** at the start of Phase 1 (always — prd-council holds a
requirements checkpoint before drafting). Not needed otherwise.

The goal of Phase 1 is a *shared understanding* of the feature before a single
line of PRD is written. This is the grill-me approach applied to PRD intake. The
checkpoint is mandatory; its **depth adapts** to what context already resolves, so
an already-grilled user gets a confirmation, not a re-interrogation.

## Shared-understanding assessment (run this FIRST)

Before asking anything, find out how much is already settled.

1. **Gather existing signal.** Read what the context already provides:
   - this conversation (a prior `grill-me` / `grill-with-docs` pass, or decisions
     the user already stated);
   - any artifact passed in or referenced (an existing PRD/requirements draft, a
     ticket, a design doc);
   - the codebase (stack, modules, conventions, ADRs, prior art).
2. **Build the grill ledger.** For each item the PRD needs — problem, solution,
   scope/out-of-scope, **UseCases**, seams/test boundaries, constraints, roster
   hints, council depth — mark it **resolved** or **open** from that signal.
3. **Branch on coverage (respecting `--grill`):**
   - **`--grill full`** → run the full grill regardless.
   - **`--grill skip`** → trust the context; render the requirements summary and
     ask for one confirm-or-correct, then proceed.
   - **`auto` (default):**
     - *Mostly resolved* (only minor gaps): present a **consolidated requirements
       summary** (problem, solution, UseCases, scope, constraints) and ask for a
       **single confirm-or-correct pass**. Grill only the still-open items. Do not
       re-walk resolved branches.
     - *Thin* (much is open): run the full grill below.
4. **Never zero-touch.** Even when everything looks resolved, always show the
   summary and get one explicit confirmation — that is the mandatory checkpoint.

## Rules (for the branches that still need grilling)

1. **One question at a time.** Walk down each branch of the decision tree,
   resolving dependencies between decisions one-by-one. A later question often
   depends on an earlier answer — do not batch dependent questions.
2. **Always recommend an answer.** For every question, state your recommended
   answer and a one-line rationale. Use `AskUserQuestion` with the recommended
   option first, labeled "(Recommended)".
3. **Explore before asking.** If a question can be answered by reading the
   codebase (stack, existing modules, naming conventions, ADRs, prior art),
   explore instead of asking. Only ask the human what the code cannot tell you.
4. **Independent leaves may be batched.** Once the dependent/architectural branches
   are resolved, a few genuinely independent leaf decisions can be asked together.
5. **Stop when shared understanding is reached** — when you could write the PRD and
   defend every decision. Over-grilling wastes the user's time; under-grilling
   produces a weak PRD the Codex council will tear apart.

## Decision tree to resolve (typical order)

Resolve top-down; skip any the codebase already answers.

1. **Problem & affected users** — what pain, for whom, why now. (Root.)
2. **Solution shape** — the user-facing solution. Confirm scope boundaries
   (what's explicitly out).
3. **UseCases** — enumerate the distinct UseCases. *These become the per-UseCase
   Technical PRDs in Phase 4*, so resolving them well here is high-leverage. For
   each: actor, trigger, main flow, primary edge case.
4. **Seams / test boundaries** — where the feature will be tested. Prefer existing
   seams; propose new ones at the highest point. Confirm with the user.
5. **Constraints** — non-functional requirements: performance, security/permissions,
   data/schema changes, API contracts, compatibility, deadlines.
6. **Roster hints** — does the user have a specific agent roster in mind, or should
   prd-council derive it (default)? (Feeds Phase 4 roster resolution.)
7. **Council depth** — is this high-stakes enough to warrant `--council heavy`?
   Recommend `default` unless the PRD is large or risky.

## Anti-patterns

- Asking what a 30-second `grep`/file read would answer.
- Asking many questions at once when answers gate each other.
- Accepting a vague "make it good" — push for the specific decision.
- Skipping the UseCase enumeration — it is the backbone of every later artifact.
