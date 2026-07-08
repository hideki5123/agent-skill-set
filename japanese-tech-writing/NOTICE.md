# japanese-tech-writing の来歴（provenance）

このスキルは、パブリックドメインの規範文書と、このリポジトリ独自に書いた運用資料
から成る。ファイルごとの権利関係は次のとおりで、`LICENSE` の該当セクションに対応する。

## references/rules.md

源流: k16shikano 氏 (X: @golden_lucky) の Gist「日本語技術文書の文章規範」
<https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d>
ライセンス: Unlicense（パブリックドメイン）。

扱い: 源流の全文を要約せずベースにしている。ただし、原文の地の文が原文自身の
規範（「中黒（・）を日本語の並列で使わない」など、本文が自ら従うべき規範）に
違反している箇所があったため、このリポジトリで自己矛盾を修正した。原文の著者は
「フォークして改造してもらってかまわない」「これだけでは『おまかせで編集』は
無理で、他のさまざまな SKILL に参照させる汎用の規範」と発言しており、この
改変はその方針に沿う。修正は表記や地の文の書き換えにとどめ、規範の主張内容
（何を推奨し何を禁じるか）は変えていない。このファイルは源流と同じ Unlicense
（パブリックドメイン）で公開する。

## SKILL.md

由来: このリポジトリで新規に書いた、モード選択と参照ファイルの読み込み順だけを
示す薄いルーター。hikimay/japanese-tech-writing と WhiteVMW/japanese-tech-writing-ex
（次項参照）の「生成、推敲、公開前チェックの3モード」という運用構造から着想を
得ているが、文面は独自に書き下ろしており、両者からの丸写しはない。
本文の詳細手順は `SKILL.md` からは分離し、`modes.md` に置いている（後述）。
ライセンス: MIT（このリポジトリの著作物）。

## references/modes.md

由来: 3モード（生成、推敲、公開前チェック）それぞれの詳細手順を記述した、
このリポジトリ独自のファイル。hikimay / WhiteVMW にはこの内容に対応する
独立ファイルはなく（両者は同等の手順を `SKILL.md` に直接書いている）、
3モードという運用構造の着想は次項の由来元から得たが、手順の文面、チェックの
順序、severity 方式との連携は、このリポジトリで独自に書き下ろしたものであり、
丸写しではない。
ライセンス: MIT（このリポジトリの著作物）。

## references/checklist.md

由来: 公開前チェックを「severity 方式（BLOCKER / IMPORTANT / TASTE の3段階）」
で行うという判定基準は、このリポジトリのオーナーが決定した独自方針であり、
hikimay / WhiteVMW の「6軸×10点、合格ライン42/60」という数値採点方式とは異なる。
チェック項目そのものは `rules.md` の規範に対応させて独自に構成しており、
6軸の採点ルーブリックの丸写しはしていない。
運用構造（公開前チェックというモードの存在自体）は hikimay/japanese-tech-writing
(MIT, <https://github.com/hikimay/japanese-tech-writing>) と
WhiteVMW/japanese-tech-writing-ex (MIT/Unlicense混在,
<https://github.com/WhiteVMW/japanese-tech-writing-ex>) の運用構造から着想を
得た。参考にしたのは「モードの一つとして公開前チェックを置く」という構成の
アイデアのみで、採点の中身、重み付け、合否基準はこのリポジトリで独立に
書き直している。
ライセンス: MIT（このリポジトリの著作物）。

## references/style-profiles.md

由来: 技術書、API リファレンス、技術ブログ、翻訳解説それぞれで `rules.md` の
規範をどう例外運用するかをまとめた、このリポジトリに完全オリジナルの資料。
hikimay にも WhiteVMW にも対応する内容はなく、上流ソースは存在しない。
ライセンス: MIT（このリポジトリの著作物）。

## naturalize-ja との関係（辞書の非重複について）

このリポジトリには既存スキル `naturalize-ja/`（`references/ai-japanese-patterns.md`
に15カテゴリの禁止フレーズ辞書を持つ）がある。`japanese-tech-writing` は
「文章設計、生成、論証、構成」に特化しており、意図的に `naturalize-ja` とは
**疎結合**にしている（統合も完全分離もしない）。

具体的には、`japanese-tech-writing` の各ファイルは `naturalize-ja/references/ai-japanese-patterns.md`
の禁止フレーズ辞書を複製せず、同梱もしていない。LLM っぽい表現に触れる箇所があっても、
それは論証構成上の禁止事項として書かれた抜粋であり、AI 臭語彙の**正本ではない**。
語彙の正本は常に `naturalize-ja/references/ai-japanese-patterns.md` である。
推敲モード（`references/modes.md`）では、文章構成や論証を整えたあとの AI 臭検出と
置換の工程を `naturalize-ja` スキルへ委譲する導線を明記している。
