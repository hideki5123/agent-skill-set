# Environments, renderers and installation

WHEN TO READ: when build_sheet.py reports no renderer; when running on claude.ai,
Claude Code on the web or Codex cloud; when installing or updating this skill.

## PNG renderers

`scripts/build_sheet.py` writes `report.json` on every run, and `grid.svg` and
`index.html` when validation passes. For PNGs it tries, in order:

1. the `resvg_py` Python module;
2. the `resvg` CLI;
3. `rsvg-convert`;
4. `cairosvg`;
5. `inkscape`;
6. node with `@resvg/resvg-js`;
7. headless Chrome or Chromium.

`--install` pip-installs `resvg_py` into
`${XDG_CACHE_HOME:-~/.cache}/logo-image/pydeps/<python>-<platform>`.

- The wheel is about 1.5 MB (about 2 MB installed) and has no system
  dependencies.
- Python 3.10+ gets the newest release; older interpreters get an older
  compatible one.
- Later runs reuse the install only when that directory belongs to the user and
  nobody else can write to it. Otherwise a temporary directory is used once.
- If pypi.org cannot be reached and no proxy is configured, `--install` gives up
  within seconds.
- Marks never contain text, so missing fonts do not matter.

| Surface | Usually found | What to do |
|---|---|---|
| macOS, Claude Code local or Remote Control | Chrome, if installed | nothing, or `--install` |
| Codex CLI / IDE / desktop app, default `workspace-write` sandbox | Chrome launch and network are both blocked | rerun the build command with escalated permissions; `--install` also needs network approval |
| Codex with `danger-full-access` | Chrome on macOS | nothing, or `--install` |
| Claude Code on the web | nothing | `--install` (PyPI is on the default Trusted allowlist) |
| claude.ai chat, code execution | unknown; the script probes | `--install` works only if the account allows package-manager egress; otherwise deliver SVG |
| Codex cloud | nothing; agent-phase internet is off by default | add `pip install resvg_py` to the environment setup script, or deliver SVG |

When nothing renders:

- Deliver `grid.svg` (opens in any browser) and `index.html` (a self-contained
  preview).
- State that no PNG was produced, so a source review of the SVG files replaced
  the visual QA pass.
- Do not claim the sheet was checked visually.

## Getting the image and delivering files

- Claude Code (local or cloud) and claude.ai: an attached or pasted image is
  visible to the model, which is all the SVG path needs. On claude.ai, uploads
  typically also appear under `/mnt/user-data/uploads` (not documented publicly).
- claude.ai: files written under `/mnt/user-data/outputs` are offered for
  download.
- Claude Code on the web: the session runs in a VM with a clone of the repo.
  Files reach the user only through a commit on a pushed branch. Ask before
  committing generated logos into their project.
- Codex: attach the image in the app, or use `codex exec -i photo.jpg "..."`.
  Copy generated images into the workspace output directory.

## Raster generation reachability

- **Codex `image_gen`:**
  - Needs a ChatGPT plan that includes Codex image generation.
  - It is a built-in tool rather than a shell command, so sandbox network
    settings are not expected to affect it (not verified).
  - Whether hosted Codex cloud tasks offer it is also unverified. If the tool is
    missing, use the SVG path.
- **gpt-image through the `openai-cli` skill** needs `OPENAI_API_KEY` in the
  environment and access to api.openai.com:
  - Claude Code on the web: api.openai.com is not on the Trusted allowlist. It
    needs Full or Custom network access plus the key as an environment variable.
    An environment API credential opens the host, but openai-cli cannot see the
    key.
  - claude.ai: api.openai.com is not reachable by default. It works only if an
    owner allowlists the domain or allows all domains, and the key still has to
    be supplied.
  - Treat this path as local-only.

## Installing and updating (maintainers)

The source of truth is `<repo-root>/logo-image/` in the skills repository.
Resolve `<repo-root>` with `git rev-parse --show-toplevel` from inside the
checkout.

| Target | Command or action |
|---|---|
| Claude Code local and Remote Control | `python my-skill-factory/scripts/install_skill.py logo-image/ --version X.Y.Z` |
| Codex CLI, IDE extension, desktop app | `python scripts/sync_skills.py --targets codex --skills logo-image` |
| claude.ai chat and Claude Code on the web | build the zip below, upload it under Customize > Skills, enable it |
| Codex cloud (unverified) | copy the folder into the task repository at `.agents/skills/logo-image/` |

Zip for claude.ai. The top-level entry must be the `logo-image/` folder:

```bash
cd <repo-root> && mkdir -p dist && rm -f dist/logo-image.zip && \
  zip -r dist/logo-image.zip logo-image -x 'logo-image/feedback/*' '*__pycache__*' '*.DS_Store'
```

Claude Code cloud sessions load skills enabled on the claude.ai account, so one
upload covers both surfaces. Re-upload after every change.

Frontmatter constraints:

- Keep the frontmatter to `name` and `description`. The Codex validator rejects
  extra keys such as `version`, and `name` must match the folder name. Pass the
  version to `install_skill.py --version` instead.
- Keep the description at 200 characters or fewer. The claude.ai help center
  states that limit.
- Codex shortens long descriptions when many skills are installed.
- Validate the way Codex does (PyYAML is required, hence `uv`):

```bash
uv run --with pyyaml python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" logo-image
```
