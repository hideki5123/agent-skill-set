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

> **literal-match の限界**: Claude Code の deny パターンは送信されるコマンド文字列に対し literal match される。 agent が `$HOME` を展開して `/home/user/...` の形で送信した場合、 `$HOME*` パターンはマッチしない。 これが上で `/home/*` / `/root` / `/Users/*` 等の絶対パス variant を併記している理由。 ただし全ての変数展開・エイリアス・シンボリックリンクを列挙するのは不可能なので、 **意味的検知は §7 PreToolUse Hook の責務** (§2.3 / §9 L3 参照)。

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

**「sudo を含むすべての書き込み系」は ask** が出発点。これだけで OWASP LLM06 の「自律性」軸を大幅に削れる。

### 5.2 ルール例（settings.json `permissions.ask`）

```json
{
  "ask": [
    "Bash(sudo *)",
    "Bash(sudo -n *)",

    "Bash(apt install *)", "Bash(apt remove *)", "Bash(apt-get *)",
    "Bash(dnf *)", "Bash(yum *)", "Bash(brew install *)", "Bash(brew uninstall *)",
    "Bash(npm install -g *)", "Bash(pip install *)", "Bash(pip3 install *)",
    "Bash(cargo install *)", "Bash(gem install *)",

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

`sudo -n` 付きの読み取り系は明示しないと ask に落ちる。**以下の `sudo -n ...` 行は Appendix B (sudoers ホワイトリスト) を採用したケース限定**。§13 経路 (agent に sudo を渡さない) では不要かつ無効。

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

    "Bash(npm run *)", "Bash(npm test *)", "Bash(npm ci)",
    "Bash(yarn *)", "Bash(pnpm *)",
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

input=$(cat)
cmd=$(echo "$input" | jq -r 'select(.tool_name=="Bash") | .tool_input.command // empty')
[ -z "$cmd" ] && exit 0

# 正規化: 変数 / $() / バッククォート / クォートを剥がす
normalized=$(echo "$cmd" \
  | sed -E 's/\$\{?[A-Za-z_][A-Za-z0-9_]*\}?/X/g' \
  | sed -E 's/\$\([^)]*\)/X/g' \
  | tr -d '`"\047')

# 連結境界で分割
echo "$normalized" | tr '&|;' '\n' | while IFS= read -r sub; do
  sub=$(echo "$sub" | xargs)  # trim
  [ -z "$sub" ] && continue

  # 真に破滅的なパターン群
  # 注: $HOME 等は上の正規化で X に置換済み。 X を「未知の変数 = 危険」として扱う
  if echo "$sub" | grep -qE '^(sudo +)?rm +(-[a-zA-Z]*[rRf][a-zA-Z]*) +(/|~|/\*|X)(/| |$)'; then
    echo "GUARDRAIL BLOCK: filesystem root/home destruction: $sub" >&2; exit 2
  fi
  if echo "$sub" | grep -qE 'dd .*of=/dev/(sd|nvme|hd|mmcblk)'; then
    echo "GUARDRAIL BLOCK: block device write: $sub" >&2; exit 2
  fi
  if echo "$sub" | grep -qE '(sudo +)?(mkfs\.|wipefs|shred +/dev/)'; then
    echo "GUARDRAIL BLOCK: disk wipe: $sub" >&2; exit 2
  fi
  if echo "$sub" | grep -qE ':\(\)\s*\{\s*:\s*\|\s*:'; then
    echo "GUARDRAIL BLOCK: fork bomb: $sub" >&2; exit 2
  fi
done

exit 0
```

> **注: 本サンプルは説明用。production 実装では次の改良が必須**:
> - **変数正規化との整合**: 上記では `$HOME` 等を事前に `X` へ正規化するので、検知側は `\$HOME` リテラルではなく `X` を「未知変数 = 危険」として扱う (上記 `rm` 正規表現参照)
> - **クォートを尊重した分割**: `tr '&|;' '\n'` は単純すぎ、クォート内のセミコロンや here-doc も分割してしまう。production では `bash --noexec --parse`、`shellcheck` の AST、または専用 shell lexer を使う
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
| **L0: 隔離** | 全層が破られた場合の被害局所化 | Container / VM / devcontainer (§13 L3) | プロセス分離 |
| **L1a: Anthropic Sandbox** | Bash 子プロセスの FS/network (Anthropic 公式) | `.claude/settings.json` の sandbox 設定 (§13 L1) | カーネルが拒否 |
| **L1b: 非 sudo 権限委譲** | sudo 経路自体を消す | group membership (§13 L2) | OS が拒否 |
| **L1c: sudoers** (Appendix B 採用時のみ) | Claude Code を経由しない攻撃 | `/etc/sudoers.d/claude-agent` | OS が拒否 |
| **L3: PreToolUse hook** | 意味的に危険なコマンド | `scripts/hooks/pretool-bash-guard.sh` | exit 2 で停止 |
| **L4: permissions.deny** | 明確にパターン化できる禁止操作 | `.claude/settings.json` | ルールで拒否 |
| **L5: permissions.ask** | 影響大の操作 | `.claude/settings.json` | 人間承認待ち |
| **L6: 監査** | 事後検出・学習 | shell history + auditd + Claude セッションログ | アラート |

**重要 (v2 更新)**: L3 〜 L5 は LLM 経由でのみ効く。L0 〜 L1c は経由を問わず効く。本気で守るなら **L0 + L1a + L1b が主**、L1c (sudoers) は §13 経路が取れない場合のみ。L3 〜 L5 は UX 改善層。

---

## 10. 運用ガイド

### 10.1 導入順序（v2 推奨）

0. **段階0**: 既存環境を測定（どんなコマンドが発行されているか1週間ログ取得）
1. **段階1 — §13 経路の評価**: agent に sudo を渡さずに済むか棚卸し。L1 (Anthropic sandbox) / L2 (group) / L3 (devcontainer) でどこまでカバーできるか判定
2. **段階2A（推奨）**: §13 経路でカバーできる → L1 を有効化、必要に応じて L2 (group 追加) と L3 (devcontainer) を整備。§§4-7 (deny/ask/allow/hook) は §13 経路でも引き続き適用
3. **段階2B（fallback）**: §13 経路でカバーできない真の特権操作が残る → **Appendix B** (sudoers ホワイトリスト) を採用。§§4-7 と組み合わせる
4. **段階3**: 1〜2 週間運用して摩擦と漏れを確認
5. **段階4**: 漏れに応じて L1 sandbox 範囲を縮小、ask ルール調整、hook 強化

(v1 の sudoers-first 順序は §13 検証を経て廃止)

### 10.2 NG パターン

- ❌ `--dangerously-skip-permissions` を常用する（root/sudo 配下では Anthropic が物理的に blocked: [Issue #9184](https://github.com/anthropics/claude-code/issues/9184)）
- ❌ **§13 経路を検証せずいきなり Appendix B (sudoers) を採用する**（v1 主軸だが v2 では fallback）
- ❌ deny を肥大化させる（ask で十分なものまで deny にして摩擦を生む）
- ❌ `NOPASSWD: ALL` を sudoers に書く
- ❌ パターン deny だけに頼り hook を省く（[The Register 2026-04 の bypass 事例](https://www.theregister.com/2026/04/01/claude_code_rule_cap_raises/)）
- ❌ コンテナの中で root として動かす（隔離の意味が半減 — ただし devcontainer 内 root は host 隔離前提なら可）

### 10.3 監査ログのチェックポイント

- ask に対する人間の承認率（高すぎる = ask が広すぎる、低すぎる = エージェントが暴れすぎ）
- deny / hook ブロックの発生（あったら必ず原因調査）
- sudoers 外コマンドの試行（プロンプトインジェクション兆候）

---

## 11. 参考文献

### LLM / AI Agent セキュリティ

- [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm06-sensitive-information-disclosure/) — 3軸最小化と Complete Mediation の元ネタ
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

| Layer | 何を | 何で | カバーする操作 |
|---|---|---|---|
| **L1** | Anthropic native sandbox を有効化 | `.claude/settings.json` の sandbox 設定 | filesystem write / network egress を allowlist 化 |
| **L2** | group membership で sudo を回避 | `usermod -aG docker,systemd-journal claude-agent` 等 | Docker, journalctl, audio 等 通常 sudo 必須操作 |
| **L3** | devcontainer で system mutation を局所化 | `.devcontainer/devcontainer.json` | apt install, systemctl restart 等を container 内に閉じる |
| **L4** | 人間 delegate | Slack / CLI 経由で「これやって」プロンプト | 上記でカバーできない真の特権操作 |

#### L1: Anthropic native sandbox

最初に有効化すべき層。`.claude/settings.json` の `sandbox` 設定で filesystem 範囲と network egress を制限する。**84% prompt 削減効果の根源**。

macOS では `sandbox-exec` (Apple は deprecated 化しているが現状動作。[Infralovers 2026-02 が指摘](https://www.infralovers.com/blog/2026-02-15-sandboxing-claude-code-macos/))、Linux では seccomp / landlock。詳細は [Claude Code Sandboxing docs](https://code.claude.com/docs/en/sandboxing) 参照。

> **注意**: macOS の `sandbox-exec` deprecation は長期的リスク。Production 用途では Linux + devcontainer (L3) を併用するのが安全側。

#### L2: group membership

「agent が docker を使えるようにする」ためには `sudo docker ...` を許可するのではなく、agent ユーザーを `docker` group に入れる。**sudo 経路を完全に消す**。

```bash
# 例: claude-agent を docker と systemd-journal group に追加
sudo usermod -aG docker,systemd-journal claude-agent
```

これにより以下が sudo 不要になる:
- `docker ps` / `docker compose up` / `docker exec`
- `journalctl -u <unit>` (systemd-journal group)
- `cat /var/log/<unit>.log` (適切な ACL / group 設定下)

group 追加は **特権昇格ではない**: agent は root にはならず、特定リソースへの直接アクセス権だけが追加される。sudoers より遥かに安全 (sudoers は実行時に EUID=0 になる、group は元 UID のまま)。

#### L3: devcontainer

`apt install`、`systemctl restart` のような「system 状態を変える」操作は、agent ホストではなく **使い捨て可能な devcontainer 内**で実行する。container を捨てれば変更も消える。

```jsonc
// .devcontainer/devcontainer.json (抜粋)
{
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "remoteUser": "vscode",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "postCreateCommand": "sudo apt-get update && sudo apt-get install -y <pkgs>"
}
```

container 内では agent に `NOPASSWD: ALL` を渡しても **ホストには影響しない**。これが「container × root」が許される唯一の文脈 (§10.2 NG パターン参照)。

#### L4: 人間 delegate

L1-L3 でカバーできない真の host 特権操作 (hardware 操作、L0 物理アクセス、組織ポリシーで sudo が要る操作) は agent に渡さず、**人間に Slack / CLI 経由で頼む形式**にする。

```
エージェント: 「以下のコマンドを host で実行してください: sudo systemctl restart nginx」
人間:        (確認後) 実行 → 結果を agent に貼り戻す
```

非効率に見えるが、L4 まで到達するケース自体が少なければ問題にならない。**L1-L3 で 90% 以上カバーできるのが推奨ライン**。

### 13.3 レシピ選択ガイド

| 状況 | 推奨 |
|---|---|
| 個人開発機 (1-3 台) | L1 + L3 を主、L4 を補助。L2 はオプション。**Appendix B 不要** |
| 開発チーム共有サーバー | L1 + L2 + L3。L4 を運用ルール化 |
| 無人 CI runner | L1 + L3。L4 不可なので残りは **Appendix B (sudoers ホワイトリスト) を fallback** |
| Production deploy server | **Appendix B 必須**。加えて L1 で sandbox 最小化 |

---

## Appendix B: sudoers ベース設計 (sudo がどうしても必要な場合)

§13 のいずれの recipe でも sudo を完全には避けられないケースに限って採用する fallback 設計。
**v1 ではこの内容が本書の中核 (旧 §8) だった**。v2 では条件付き fallback に降格。

採用条件 (§10.1 段階2B):
- 無人 CI runner / 自動デプロイ等で L4 (人間 delegate) が物理的に取れない
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
# 読み取り系: パスワードなしで許可
claude-agent ALL=(root) NOPASSWD: \
    /bin/systemctl status *, \
    /bin/journalctl, \
    /bin/journalctl -n *, \
    /bin/journalctl -u *, \
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

# それ以外は全部拒否（明示）
claude-agent ALL=(ALL) !ALL
```

### B.4 注意点 (旧 §8.4)

- `NOPASSWD` は読み取り系**のみ**。書き込み系で NOPASSWD すると LLM が無人で破壊操作を打てる
- **ワイルドカード `*` は sudoers では `/` もマッチする**ため path traversal を許容する。 例: `/bin/cat /var/log/*.log` は `/var/log/../../etc/shadow.log` 形式の引数でもマッチし、結果として `/etc/shadow.log` (任意位置の `.log` ファイル) を root として読み取りに行ける。 **フルパス + 固定引数** (例: `/bin/cat /var/log/myapp.log` のように unit 名で具体列挙) を推奨。 やむを得ず `*` を使う場合は hook 側で path canonicalize して `..` を含む引数を弾くこと
- B.3 サンプルの `/var/log/*.log` 等は説明簡略化のための例示。 production では各 unit 名を個別に列挙すること
- `Defaults:claude-agent !env_reset, env_keep += "..."` のような env 緩和は **しない**

### B.5 §13 経路への移行 (v2 追加)

状況が変わって §13 の L1-L4 いずれかが採用可能になったら、**Appendix B 経路は速やかに retire する**。sudoers が残るほど bypass の機会が増える (§2.3 の Adversa 事例参照)。

retire 手順:
1. §13 L1 (sandbox) を先行有効化
2. §13 L2 (group) で sudo 経由していた読み取り系を group 経由に移行
3. §13 L3 (devcontainer) で残った書き込み系を container 内に閉じ込め
4. `/etc/sudoers.d/claude-agent` を削除
5. §§4-7 の deny / ask / allow / hook は引き続き有効
