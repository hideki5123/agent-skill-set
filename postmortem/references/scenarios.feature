# WHEN TO READ: only when auditing or amending this skill. Not needed for normal execution.

Feature: Postmortem generation from a Slack incident thread

  Background:
    Given slack-cli is installed and configured
    And the main session runs Bash only for preflight, ticket creation, and publishing
    And any command that fetches incident evidence is delegated to a subagent

  Scenario: Primary path — permalink to published postmortem
    Given the user pastes a Slack permalink to an incident thread
    When the skill runs
    Then it dispatches postmortem:slack-collector with only the channel and thread_ts
    And the collector returns an evidence card with permalinked events, signals, detected_via, and refs
    And no raw Slack messages enter the main session
    And it dispatches code-collector and tracker-collector in parallel, seeded with the refs
    And it merges the cards into a sourced timeline capped at 40 rows and computes TTD, TTM, and TTR
    And it writes the draft and a claims file to disk rather than into the conversation
    And it dispatches one factchecker per source domain, which re-fetch from the sources
    And CONTRADICTED claims are corrected in the file before the user sees it
    And after approval it publishes from the file with `confluence create -f`

  Scenario: The document is never re-emitted into the conversation
    Given the draft exists on disk
    When the user asks for three rounds of revisions
    Then each revision is an Edit on the changed section only
    And publishing reads the file with -f rather than inlining it into a heredoc
    And the main session holds one copy of the document, not five

  Scenario: Fact-checker catches a timezone error the collector introduced
    Given the slack-collector converted an epoch timestamp with the wrong offset
    And TTD is derived from that timestamp
    When the factchecker re-fetches the Slack message rather than trusting the evidence card
    Then it returns CONTRADICTED with the correct time and a concrete correction
    And the skill applies it and recomputes TTD, TTM, TTR, and every dependent claim

  Scenario: Fact-checkers do not verify interpretation
    Given the draft states a root cause and three contributing factors
    When the skill builds the claims file
    Then the root cause, contributing factors, and lessons are excluded from it
    And only source-settleable facts (times, numbers, what changed, who acted, what was said) are checked
    And the interpretation is put to the user in Phase 6 instead

  Scenario: Verdicts return only what is wrong
    Given 24 claims are dispatched and 20 are confirmed
    When the factcheckers return
    Then they return a count line plus rows for the 4 non-confirmed claims only
    And no CONFIRMED rows cross back into the main session

  Scenario: Draft is mostly wrong — re-collect rather than patch
    Given more than a third of the claims come back CONTRADICTED
    When the skill applies verdicts
    Then it does not patch claim by claim
    And it re-runs Stage A collection, tells the user why, and rebuilds the timeline

  Scenario: first_impact_at cannot be established
    Given no source says when user impact actually began
    And the user does not know either
    When the skill computes metrics
    Then it does not substitute detected_at, which would report TTD as zero
    And it reports "time to mitigate from detection" instead, labelled as such
    And "we cannot tell when impact began" becomes an open question and a detection action item

  Scenario: The incident was found by a customer, not by monitoring
    Given the slack-collector returns detected_via = customer-report
    When the skill drafts the document
    Then "Detected by" records customer report rather than a guessed "alert"
    And the fact that monitoring missed it appears in "What went badly"
    And the action items include a detection item

  Scenario: The incident was stopped by a rollback
    Given the mitigation was a rollback, a feature-flag flip, or a restart
    When the skill drafts the action items
    Then it includes a remediation item for the durable fix
    Because the system is still broken even though the incident feels over

  Scenario: Incident had more than one cause
    Given the trigger landed on a system with a stale alert threshold and a slow rollback path
    When the skill drafts Root Cause & Contributing Factors
    Then it records the trigger, the root cause, and each contributing factor separately
    And each contributing factor is a candidate action item

  Scenario: Recurrence found
    Given the tracker-collector finds a prior incident with the same failure mode
    Then the Overview's Recurrence row links the prior incident
    And the action items address why the previous remediation did not hold

  Scenario: Customers were affected and never told
    Given the incident had user impact
    And no status-page update or customer notice appears in any source
    When the skill drafts the Communications section
    Then it records customers_informed = false
    And that appears in "What went badly" rather than being omitted as a non-event

  Scenario: A subagent returns a raw dump instead of a card
    Given a collector ignores its caps and returns raw JSON
    When it lands in the main session verbatim
    Then the skill does not quote it, re-read it, or paste it
    And it proceeds with whatever is usable and records the failure in the Retrospective
    Because a subagent return cannot be filtered after the fact — the caps live in the collector

  Scenario: A collector's CLI fails
    Given jira is installed but the JQL query errors
    When the tracker-collector returns
    Then the failure is recorded in the card's gaps
    And the main session does not read the empty card as "the tracker had nothing"

  Scenario: Ambiguous anchor — channel with several incident threads
    Given the user names a channel instead of a permalink
    And several candidate incident threads exist
    Then the slack-collector returns empty events and lists the candidates in gaps
    And the main session asks the user to pick

  Scenario: Two plausible trigger commits
    Given two PRs touching the failing surface merged minutes apart before impact
    Then the code-collector returns both as candidates and says so in gaps
    And the main session asks the user which one, rather than asserting a trigger

  Scenario: Causal claim is asserted as fact
    Given the draft says "PR #456 caused the outage"
    And the source establishes only that PR #456 merged 9 minutes before impact
    Then the factchecker returns UNSUPPORTED and downgrades it to "most likely trigger"

  Scenario: Optional CLI missing
    Given gh is not installed
    When the skill runs preflight
    Then the per-tool check reports the other three as present, not short-circuited
    And it skips the code-collector and records the missing evidence source under Open questions
    And it does not stop

  Scenario: Action items become Jira tickets only with approval
    Given the draft has three action items
    Then the skill presents the table and offers to file them
    And no ticket is created without explicit approval
    And every created ticket is unassigned and links the postmortem
    And the skill does not promise labels, which the installed jira CLI cannot set

  Scenario: User cancels at review
    Given the user rejects the draft at Phase 6
    Then nothing is published and no ticket is created
    And the draft remains on disk

  Scenario: Confluence publish fails
    Given the user approved the document
    And confluence create returns an error
    Then the skill reports the file path and the error
    And the document is not lost, because it was written to disk before publishing
