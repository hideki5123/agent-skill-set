#!/usr/bin/env bash
# POST local files to Figma MCP upload submit-URLs (multipart 'file' field —
# the filename becomes the Figma layer name).
# Usage: post_uploads.sh mapping.tsv
#   mapping.tsv lines: <submitUrl>\t<filepath>
set -euo pipefail
[ $# -eq 1 ] || { echo "usage: $0 mapping.tsv" >&2; exit 2; }
ok=0; fail=0
while IFS=$'\t' read -r url f; do
  [ -z "${url:-}" ] && continue
  r=$(curl -s -X POST -F "file=@${f}" "$url")
  if printf '%s' "$r" | grep -q '"success":true'; then
    ok=$((ok+1))
  else
    fail=$((fail+1)); echo "FAIL ${f}: ${r}" >&2
  fi
done < "$1"
echo "uploaded ok=${ok} fail=${fail}"
[ "$fail" -eq 0 ]
