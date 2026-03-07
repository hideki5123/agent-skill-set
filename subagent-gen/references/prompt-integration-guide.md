# Using PROJECT-KNOWLEDGE.md in Subagent Prompts

Profiles are stored globally at `~/.claude/knowledge/{name}.md` and symlinked
locally at `.agent/local/PROJECT-KNOWLEDGE.md`. Both paths point to the same file.

## Quick Start

When spawning any subagent (via the Agent tool), prepend the profile:

```
Read .agent/local/PROJECT-KNOWLEDGE.md for deep codebase context, then:

<your actual task prompt here>
```

The subagent will read the profile and have instant domain expertise.

## Selective Section Loading

For token-constrained subagents or narrow tasks, instruct the agent to focus on
specific sections:

| Task Type | Sections to Load |
|-----------|-----------------|
| Bug investigation | Structure + Architecture + Conventions |
| Architecture question | Architecture + Structure + Tech Stack |
| New feature implementation | All sections (full profile) |
| Code review | Conventions + Architecture + Domain Concepts |
| API work | API Surface + Architecture + Domain Concepts |
| Config / deployment | Configuration + Tech Stack + Structure |
| Testing | Conventions (Testing subsection) + Structure |
| Onboarding / Q&A | All sections (full profile) |

Example for a focused prompt:

```
Read the "Architecture" and "Domain Concepts" sections from
.agent/local/PROJECT-KNOWLEDGE.md for context, then:

Explain how the telemetry ingestion pipeline works, from device
data arriving at the API to storage in the database.
```

## Example: Explore Agent with Profile

```
You are investigating a performance issue in the device telemetry pipeline.

Read .agent/local/PROJECT-KNOWLEDGE.md for full codebase context.

Then find why telemetry data for device X arrives with 5-minute delays.
Start from the ingestion entry point identified in the profile and trace
through the pipeline. Focus on queue processing and batch commit timing.
```

## Example: Code Review Agent with Profile

```
You are reviewing a pull request that changes the authentication flow.

Read .agent/local/PROJECT-KNOWLEDGE.md for codebase conventions and
architecture context.

Then review the diff below against the project's established patterns for:
- Auth guard usage (see Conventions > Patterns > Auth guards)
- Error handling style (see Conventions > Patterns > Error handling)
- State management approach (see Architecture > State Management)

<diff>
{paste diff here}
</diff>
```

## Cross-Project Usage

Profiles are stored globally, so any project can reference any other project's knowledge.

### Reference another project's profile

```
Read ~/.claude/knowledge/backend-api.md for the backend API's architecture, then:

This frontend component needs to call the /api/v1/devices endpoint.
Based on the backend's conventions, what request format and auth headers
should I use? What response shape should I expect?
```

### Combine multiple project profiles

```
Read ~/.claude/knowledge/frontend-app.md and ~/.claude/knowledge/backend-api.md
for context on both projects, then:

Design the integration between the frontend dashboard and the backend
telemetry API. Consider both projects' conventions and patterns.
```

### List available profiles

Use `/subagent-gen --list` or check directly:

```bash
ls ~/.claude/knowledge/
```

### Example: Working in frontend, need backend knowledge

```
You are implementing a new data fetching hook in the frontend.

Read ~/.claude/knowledge/backend-api.md for the backend's API surface and
auth patterns. Read .agent/local/PROJECT-KNOWLEDGE.md for this frontend
project's conventions.

Create a useDeviceTelemetry hook that fetches telemetry data, following
this project's hook patterns and the backend's API conventions.
```

## Keeping the Profile Fresh

Run the subagent-gen skill with `--update` periodically, especially after:
- Major refactors or architectural changes
- New module or package additions
- Framework upgrades
- Dependency changes that affect patterns
- Before onboarding a new team member (to verify accuracy)

The update mode preserves any custom annotations you've added (wrapped in
`<!-- USER: ... -->` comments) while refreshing machine-generated sections.

## Tips

- **Don't over-include**: A focused subagent with 2 relevant sections performs
  better than one loaded with the entire profile for a narrow task.
- **Combine with HANDOVER.md**: If using session-handover, the subagent can read
  both files for project knowledge + current session context.
- **Custom annotations**: Add `<!-- USER: important context here -->` blocks to
  the profile for details that automated analysis might miss (e.g., "we're
  migrating from REST to GraphQL — new endpoints go in api/graphql/").
- **Cross-project naming**: Use meaningful `--name` values (e.g., `backend-api`,
  `frontend-dashboard`) so profiles are easy to find in `~/.claude/knowledge/`.
