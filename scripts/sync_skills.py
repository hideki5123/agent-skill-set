#!/usr/bin/env python3
"""Sync authoring-first skills for Claude marketplace and Codex.

Usage:
  python scripts/sync_skills.py
  python scripts/sync_skills.py --skills dev-workflow review-pr
  python scripts/sync_skills.py --targets claude
  python scripts/sync_skills.py --targets codex
  python scripts/sync_skills.py --validate
  python scripts/sync_skills.py --targets codex --include-deprecated

The `claude` target shares its copy/validate logic with sync_marketplace.py
via skill_layout.py, so the two can no longer disagree about what belongs in
a generated Claude plugin. The `codex` target is a deliberately different,
simpler contract implemented directly here: a flat copy of the whole skill
tree (including `agents/` and `feedback/`) into `$CODEX_HOME/skills/<name>/`.

Skills marked `deprecated: true` in their SKILL.md frontmatter are excluded
from the `codex` target by default (and purged if a stale copy exists there)
so a disabled skill doesn't stay live for Codex indefinitely. Pass
`--include-deprecated` to sync/validate them anyway.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from skill_layout import (
    EXCLUDED_TREE_NAMES,
    MARKETPLACE_REGISTRY,
    PLUGINS_DIR,
    SkillMeta,
    collect_files,
    copy_agents_tree,
    copy_claude_skill_tree,
    discover_source_skills,
    ensure_plugin_metadata,
    sync_registry,
    validate_claude_plugin,
)

DEFAULT_CODEX_HOME = Path.home() / ".codex"


def resolve_codex_home(override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()

    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve()

    return DEFAULT_CODEX_HOME.resolve()


def codex_skills_dir(codex_home: Path) -> Path:
    return codex_home / "skills"


def copy_codex_skill_tree(source_dir: Path, dest_dir: Path) -> None:
    """Full flat copy including agents/ and feedback/ — Codex's own contract.
    Deliberately does not apply the Claude-layout exclusions."""
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


def validate_codex_tree(meta: SkillMeta, destination: Path) -> list[str]:
    errors: list[str] = []
    if not destination.exists():
        return [f"[{meta.name}] missing generated directory (codex skills dir): {destination}"]

    source_files = collect_files(meta.source_dir)
    generated_files = collect_files(destination)

    missing = sorted(set(source_files) - set(generated_files))
    extra = sorted(set(generated_files) - set(source_files))
    changed = sorted(
        rel for rel in source_files.keys() & generated_files.keys() if source_files[rel] != generated_files[rel]
    )

    if missing:
        errors.append(f"[{meta.name}] missing files in codex skills dir: {', '.join(missing)}")
    if extra:
        errors.append(f"[{meta.name}] extra files in codex skills dir: {', '.join(extra)}")
    if changed:
        errors.append(f"[{meta.name}] changed file content in codex skills dir: {', '.join(changed)}")

    return errors


def run_claude_sync(skills: list[SkillMeta]) -> None:
    synced: list[SkillMeta] = []
    for meta in skills:
        plugin_dir = PLUGINS_DIR / meta.name
        plugin_skill_dir = plugin_dir / "skills" / meta.name
        copy_claude_skill_tree(meta.source_dir, plugin_skill_dir)
        has_agents = copy_agents_tree(meta.source_dir, plugin_dir)
        ensure_plugin_metadata(plugin_dir, meta, has_agents)
        synced.append(meta)
        suffix = " (+agents)" if has_agents else ""
        print(f"[claude] Synced {meta.name}: {meta.source_dir} -> {plugin_skill_dir}{suffix}")

    if synced:
        sync_registry(synced)
        print(f"[claude] Updated registry: {MARKETPLACE_REGISTRY}")
    else:
        print("[claude] No skills matched selection; nothing synced.")


def run_codex_sync(skills: list[SkillMeta], codex_home: Path, include_deprecated: bool) -> None:
    skills_dir = codex_skills_dir(codex_home)
    skills_dir.mkdir(parents=True, exist_ok=True)

    if not skills:
        print("[codex] No skills matched selection; nothing synced.")
        return

    for meta in skills:
        destination = skills_dir / meta.name
        if meta.deprecated and not include_deprecated:
            if destination.exists():
                shutil.rmtree(destination)
                print(f"[codex] Purged deprecated skill: {destination}")
            else:
                print(f"[codex] Skipped deprecated skill: {meta.name}")
            continue
        copy_codex_skill_tree(meta.source_dir, destination)
        print(f"[codex] Synced {meta.name}: {meta.source_dir} -> {destination}")


def run_validate(skills: list[SkillMeta], targets: set[str], codex_home: Path, include_deprecated: bool) -> int:
    all_errors: list[str] = []

    for meta in skills:
        if "claude" in targets:
            all_errors.extend(validate_claude_plugin(meta))

        if "codex" in targets:
            codex_skill_dir = codex_skills_dir(codex_home) / meta.name
            if meta.deprecated and not include_deprecated:
                if codex_skill_dir.exists():
                    all_errors.append(
                        f"[{meta.name}] deprecated skill still present in codex skills dir: {codex_skill_dir} "
                        "(run `sync_skills.py --targets codex` to purge, or pass --include-deprecated to keep it)"
                    )
                continue
            all_errors.extend(validate_codex_tree(meta, codex_skill_dir))

    if all_errors:
        print("Validation failed:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    target_summary = ", ".join(sorted(targets))
    print(f"Validation succeeded for targets: {target_summary}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync source skills to Claude marketplace and Codex skills")
    parser.add_argument("--validate", action="store_true", help="Validate generated targets match source skills")
    parser.add_argument(
        "--skills",
        nargs="+",
        default=None,
        help="Optional skill names (or root dir names) to sync/validate",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        choices=["claude", "codex"],
        default=["claude", "codex"],
        help="Targets to sync/validate (default: claude codex)",
    )
    parser.add_argument(
        "--codex-home",
        default=None,
        help="Codex home directory (default: $CODEX_HOME or ~/.codex)",
    )
    parser.add_argument(
        "--include-deprecated",
        action="store_true",
        help="Also sync/validate deprecated skills for the codex target (default: excluded and purged)",
    )
    args = parser.parse_args()

    selected = set(args.skills) if args.skills else None
    skills = discover_source_skills(selected)
    if not skills:
        print("No source skills found. Expected skill roots with SKILL.md at repo root.")
        return 1

    targets = set(args.targets)
    codex_home = resolve_codex_home(args.codex_home)

    if args.validate:
        return run_validate(skills, targets, codex_home, args.include_deprecated)

    if "claude" in targets:
        run_claude_sync(skills)
    if "codex" in targets:
        run_codex_sync(skills, codex_home, args.include_deprecated)

    return 0


if __name__ == "__main__":
    sys.exit(main())
