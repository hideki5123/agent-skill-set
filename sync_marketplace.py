#!/usr/bin/env python3
"""Sync authoring-first skills into marketplace plugin artifacts.

Usage:
  python sync_marketplace.py
  python sync_marketplace.py --validate
  python sync_marketplace.py --skills dev-workflow review-pr
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MARKETPLACE_ROOT = ROOT / "my-marketplace"
MARKETPLACE_REGISTRY = MARKETPLACE_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = MARKETPLACE_ROOT / "plugins"

EXCLUDED_SOURCE_DIRS = {
    ".git",
    ".cursor",
    "my-marketplace",
}
EXCLUDED_TREE_NAMES = {
    "__pycache__",
    ".DS_Store",
}


@dataclass
class SkillMeta:
    dir_name: str
    name: str
    description: str
    source_dir: Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_skill_frontmatter(skill_md: Path) -> tuple[str, str]:
    text = read_text(skill_md)
    if not text.startswith("---"):
        raise ValueError(f"{skill_md} is missing YAML frontmatter")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{skill_md} has malformed YAML frontmatter")

    frontmatter = parts[1].splitlines()
    name = ""
    description = ""

    idx = 0
    while idx < len(frontmatter):
        line = frontmatter[idx]
        stripped = line.strip()

        if stripped.startswith("name:"):
            name = stripped.split(":", 1)[1].strip()
            idx += 1
            continue

        if stripped.startswith("description:"):
            raw = stripped.split(":", 1)[1].strip()
            if raw in (">", "|"):
                idx += 1
                desc_lines: list[str] = []
                while idx < len(frontmatter):
                    block_line = frontmatter[idx]
                    if not block_line.startswith("  "):
                        break
                    desc_lines.append(block_line.strip())
                    idx += 1
                description = " ".join(line for line in desc_lines if line).strip()
                continue

            description = raw.strip()
            idx += 1
            continue

        idx += 1

    if not name:
        raise ValueError(f"{skill_md} frontmatter must include `name`")

    return name, description


def discover_source_skills(selected: set[str] | None) -> list[SkillMeta]:
    skills: list[SkillMeta] = []
    for child in ROOT.iterdir():
        if not child.is_dir():
            continue
        if child.name in EXCLUDED_SOURCE_DIRS:
            continue

        skill_md = child / "SKILL.md"
        if not skill_md.exists():
            continue

        name, description = parse_skill_frontmatter(skill_md)
        if selected and name not in selected and child.name not in selected:
            continue

        skills.append(
            SkillMeta(
                dir_name=child.name,
                name=name,
                description=description,
                source_dir=child,
            )
        )

    skills.sort(key=lambda item: item.name)
    return skills


def copy_skill_tree(source_dir: Path, dest_dir: Path) -> None:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    for item in source_dir.iterdir():
        if item.name in EXCLUDED_TREE_NAMES:
            continue
        dest_path = dest_dir / item.name
        if item.is_dir():
            shutil.copytree(
                item,
                dest_path,
                ignore=shutil.ignore_patterns(*EXCLUDED_TREE_NAMES),
            )
        else:
            shutil.copy2(item, dest_path)


def ensure_plugin_metadata(plugin_dir: Path, meta: SkillMeta) -> None:
    plugin_meta_dir = plugin_dir / ".claude-plugin"
    plugin_meta_dir.mkdir(parents=True, exist_ok=True)

    plugin_json_path = plugin_meta_dir / "plugin.json"
    version = "1.0.0"
    if plugin_json_path.exists():
        try:
            existing = json.loads(read_text(plugin_json_path))
            version = str(existing.get("version", version))
        except json.JSONDecodeError:
            pass

    plugin_json = {
        "name": meta.name,
        "version": version,
        "description": (meta.description or f"{meta.name} skill")[:200],
        "author": {"name": "Hideki"},
        "keywords": [meta.name],
        "license": "MIT",
        "skills": "./skills",
    }
    write_json(plugin_json_path, plugin_json)

    plugin_marketplace = {
        "name": "hideki-plugins",
        "owner": {"name": "Hideki"},
        "metadata": {"description": "Custom Claude Code plugins by Hideki"},
        "plugins": [
            {
                "name": meta.name,
                "source": {"type": "local", "path": "."},
                "description": plugin_json["description"],
                "version": version,
            }
        ],
    }
    write_json(plugin_meta_dir / "marketplace.json", plugin_marketplace)


def sync_registry(synced: list[SkillMeta]) -> None:
    if MARKETPLACE_REGISTRY.exists():
        registry = json.loads(read_text(MARKETPLACE_REGISTRY))
    else:
        registry = {"name": "hideki-plugins", "owner": {"name": "Hideki"}, "plugins": []}

    existing_plugins = registry.get("plugins", [])
    existing_by_name = {plugin.get("name"): plugin for plugin in existing_plugins}

    for meta in synced:
        existing_by_name[meta.name] = {
            "name": meta.name,
            "source": f"./plugins/{meta.name}",
            "description": (meta.description or f"{meta.name} skill")[:200],
        }

    registry["plugins"] = sorted(existing_by_name.values(), key=lambda item: item["name"])
    write_json(MARKETPLACE_REGISTRY, registry)


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def collect_files(base: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for file_path in base.rglob("*"):
        if not file_path.is_file():
            continue
        if any(part in EXCLUDED_TREE_NAMES for part in file_path.parts):
            continue
        rel = str(file_path.relative_to(base)).replace("\\", "/")
        files[rel] = file_hash(file_path)
    return files


def validate(meta: SkillMeta) -> list[str]:
    errors: list[str] = []
    plugin_skill_dir = PLUGINS_DIR / meta.name / "skills" / meta.name
    if not plugin_skill_dir.exists():
        return [f"[{meta.name}] missing generated directory: {plugin_skill_dir}"]

    source_files = collect_files(meta.source_dir)
    generated_files = collect_files(plugin_skill_dir)

    missing = sorted(set(source_files) - set(generated_files))
    extra = sorted(set(generated_files) - set(source_files))
    changed = sorted(
        rel for rel in source_files.keys() & generated_files.keys() if source_files[rel] != generated_files[rel]
    )

    if missing:
        errors.append(f"[{meta.name}] missing files in generated plugin: {', '.join(missing)}")
    if extra:
        errors.append(f"[{meta.name}] extra files in generated plugin: {', '.join(extra)}")
    if changed:
        errors.append(f"[{meta.name}] changed file content: {', '.join(changed)}")

    return errors


def run_sync(skills: list[SkillMeta]) -> None:
    synced: list[SkillMeta] = []

    for meta in skills:
        plugin_dir = PLUGINS_DIR / meta.name
        plugin_skill_dir = plugin_dir / "skills" / meta.name
        copy_skill_tree(meta.source_dir, plugin_skill_dir)
        ensure_plugin_metadata(plugin_dir, meta)
        synced.append(meta)
        print(f"Synced {meta.name}: {meta.source_dir} -> {plugin_skill_dir}")

    if synced:
        sync_registry(synced)
        print(f"Updated registry: {MARKETPLACE_REGISTRY}")
    else:
        print("No skills matched selection; nothing synced.")


def run_validate(skills: list[SkillMeta]) -> int:
    all_errors: list[str] = []
    for meta in skills:
        all_errors.extend(validate(meta))

    if all_errors:
        print("Validation failed:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print("Validation succeeded: source and generated skills are in sync.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync source skills to marketplace plugin artifacts")
    parser.add_argument("--validate", action="store_true", help="Validate generated plugins match source skills")
    parser.add_argument(
        "--skills",
        nargs="+",
        default=None,
        help="Optional skill names (or root dir names) to sync/validate",
    )
    args = parser.parse_args()

    selected = set(args.skills) if args.skills else None
    skills = discover_source_skills(selected)
    if not skills:
        print("No source skills found. Expected skill roots with SKILL.md at repo root.")
        return 1

    if args.validate:
        return run_validate(skills)

    run_sync(skills)
    return 0


if __name__ == "__main__":
    sys.exit(main())
