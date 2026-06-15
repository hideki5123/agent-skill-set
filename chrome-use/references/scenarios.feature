Feature: chrome-use — drive a logged-in Chrome via the DevTools Protocol, on demand

  Background:
    Given Chrome 144+ is already running and logged in
    And local remote debugging was enabled once at chrome://inspect/#remote-debugging
    And Node is available on PATH

  Scenario: Connection check passes
    When the user runs "chrome-use.mjs check"
    Then it spawns the DevTools backend, connects via autoConnect, and lists open pages
    And it confirms run/snapshot/screenshot are usable
    And the DevTools backend exits when the command finishes (no idle process)

  Scenario: Check detects a missing connection
    Given Chrome is not running or remote debugging is not enabled
    When the user runs "chrome-use.mjs check"
    Then it prints Japanese guidance covering Chrome-running, chrome://inspect, the
         approval dialog, and system-sleep
    And it exits non-zero

  Scenario: Read content from the active logged-in tab
    Given the target page is the active tab and behind a login
    When the user runs run with an extraction --js (bare expression or function)
    Then chrome-use evaluates it on the active page and returns the result as JSON
    And the user's tabs are untouched

  Scenario: Open in a new tab, wait, extract
    When the user runs run with --new-tab --url, --wait TEXT, and an extraction --js
    Then chrome-use opens the URL in a new tab, waits for the text, and extracts
    And the pre-existing tabs and the active tab are left as they were

  Scenario: uid-based interaction stays in one session
    Given the user asked to fill and submit a form
    When the steps take_snapshot, fill_form, and click run via a single "batch"
    Then the uids from the snapshot remain valid for the fill/click in that session
    And for state-changing actions on sensitive sites the skill confirms first

  Scenario: DOM interaction is self-contained per invocation
    Given the user asked to click something on the active tab
    When the user runs run with an interaction --js (click / setter+dispatchEvent)
    Then the action executes against the real logged-in session in one invocation

  Scenario: Each command is a fresh CDP session
    Given two separate chrome-use invocations
    Then session state (selected page, snapshot uids) does not carry between them
    And flows that need shared state are bundled into one run or one batch

  Scenario: Generic escape hatch
    Given a DevTools tool not wrapped by a convenience subcommand
    When the user runs "chrome-use.mjs call <tool> --params <json>"
    Then that tool is invoked directly and its text result is printed

  Scenario: No idle residency
    Given the chrome-devtools MCP server is NOT registered globally
    Then no DevTools process runs except while a chrome-use command is executing
