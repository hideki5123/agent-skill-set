Feature: chrome-use — drive a logged-in Chromium browser via AppleScript

  Background:
    Given macOS with a Chromium browser already running and logged in
    And the controlling process has (or can obtain) Automation consent
    And "Allow JavaScript from Apple Events" is enabled

  Scenario: Preflight passes
    When the user runs "chrome-use.sh check"
    Then it reports Automation consent OK and the JS toggle enabled
    And it confirms run is usable

  Scenario: Preflight detects a missing toggle
    Given "Allow JavaScript from Apple Events" is OFF
    When the user runs "chrome-use.sh check"
    Then it reports the toggle is disabled
    And it instructs the user to enable it via View > Developer (manual, not scriptable)

  Scenario: Extract content from an existing logged-in tab
    Given the target page is open in a tab and behind a login
    When the user runs run with --url matching that tab and an extraction --js
    Then chrome-use activates that tab and returns the extracted text on stdout
    And it does not close the user's pre-existing tab

  Scenario: Open, wait, extract, and clean up
    Given the target URL is not open in any tab
    When the user runs run with --url, --wait SELECTOR, and an extraction --js
    Then chrome-use opens the URL in a new tab, waits for the selector,
         extracts, and closes the tab it opened
    And the pre-existing tabs are untouched

  Scenario: Interaction on the live session
    Given the user asked to click or fill something on the active tab
    When the user runs run with an interaction --js (click/setter+dispatchEvent)
    Then the action executes against the real logged-in session
    And for state-changing actions on sensitive sites the skill confirms first

  Scenario: Wait timeout is a hard error
    Given a --wait selector that never appears
    When run is executed
    Then it exits non-zero with a Japanese wait-timeout message

  Scenario: Background job cannot grant Automation consent
    Given the command runs in a background context with no prior consent
    When it tries to control the browser
    Then the AppleEvent times out (-1712) and the skill explains that approval
         must happen in the foreground

  Scenario: Non-default Chromium browser
    Given Brave/Edge/Arc is the target
    When run is called with --app "<Browser Name>"
    Then the same execute-javascript path is used against that app

  Scenario: Clipboard fallback when the toggle is unavailable
    Given "Allow JavaScript from Apple Events" cannot be enabled
    When the user pastes a copy(...) snippet in the DevTools console
    Then the skill reads the result with pbpaste
