Feature: auto-mode skill — return to classifier-guided mode

  Background:
    Given the auto-mode plugin is installed and enabled
    And the bypass-toggle plugin is also installed (auto-mode shares its flag file)

  Scenario: User asks to switch to auto after plan approval
    Given ~/.claude/bypass-toggle/state.json exists with enabled=true
    And the user has just approved a plan from the iPhone Claude app
    When the user says "auto に戻して" or "/auto-mode"
    Then the flag file is deleted
    And the user is told auto mode is now in effect
    And the next tool call goes through the session's --permission-mode auto classifier

  Scenario: User asks to switch to auto when already in auto
    Given the flag file does not exist
    When the user says "auto on" or "オートに戻して"
    Then the skill reports "already in auto" and makes no file change

  Scenario: User asks for status while bypass is on with TTL
    Given the flag file has enabled=true and a future expires_at
    When the user says "auto status"
    Then the reply says "MODE: BYPASS" with remaining seconds

  Scenario: User asks for status while bypass is off
    Given the flag file does not exist
    When the user says "auto status"
    Then the reply says "MODE: auto / native"

  Scenario: Caveat — session was started in plan mode
    Given the session was launched with --permission-mode plan (e.g. cc foreground)
    And bypass-toggle was used to override plan
    When the user runs auto-mode to clear bypass
    Then the session returns to plan mode (NOT auto)
    And the skill's docs explicitly warn about this dependency on startup --permission-mode

  Scenario: Plugin is Claude Code only
    Given Cursor or another agent is running
    When auto-mode is invoked
    Then only ~/.claude/bypass-toggle/state.json is touched
    And no Cursor config or other agent config is modified
