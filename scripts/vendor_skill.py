#!/usr/bin/env python3
"""Vendor a single skill from an upstream GitHub repo into this repo (on-demand).

On-demand vendoring: fetch exactly one skill's files at a *pinned commit*, copy
them into a top-level ``<name>/`` directory, and write a ``LICENSE`` file that
records provenance (upstream URL, source path, commit SHA, retrieval date).

Supply-chain stance:
- No package manager, no install-time code execution. Only file downloads over
  HTTPS via the Python standard library (urllib). Nothing is executed.
- Pinned to a resolved commit SHA, so re-running is reproducible and an upstream
  force-push cannot silently change what you vendored.
- The surface you accept == the files visible in the resulting commit diff.
  Unused upstream skills never enter your tree.

This is the fetch+provenance stage only. Marketplace registration, caching, and
enablement are handled by ``my-skill-factory/scripts/install_skill.py`` (run it
afterwards, or pass ``--install`` to chain it).

Usage:
    # List skills available upstream (at the pinned/default ref)
    python scripts/vendor_skill.py --list

    # Vendor one skill (auto-locates skills/<category>/<name>)
    python scripts/vendor_skill.py grill-me

    # Pin to a specific commit / tag / branch
    python scripts/vendor_skill.py handoff --ref e3b90b5

    # Vendor, then install into the local marketplace
    python scripts/vendor_skill.py handoff --install

    # A different upstream repo / explicit path
    python scripts/vendor_skill.py foo --repo owner/repo --path skills/foo

An optional GITHUB_TOKEN / GH_TOKEN env var (existence only; never printed) is
used to raise the GitHub API rate limit. None is required for normal use.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

DEFAULT_REPO = "mattpocock/skills"
SKILLS_ROOT = "skills"  # upstream dir holding <category>/<name> skill dirs
API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"

REPO_ROOT = Path(__file__).resolve().parent.parent


def _request(url: str, raw: bool = False):
    headers = {
        "User-Agent": "agent-skill-set-vendor",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        sys.exit(f"Error: HTTP {e.code} fetching {url}\n{detail}")
    except urllib.error.URLError as e:
        sys.exit(f"Error: network failure fetching {url}: {e.reason}")
    return data if raw else json.loads(data)


def resolve_commit(repo: str, ref: str) -> str:
    """Resolve a branch / tag / SHA to a full commit SHA so the vendor is pinned."""
    return _request(f"{API}/repos/{repo}/commits/{ref}")["sha"]


def fetch_tree(repo: str, sha: str) -> list:
    """Return the full recursive git tree as a list of {path, type} entries."""
    data = _request(f"{API}/repos/{repo}/git/trees/{sha}?recursive=1")
    if data.get("truncated"):
        sys.exit("Error: upstream tree is truncated (repo too large for one recursive listing).")
    return data["tree"]


def list_skill_paths(tree: list) -> list:
    """Skill dirs = any directory under SKILLS_ROOT/ that contains a SKILL.md."""
    paths = []
    for e in tree:
        if e["type"] == "blob" and e["path"].endswith("/SKILL.md"):
            d = e["path"][: -len("/SKILL.md")]
            if d.startswith(SKILLS_ROOT + "/"):
                paths.append(d)
    return sorted(paths)


def locate_skill(skill_paths: list, name: str, explicit_path: str) -> str:
    if explicit_path:
        path = explicit_path.rstrip("/")
        if path not in skill_paths:
            sys.exit(f"Error: {path} has no SKILL.md upstream. Use --list to see options.")
        return path
    matches = [p for p in skill_paths if p.rsplit("/", 1)[-1] == name]
    if not matches:
        sys.exit(f"Error: no upstream skill named '{name}'. Use --list to see options.")
    if len(matches) > 1:
        joined = "\n  ".join(matches)
        sys.exit(f"Error: '{name}' is ambiguous; re-run with --path one of:\n  {joined}")
    return matches[0]


def fetch_raw(repo: str, sha: str, path: str) -> bytes:
    return _request(f"{RAW}/{repo}/{sha}/{path}", raw=True)


def write_provenance(repo: str, sha: str, skill_path: str, dest: Path, copied: list):
    try:
        license_text = fetch_raw(repo, sha, "LICENSE").decode("utf-8", "replace").strip()
    except SystemExit:
        license_text = "(upstream LICENSE not found at repo root)"
    lic_name = "MIT License" if "MIT License" in license_text else "license"
    files = ", ".join(sorted(copied)) or "SKILL.md"
    body = (
        f"Vendored from: https://github.com/{repo}\n"
        f"Source path:   {skill_path}/\n"
        f"Commit:        {sha}\n"
        f"Retrieved:     {date.today().isoformat()}\n\n"
        f"The skill files in this directory ({files}) are copied verbatim from the\n"
        f"upstream repository above and are distributed under the following {lic_name}.\n\n"
        + "-" * 70 + "\n\n"
        + license_text + "\n"
    )
    (dest / "LICENSE").write_text(body, encoding="utf-8")
    print(f"  [+] {dest.name}/LICENSE (provenance, pinned @ {sha[:10]})")


def vendor(repo: str, sha: str, skill_path: str, tree: list, dest_root: Path):
    name = skill_path.rsplit("/", 1)[-1]
    blobs = [
        e["path"] for e in tree
        if e["type"] == "blob" and e["path"].startswith(skill_path + "/")
    ]
    if not blobs:
        sys.exit(f"Error: no files found under {skill_path}")

    dest = dest_root / name
    dest.mkdir(parents=True, exist_ok=True)

    copied = []
    for bp in blobs:
        rel = bp[len(skill_path) + 1:]
        # We generate our own LICENSE provenance file; skip any upstream one.
        if rel == "LICENSE" or rel.startswith("LICENSE."):
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(fetch_raw(repo, sha, bp))
        copied.append(rel)
        print(f"  [+] {name}/{rel}")

    write_provenance(repo, sha, skill_path, dest, copied)
    return name, dest


def main():
    ap = argparse.ArgumentParser(
        description="Vendor a single skill from an upstream GitHub repo (on-demand, pinned).",
    )
    ap.add_argument("name", nargs="?", help="Skill name to vendor (basename of its upstream dir).")
    ap.add_argument("--repo", default=DEFAULT_REPO, help=f"owner/repo (default: {DEFAULT_REPO})")
    ap.add_argument("--ref", default="HEAD",
                    help="Branch / tag / SHA to pin (default: HEAD of the default branch)")
    ap.add_argument("--path", help="Explicit upstream skill path, e.g. skills/productivity/grill-me")
    ap.add_argument("--dest", type=Path, default=REPO_ROOT,
                    help="Destination root for the vendored <name>/ dir (default: repo root)")
    ap.add_argument("--list", action="store_true", help="List skills available upstream and exit")
    ap.add_argument("--install", action="store_true",
                    help="Run install_skill.py after vendoring")
    ap.add_argument("--version", default="1.0.0", help="Version passed to install_skill.py")
    args = ap.parse_args()

    sha = resolve_commit(args.repo, args.ref)
    tree = fetch_tree(args.repo, sha)
    skill_paths = list_skill_paths(tree)

    if args.list:
        print(f"Available skills in {args.repo} @ {sha[:10]}:")
        for p in skill_paths:
            rel = p[len(SKILLS_ROOT) + 1:] if p.startswith(SKILLS_ROOT + "/") else p
            print(f"  {rel:34}  (vendor name: {p.rsplit('/', 1)[-1]})")
        return

    if not args.name and not args.path:
        ap.error("provide a skill name, or --path, or --list")

    skill_path = locate_skill(skill_paths, args.name, args.path)
    print(f"Vendoring {skill_path} from {args.repo} @ {sha[:10]} ...")
    name, dest = vendor(args.repo, sha, skill_path, tree, args.dest)

    rel_dest = dest.relative_to(REPO_ROOT) if dest.is_relative_to(REPO_ROOT) else dest
    install_script = REPO_ROOT / "my-skill-factory" / "scripts" / "install_skill.py"
    print(f"\nVendored '{name}' -> {rel_dest}")

    if args.install:
        print("\nInstalling ...")
        subprocess.run(
            [sys.executable, str(install_script), str(dest), "--version", args.version],
            check=True,
        )
    else:
        rel_install = install_script.relative_to(REPO_ROOT)
        print("Review the files, then install into the local marketplace with:")
        print(f"  python {rel_install} {rel_dest}/ --version {args.version}")


if __name__ == "__main__":
    main()
