# logo-image - BDD spec
# WHEN TO READ: only when auditing or amending this skill.

Feature: Image to a cohesive minimalist logo collection

  Scenario: Claude builds an SVG collection from an attached photo
    Given the user attaches a photo with one clear subject and asks for logos
    When the skill runs on Claude with no count specified
    Then it reads svg-craft.md and writes brief.json with 3-5 ranked features,
          look-alikes, proportions, an accent role and at most 4 colors
      And it authors 16 SVG marks in the checkerboard sheet order, with the whole
          silhouette only in G1 and L1 and every other slot a different construction
      And build_sheet.py runs with --bg set to the brief's paper and writes
          grid.svg, grid.png, grid-small.png, index.html and report.json in a 4x4 layout
      And the agent snapshots each round, scores cells with blind naming,
          repairs at most two rounds, and reports paths, renderer and weak cells

  Scenario: Pasted outlines are flagged
    Given the same long path data appears in three or more marks
    When build_sheet.py runs
    Then report.json carries a sheet warning naming those marks

  Scenario: Codex renders the sheet with the built-in image generator
    Given the skill runs on Codex, image_gen is in the tool list,
          and the user did not ask for editable vectors
    When the skill runs
    Then it tells the user the raster path uses Codex image-generation quota
      And it makes one image_gen call for the whole sheet, passing the photo via
          num_last_images_to_include or referenced_image_paths but not both
      And it copies the result to logo-sheet.png with prompt.txt beside it
      And it checks the count and absence of text, with at most 3 generations
      And it says the output is raster and offers the SVG path

  Scenario: Codex user wants vector files
    Given the skill runs on Codex
    When the user asks for SVG or editable vector logos
    Then the SVG path runs instead of image_gen

  Scenario: Codex sandbox blocks the browser renderer
    Given build_sheet.py runs under Codex workspace-write and logs chrome-headless failed
    When the agent handles renderer null
    Then it reruns the same build command with escalated permissions

  Scenario: No rasterizer anywhere
    Given build_sheet.py reports renderer null
    When the agent reruns with --install and PyPI is unreachable
    Then the install gives up quickly
      And the agent delivers grid.svg and index.html
      And states that no PNG was produced and no visual QA pass happened

  Scenario: Invalid or unsafe marks are rejected
    Given a mark contains <text>, a DOCTYPE in any encoding, an external url()
          reference in any letter case, a root transform, or duplicate ids
    When build_sheet.py runs
    Then it exits 1 with per-file errors, removes stale sheet files,
          and writes report.json without a sheet

  Scenario: Uneven count requested
    Given the user asks for 17 or 18 logos
    When the brief is written
    Then the count becomes 16 or 20 and the user is told why

  Scenario: No image provided
    Given the user asks for a logo grid without attaching or naming an image
    When the skill starts
    Then it asks for the image before doing anything else

  Scenario: Image contains an existing logo or a real person
    Given the photo shows a branded product or an identifiable person
    When marks are designed
    Then no existing trademark, text or likeness is reproduced
      And the subject is abstracted into original generic forms

  Scenario: Delivery from Claude Code on the web
    Given the skill runs in a Claude Code cloud session
    When the output directory is chosen
    Then the agent asks once whether to commit the results to a branch
      And the delivery message says whether and where they were committed

  Scenario: gpt-image requested from a cloud Claude session
    Given the skill runs in Claude Code on the web or claude.ai
    When the user asks for a gpt-image rendered sheet
    Then the agent explains api.openai.com is not reachable there by default
      And offers the SVG path instead of attempting the call

  Scenario: Retrospective outside the skills repository
    Given the skill is installed as a project copy, plugin cache, Codex skill or claude.ai upload
    When a run finishes
    Then no feedback question is asked and nothing is written under the skill directory
