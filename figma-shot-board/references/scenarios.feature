# figma-shot-board — BDD spec
# WHEN TO READ: only when auditing or amending this skill.

Feature: Screenshots to a labeled Figma board

  Scenario: New file board
    Given the user has N local screenshots grouped into sections
    When they ask to put them in Figma without naming a target file
    Then whoami resolves plans (ask which team if multiple), a new design file is
      created via create_new_file (after loading figma-create-new-file), and a
      sectioned auto-layout board is built with layer names = filenames

  Scenario: Board inside an existing file
    Given the user provides an existing Figma file URL
    When the board is built
    Then a NEW page is created for it (existing pages untouched) and the final
      answer includes the page URL with node-id

  Scenario: Upload placement gotchas are corrected
    Given upload_assets placed frames as 400x300 FILL frames on the first page
    When the fix step runs
    Then every frame is resized to its image's natural size divided by the
      capture scale and moved to the target page before layout

  Scenario: Relocation request
    Given a board already exists in file A
    When the user asks to move it to file B
    Then images are re-uploaded to B (hashes are per-file), the board is rebuilt,
      the old location is renamed "MOVED → ...", and the user is told the MCP
      cannot delete files

  Scenario: Rate limited or unauthenticated
    Given a Figma MCP call fails with auth or rate-limit errors
    When the failure occurs
    Then whoami is called to diagnose, and the user is told to re-auth via
      claude.ai connector settings or /mcp (non-interactive sessions cannot OAuth)
