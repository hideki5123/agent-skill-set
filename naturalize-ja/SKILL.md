---
name: naturalize-ja
description: 任意の日本語テキスト (ファイル / 貼り付けテキスト / ディレクトリ) を読み、AI 生成と気づかれる「不自然な日本語表現」を検出・置換します。プレ AI 時代の技術ブログ調へ整えるための禁止フレーズ辞書 (15 カテゴリ。実フィードバックと公開研究を統合) と、grep + 質的レビューの二段監査を内蔵 (subagent をさらに spawn せず、自分のコンテキスト内で完結)。en-to-ja-explainer など他スキルから委譲して使うことも想定。Triggers: 「AI っぽい日本語をレビューして」「この文章を自然な日本語にして」「ChatGPT 臭を抜きたい」「日本語の AI 臭をチェック」「ナチュラルな日本語に直して」「AI 生成バレしないように直して」「naturalize Japanese」「naturalize-ja」「/naturalize-ja」
version: 1.1.0
---

# naturalize-ja

`naturalize-ja:naturalize-ja` サブエージェントに処理を委譲する thin wrapper。
ロール定義 (日本語ネイティブのレビュアー) と二段監査ワークフロー (grep +
質的レビューを **同一コンテキスト内**で完結) は subagent 側に集約。

## 呼び出し方

```text
@agent-naturalize-ja:naturalize-ja <target> [--policy auto|propose] [--scope <section>]
```

引数の意味と挙動は subagent 側の system prompt に書いてある。auto-discovery
のトリガーフレーズ経由でこの skill が呼ばれたときは、ユーザー入力をその
まま subagent に渡して実行を委ねる。

## 委譲元から見たインターフェース

他スキル (例: `en-to-ja-explainer`) からこのスキルを呼びたいときは:

- `@agent-naturalize-ja:naturalize-ja` を直接呼ぶ (subagent への
  delegation。スキル経由のホップを省略できる)
- もしくは `/naturalize-ja` skill 呼出 (本 wrapper 経由)

どちらでも、最終的に subagent 側のワークフローが走る。

## なぜ subagent 化したか

- このスキルの本質は「同じ役割・判断基準を持つ担当者に任せる」(role-based)
  であり、「毎回同じ手順を回す」(procedure-based) ではない
- 委譲元 (en-to-ja-explainer など) から呼ぶときに、subagent 呼出のほうが
  context boundary が綺麗
- 内部で subagent をさらに spawn しない設計に整理されたことで、subagent
  化が現実的になった (Claude Code の subagent は further subagent を spawn
  できない)

## References

subagent が必要に応じて読む reference:

- `references/ai-japanese-patterns.md` — 15 カテゴリの禁止フレーズと置換辞書
- `references/review-agent-prompt.md` — 質的レビューのチェックリスト

## Retrospective

セッション完了時:

1. 辞書に無かった新パターンが見つかったか確認する
2. ユーザーに 1 行で問いかける:「今回直したフレーズで辞書に追加すべき
   パターンや、見落としていた表現があれば一言だけ (Enter でスキップ)」
3. フィードバックがある、または新パターンが現場で出ていた場合:
   a. `feedback/log.md` を作成 / 追記
   b. エントリには新パターンとカテゴリ案を含める
4. クリーンに完走でフィードバックも新パターンも無ければ、ログ無しで終了

## Feedback Check

スキル起動時、`feedback/log.md` に 5 件以上あれば直近 10 件を読む。
同じ新パターンが 3 件以上検出されているなら、ユーザーに伝える:

「直近のフィードバックで『X』というパターンが繰り返し検出されています。
`ai-japanese-patterns.md` のカテゴリ Y への追加を提案します。」

決定はユーザーに委ね、深い分析が必要なら `/skill-improve --skill
naturalize-ja` に進める。ログが無い、または 5 件未満なら静かにスキップ。
