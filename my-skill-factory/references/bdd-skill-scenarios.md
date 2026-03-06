# BDD Scenarios for Skill Design

Use Given/When/Then scenarios to specify what a skill should do before building it. These are **design specifications**, not executable tests.

## Vocabulary

| Keyword | Meaning in skill context |
|---------|--------------------------|
| **Given** | Trigger context — what state/situation the user is in |
| **When** | User action — what the user says or does to invoke the skill |
| **Then** | Skill output — what Claude produces, creates, or modifies |

## Writing Good Scenarios

Aim for 3-5 scenarios per skill:
1. **Primary use case** — the most common invocation
2. **Secondary path** — an alternative input or mode
3. **Edge case** — missing info, invalid input, or boundary condition

### Template

```gherkin
Scenario: <descriptive name>
  Given <context about the user's situation>
  When <user action or phrase>
  Then <what the skill produces>
```

## Patterns by Skill Type

### Workflow skills (sequential steps)

```gherkin
Scenario: Full workflow from scratch
  Given the user has no existing <artifact>
  When the user invokes the skill with a goal description
  Then the skill walks through each step and produces <output>

Scenario: Partial input provided
  Given the user already has <partial artifact>
  When the user invokes the skill with existing context
  Then the skill skips completed steps and continues from the right point
```

### Analysis skills (inspect and report)

```gherkin
Scenario: Standard analysis
  Given a codebase with <characteristic>
  When the user asks to analyze <target>
  Then the skill produces a report covering <sections>

Scenario: Nothing to report
  Given a codebase with no issues in <area>
  When the user asks to analyze <target>
  Then the skill confirms no issues found with brief summary
```

### Task skills (single operation)

```gherkin
Scenario: Successful task
  Given <preconditions>
  When the user asks to <action>
  Then the skill performs <operation> and confirms completion

Scenario: Missing prerequisites
  Given <precondition> is not met
  When the user asks to <action>
  Then the skill explains what is needed and how to set it up
```

## Self-Referential Example (Skill Factory)

```gherkin
Scenario: Create a new skill from scratch
  Given the user has a clear idea for a new skill
  When the user says "create a skill for X"
  Then the skill gathers requirements, designs structure, creates files, installs, and verifies

Scenario: Update an existing skill
  Given a skill is already installed in the marketplace
  When the user says "update the X skill to add Y"
  Then the skill writes change-delta scenarios, edits files, re-installs, and verifies

Scenario: Vague request
  Given the user provides only a one-line idea
  When the user says "make me a skill"
  Then the skill asks focused questions to clarify purpose, triggers, and outputs
```

## Update-Delta Scenarios

When modifying an existing skill, write scenarios that describe **only what changes**:

```gherkin
Scenario: New capability added
  Given the skill currently does A and B
  When the user invokes the skill for new capability C
  Then the skill also handles C while A and B remain unchanged

Scenario: Behavior modification
  Given the skill currently produces output in format X
  When the user invokes the skill
  Then the skill produces output in format Y instead
```

Compare new scenarios against existing ones to identify:
- **Added** — new scenarios not covered before
- **Modified** — existing scenarios whose Then clause changes
- **Removed** — scenarios that no longer apply

## Anti-Patterns

| Problem | Example | Fix |
|---------|---------|-----|
| Too implementation-specific | "Then Claude reads line 42 of config.yaml" | Describe outcomes, not mechanics |
| Too vague | "Then the skill works correctly" | Specify what "correctly" means |
| Too many scenarios | 15+ scenarios for a simple skill | Stick to 3-5; group related behaviors |
| Testing internals | "Then the SKILL.md contains a ## Step 2 section" | Focus on user-visible behavior |
| Duplicate coverage | Two scenarios testing the same path | Merge or pick the more descriptive one |
