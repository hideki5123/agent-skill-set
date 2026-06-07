Feature: prd-council — adversarial PRD authoring and execution-ready doc generation
  As a user with a feature idea
  I want a PRD debated with Codex to mutual approval, then technical docs and tasks
  So that a PdM-role agent could later distribute the work to specialist agents
  Document-generation only — the skill never executes the specialist agents.

  Background:
    Given prd-council is invoked in a target project
    And the document language follows the session language
    And commit messages are always English

  Scenario: Happy path — grill, draft, Codex approval, technical docs, tasks
    Given Codex is available via the user's ChatGPT login
    When prd-council runs
    Then it runs the Phase-1 requirements checkpoint (assess context, then grill open branches)
    And it drafts prd.md from the agreed requirements and codebase
    And it debates prd.md with Codex round-by-round requesting structured verdicts
    And it stops when Codex returns approve and Claude has no unresolved objection
    And it writes debate-log.md with every round
    And it writes technical-prd-summary.md and one technical-prd-<usecase>.md per UseCase
    And it writes tasks.md grouped by UseCase with role, dependencies, and acceptance
    And all files are written under docs/prd/<slug>/

  Scenario: Already grilled — confirm, do not re-interrogate
    Given the requirements are already resolved (a prior grill-me pass in this
      conversation, or a passed-in PRD/ticket, or rich codebase signal)
    When prd-council runs Phase 1 with --grill auto
    Then it runs the shared-understanding assessment first and builds a grill ledger
    And it presents a consolidated requirements summary for a single confirm-or-correct
    And it grills only the still-open branches, not the resolved ones

  Scenario: Thin context — full grill
    Given little about the feature is resolvable from context or the codebase
    When prd-council runs Phase 1 with --grill auto
    Then it runs the full one-question-at-a-time grill

  Scenario: Grill depth overrides
    Given --grill full is passed
    Then prd-council runs a complete grill even if context looks sufficient
    Given --grill skip is passed
    Then prd-council trusts the context but still shows the summary for one confirm

  Scenario: Codex requests revisions before approving
    Given Codex returns verdict "revise" with blocking_issues
    When prd-council receives the verdict
    Then it resolves every blocking issue and revises prd.md
    And it re-sends the revised PRD with a changelog on the same thread
    And it continues until mutual approval or the round cap

  Scenario: Non-convergence escalates to the user
    Given the debate reaches the round cap without mutual approval
    When the cap is hit
    Then prd-council stops looping
    And it surfaces the open disagreements to the user for a decision
    And debate-log.md records "escalated after N rounds"

  Scenario: Heavy council mode
    Given the invocation includes --council heavy
    When the debate runs
    Then each round gathers a Codex verdict plus Claude self-critique across lenses
    And a round passes only when Codex and every lens approve

  Scenario: Codex unavailable — graceful degradation
    Given ~/.codex/auth.json is missing or --no-codex is set
    When prd-council reaches the debate phase
    Then it runs a Claude-only self-critique council instead of skipping the loop
    And debate-log.md is clearly marked DEGRADED
    And the user is advised to run codex login for a true council

  Scenario: Roster resolution binds to an installed subagent
    Given the project stack is .NET and a dotnet-senior subagent is installed
    When prd-council resolves the roster in Phase 4
    Then the Backend role is bound to @agent-…:dotnet-senior in the roster table
    And roles with no matching installed subagent keep their generic label

  Scenario: Roster override
    Given the invocation includes --agents "frontend,backend,qa"
    When the roster is resolved
    Then only those roles (plus PdM) appear, overriding auto-selection

  Scenario: Document-generation boundary — no execution
    Given the deliverables are written
    When prd-council finishes
    Then it does NOT spawn or run any specialist agent
    And it prints an index of the generated files only

  Scenario: Local-only output — no publishing
    When prd-council finalizes
    Then it writes files locally under the output directory
    And it does not publish to Jira, Notion, Confluence, or GitHub

  Scenario: UseCases drive the per-UseCase documents
    Given the PRD enumerates N distinct UseCases
    When the technical documents are generated
    Then exactly N technical-prd-<usecase>.md files are produced
    And tasks.md is grouped by those same UseCases
