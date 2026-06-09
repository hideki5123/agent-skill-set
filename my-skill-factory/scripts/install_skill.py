#!/usr/bin/env python3
"""Install a skill into the hideki-plugins local marketplace.

Usage:
    python install_skill.py <skill-dir> [--version VERSION]

This script:
1. Copies skill files into the marketplace plugin structure
2. Registers the plugin in the root marketplace.json
3. Caches the plugin for Claude Code
4. Registers in installed_plugins.json
5. Enables in settings.json

All paths are configured for Hideki's environment.
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Environment paths ──────────────────────────────────────────────
def _find_marketplace_dir() -> Path:
    """Locate the my-marketplace root. Honors MY_MARKETPLACE_DIR; otherwise
    walks up from this script looking for a directory that contains
    .claude-plugin/marketplace.json (either the parent itself or a
    `my-marketplace` sibling). Works on Linux, macOS, and Windows."""
    env = os.environ.get("MY_MARKETPLACE_DIR")
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve()
    for cur in [here.parent, *here.parents]:
        if (cur / ".claude-plugin" / "marketplace.json").exists():
            return cur
        sibling = cur / "my-marketplace"
        if (sibling / ".claude-plugin" / "marketplace.json").exists():
            return sibling.resolve()
    sys.exit(
        "Error: could not locate my-marketplace directory. "
        "Set MY_MARKETPLACE_DIR to override."
    )


MARKETPLACE_DIR = _find_marketplace_dir()
MARKETPLACE_JSON = MARKETPLACE_DIR / ".claude-plugin" / "marketplace.json"
CLAUDE_DIR = Path.home() / ".claude"
PLUGINS_DIR = CLAUDE_DIR / "plugins"
INSTALLED_JSON = PLUGINS_DIR / "installed_plugins.json"
SETTINGS_JSON = CLAUDE_DIR / "settings.json"
CACHE_DIR = PLUGINS_DIR / "cache" / "hideki-plugins"
MARKETPLACE_NAME = "hideki-plugins"


def strip_comments(text: str) -> str:
    # Remove // line comments and /* */ block comments, but NOT when they appear
    # inside a JSON string — e.g. the // in an "http://..." URL must survive.
    # String-aware scan (honors backslash escapes); preserves newlines so line
    # numbers in any parse error still match the source.
    out = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == '\\' and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1; continue
        if c == '"':
            in_str = True; out.append(c); i += 1; continue
        if c == '/' and i + 1 < n and text[i + 1] == '/':
            j = i + 2
            while j < n and text[j] != '\n':
                j += 1
            i = j; continue
        if c == '/' and i + 1 < n and text[i + 1] == '*':
            j = i + 2
            while j + 1 < n and not (text[j] == '*' and text[j + 1] == '/'):
                j += 1
            i = j + 2; continue
        out.append(c); i += 1
    return ''.join(out)

def read_json(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    clean_text = strip_comments(text)
    return json.loads(clean_text)


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


TOP_LEVEL_KEY = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")


def parse_frontmatter(fm: str) -> dict:
    """Parse the subset of YAML these SKILL.md frontmatters use.

    Handles top-level ``key: value`` plus folded (``>``) and literal (``|``)
    block scalars whose continuation lines are indented. Continuation lines are
    never mistaken for their own keys — which is why a naive line-by-line
    ``partition(':')`` mangled folded ``description: >`` blocks down to ``>``.
    Not a general YAML parser; just enough for name / description / deprecated.
    """
    meta = {}
    lines = fm.splitlines()
    i, n = 0, len(lines)
    while i < n:
        m = TOP_LEVEL_KEY.match(lines[i])
        if not m:
            i += 1
            continue
        key, rest = m.group(1).strip(), m.group(2).strip()
        i += 1
        if rest and rest[0] in (">", "|"):
            # Block scalar — gather indented (or blank) continuation lines.
            folded = rest[0] == ">"
            block = []
            while i < n and (lines[i].strip() == "" or lines[i][:1] in (" ", "\t")):
                block.append(lines[i].strip())
                i += 1
            if folded:
                meta[key] = " ".join(b for b in block if b)
            else:
                meta[key] = "\n".join(block).strip()
        else:
            meta[key] = rest
    return meta


def extract_skill_meta(skill_dir: Path) -> dict:
    """Read name and description from SKILL.md frontmatter."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        sys.exit(f"Error: {skill_md} not found")

    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        sys.exit("Error: SKILL.md missing YAML frontmatter")

    # Parse frontmatter between --- markers
    parts = text.split("---", 2)
    if len(parts) < 3:
        sys.exit("Error: SKILL.md frontmatter not properly closed")

    return parse_frontmatter(parts[1])


def install(skill_dir: Path, version: str, cache_only: bool = False):
    skill_dir = skill_dir.resolve()
    if not skill_dir.is_dir():
        sys.exit(f"Error: {skill_dir} is not a directory")

    # Guard against CRLF-induced whitespace ending up in the version string
    # (would result in a cache dir literally named "1.1.0\r").
    version = (version or "").strip()

    meta = extract_skill_meta(skill_dir)
    name = (meta.get("name") or "").strip()
    desc = meta.get("description", "")
    if not name:
        sys.exit("Error: SKILL.md frontmatter missing 'name' field")

    # A skill marked `deprecated: true` in its SKILL.md frontmatter is still
    # cached/registered (so it stays in the catalog for reference), but is NOT
    # enabled. This makes deprecation durable: re-running install — including
    # the pre-push hook's --cache-only path — keeps it disabled instead of
    # silently re-enabling it.
    deprecated = (meta.get("deprecated") or "").strip().lower() in ("true", "yes", "1")

    plugin_key = f"{name}@{MARKETPLACE_NAME}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    print(f"Installing skill: {name} v{version}"
          f"{' (cache-only)' if cache_only else ''}"
          f"{' [DEPRECATED — will stay disabled]' if deprecated else ''}")

    # Directories to exclude from the skills/<name>/ copy.
    # - feedback / .git / __pycache__ are authoring-side data.
    # - "agents" is excluded here because plugin subagents live at
    #   <plugin>/agents/, NOT under skills/<name>/agents/. They are copied
    #   separately below (see copy_agents_tree).
    SKIP_DIRS = {"feedback", ".git", "__pycache__", "agents"}
    has_agents = (skill_dir / "agents").is_dir()

    if cache_only:
        # Build plugin structure in a temp directory, cache it, then clean up
        import tempfile
        tmp_root = Path(tempfile.mkdtemp())
        try:
            plugin_dir = tmp_root / name
            plugin_skills = plugin_dir / "skills" / name
            plugin_claude = plugin_dir / ".claude-plugin"
            plugin_skills.mkdir(parents=True)
            plugin_claude.mkdir(parents=True)

            for item in skill_dir.iterdir():
                if item.is_dir() and item.name in SKIP_DIRS:
                    continue
                dest = plugin_skills / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)

            # Plugin subagents live at <plugin>/agents/, NOT under skills/<name>/.
            if has_agents:
                shutil.copytree(skill_dir / "agents", plugin_dir / "agents")

            plugin_json = {
                "name": name, "version": version, "description": desc[:200],
                "author": {"name": "Hideki"}, "keywords": [name],
                "license": "MIT", "skills": "./skills"
            }
            if has_agents:
                plugin_json["agents"] = "./agents"
            write_json(plugin_claude / "plugin.json", plugin_json)
            write_json(plugin_claude / "marketplace.json", {
                "name": MARKETPLACE_NAME,
                "owner": {"name": "Hideki"},
                "metadata": {"description": "Custom Claude Code plugins by Hideki"},
                "plugins": [{"name": name, "source": {"type": "local", "path": "."},
                             "description": desc[:200], "version": version}]
            })

            cache_dir = CACHE_DIR / name / version
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
            shutil.copytree(plugin_dir, cache_dir)
            print(f"  [+] Cached: {cache_dir}")
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)
    else:
        # 1. Create marketplace plugin structure
        plugin_dir = MARKETPLACE_DIR / "plugins" / name
        plugin_skills = plugin_dir / "skills" / name
        plugin_claude = plugin_dir / ".claude-plugin"

        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)

        plugin_skills.mkdir(parents=True)
        plugin_claude.mkdir(parents=True)

        # Copy skill contents (excluding authoring-side directories)
        for item in skill_dir.iterdir():
            if item.is_dir() and item.name in SKIP_DIRS:
                continue
            dest = plugin_skills / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        # Plugin subagents live at <plugin>/agents/, NOT under skills/<name>/.
        if has_agents:
            shutil.copytree(skill_dir / "agents", plugin_dir / "agents")

        # Write plugin.json
        plugin_json = {
            "name": name,
            "version": version,
            "description": desc[:200],
            "author": {"name": "Hideki"},
            "keywords": [name],
            "license": "MIT",
            "skills": "./skills"
        }
        if has_agents:
            plugin_json["agents"] = "./agents"
        write_json(plugin_claude / "plugin.json", plugin_json)

        # Write per-plugin marketplace.json
        write_json(plugin_claude / "marketplace.json", {
            "name": MARKETPLACE_NAME,
            "owner": {"name": "Hideki"},
            "metadata": {"description": "Custom Claude Code plugins by Hideki"},
            "plugins": [{
                "name": name,
                "source": {"type": "local", "path": "."},
                "description": desc[:200],
                "version": version
            }]
        })
        print(f"  [+] Marketplace plugin: {plugin_dir}")

        # 2. Register in root marketplace.json
        marketplace = read_json(MARKETPLACE_JSON)
        existing = [p for p in marketplace["plugins"] if p["name"] != name]
        existing.append({
            "name": name,
            "source": f"./plugins/{name}",
            "description": desc[:200]
        })
        marketplace["plugins"] = existing
        write_json(MARKETPLACE_JSON, marketplace)
        print(f"  [+] Root marketplace.json updated")

        # 3. Cache for Claude Code
        cache_dir = CACHE_DIR / name / version
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        shutil.copytree(plugin_dir, cache_dir)
        print(f"  [+] Cached: {cache_dir}")

    # 4. Register in installed_plugins.json
    installed = read_json(INSTALLED_JSON)
    installed["plugins"][plugin_key] = [{
        "scope": "user",
        "installPath": str(cache_dir),
        "version": version,
        "installedAt": now,
        "lastUpdated": now,
        "gitCommitSha": ""
    }]
    write_json(INSTALLED_JSON, installed)
    print(f"  [+] installed_plugins.json updated")

    # 5. Enable in settings.json (but keep deprecated skills disabled)
    settings = read_json(SETTINGS_JSON)
    if "enabledPlugins" not in settings:
        settings["enabledPlugins"] = {}
    settings["enabledPlugins"][plugin_key] = not deprecated
    write_json(SETTINGS_JSON, settings)
    print(f"  [+] settings.json: {plugin_key} {'disabled (deprecated)' if deprecated else 'enabled'}")

    if deprecated:
        print(f"\nDone! '{name}' is cached and registered but left DISABLED (deprecated). "
              f"Re-running install will keep it disabled.")
    else:
        print(f"\nDone! '{name}' is now available as '{name}:{name}' in new Claude Code sessions.")


def main():
    parser = argparse.ArgumentParser(description="Install a skill into hideki-plugins marketplace")
    parser.add_argument("skill_dir", type=Path, help="Path to the skill directory containing SKILL.md")
    parser.add_argument("--version", default="1.0.0", help="Version string (default: 1.0.0)")
    parser.add_argument("--cache-only", action="store_true",
                        help="Only update the Claude Code cache, skip marketplace file writes")
    args = parser.parse_args()
    install(args.skill_dir, args.version, cache_only=args.cache_only)


if __name__ == "__main__":
    main()
