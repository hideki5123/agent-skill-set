#!/usr/bin/env bash
# Launch a backgrounded, remote-controllable, autonomous Claude Code session that
# runs /prd-council seeded with an implementation brief. Emulates the user's `ccb`
# (= claude-bg --permission-mode auto --allow-dangerously-skip-permissions).
#
# Usage:
#   launch_council_session.sh --target <dir> --slug <slug> [--lang <l>]
#                             [--model <m>] [--brief <relpath>] [--print-only]
#
# Resolves claude-bg / claude on PATH — no operator-specific paths are embedded.
set -euo pipefail

target="" ; slug="" ; lang="auto" ; model="" ; brief="" ; print_only=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)     target="${2:-}"; shift 2 ;;
    --slug)       slug="${2:-}"; shift 2 ;;
    --lang)       lang="${2:-auto}"; shift 2 ;;
    --model)      model="${2:-}"; shift 2 ;;
    --brief)      brief="${2:-}"; shift 2 ;;
    --print-only) print_only=1; shift ;;
    *) echo "launch_council_session.sh: unknown arg '$1'" >&2; exit 2 ;;
  esac
done

[ -n "$target" ] || { echo "error: --target is required" >&2; exit 2; }
[ -n "$slug" ]   || { echo "error: --slug is required" >&2; exit 2; }
[ -d "$target" ] || { echo "error: target dir not found: $target" >&2; exit 2; }
[ -n "$brief" ]  || brief="docs/design/${slug}-impl-brief.md"

gen_uuid() {
  if command -v uuidgen >/dev/null 2>&1; then
    uuidgen | tr '[:upper:]' '[:lower:]'
  elif [ -r /proc/sys/kernel/random/uuid ]; then
    cat /proc/sys/kernel/random/uuid
  else
    od -An -tx1 -N16 /dev/urandom | tr -d ' \n' \
      | sed -E 's/(.{8})(.{4})(.{4})(.{4})(.{12})/\1-\2-\3-\4-\5/'
  fi
}

read -r -d '' seed <<EOF || true
Read the implementation brief at ${brief} — it is the finalized, already-grilled
and Codex-reviewed design. Treat it as the complete requirements: do NOT re-grill
from scratch. Then run /prd-council --slug ${slug} --out docs/prd/${slug}/ --lang ${lang},
using the brief as the agreed requirements; only ask if a genuine blocking gap
remains. Emit the execution-ready doc set + tasks.md, then begin implementation per
tasks.md, following the brief's Branch setup (fresh feature branch — never a
design/doc/PR branch).
EOF

model_args=()
[ -n "$model" ] && model_args=(--model "$model")

cd "$target"

# Build the human-readable command string for printing.
render_cmd() {
  if command -v claude-bg >/dev/null 2>&1; then
    printf 'claude-bg --label %q --permission-mode auto --allow-dangerously-skip-permissions' "$slug"
    [ -n "$model" ] && printf ' --model %q' "$model"
    printf ' %q\n' "$seed"
  else
    local sid sid8; sid="$(gen_uuid)"; sid8="${sid%%-*}"
    printf 'claude --session-id %q --remote-control %q --bg --permission-mode auto --allow-dangerously-skip-permissions' \
      "$sid" "${slug}-${sid8}"
    [ -n "$model" ] && printf ' --model %q' "$model"
    printf ' %q\n' "$seed"
  fi
}

if [ "$print_only" -eq 1 ]; then
  echo "# Run from: $target"
  render_cmd
  exit 0
fi

# 1) Preferred: the user's claude-bg launcher (ccb-style flags).
if command -v claude-bg >/dev/null 2>&1; then
  echo "Launching via claude-bg (label=${slug}) in ${target} ..." >&2
  exec claude-bg --label "$slug" \
    --permission-mode auto --allow-dangerously-skip-permissions \
    "${model_args[@]}" "$seed"
fi

# 2) Fallback: replicate claude-bg with plain claude.
if command -v claude >/dev/null 2>&1; then
  sid="$(gen_uuid)"; sid8="${sid%%-*}"
  echo "claude-bg not found; launching via 'claude --bg' (rc=${slug}-${sid8}) ..." >&2
  exec claude --session-id "$sid" --remote-control "${slug}-${sid8}" --bg \
    --permission-mode auto --allow-dangerously-skip-permissions \
    "${model_args[@]}" "$seed"
fi

# 3) Last resort: print the command for the user to run.
echo "error: neither 'claude-bg' nor 'claude' found on PATH." >&2
echo "Run this manually from ${target}:" >&2
render_cmd
exit 1
