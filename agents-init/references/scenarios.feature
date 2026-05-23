Feature: agents-init wires AGENTS.md as source of truth with CLAUDE.md as symlink
  Codex CLI (and Aider, Cursor, etc.) read AGENTS.md.
  Claude Code reads CLAUDE.md. Maintaining both by hand causes drift.
  This skill makes AGENTS.md the real file and CLAUDE.md a symlink to it.

  Background:
    Given the current directory is a git repository

  Scenario: Green-field repo with no existing context files
    Given neither CLAUDE.md nor AGENTS.md exists
    When the user runs /agents-init
    Then the skill detects state "needs-init"
    And the skill invokes Claude's built-in /init to generate CLAUDE.md
    And the script renames CLAUDE.md to AGENTS.md
    And the script creates CLAUDE.md as a symlink to AGENTS.md
    And the user is shown the recommended git commit command

  Scenario: Pre-existing hand-written CLAUDE.md
    Given only CLAUDE.md exists as a regular file
    When the user runs /agents-init
    Then the skill detects state "ready-claude"
    And the user is asked to confirm renaming
    When the user confirms
    Then CLAUDE.md is renamed to AGENTS.md and symlinked back
    And /init is NOT invoked

  Scenario: Pre-existing AGENTS.md only
    Given only AGENTS.md exists
    When the user runs /agents-init
    Then the skill detects state "ready-agents"
    And the script creates CLAUDE.md as a symlink to AGENTS.md
    And no rename occurs

  Scenario: Both files exist with byte-identical content
    Given CLAUDE.md and AGENTS.md exist with identical content
    When the user runs /agents-init
    Then the skill detects state "identical"
    And the script deletes the duplicate CLAUDE.md
    And the script creates CLAUDE.md as a symlink to AGENTS.md

  Scenario: Both files exist with different content, user keeps AGENTS
    Given CLAUDE.md and AGENTS.md exist with different content
    When the user runs /agents-init
    Then the skill detects state "conflict"
    And a unified diff is printed to stderr
    And the user is asked which to keep
    When the user chooses "keep AGENTS.md"
    Then the script runs --wire --prefer=agents
    And CLAUDE.md is deleted and re-created as a symlink

  Scenario: Both files exist with different content, user keeps CLAUDE
    Given CLAUDE.md and AGENTS.md exist with different content
    When the user runs /agents-init and chooses "keep CLAUDE.md"
    Then the script runs --wire --prefer=claude
    And AGENTS.md is backed up to AGENTS.md.bak.<unix-timestamp>
    And CLAUDE.md is renamed to AGENTS.md
    And CLAUDE.md is re-created as a symlink

  Scenario: Idempotent re-run on already-wired repo
    Given CLAUDE.md is a symlink to AGENTS.md and AGENTS.md exists
    When the user runs /agents-init
    Then the skill detects state "wired"
    And no filesystem changes are made
    And the user is told "already wired"

  Scenario: Foreign symlink (CLAUDE.md points somewhere unexpected)
    Given CLAUDE.md is a symlink to some other path
    When the user runs /agents-init
    Then the skill detects state "foreign-symlink"
    And the skill stops and asks the user before repointing
    When the user confirms
    Then the script runs --wire --force
    And CLAUDE.md is unlinked and re-created as a symlink to AGENTS.md

  Scenario: Not inside a git repository
    Given the current directory is not a git repository
    When --wire or --detect runs without --allow-non-git
    Then the script refuses with an error
    And the user is told to pass --allow-non-git to override

  Scenario: File ignored by .gitignore
    Given .gitignore contains a top-level entry for CLAUDE.md or AGENTS.md
    When the script runs --wire
    Then the wiring completes
    And the result JSON includes a warning that the file will not be committed

  Scenario: Windows host falls back to file copy
    Given the script runs on win32
    When --wire creates the companion file
    Then shutil.copyfile is used instead of os.symlink
    And the actions list includes a WARNING line about re-running after edits
