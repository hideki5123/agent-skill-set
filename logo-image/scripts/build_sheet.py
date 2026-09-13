#!/usr/bin/env python3
"""Validate hand-authored SVG logo marks, lay them out as one even grid sheet,
and render the sheet to PNG when a rasterizer is available.

Python 3.8+ standard library only. Nothing is installed unless --install is
passed.

Outputs in --out:
  grid.svg        composed sheet (when validation passes)
  grid.png        raster sheet at --scale (when a renderer was found)
  grid-small.png  thumbnail at --thumb-scale for legibility checks
  index.html      self-contained preview with per-mark names and warnings
  report.json     validation findings, layout, palette, renderer log

Exit codes: 0 ok, 1 validation failed, 2 usage error, 3 --png require but no renderer.
"""
from __future__ import annotations

import argparse
import base64
import collections
import html
import importlib
import json
import math
import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import sys
import sysconfig
import tempfile
import time
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

MAX_BYTES = 200_000
MAX_ELEMENTS = 1500
MAX_DEPTH = 24

# Style system from references/svg-craft.md. Deviations are warnings, not errors.
STYLE_VIEWBOX = (0.0, 0.0, 240.0, 240.0)
STYLE_STROKES = {8.0, 12.0}
LIVE_MIN, LIVE_MAX = 24.0, 216.0
MIRROR_RE = re.compile(r"^translate\(\s*240[\s,]+0\s*\)\s*scale\(\s*-1[\s,]+1\s*\)$")

FORBIDDEN = {"script", "foreignObject", "image", "feImage", "iframe", "video",
             "audio", "canvas", "embed", "object", "a", "style"}
ANIMATION = {"animate", "animateColor", "animateMotion", "animateTransform", "set", "discard"}
FONT_DEPENDENT = {"text", "tspan", "textPath"}
DISCOURAGED = {"linearGradient": "gradient", "radialGradient": "gradient",
               "filter": "filter", "pattern": "pattern"}
OPACITY_ATTRS = {"opacity", "fill-opacity", "stroke-opacity"}
COLOR_ATTRS = {"fill", "stroke", "stop-color", "color", "flood-color", "lighting-color"}
NON_COLORS = {"", "none", "currentcolor", "inherit", "transparent"}
NAMED_COLORS = {"black": "#000000", "white": "#FFFFFF"}
DRAWABLE = {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon", "use", "text"}
SHAPES = {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon"}
ROOT_ALLOWED_ATTRS = {"viewBox", "width", "height"}
NON_RENDERED = {"defs", "mask", "clipPath", "symbol", "marker", "pattern"}
CUTTERS = {"mask", "clipPath"}
ROOT_FORBIDDEN_ATTRS = {"style", "transform", "clip-path", "mask", "filter", "overflow"}
ROOT_ATTRS_NOT_COPIED = {"width", "height", "x", "y", "viewBox",
                         "preserveAspectRatio", "version", "baseProfile"}
GEOMETRY_ATTRS = {"d", "points", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy",
                  "r", "rx", "ry", "width", "height"}
DROP_ON_COMPOSE = {"metadata", "title", "desc"}
URL_RE = re.compile(r"url\(\s*(['\"]?)([^'\")]*)\1\s*\)", re.I)
FRACTION_RE = re.compile(r"\d\.\d*[1-9]|(?<![\d.])\.\d*[1-9]")
PATH_TOKEN = re.compile(r"[A-Za-z]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
PATH_ARGS = {"M": 2, "L": 2, "T": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "A": 7}
COLOR_ARG_RE = re.compile(r"#[0-9A-Fa-f]{3}|#[0-9A-Fa-f]{6}|[A-Za-z]+")
DTD_MESSAGE = "DOCTYPE/ENTITY declarations are not allowed; remove the <!DOCTYPE ...> line"


def local(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def to_number(value: str | None) -> float | None:
    if value is None:
        return None
    v = value.strip()
    if v.endswith("px"):
        v = v[:-2]
    try:
        f = float(v)
    except ValueError:
        return None
    return f if math.isfinite(f) else None


def normalize_color(value: str) -> str | None:
    v = value.strip().lower()
    if re.fullmatch(r"#[0-9a-f]{3}", v):
        v = "#" + "".join(ch * 2 for ch in v[1:])
    if re.fullmatch(r"#[0-9a-f]{6}", v):
        return v.upper()
    mo = re.fullmatch(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", v)
    if mo and all(int(g) <= 255 for g in mo.groups()):
        return "#" + "".join(f"{int(g):02X}" for g in mo.groups())
    return NAMED_COLORS.get(v)


# ---------------------------------------------------------------- geometry

def path_points(d: str) -> list[tuple[float, float]]:
    """Endpoints of every path segment, absolute or relative (control points skipped)."""
    toks = PATH_TOKEN.findall(d)
    pts: list[tuple[float, float]] = []
    x = y = sx = sy = 0.0
    cmd = None
    i = 0
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                x, y = sx, sy
                cmd = None
            continue
        if cmd is None:
            break
        up = cmd.upper()
        n = PATH_ARGS.get(up)
        if not n or i + n > len(toks):
            break
        try:
            vals = [float(v) for v in toks[i:i + n]]
        except ValueError:
            break
        i += n
        rel = cmd.islower()
        if up == "H":
            x = x + vals[0] if rel else vals[0]
        elif up == "V":
            y = y + vals[0] if rel else vals[0]
        else:
            x, y = (x + vals[-2], y + vals[-1]) if rel else (vals[-2], vals[-1])
        if up == "M":
            sx, sy = x, y
            cmd = "l" if rel else "L"
        pts.append((x, y))
    return pts


def shape_extent(el: ET.Element, tag: str, half: float) -> tuple[float, float] | None:
    """Smallest and largest coordinate a shape reaches, on either axis."""
    def num(name: str) -> float | None:
        raw = el.get(name)
        return 0.0 if raw is None else to_number(raw)

    if tag in ("circle", "ellipse"):
        cx, cy = num("cx"), num("cy")
        rx = num("r") if tag == "circle" else num("rx")
        ry = num("r") if tag == "circle" else num("ry")
        if None in (cx, cy, rx, ry):
            return None
        xs, ys = [cx - rx, cx + rx], [cy - ry, cy + ry]
    elif tag == "rect":
        x, y, w, h = num("x"), num("y"), num("width"), num("height")
        if None in (x, y, w, h):
            return None
        xs, ys = [x, x + w], [y, y + h]
    elif tag == "line":
        x1, y1, x2, y2 = num("x1"), num("y1"), num("x2"), num("y2")
        if None in (x1, y1, x2, y2):
            return None
        xs, ys = [x1, x2], [y1, y2]
    elif tag in ("polyline", "polygon"):
        nums = [to_number(t) for t in re.split(r"[\s,]+", (el.get("points") or "").strip()) if t]
        if not nums or None in nums or len(nums) % 2:
            return None
        xs, ys = nums[0::2], nums[1::2]
    elif tag == "path":
        pts = path_points(el.get("d") or "")
        if not pts:
            return None
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    else:
        return None
    return min(xs + ys) - half, max(xs + ys) + half


def long_subpaths(root: ET.Element) -> set[str]:
    """Normalized path data long enough that repeating it across marks means a
    pasted outline rather than a shared primitive."""
    found: set[str] = set()
    stack = [(root, False)]
    while stack:
        el, in_cut = stack.pop()
        tag = local(el.tag)
        if not in_cut:
            if tag == "path":
                for sub in re.findall(r"[Mm][^Mm]*", el.get("d") or ""):
                    toks = PATH_TOKEN.findall(sub)
                    cmds = [t.upper() for t in toks if t.isalpha()]
                    # arcs-only subpaths are plain circles and rings: shared primitives, not outlines
                    if len(cmds) >= 6 and set(cmds) - {"M", "A", "Z"}:
                        found.add(" ".join(toks))
            elif tag in ("polygon", "polyline"):
                toks = [t for t in re.split(r"[\s,]+", (el.get("points") or "").strip()) if t]
                if len(toks) >= 12:
                    found.add(tag + " " + " ".join(toks))
        stack.extend((child, in_cut or tag in CUTTERS) for child in el)
    return found


# ---------------------------------------------------------------- validation

class Mark:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.stem
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.colors: set[str] = set()
        self.subpaths: set[str] = set()
        self.root: ET.Element | None = None
        self.viewbox: tuple[float, float, float, float] | None = None
        self.source = ""


class _Refused(Exception):
    pass


def refuse_dtd_and_pi(raw: bytes) -> None:
    """Run expat over the same bytes ElementTree parses, so no encoding trick
    slips past, and stop at a DTD, entity or processing instruction before any
    expansion happens."""
    parser = expat.ParserCreate()

    def refuse(message: str):
        def handler(*_args):
            raise _Refused(message)
        return handler

    parser.StartDoctypeDeclHandler = refuse(DTD_MESSAGE)
    parser.EntityDeclHandler = refuse(DTD_MESSAGE)
    parser.ProcessingInstructionHandler = refuse(
        "processing instructions such as <?xml-stylesheet ...?> are not allowed")
    parser.Parse(raw, True)


def add_color(m: Mark, value: str, where: str) -> None:
    c = value.strip()
    if c.lower() in NON_COLORS or c.lower().startswith("url("):
        return
    norm = normalize_color(c)
    if norm:
        m.colors.add(norm)
    else:
        m.warnings.append(f"color {c[:40]!r} in {where}: use #RRGGBB hex")


def validate(path: Path, allow_text: bool) -> Mark:
    m = Mark(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        m.errors.append(f"cannot read file: {exc.strerror or exc}")
        return m
    if len(raw) > MAX_BYTES:
        m.errors.append(f"file is {len(raw)} bytes (limit {MAX_BYTES})")
        return m
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in raw:
        m.errors.append("file is not UTF-8 (UTF-16 or binary); save it as UTF-8")
        return m
    try:
        m.source = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        m.errors.append("file is not valid UTF-8; save it as UTF-8")
        return m
    try:
        refuse_dtd_and_pi(raw)
    except _Refused as exc:
        m.errors.append(str(exc))
        return m
    except expat.ExpatError as exc:
        m.errors.append(f"XML parse error: {exc}")
        return m
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        m.errors.append(f"XML parse error: {exc}")
        return m
    if root.tag != f"{{{SVG_NS}}}svg":
        m.errors.append(f'root must be <svg xmlns="{SVG_NS}">, got {root.tag!r}')
        return m
    extra_root = []
    for key in root.attrib:
        if local(key) in ROOT_FORBIDDEN_ATTRS:
            m.errors.append(f'root <svg> attribute "{local(key)}" is not allowed; move it to an inner <g>')
        elif local(key) not in ROOT_ALLOWED_ATTRS:
            extra_root.append(local(key))
    if extra_root:
        m.warnings.append(f"root <svg> should carry only viewBox, width and height; move {sorted(extra_root)} to an inner <g>")

    vb = root.get("viewBox")
    if not vb:
        m.errors.append("root <svg> has no viewBox")
    else:
        nums = [to_number(v) for v in re.split(r"[\s,]+", vb.strip()) if v]
        if len(nums) != 4 or None in nums or nums[2] <= 0 or nums[3] <= 0:
            m.errors.append(f"invalid viewBox {vb!r}")
        else:
            m.viewbox = (nums[0], nums[1], nums[2], nums[3])
            if m.viewbox != STYLE_VIEWBOX:
                m.warnings.append(f'viewBox is "{vb}"; the style rules assume "0 0 240 240"')

    id_counts = collections.Counter(el.get("id") for el in root.iter() if el.get("id"))
    dupes = sorted(k for k, c in id_counts.items() if c > 1)
    if dupes:
        m.errors.append(f"duplicate id(s) {dupes}; every id in a mark must be unique")

    count, drawable, max_depth = 0, 0, 0
    odd_strokes: set[str] = set()
    fractional: set[str] = set()
    outside: list[str] = []
    check_live = m.viewbox == STYLE_VIEWBOX
    # (element, depth, inside mask/clipPath, inside a non-rendered container,
    #  under a transform, stroke painted, stroke width)
    stack = [(root, 0, False, False, False, False, 1.0)]
    while stack:
        el, depth, in_cut, in_defs, transformed, stroke_on, stroke_w = stack.pop()
        count += 1
        max_depth = max(max_depth, depth)
        tag = local(el.tag)
        if not el.tag.startswith(f"{{{SVG_NS}}}"):
            m.errors.append(f"non-SVG element {el.tag!r}")
        if tag in FORBIDDEN:
            hint = " (use presentation attributes; CSS is global in a composed sheet)" if tag == "style" else ""
            m.errors.append(f"<{tag}> is not allowed{hint}")
        if tag in ANIMATION:
            m.errors.append(f"<{tag}> animation is not allowed in static marks")
        if tag in FONT_DEPENDENT:
            msg = f"<{tag}> depends on installed fonts and may render blank or differently; draw letters as <path>"
            (m.warnings if allow_text else m.errors).append(msg)
        if tag in DISCOURAGED:
            m.warnings.append(f"<{tag}>: {DISCOURAGED[tag]}s break the flat style rules")
        if tag in DRAWABLE and not in_defs:
            drawable += 1

        if el.get("stroke") is not None:
            stroke_on = el.get("stroke").strip().lower() not in ("", "none")
        width = to_number(el.get("stroke-width"))
        if width is not None:
            stroke_w = width
        transform = el.get("transform")
        if transform is not None and el is not root and not MIRROR_RE.match(transform.strip()):
            transformed = True

        for key, val in el.attrib.items():
            k = local(key)
            v = val.strip()
            if key == XML_ID:
                m.errors.append(f"xml:id on <{tag}> is not allowed; use id")
            if k.lower().startswith("on"):
                m.errors.append(f"event handler attribute {k!r} on <{tag}>")
            if k == "href" and not v.startswith("#"):
                m.errors.append(f"external reference {k}={v[:60]!r} on <{tag}> (only #local ids)")
            if "\\" in v:
                m.errors.append(f"backslash escape in {k} on <{tag}> is not allowed")
            for _, target in URL_RE.findall(v):
                if not target.strip().startswith("#"):
                    m.errors.append(f"external url({target[:60]}) in {k} on <{tag}>")
            if re.search(r"javascript:|data:|@import|expression\(", v, re.I):
                m.errors.append(f"disallowed content in {k} on <{tag}>")
            if k in OPACITY_ATTRS:
                m.warnings.append(f"{k} on <{tag}>: use a solid pre-mixed color instead")
            if k == "style":
                m.warnings.append(f"style attribute on <{tag}>: use presentation attributes")
            if k == "vector-effect":
                m.warnings.append(f"vector-effect on <{tag}> is not allowed by the style rules")
            if k == "transform" and "skew" in v.lower():
                m.warnings.append(f"skew transform on <{tag}> distorts stroke weights")
            if tag == "use" and k in {"fill", "stroke"} | OPACITY_ATTRS:
                m.warnings.append(f"{k} set on <use>; put it on a wrapping <g> (some renderers drop it)")
            if k in GEOMETRY_ATTRS and not in_cut and FRACTION_RE.search(v):
                fractional.add(f"<{tag}> {k}")
            if not in_cut:
                if k in COLOR_ATTRS:
                    add_color(m, v, f"{k} on <{tag}>")
                elif k == "style":
                    for decl in v.split(";"):
                        prop, _, pval = decl.partition(":")
                        if prop.strip().lower() in COLOR_ATTRS:
                            add_color(m, pval, f"style on <{tag}>")

        if tag in SHAPES and stroke_on and not (in_cut or in_defs) and stroke_w > 0 \
                and stroke_w not in STYLE_STROKES:
            odd_strokes.add(f"{stroke_w:g}")

        if check_live and not (in_cut or in_defs or transformed):
            ext = shape_extent(el, tag, stroke_w / 2.0 if stroke_on else 0.0)
            if ext and (ext[0] < LIVE_MIN - 0.5 or ext[1] > LIVE_MAX + 0.5):
                outside.append(f"<{tag}> spans {ext[0]:g}..{ext[1]:g}")

        child_state = (in_cut or tag in CUTTERS, in_defs or tag in NON_RENDERED,
                       transformed, stroke_on, stroke_w)
        stack.extend((child, depth + 1) + child_state for child in el)

    if odd_strokes:
        m.warnings.append(f"visible stroke widths {sorted(odd_strokes)} are outside the 12/8 system")
    if fractional:
        m.warnings.append(f"fractional coordinates in {', '.join(sorted(fractional)[:4])}; use integers")
    if outside:
        m.warnings.append(f"drawing leaves the live area 24..216: {'; '.join(outside[:3])}")
    if count > MAX_ELEMENTS:
        m.errors.append(f"{count} elements (limit {MAX_ELEMENTS}); simplify the mark")
    if max_depth > MAX_DEPTH:
        m.errors.append(f"nesting depth {max_depth} (limit {MAX_DEPTH})")
    if drawable == 0:
        m.errors.append("nothing is drawn outside <defs>, <mask> or <clipPath>")
    m.warnings = list(dict.fromkeys(m.warnings))
    m.errors = list(dict.fromkeys(m.errors))
    m.subpaths = long_subpaths(root)
    m.root = root
    return m


# -------------------------------------------------------------------- layout

def choose_grid(n: int, cols: int = 0) -> tuple[int, int]:
    """Pick columns and rows so every row is full.

    Prefers the squarest grid with cols >= rows and cols/rows <= 1.5, so
    16 -> 4x4 and 20 -> 5x4. Returns (0, 0) when no such grid exists (17-19).
    An explicit cols value is honored as given.
    """
    if n <= 0:
        return 0, 0
    if cols:
        return cols, math.ceil(n / cols)
    for c in range(math.ceil(math.sqrt(n)), n + 1):
        if n % c == 0 and c / (n // c) <= 1.5:
            return c, n // c
    return 0, 0


def prefix_ids(root: ET.Element, prefix: str) -> None:
    ids: dict[str, str] = {}
    for el in root.iter():
        old = el.get("id")
        if old:
            ids[old] = prefix + old
            el.set("id", ids[old])
    if not ids:
        return

    def fix_url(value: str) -> str:
        def repl(mo: re.Match) -> str:
            target = mo.group(2).strip()
            if target.startswith("#") and target[1:] in ids:
                return f"url(#{ids[target[1:]]})"
            return mo.group(0)
        return URL_RE.sub(repl, value)

    for el in root.iter():
        for key, val in list(el.attrib.items()):
            v = val.strip()
            if local(key) == "href" and v.startswith("#") and v[1:] in ids:
                el.set(key, "#" + ids[v[1:]])
            elif "url(" in val.lower():
                el.set(key, fix_url(val))


def compose(marks: list[Mark], cols: int, rows: int, cell: int, gap: int, pad: int,
            bg: str, tile: str, inset: float) -> tuple[ET.Element, int, int]:
    width = pad * 2 + cols * cell + (cols - 1) * gap
    height = pad * 2 + rows * cell + (rows - 1) * gap
    sheet = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": str(width), "height": str(height),
        "viewBox": f"0 0 {width} {height}"})
    ET.SubElement(sheet, f"{{{SVG_NS}}}rect", {
        "x": "0", "y": "0", "width": str(width), "height": str(height), "fill": bg})
    inner = cell - 2 * round(cell * inset)
    for i, mark in enumerate(marks):
        row, col = divmod(i, cols)
        x = pad + col * (cell + gap)
        y = pad + row * (cell + gap)
        if tile != "none":
            ET.SubElement(sheet, f"{{{SVG_NS}}}rect", {
                "x": str(x), "y": str(y), "width": str(cell), "height": str(cell),
                "rx": str(round(cell * 0.06)), "fill": tile})
        src = mark.root
        assert src is not None and mark.viewbox is not None
        prefix_ids(src, f"m{i + 1:02d}-")
        nested = ET.SubElement(sheet, f"{{{SVG_NS}}}svg", {
            "x": str(x + (cell - inner) // 2), "y": str(y + (cell - inner) // 2),
            "width": str(inner), "height": str(inner),
            "viewBox": " ".join(f"{n:g}" for n in mark.viewbox),
            "preserveAspectRatio": "xMidYMid meet", "overflow": "hidden"})
        # Inheritable root attributes (fill, stroke, ...) move to a wrapper group
        # so nothing on the mark root can override the cell's clipping.
        wrap = ET.SubElement(nested, f"{{{SVG_NS}}}g", {
            k: v for k, v in src.attrib.items()
            if local(k) not in ROOT_ATTRS_NOT_COPIED | ROOT_FORBIDDEN_ATTRS})
        wrap.extend(ch for ch in list(src) if local(ch.tag) not in DROP_ON_COMPOSE)
    return sheet, width, height


# -------------------------------------------------------------- rasterizing

def png_size(path: Path) -> tuple[int, int] | None:
    try:
        head = path.read_bytes()[:24]
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def run(cmd: list[str], timeout: int = 120, cwd: str | None = None,
        env: dict[str, str] | None = None) -> None:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=timeout, cwd=cwd, env=env)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).decode(errors="replace").strip().splitlines()[-3:]
        raise RuntimeError(f"exit {proc.returncode}: {' | '.join(tail)}")


class Unavailable(Exception):
    pass


_FAMILIES: dict[str, str] | None = None


def font_families() -> dict[str, str]:
    """resvg resolves generic families to fixed names (sans-serif -> "Arial").
    On Linux images without those fonts <text> renders blank, so name the
    families fontconfig actually has. Only matters with --allow-text."""
    global _FAMILIES
    if _FAMILIES is None:
        _FAMILIES = {}
        exe = shutil.which("fc-match")
        for generic in ("sans-serif", "serif", "monospace"):
            if not exe:
                break
            try:
                res = subprocess.run([exe, "-f", "%{family[0]}", generic], stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, timeout=10)
                name = res.stdout.decode(errors="replace").strip()
                if name:
                    _FAMILIES[generic] = name
            except (OSError, subprocess.SubprocessError):
                break
    return _FAMILIES


def r_resvg_py(svg: Path, png: Path, w: int, h: int, bg: str, fonts: list[str]) -> None:
    try:
        resvg_py = importlib.import_module("resvg_py")
    except ImportError as exc:
        raise Unavailable("python module resvg_py not importable") from exc
    kwargs = {"svg_path": str(svg), "width": w, "background": bg}
    if fonts:
        kwargs["font_dirs"] = fonts
    fam = font_families()
    if "sans-serif" in fam:
        kwargs["font_family"] = kwargs["sans_serif_family"] = fam["sans-serif"]
    if "serif" in fam:
        kwargs["serif_family"] = fam["serif"]
    if "monospace" in fam:
        kwargs["monospace_family"] = fam["monospace"]
    png.write_bytes(bytes(resvg_py.svg_to_bytes(**kwargs)))


def r_cairosvg(svg: Path, png: Path, w: int, h: int, bg: str, fonts: list[str]) -> None:
    try:
        cairosvg = importlib.import_module("cairosvg")
    except (ImportError, OSError) as exc:  # OSError: libcairo missing
        raise Unavailable(f"cairosvg unusable: {str(exc).splitlines()[0]}") from exc
    cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=w, background_color=bg)


def _which(*names: str) -> str:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    raise Unavailable(f"none of {names} on PATH")


def r_resvg_cli(svg, png, w, h, bg, fonts):
    exe = _which("resvg")
    cmd = [exe, "-w", str(w), "--background", bg]
    for d in fonts:
        cmd += ["--use-fonts-dir", d]
    fam = font_families()
    for generic, flag in (("sans-serif", "--sans-serif-family"), ("serif", "--serif-family"),
                          ("monospace", "--monospace-family")):
        if generic in fam:
            cmd += [flag, fam[generic]]
    run(cmd + [str(svg), str(png)])


def r_rsvg_convert(svg, png, w, h, bg, fonts):
    run([_which("rsvg-convert"), "-w", str(w), "-b", bg, "-o", str(png), str(svg)])


def r_inkscape(svg, png, w, h, bg, fonts):
    run([_which("inkscape"), str(svg), "--export-type=png", f"--export-filename={png}",
         f"--export-width={w}", f"--export-background={bg}", "--export-background-opacity=1"])


def r_node_resvg_js(svg, png, w, h, bg, fonts):
    node = _which("node")
    js = ("const {Resvg}=require('@resvg/resvg-js');const fs=require('fs');"
          "const [s,o,w,bg,sans]=process.argv.slice(1);const font={loadSystemFonts:true};"
          "if(sans){font.defaultFontFamily=sans;font.sansSerifFamily=sans;}"
          "const r=new Resvg(fs.readFileSync(s),{background:bg,fitTo:{mode:'width',value:+w},font});"
          "fs.writeFileSync(o,r.render().asPng());")
    cwd = str(svg.parent)
    probe = subprocess.run([node, "-e", "require.resolve('@resvg/resvg-js')"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=cwd)
    if probe.returncode != 0:
        raise Unavailable("node found but @resvg/resvg-js not resolvable")
    run([node, "-e", js, str(svg.resolve()), str(png.resolve()), str(w), bg,
         font_families().get("sans-serif", "")], cwd=cwd)


def _chrome() -> str:
    for n in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
        p = shutil.which(n)
        if p:
            return p
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(mac):
        return mac
    for base in (os.environ.get("PLAYWRIGHT_BROWSERS_PATH"), os.path.expanduser("~/.cache/ms-playwright")):
        if base and os.path.isdir(base):
            for p in sorted(Path(base).glob("chromium-*/chrome-linux*/chrome"), reverse=True):
                return str(p)
    raise Unavailable("no Chrome/Chromium binary found")


def r_chrome(svg, png, w, h, bg, fonts):
    exe = _chrome()
    tmp = Path(tempfile.mkdtemp(prefix=".chrome-", dir=str(png.parent)))
    page = tmp / "page.html"
    page.write_text(f'<html><body style="margin:0;background:{bg}">'
                    f'<img src="{svg.resolve().as_uri()}" width="{w}" height="{h}" '
                    f'style="display:block"></body></html>', encoding="utf-8")
    cmd = [exe, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--no-default-browser-check", f"--user-data-dir={tmp / 'profile'}",
           "--force-device-scale-factor=1", f"--window-size={w},{h}",
           f"--screenshot={png.resolve()}", page.as_uri()]
    if sys.platform.startswith("linux"):
        cmd.insert(1, "--no-sandbox")  # containers and root sessions cannot use Chrome's sandbox
    # Chrome may write the screenshot and then linger (macOS updater helpers kept
    # it alive for more than 45 s), so poll for a complete PNG instead of waiting.
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
    try:
        deadline, last = time.time() + 60, -1
        while True:
            size = png.stat().st_size if png.exists() else -1
            if size > 0 and (size == last or proc.poll() is not None) and png_size(png):
                break
            if proc.poll() is not None and size <= 0:
                raise RuntimeError(f"chrome exited {proc.returncode} without a screenshot")
            if time.time() > deadline:
                raise RuntimeError("chrome produced no screenshot within 60 s")
            last = size
            time.sleep(0.5)
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except (AttributeError, OSError):
            if proc.poll() is None:
                proc.kill()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        try:  # helpers can outlive the main process
            os.killpg(proc.pid, getattr(signal, "SIGKILL", signal.SIGTERM))
        except (AttributeError, OSError):
            pass
        shutil.rmtree(tmp, ignore_errors=True)


RENDERERS = [
    ("resvg_py", r_resvg_py),
    ("resvg-cli", r_resvg_cli),
    ("rsvg-convert", r_rsvg_convert),
    ("cairosvg", r_cairosvg),
    ("inkscape", r_inkscape),
    ("node-resvg-js", r_node_resvg_js),
    ("chrome-headless", r_chrome),
]


def pydeps_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    tag = f"{sys.implementation.cache_tag}-{sysconfig.get_platform()}"
    return Path(base) / "logo-image" / "pydeps" / tag


def trusted_dir(d: Path) -> bool:
    """Only import from a directory this user owns and nobody else can write."""
    try:
        st = d.stat()
    except OSError:
        return False
    if not d.is_dir():
        return False
    if hasattr(os, "getuid") and st.st_uid != os.getuid():
        return False
    return not st.st_mode & 0o022


def add_import_dir(d: Path) -> None:
    if str(d) not in sys.path:
        sys.path.append(str(d))  # append: never shadow the standard library
        importlib.invalidate_caches()


def use_cached_pydeps() -> None:
    d = pydeps_dir()
    if trusted_dir(d):
        add_import_dir(d)


def pypi_unreachable() -> bool:
    proxy_vars = ("HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "PIP_INDEX_URL",
                  "PIP_PROXY", "UV_INDEX_URL", "UV_DEFAULT_INDEX")
    if any(os.environ.get(k) for k in proxy_vars):
        return False  # a proxy or mirror decides; let the installer try
    try:
        socket.create_connection(("pypi.org", 443), timeout=5).close()
        return False
    except OSError:
        return True


def try_install_resvg_py() -> str:
    """Opt-in only. Installs the resvg_py wheel into a per-user cache directory."""
    if pypi_unreachable():
        return "install skipped: pypi.org:443 is not reachable from here"
    target, reusable = pydeps_dir(), True
    try:
        target.mkdir(parents=True, exist_ok=True)
        os.chmod(target, 0o755)
        if not trusted_dir(target):
            raise OSError("cache directory is not private to this user")
    except OSError:
        target, reusable = Path(tempfile.mkdtemp(prefix="logo-image-pydeps-")), False
    env = dict(os.environ, UV_CACHE_DIR=str(target / ".uv-cache"), UV_HTTP_TIMEOUT="15")
    cmds = []
    uv = shutil.which("uv")
    if uv:
        cmds.append([uv, "pip", "install", "--quiet", "--upgrade", "--python", sys.executable,
                     "--target", str(target), "resvg_py"])
    cmds.append([sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
                 "--upgrade", "--timeout", "15", "--retries", "1", "--target", str(target), "resvg_py"])
    attempts = []
    for cmd in cmds:
        try:
            run(cmd, timeout=150, env=env)
            add_import_dir(target)
            note = "" if reusable else " (temporary directory, not reused by later runs)"
            return f"installed resvg_py into {target} via {Path(cmd[0]).name}{note}"
        except Exception as exc:  # noqa: BLE001
            attempts.append(f"{Path(cmd[0]).name}: {exc}")
    return "install failed: " + " ; ".join(attempts)


def rasterize(svg: Path, png: Path, w: int, h: int, bg: str, fonts: list[str],
              only: str | None) -> tuple[str | None, list[str]]:
    log: list[str] = []
    for name, fn in RENDERERS:
        if only and name != only:
            continue
        try:
            if png.exists():
                png.unlink()
            fn(svg, png, w, h, bg, fonts)
            size = png_size(png)
            if not size:
                raise RuntimeError("renderer produced no valid PNG")
            if abs(size[0] - w) > 1 or abs(size[1] - h) > 1:
                raise RuntimeError(f"renderer produced {size[0]}x{size[1]}, expected {w}x{h}")
            log.append(f"{name}: ok {size[0]}x{size[1]} -> {png.name}")
            return name, log
        except Unavailable as exc:
            log.append(f"{name}: unavailable ({exc})")
        except Exception as exc:  # noqa: BLE001
            log.append(f"{name}: failed ({type(exc).__name__}: {str(exc)[:200]})")
    if png.exists():
        png.unlink()
    return None, log


# -------------------------------------------------------------------- output

def data_uri(svg_text: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg_text.encode()).decode()


def write_html(out: Path, title: str, sheet_svg: str, marks: list[Mark], grid: str,
               png_name: str | None, png_mode: str, bg: str, sheet_warnings: list[str]) -> None:
    cards = "\n".join(
        f'<figure><img src="{data_uri(m.source)}" alt="{html.escape(m.name)}">'
        f'<figcaption>{i + 1:02d} {html.escape(m.name)}'
        + "".join(f"<small>{html.escape(w)}</small>" for w in m.warnings)
        + "</figcaption></figure>"
        for i, m in enumerate(marks))
    if png_name:
        png_note = f'<p>Raster: <a href="{png_name}">{png_name}</a></p>'
    elif png_mode == "off":
        png_note = "<p>PNG rendering was skipped (--png off).</p>"
    else:
        png_note = "<p>No rasterizer was available; grid.svg is the deliverable.</p>"
    notes = "".join(f"<p class=warn>{html.escape(w)}</p>" for w in sheet_warnings)
    out.write_text(f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>
body{{margin:0;padding:24px 16px;background:{bg};color:#1f2937;font:14px/1.5 system-ui,sans-serif}}
main{{max-width:1200px;margin:0 auto}} h1{{font-size:20px;margin:0 0 12px}}
.sheet img{{width:100%;height:auto;display:block;border-radius:8px;box-shadow:0 1px 3px #0002}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:16px;margin-top:24px}}
figure{{margin:0;background:#fff;border-radius:8px;padding:12px}} figure img{{width:100%;aspect-ratio:1;object-fit:contain}}
figcaption{{font-size:12px;margin-top:6px}} small,.warn{{display:block;color:#b45309}}
</style><main><h1>{html.escape(title)} ({len(marks)} marks, {grid})</h1>
<div class="sheet"><img src="{data_uri(sheet_svg)}" alt="logo sheet"></div>{png_note}{notes}
<div class="grid">{cards}</div></main></html>
""", encoding="utf-8")


def color_arg(value: str) -> str:
    if not COLOR_ARG_RE.fullmatch(value):
        raise argparse.ArgumentTypeError("use a hex color such as #F6F3EC or a color name")
    return value


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="SVG files or directories containing .svg files (sorted by name)")
    ap.add_argument("--out", required=True, help="output directory (must not be an input directory)")
    ap.add_argument("--title", default="Logo mark collection")
    ap.add_argument("--cols", type=int, default=0, help="columns (default: even grid chosen from the count)")
    ap.add_argument("--allow-ragged", action="store_true", help="allow a partly empty last row")
    ap.add_argument("--cell", type=int, default=240)
    ap.add_argument("--gap", type=int, default=56)
    ap.add_argument("--pad", type=int, default=72)
    ap.add_argument("--inset", type=float, default=0.0, help="extra padding inside a cell, as a fraction")
    ap.add_argument("--bg", type=color_arg, default="#F6F3EC", help="sheet background (use the brief's paper)")
    ap.add_argument("--tile", type=color_arg, default="none", help="cell tile color, or 'none'")
    ap.add_argument("--scale", type=float, default=2.0, help="PNG pixels per SVG unit")
    ap.add_argument("--thumb-scale", type=float, default=0.25, help="thumbnail pixels per SVG unit, 0 to skip")
    ap.add_argument("--png", choices=["auto", "off", "require"], default="auto")
    ap.add_argument("--renderer", choices=[n for n, _ in RENDERERS], help="force one renderer")
    ap.add_argument("--install", action="store_true", help="pip-install resvg_py into a cache dir if no renderer works")
    ap.add_argument("--font-dir", action="append", default=[], help="extra font directory (only with --allow-text)")
    ap.add_argument("--allow-text", action="store_true", help="downgrade <text> from error to warning")
    ap.add_argument("--min", type=int, default=16, help="minimum number of marks")
    ap.add_argument("--max", type=int, default=20, help="maximum number of marks")
    ap.add_argument("--max-colors", type=int, default=4, help="palette size before a sheet warning")
    args = ap.parse_args()

    bad = []
    if args.cols < 0:
        bad.append("--cols must be 0 or more")
    if args.cell <= 0 or args.gap < 0 or args.pad < 0:
        bad.append("--cell must be positive and --gap/--pad not negative")
    if not 0 <= args.inset < 0.5:
        bad.append("--inset must be in [0, 0.5)")
    if args.scale <= 0 or args.thumb_scale < 0:
        bad.append("--scale must be positive and --thumb-scale not negative")
    if args.min < 1 or args.min > args.max or args.max_colors < 1:
        bad.append("--min must be 1..--max and --max-colors at least 1")
    if bad:
        ap.error("; ".join(bad))

    out = Path(args.out).resolve()
    files: list[Path] = []
    for item in args.inputs:
        p = Path(item)
        if p.is_dir():
            if p.resolve() == out:
                print("error: --out must not be one of the input directories", file=sys.stderr)
                return 2
            files += sorted((q for q in p.iterdir()
                             if q.suffix.lower() == ".svg" and not q.name.startswith(".") and not q.is_dir()),
                            key=lambda q: q.name)
        elif p.exists():
            files.append(p)
        else:
            print(f"error: {item} not found", file=sys.stderr)
            return 2
    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"error: --out {out}: {exc.strerror or exc}", file=sys.stderr)
        return 2
    for name in ("grid.svg", "grid.png", "grid-small.png", "index.html"):
        try:
            (out / name).unlink()
        except OSError:
            pass

    marks = [validate(f, args.allow_text) for f in files]
    n = len(marks)
    cols, rows = choose_grid(n, args.cols)
    if cols == 0 and args.allow_ragged and n > 0:
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
    problems = [f"{m.path.name}: {e}" for m in marks for e in m.errors]
    if not args.min <= n <= args.max:
        problems.append(f"got {n} marks, expected {args.min}-{args.max}")
    elif cols == 0:
        problems.append(f"{n} marks cannot fill an even grid; use 16 (4x4) or 20 (5x4)")
    elif n % cols and not args.allow_ragged:
        problems.append(f"{n} marks in {cols} columns leaves the last row partly empty; "
                        "change --cols or pass --allow-ragged")

    palette = sorted(set().union(*(m.colors for m in marks))) if marks else []
    sheet_warnings = []
    if len(palette) > args.max_colors:
        sheet_warnings.append(f"sheet uses {len(palette)} colors (limit {args.max_colors}): {', '.join(palette)}")
    owners: dict[str, list[str]] = collections.defaultdict(list)
    for m in marks:
        for sub in m.subpaths:
            owners[sub].append(m.name)
    for sub, names in sorted(owners.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(names) > 2:
            sheet_warnings.append(
                f"the same path data ({sub[:40]}...) is pasted into {len(names)} marks "
                f"({', '.join(sorted(names))}); redraw the subject in each slot's own construction")
    warning_total = sum(len(m.warnings) for m in marks) + len(sheet_warnings)

    report = {
        "status": "invalid", "count": n, "grid": f"{cols}x{rows}" if cols else None,
        "grid_svg": None, "grid_png": None, "grid_small_png": None, "renderer": None,
        "renderer_log": [], "preview": None, "palette": palette,
        "warnings": warning_total, "sheet_warnings": sheet_warnings,
        "marks": [{"pos": i + 1, "row": i // cols + 1 if cols else None,
                   "col": i % cols + 1 if cols else None, "file": str(m.path.resolve()),
                   "errors": m.errors, "warnings": m.warnings}
                  for i, m in enumerate(marks)],
    }
    for m in marks:
        for w in m.warnings:
            print(f"warning: {m.path.name}: {w}", file=sys.stderr)
    for w in sheet_warnings:
        print(f"warning: {w}", file=sys.stderr)
    if problems:
        (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
        print(json.dumps({"status": "invalid", "count": n, "errors": len(problems),
                          "report": str(out / "report.json")}))
        return 1

    sheet, width, height = compose(marks, cols, rows, args.cell, args.gap, args.pad,
                                   args.bg, args.tile, args.inset)
    sheet_svg = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(sheet, encoding="unicode")
    svg_path = out / "grid.svg"
    svg_path.write_text(sheet_svg, encoding="utf-8")

    renderer, log = None, []
    png_path, small_path = out / "grid.png", out / "grid-small.png"
    if args.png != "off":
        use_cached_pydeps()
        pw, ph = round(width * args.scale), round(height * args.scale)
        renderer, log = rasterize(svg_path, png_path, pw, ph, args.bg, args.font_dir, args.renderer)
        if renderer is None and args.install:
            log.append(try_install_resvg_py())
            renderer, more = rasterize(svg_path, png_path, pw, ph, args.bg, args.font_dir, "resvg_py")
            log += more
        if renderer and args.thumb_scale > 0:
            tw, th = round(width * args.thumb_scale), round(height * args.thumb_scale)
            ok, more = rasterize(svg_path, small_path, tw, th, args.bg, args.font_dir, renderer)
            log += more
            if not ok:
                log.append("thumbnail failed; view grid.png at reduced size instead")

    write_html(out / "index.html", args.title, sheet_svg, marks, f"{cols}x{rows}",
               "grid.png" if renderer else None, args.png, args.bg, sheet_warnings)
    status = "no_renderer" if args.png == "require" and renderer is None else "ok"
    report.update({
        "status": status, "sheet": [width, height], "grid_svg": str(svg_path),
        "grid_png": str(png_path) if renderer else None,
        "grid_small_png": str(small_path) if small_path.exists() else None,
        "renderer": renderer, "renderer_log": log, "preview": str(out / "index.html")})
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "count", "grid", "grid_png", "grid_small_png",
                                             "renderer", "warnings", "preview")}))
    if status == "no_renderer":
        print("error: --png require but no renderer succeeded:\n  " + "\n  ".join(log), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
