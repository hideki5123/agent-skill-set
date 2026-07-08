Feature: Parallel multi-agent codebase investigation
  Fan out multiple Workflow agents in parallel to investigate a codebase question,
  making the multi-agent orchestration explicit and visible instead of an implicit
  background behavior, then synthesize a ranked, cited answer in chat.

  Scenario: Investigate a cross-file bug root cause
    Given a codebase with a reported symptom whose cause is not obvious from one file
    When the user invokes /parallel-investigate "<question>" or says "並列で調査して: <question>"
    Then the skill decomposes the question into investigation dimensions
    And tells the user what those dimensions are before launching
    And runs a Workflow with one parallel agent per dimension in an Explore phase
    And follows with a Synthesize phase that cross-references findings into a
        ranked, file:line-cited answer
    And reports the ranked findings back in chat

  Scenario: Natural language trigger without the explicit command
    Given the user describes an investigation need in prose, not the slash command
    When the user says something like "複数エージェントで並列調査して" or
         "investigate this in parallel across the codebase"
    Then the skill recognizes the request
    And follows the same Workflow-based investigation flow as the explicit command

  Scenario: Investigation spans more than one local repository
    Given the question's answer could live in a related repo not currently open
        (e.g. a backend service and the client app that talks to it)
    When the user names the other repository, or the assistant cannot find the
        referenced component in the current repo and must look for it
    Then the skill locates the other repository (asking the user if it cannot be
        found automatically)
    And includes agents scoped to each repository as separate dimensions
    And the synthesis step attributes each finding to its source repository

  Scenario: Question is too vague to decompose
    Given the user's request lacks a concrete subject or codebase area
        ("調べて" with nothing else)
    When the skill attempts to identify investigation dimensions and cannot
    Then it asks the user 1-2 clarifying questions before launching any Workflow
    And does not guess dimensions or launch agents on a guess

  Scenario: Trivial question does not warrant fan-out
    Given the question can be answered by reading one file or a single targeted grep
    When the skill assesses that more than one investigation angle is not needed
    Then it explains this briefly and investigates directly
    And does not launch a multi-agent Workflow for it

  Scenario: Skill records feedback after execution
    Given the skill completed an investigation (success or failure)
    When the Retrospective step runs
    Then it reflects on the session (corrections, wrong decomposition, errors),
         asks the user for optional feedback, and appends a structured entry
         to feedback/log.md if feedback is provided or issues occurred

  Scenario: Skill notices recurring feedback pattern
    Given feedback/log.md has 5+ entries with a recurring issue
    When the skill is invoked and the Feedback Check runs
    Then it warns the user about the pattern and suggests
         /skill-improve --skill parallel-investigate

  Scenario: No feedback recorded when session is clean
    Given the investigation completed successfully with no corrections or issues
    When the user skips the feedback prompt
    Then no entry is written to feedback/log.md
