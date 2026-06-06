# chrome-use JavaScript recipes

WHEN TO READ: load this when you need ready-made extraction or interaction snippets,
or the worked X/Twitter example. Each recipe is the JS you feed to
`chrome-use.sh run --js -` (or save to a file and pass the path). End extraction
snippets with a string (`JSON.stringify(...)` for structured data) so AppleScript
returns it cleanly on stdout.

## Conventions

- Results are returned as the value of the final expression. Wrap multi-statement
  logic in an IIFE: `(function(){ ...; return X; })()`.
- For structured output, `return JSON.stringify(obj)` and parse on the bash side.
- Selectors with single quotes need escaping; prefer double quotes inside JS and
  single quotes for `--wait` selectors (the helper wraps `--wait` in single quotes).

## Extraction

Visible text of the page:

```js
document.body.innerText
```

innerText of a specific selector:

```js
(document.querySelector('main')||document.body).innerText
```

All links (href + text), as JSON:

```js
JSON.stringify([...document.querySelectorAll('a[href]')].map(a=>({href:a.href,text:a.innerText.trim()})))
```

All image URLs:

```js
JSON.stringify([...document.images].map(i=>i.currentSrc||i.src).filter(Boolean))
```

A table to rows:

```js
JSON.stringify([...document.querySelectorAll('table tr')].map(tr=>[...tr.children].map(td=>td.innerText.trim())))
```

Page metadata:

```js
JSON.stringify({title:document.title,url:location.href,desc:(document.querySelector('meta[name=description]')||{}).content||''})
```

## Interaction

Click the first element matching a selector:

```js
(function(){var e=document.querySelector('button[type=submit]');if(!e)return 'not found';e.click();return 'clicked';})()
```

Set an input value and fire events React/Vue listen for:

```js
(function(){var el=document.querySelector('input[name=q]');if(!el)return 'no input';
var set=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
set.call(el,'hello world');
el.dispatchEvent(new Event('input',{bubbles:true}));
el.dispatchEvent(new Event('change',{bubbles:true}));
return el.value;})()
```

Submit a form:

```js
(function(){var f=document.querySelector('form');if(!f)return 'no form';f.requestSubmit?f.requestSubmit():f.submit();return 'submitted';})()
```

Select an option:

```js
(function(){var s=document.querySelector('select#country');if(!s)return 'no select';
s.value='JP';s.dispatchEvent(new Event('change',{bubbles:true}));return s.value;})()
```

Scroll to the bottom once (call repeatedly between runs to lazy-load):

```js
(function(){window.scrollTo(0,document.body.scrollHeight);return document.body.scrollHeight;})()
```

Wait-for-selector inside one run (returns when present or after ~maxMs):

```js
// prefer the helper's --wait flag; use this only when you need it inline
(async function(){var sel='[data-testid="cellInnerDiv"]';for(var i=0;i<30;i++){if(document.querySelector(sel))return 'present';await new Promise(r=>setTimeout(r,300));}return 'timeout';})()
```

Note: Chromium's `execute javascript` returns the value synchronously; an async/Promise
result may come back as `[object Promise]`. For awaited results, keep the wait loop in
AppleScript (the `--wait` flag) rather than in JS, or poll across multiple `run` calls.

## Infinite-scroll collection pattern (across multiple runs)

1. `run --js -` with the extraction snippet to grab what's currently rendered.
2. `run --js -` with the scroll snippet.
3. Repeat 1-2 until the count stops growing or you have enough; dedupe in bash.

This avoids long-running async JS and keeps each `run` fast and observable.

## Worked example: X/Twitter thread extraction

The example that motivated this skill. Save as a file and run with `--url` + `--wait`:

```js
(function(){
  var arts=[].slice.call(document.querySelectorAll('article'));
  return arts.map(function(a,i){
    var who=(a.querySelector('[data-testid="User-Name"]')||{}).innerText||'';
    who=who.replace(/\n+/g,' ').trim();
    var tEl=a.querySelector('[data-testid="tweetText"]');
    var t=tEl?tEl.innerText:'';
    var timeEl=a.querySelector('time');
    var tm=timeEl?(timeEl.getAttribute('datetime')||''):'';
    var imgs=[].slice.call(a.querySelectorAll('[data-testid="tweetPhoto"] img'))
      .map(function(im){return im.src;}).join(' , ');
    return '=== ARTICLE '+(i+1)+' ===\n'+who+'\n'+tm+(imgs?('\nIMAGES: '+imgs):'')+'\n\n'+t;
  }).join('\n\n##########\n\n');
})();
```

Invocation:

```bash
scripts/chrome-use.sh run \
  --url "x.com/USER/status/ID" \
  --wait 'article [data-testid="tweetText"]' \
  --js /path/to/xtweet.js
```

Scroll first (repeat the scroll recipe) to pull in more of a long thread before
extracting. This is an *example application of the generic recipes*, not a maintained
site-specific extractor — X's DOM (`data-testid` values) changes over time; adjust
selectors if it breaks.

## Clipboard fallback (when the JS-from-Apple-Events toggle is unavailable)

If the toggle truly cannot be enabled, drive extraction through the DevTools console
instead and read the clipboard:

1. Ask the user to open the target tab and DevTools console (Cmd+Option+J).
2. Have them paste a snippet ending in `copy(...)`, e.g.:

   ```js
   copy([...document.querySelectorAll('article')].map(a=>{
     var w=(a.querySelector('[data-testid="User-Name"]')||{}).innerText||'';
     var t=(a.querySelector('[data-testid="tweetText"]')||{}).innerText||'';
     return w.replace(/\n+/g,' ')+'\n'+t;
   }).filter(x=>x.trim()).join('\n\n----\n\n'))
   ```

3. Read it on the bash side: `pbpaste`.

`copy()` is a DevTools console helper and is reliable regardless of the AppleScript
toggle.
