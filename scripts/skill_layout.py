"""Shared discovery/copy/validate logic for the Claude marketplace plugin layout.

`sync_marketplace.py` and `sync_skills.py` both write to
`my-marketplace/plugins/<name>/` and previously carried independent copies of
this logic that had drifted apart (one hoisted `agents/` and excluded it from
`skills/<name>/`, the other didn't; neither excluded `feedback/`, which churns
on every skill run and made `--validate` permanently red). This module is the
single source of truth for what belongs in a generated Claude plugin, so the
two entrypoints can no longer disagree about it.

The Codex sync target (`~/.codex/skills/<name>/`) is a deliberately different,
simpler contract — a flat copy including `agents/` and `feedback/` — and stays
implemented directly in `sync_skills.py`, not here.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_ROOT = PROJECT_ROOT / "my-marketplace"
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
    ".git",
}
AGENTS_SUBDIR = "agents"
FEEDBACK_SUBDIR = "feedback"

# Authoring-side directories that never belong in a generated Claude plugin
# copy. `agents/` is hoisted to `plugins/<name>/agents/` instead of living
# under `skills/<name>/agents/`; `feedback/` is dev-repo-only (it mutates on
# every skill run and has nothing to do with plugin content). Must stay in
# lockstep with `install_skill.py`'s `SKIP_DIRS`.
CLAUDE_SKILL_EXCLUDED_DIRS = {AGENTS_SUBDIR, FEEDBACK_SUBDIR}


@dataclass
class SkillMeta:
    dir_name: str
    name: str
    description: str
    source_dir: Path
    deprecated: bool = False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_skill_frontmatter(skill_md: Path) -> tuple[str, str, bool]:
    text = read_text(skill_md)
    if not text.startswith("---"):
        raise ValueError(f"{skill_md} is missing YAML frontmatter")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{skill_md} has malformed YAML frontmatter")

    frontmatter = parts[1].splitlines()
    name = ""
    description = ""
    deprecated = False

    idx = 0
    while idx < len(frontmatter):
        line = frontmatter[idx]
        stripped = line.strip()

        if stripped.startswith("name:"):
            name = stripped.split(":", 1)[1].strip()
            idx += 1
            continue

        if stripped.startswith("deprecated:"):
            deprecated = stripped.split(":", 1)[1].strip().lower() in ("true", "yes", "1")
            idx += 1
            continue

        if stripped.startswith("description:"):
            raw = stripped.split(":", 1)[1].strip()
            # YAML block scalar indicators (">", "|") may carry a chomping
            # modifier ("-" strip, "+" keep) or explicit indent digit right
            # after them (e.g. ">-", "|2") — match on the leading character,
            # not an exact "raw in (...)" check, or e.g. ">-" falls through
            # and gets treated as a literal one-line description.
            if raw[:1] in (">", "|"):
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

    return name, description, deprecated


def discover_source_skills(selected: set[str] | None) -> list[SkillMeta]:
    skills: list[SkillMeta] = []
    for child in PROJECT_ROOT.iterdir():
        if not child.is_dir():
            continue
        if child.name in EXCLUDED_SOURCE_DIRS:
            continue

        skill_md = child / "SKILL.md"
        if not skill_md.exists():
            continue

        name, description, deprecated = parse_skill_frontmatter(skill_md)
        if selected and name not in selected and child.name not in selected:
            continue

        skills.append(
            SkillMeta(
                dir_name=child.name,
                name=name,
                description=description,
                source_dir=child,
                deprecated=deprecated,
            )
        )

    skills.sort(key=lambda item: item.name)
    return skills


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


def copy_claude_skill_tree(source_dir: Path, dest_dir: Path) -> None:
    """Copy into `plugins/<name>/skills/<name>/`, excluding `agents/` (hoisted
    separately) and `feedback/` (dev-repo-only)."""
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    for item in source_dir.iterdir():
        if item.name in EXCLUDED_TREE_NAMES:
            continue
        if item.name in CLAUDE_SKILL_EXCLUDED_DIRS and item.is_dir():
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


def copy_agents_tree(source_dir: Path, plugin_dir: Path) -> bool:
    """Hoist `<source>/agents/` to `plugins/<name>/agents/`. Returns whether
    the source skill has an `agents/` directory at all."""
    source_agents = source_dir / AGENTS_SUBDIR
    if not source_agents.is_dir():
        return False

    dest_agents = plugin_dir / AGENTS_SUBDIR
    if dest_agents.exists():
        shutil.rmtree(dest_agents)
    shutil.copytree(
        source_agents,
        dest_agents,
        ignore=shutil.ignore_patterns(*EXCLUDED_TREE_NAMES),
    )
    return True


def ensure_plugin_metadata(plugin_dir: Path, meta: SkillMeta, has_agents: bool) -> None:
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

    plugin_json: dict = {
        "name": meta.name,
        "version": version,
        "description": (meta.description or f"{meta.name} skill")[:200],
        "author": {"name": "Hideki"},
        "keywords": [meta.name],
        "license": "MIT",
        "skills": "./skills",
    }
    # Deliberately NO "agents" key. `"agents": "./agents"` makes Claude Code reject the
    # manifest ("Plugin X has an invalid manifest file") and silently unregister the
    # plugin's SKILLS along with it. <plugin>/agents/*.md is discovered by convention,
    # so shipping the directory is sufficient — and is how the official plugins do it.
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


def validate_claude_plugin(meta: SkillMeta) -> list[str]:
    """Validate `plugins/<name>/` against source: the `skills/<name>/` tree,
    the hoisted `agents/` tree, and the `plugin.json` `agents` key. Earlier
    validators only checked the first of these, which let missing/stale
    `agents/` copies and metadata pass silently."""
    errors: list[str] = []
    plugin_dir = PLUGINS_DIR / meta.name
    plugin_skill_dir = plugin_dir / "skills" / meta.name
    if not plugin_skill_dir.exists():
        return [f"[{meta.name}] missing generated directory: {plugin_skill_dir}"]

    source_files = {
        rel: digest
        for rel, digest in collect_files(meta.source_dir).items()
        if not any(rel == d or rel.startswith(f"{d}/") for d in CLAUDE_SKILL_EXCLUDED_DIRS)
    }
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

    source_agents = meta.source_dir / AGENTS_SUBDIR
    plugin_agents = plugin_dir / AGENTS_SUBDIR
    has_source_agents = source_agents.is_dir()
    has_plugin_agents = plugin_agents.is_dir()

    if has_source_agents and not has_plugin_agents:
        errors.append(f"[{meta.name}] missing hoisted agents/ directory: {plugin_agents}")
    elif has_plugin_agents and not has_source_agents:
        errors.append(f"[{meta.name}] extra hoisted agents/ directory (no source agents/): {plugin_agents}")
    elif has_source_agents and has_plugin_agents:
        agent_source_files = collect_files(source_agents)
        agent_generated_files = collect_files(plugin_agents)
        a_missing = sorted(set(agent_source_files) - set(agent_generated_files))
        a_extra = sorted(set(agent_generated_files) - set(agent_source_files))
        a_changed = sorted(
            rel
            for rel in agent_source_files.keys() & agent_generated_files.keys()
            if agent_source_files[rel] != agent_generated_files[rel]
        )
        if a_missing:
            errors.append(f"[{meta.name}] missing files in agents/: {', '.join(a_missing)}")
        if a_extra:
            errors.append(f"[{meta.name}] extra files in agents/: {', '.join(a_extra)}")
        if a_changed:
            errors.append(f"[{meta.name}] changed file content in agents/: {', '.join(a_changed)}")

    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if plugin_json_path.exists():
        try:
            plugin_json = json.loads(read_text(plugin_json_path))
        except json.JSONDecodeError:
            plugin_json = {}
        # An "agents" key is INVALID in plugin.json — Claude Code rejects the whole
        # manifest and unregisters the plugin's skills too. Agents are discovered from
        # <plugin>/agents/ by convention. This check used to require the key, which is
        # what kept every agents-carrying skill in this repo silently unregistered.
        if "agents" in plugin_json:
            errors.append(
                f'[{meta.name}] plugin.json declares an "agents" key — this invalidates '
                f"the manifest and unregisters the plugin's skills. Remove it; agents/ "
                f"is discovered by convention."
            )
    elif has_source_agents:
        errors.append(f"[{meta.name}] plugin.json missing: {plugin_json_path}")

    return errors
