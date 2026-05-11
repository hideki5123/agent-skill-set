# Site Template Guide

このスキルで生成するサイトの骨格と、過去の運用で実際に踏んだ落とし穴の対処。

## ファイル構成

```
<output-dir>/
├── index.html       # 1 ページで完結
├── styles.css       # レスポンシブ前提
└── script.js        # 任意。インタラクティブな確認 UI 等
```

シンプルなら 3 ファイルで完結。バンドラは使わない (生 HTML/CSS/JS)。Python http.server で配信する前提。

## index.html の骨格テンプレート

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{topic} をやさしく解説</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <header class="hero">
    <div class="hero-inner">
      <p class="kicker">{ソース名} を日本語で</p>
      <h1>{topic} を{形容詞}解説</h1>
      <p class="subtitle">{1-2 行のサブタイトル}</p>
      <p class="source">原文: <a href="{url}" target="_blank" rel="noopener">{url}</a></p>
    </div>
  </header>
  <div class="layout">
    <aside class="toc">
      <p class="toc-title">目次</p>
      <ol>
        <li><a href="#sec1">セクション 1</a></li>
      </ol>
    </aside>
    <main>
      <section id="sec1">
        <h2>① セクション 1</h2>
        <p>...</p>
      </section>
    </main>
  </div>
  <script src="script.js"></script>
</body>
</html>
```

## CSS の必須要素

### 1. type-scale を `clamp()` でビューポート連動に

```css
.hero h1 { font-size: clamp(24px, 5.5vw, 44px); }
h2 { font-size: clamp(19px, 3.6vw, 26px); }
h3 { font-size: clamp(15px, 2.4vw, 17px); }
pre { font-size: clamp(11px, 2.1vw, 13px); }
```

### 2. TOC を画面幅で 1-2 列切り替え

```css
.toc ol { columns: 1; }                       /* default: PC 1 列 */
@media (max-width: 900px) { .toc ol { columns: 2; } }
@media (max-width: 480px) { .toc ol { columns: 1; } }
```

### 3. table と pre は横スクロール許可

```css
.table-wrap, pre { overflow-x: auto; -webkit-overflow-scrolling: touch; }
table.modes { min-width: 480px; }
```

### 4. SVG diagram は `min-width` + `overflow-x: auto`

```css
.diagram { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.diagram svg { width: 100%; min-width: 640px; height: auto; display: block; }
```

狭い画面では横スクロールさせる。スマホで文字が潰れて読めないよりは、横スクロールできて読める方を選ぶ。

### 5. playground (インタラクティブ UI) は段組を画面幅で切り替え

```css
.playground { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
@media (max-width: 800px) { .playground { grid-template-columns: 1fr; } }
@media (max-width: 560px) {
  .play-controls .control {
    grid-template-columns: 1fr 56px;
    grid-template-rows: auto auto;
  }
  .play-controls label { grid-column: 1 / -1; grid-row: 1; }
  .play-controls input[type="range"],
  .play-controls select { grid-column: 1; grid-row: 2; }
  .play-controls .val { grid-column: 2; grid-row: 2; }
}
```

---

## SVG diagram の落とし穴

過去の運用で実際に踏んだもの。

### 落とし穴 1: テキストが viewBox 端で切れる

**症状**: `<text x="600" y="222">τ ≈ 0.32 (...)</text>` のような要素が、viewBox 幅 800 を超えて伸びる。SVG はデフォルトで `overflow: hidden` のため、viewBox の外側はクリップされる。

**対策**:

1. すべての `<text>` の終端 (x + 文字数 × 推定文字幅) が viewBox 幅以内に収まるよう、座標を計算して配置を決める
2. 長い説明文は左寄せ (x = 40 程度) から始める
3. すべての `<text>` に明示的に `font-size` 属性を指定する (デフォルト 16px に依存しない)
4. text-anchor の選択も注意 — 「end」アンカーなら x は文字の右端
5. 配置に迷ったら、viewBox を縦に拡大 (`<svg viewBox="0 0 800 320">`) して、説明文を別行に逃がす

### 落とし穴 2: モバイルで文字が潰れて読めない

**症状**: viewBox 800 × 200 の SVG を 320px 幅の画面で表示すると、テキストが 5-6px に縮んで読めない。

**対策**: `.diagram svg { min-width: 640px; }` を当てて、足りない画面は親要素の `overflow-x: auto` で横スクロールさせる。これは「全部見える + 文字微小」より「読めるサイズ + 横スクロール」の方が UX 上は望ましいという判断。

### 落とし穴 3: フォントサイズ未指定

SVG `<text>` の `font-size` を未指定にすると、ブラウザの SVG デフォルト (通常 16px) になり、CSS の clamp 等は効かない。常に属性で指定する:

```svg
<text x="40" y="200" font-size="14" fill="#333">τ の意味:</text>
```

---

## script.js (プレイグラウンド系) の規約

### 不正値を「警告」しすぎない

スライダーの組み合わせ次第で物理的にあり得ない値 (例: 合計 > 1 のとき残り変数が負) になるケースは、「警告 + 式どおりの結果を表示」が正解。clamp して綺麗な数字に直すと、教育用途では式の意味が破綻する。

```javascript
// NG: clamp して綺麗に見せる
const safe = Math.max(value, 0);
display = safe;  // 式が破綻する

// OK: 計算は式どおり、表示バーだけ視覚的に clamp、警告を併記
display = actualValue;                            // 式どおり
bar.style.width = clamp(actualValue, 0, 1) * 100 + '%';
if (invalid) showWarning(actualValue);
```

### アクセシビリティの最低要件

- `<label>` には必ず `for="..."` を付ける
- 動的に変わる結果領域には `aria-live="polite"` を付ける
- スライダーや select は `tabindex` の自然順序に従う

### 構成スタイル

- IIFE で囲む: `(function () { ... })();`
- DOM 取得を上でまとめてキャッシュ
- `update()` 関数で「入力 → 計算 → 表示」の一方向更新
- イベントリスナーは forEach でまとめて登録

```javascript
(function () {
  const a0 = document.getElementById('alpha0');
  const out = document.getElementById('p-result');

  function update() {
    const v = parseFloat(a0.value);
    out.textContent = v.toFixed(2);
  }

  [a0].forEach(el => {
    el.addEventListener('input', update);
    el.addEventListener('change', update);
  });

  update();
})();
```

---

## SVG diagram を描くときの座標計算ノート

viewBox 0 0 800 220 の場合、文字数からおおまかな終端 x を計算する:

| 文字種 | 推定幅 (font-size=14 のとき) |
|---|---|
| 半角英数 | 約 7-8px |
| 半角記号 / カッコ | 約 4-6px |
| 全角ひらがな・カタカナ・漢字 | 約 14px |
| 半角スペース | 約 4px |

例: 「τ ≈ 0.32 (ステージ 2 の 32% まで進んだ)」を font-size 14 で書くと:

- `τ ≈ 0.32 ` ≈ 9 文字 × 7 = 63
- `(ステージ 2 の 32% まで進んだ)` ≈ Japanese 8 文字 × 14 + 半角 6 文字 × 7 + 記号 4 文字 × 5 = 174
- 合計 ≈ 237px

x=40 から始めれば終端 ≈ 277。viewBox 800 内に余裕で収まる。

迷ったら font-size を明示し、テキスト幅を保守的に見積もって 100-150px の余白を確保する。
