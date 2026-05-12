# BDD spec for skill-improve.
#
# Read only by /skill-improve audit tooling or when amending the skill —
# NOT loaded during normal execution.

Feature: skill-improve — OIAE retrofit + feedback-driven amendments

  Scenario: Retrofit OIAE to skill without feedback loop
    Given an existing skill has no Retrospective, Feedback Check, or version field
    When /skill-improve --skill <name> is invoked
    Then assess opt-in level, present to user, add missing OIAE components,
         install, commit, and push

  Scenario: Analyze feedback and propose amendments
    Given a skill has feedback/log.md with recurring issues
    When /skill-improve --skill <name> is invoked
    Then read all feedback, identify patterns, propose amendments with evidence,
         apply approved changes, record in amendments.md, install, commit, and push

  Scenario: Skill already has OIAE and no feedback yet
    Given a skill has Retrospective and Feedback Check but no feedback/log.md
    When /skill-improve --skill <name> is invoked
    Then report that OIAE components are present but no feedback data exists yet,
         and suggest running the skill a few times to collect data

  Scenario: Evaluate previous amendments
    Given a skill has amendments in "applied — monitoring" status
    When /skill-improve --skill <name> is invoked
    Then check post-amendment feedback entries, update amendment status
         to effective or ineffective, and suggest rollback if ineffective

  Scenario: Retrofit-only mode
    Given --retrofit-only flag is set
    When /skill-improve --skill <name> --retrofit-only is invoked
    Then only add missing OIAE components, skip feedback analysis

  Scenario: Analyze-only mode
    Given --analyze-only flag is set and feedback exists
    When /skill-improve --skill <name> --analyze-only is invoked
    Then only analyze feedback and propose amendments, skip retrofit

  Scenario: Feedback Check surfaces a recurring pattern in skill-improve itself
    Given skill-improve/feedback/log.md has 5+ entries with a common issue keyword in 3+
    When /skill-improve is invoked on any target
    Then it tells the user about the pattern and suggests
         /skill-improve --skill skill-improve, then continues normally on the requested target

  Scenario: Retrospective with low rating triggers WHY follow-up
    Given the user provides a rating of 1-4 in the Retrospective
    When Phase 4 (Report) completes
    Then skill-improve asks the WHY follow-up in Japanese before recording the entry
    And the recorded entry has a Rating reason field populated verbatim

  Scenario: Retrospective recorded after a run with corrections
    Given the user rejected a proposed amendment or course-corrected mid-run
    When Phase 4 (Report) completes
    Then skill-improve asks for a 1-5 rating in Japanese, creates feedback/log.md if missing,
         and prepends an entry capturing the corrections, the user's note, and the outcome

  Scenario: Retrospective skipped on a clean run
    Given the run had no corrections, no issues, and the user provides no feedback
    When Phase 4 (Report) completes
    Then skill-improve ends without writing to feedback/log.md

  Scenario: Retrofits and amendments must not introduce hardcoded paths
    Given the skill is being retrofitted with OIAE components or amended based on feedback
    When new content is written into the target skill's SKILL.md, references, or scripts
    Then no operator-specific path (/Users/..., /home/..., C:\..., D:\..., /private/...)
         appears in the new content except as an explicit documentation example
    And before install, the path-discipline grep is run and any non-example hits are
         replaced with <repo-root>, ~, $HOME, or runtime resolution

  Scenario: Smoke check after retrofit or amendment
    Given Phase 2 retrofit or Phase 3 amendment has installed an updated skill
    When skill-improve verifies completion
    Then it confirms the amended skill loads in a fresh session via `claude -p` listing
    And confirms the frontmatter version matches the bumped version
    And confirms path-discipline grep still passes
    And only then reports completion to the user
