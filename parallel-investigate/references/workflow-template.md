# Workflow Script Template

WHEN TO READ: during Step 3 (Launch the Workflow), as the starting pattern to
adapt for the actual investigation. Do not paste this verbatim into a real run —
fill in the real dimensions, prompts, and question first.

```js
export const meta = {
  name: '<short-kebab-case-slug>',
  description: 'Investigate: <one-line restatement of the question>',
  phases: [
    { title: 'Explore', detail: 'parallel deep-read across <N> dimensions' },
    { title: 'Synthesize', detail: 'merge findings into a ranked, cited answer' },
  ],
}

phase('Explore')

const dimensions = [
  {
    key: '<short-key>',
    label: 'explore:<short-key>',
    prompt: `You are investigating: <restate the symptom/question in full — agents
share no context with you or each other>.

Read these files/dirs in <repo path if not cwd>:
- <file/dir 1> — <what to look for>
- <file/dir 2> — <what to look for>

Report exactly:
1. <specific thing to trace, e.g. "the full code path from X to Y">
2. <every condition under which the symptom would/would not occur>
3. Cite file:line for every claim.`,
  },
  // ...one entry per dimension identified in Step 1
]

const findings = await parallel(
  dimensions.map(d => () => agent(d.prompt, { label: d.label, phase: 'Explore' })
    .then(text => ({ key: d.key, text })))
)

phase('Synthesize')

const bundle = findings.filter(Boolean)
  .map(f => `## Findings: ${f.key}\n${f.text}`).join('\n\n---\n\n')

const synthesis = await agent(
  `<paste the full instructions from references/synthesis-format.md, then:>

${bundle}`,
  { label: 'synthesis', phase: 'Synthesize' }
)

return { findings, synthesis }
```

Notes:
- `parallel()` between Explore and Synthesize is intentional and correct here —
  synthesis genuinely needs every Explore finding at once to cross-reference and
  rank them. This is the documented exception to "default to pipeline()" in the
  Workflow tool's own guidance.
- Each Explore prompt must be fully self-contained: restate the question, name
  the exact files/dirs, and specify exactly what to report back with citations.
  Agents do not see this conversation or each other's prompts.
- Label every agent (`explore:<dimension>`, `synthesis`) so `/workflows` progress
  is legible — this labeling is part of what makes the investigation "explicit"
  rather than an opaque background call.
- Launch with the `Workflow` tool directly (it runs in the background and
  returns a task ID immediately); do not wrap it inside a generic `Agent` call,
  which would hide the parallel structure from the user.
- If a dimension needs a different repo's working directory, say so in that
  dimension's own prompt (e.g. "Read these files under `~/tx/repos/<other-repo>/`")
  — do not assume the agent inherits your cwd.
