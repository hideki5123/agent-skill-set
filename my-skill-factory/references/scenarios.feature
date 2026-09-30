Feature: my-skill-factory
  Create, update, and install custom skills into the local hideki-plugins marketplace,
  keeping the factory's own knowledge current through two improvement loops:
  OIAE (inward, from this skill's feedback) and Ecosystem Refresh (outward, from
  Claude Code / Codex / model / spec changes).

  # WHEN TO READ: only when auditing or amending this skill
  # (e.g. /skill-improve --skill my-skill-factory). Never during normal execution.

  Scenario: Create a new skill from scratch
    Given the user has a clear idea for a new skill
    When the user says "create a skill for X"
    Then the skill gathers requirements, writes BDD scenarios, designs structure,
         assesses whether team orchestration is needed, includes team perspectives
         if warranted, creates files, installs, commits and pushes, and verifies

  Scenario: Skill assessed as needing team orchestration
    Given the user wants a skill with a multi-phase workflow touching security and architecture
    When the assessment finds 2+ criteria are true
    Then the skill includes a "Create an agent team..." step with selected perspectives
         and a references file with detailed teammate prompts

  Scenario: Skill assessed as NOT needing team orchestration
    Given the user wants a simple single-step utility skill
    When the assessment finds 0-1 criteria are true
    Then team orchestration is skipped and no team review step is included in the skill

  Scenario: Update an existing skill
    Given a skill is already installed in the marketplace
    When the user says "update the X skill to add Y"
    Then the skill writes change-delta scenarios, identifies added/modified/removed behaviors,
         edits files, always re-installs immediately without asking, commits and pushes, and verifies

  Scenario: Vague request
    Given the user provides only a one-line idea without details
    When the user says "make me a skill"
    Then the skill asks focused questions to clarify purpose, triggers, and output format

  Scenario: Skill with external dependencies
    Given the user needs a skill that relies on CLI tools or MCP servers
    When the user describes the skill's requirements
    Then the skill identifies dependencies, documents them in SKILL.md, and includes setup guidance

  Scenario: Re-install without changes
    Given a skill's files have not changed
    When the user re-runs the install script
    Then the script overwrites the previous installation and the skill remains functional

  Scenario: Feedback Check surfaces a recurring pattern in the factory itself
    Given my-skill-factory/feedback/log.md has 5+ entries with a common issue keyword in 3+
    When the factory is invoked
    Then it tells the user about the pattern and suggests
         /skill-improve --skill my-skill-factory, then continues normally

  Scenario: Retrospective recorded after a run with corrections
    Given the user rejected the initial design and asked for a different approach mid-run
    When the workflow completes
    Then the factory asks for a 1-5 rating in Japanese, creates feedback/log.md if missing,
         and prepends an entry capturing the corrections, the user's note, and the outcome

  Scenario: Retrospective skipped on a clean run
    Given the run had no corrections, no issues, and the user provides no feedback
    When the workflow completes
    Then the factory ends without writing to feedback/log.md

  Scenario: New skill must not contain hardcoded absolute paths
    Given the user is creating or editing a skill
    When the factory writes any of the skill's SKILL.md, references, or scripts
    Then no operator-specific path (/Users/..., /home/..., C:\..., D:\..., /private/...)
         appears in the skill's content except as an explicit documentation example
    And before install, the path-discipline grep is run and any non-example hits are
         replaced with <repo-root>, ~, $HOME, or runtime resolution

  Scenario: Improve a skill based on feedback
    Given a skill has feedback/log.md with recurring failure patterns
    When the user says "improve skill X" or "fix skill X based on feedback"
    Then the factory routes to /skill-improve, which reads all feedback, identifies patterns,
         proposes targeted amendments with evidence, applies approved changes,
         records in amendments.md, and re-installs

  Scenario: Evaluate previous amendments
    Given a skill has amendments with status "applied — monitoring"
    When the improve workflow (/skill-improve) runs
    Then it checks post-amendment feedback, updates amendment status to effective/ineffective,
         and suggests rollback for ineffective amendments

  Scenario: Skill has no feedback yet
    Given a skill's feedback/ directory does not exist or log.md is empty
    When the user asks to improve the skill
    Then the factory reports no feedback data and suggests running the skill a few times first

  # --- Ecosystem Refresh (v1.2.0) ---

  Scenario: Ecosystem check is not due
    Given the last refresh is recent and neither claude nor codex moved past the due policy
    When the factory is invoked
    Then ecosystem_check.py prints "due": false after two --version calls
    And the factory continues to Step 1 silently, reading no refresh protocol

  Scenario: Ecosystem check is due
    Given Claude Code or Codex moved past the due policy, or the last refresh is too old
    When the factory is invoked
    Then it reads references/ecosystem-refresh.md, launches the research brief as a
         background subagent, tells the user in one Japanese line, and starts Step 1
         without waiting

  Scenario: Research proposals require approval even in auto-mode
    Given the background research returned proposals with primary-source citations
    When Step 2 begins
    Then every proposal is shown via AskUserQuestion with its claim and source
    And only approved items are used in this run's design
    And no proposal is written to disk before the primary task completes

  Scenario: Research still running when Step 2 starts
    Given the background research has not returned yet
    When Step 2 begins
    Then the factory designs with the current knowledge base and triages the proposals
         at the end instead of blocking the user

  Scenario: Write-back after the primary task
    Given the user approved some proposals and declined others
    When Step 5 of the primary task has completed and its commit is pushed
    Then approved items are written to references/ecosystem-practices.md,
         declined titles are added to feedback/ecosystem-state.json,
         ecosystem_check.py record stamps the versions and date,
         an AMD-NNN entry with Source: ecosystem-refresh is appended,
         and the factory is re-installed with an explicit --version and committed separately

  Scenario: Every proposal declined
    Given the user declined every proposal
    When the write-back runs
    Then no knowledge-base or version change is made
    But ecosystem_check.py record still runs and the state file is committed,
        so the same research does not re-run on the next invocation

  Scenario: Synced machine runs an older CLI than recorded
    Given the state file records claude 2.1.285 and this machine runs claude 2.1.278
    When the factory is invoked
    Then the older local version is not a reason to refresh

  Scenario: One CLI is not installed
    Given codex is not installed on this machine
    When ecosystem_check.py runs
    Then the codex version is null, the check still completes with exit code 0,
         and the absent tool is not a reason to refresh

  Scenario: No background subagent available
    Given the factory is running under Codex, where no background subagent can be spawned
    When the ecosystem check is due
    Then the refresh is skipped without running record, so the next Claude Code run picks it up
