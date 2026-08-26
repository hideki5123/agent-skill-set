# レビューラウンドの検証 (headless + 敵対的整合チェック)

WHEN TO READ: Phase 3 の各ラウンド。

## 1. headless実挙動検証 (playwright)

既存の playwright インストールを探して流用する (`find ~ -maxdepth 4 -type d
-name playwright -path '*node_modules*'`)。なければ `npx playwright` (初回は遅い)。

```bash
# 構文チェック (scriptブロック抽出→node --check)
python3 - file.html <<'PY'
import sys; src = open(sys.argv[1]).read()
s = src.index('<script>')+8; e = src.index('</script>')
open('/tmp/simcheck.js','w').write(src[s:e])
PY
node --check /tmp/simcheck.js
```

```js
// フロー検証の型 (page.click → waitForTimeout(遅延+α) → textContent断言)
const { chromium } = require('<playwrightのパス>');
const p = await (await chromium.launch()).newPage();
const errs = []; p.on('pageerror', e => errs.push(e.message));
await p.goto('file://...');
await p.click('button:has-text("Escalate")');
await p.waitForTimeout(1500);   // 疑似RPC遅延ぶん待つ
console.log(await p.textContent('#chip-mode'), errs);
```

キャプチャ: `deviceScaleFactor: 2` + 要素単位 `locator.screenshot()`、
動画は `newContext({ recordVideo: { dir } })` → `ctx.close()` 後に `video.path()`。

## 2. 敵対的整合チェック (検証agent)

1ラウンドにつき1 agent (大改修時は naturalize-ja 等と2並列)。**レビューのみ・
編集させない**。findingsは構造化 (severity: must/should/nit, location, issue, fix)
で受け、main loop が取捨して適用する。プロンプト雛形:

```
Read BOTH files: <spec> and <sim>. Adversarially verify that decisions <今回のD一覧>
are consistently applied across both, and no stale content contradicts them.
Do NOT edit files; return findings only (empty list if all good).

Check in particular:
1. Copy table vs mocks/simulator strings: every product UI string visible in either
   file has a matching copy-table row and vice versa; no leftover keys for removed things.
2. Decision log, guide cards, section decision boxes, diagrams, legends, and the
   simulator coverage list all agree with the decisions — no row still describing
   an abolished behavior.
3. Simulator logic consistency: guards unreachable states, coverage hits fire, etc.
4. (必要なら) 実コードとの照合: enum値・既存UIパターンをリポジトリで確認させる。
5. HTML sanity around edited regions (unclosed tags, orphan pins, broken aria-labels).
```

- 実コード照合を入れると「仕様に存在しない値」を検出できる (実績: 実在しない
  status値・親スペックと矛盾するCancel挙動)。
- findingsの1件目がmustなら反映→再公開。nitは任意採用でよいが、
  「全ストリング」整合系のnitは放置すると次巡でmustに化けるので早めに潰す。

## 3. 「効かない」報告への手順

1. headlessで報告手順を再現してみる (JSエラー捕捉付き)。
2. 再現しない場合はバグではなく**操作の罠**: 再描画による入力状態リセット、
   分かりにくい既存挙動 (別Request型が作られる等)、disabledの理由不提示を疑う。
3. 罠自体を設計で潰し (状態保持・ガードのUI先取り+理由表示)、Dとして記録。
