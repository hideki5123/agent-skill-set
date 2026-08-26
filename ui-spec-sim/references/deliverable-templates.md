# 成果物スケルトン (スペック / シミュレーター)

WHEN TO READ: Phase 1-2 の執筆時のみ。実証済みの構造・実装パターン集
(2026-08 ROMS-4831 で6巡のレビューを通過した形)。

## 共通

- 1ファイル・自己完結HTML (artifactのCSPは外部ホスト不可、Google Fontsのみ可)。
- テーマ: スペックの地はlight/darkトークン対応、**モック部は固定light**
  (実アプリのスクショという扱い。literal色でOK)。
- モックは対象アプリの実装スタックに寄せる (例: MatBlazorなら紫raised、
  Bootstrapならbtn-danger)。実コードから色・部品様式を拾う。

## スペックHTML の構成順

1. ヘッダー: チケット系譜 (SPEC→実装先→親) のリンク行
2. レビューガイド: 「確認① 決定済みD1–Dn / 確認② 未決Q1–Qn」の2カード
3. ライフサイクル図 (状態遷移の全体像。hazard状態は斜線背景等で強調)
4. 要件セクション (チケットの要件番号と1:1対応。REQ n タグ)
   - 決定ボックス: `D番号: 決定文` + `<span class="alt">不採用案 — 理由</span>`
   - 状態切替トグル (seg) で1つのモックに複数状態を持たせる
   - ピン (赤丸英字) をモック内の該当要素に**インライン**配置 (絶対座標は
     レスポンシブで壊れる)、凡例をモック直下に
5. 文言一覧テーブル: key (mono) / 文言 / 使用箇所。プレースホルダは {robot} 形式
6. 決定ログテーブル: # / 決定 / 不採用案 / 理由
7. Qカード: 案A/案B (opt-tag) + 推奨 + 解決後は `.q-decided` で決定欄追記
8. フッター: rev履歴 (rev.N 日付 — 反映内容)

### 決定ログの運用

- D番号は**追加のみ**。内容が変わったら「D5改」表記で同番号を更新し、
  フッターに履歴を残す。削除・再利用はしない。
- ユーザーの疑問に答えた設計 (異常系の扱い等) も D として明文化する —
  口頭回答で終わらせると次巡で矛盾の種になる。

## シミュレーターHTML の骨格 (vanilla JS)

```js
let S;                 // 状態: { opMode, req: null|{status,...}, ... }
let busy = null;       // {key} — in-flight RPC (D: 全操作にspinner+全ボタンdisable)
let dialog = null;     // {type, ...}
const coverage = {};   // 遷移カバレッジ (COV配列のkey→bool)

function run(key, ms, fn) {          // 疑似RPC: 遅延+spinner+二重クリック防止
  if (busy) return;
  busy = { key }; renderAll(); renderDialog();
  setTimeout(() => { busy = null; fn(); renderAll(); renderDialog(); }, ms);
}
function hit(key) { if (key in coverage && !coverage[key]) { coverage[key] = true; renderCoverage(); } }
```

- **カバレッジ項目は設計上の遷移・ガードと1:1**。操作で `hit()`、ガードの
  disabled表示は該当stateの描画時に `hit()` (観測ベース)。
- 描画は全面再描画 (`renderAll()`)。**フォーム状態 (checkbox等) は再描画で消える**
  ので、描画前に現在値を読んで復元する。
- 遷移ログ: 先頭挿入・タイムスタンプ付き。副作用 (通知・ジョブ取消) も1行で残す。
- 障害注入はcheckbox、異常系再現は専用ボタン (「(シミュレーション)」明示)。
- ダイアログの説明はテキストでなく**遷移ビジュアル** (before→afterのフラットな
  タグ2行。ボタンに見える塗り・枠は使わない — 押せると誤認される)。

## 検証つき納品

スクショ・動画が要るときは playwright でheadlessキャプチャ
(references/verify-round.md のスニペット)。2x撮影→配置先で1/2。
Figmaボード化は figma-shot-board スキルへ。
