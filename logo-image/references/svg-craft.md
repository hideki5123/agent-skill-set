# SVG craft: from photo subject to a cohesive mark collection

WHEN TO READ: on the SVG path, before writing brief.json (section 1 explains its
fields), and again when repairing cells after QA.

Contents: 1 abstraction, 2 slots and sheet order, 3 construction rules,
4 consistency, 5 layout, 6 QA rubric.

## 1. Abstract the subject

1. **View.** Use the view the photo shows (front, profile, three-quarter,
   top-down). A vessel or product whose key feature is on top may be drawn
   slightly raised so its rim shows as an ellipse.
2. **Cues.** List 6-10 visible shape cues and keep the ones that still read in a
   solid one-color silhouette.
3. **Features.** Rank the survivors by how well they separate the subject from
   its look-alikes, and keep 3-5. Feature 1 is the cue look-alikes lack (for a
   fox, the narrow muzzle with white cheeks rather than the ears a cat also
   has). Write the look-alikes into the brief. Test the master shape against
   them and against common false readings (a letter, an arrow, a heart, an
   envelope), and change a proportion until none fits.
4. **Proportions, not outlines.** Record the key ratios (ear height to head
   height, saucer width to cup width) in the brief. Cohesion comes from the
   palette, the two stroke weights, the corner style, the accent role and these
   proportions. Only G1 (solid) and L1 (contour) show the whole silhouette; every
   other slot crops it, uses features 1-2, or rebuilds it in its own
   construction. The build flags identical path data in 3 or more marks but
   cannot see rescaled copies, so check those yourself.
5. **Drop.** Texture, shading, perspective, background, props, parts smaller
   than 16u, repeated detail beyond 3, any text or existing logo on the subject,
   and the likeness of a real person.
6. **Palette** (at most 4 hex values for the whole sheet):
   - `ink`: the subject's identity hue, darkened only until it contrasts at
     least 4.5:1 with paper. A subject without a saturated identity hue uses its
     darkest large area; a white or very light subject uses its darkest
     meaningful region (contents, shadow line).
   - `accent`: a second hue from the subject, used only on the feature named in
     `accent_role`, and absent from marks that do not show that feature.
   - `tint` (optional): paper + 0.4 x (ink - paper) per channel. Without tint,
     G3 facets are ink separated by paper seams and the W-iso side face is a W2
     outline.
   - `paper`: the off-white sheet background, such as #F6F3EC.
7. **Letters.** The initials of the brand name the user gave (at most 2),
   otherwise the first letter of the subject noun. M3 needs two letters: with a
   single initial, use the first two letters of the subject noun.
8. **Corners.** `sharp` for straight-edged subjects (miter joins, butt caps),
   `round` otherwise (round caps and joins). One choice for the whole sheet;
   filled points may stay sharp either way.

## 2. Slots and sheet order

Each slot is a different construction. Changing only the color, scale or frame
around the same drawing does not make a new slot.

| Slot | Recipe |
|---|---|
| G1 geometric primitive | whole silhouette built only from 3-5 circles, triangles and rectangles, solid ink |
| G2 geometric radial | one feature repeated 3, 4, 6 or 8 times with `rotate(a 120 120)` |
| G3 geometric faceted | the subject as 6-10 flat straight-edged planes in ink and tint, paper seams at least 8u |
| L1 line monoline | whole contour at W1 plus one interior line at W2 |
| L2 line feature-only | features 1-2 as W1 strokes; add one minimal cue if they do not read alone |
| L3 line stripes | 3-5 parallel W1 lines clipped to the subject, endpoints within 30..210; drop fragments shorter than 24u |
| N1 negative knockout | circle d=192 or rounded square 176 with features 1-2 cut out as one shape |
| N2 negative figure-ground | paper between two ink shapes forms the subject's light area or feature 1, without filling a notch that defines a feature |
| N3 negative internal cut | a solid crop of the subject with 1-2 cuts at least 12u wide that open a counter or change the contour |
| E1 emblem shield | features 1-2 knocked out of a mirrored shield whose top edge follows feature 1 |
| E2 emblem frame-break | W1 ring r=84 around features 1-2 drawn solid; one feature crosses the ring diagonally with an 8u gap each side (mask) |
| E3 emblem polygon | W1 outline of a hexagon or diamond, at least 4 edges visible, the subject contour replacing the rest |
| B1 badge double ring | outer ring r=88 at W1, inner ring r=68 at W2, the subject in its own view filling the inner ring |
| B2 badge starburst | 16-24 point starburst with integer vertices and features 1-2 knocked out |
| B3 badge patch | ink rounded-rect patch R=16, the subject as a knocked-out W2 contour, a dashed border cut through a mask at W2 (`stroke-dasharray="4 16"`, round caps) |
| M1 monogram hybrid | a legible initial at W1; feature 1 replaces one terminal or sits in the letter's open space |
| M2 monogram knockout | the initial knocked out (24u stems, optically centered) of a solid container shaped like feature 2, at most 176u |
| M3 monogram ligature | two letters sharing a stem, one feature built into the join |
| W-line | one open path that reads differently from L1 and L2, both ends inside the form |
| W-dot | one `<circle r="8">` per dot on a 24u lattice centered on 120 (centers at 36+24k), kept where the center falls inside the subject |
| W-iso | 2:1 dimetric block with depth 32,-16: front face ink, side face tint, top face an 8u-wide evenodd ring; each face an explicit polygon |
| W-arc | the subject's proportions rebuilt only from circles and arc segments |

The container slots (N1, E1, E2, B1, B2, B3, M2) are where sheets turn
monotonous. Cover each frame with your hand: no two interiors may match.

Sheet order, row by row. Heavy slots (N1 N2 N3 G1 G3 E1 B2 B3 M2 W-iso W-arc)
sit on a checkerboard so no two touch horizontally or vertically.

- 16, organic subject: `N1 L1 G1 L2 / W-dot B2 M1 E1 / M2 W-line G3 B1 / L3 N2 E3 W-arc`
- 16, built or manufactured subject: the same with `W-iso` in place of `W-arc`
- 20: `N1 L1 G1 W-dot B2 / L2 E1 M1 G3 B1 / M2 E3 N3 L3 N2 / W-line B3 E2 G2 M3`

File names are the two-digit position plus the lowercase slot, so they sort into
sheet order: `01-n1.svg`, `02-l1.svg`, `03-g1.svg`, ...

## 3. Construction rules

Rules marked (build) are checked by build_sheet.py; the rest are yours to check.

- (build) Root exactly `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240">`.
  Put fills, strokes and transforms on inner elements.
- (build, direct shapes only) Everything drawn inside the live area 24..216,
  including half the stroke width. The build does not measure `<use>` copies,
  transformed groups or curve bulges. Keyline sizes: circle d=192, square 176,
  portrait 152x192, landscape 192x152.
- (build) Integer coordinates. Main shapes on multiples of 4 where it is natural;
  starburst vertices rounded to integers.
- Angles: prefer 0/45/90; 30/60 and 2:1 slopes are fine for tapers and
  isometric faces.
- Prefer primitives and `A` arcs; at most 2 cubic curves per mark. Every mark
  must stay legible in the thumbnail.
- (build) Painted strokes are W1=12 or W2=8. Strokes inside `<mask>` or
  `<clipPath>` only cut and may be any width.
- Transforms: translate, `rotate(a 120 120)` and the mirror
  `translate(240 0) scale(-1 1)`. Do not scale stroked groups; draw the smaller
  version instead.
- (build) Banned: `<text>`, `<image>`, `<style>`, gradients, patterns, filters,
  opacity, skew, `vector-effect`, external references, duplicate ids.
- Holes: one `<path fill-rule="evenodd" d="outer Z inner Z">`, or a `<mask>`
  when the cut is stroke-shaped. Never fake a hole with a paper-colored shape.
- Shapes overlap by at least 8u or keep a gap of at least 8u: no tangents, no
  hairline slivers.
- Ids start with the slot (`e1-half`). Mirror halves with `<use>` and put the
  fill on the wrapping `<g>`, not on `<use>`.
- Letters are `<path>` outlines about 128u tall (the build rejects `<text>`).
  Straight letters use `H`/`V`/`L`; curved letters use `A` arcs.

```svg
<!-- N1: knockout circle with a triangular hole (evenodd) -->
<path fill="#1F3A34" fill-rule="evenodd"
      d="M24 120 A96 96 0 1 0 216 120 A96 96 0 1 0 24 120 Z M120 64 L172 168 H68 Z"/>

<!-- E1: mirrored shield half -->
<defs><path id="e1-half" d="M120 28 L196 56 V120 C196 164 164 196 120 212 Z"/></defs>
<g fill="#1F3A34">
  <use href="#e1-half"/>
  <use href="#e1-half" transform="translate(240 0) scale(-1 1)"/>
</g>

<!-- M1: stroked letter P, 128u tall -->
<path fill="none" stroke="#1F3A34" stroke-width="12" stroke-linecap="round"
      stroke-linejoin="round" d="M96 184 V56 H136 A36 36 0 0 1 136 128 H96"/>

<!-- E2: ring gap for a crossing W1 feature: mask stroke = 12 + 8 + 8 -->
<defs>
  <mask id="e2-gap">
    <rect width="240" height="240" fill="#FFFFFF"/>
    <path d="M148 32 L100 208" fill="none" stroke="#000000" stroke-width="28"/>
  </mask>
</defs>
<circle cx="120" cy="120" r="84" fill="none" stroke="#1F3A34" stroke-width="12" mask="url(#e2-gap)"/>
```

## 4. Consistency

- The same hex values, W1/W2, corner style and accent role in every mark;
  proportions from the brief, never pasted outlines.
- Optical centering: center the ink bounding box on (120,120) and nudge
  bottom-heavy forms (triangles, shields) up by 4-8u.
- Similar visual weight within a construction type: an outline mark should not
  look much smaller or lighter than the other outline marks, and a solid mark
  not much heavier than the other solid marks.

## 5. Layout

build_sheet.py lays out the sheet: cell 240 (the mark viewBox maps 1:1),
gutter 56, margin 72, full-bleed paper background, no captions. A 4x4 sheet is
1272x1272 and a 5x4 sheet 1568x1272. The PNG renders at 2x, plus a quarter-scale
thumbnail. Mark names appear only in index.html and report.json.

## 6. QA rubric

Before each repair round, copy `grid.png` and `marks/` into `<out>/rounds/r<N>/`.
Look at `grid-small.png` first, then `grid.png`.

1. **Blind naming:** for each cell, write down the first noun it suggests before
   rereading the brief.
2. **Grouping:** mentally remove frames, rings, cuts, seams, dots and
   containers, then group the cells whose remaining subject shape is the same
   even with nudged coordinates.
3. **Score each cell:**
   - R (0-2): 2 if the noun is the subject (for M slots, when both the letter and
     the subject read), 1 if ambiguous, 0 if it is something else.
   - D (0 or 2): 0 for every cell in a group larger than 2 except its two best
     cells; otherwise 2.
   - C (0-2): palette, stroke weights, corner style and accent role follow the brief.
   - S (0-2): still legible in the thumbnail.
   - G (0-2): clean geometry: symmetry holds, and there are no spikes, slivers,
     tangents or clipping.
   - F (0-2): reads as its named family.
4. **Rebuild** every cell with R=0, D=0 or a build warning, up to 6 per round;
   fill any remaining places with the lowest totals.
5. **Record** each round in `<out>/qa.json` as
   `{"rounds": [{"round": 1, "cells": [{"pos": 1, "slot": "n1", "noun": "fox", "R": 2, "D": 2, "C": 2, "S": 2, "G": 2, "F": 2}]}]}`.
6. **Build again and compare.** Restore any cell that got worse from `rounds/`.
   After the second round, look once more, then deliver and name the cells that
   are still weak.
