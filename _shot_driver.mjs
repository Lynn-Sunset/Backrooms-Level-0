import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME_CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
];
const CHROME = CHROME_CANDIDATES.find(p => existsSync(p));
if (!CHROME) { console.error('未找到 Chrome/Edge'); process.exit(4); }
console.log('using browser:', CHROME);

const URL = process.argv[2] || 'http://127.0.0.1:8000/index.html?shot=1&level=0';
const OUT = process.argv[3] || join(tmpdir(), 'backrooms_shot.png');
const PORT = 9334;
const profile = mkdtempSync(join(tmpdir(), 'bk-shot-'));

const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', '--enable-unsafe-swiftshader',
  '--use-angle=swiftshader', '--no-sandbox', '--no-first-run',
  '--no-default-browser-check', '--mute-audio', '--hide-scrollbars',
  `--window-size=1280,720`,
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, 'about:blank'
], { stdio: ['ignore', 'ignore', 'inherit'] });

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function createPage() {
  for (let i = 0; i < 60; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/new?${encodeURIComponent(URL)}`, { method: 'PUT' });
      return await res.json();
    } catch { await sleep(200); }
  }
  throw new Error('CDP /json/new unreachable');
}

const target = await createPage();
const ws = new WebSocket(target.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
const logs = [];
const shots = [];

function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const msgId = ++id;
    pending.set(msgId, { resolve, reject });
    ws.send(JSON.stringify({ id: msgId, method, params }));
  });
}

ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id) {
    const p = pending.get(msg.id);
    if (p) { pending.delete(msg.id); p.resolve(msg.result); }
    return;
  }
  if (msg.method === 'Runtime.consoleAPICalled') {
    const text = msg.params.args.map(a => a.value ?? a.description ?? '').join(' ');
    logs.push(text);
  } else if (msg.method === 'Runtime.exceptionThrown') {
    const d = msg.params.exceptionDetails;
    logs.push('[EXCEPTION] ' + (d.exception?.description ?? d.text));
  }
};

await new Promise(r => ws.onopen = r);
await send('Runtime.enable');
await send('Page.enable');
await send('Page.navigate', { url: URL });

// SwiftShader 软件渲染下 L0→L1→L2 全流程可能较慢（仓库/园林大量几何合并），放宽超时
const deadline = Date.now() + 150000;
while (Date.now() < deadline) {
  if (logs.some(l => l.includes('[SHOT] READY') || l.includes('[SHOT] FAILED'))) break;
  await sleep(250);
}
await sleep(400);
if (logs.some(l => l.includes('[SHOT] FAILED'))) {
  console.log('SHOT FAILED; logs:'); logs.forEach(l => console.log('  ', l));
  try { ws.close(); } catch {}
  chrome.kill(); process.exit(2);
}
const res = await send('Page.captureScreenshot', { format: 'png' });
writeFileSync(OUT, Buffer.from(res.data, 'base64'));
shots.push(OUT);

console.log('screenshot saved:', shots[0]);
console.log('--- all logs ---');
logs.forEach(l => console.log('  ' + l));
try { ws.close(); } catch {}
try { chrome.kill(); } catch {}
try { spawnSync('taskkill', ['/F', '/T', '/PID', String(chrome.pid)], { stdio: 'ignore' }); } catch {}
process.exit(shots.length ? 0 : 3);
