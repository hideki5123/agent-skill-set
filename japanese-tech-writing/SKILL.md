---
name: japanese-tech-writing
description: 日本語の技術文書（書籍の章、記事、解説文）を新規に書く、既存の下書きを推敲する、公開前に規範違反を洗い出す、の3モードで支援します。k16shikano氏のGist「日本語技術文書の文章規範」(Unlicense) をベースにした段落構成、論証の厳密さ、読み手の負荷管理、演出の抑制などの文章規範 (references/rules.md) と、BLOCKER/IMPORTANT/TASTEのseverity方式チェックリスト (references/checklist.md) を内蔵。技術書/APIリファレンス/技術ブログ/翻訳解説ごとの例外は references/style-profiles.md に分離。AIっぽい語彙そのものの検出と置換は行わず、既存スキル naturalize-ja に委譲します (疎結合)。Triggers: 「日本語の技術文書を書いて」「技術書の章を書いて」「この下書きを推敲して」「パラグラフライティングで整えて」「公開前にチェックして」「日本語技術文書の規範に沿って直して」「japanese tech writing」「japanese-tech-writing」「/japanese-tech-writing」
version: 1.0.0
---

# japanese-tech-writing

日本語の技術文書（書籍の章、記事、解説文）を対象に、**生成**、**推敲**、**公開前チェック**の3モードで文章規範を適用する薄いルーター。規範の本体、チェック項目、モードごとの手順は `references/` に分離してあり、このファイルはモードの選び方と参照順だけを示す。規範の内容そのものはここに書き写さない。

規範の出典（k16shikano氏のGist、Unlicense）と、このリポジトリでの改変範囲は [NOTICE.md](NOTICE.md) と [LICENSE](LICENSE) にファイル単位で明記してある。

## 3つのモード

ユーザーの依頼が次のどれに該当するかを最初に判定する。

### モードA: 生成

新しい日本語技術文書を最初から書くとき。

読み込み順:

1. [references/rules.md](references/rules.md)：全規範。書きながら適用する（下書きを書いてから後で直す二段構えにしない）。
2. [references/style-profiles.md](references/style-profiles.md)：文書の型（技術書/APIリファレンス/技術ブログ/翻訳解説）に該当する例外があれば適用する。
3. [references/modes.md](references/modes.md) の「モードA」：上記2つを適用する実行手順。

### モードB: 推敲

既存の下書きを受け取り、規範に沿って直すとき。

読み込み順:

1. [references/modes.md](references/modes.md) の「モードB」：4パスの手順とその順序。まず論証と厳密さ、次に構成と段落、続いて読み手の負荷と冗長、最後に表層の順で適用する。この順序を守る。
2. [references/rules.md](references/rules.md)：各パスが参照する規範本体。
3. [references/style-profiles.md](references/style-profiles.md)：文書の型に応じた例外。
4. 4パス完了後、仕上げ確認として [references/checklist.md](references/checklist.md) を通してもよい（任意）。
5. 4パス完了後、AIっぽい語彙の検出と置換は行わず、naturalize-jaへ引き継ぐ（後述）。

### モードC: 公開前チェック

文書を公開する前に、修正はせず違反を洗い出して報告するとき。

読み込み順:

1. [references/checklist.md](references/checklist.md)：点検項目とseverity (BLOCKER/IMPORTANT/TASTE)。
2. [references/rules.md](references/rules.md)：各項目の違反判断根拠と具体例。
3. [references/style-profiles.md](references/style-profiles.md)：文書の型に応じた例外。
4. [references/modes.md](references/modes.md) の「モードC」：報告の順序と総合判定の出し方。

## naturalize-ja との関係

`japanese-tech-writing` と、このリポジトリの既存スキル `naturalize-ja` は**疎結合**である。統合もしないし、完全に分離もしない。

- **役割分担**: `japanese-tech-writing` は文章設計、生成、論証、構成を担当する。`naturalize-ja` は既存テキストのAIっぽさ検出と置換に特化し、`naturalize-ja/references/ai-japanese-patterns.md` に15カテゴリの禁止フレーズ辞書を持つ。**AIっぽい語彙の正本は常にnaturalize-ja側**であり、`references/rules.md` の「LLMっぽい表現の禁止」節は、論証や構成に絡む言い回し（予告と総括、正面から系など）の抜粋にすぎない。
- **推敲モード(B)での導線**: 4パスを終えたテキストは、そのままAIっぽさ検出のためnaturalize-jaへ引き継ぐ。呼び出しは次のいずれか:
  - `@agent-naturalize-ja:naturalize-ja <target> --policy propose`（subagent直接呼出。en-to-ja-explainerが委譲元として使う形と同じ）
  - `/naturalize-ja` スキル呼出（wrapper経由。挙動は同じ）
- **生成モード(A)と公開前チェック(C)ではnaturalize-jaを呼ばない**: 生成モードは最初から規範に沿って書くため、後段の語彙検出は不要になる。公開前チェックは違反の洗い出しに徹し、修正の実行（naturalize-jaへの引き継ぎを含む）はモードB、あるいはユーザーの判断に委ねる。

## References

- [references/rules.md](references/rules.md)：文章規範の本体
- [references/checklist.md](references/checklist.md)：公開前チェックの点検項目とseverity
- [references/modes.md](references/modes.md)：3モードそれぞれの実行手順
- [references/style-profiles.md](references/style-profiles.md)：技術書/APIリファレンス/技術ブログ/翻訳解説の例外

## Retrospective

セッション完了時:

1. セッション中に起きたことを振り返る:
   - rules.md / checklist.md に無かった判断（新しい違反パターン、判定に迷ったケース）
   - モードの選択を誤った、あるいはユーザーに訂正されたケース
   - style-profiles.md のジャンル判定で迷ったケース
2. ユーザーに1行で問いかける:「今回の規範適用で、追加すべきルールや見落としていた違反パターンがあれば一言だけ (Enterでスキップ)」
3. フィードバックがある場合:
   a. `feedback/log.md` を作成/追記する
   b. エントリには該当ファイル (rules.md / checklist.md / modes.md / style-profiles.md) と提案内容を含める
   c. AIっぽい語彙そのものに関するフィードバックであれば、正本を持つnaturalize-ja側の `feedback/log.md` への転記も提案する
4. クリーンに完走し、フィードバックも無ければログは書かずに終了する

## Feedback Check

スキル起動時、`feedback/log.md` に5件以上あれば直近10件を読む。同じ指摘が3件以上あるなら、ユーザーに伝える:

「直近のフィードバックで『X』というパターンが繰り返し指摘されています。references/該当ファイルへの追加を提案します。」

決定はユーザーに委ね、深い分析が必要なら `/skill-improve --skill japanese-tech-writing` に進める。ログが無い、または5件未満なら静かにスキップする。
