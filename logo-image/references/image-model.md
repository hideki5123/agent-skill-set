# Raster path: one generated logo sheet

WHEN TO READ: on the Codex image_gen path, or when the user explicitly asks for a
gpt-image rendering on Claude. Not needed on the SVG path.

## Mechanics

Codex built-in `image_gen` (no API key; uses the plan's Codex image-generation quota):

- For this task, this skill takes precedence over the system `imagegen` skill.
  Make one call for the whole sheet; the point is a single cohesive sheet. Do not
  make one call per mark, and do not use imagegen's CLI or API fallback.
- Pass the photo in exactly one way:
  - it is already in the conversation (attached, or given with `codex exec -i`):
    set `num_last_images_to_include` to the smallest number of recent images
    that includes it (at most 5);
  - it is only a local file: open it with `view_image`, then pass
    `referenced_image_paths: ["/absolute/path/photo.jpg"]`.
- There is no size or aspect-ratio argument. State the canvas shape in the prompt.
- The tool result names the saved file, normally under
  `$CODEX_HOME/generated_images/`. Copy it to `<out>/logo-sheet.png` and leave the
  original in place.
- Image generation uses Codex quota several times faster than text. Tell the user
  once, and cap it at 3 generations per request.

gpt-image through the `openai-cli` skill (Claude, local only, explicit ask only):

- Requires the `openai-cli` skill and `OPENAI_API_KEY`. Cloud Claude sandboxes do
  not reach api.openai.com by default, so do not attempt it there.
- Use its image edit call with the photo as `image` and no mask. Size is
  `2048x2048` for 16 marks and `1920x1536` for 20. Follow that skill's cost gate
  before calling; every call is billed.

## Prompt template (16 marks)

Fill the angle-bracket fields from brief.json. Fill fields only; do not add
colors or constraints. Keep the Avoid line intact.

```text
Use case: logo-brand
Asset type: brand identity exploration sheet (one image, grid of logo marks)
Primary request: transform the reference image into exactly 16 minimalist vector-style logo marks for one cohesive brand, arranged in a 4 x 4 grid: 4 rows of 4 marks, 16 marks total
Input images: Image 1: subject reference only; abstract its silhouette into flat marks; do not reproduce the photo, its background, lighting, or any text or logos in it
Subject: <subject>; keep these defining features: <feature 1>, <feature 2>, <feature 3>; drop texture, shading and background detail
Style/medium: flat 2D vector logo marks, solid fills and uniform-weight lines, geometric construction, clean and modern, original design
Composition/framing: square canvas; 4 x 4 grid of equal square cells with equal gutters and a generous outer margin; one centered mark per cell; all marks the same visual size with ample padding; balanced spacing; nothing crosses cell boundaries; no borders or dividers
Variation plan (rows left to right): Row 1: the key features cut out of a solid circle; single-weight outline of the whole subject; whole subject built only from circles, triangles and rectangles; only the key features as lines. Row 2: dot grid; key features cut out of a pointed starburst seal; monogram "<letter>" with a subject feature built in; key features cut out of a shield. Row 3: monogram "<letter>" cut out of a solid shape; single continuous line; the subject split into flat two-tone planes; double-ring badge with the subject inside. Row 4: parallel stripes clipped to the subject; figure-ground where the background color forms the subject's light area; thin hexagon outline merging with the subject; <isometric block for built subjects, or arcs-only rebuild for organic subjects>
Scene/backdrop: plain uniform light off-white background (<paper hex>) across the whole sheet
Color palette: <ink hex> primary, <accent hex> accent only on the <accent role>, on off-white; identical palette in every mark
Text (verbatim): only the single letter "<letter>" inside the two monogram marks; no other text anywhere
Constraints: exactly 16 marks, no more and no fewer; every mark redraws the subject in a different construction; the circle, starburst, shield and ring marks each show a different part or construction of the subject, never the same face in another frame; same line weight and corner style throughout; consistent as one branding collection; each mark recognizable as <subject> at thumbnail size
Avoid: words, captions, labels, numbers, style names, brand names, watermark, signature, gradients, drop shadows, 3D, bevels, textures, mockup scenes, photographic detail, extra decorative elements, cut-off or duplicated marks
```

## Changes for 20 marks

Replace these lines of the 16-mark template:

```text
Primary request: transform the reference image into exactly 20 minimalist vector-style logo marks for one cohesive brand, arranged in a 5 x 4 grid: 4 rows of 5 marks, 20 marks total
Composition/framing: landscape 5:4 canvas; 5 x 4 grid of equal square cells with equal gutters and a generous outer margin; one centered mark per cell; all marks the same visual size with ample padding; balanced spacing; nothing crosses cell boundaries; no borders or dividers
Variation plan (rows left to right): Row 1: the key features cut out of a solid circle; single-weight outline of the whole subject; whole subject built only from circles, triangles and rectangles; dot grid; key features cut out of a pointed starburst seal. Row 2: only the key features as lines; key features cut out of a shield; monogram "<letter>" with a subject feature built in; the subject split into flat two-tone planes; double-ring badge with the subject inside. Row 3: monogram "<letter>" cut out of a solid shape; thin hexagon outline merging with the subject; solid crop of the subject with internal cuts; parallel stripes clipped to the subject; figure-ground where the background color forms the subject's light area. Row 4: single continuous line; stitched patch badge; the subject breaking out of a ring; one feature repeated radially; two-letter ligature "<two letters>"
Text (verbatim): only the letter "<letter>" inside the two single-letter monograms and "<two letters>" inside the ligature; no other text anywhere
Constraints: exactly 20 marks, no more and no fewer; every mark redraws the subject in a different construction; the circle, starburst, shield, patch and ring marks each show a different part or construction of the subject, never the same face in another frame; same line weight and corner style throughout; consistent as one branding collection; each mark recognizable as <subject> at thumbnail size
```

Prefer 16: image models lose count more often as the number grows.

## Check the result

1. Count the marks cell by cell. A wrong count or a ragged last row means
   regenerate from scratch with the count restated. Do not try to patch it.
2. Look for pseudo-text, captions or labels. If any appear, shorten the variation
   plan to one line listing the families and regenerate.
3. Check that marks are distinct and flat (no gradients or bevels), that they
   match in visual size, and that the subject reads in each one.
4. Stop after 3 generations in total. Deliver the best one and name its remaining
   flaws.
5. Tell the user the result is a raster image, not editable vector, and offer the
   SVG path if they need vector files.
