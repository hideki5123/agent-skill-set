#!/usr/bin/env bash
# chrome-use — drive an already-running, logged-in Chromium browser via
# AppleScript: navigate, interact, and extract from the REAL logged-in session
# with the browser left open and no profile copy. macOS only.
#
# Subcommands:
#   check   [--app NAME]
#   run     [--app NAME] [--url URL] --js FILE|- [--wait SEL] [--out PATH] [--keep-tab]
#   screenshot [--app NAME] [--out PATH]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="Google Chrome"
TMPROOT="${CLAUDE_JOB_DIR:+$CLAUDE_JOB_DIR/tmp}"
TMPROOT="${TMPROOT:-${TMPDIR:-/tmp}}"
[ -d "$TMPROOT" ] || TMPROOT="${TMPDIR:-/tmp}"

guidance() {
	# $1 = combined stderr text from osascript
	local s="$1"
	if printf '%s' "$s" | grep -qiE "turned off|\(12\)"; then
		cat >&2 <<EOF
[chrome-use] "Allow JavaScript from Apple Events" が無効です。
  対処: $APP のメニュー → View → Developer → Allow JavaScript from Apple Events を ON。
  （このトグルはスクリプトから自動でONにできません。手動操作が必要です。）
EOF
	elif printf '%s' "$s" | grep -q -- "-1743"; then
		cat >&2 <<EOF
[chrome-use] 自動化(Automation)の許可がありません。
  対処: フォアグラウンドで 'chrome-use.sh check' を実行し、
  「"…" が "$APP" を操作しようとしています」ダイアログで「許可」を押してください。
EOF
	elif printf '%s' "$s" | grep -q -- "-1712"; then
		cat >&2 <<EOF
[chrome-use] 自動化の許可が承認待ち、または $APP が応答していません(-1712)。
  対処: 画面の許可ダイアログを承認してください（別画面/ウィンドウの裏に隠れがち）。
  バックグラウンド実行では承認できません。フォアグラウンドで再実行を。
EOF
	elif printf '%s' "$s" | grep -q -- "-1723"; then
		cat >&2 <<EOF
[chrome-use] JS実行が拒否されました(-1723)。考えられる原因:
  - "Allow JavaScript from Apple Events" が OFF（→ メニューで ON）
  - 対象タブが chrome:// 等のスクリプト不可ページ（→ 通常のWebページをアクティブに）
EOF
	elif printf '%s' "$s" | grep -q "wait-timeout"; then
		local msg
		msg=$(printf '%s' "$s" | sed -n 's/.*\(wait-timeout:.*\)/\1/p' | head -1)
		printf '[chrome-use] 待機タイムアウト: %s\n' "${msg:-$s}" >&2
	else
		printf '[chrome-use] エラー: %s\n' "$s" >&2
	fi
}

ensure_app() {
	if ! open -Ra "$APP" 2>/dev/null; then
		cat >&2 <<EOF
[chrome-use] アプリが見つかりません: "$APP"
  --app にChromium系の正しいアプリ名を指定してください
  （例: "Google Chrome", "Brave Browser", "Microsoft Edge", "Arc", "Vivaldi"）。
EOF
		return 1
	fi
}

cmd_check() {
	while [ $# -gt 0 ]; do case "$1" in
		--app) APP="$2"; shift 2;;
		*) shift;;
	esac; done
	echo "== chrome-use preflight (app: $APP) =="
	ensure_app || return 2
	local out
	# 1) Automation consent — must succeed in the FOREGROUND on first grant.
	if out=$(osascript -e "tell application \"$APP\" to return (count of windows)" 2>&1); then
		echo "[OK] 自動化許可: $APP を操作できます (windows=$out)"
	else
		echo "[NG] 自動化許可なし"
		guidance "$out"
		return 1
	fi
	# 2) JS-from-Apple-Events toggle — probe with 1+1 (locale-independent).
	if out=$(osascript -e "tell application \"$APP\" to tell active tab of front window to return (execute javascript \"1+1\")" 2>&1); then
		if [ "$out" = "2" ]; then
			echo "[OK] Allow JavaScript from Apple Events: 有効"
		else
			echo "[??] JS実行は通りましたが戻り値が想定外: $out"
		fi
	else
		echo "[NG] JavaScript実行不可"
		guidance "$out"
		return 1
	fi
	echo "preflight 完了 — chrome-use run が使えます。"
}

cmd_run() {
	local url="" jsfile="" wait="" out="" keep="0"
	while [ $# -gt 0 ]; do case "$1" in
		--app) APP="$2"; shift 2;;
		--url) url="$2"; shift 2;;
		--js) jsfile="$2"; shift 2;;
		--wait) wait="$2"; shift 2;;
		--out) out="$2"; shift 2;;
		--keep-tab) keep="1"; shift;;
		*) echo "[chrome-use] 不明な引数: $1" >&2; return 2;;
	esac; done

	local tmpjs="" cleanup_js="0"
	if [ "$jsfile" = "-" ]; then
		tmpjs="$(mktemp "$TMPROOT/chrome-use-XXXXXX.js")"
		cat > "$tmpjs"
		cleanup_js="1"
	elif [ -n "$jsfile" ]; then
		[ -f "$jsfile" ] || { echo "[chrome-use] JSファイルが見つかりません: $jsfile" >&2; return 2; }
		tmpjs="$jsfile"
	else
		echo "[chrome-use] --js FILE|- が必要です" >&2; return 2
	fi

	ensure_app || { [ "$cleanup_js" = "1" ] && rm -f "$tmpjs"; return 2; }

	# The app name must be literal in the AppleScript (terminology can't load from a
	# variable), so substitute it into a temp copy of the template before running.
	local tmpscpt
	tmpscpt="$(mktemp "$TMPROOT/chrome-use-run-XXXXXX.applescript")"
	sed "s|__APP__|$APP|g" "$SCRIPT_DIR/run.applescript" > "$tmpscpt"

	local errf rc=0 result=""
	errf="$(mktemp "$TMPROOT/chrome-use-err-XXXXXX")"
	if result=$(osascript "$tmpscpt" "$url" "$tmpjs" "$wait" "30" "$keep" 2>"$errf"); then
		if [ -n "$out" ]; then
			printf '%s' "$result" > "$out"
			echo "[chrome-use] 出力を $out に保存しました"
		else
			printf '%s\n' "$result"
		fi
	else
		rc=$?
		guidance "$(cat "$errf")"
	fi
	rm -f "$errf" "$tmpscpt"
	[ "$cleanup_js" = "1" ] && rm -f "$tmpjs"
	return $rc
}

cmd_screenshot() {
	local out="screenshot.png"
	while [ $# -gt 0 ]; do case "$1" in
		--app) APP="$2"; shift 2;;
		--out) out="$2"; shift 2;;
		*) shift;;
	esac; done
	ensure_app || return 2
	osascript -e "tell application \"$APP\" to activate" >/dev/null 2>&1 || true
	local b
	if ! b=$(osascript -e "tell application \"$APP\" to get bounds of front window" 2>&1); then
		guidance "$b"; return 1
	fi
	# b looks like: "12, 34, 1440, 900"
	local x1 y1 x2 y2
	IFS=', ' read -r x1 y1 x2 y2 <<<"$b"
	local w=$((x2 - x1)) h=$((y2 - y1))
	if screencapture -x -R "${x1},${y1},${w},${h}" "$out" 2>/dev/null && [ -s "$out" ]; then
		echo "[chrome-use] $out に保存 (window region ${x1},${y1} ${w}x${h})"
	else
		# Region capture can fail across multiple/secondary displays; fall back to
		# capturing the full screen the browser is on (best-effort).
		if screencapture -x "$out" 2>/dev/null && [ -s "$out" ]; then
			echo "[chrome-use] ウィンドウ領域の取得に失敗したため全画面を保存: $out"
		else
			echo "[chrome-use] スクリーンショットに失敗しました" >&2
			return 1
		fi
	fi
}

sub="${1:-}"; [ $# -gt 0 ] && shift || true
case "$sub" in
	check) cmd_check "$@";;
	run) cmd_run "$@";;
	screenshot) cmd_screenshot "$@";;
	*) cat >&2 <<'EOF'
usage:
  chrome-use.sh check [--app NAME]
  chrome-use.sh run [--app NAME] [--url URL] --js FILE|- [--wait SELECTOR] [--out PATH] [--keep-tab]
  chrome-use.sh screenshot [--app NAME] [--out PATH]
EOF
	   exit 2;;
esac
