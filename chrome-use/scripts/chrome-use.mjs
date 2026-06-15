#!/usr/bin/env node
// chrome-use — drive the user's already-running, LOGGED-IN Chrome on demand via
// the Chrome DevTools Protocol, with ZERO idle residency.
//
// Each invocation spawns `npx chrome-devtools-mcp@<pin> --autoConnect` as a
// short-lived subprocess, speaks the MCP stdio protocol (newline-delimited
// JSON-RPC) to run the requested tool calls against the real logged-in Chrome,
// then kills the subprocess. Nothing stays resident between commands or between
// Claude sessions — unlike registering the MCP server globally.
//
// Requires (one-time, see `check`): Chrome 144+ running, and local remote
// debugging enabled once at chrome://inspect/#remote-debugging.
//
// Zero npm dependencies: only Node builtins. Node is already required because
// the MCP server itself is a Node package (npx), so the client is Node too —
// no extra toolchain.
//
// Subcommands:
//   check
//   run    [--url URL] [--new-tab] [--wait TEXT]... [--js FILE|-] [--expr]
//          [--snapshot] [--screenshot PATH] [--full-page] [--out PATH]
//   snapshot   [--out PATH] [--verbose]
//   screenshot [--out PATH] [--full-page] [--format png|jpeg|webp]
//   tools
//   call   <tool> [--params JSON | --params-file PATH | --params -]

import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';

const MCP_VERSION = process.env.CHROME_DEVTOOLS_MCP_VERSION || '1.2.0';
const MCP_CHANNEL = process.env.CHROME_DEVTOOLS_MCP_CHANNEL || ''; // canary|dev|beta|stable
const CALL_TIMEOUT_MS = Number(process.env.CHROME_USE_TIMEOUT_MS || 60000);

// ── minimal one-shot MCP stdio client ───────────────────────────────────────
class Mcp {
  constructor() {
    const args = ['-y', `chrome-devtools-mcp@${MCP_VERSION}`, '--autoConnect', '--no-usage-statistics'];
    if (MCP_CHANNEL) args.push('--channel', MCP_CHANNEL);
    this.srv = spawn('npx', args, { stdio: ['pipe', 'pipe', 'pipe'] });
    this.buf = '';
    this.pending = new Map();
    this.idc = 0;
    this.stderr = '';
    this.srv.stderr.on('data', (d) => { this.stderr += d.toString(); });
    this.srv.stdout.on('data', (d) => this._onData(d));
    this.srv.on('exit', () => {
      for (const [, rej] of this.pending) rej.reject(new Error('mcp server exited\n' + this.stderr.trim()));
      this.pending.clear();
    });
  }
  _onData(d) {
    this.buf += d.toString();
    let i;
    while ((i = this.buf.indexOf('\n')) >= 0) {
      const line = this.buf.slice(0, i).trim();
      this.buf = this.buf.slice(i + 1);
      if (!line) continue;
      let msg;
      try { msg = JSON.parse(line); } catch { continue; }
      if (msg.id != null && this.pending.has(msg.id)) {
        const p = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        p.resolve(msg);
      }
    }
  }
  _rpc(method, params) {
    const id = ++this.idc;
    const payload = JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n';
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`timeout after ${CALL_TIMEOUT_MS}ms waiting for ${method}`));
      }, CALL_TIMEOUT_MS);
      this.pending.set(id, { resolve: (m) => { clearTimeout(timer); resolve(m); }, reject: (e) => { clearTimeout(timer); reject(e); } });
      this.srv.stdin.write(payload);
    });
  }
  _notify(method, params) {
    this.srv.stdin.write(JSON.stringify({ jsonrpc: '2.0', method, params }) + '\n');
  }
  async init() {
    await this._rpc('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'chrome-use', version: '2.0.0' },
    });
    this._notify('notifications/initialized', {});
  }
  async listTools() {
    const r = await this._rpc('tools/list', {});
    return (r.result && r.result.tools) || [];
  }
  // Returns { text, isError }. Throws only on transport-level errors.
  async call(name, args) {
    const r = await this._rpc('tools/call', { name, arguments: args || {} });
    if (r.error) return { text: r.error.message || JSON.stringify(r.error), isError: true };
    const content = (r.result && r.result.content) || [];
    const text = content.filter((c) => c.type === 'text').map((c) => c.text).join('\n');
    return { text, isError: !!(r.result && r.result.isError) };
  }
  close() { try { this.srv.kill('SIGTERM'); } catch { /* ignore */ } }
}

// ── helpers ──────────────────────────────────────────────────────────────────
function readSource(spec) {
  if (spec === '-') return readFileSync(0, 'utf8');
  return readFileSync(spec, 'utf8');
}

// chrome-devtools-mcp's evaluate_script expects a FUNCTION declaration string,
// e.g. `() => { return document.title }`. Pass functions through unchanged;
// wrap a bare expression so callers can also hand us `document.title`.
function asFunction(src, forceExpr) {
  const t = src.trim();
  const looksLikeFn = /^(async\s+)?(function\b|\(|[A-Za-z_$][\w$]*\s*=>)/.test(t);
  if (looksLikeFn && !forceExpr) return src;
  if (forceExpr) return `() => { return (${t}\n) }`;
  // Heuristic: contains a statement-y token → treat as a function body.
  if (/[;{]/.test(t) || /\breturn\b/.test(t)) return `() => {\n${src}\n}`;
  return `() => { return (${t}\n) }`;
}

function connectionGuidance(detail) {
  return [
    '[chrome-use] Chrome に接続できませんでした。',
    '  確認事項:',
    '   1. Chrome (144+) が起動しているか（普段のログイン済みウィンドウ）',
    '   2. chrome://inspect/#remote-debugging で「ローカルのリモートデバッグ接続を許可」を一度有効化したか',
    '   3. 接続時に Chrome が出す許可ダイアログを承認したか',
    '   4. 本体がスリープしていないか（ディスプレイOFFは可、システムスリープは不可）',
    detail ? '  詳細: ' + detail.split('\n').slice(0, 4).join(' / ') : '',
  ].filter(Boolean).join('\n');
}

function parseFlags(argv, spec) {
  // spec: { name: 'string'|'bool'|'array' }
  const out = {};
  for (const [k, v] of Object.entries(spec)) if (v === 'array') out[k] = [];
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const kind = spec[key];
      if (!kind) { rest.push(a); continue; }
      if (kind === 'bool') out[key] = true;
      else if (kind === 'array') out[key].push(argv[++i]);
      else out[key] = argv[++i];
    } else rest.push(a);
  }
  return { out, rest };
}

function out(text, file) {
  if (file) { writeFileSync(file, text); process.stderr.write(`[chrome-use] 出力を ${file} に保存しました\n`); }
  else process.stdout.write(text + (text.endsWith('\n') ? '' : '\n'));
}

// ── subcommands ───────────────────────────────────────────────────────────────
async function cmdTools() {
  const m = new Mcp();
  try {
    await m.init();
    const tools = await m.listTools();
    console.log(`# ${tools.length} tools`);
    for (const t of tools) console.log(`- ${t.name}: ${(t.description || '').split('\n')[0]}`);
  } finally { m.close(); }
}

async function cmdCheck() {
  const m = new Mcp();
  try {
    await m.init();
    const r = await m.call('list_pages', {});
    if (r.isError) { console.error(connectionGuidance(r.text)); process.exitCode = 1; return; }
    console.log('[OK] Chrome に接続できました。開いているページ:');
    console.log(r.text);
    console.log('chrome-use run / snapshot / screenshot が使えます。');
  } catch (e) {
    console.error(connectionGuidance(String(e.message || e)));
    process.exitCode = 1;
  } finally { m.close(); }
}

// Run a sequence of tool calls in ONE connection. Because each chrome-use
// invocation is a fresh CDP session, uid-based tools (click/fill from a
// take_snapshot) only stay valid within a single session — batch keeps a
// snapshot→click→fill→submit chain together. Input: JSON array of
// {tool, args} (or {name, arguments}). Each step's text result is printed,
// separated by a marker; a failing step stops the batch.
async function cmdBatch(argv) {
  const { out: f } = parseFlags(argv, { steps: 'string', 'steps-file': 'string', out: 'string' });
  let raw;
  if (f['steps-file']) raw = readFileSync(f['steps-file'], 'utf8');
  else if (f.steps === '-' || !f.steps) raw = readFileSync(0, 'utf8');
  else raw = f.steps;
  const steps = JSON.parse(raw);
  if (!Array.isArray(steps)) { console.error('[chrome-use] batch には {tool,args} の JSON 配列が必要です'); process.exit(2); }
  const m = new Mcp();
  const chunks = [];
  try {
    await m.init();
    for (let i = 0; i < steps.length; i++) {
      const s = steps[i];
      const name = s.tool || s.name;
      const args = s.args || s.arguments || {};
      const r = await m.call(name, args);
      chunks.push(`### step ${i + 1}: ${name}${r.isError ? ' [ERROR]' : ''}\n${r.text}`);
      if (r.isError) { process.exitCode = 1; break; }
    }
    out(chunks.join('\n\n'), f.out);
  } catch (e) {
    console.error(connectionGuidance(String(e.message || e)));
    process.exitCode = 1;
  } finally { m.close(); }
}

async function cmdCall(argv) {
  const tool = argv[0];
  if (!tool || tool.startsWith('--')) { console.error('[chrome-use] usage: call <tool> [--params JSON|--params-file F|--params -]'); process.exit(2); }
  const { out: f } = parseFlags(argv.slice(1), { params: 'string', 'params-file': 'string' });
  let args = {};
  if (f['params-file']) args = JSON.parse(readFileSync(f['params-file'], 'utf8'));
  else if (f.params === '-') args = JSON.parse(readFileSync(0, 'utf8'));
  else if (f.params) args = JSON.parse(f.params);
  const m = new Mcp();
  try {
    await m.init();
    const r = await m.call(tool, args);
    out(r.text);
    if (r.isError) process.exitCode = 1;
  } catch (e) { console.error('[chrome-use] ' + (e.message || e)); process.exitCode = 1; }
  finally { m.close(); }
}

async function cmdSnapshot(argv) {
  const { out: f } = parseFlags(argv, { out: 'string', verbose: 'bool' });
  const m = new Mcp();
  try {
    await m.init();
    const r = await m.call('take_snapshot', { verbose: !!f.verbose });
    if (r.isError) { console.error(connectionGuidance(r.text)); process.exitCode = 1; return; }
    out(r.text, f.out);
  } finally { m.close(); }
}

async function cmdScreenshot(argv) {
  const { out: f } = parseFlags(argv, { out: 'string', 'full-page': 'bool', format: 'string' });
  const path = f.out || 'screenshot.png';
  const m = new Mcp();
  try {
    await m.init();
    const r = await m.call('take_screenshot', { filePath: path, fullPage: !!f['full-page'], format: f.format || 'png' });
    if (r.isError) { console.error(connectionGuidance(r.text)); process.exitCode = 1; return; }
    process.stderr.write(`[chrome-use] スクリーンショットを ${path} に保存しました\n`);
    if (r.text) console.log(r.text);
  } finally { m.close(); }
}

async function cmdRun(argv) {
  const { out: f } = parseFlags(argv, {
    url: 'string', 'new-tab': 'bool', wait: 'array', js: 'string', expr: 'bool',
    snapshot: 'bool', screenshot: 'string', 'full-page': 'bool', out: 'string',
  });
  // Read JS up front (stdin can only be consumed once).
  let jsSrc = null;
  if (f.js) jsSrc = readSource(f.js);

  const m = new Mcp();
  try {
    await m.init();
    const fail = (r) => { console.error(connectionGuidance(r.text)); process.exitCode = 1; };

    if (f.url) {
      const r = f['new-tab']
        ? await m.call('new_page', { url: f.url })
        : await m.call('navigate_page', { type: 'url', url: f.url });
      if (r.isError) return fail(r);
    }
    if (f.wait && f.wait.length) {
      const r = await m.call('wait_for', { text: f.wait });
      if (r.isError) { console.error('[chrome-use] wait_for 失敗: ' + r.text); process.exitCode = 1; return; }
    }
    if (jsSrc != null) {
      const r = await m.call('evaluate_script', { function: asFunction(jsSrc, !!f.expr) });
      if (r.isError) { console.error('[chrome-use] evaluate_script 失敗: ' + r.text); process.exitCode = 1; return; }
      out(r.text, f.out);
    }
    if (f.snapshot) {
      const r = await m.call('take_snapshot', {});
      if (r.isError) return fail(r);
      out(r.text, f.out);
    }
    if (f.screenshot) {
      const r = await m.call('take_screenshot', { filePath: f.screenshot, fullPage: !!f['full-page'] });
      if (r.isError) return fail(r);
      process.stderr.write(`[chrome-use] スクリーンショットを ${f.screenshot} に保存しました\n`);
    }
    if (!f.url && jsSrc == null && !f.snapshot && !f.screenshot && (!f.wait || !f.wait.length)) {
      console.error('[chrome-use] run には少なくとも一つ指定が必要です: --url / --js / --snapshot / --screenshot / --wait');
      process.exitCode = 2;
    }
  } catch (e) {
    console.error(connectionGuidance(String(e.message || e)));
    process.exitCode = 1;
  } finally { m.close(); }
}

// ── dispatch ──────────────────────────────────────────────────────────────────
const [, , sub, ...rest] = process.argv;
const cmds = {
  check: () => cmdCheck(),
  run: () => cmdRun(rest),
  snapshot: () => cmdSnapshot(rest),
  screenshot: () => cmdScreenshot(rest),
  tools: () => cmdTools(),
  call: () => cmdCall(rest),
  batch: () => cmdBatch(rest),
};
if (!cmds[sub]) {
  process.stderr.write(`usage:
  chrome-use.mjs check
  chrome-use.mjs run [--url URL] [--new-tab] [--wait TEXT]... [--js FILE|-] [--expr] [--snapshot] [--screenshot PATH] [--full-page] [--out PATH]
  chrome-use.mjs snapshot [--out PATH] [--verbose]
  chrome-use.mjs screenshot [--out PATH] [--full-page] [--format png|jpeg|webp]
  chrome-use.mjs tools
  chrome-use.mjs call <tool> [--params JSON | --params-file PATH | --params -]
  chrome-use.mjs batch [--steps JSON | --steps-file PATH | --steps -] [--out PATH]
`);
  process.exit(2);
}
cmds[sub]().catch((e) => { console.error('[chrome-use] ' + (e && e.message || e)); process.exit(1); });
