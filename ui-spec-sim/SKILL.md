---
name: ui-spec-sim
description: >
  チケットや要件から「HTML UIスペック (決定ログ D番号・未決Qカード・文言一覧)」と
  「触って遷移を確認できるHTMLシミュレーター (カバレッジ自動チェック付き)」のペアを
  artifactとして作り、ユーザーレビューを何巡も回して確定させる設計レビューループ。
  各巡で敵対的な整合検証 (スペック⇔シミュレーター⇔文言表) を行い、確定した内容だけを
  実装Ticket/Confluenceに最低限のテキストで同期する。Figma納品はfigma-shot-boardに委譲。
  Use when the user wants an interactive UI spec, a transition simulator, a
  decision-log driven design review, or to iterate a UI design with confirmable
  state transitions. Triggers: "ui-spec-sim", "/ui-spec-sim", "UIスペックとシミュレーター",
  "スペックシミュレーター", "設計レビューループ", "遷移を触って確認できるものを作って",
  "トランジションシミュレーター", "デザイン決定ログでレビュー", "interactive spec",
  "transition simulator", "spec with simulator".
version: 1.0.0
---

# ui-spec-sim — UIスペック+シミュレーターの設計レビューループ

チケット1枚から、レビュー可能な2つのHTML成果物を作り、ユーザーの指摘を
**決定ログ (D番号)** として積み上げながら確定させる。実装者は文言一覧と
シミュレーターの遷移をそのまま実装すればよい状態がゴール。

## 成果物の型 (2 artifacts・別URL)

| 成果物 | 役割 |
|---|---|
| **スペックHTML** | 要件ごとのセクション+実UI忠実なモック+決定ログ (D1..)+未決Qカード (案A/B+推奨)+文言一覧 (全UIストリング) |
| **シミュレーターHTML** | 決定を実装した状態機械。遷移カバレッジ自動チェック (触った遷移にチェック=確認漏れが残る)・遷移ログ・障害注入トグル・in-flight遅延 |

言語規則: **注釈=ユーザーの言語 / 製品UI文言=製品の言語** (両成果物とも)。
UI文言はスペックの文言一覧が唯一の正で、モック・シミュレーターは一字一句同じ文字列を使う。

## Phase 0: グラウンディング

1. チケット→親チケット→親スペック (Confluence等) の順に読む。
2. **実UIコードを読んで見た目を掴む** — 対象アプリの実コンポーネント (ボタン様式・
   フィールド様式・テーマ色) をリポジトリから確認し、モックはそれに寄せる。
   汎用デザインの再発明をしない。
3. enum・status値など仕様の土台になる値は**実コードで裏取り**する (存在しない値を
   スペックに書かない)。

## Phase 1: スペックHTML

構造とスケルトンは references/deliverable-templates.md を参照
(WHEN TO READ: このPhaseとPhase 2 の執筆時のみ)。要点:

- **決定ログ**: D番号は増えるのみ。改訂は「D5改」と書き、旧番号は再利用しない
  (チャット・チケットからの参照を壊さない)。各決定に**不採用案と理由**を併記。
- **未決Qカード**: 案A/案B+推奨を明示。解決したら「決定」欄を追記して残す
  (履歴が消えない)。
- **文言一覧**: モックに見えるUIストリング全部に key を振る。「全ストリング」を
  名乗る以上、モックとの完全一致を検証で担保する (下記Phase 3)。
- artifactとして公開し、以後**同じURLで再公開**し続ける。

## Phase 2: シミュレーターHTML

- スペックの決定を全部実装した状態機械。1ファイル・vanilla JS。
- **カバレッジ一覧**が肝: 設計済み遷移を列挙し、操作すると自動チェック。
  「未チェック=未確認」がユーザーへの価値。ガード (disabled化・拒否) も
  観測ベースでチェックする。
- 障害注入 (Slack失敗等)・異常系再現ボタン・RPC遅延+spinner (二重クリック防止) を
  入れて、正常系以外も触れるようにする。
- シミュレーター都合の要素 (再現ボタン等) は「(シミュレーション)」と明示し、
  製品UIと区別する。

## Phase 3: レビューラウンド (何巡でも)

1ユーザー指摘 = 1ラウンド。毎回:

1. 指摘を新D番号 (または D改) に落とし、**スペック・シミュレーター・文言一覧の
   3点を同時に更新**する。片方だけ直すと必ず矛盾が残る。
2. シミュレーターは **headlessブラウザで実挙動を検証** (構文チェック+主要フロー)。
   references/verify-round.md のスニペットを使う (WHEN TO READ: 各ラウンド)。
3. **敵対的整合検証**: 検証agentにスペック⇔シミュレーター⇔文言表⇔決定ログの
   矛盾・古い記述の残骸を探させる (プロンプト雛形は references/verify-round.md)。
   must/should/nit で受け取り、main loopで取捨して反映。
4. 同じURLで再公開し、報告は「今回のD/Q差分」を先頭に。

「効かない」系の報告は、まずheadlessで再現を試みる — 再現しなければ操作上の罠
(状態リセット・分かりにくい既存挙動) を疑い、罠自体を設計で潰す。

## Phase 4: 外部同期 (求められたときだけ)

- **実装Ticket**: 蒸留したテキスト (state flowサマリー+要件+文言一覧への参照) と
  **スクショ (シミュレーター専用の絵は除外)**。添付はjira-cliスキルのREST
  フォールバック参照。
- **親スペック (Confluence)**: 変更された決定だけを外科的に反映。confluenceスキルの
  「Surgical edits — safety rules」に従う (literal-textアンカー・update直前再fetch)。
- **Figma**: figma-shot-board スキルに委譲 (スクショ→ラベル付きボード)。

### 鉄則 (過去の失敗から)

- **チーム向けドキュメントにシミュレーションの内容を書かない**。チームに見せるのは
  Ticket上の最低限テキスト+製品状態のスクショだけ。シミュレーター・録画・探索物は
  チャット/artifactに留める。
- artifactリンクは共有設定するまで本人しか開けない — チーム共有前提の場所に貼るとき
  は一言添える。
- 破壊的操作なしのUI (押せるのに失敗するボタン) を作らない — ガードはUIで先取りし、
  server側はバックストップ。

## References

- references/deliverable-templates.md — スペック/シミュレーターの構造スケルトンと
  実装パターン。WHEN TO READ: Phase 1-2 の執筆時のみ。
- references/verify-round.md — 整合検証agentのプロンプト雛形+headless検証スニペット。
  WHEN TO READ: Phase 3 の各ラウンド。
- references/scenarios.feature — BDD spec。スキル自体の監査・改修時のみ読む。
  通常実行では不要。

## Feedback Check

実行開始前に、この SKILL.md の隣の feedback/log.md が存在し5件以上あれば直近10件を
読む。同一キーワードの問題が3件以上、または直近10件の平均評価が3未満なら、ユーザーに
日本語で伝える: 「過去のフィードバックで類似パターンを検出: [簡潔に]。
/skill-improve --skill ui-spec-sim で改善案を分析できます。」いずれでも実行は続行。
log.md がなければ黙ってスキップ。

## Retrospective

ワークフロー完了後に振り返る:

1. 途中の是正 (却下された設計・方針転換・検証で見つかったバグ) があったか確認。
2. ユーザーに日本語で聞く: 「今回のスペック/シミュレーター作成のフィードバック
   (1-5の評価、気になった点、または何もなければEnter)」
   **評価が5未満なら必ず追問**: 「なぜその評価ですか？ (改善のために具体的に教えてください)」
   回答を Rating reason として逐語記録。auto-modeでもこの追問は省略しない。
3. フィードバックがある、または是正が実際にあった場合:
   a. feedback/ ディレクトリがなければ作成 (この SKILL.md の隣。skillのソースdirは
      git rev-parse --show-toplevel から解決)。
   b. feedback/log.md を読み (なければ `# Feedback Log` ヘッダー+空行+
      `<!-- Append new entries at the top. Do not edit previous entries. -->` で作成)、
      ヘッダー直後に新エントリを追加 (Skill Version / Task / Outcome / Rating /
      Rating reason / Corrections / Issues / User Note)。
   c. 一文の日本語で記録完了を伝える。
4. スキップかつ是正なしなら記録せず終了。
