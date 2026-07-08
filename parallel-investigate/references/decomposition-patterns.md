# Decomposition Patterns

WHEN TO READ: during Step 1 (Scope the question), when deciding how many agents to
launch and what each should investigate.

Good decomposition is the single highest-leverage decision in this skill. Bad
decomposition (dimensions that overlap, or that are too coarse to parallelize)
wastes agent-turns without improving the answer. Pick ONE of these patterns, or
combine two when the question genuinely spans both axes.

## By layer (most common — "why does X happen" bug/behavior questions)

Split along the path the data/control flow actually takes. A typical service or
app bug decomposes into:
- **Read/display path** — where the value is rendered or consumed (UI, API
  response, log line)
- **Write/update path** — the business logic that produces or mutates the value
- **Trigger/entry point** — the real-world event that invokes the write path (an
  RPC call, a webhook, a cron job, a user action)
- **Persistence** — the data model and storage layer (schema, migrations,
  query/write correctness)
- **Tests** — existing tests often encode already-known edge cases; a dedicated
  test-reading agent surfaces documented exclusions fast

Worked example: "some rows show a missing field in a dashboard" decomposed into
exactly these five dimensions — UI display logic, the usecase that computes/writes
the field, the RPC/event that triggers that usecase, the DB read/write path, and
the existing test suite. The test-reading agent and the write-logic agent
independently converged on the same root cause (a permission gate silently
skipping certain accounts) without being told to look for it — that independent
convergence is what justified tagging the answer CONFIRMED rather than PLAUSIBLE
(see `synthesis-format.md`).

## By repository (cross-repo questions)

When the symptom's cause could live in more than one local repo — e.g. a backend
service and the client app that talks to it — assign one dimension (or one
sub-cluster of dimensions) per repository. Do not assume the answer lives only in
the repo the user is currently sitting in; if the codebase references an external
component whose source is not present (grep for it and get nothing), say so
explicitly and look for it:

1. Check common sibling-repo roots on this machine (e.g. `~/tx/repos/`,
   `~/repos/`, `~/dev/` — adjust to whatever this user's layout actually looks
   like) with a shallow `find`/`ls` for a plausibly-named directory.
2. If nothing plausible turns up, ask the user for the repo name/path in one
   question rather than guessing or giving up silently.
3. Before reading a repo you did not already have open, run `git status` — if it
   is on a non-default branch with uncommitted changes, investigate the working
   tree as-is (read-only) rather than switching branches or pulling; that is
   someone's in-progress work and must not be disturbed by an investigation task.

Once located, treat each repo's relevant dimensions as their own Explore-phase
agents, with the repo path made explicit in the prompt (agents don't share your
cwd or your conversation context). The synthesis step should attribute each
finding to its repo so the final answer is traceable.

## By hypothesis (competing-theories questions)

When the question is "is it A or B" rather than "trace the flow", give each
candidate hypothesis its own agent with instructions to actively look for
evidence *against* its own hypothesis first (this avoids confirmation bias), then
report what it found either way. The synthesis step adjudicates between
hypotheses using that evidence.

## Sizing

- 3-5 dimensions is the common range. Fewer than 3 rarely benefits from
  parallelization — investigate directly instead (see the trivial-question guard
  in SKILL.md Step 1).
- More than ~6 dimensions usually means the decomposition is too fine-grained;
  merge overlapping ones (e.g. "list-view read path" and "detail-view read path"
  are usually one dimension, not two, unless they are genuinely different code
  paths worth separating).
