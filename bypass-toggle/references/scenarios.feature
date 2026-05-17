Feature: bypass-toggle skill — flag-backed permission bypass

  Background:
    Given the bypass-toggle plugin is installed and enabled in settings.json
    And the user is in a Claude Code session

  Scenario: Turn on bypass with no TTL
    When the user says "bypass on" or "/bypass-toggle on"
    Then ~/.claude/bypass-toggle/state.json is created with enabled=true and expires_at=null
    And the user is told it is on for all sessions until turned off
    And the user is warned that this user's other Claude Code sessions are affected

  Scenario: Turn on bypass with a TTL
    When the user says "bypass on for 30 minutes" or "バイパス 30分だけ"
    Then state.json has enabled=true and expires_at = now + 1800 seconds
    And the user is told it will auto-expire in 30 minutes

  Scenario: Turn off bypass
    Given state.json exists with enabled=true
    When the user says "bypass off" or "バイパス off"
    Then state.json is deleted
    And the user is told permission prompts are back

  Scenario: Show status when off
    Given state.json does not exist
    When the user says "bypass status"
    Then the reply says "OFF"

  Scenario: Show status when on with TTL
    Given state.json has enabled=true and a future expires_at
    When the user says "bypass status"
    Then the reply says "ON" with remaining seconds

  Scenario: Status when TTL expired but state file lingers
    Given state.json has enabled=true and expires_at in the past
    When the user says "bypass status"
    Then the reply says "EXPIRED"
    And the hook (separately) sees the same file and falls through to normal permission flow

  Scenario: Hook fires while bypass is on
    Given state.json has enabled=true and is not expired
    When any tool call is about to run
    Then the PreToolUse hook returns hookSpecificOutput.permissionDecision="allow"
    And the tool runs without an ask-permission prompt

  Scenario: Hook is silent when bypass is off
    Given state.json does not exist
    When any tool call is about to run
    Then the PreToolUse hook produces no stdout and exits 0
    And the session's normal permission mode (auto/plan/default) decides

  Scenario: Plugin is Claude Code only
    Given Cursor or another agent is running on the same machine
    When the bypass-toggle flag is on
    Then Cursor's behavior is unchanged — it never reads ~/.claude/plugins/...
    And no Cursor config file is touched by this plugin

  Scenario: Existing sessions don't pick up the hook until restart
    Given a Claude Code session was started before bypass-toggle was installed
    When the user enables bypass and runs a tool call in that session
    Then the hook does not fire (it's loaded at session start)
    And the skill's docs note that NEW sessions are required
