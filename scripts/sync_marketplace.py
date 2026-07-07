#!/usr/bin/env python3
"""Sync authoring-first skills into marketplace plugin artifacts.

Usage:
  python scripts/sync_marketplace.py
  python scripts/sync_marketplace.py --validate
  python scripts/sync_marketplace.py --skills dev-workflow review-pr

See skill_layout.py for the canonical Claude plugin layout both this script
and sync_skills.py's `claude` target share.
"""

from __future__ import annotations

import argparse
import sys

from skill_layout import (
    MARKETPLACE_REGISTRY,
    PLUGINS_DIR,
    SkillMeta,
    copy_agents_tree,
    copy_claude_skill_tree,
    discover_source_skills,
    ensure_plugin_metadata,
    sync_registry,
    validate_claude_plugin,
)


def run_sync(skills: list[SkillMeta]) -> None:
    synced: list[SkillMeta] = []

    for meta in skills:
        plugin_dir = PLUGINS_DIR / meta.name
        plugin_skill_dir = plugin_dir / "skills" / meta.name
        copy_claude_skill_tree(meta.source_dir, plugin_skill_dir)
        has_agents = copy_agents_tree(meta.source_dir, plugin_dir)
        ensure_plugin_metadata(plugin_dir, meta, has_agents)
        synced.append(meta)
        suffix = " (+agents)" if has_agents else ""
        print(f"Synced {meta.name}: {meta.source_dir} -> {plugin_skill_dir}{suffix}")

    if synced:
        sync_registry(synced)
        print(f"Updated registry: {MARKETPLACE_REGISTRY}")
    else:
        print("No skills matched selection; nothing synced.")


def run_validate(skills: list[SkillMeta]) -> int:
    all_errors: list[str] = []
    for meta in skills:
        all_errors.extend(validate_claude_plugin(meta))

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
