---
name: figma-shot-board
description: >
  Place a set of local screenshots/images into Figma as a labeled, sectioned
  board (auto-layout, title + section rows, layer names = filenames) using the
  Figma MCP (upload_assets + use_figma). Works against a new file or an existing
  file/page, and encodes the non-obvious upload gotchas (default 400x300 FILL
  frames, first-page placement, natural-size resize, 2x capture scaling).
  Use when the user wants screenshots arranged in Figma, UI states delivered as
  a Figma page, or images moved/relocated between Figma files. Triggers:
  "figma-shot-board", "/figma-shot-board", "figma shot board", "スクショをFigmaに並べて",
  "FigmaにUIステートを起こして", "スクショをFigmaに起こして", "screenshots to figma",
  "figma board of screenshots", "put these images in figma", "Figmaに画像を配置".
version: 1.0.0
---

# figma-shot-board — screenshots → labeled Figma board

Turn N local images into one tidy Figma page: header (title + subtitle) and
labeled sections, each a horizontal row of image frames at their natural size.

## Inputs to establish first

- Image files, their **order**, and a section grouping (section label → files).
- Scale divisor: captures taken at `deviceScaleFactor: 2` should be placed at
  natural size ÷ 2 (logical 1x). Default divisor 2 for playwright 2x captures,
  1 for plain images.
- Target: an existing Figma file URL (extract fileKey), or a new file
  (needs plan/team choice — `whoami` lists plans; ask if multiple).
- Page: new page name (recommended; never disturb existing pages) or an
  existing page node-id.

## Workflow

1. **Preflight**: call `whoami` (auth check + plan keys; also the tool to cite
   when rate-limited). MANDATORY prerequisite skills: load `figma-create-new-file`
   before any `create_new_file` call, and `figma-use` before any `use_figma` call.
2. **Target file/page**: for a new file use `create_new_file` (lands in drafts —
   tell the user it can be dragged into a project). For a page inside a design
   file use `use_figma` with `figma.createPage()` (design files only).
3. **Get upload URLs**: `upload_assets(fileKey, count=N)` → N single-use submit
   URLs (expire in 10 min — upload promptly).
4. **POST the files** with `scripts/post_uploads.sh` (multipart `file` field —
   **the filename becomes the Figma layer name**, so name files descriptively
   before uploading). Keep URL↔file order aligned.
5. **Fix placement (the big gotchas)** via one `use_figma` call:
   - Uploaded frames land on the **first/current page** as **400×300 frames with
     the image as a FILL** (cropped!) — NOT at natural size.
   - For each frame: read `fills` → `figma.getImageByHash(fill.imageHash)` →
     `await img.getSizeAsync()` → `frame.resize(w/divisor, h/divisor)`.
   - Move to the target page with `targetPage.appendChild(frame)` (works across
     pages; collect frames from whatever page they landed on).
6. **Build the board** (respect ~10 ops per `use_figma` call — split into 2-3
   calls): root `figma.createAutoLayout('VERTICAL', {itemSpacing: 56, padding…})`
   with a light fill, positioned away from (0,0); header (title 28 Semi Bold +
   subtitle 14 gray); per section a VERTICAL auto-layout (label 18 Semi Bold +
   HORIZONTAL row, `counterAxisAlignItems: 'MIN'`, itemSpacing 24) and
   `row.appendChild(frame)` for its images. Font loads first
   (`Inter` styles are `Semi Bold`, not `SemiBold`).
7. **Verify**: `await root.screenshot()` in the last call and eyeball it.
   Return the page URL: `https://www.figma.com/design/<fileKey>/<name>?node-id=<pageId with ':'→'-'>`.
8. **Relocation** ("move this board to file X"): rebuild in the target file
   (repeat 3-7 — image hashes are per-file, re-upload is required), then mark
   the old page/file clearly (rename to "MOVED → …"); the MCP cannot delete
   files — tell the user to delete the old draft.

## Gotcha table

| Symptom | Cause / fix |
|---|---|
| All frames 400×300, images cropped | Default placement is FILL on a fixed frame — resize to `getSizeAsync()` ÷ divisor |
| Frames on the wrong page | Uploads land on the current/first page — `targetPage.appendChild()` them |
| Blurry at 100% | 2x captures placed at pixel size — divide by 2 |
| Layer named "image" | POSTed raw bytes — use multipart `file` field so the filename is used |
| Upload URL 4xx | Single-use / expired (10 min) — request fresh URLs with `upload_assets` |
| `figma.createPage` throws | FigJam/Slides file — pages are design-file only |
| Font error "SemiBold" | Inter style strings contain a space: `Semi Bold` |

## References

- references/scenarios.feature — BDD spec. Read only when auditing or amending
  this skill; not needed for normal execution.
- scripts/post_uploads.sh — multipart POST loop for submit URLs
  (usage: `post_uploads.sh mapping.tsv` where each line is `submitUrl<TAB>filepath`).

## Retrospective

After the board is delivered, reflect on the run:

1. Consider: mid-session corrections (wrong file/team, re-uploads, layout redo)?
2. Ask the user (in Japanese): 「今回のFigmaボード作成のフィードバック (1-5の評価、気になった点、または何もなければEnter)」
   **If the rating is < 5, ALWAYS follow up**: 「なぜその評価ですか？ (改善のために具体的に教えてください)」 and record the answer verbatim as Rating reason.
3. If feedback was given OR corrections occurred: create `feedback/` next to this
   SKILL.md if missing (resolve via `git rev-parse --show-toplevel`), create
   `feedback/log.md` with the standard header if missing, and prepend an entry
   (Skill Version / Task / Outcome / Rating / Rating reason / Corrections /
   Issues / User Note). Confirm in one short Japanese sentence.
4. If skipped and no corrections occurred, end without recording.
