# AI Agent Sudo Permissions — ガードレール設計書

ローカルAIエージェントに `sudo` を含む特権操作を任せるための、3層パーミッションモデルと多層防御の設計ドキュメント。

> Status: Design only（実装は含みません。`.claude/settings.json` や hook の実体は本書を元に各リポジトリで導入する）

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
    "Bash(sudo rm -rf /*)",
    "Bash(sudo rm -rf ~*)",

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

`sudo -n` 付きの読み取り系は明示しないと ask に落ちる。

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
  if echo "$sub" | grep -qE '^(sudo +)?rm +(-[a-zA-Z]*[rRf][a-zA-Z]*) +(/|~|/\*|\$HOME)( |$)'; then
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

> 注: 上の正規表現は説明用。本実装では unit test を伴うべき。

---

## 8. 補助層: sudoers（最強の Complete Mediation）

### 8.1 なぜ必要か

settings.json と hook は **Claude Code のプロセス内の防御**。Claude Code を経由しない攻撃（プロンプトインジェクション経由で別シェルを起動など）に対しては OS レベルの sudoers が最後の砦。

### 8.2 設計方針

- エージェント専用ユーザー `claude-agent` を作成
- `claude-agent` の sudoers は**読み取り系のみ NOPASSWD**、書き込み系は**コマンド単位ホワイトリスト**
- ワイルドカード（`*`）は sudoers では極力使わない（引数迂回のリスク）

### 8.3 サンプル: `/etc/sudoers.d/claude-agent`

```sudoers
# 読み取り系: パスワードなしで許可
claude-agent ALL=(root) NOPASSWD: \
    /bin/systemctl status *, \
    /bin/journalctl, \
    /bin/journalctl -n *, \
    /bin/journalctl -u *, \
    /usr/bin/ss -tlnp, \
    /usr/bin/lsof, \
    /bin/cat /var/log/*.log, \
    /usr/bin/tail /var/log/*.log

# 書き込み系: パスワード要求（人間の関与を強制）
claude-agent ALL=(root) PASSWD: \
    /bin/systemctl restart myapp, \
    /bin/systemctl reload nginx

# それ以外は全部拒否（明示）
claude-agent ALL=(ALL) !ALL
```

### 8.4 注意点

- `NOPASSWD` は読み取り系**のみ**。書き込み系で NOPASSWD すると LLM が無人で破壊操作を打てる
- ワイルドカード `*` は sudoers の引数マッチで予期せぬ挙動になりがち。**フルパス＋固定引数**を推奨
- `Defaults:claude-agent !env_reset, env_keep += "..."` のような env 緩和は**しない**

---

## 9. 多層防御の全体像

| 層 | 防御対象 | 実装 | 検出時の挙動 |
|---|---|---|---|
| **L0: 隔離** | 全層が破られた場合の被害局所化 | Container / VM / user namespace | プロセス分離 |
| **L1: sudoers** | Claude Code を経由しない攻撃 | `/etc/sudoers.d/claude-agent` | OS が拒否 |
| **L2: Sandbox (OS-level)** | Bash 子プロセスの FS/network | Claude Code `sandbox` 設定 | カーネルが拒否 |
| **L3: PreToolUse hook** | 意味的に危険なコマンド | `scripts/hooks/pretool-bash-guard.sh` | exit 2 で停止 |
| **L4: permissions.deny** | 明確にパターン化できる禁止操作 | `.claude/settings.json` | ルールで拒否 |
| **L5: permissions.ask** | 影響大の操作 | `.claude/settings.json` | 人間承認待ち |
| **L6: 監査** | 事後検出・学習 | shell history + auditd + Claude セッションログ | アラート |

**重要**: L3 〜 L5 は LLM 経由でのみ効く。L0 〜 L2 は経由を問わず効く。本気で守るなら L0 〜 L2 が主、L3 〜 L5 は UX 改善層と捉える。

---

## 10. 運用ガイド

### 10.1 導入順序（推奨）

1. **段階0**: 既存環境を測定（どんなコマンドが発行されているか1週間ログ取得）
2. **段階1**: ask を広く設定（sudo 全部 ask）して**生活実態と摩擦点を把握**
3. **段階2**: 頻発する安全な操作を allow に昇格
4. **段階3**: deny を最小セットで導入（本書の §4）
5. **段階4**: PreToolUse hook と sudoers を追加（本気の防御）
6. **段階5**: 隔離環境（コンテナ/VM）に移行

各段階で**1〜2週間運用**して摩擦と漏れを確認してから次へ。

### 10.2 NG パターン

- ❌ `--dangerously-skip-permissions` を常用する
- ❌ deny を肥大化させる（ask で十分なものまで deny にして摩擦を生む）
- ❌ `NOPASSWD: ALL` を sudoers に書く
- ❌ パターン deny だけに頼り hook を省く
- ❌ コンテナの中で root として動かす（隔離の意味が半減）

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

---

## 12. 改訂履歴

| 日付 | 変更 |
|---|---|
| 2026-05-13 | 初版（緩め deny + 広め ask 方針） |
