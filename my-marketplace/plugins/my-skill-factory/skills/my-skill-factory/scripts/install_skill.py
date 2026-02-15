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
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Environment paths ──────────────────────────────────────────────
MARKETPLACE_DIR = Path(r"D:\Shared\agents\my-skills\my-marketplace")
MARKETPLACE_JSON = MARKETPLACE_DIR / ".claude-plugin" / "marketplace.json"
CLAUDE_DIR = Path.home() / ".claude"
PLUGINS_DIR = CLAUDE_DIR / "plugins"
INSTALLED_JSON = PLUGINS_DIR / "installed_plugins.json"
SETTINGS_JSON = CLAUDE_DIR / "settings.json"
CACHE_DIR = PLUGINS_DIR / "cache" / "hideki-plugins"
MARKETPLACE_NAME = "hideki-plugins"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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

    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()
    return meta


def install(skill_dir: Path, version: str):
    skill_dir = skill_dir.resolve()
    if not skill_dir.is_dir():
        sys.exit(f"Error: {skill_dir} is not a directory")

    meta = extract_skill_meta(skill_dir)
    name = meta.get("name")
    desc = meta.get("description", "")
    if not name:
        sys.exit("Error: SKILL.md frontmatter missing 'name' field")

    plugin_key = f"{name}@{MARKETPLACE_NAME}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    print(f"Installing skill: {name} v{version}")

    # 1. Create marketplace plugin structure
    plugin_dir = MARKETPLACE_DIR / "plugins" / name
    plugin_skills = plugin_dir / "skills" / name
    plugin_claude = plugin_dir / ".claude-plugin"

    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)

    plugin_skills.mkdir(parents=True)
    plugin_claude.mkdir(parents=True)

    # Copy skill contents
    for item in skill_dir.iterdir():
        dest = plugin_skills / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    # Write plugin.json
    write_json(plugin_claude / "plugin.json", {
        "name": name,
        "version": version,
        "description": desc[:200],
        "author": {"name": "Hideki"},
        "keywords": [name],
        "license": "MIT",
        "skills": "./skills"
    })

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
        "installPath": str(cache_dir).replace("/", "\\"),
        "version": version,
        "installedAt": now,
        "lastUpdated": now,
        "gitCommitSha": ""
    }]
    write_json(INSTALLED_JSON, installed)
    print(f"  [+] installed_plugins.json updated")

    # 5. Enable in settings.json
    settings = read_json(SETTINGS_JSON)
    if "enabledPlugins" not in settings:
        settings["enabledPlugins"] = {}
    settings["enabledPlugins"][plugin_key] = True
    write_json(SETTINGS_JSON, settings)
    print(f"  [+] settings.json: {plugin_key} enabled")

    print(f"\nDone! '{name}' is now available as '{name}:{name}' in new Claude Code sessions.")


def main():
    parser = argparse.ArgumentParser(description="Install a skill into hideki-plugins marketplace")
    parser.add_argument("skill_dir", type=Path, help="Path to the skill directory containing SKILL.md")
    parser.add_argument("--version", default="1.0.0", help="Version string (default: 1.0.0)")
    args = parser.parse_args()
    install(args.skill_dir, args.version)


if __name__ == "__main__":
    main()
