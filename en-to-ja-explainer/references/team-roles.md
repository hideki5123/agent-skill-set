# Multi-Agent Review Team

生成した日本語サイトを 3-4 視点で並列レビューする。各レビュアは独立して走らせ、結果を Synthesis Protocol で統合する。

## Required: 技術正確性レビュー (codex-cli にデリゲート)

別 AI のクロスチェックが、訳しすぎ / 訳し漏れ / 数式パラメータの取り違えに最も効く。`codex-cli` スキルを使う。

呼び出しテンプレート:

```bash
codex exec "日本語サイト {OUTPUT_DIR} を、英語原文 {SOURCE_URL} に照らしてレビューしてください。
次の観点で確認します:

1. 事実誤りや、訳し漏れ・訳しすぎによる誤解
2. 数式・コマンド引数の対応関係 (パラメータ名、デフォルト値、フラグの意味)
3. 英→日の用語訳が一貫しているか
4. コード例が原文と一致するか

結果は CRITICAL / IMPORTANT / NICE-TO-HAVE で分類。
各 finding には対応する日本語サイトの file:line 参照を必ず添える。
800 字以内。" \
  --full-auto -s read-only -o /tmp/codex-tech-review.txt -C {OUTPUT_DIR} --skip-git-repo-check
```

`run_in_background: true` で投げ、Monitor で `-o` ファイルを待つ。

## Required: 日本語自然さレビュー (naturalize-ja に委譲)

`naturalize-ja` スキルを呼ぶ:

- 入力: `<output-dir>/index.html` (および本文 .md ファイルがあれば追加)
- ポリシー: `propose` (Synthesis Protocol で他レビューと合わせて判断するため、自動適用はしない)
- 期待される出力: CRITICAL / IMPORTANT / NICE-TO-HAVE 分類済み findings、および辞書に無い新パターン候補

辞書 (A-O カテゴリ)、grep コマンド、サブエージェントへのプロンプトテンプレートはすべて
naturalize-ja 側に集約されている。このスキルは詳細を抱えない。

## Required: UX / レスポンシブレビュー

サイトを 3 つの幅 (320px / 768px / 1024px) で表示したときの想定レイアウトを静的に検証する。汎用 Agent にデリゲート。

プロンプトテンプレート:

```
サイト {OUTPUT_DIR} の HTML / CSS を静的に解析し、次の問題が起きる可能性が
あるかを 320px / 768px / 1024px の 3 つの幅で検証してください。

1. SVG diagram のテキストが viewBox を超えて切れていないか
   - 各 <text x="..."> の x + 推定文字幅 が viewBox の幅を超えていないか
   - 外周要素 (rect, line, polygon) が viewBox 内に収まっているか
2. <table> がはみ出さずに横スクロール対応されているか
   - .table-wrap などの overflow-x: auto が当たっているか
   - 最低幅 (min-width) が短すぎないか
3. <pre><code> が折り返しまたは横スクロールできるか
4. hero / h2 / h3 が幅に応じて適切に縮むか (clamp() の使用有無)
5. <label> に for="..." が付いているか / 動的結果領域に aria-live があるか
6. プレイグラウンドのような入力 UI がスマホで操作可能な配置か

問題ごとに (file:line) と、提案する CSS / SVG 修正の最小差分を示す。
重大さは CRITICAL / IMPORTANT / NICE-TO-HAVE で分類。
```

## Optional: 学習体験レビュー (読者層指定時のみ)

ターゲット読者が「初学者」など明示されているときだけ起動する。

プロンプトテンプレート:

```
対象読者を {AUDIENCE_LEVEL} と仮定し、サイト {OUTPUT_DIR} の説明の組み立てが
妥当かを検証してください。

- 前提知識の説明が読者層に対して十分か (前出しすぎ / 不足)
- 専門用語が出てきた時点で定義 or 用語集リンクが付くか
- 数式や図が出る順序が概念導入と整合しているか
- 例示が現実味のあるタスクで一貫しているか
- 「飛躍」している段落はないか (前の説明だけでは次の主張が出てこない箇所)

各 finding は file:line と該当セクションを参照。
CRITICAL / IMPORTANT / NICE-TO-HAVE で分類。
```

---

## Synthesis Protocol

並列で得られた 3-4 レビューを統合する手順:

1. **集約** — 各レビュアの findings を 1 つのリストに統合 (出力ファイル `/tmp/*-review.txt` を順に読む)
2. **分類** — CRITICAL / IMPORTANT / NICE-TO-HAVE
   - **CRITICAL**: 事実誤り、読み手を誤導するレベルの AI 臭、画面が破綻するレイアウトバグ
   - **IMPORTANT**: 読みやすさ・学習体験を明確に改善する
   - **NICE-TO-HAVE**: 微妙な好み、アクセシビリティ細部
3. **重複削除** — 複数視点が同じ箇所を指していれば、最も具体的なものを採用
4. **適用順** —
   - CRITICAL は確認なしで自動適用
   - IMPORTANT は箇条書きで提示し、ユーザーに「全部適用 / 個別選択 / 保留」を聞く
   - NICE-TO-HAVE は提示のみ、適用は明示の指示が来てから
5. **適用後の再チェック** — `ai-japanese-patterns.md` の grep を再実行し、修正で新たな AI 臭が混入していないか確認
6. **報告** — ユーザーには「適用済み / 保留中」のリストと、サーバ URL、LAN URL、新たに辞書追加候補となった表現があれば併せて返す

---

## Cross-Skill Delegation

| 視点 | 委譲先 | いつ |
|---|---|---|
| 技術正確性 | `codex-cli` | 常に。クロスチェック効果が高い |
| QA 観点 | `orch-qa` | サイトに自動テスト (E2E等) が書かれている場合のみ |
| シナリオ網羅 | `scenario-gen` | サイトの例示の網羅性を機械的に確認したいとき |

委譲は **示唆** にとどめる。最終決定はオーケストレータ (このスキル) 側。

---

## 実装メモ

並列実行の例 (Claude が 1 メッセージで投げる):

```
- Skill(skill="naturalize-ja", args="<output-dir>/index.html --policy propose")
- Agent(subagent_type=general-purpose, prompt=UX/レスポンシブレビュー...)
- Bash(codex exec ... --full-auto -s read-only -o /tmp/codex-tech-review.txt, run_in_background=true)
```

3 つは独立しているので並列で投げる。codex は背景実行 + Monitor で待ち、naturalize-ja と UX Agent は前景で同時起動。全部揃ったら Synthesis に入る。
