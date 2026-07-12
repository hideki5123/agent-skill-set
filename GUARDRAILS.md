# AI Agent Sudo Permissions — ガードレール設計書

ローカルAIエージェントに `sudo` を含む特権操作を任せるための、3層パーミッションモデルと多層防御の設計ドキュメント。

> Status: Design only（実装は含みません。`.claude/settings.json` や hook の実体は本書を元に各リポジトリで導入する）

> **v2 (2026-05-16) で方針転換**: 検証 ([Anthropic Issue #9184](https://github.com/anthropics/claude-code/issues/9184) / [The Register 2026-04](https://www.theregister.com/2026/04/01/claude_code_rule_cap_raises/) / [Infralovers 2026-02](https://www.infralovers.com/blog/2026-02-15-sandboxing-claude-code-macos/)) の結果、「Agent に sudo を渡さない」が第一推奨。**§13** を最初に読み、sudoers ベースの v1 設計が必要かを判定すること。v1 の sudoers 詳細は **Appendix B** に退避した。

---

## 1. 目的とスコープ

ローカル開発機 / 開発サーバー / CI ランナー上で動くAIエージェントに対し:

- 読み取り系の安全操作は**自動許可**して生産性を落とさない
- 影響が大きい・取り消し可能な操作は**人間が承認**する
- 真に**不可逆かつ破滅的**な操作だけは**機械的に拒否**する
- パターンマッチングの脆弱性を**hook と sudoers の層**で補う
- すべての層は**最小権限**と**Complete Mediation**（強制点は下流）の原則で設計する

非スコープ: 本書はクラウド/IAM のエージェント権限設計（AWS Bedrock Agents 等）は扱わない。対象はローカルマシン上の Claude Code / Codex CLI / 類似ツールに限る。

---

## 2. 設計原則（業界ベストプラクティスの要約）

### 2.1 OWASP LLM06:2025 "Excessive Agency" の3軸最小化

LLMエージェントの暴走被害は次の3軸の積算で決まる。各軸を独立に最小化する。

| 軸 | 意味 | 本設計での対応 |
|---|---|---|
| **機能 (Functionality)** | エージェントが呼べる道具の集合 | open-ended なシェルは許すが、危険サブセットを deny/ask で削る |
| **権限 (Permissions)** | 道具が下流に対して持つ権限 | sudoers でコマンド単位ホワイトリスト。`NOPASSWD` は読み取り系のみ |
| **自律性 (Autonomy)** | 人間承認なしで実行できる範囲 | 影響大の操作は `ask` 強制。`bypassPermissions` は禁止 |

特に重要なのは **Complete Mediation**: LLMの「これは安全だ」という判断に依存せず、下流システム（sudoers, IAM, ファイルシステム権限）で物理的に強制する。

### 2.2 業界共通の原則

- **Least Privilege**: エージェントに渡す権限は「実際に必要なもの」のみ。デフォルト service account 流用はアンチパターン
- **独立アイデンティティ**: エージェントは専用ユーザー（例: `claude-agent`）として動かす。ユーザー成りすましにしない
- **Defense in Depth**: 単一の防御層に頼らない。パターン / hook / sudoers / 隔離 / 監査の積層
- **Human-in-the-loop**: 不可逆・影響大の操作は必ず人間承認
- **Audit & Anomaly Detection**: 全特権操作をログ化し、異常パターンを後追いできる状態にする

### 2.3 パターンマッチングの脆弱性（重要な制約）

Anthropic 公式ドキュメントは Bash パターン制約の脆弱性を明記している。例えば `Bash(curl http://github.com/*)` は以下で迂回される:

```bash
URL=http://github.com && curl $URL          # 変数経由
curl -X GET http://github.com/...            # フラグ前置
curl -L http://bit.ly/xyz                    # リダイレクト
curl  http://github.com                      # 余分なスペース
$(echo cu)rl http://github.com               # コマンド置換
```

したがって**パターン deny だけに依存してはならない**。本設計では PreToolUse hook と sudoers を補助層として要求する。

**実際の bypass 事例 (v2 追記)**: Claude Code v2.1.x 系で deny ルールの自動チェックが 50 個以上の subcommand chain (`&&` / `||` / `;` / `|`) で skip される脆弱性が Adversa により発見・公表された (`MAX_SUBCOMMANDS_FOR_SECURITY_CHECK = 50`)。50 個の no-op コマンドと危険コマンドを組み合わせると deny が回避され ask フォールバックに落ちる。v2.1.90 で patched。([The Register 2026-04-01](https://www.theregister.com/2026/04/01/claude_code_rule_cap_raises/))

これは「pattern deny だけに依存してはならない」原則を実証する事例であり、§13「agent に sudo を渡さない」が v2 で第一推奨になった主因の一つ。

---

## 3. 3層パーミッションモデル

評価順は **deny → ask → allow**（公式仕様）。最初にマッチしたルールが勝つので、deny は常に最強。

```
┌─────────────────────────────────────────────────────────┐
│ Tier 1: DENY  ← 真に不可逆＆破滅的（最小限）          │
├─────────────────────────────────────────────────────────┤
│ Tier 2: ASK   ← sudo を含む影響大の操作（広め）       │
├─────────────────────────────────────────────────────────┤
│ Tier 3: ALLOW ← 読み取り専用＆ローカル開発（明示分のみ）│
│                 ※読み取り系の多くは built-in 自動許可    │
└─────────────────────────────────────────────────────────┘
```

設計方針: **生産性重視（緩め）**。Deny は「やってしまったら復旧不能・サポート案件・セキュリティ事故」のみ。それ以外は ask に投げて人間に判断してもらう。

> **v2 注記**: §§3-7 は agent に sudo を渡す前提でも渡さない前提でも適用される共通基盤。「sudo を渡すかどうか」自体の判断は §13 を先に読むこと。

---

## 4. Tier 1: DENY（真に不可逆＆破滅的）

### 4.1 含めるカテゴリ（緩め版）

| カテゴリ | 理由 |
|---|---|
| ファイルシステムルート/ホームの破壊 | 復旧 = リストア。実質不可逆 |
| ブロックデバイスへの直接書き込み | 物理メディア破壊。即時不可逆 |
| Sudoers / passwd / shadow の改変 | サイレントな特権昇格、検出困難 |
| 認証情報の読み出し | 一度漏れたら回収不能 |
| リモートロックアウト | 復旧に物理アクセスが必要 |
| Fork bomb | システム凍結 |
| main/master への force push | git 履歴破壊、他開発者への影響大 |

### 4.2 ルール例（settings.json `permissions.deny`）

> **メモ**: 下記 JSON は `.claude/settings.json` の `permissions` キー配下に置く fragment。 単独で完全な settings として使うなら `{ "permissions": { "deny": [...] } }` のように 1 階層ラップする。

```json
{
  "deny": [
    "Bash(rm -rf /)",
    "Bash(rm -rf /*)",
    "Bash(rm -rf ~)",
    "Bash(rm -rf ~/*)",
    "Bash(rm -rf $HOME*)",
    "Bash(sudo rm -rf /)",
    "Bash(sudo rm -rf /*)",
    "Bash(sudo rm -rf ~)",
    "Bash(sudo rm -rf ~*)",
    "Bash(sudo rm -rf $HOME*)",
    "Bash(rm -rf /home/*)",
    "Bash(rm -rf /root)",
    "Bash(rm -rf /root/*)",
    "Bash(rm -rf /Users/*)",
    "Bash(sudo rm -rf /home/*)",
    "Bash(sudo rm -rf /root)",
    "Bash(sudo rm -rf /root/*)",
    "Bash(sudo rm -rf /Users/*)",

    "Bash(dd * of=/dev/sd*)",
    "Bash(dd * of=/dev/nvme*)",
    "Bash(sudo dd *)",
    "Bash(sudo mkfs*)",
    "Bash(sudo wipefs *)",
    "Bash(sudo shred /dev/*)",

    "Bash(sudo visudo*)",
    "Edit(/etc/sudoers)",
    "Edit(/etc/sudoers.d/**)",
    "Edit(/etc/passwd)",
    "Edit(/etc/shadow)",
    "Bash(sudo passwd root*)",

    "Bash(sudo systemctl stop ssh*)",
    "Bash(sudo systemctl disable ssh*)",
    "Bash(sudo systemctl mask ssh*)",

    "Read(~/.ssh/id_*)",
    "Read(~/.ssh/*_rsa)",
    "Read(~/.ssh/*_ed25519)",
    "Read(~/.aws/credentials)",
    "Read(~/.gnupg/**)",
    "Read(/home/*/.ssh/id_*)",
    "Read(/home/*/.ssh/*_rsa)",
    "Read(/home/*/.ssh/*_ed25519)",
    "Read(/Users/*/.ssh/id_*)",
    "Read(/Users/*/.ssh/*_rsa)",
    "Read(/Users/*/.ssh/*_ed25519)",
    "Read(/root/.ssh/id_*)",
    "Read(/root/.ssh/*_rsa)",
    "Read(/root/.ssh/*_ed25519)",
    "Read(/home/*/.aws/credentials)",
    "Read(/Users/*/.aws/credentials)",
    "Read(/root/.aws/credentials)",
    "Read(/home/*/.gnupg/**)",
    "Read(/Users/*/.gnupg/**)",
    "Read(/root/.gnupg/**)",

    "Bash(:(){ :|:& };:)",

    "Bash(git push --force * main)",
    "Bash(git push --force * master)",
    "Bash(git push -f * main)",
    "Bash(git push -f * master)",
    "Bash(git push --force-with-lease * main)",
    "Bash(git push --force-with-lease * master)"
  ]
}
```

> **literal-match の限界 (重要)**: Claude Code の deny パターンは送信される文字列に対し literal match される。 agent が `~` や `$HOME` を展開して絶対パス (`/home/user/...`) で送信した場合、 `~/...` や `$HOME*` パターンはマッチしない。 これが Bash 系 (`rm`, `sudo rm` 等) と Read 系 (`~/.ssh/...`) の両方で `/home/*` / `/root` / `/Users/*` 等の絶対パス variant を併記している理由。
>
> **Bash vs Read / Edit の重要な差**: §7 PreToolUse Hook は **Bash 限定** (`select(.tool_name=="Bash")` で他ツールを除外)。 **Read / Edit ツールには hook が走らない**ため、 機密ファイル保護は settings.json の deny パターン**だけ**が頼り。 上の絶対パス列挙はとりわけ重要。 列挙し切れない経路 (symlink、 bind mount、 OS 固有 home prefix、 NFS mount 等) は **§9 L0 隔離** (container / VM / user namespace) で物理的に隔てる以外にない。 Bash 系は §7 hook の意味的検知 (§2.3 / §9 L4) で別途カバーされる。

### 4.3 意図的に **deny に入れない** もの（ask に任せる）

生産性重視のため、以下は ask 止まり:

- `chmod -R 777` / `chown -R` — 取り返しがつく
- パッケージのアンインストール — 再インストールできる
- 単体サービスの停止（ssh以外） — 再起動できる
- ファイアウォール無効化 — 再有効化できる
- feature ブランチへの force push — リフログから復旧可
- `/etc` 配下の一般的な編集（sudoers/passwd/shadow 以外） — ask で承認させる

---

## 5. Tier 2: ASK（重要・影響あり）

### 5.1 デフォルト方針

書き込み系の操作と sudo を **ask** に置きたい — が、 **`Bash(sudo *)` のような broad パターンを §5.2 に書いてはならない**。 Claude Code の評価順 (deny → ask → allow, 各層内 first match) では broad な ask が §6.2 の specific allow より先にマッチしてしまい、 `sudo -n systemctl status myapp` のような読み取り系 allow が永遠に発火しない (settings.json だけでは「default ask, 特定だけ allow」を直接表現できない)。

したがって sudo のコンプリヘンシブな防御は次の層に分担する:

- **§7 PreToolUse Hook** — 意味的に危険な sudo コマンドを exit 2 で停止
- **Appendix B sudoers** — sudoers ホワイトリストで OS レベル拒否 (採用時のみ)

settings.json の ask には **具体的なサブコマンド** (`apt install *`, `systemctl restart *`, `mount *` 等) のみを書く。 これだけでも OWASP LLM06 の「自律性」軸を大幅に削れる。

### 5.2 ルール例（settings.json `permissions.ask`）

> **メモ**: §4.2 と同じく `permissions` キー配下に置く fragment。 単独で完全な settings として使うなら `{ "permissions": { "ask": [...] } }` でラップする。

```json
{
  "ask": [
    "Bash(apt install *)", "Bash(apt remove *)", "Bash(apt-get *)",
    "Bash(dnf *)", "Bash(yum *)", "Bash(brew install *)", "Bash(brew uninstall *)",
    "Bash(npm install -g *)", "Bash(pip install *)", "Bash(pip3 install *)",
    "Bash(cargo install *)", "Bash(gem install *)",

    "Bash(npm run *)", "Bash(npm test *)", "Bash(npm ci)",
    "Bash(yarn *)", "Bash(pnpm *)",

    "Bash(systemctl restart *)", "Bash(systemctl stop *)", "Bash(systemctl start *)",
    "Bash(systemctl enable *)", "Bash(systemctl disable *)",
    "Bash(service * *)",

    "Bash(crontab *)",
    "Bash(mount *)", "Bash(umount *)",

    "Bash(chmod -R *)", "Bash(chown -R *)",
    "Bash(ufw *)", "Bash(iptables *)", "Bash(nft *)",

    "Bash(git push *)",
    "Bash(git reset --hard *)",
    "Bash(git clean -fd*)",

    "WebFetch",
    "Edit(/etc/**)",
    "Edit(~/.bashrc)", "Edit(~/.zshrc)", "Edit(~/.profile)"
  ]
}
```

`Bash(sudo *)` / `Bash(sudo -n *)` は **意図的に入れていない** (§5.1 参照)。 sudo 全般のカバレッジは §7 hook + Appendix B sudoers に委ねる。

### 5.3 ask が出たときの人間側のチェックリスト

1. このコマンドは**今のタスクと関係あるか？**（無関係なら prompt injection を疑う）
2. **冪等か？ 失敗しても安全か？**（ある程度 yes なら通す）
3. **下流の状態を変えるか？**（パッケージ追加/サービス変更は慎重に）
4. **取り消し方法は明確か？**（不明なら一旦 reject して聞き返す）

---

## 6. Tier 3: ALLOW（自動許可）

### 6.1 自動許可される built-in 読み取り系（明示不要）

Claude Code は次を built-in で読み取り扱いし、ルールなしで自動実行する:
`ls, cat, echo, pwd, head, tail, grep, find, wc, which, diff, stat, du, cd`, read-only な `git`。

### 6.2 明示で追加したい読み取り系（settings.json `permissions.allow`）

`sudo -n` 付きの読み取り系を allow に明示する。 §5.2 で broad な `Bash(sudo *)` を ask に**置かない** (§5.1 参照) ため、 下記の specific allow が評価順 (deny → ask → allow) 上 fire できる。 **以下の `sudo -n ...` 行は Appendix B (sudoers ホワイトリスト) を採用したケース限定**。§13 経路 (agent に sudo を渡さない) では不要かつ無効。

> **package-manager script を allow しない理由 (v2)**: `npm run *` / `yarn *` / `pnpm *` 系は `package.json` の任意スクリプトを実行でき、 そこから sudo / 破壊操作 / ネットワーク exfil に到達するバイパス経路になる。 Claude Code は top-level Bash しか評価しないため、 script 内部は素通り。 これらは §5.2 ask に移してある。 信頼できる固定スクリプト名 (例: `npm run lint`, `npm run typecheck`) のみ allow に置きたい場合は project ごとに narrowly 列挙すること (例: `Bash(npm run lint)`, `Bash(npm run typecheck)`)。 同様の risk が `cargo test` / `go test` / `pytest` にもあるが、 テストコード経由の攻撃面は npm scripts ほど顕在化していないため `allow` に残置。 untrusted リポジトリで作業する場合は hook 側でテスト起動を blockable にすることを検討。

> **メモ**: §4.2 と同じく `permissions` キー配下に置く fragment。 単独で完全な settings として使うなら `{ "permissions": { "allow": [...] } }` でラップする。

```json
{
  "allow": [
    "Bash(sudo -n systemctl status *)",
    "Bash(sudo -n journalctl *)",
    "Bash(sudo -n ss -tlnp)",
    "Bash(sudo -n netstat *)",
    "Bash(sudo -n cat /var/log/*)",
    "Bash(sudo -n tail /var/log/*)",
    "Bash(sudo -n ls /var/log/*)",
    "Bash(sudo -n lsof *)",
    "Bash(sudo -n ps *)",

    "Bash(python -m pytest *)", "Bash(pytest *)",
    "Bash(cargo test *)", "Bash(cargo build *)",
    "Bash(go test *)", "Bash(go build *)",

    "Bash(git status)", "Bash(git diff *)", "Bash(git log *)",
    "Bash(git branch *)", "Bash(git fetch *)",
    "Bash(git commit *)", "Bash(git add *)"
  ]
}
```

---

## 7. 補助層: PreToolUse Hook

### 7.1 なぜ必要か

§2.3 で述べたとおりパターン制約は脆い。Hook は **exit code 2 で完全ブロック**でき、`bypassPermissions` モードでも動作する（ただし deny ルール自体は hook より優先）。

### 7.2 Hook の責務（やること）

- Bash コマンドを **正規化**してから危険パターン照合（変数展開、`$()`、バッククォート、`&&`/`||`/`;`/`|` 連結を分解）
- パターンが匿名化されても残る**意味的な危険性**を検知（例: `rm -r` + ルート/ホーム指向、`dd of=/dev/sd`, `mkfs.*`）
- 失敗時は stderr に**明確なブロック理由**を出力（ユーザーが理由を理解できるように）

### 7.3 Hook が **やらない** こと

- 通常の許可判断（それは settings.json の責務）
- 認証情報のスキャン（別途 DLP 層で）
- LLMの意図解釈（複雑なロジックを hook に入れない。デバッグ不能になる）

### 7.4 設計サンプル（実装は別途）

```bash
#!/usr/bin/env bash
# scripts/hooks/pretool-bash-guard.sh
# 責務: 真に破滅的なコマンドを意味解析で止める（パターン deny の補完）
# 設計: fail-closed (依存欠落・入力不正・内部エラーは exit 2 で block)

set -o pipefail

input=$(cat)

# === 依存チェック (fail-closed) ===
if ! command -v jq >/dev/null 2>&1; then
  echo "GUARDRAIL ERROR: jq not installed — blocking by default" >&2
  exit 2
fi

# === JSON parse (失敗時 block) ===
tool_name=$(printf '%s\n' "$input" | jq -r '.tool_name // empty' 2>/dev/null)
if [ -z "$tool_name" ]; then
  echo "GUARDRAIL ERROR: invalid hook input JSON — blocking by default" >&2
  exit 2
fi

# Bash 以外は対象外 (Read/Edit 等は settings.json deny に委ねる、 §4.2 参照)
[ "$tool_name" != "Bash" ] && exit 0

cmd=$(printf '%s\n' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$cmd" ] && exit 0

# === 正規化: 変数 / $() / バッククォート / クォートを剥がす ===
normalized=$(printf '%s\n' "$cmd" \
  | sed -E 's/\$\{?[A-Za-z_][A-Za-z0-9_]*\}?/X/g' \
  | sed -E 's/\$\([^)]*\)/X/g' \
  | tr -d '`"\047')

# === 分割前に評価する検査 ===
# 注: `:(){ :|:& };:` のような fork bomb は & | ; を含むので、
#     分割後に regex すると fragment 化されてマッチしない。
#     分割前の cmd 全体に対して照合する。
if printf '%s\n' "$normalized" | grep -qE '[A-Za-z_:]+\(\)\s*\{[^}]*\|[^}]*&[^}]*\}'; then
  echo "GUARDRAIL BLOCK: fork bomb-like recursive function: $cmd" >&2
  exit 2
fi

# === 連結境界で分割して各サブコマンドを評価 ===
# 注: パイプライン `... | while` は while をサブシェルで実行するため、
#     ループ内の `exit 2` がサブシェルだけを抜けて hook 全体が exit 0 で
#     続いてしまう (危険コマンドが silently 通る)。
#     プロセス置換 `done < <(...)` で while をメインシェルに留める。
while IFS= read -r sub; do
  sub=$(printf '%s\n' "$sub" | xargs)  # trim
  [ -z "$sub" ] && continue

  # === rm 系の 3 段階チェック ===
  # 1) コマンドが (sudo) rm で始まる
  # 2) かつ recursive/force 系 flag をどこかに含む (short / long / 分離 / 結合 すべて対応)
  # 3) かつ 危険 target (/, ~, /*, X) を引数にもつ
  # 注: $HOME 等は上の正規化で X に置換済み。 X を「未知変数 = 危険」として扱う
  if printf '%s\n' "$sub" | grep -qE '^(sudo +)?rm( |$)'; then
    if printf '%s\n' "$sub" | grep -qE '(^| )(-[a-zA-Z]*[rRf][a-zA-Z]*|--recursive|--force|--no-preserve-root)( |$)'; then
      if printf '%s\n' "$sub" | grep -qE ' (/|~|/\*|X)(/| |$)'; then
        echo "GUARDRAIL BLOCK: rm with recursive/force flag targeting root/home: $sub" >&2; exit 2
      fi
    fi
  fi

  if printf '%s\n' "$sub" | grep -qE 'dd .*of=/dev/(sd|nvme|hd|mmcblk)'; then
    echo "GUARDRAIL BLOCK: block device write: $sub" >&2; exit 2
  fi
  if printf '%s\n' "$sub" | grep -qE '(sudo +)?(mkfs\.|wipefs|shred +/dev/)'; then
    echo "GUARDRAIL BLOCK: disk wipe: $sub" >&2; exit 2
  fi
done < <(printf '%s\n' "$normalized" | tr '&|;' '\n')

exit 0
```

> **注: 本サンプルは説明用。production 実装では次の改良が必須**:
> - **fail-closed 設計**: 上記サンプル通り、 jq 不在 / 入力 JSON 不正 / 内部エラー時は **exit 2 (block)** で停止する。 silently exit 0 (= allow) は security hook として致命的
> - **変数正規化との整合**: `$HOME` 等を事前に `X` へ正規化し、 検知側は `\$HOME` リテラルではなく `X` を「未知変数 = 危険」として扱う
> - **クォートを尊重した分割**: `tr '&|;' '\n'` は単純すぎ、クォート内のセミコロンや here-doc も分割してしまう。 production では `bash -n` で構文検証、 `shfmt -tojson` や [mvdan/sh](https://github.com/mvdan/sh) (Go) で AST 解析、 または専用 shell lexer を使う
> - **fork bomb は分割前に評価**: `&` / `|` / `;` を含む fork bomb payload (`:(){ :|:& };:` 等) は分割後だと fragment 化されて regex に当たらないため、 上記サンプルでは分割前の `$normalized` 全体で照合している。 ただし任意の関数名 / 難読化に対しては best-effort 止まり。 **真の防御は OS 側の `ulimit -u <max-procs>` や cgroups (`pids.max`) によるプロセス数制限**。 hook 検知は補助層に留める
> - **rm 長 option 対応**: 上記の 3 段階チェックは `-r -f` (分離), `--recursive --force` (long), `-rf --no-preserve-root` も捕捉する。 ただし `rm -rf -- /` のような `--` end-of-options や、 echo/eval 経由の難読化には弱い。 不明な rm 形は **fail closed** にするのが production 推奨
> - 危険 / 良性両方のコーパスで unit test を伴う

---

## 8. 補助層: sudoers (v1 主軸。v2 では条件付き fallback)

v1 ではこの章が本書の中核だった。**v2 では §13「Agent に sudo を与えない」が第一推奨**に転換。sudoers ベース設計の詳細は **Appendix B** に退避した。

Appendix B (sudoers ホワイトリスト) を採用するのは次のケースに限る:

- 無人 CI runner / 自動デプロイ等で人間 in-the-loop が物理的に取れない
- single-purpose appliance で操作対象がほぼ固定
- §13 のいずれの recipe も組織制約で採用不可

それ以外は §13 を採用すること。

---

## 9. 多層防御の全体像

| 層 | 防御対象 | 実装 | 検出時の挙動 |
|---|---|---|---|
| **L0: 隔離** | 全層が破られた場合の被害局所化 | Container / VM / devcontainer (§13 R3) | プロセス分離 |
| **L1: Anthropic Sandbox** | Bash 子プロセスの FS/network (Anthropic 公式) | `.claude/settings.json` の sandbox 設定 (§13 R1) | カーネルが拒否 |
| **L2: 非 sudo 権限委譲** | sudo 経路自体を消す | group membership (§13 R2) | OS が拒否 |
| **L3: sudoers** (Appendix B 採用時のみ) | Claude Code を経由しない攻撃 | `/etc/sudoers.d/claude-agent` | OS が拒否 |
| **L4: PreToolUse hook** | 意味的に危険なコマンド | `scripts/hooks/pretool-bash-guard.sh` | exit 2 で停止 |
| **L5: permissions.deny** | 明確にパターン化できる禁止操作 | `.claude/settings.json` | ルールで拒否 |
| **L6: permissions.ask** | 影響大の操作 | `.claude/settings.json` | 人間承認待ち |
| **L7: 監査** | 事後検出・学習 | shell history + auditd + Claude セッションログ | アラート |

**重要 (v2 更新)**: L4 〜 L6 は LLM 経由でのみ効く。L0 〜 L3 は経由を問わず効く。本気で守るなら **L0 + L1 + L2 が主**、L3 (sudoers) は §13 経路が取れない場合のみ。L4 〜 L6 は UX 改善層。

> **L 表記と R 表記の使い分け (v2 注記)**: 本章 §9 の **L0-L7** は「防御層 (Defense Layer)」の番号。 §13.2 の **R1-R4** は「推奨レシピ (Recipe)」の番号で別名前空間。 §9 表内の `(§13 R3)` 等の cross-ref は「§13 で言うところの recipe R3 がこの層に対応する」の意。 マッピング: R1 ≈ L1, R2 ≈ L2, R3 ≈ L0 の subset, R4 は §9 の防御層には属さない (運用層)。

---

## 10. 運用ガイド

### 10.1 導入順序（v2 推奨）

0. **段階0**: 既存環境を測定（どんなコマンドが発行されているか1週間ログ取得）
1. **段階1 — §13 経路の評価**: agent に sudo を渡さずに済むか棚卸し。R1 (Anthropic sandbox) / R2 (group) / R3 (devcontainer) でどこまでカバーできるか判定
2. **段階2A（推奨）**: §13 経路でカバーできる → R1 を有効化、必要に応じて R2 (group 追加) と R3 (devcontainer) を整備。§§4-7 (deny/ask/allow/hook) は §13 経路でも引き続き適用
3. **段階2B（fallback）**: §13 経路でカバーできない真の特権操作が残る → **Appendix B** (sudoers ホワイトリスト) を採用。§§4-7 と組み合わせる
4. **段階3**: 1〜2 週間運用して摩擦と漏れを確認
5. **段階4**: 漏れに応じて R1 sandbox 範囲を縮小、ask ルール調整、hook 強化

(v1 の sudoers-first 順序は §13 検証を経て廃止)

### 10.2 NG パターン

- ❌ `--dangerously-skip-permissions` を常用する（root/sudo 配下では Anthropic が物理的に blocked: [Issue #9184](https://github.com/anthropics/claude-code/issues/9184)）
- ❌ **§13 経路を検証せずいきなり Appendix B (sudoers) を採用する**（v1 主軸だが v2 では fallback）
- ❌ deny を肥大化させる（ask で十分なものまで deny にして摩擦を生む）
- ❌ `NOPASSWD: ALL` を sudoers に書く
- ❌ パターン deny だけに頼り hook を省く（[The Register 2026-04 の bypass 事例](https://www.theregister.com/2026/04/01/claude_code_rule_cap_raises/)）
- ❌ コンテナの中で root として動かす（隔離の意味が半減 — ただし devcontainer 内 root は host 隔離前提なら可）
- ❌ `Bash(sudo *)` のような broad パターンを ask に置く（§6.2 の specific sudo -n allow を mask する。 §5.1 参照）

### 10.3 監査ログのチェックポイント

- ask に対する人間の承認率（高すぎる = ask が広すぎる、低すぎる = エージェントが暴れすぎ）
- deny / hook ブロックの発生（あったら必ず原因調査）
- sudoers 外コマンドの試行（プロンプトインジェクション兆候）

---

## 11. 参考文献

### LLM / AI Agent セキュリティ

- [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) — 3軸最小化と Complete Mediation の元ネタ
- [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) — 包括的なチェックリスト
- [AWS Well-Architected GENSEC05-BP01: Least privilege for agentic workflows](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/gensec05-bp01.html) — IAM 観点の最小権限
- [Oso — Best Practices of Authorizing AI Agents](https://www.osohq.com/learn/best-practices-of-authorizing-ai-agents) — 認可モデル設計
- [BeyondTrust — AI Agent Identity Governance and Least Privilege](https://www.beyondtrust.com/blog/entry/ai-agent-identity-governance-least-privilege) — エージェント独立アイデンティティ
- [IBM — AI Agent Security Best Practices and Tutorial](https://www.ibm.com/think/tutorials/ai-agent-security)
- [MintMCP — AI agent security: the complete enterprise guide for 2026](https://www.mintmcp.com/blog/ai-agent-security)

### Claude Code 仕様

- [Claude Code — Configure permissions](https://code.claude.com/docs/en/permissions) — allow/ask/deny の精密仕様、パターンの脆弱性警告
- [Claude Code — Hooks guide](https://code.claude.com/docs/en/hooks-guide) — PreToolUse hook の API
- [Claude Code — Sandboxing](https://code.claude.com/docs/en/sandboxing) — OS レベル隔離

### Linux 特権設計

- `sudoers(5)` man page — sudoers のセマンティクス
- `auditd(8)` — 特権操作の監査ログ

### v2 (2026-05-16) で追加した一次資料

- [Anthropic Claude Code Issue #9184 (2025-10-08, closed)](https://github.com/anthropics/claude-code/issues/9184) — `--dangerously-skip-permissions cannot be used with root/sudo privileges for security reasons`。Anthropic 公式が「agent-as-root は破滅的失敗モード」と物理的に blocked。本書の v2 方針転換の最大根拠
- [The Register 2026-04-01 — "Claude Code bypasses safety rule if given too many commands"](https://www.theregister.com/2026/04/01/claude_code_rule_cap_raises/) — Adversa 発見の `MAX_SUBCOMMANDS_FOR_SECURITY_CHECK = 50` bypass。v2.1.90 で patched。「pattern deny だけに依存できない」原則の実証
- [Infralovers Blog 2026-02-15 — "Sandboxing Claude Code on macOS: What I Actually Found"](https://www.infralovers.com/blog/2026-02-15-sandboxing-claude-code-macos/) — sandbox 有効化で permission prompt 約 **84% 減** (Anthropic internal 計測の出典として引用)。macOS `sandbox-exec` の deprecation 状況にも言及

---

## 12. 改訂履歴

| 日付 | 変更 |
|---|---|
| 2026-05-13 | 初版（緩め deny + 広め ask 方針） |
| 2026-05-16 | **v2 方針転換**: 「agent に sudo を渡さない」を §13 で主軸化。v1 の sudoers 詳細 (旧 §8) を Appendix B に退避。§2.3 に Adversa bypass 事例、§11 に Anthropic Issue #9184 等の一次資料を追加。§9 / §10.1 / §10.2 を v2 順序に更新。 |
| 2026-05-16 (rev2) | レビュー指摘対応: §9 防御層を L0-L7 に正規化 (L1a/b/c と L2 gap を解消)、§13 推奨レシピを **R1-R4** 別名前空間にリネーム。§5.1 / §5.2 / §6.2 を Claude Code 評価順 (deny→ask→allow first match) に整合させ、broad `Bash(sudo *)` ask を削除し sudo カバレッジを §7 hook と Appendix B に明示委譲。§13.2 R2 group の docker 警告強化、R3 devcontainer の隔離前提を列挙、Appendix B.3 から `!ALL` catch-all 削除、§7.4 hook のサブシェル exit バグ修正、§11 OWASP URL 訂正。 |

---

## 13. v2 推奨: Agent に sudo を与えない

v1 (§§3-8) は「sudoers でホワイトリスト渡し」を中核としていたが、検証 (§11 v2 一次資料 3 件) の結果、Anthropic 公式の方向性と整合しないため v2 で方針転換した。

### 13.1 なぜ sudo を渡さないか

3つの直接的な根拠が揃った:

- **Anthropic 公式が明示的に root/sudo 起動を blocked** ([Issue #9184](https://github.com/anthropics/claude-code/issues/9184), closed as intended, 2025-10-08): `--dangerously-skip-permissions` は root/sudo 配下では実行不可。これは Anthropic 自身が「agent-as-root は破滅的失敗モード」と判断した公式表明
- **deny ルールは pattern bypass される実例あり** ([The Register 2026-04-01](https://www.theregister.com/2026/04/01/claude_code_rule_cap_raises/)): `MAX_SUBCOMMANDS_FOR_SECURITY_CHECK = 50` を超える subcommand chain で自動セキュリティチェックが skip され ask フォールバックに落ちる脆弱性が Adversa により発見・公表。v2.1.90 で patched 済みだが、「pattern deny だけに依存できない」原則の実証材料
- **Sandbox の UX 影響は許容範囲** ([Anthropic 2026, via Infralovers](https://www.infralovers.com/blog/2026-02-15-sandboxing-claude-code-macos/)): Anthropic 自身の internal usage 計測で sandboxing 有効化により permission prompt が約 **84% 減少**。「sandbox は煩わしい」は思い込み

**結論**: OS の root 権限を agent に渡すより、**agent の必要な能力を OS の非特権機構で肩代わりさせる方が安全かつ低摩擦**。

### 13.2 4-layer 推奨レシピ

> **記法**: 本節の **R1-R4** は「推奨レシピ (Recipe)」の番号。 §9 の防御層番号 (L0-L7) とは別名前空間 (§9 末尾注記参照)。

| Recipe | 何を | 何で | カバーする操作 |
|---|---|---|---|
| **R1** | Anthropic native sandbox を有効化 | `.claude/settings.json` の sandbox 設定 | filesystem write / network egress を allowlist 化 |
| **R2** | group membership で sudo を回避 | `usermod -aG systemd-journal claude-agent` 等 (危険 group は避ける、 §13.2 R2 参照) | journalctl, log 読み取り、 メディアデバイス 等 |
| **R3** | devcontainer で system mutation を局所化 | `.devcontainer/devcontainer.json` | apt install, systemctl restart 等を container 内に閉じる |
| **R4** | 人間 delegate | Slack / CLI 経由で「これやって」プロンプト | 上記でカバーできない真の特権操作 |

#### R1: Anthropic native sandbox

最初に有効化すべき層。`.claude/settings.json` の `sandbox` 設定で filesystem 範囲と network egress を制限する。**84% prompt 削減効果の根源**。

macOS では `sandbox-exec` (Apple は deprecated 化しているが現状動作。[Infralovers 2026-02 が指摘](https://www.infralovers.com/blog/2026-02-15-sandboxing-claude-code-macos/))、Linux では seccomp / landlock。詳細は [Claude Code Sandboxing docs](https://code.claude.com/docs/en/sandboxing) 参照。

> **注意**: macOS の `sandbox-exec` deprecation は長期的リスク。Production 用途では Linux + devcontainer (R3) を併用するのが安全側。

#### R2: group membership (ただし group 選びに注意)

sudo を使わず、特定リソースへの直接アクセス権を group 経由で agent に付与する。 ただし **group の中には実質的に host root と等価の権限を与えるものがある**ため、 「sudoers より安全」と単純には言えない。 採用する group を**個別に評価**すること。

**安全な group の例** (host root に escalate できない):

- `systemd-journal` — `journalctl` 読み取り
- `audio` / `video` — メディアデバイス
- service-account group (例: `nginx`, `myapp`) — そのサービスの log / config 読み取り

**危険な group** (事実上 host root と等価。 これらに入れるなら sudoers NOPASSWD: ALL と同等のリスクと扱うこと):

- **`docker`** — `docker run --privileged -v /:/host` で host filesystem を完全制御できる
- `kvm` — VM 経由で host メモリにアクセス可
- `disk` — block device 直接読み書きで filesystem 全域改竄可
- `lxd` / `wheel` — それぞれ container escape / sudo 経路

```bash
# 例: 安全な group のみ追加 (systemd-journal で journalctl 読み取りを許可)
sudo usermod -aG systemd-journal claude-agent

# 注意: docker group は host root と等価。 Docker を使わせたい場合は
#       rootless docker または Podman を検討し、 素の docker group には入れない
```

これにより以下が sudo 不要になる (安全 group 経由):
- `journalctl -u <unit>` (systemd-journal group)
- `cat /var/log/<unit>.log` (適切な ACL / group 設定下)

評価軸: **「その group 経由で host root に escalate できる経路があるか」** をチェックする。 「group は sudo より安全」ではなく「**正しい group を選べば** sudo より低リスク」が正確な表現。

#### R3: devcontainer

`apt install`、`systemctl restart` のような「system 状態を変える」操作は、agent ホストではなく **使い捨て可能な devcontainer 内**で実行する。container を捨てれば変更も消える。

```jsonc
// .devcontainer/devcontainer.json (抜粋) — DinD 等の privileged feature は使わない baseline
{
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "remoteUser": "vscode",
  "postCreateCommand": "sudo apt-get update && sudo apt-get install -y <pkgs>"
}
```

> **DinD についての注意**: 素の `docker-in-docker` devcontainer feature は内部で **`--privileged` を必要とする** ため、 下記の隔離前提と矛盾する。 container 内で Docker が必要な場合は **rootless Podman** (`podman` パッケージを直接 apt install して utilize) や **host docker socket を共有しない別構成** を別途検討すること。 「DinD feature を入れただけで安全」 という前提で扱わない。

container 内では agent に `NOPASSWD: ALL` を渡しても **ホスト本体への影響は限定的** — ただし以下の隔離前提が**すべて**成立する場合のみ:

- `--privileged` フラグは使わない
- host filesystem の bind mount は最小限 (workspace のみ。 `/`、 `/var/run/docker.sock`、 `/proc`、 `/sys` 等の bind mount は **NG**)
- docker-in-docker は **ホスト docker.sock 共有方式ではなく nested daemon 方式**で構築する (上記 `docker-in-docker:2` feature は nested daemon 側で安全。 socket mount 式 DinD は host docker access に等価で **NG**)
- host capabilities の追加 (`--cap-add SYS_ADMIN` 等) はしない
- 可能なら user namespace remapping を有効化 (container root != host root)

これらが満たされない container は **隔離されておらず、 container 内 root は事実上 host root と等価**。 隔離前提が成立するときに限り「container × root」が許される (§10.2 NG パターン参照)。

#### R4: 人間 delegate

R1-R3 でカバーできない真の host 特権操作 (hardware 操作、L0 物理アクセス、組織ポリシーで sudo が要る操作) は agent に渡さず、**人間に Slack / CLI 経由で頼む形式**にする。

```
エージェント: 「以下のコマンドを host で実行してください: sudo systemctl restart nginx」
人間:        (確認後) 実行 → 結果を agent に貼り戻す
```

非効率に見えるが、R4 まで到達するケース自体が少なければ問題にならない。**R1-R3 で 90% 以上カバーできるのが推奨ライン**。

### 13.3 レシピ選択ガイド

| 状況 | 推奨 |
|---|---|
| 個人開発機 (1-3 台) | R1 + R3 を主、R4 を補助。R2 はオプション。**Appendix B 不要** |
| 開発チーム共有サーバー | R1 + R2 + R3。R4 を運用ルール化 |
| 無人 CI runner | R1 + R3。R4 不可なので残りは **Appendix B (sudoers ホワイトリスト) を fallback** |
| Production deploy server | **Appendix B 必須**。加えて R1 で sandbox 最小化 |

---

## Appendix B: sudoers ベース設計 (sudo がどうしても必要な場合)

§13 のいずれの recipe でも sudo を完全には避けられないケースに限って採用する fallback 設計。
**v1 ではこの内容が本書の中核 (旧 §8) だった**。v2 では条件付き fallback に降格。

採用条件 (§10.1 段階2B):
- 無人 CI runner / 自動デプロイ等で R4 (人間 delegate) が物理的に取れない
- single-purpose appliance で操作対象がほぼ固定
- §13 のいずれの recipe も組織制約で採用不可

### B.1 なぜ sudoers が必要か (旧 §8.1)

settings.json と hook は **Claude Code のプロセス内の防御**。Claude Code を経由しない攻撃 (プロンプトインジェクション経由で別シェルを起動など) に対しては OS レベルの sudoers が最後の砦。

ただし §13 経路 (sandbox + group + devcontainer) が取れるなら、そもそも sudo 経路自体を持たないため Claude Code 経由かどうかを問わず sudo は使えない。これが v2 で sudoers が「最強」から「条件付き fallback」に降格した理由。

### B.2 設計方針 (旧 §8.2)

- エージェント専用ユーザー `claude-agent` を作成
- `claude-agent` の sudoers は **読み取り系のみ NOPASSWD**、書き込み系は **コマンド単位ホワイトリスト**
- ワイルドカード (`*`) は sudoers では極力使わない (引数迂回のリスク)

### B.3 サンプル: `/etc/sudoers.d/claude-agent` (旧 §8.3)

```sudoers
# 読み取り系: パスワードなしで許可 (引数まで完全固定。 wildcard も bare コマンドも使わない)
claude-agent ALL=(root) NOPASSWD: \
    /bin/systemctl status myapp, \
    /bin/systemctl status nginx, \
    /bin/journalctl -u myapp, \
    /bin/journalctl -u nginx, \
    /bin/journalctl -u myapp -n 100, \
    /bin/journalctl -u nginx -n 100, \
    /usr/bin/ss -tlnp, \
    /usr/bin/lsof, \
    /bin/cat /var/log/myapp.log, \
    /bin/cat /var/log/nginx/access.log, \
    /usr/bin/tail /var/log/myapp.log, \
    /usr/bin/tail /var/log/nginx/access.log

# 書き込み系: パスワード要求（人間の関与を強制）
claude-agent ALL=(root) PASSWD: \
    /bin/systemctl restart myapp, \
    /bin/systemctl reload nginx
```

### B.4 注意点 (旧 §8.4)

- `NOPASSWD` は読み取り系**のみ**。書き込み系で NOPASSWD すると LLM が無人で破壊操作を打てる
- **コマンドを引数リストなしで列挙すると sudoers は任意引数を許可する**: 例: `/bin/journalctl,` (引数なし) は `journalctl --vacuum-time=1s` のような mutate 系も通してしまう。 read-only を意図するなら **引数まで完全固定** (`/bin/journalctl -u myapp` のように unit / option 単位で列挙) するか、 引数なしを意図するなら明示的に `""` 空引数リストを書く (例: `/bin/journalctl ""`)。 B.3 サンプルは全て引数固定で書いてある
- **ワイルドカード `*` は sudoers では `/` もマッチする**ため path traversal を許容する。 例: `/bin/cat /var/log/*.log` は `/var/log/../../etc/shadow.log` 形式の引数でもマッチし、結果として `/etc/shadow.log` (任意位置の `.log` ファイル) を root として読み取りに行ける。 **フルパス + 固定引数** (例: `/bin/cat /var/log/myapp.log` のように unit 名で具体列挙) を推奨。 やむを得ず `*` を使う必要がある場合は、 **constrained wrapper script** を作って sudoers にはそれだけを登録する (wrapper 内で `realpath` を取り、 `..` や symlink を検査し、 unsafe なら exit 1)。 hook 側 (§7) の canonicalization は **Claude Code 経由のコマンドにしか効かない**ため、 別シェル / 別プロセスから sudo が呼ばれる経路には無効 — sudoers fallback の OS-level 防御目的には合わない
- `Defaults:claude-agent !env_reset, env_keep += "..."` のような env 緩和は **しない**
- **catch-all deny `claude-agent ALL=(ALL) !ALL` は書かない**: sudoers は未列挙コマンドを既定で deny する。 末尾の `!ALL` は評価順 (last-match-wins) で先行する NOPASSWD/PASSWD allow をすべて上書きしてしまい、 列挙したホワイトリストごと無効化される

### B.5 §13 経路への移行 (v2 追加)

状況が変わって §13 の R1-R4 いずれかが採用可能になったら、**Appendix B 経路は速やかに retire する**。sudoers が残るほど bypass の機会が増える (§2.3 の Adversa 事例参照)。

retire 手順:
1. §13 R1 (sandbox) を先行有効化
2. §13 R2 (group) で sudo 経由していた読み取り系を group 経由に移行
3. §13 R3 (devcontainer) で残った書き込み系を container 内に閉じ込め
4. `/etc/sudoers.d/claude-agent` を削除
5. §§4-7 の deny / ask / allow / hook は引き続き有効
