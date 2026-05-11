---
name: en-to-ja-explainer
description: 英語の技術ドキュメント (Hugging Face docs / GitHub README / arXiv 論文 / 技術ブログ等) を、日本人が読んで AI 生成と気づかない自然な日本語の解説サイトに変換します。フェッチ → 構成設計 → HTML/CSS/JS 生成 → 多角レビュー (技術正確性 + 日本語自然さ + UX) → 修正 → ローカル配信、まで一気通貫。日本語のチェックは AI らしさパターン辞書と複数視点のサブエージェントレビューで二段構え。Triggers: 「英語ドキュメントを日本語で解説するサイトを作って」「Japanese explainer for [URL]」「英語の技術ドキュメントをやさしく日本語にして」「Convert this English doc to a Japanese site」「AI っぽくない日本語で技術解説」「Hugging Face docs を日本語化」「arXiv を日本語で噛み砕いて」「en-to-ja explainer」「/en-to-ja-explainer」
version: 1.0.0
---

# en-to-ja-explainer

英語の技術ドキュメントを、日本人が読んで AI 生成と分からない自然な日本語の解説サイトに変換するスキル。最大の差別化は「AI っぽい日本語の自動除去」。

## いつ使うか

- 英語のドキュメント (URL or 貼り付けテキスト) から日本語解説サイトを作ってほしいと言われたとき
- 既存の日本語サイトを「AI 臭を抜きたい」と言われたとき
- ユーザーが特定フレーズを「これ AI っぽい」と指摘し、似たパターンを全体に展開してほしいとき

逆に使わないケース:
- 数行レベルの短い翻訳 (skill を介さず直接対応)
- 解説を伴わない素の翻訳のみ (翻訳特化のスキルがあればそちら)

## 入力で確認すること

ユーザーが指定していなければ、最大 2 つだけ聞く:

1. **ソース URL** または貼り付けテキスト
2. **想定読者層** (初学者 / 中級 / 上級) — 足場づくりの深さに影響
3. **出力ディレクトリ** — デフォルト `./<topic>-ja-explainer/`
4. **ローカル配信ポート** — デフォルト `8765`

聞きすぎない。3 件以上は推測 + デフォルトで進めて、必要なら後で確認。

## ワークフロー

### Step 1: フェッチと構成設計

1. `WebFetch` で英語の原文を取得。長すぎる場合はパスごとに分けて取得し、構成段階で取捨選択する
2. 抽出する要素:
   - トピック名 / スコープ
   - 読者が知らない可能性のある専門用語
   - 前提知識 (上流概念)
   - 原文に出てくる主な例 / アナロジー (再利用すると一貫性が出る)
3. 日本語のセクション構成案を作る。標準的な骨格:
   1. なぜこの記事を読むのか (intro + ゴール)
   2. 前提知識・用語の確認
   3. 中心概念を 3-7 セクションで段階的に
   4. 数式や仕様の読み解き
   5. インタラクティブな確認 (任意)
   6. コマンド / コードの読み方 (該当する場合)
   7. 用語集
4. 構成案をユーザーに 1 度提示し、合意を取ってから本文を書き始める

### Step 2: サイトの雛形を生成

最低限 3 ファイル:

```
<output-dir>/
├── index.html       # 1 ページで完結
├── styles.css       # レスポンシブ前提
└── script.js        # 任意。インタラクティブな確認 UI 等
```

詳細な構造・breakpoint・SVG ルールは `references/site-template-guide.md` を参照。最低限守るべきこと:

- `clamp()` で hero/h1/h2/h3/pre をビューポート連動に
- SVG は `min-width: 640px` + `overflow-x: auto` (スマホでは横スクロール、ただし字が潰れない)
- `<table>` / `<pre>` も `overflow-x: auto`
- TOC はタブレット幅で 2 列、スマホで 1 列に切り替え
- すべての `<label>` に `for="..."`、動的結果領域に `aria-live="polite"`

### Step 3: 日本語本文を書く

**書き始める前に必ず** `references/ai-japanese-patterns.md` を読み、これを文体ガイドとして従う。

各セクションで:

1. 当たり前の日本語でドラフト
2. ドラフト直後に AI 表現の grep を回す (patterns ファイルに grep コマンドあり)
3. ヒットを 1 つずつ置換

「読みやすさ」ではなく「ネイティブが読んで引っかからないか」を最適化軸にする。

加えて、用語訳の一貫性と文体は `references/tech-translation-guide.md` を参照。

### Step 4: 多角レビュー

`references/team-roles.md` の各エージェントを並列で走らせる:

- **技術正確性レビュー** — `codex-cli` スキルにデリゲート。英語原文と日本語の対応を機械的にクロスチェック
- **日本語自然さレビュー** — 汎用 Agent。`ai-japanese-patterns.md` のカテゴリ A〜L に照らして AI 臭を網羅検査
- **UX/レスポンシブレビュー** — 汎用 Agent。SVG overflow、表のはみ出し、コードブロック、clamp() の使用などを静的に検証
- **(任意) 学習体験レビュー** — 汎用 Agent。読者層に対して説明順序が妥当か

依存関係がないので可能な限り並列。プロンプトのテンプレートは `references/team-roles.md` にある。

### Step 5: 修正の適用

`references/team-roles.md` の Synthesis Protocol に従う:

- CRITICAL → 自動適用
- IMPORTANT → ユーザーに確認 (内容変更や文体に影響するため)
- NICE-TO-HAVE → 提示のみ、適用は明示の指示が来てから

適用後、もう一度 patterns ファイルの grep を回し、新規 AI 臭が混入していないか確認する。

### Step 6: ローカル配信

`scripts/serve.sh <output-dir> [port]` で起動 (内部で `python3 -m http.server`)。

LAN IP も解決して、スマホからアクセスできる URL も併せて返す。

### Step 7: ユーザーへの最終報告

返す内容:

- ローカル URL
- LAN URL (取れた場合のみ)
- 生成ファイルのパス一覧
- 適用したレビュー findings の要約 (CRITICAL は何件、IMPORTANT は何件保留中、など)
- 残課題・既知の制約

## References

- `references/ai-japanese-patterns.md` — AI 日本語の禁止語句・置換辞書 (**最重要**)
- `references/team-roles.md` — レビューエージェントのプロンプト集と統合プロトコル
- `references/site-template-guide.md` — HTML / CSS / SVG / レスポンシブの基本パターンと落とし穴
- `references/tech-translation-guide.md` — 英→日の用語訳と文体方針

## Behavior Scenarios

```gherkin
Scenario: 英語 URL から日本語解説サイトを生成
  Given ユーザーが英語の技術ドキュメント URL を提示
  When ユーザーが「Hugging Face docs を日本語化して explainer サイト作って」と言う
  Then スキルは原文をフェッチし、構成案を提示して合意を取り、HTML/CSS/JS を
       レスポンシブで生成、AI 臭 grep + 多角レビューを実施、CRITICAL を適用、
       ローカルサーバを起動して URL を返す

Scenario: 既存サイトの日本語自然さ監査
  Given ユーザーが既に書かれた日本語の HTML ファイルを指定
  When ユーザーが「AI っぽい日本語をレビューして直して」と言う
  Then スキルは ai-japanese-patterns.md の grep を実行し、自然さレビュー
       エージェントを起動、カテゴリ別に Before/After を提示、承認分を適用

Scenario: ユーザーが 1 フレーズを「これ AI っぽい」と指摘
  Given サイトは既に生成済み
  When ユーザーが該当フレーズを引用して「これ AI っぽい」と指摘
  Then スキルはそのフレーズが ai-japanese-patterns.md のどのカテゴリかを判定し、
       同パターンを全ファイルから検索、一括修正を 1 メッセージで適用する。
       辞書に無いパターンであれば、辞書への追加候補としても記録する

Scenario: モバイル / レスポンシブの不具合報告
  Given ユーザーが「文字が切れている」「表がはみ出る」等のレイアウト問題を報告
  When ユーザーがスクリーンショットまたは現象を共有
  Then スキルは SVG viewBox overflow / table overflow / フォントスケーリングの
       いずれかを特定し、site-template-guide.md の対応パターンに沿って
       最小差分の修正を適用する

Scenario: 長すぎる英語ソース
  Given 原文が長文 (arXiv 論文等)
  When ユーザーが日本語 explainer 作成を依頼
  Then スキルは複数パスで取得 (abstract → 主要セクション → 必要時の詳細) し、
       本文を書き始める前にセクション構成をユーザーに確認する

Scenario: ユーザーが想定読者層を未指定
  Given URL 以外の前提条件が指定されていない
  When スキルが起動
  Then 想定読者層・出力ディレクトリ・ポートの 3 つを最大 2 つだけ確認する。
       それ以上は推測 + デフォルトで進める
```

## Retrospective

セッション完了時 (Step 7 が終わった後) に次を行う:

1. セッション中の出来事を振り返る:
   - 構成案や訳語の差し戻し
   - 多角レビューで覆った AI 臭の表現
   - `ai-japanese-patterns.md` の辞書に無かった新パターン
   - レイアウト / SVG の修正
2. ユーザーに 1 行で問いかける (日本語):
   「今回のレビューで気になった AI 表現 / 改善ポイントがあれば一言だけ (Enter でスキップ)」
3. ユーザーからフィードバックがある、または辞書に無い新パターンが現場で出ていた場合:
   a. このスキルのソースディレクトリを `git rev-parse --show-toplevel` で解決し、`feedback/log.md` を作成 / 追記
   b. log エントリには新パターンとカテゴリ案を必ず含める (`ai-japanese-patterns.md` 更新の根拠になる)
4. クリーンに完走でフィードバックも新パターンも無ければ、ログには書かず終了

ログのフォーマットは `references/skill-improvement-guide.md` (factory 側) を参照。

## Feedback Check

スキル起動時、`feedback/log.md` に 5 件以上の記録があるなら直近 10 件を読む。同一の新パターン (辞書未登録の AI 表現) が 3 件以上で出ているなら、ユーザーに伝える:

「直近のフィードバックで『X』というパターンが繰り返し検出されています。`ai-japanese-patterns.md` への追加を提案します。」

決定はユーザーに委ね、必要なら `/skill-improve --skill en-to-ja-explainer` で深い分析に進める。

ログが無い、または 5 件未満なら静かにスキップして通常実行に移る。
