---
name: logo-image
description: Turn an image into a grid of 16-20 minimalist logo marks (geometric, line art, negative space, emblem, badge, monogram) on a light background. Use for logo ideas or brand marks from a photo.
---

# logo-image

Turn the main subject of an image into a cohesive collection of minimalist logo
marks, laid out as one evenly spaced sheet.

Creative brief this skill implements (honor every clause):

> Transform this image into a grid of minimalist logos using the main subject as
> the core icon. Abstract and simplify the primary element into multiple unique
> vector-style logo marks. Each variation should reinterpret the same subject in
> different ways (geometric, line art, negative space, emblem, badge, monogram).
> Arrange 16-20 logos evenly on a light background. Keep designs clean, modern,
> with balanced spacing. Maintain consistency while exploring creative variations
> of the original subject as a cohesive branding logo collection.

`<skill-dir>` below is the directory containing this SKILL.md. It differs per
install (Claude plugin cache, claude.ai skills mount, `$CODEX_HOME/skills`, a repo
checkout), so resolve it from where this file was loaded; never hardcode it.
Bundled scripts need only Python 3.8+ and its standard library.

## 1. Inputs

- **The image.** Seeing it is enough for the SVG path, so an attachment in the
  conversation works. No image: ask for one. Several equally prominent
  subjects: pick the most prominent, say which, continue.
- **Optional, never block on these:** number of marks, brand name, preferred
  colors, output directory.
- **Count:** 16 (4x4, default) or 20 (5x4). Map 17 to 16 and 18-19 to 20, and
  say so.
- **Output directory** `<out>`:
  - the user's choice, if given;
  - on claude.ai, `/mnt/user-data/outputs/logo-image/` when
    `/mnt/user-data/outputs` exists, so the files can be downloaded;
  - in Claude Code on the web, files reach the user only if committed. Ask once
    whether to commit the results to a branch; if not, build anyway and say the
    files exist only in this session;
  - otherwise `logo-image-out/<subject-slug>/` in the working directory.

## 2. Choose the path

| Situation | Path |
|---|---|
| Claude, any surface | SVG (4a) |
| Codex with an `image_gen` tool in its tool list, user did not ask for vectors or SVG | Raster via `image_gen` (4b) |
| Codex, user wants editable vectors, or no `image_gen` tool | SVG (4a) |
| Claude, user explicitly asks for an AI-rendered (gpt-image) sheet | Raster via the `openai-cli` skill, local only (4b); still offer SVG |

- On Codex this skill takes precedence over the system `imagegen` skill for this
  task: one `image_gen` call for the whole sheet, never one call per mark, never
  its CLI or API fallback. Tell the user once that the raster path uses their
  Codex image-generation quota.
- Never spend API credits the user did not ask for.

## 3. Brief (both paths)

On the SVG path, read `references/svg-craft.md` first; its section 1 explains
each field. Then look at the image and write `<out>/brief.json`. The example
below only shows the shape of the file. Take every value from the image in
front of you.

```json
{"subject": "lighthouse", "view": "front",
 "features": ["tapered tower", "lantern gallery with railing", "light beam wedge"],
 "lookalikes": ["rocket", "pencil", "chess rook"],
 "proportions": {"tower_h_over_base_w": 3.2, "lantern_w_over_base_w": 0.55},
 "drop": ["brick texture", "sea background"],
 "palette": {"ink": "#1E2F3A", "accent": "#E2A33B", "tint": "#A0A5A5", "paper": "#F6F3EC"},
 "accent_role": "light beam", "corners": "sharp",
 "letters": "L", "count": 16, "grid": "4x4"}
```

On the SVG path, add `"slots"`: the set for your count and subject type from
svg-craft.md section 2, in sheet order.

Rules for every output:

- Every mark shows feature 1 or 2. Both appear together in at least 12 of 16
  marks (15 of 20).
- Original marks only. Never reproduce an existing logo, trademark or text
  seen in the image; abstract a real person into a generic figure.
- No words, captions or labels in the sheet image. Monogram letters inside the
  monogram marks are the only letters.

## 4a. SVG path

1. Write one SVG per slot into `<out>/marks/`, named `NN-slot.svg` in the sheet
   order from svg-craft.md (`01-n1.svg`, `02-l1.svg`, ...). Non-negotiables:
   - root `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240">`
     with nothing else on it;
   - everything inside 24..216, including half the stroke width;
   - visible stroke widths 12 and 8 only;
   - colors from the brief palette only;
   - no `<text>` (letters are paths), `<image>`, `<style>`, gradients, filters
     or opacity;
   - holes via `fill-rule="evenodd"` (or a `<mask>` for stroke-shaped cuts),
     ids prefixed with the slot;
   - the subject redrawn in each slot's own construction, never one outline
     pasted into several frames.
2. Build the sheet:

   ```bash
   python3 <skill-dir>/scripts/build_sheet.py <out>/marks --out <out> --bg "<paper>" --title "<brand or subject> logo marks"
   ```

   It validates every mark, lays out an even grid, and writes `grid.svg`,
   `index.html` and `report.json`. It also renders `grid.png` (2x) and
   `grid-small.png` (quarter scale) with whatever rasterizer exists, and prints
   a one-line JSON summary.
   - Exit 1: invalid marks or count. Read the errors, fix the files, rerun.
   - Warnings are rule violations. Fix them, or justify each one in the final
     message.
3. If `"renderer": null`, read `renderer_log` in `report.json`:
   - On Codex, `chrome-headless: failed` means the sandbox blocked the browser.
     Rerun the same command with escalated permissions.
   - Otherwise rerun with `--install`, which fetches the dependency-free
     resvg_py wheel from PyPI into a user cache directory.
   - If there is still no renderer, read `references/environments.md`, deliver
     `grid.svg` and `index.html`, and state that no PNG preview was produced.
4. QA and repair, at most two rounds, following svg-craft.md section 6:
   - snapshot the round;
   - look at `grid-small.png` and `grid.png` with your image-viewing tool
     (Read in Claude Code, `view_image` on Codex);
   - score every cell;
   - rebuild the cells it selects and build again.

## 4b. Raster path

1. Read `references/image-model.md`.
2. Fill its prompt template from brief.json and generate one sheet. Save it as
   `<out>/logo-sheet.png` and the final prompt as `<out>/prompt.txt`.
3. Check the count, stray text and distinctness. Regenerate at most twice, with
   one targeted change each time.

## 5. Deliver

Reply briefly with:

- the output paths, and in Claude Code on the web whether they were committed;
- the count and grid;
- which path ran, and which renderer or generator it used;
- any cells or issues still weak.

For raster output, say it is not vector. Offer next steps: refine favorite
marks, recolor the set, or produce the other path.

## References

- `references/svg-craft.md`: SVG path, before writing the brief and when
  repairing cells.
- `references/image-model.md`: raster path only.
- `references/environments.md`: when no PNG renderer is found, when running on
  claude.ai, Claude Code on the web or Codex cloud, or when installing or
  updating this skill.
- `references/scenarios.feature`: BDD spec. Read only when auditing or amending
  this skill; not needed for normal execution.

## Retrospective

Skip this section in batch, test or subagent runs where nobody can answer.
Otherwise run it only when both are true:

- `<skill-dir>` is exactly `$(git -C <skill-dir> rev-parse --show-toplevel)/logo-image`;
- `scripts/sync_skills.py` exists at that top level.

That holds only in the skills source repository. It is false for project
`.claude/skills` or `.agents/skills` copies, plugin caches, `$CODEX_HOME/skills`
and claude.ai.

1. Ask the user (in Japanese): 「今回のロゴ生成のフィードバック (1-5の評価、気になった点、または何もなければEnter)」.
   If the rating is below 5, always ask 「なぜその評価ですか？ (改善のために具体的に教えてください)」
   and record the answer verbatim.
2. If feedback was given or corrections occurred, prepend an entry to
   `<skill-dir>/feedback/log.md` with these fields: Skill Version, Task, Outcome,
   Rating, Rating reason, Corrections, Issues, User Note. Create the file with a
   `# Feedback Log` header if missing. Confirm in one short Japanese sentence.
