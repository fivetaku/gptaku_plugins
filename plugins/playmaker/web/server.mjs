#!/usr/bin/env node
// playmaker 웹 보기 — 화면을 그리지 않는 호스트(Paseo 등)용 실시간 보드.
// 의존성 없음. 127.0.0.1에만 열고, 시작할 때 받은 골 폴더 하나의 PLAN.md·PROGRESS.md만 읽는다(쓰지 않는다).
// Paseo에서는 골 작업 세션에 연결해 카드에서 그 세션으로 메시지를 보낼 수 있다(`paseo send`).
// 사용: node server.mjs --dir <골 폴더> [--port 4777] [--port-file <경로>] [--paseo <paseo CLI> --project <에이전트 cwd> --agent <ID>]
import { createServer } from 'node:http'
import { execFile } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { readFileSync, statSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { resolve } from 'node:path'
import { parseBoard, summaryLine } from '../hooks/parse.ts'

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => (a.startsWith('--') ? [...acc, [a.slice(2), all[i + 1]]] : acc), []),
)
const DIR = resolve(args.dir ?? process.cwd())
const FIRST = Number(args.port ?? 4777)
const PASEO = args.paseo || ''
const PROJECT = args.project ? resolve(args.project) : ''
const TOKEN = randomBytes(16).toString('hex') // 이 페이지에서 온 요청만 메시지를 보낼 수 있게
const IDLE_MS = 6 * 3600 * 1000 // 6시간 아무도 안 보면 스스로 종료
let lastHit = Date.now()
let port = FIRST
let link = args.agent ? { agentId: args.agent, by: 'start' } : null
const sent = [] // 보낸 메시지 기록 (최근 30건, 메모리에만)

function board() {
  const plan = readFileSync(`${DIR}/PLAN.md`, 'utf8')
  const progress = readFileSync(`${DIR}/PROGRESS.md`, 'utf8')
  const b = parseBoard(DIR, plan, progress, Date.now())
  const touched = Math.max(statSync(`${DIR}/PLAN.md`).mtimeMs, statSync(`${DIR}/PROGRESS.md`).mtimeMs)
  return { ...b, summary: summaryLine(b), touched }
}

const run = (cmd, argv, ms = 8000) => new Promise((ok, fail) =>
  execFile(cmd, argv, { timeout: ms, maxBuffer: 8 << 20 }, (e, out, err) => (e ? fail(new Error(String(err || e.message).trim().slice(0, 300))) : ok(out))))

// 같은 프로젝트에서 도는 Paseo 세션 목록 (4초 캐시)
let agentsCache = { at: 0, list: [] }
async function agents() {
  if (!PASEO) return []
  if (Date.now() - agentsCache.at < 4000) return agentsCache.list
  try {
    const all = JSON.parse(await run(PASEO, ['ls', '--json']))
    const home = homedir()
    const mine = all.filter(a => {
      if (a.status === 'closed') return false
      const cwd = resolve(String(a.cwd ?? '').replace(/^~(?=\/|$)/, home))
      return PROJECT ? cwd === PROJECT : DIR === cwd || DIR.startsWith(cwd + '/')
    })
    agentsCache = { at: Date.now(), list: mine.map(a => ({ id: a.id, shortId: a.shortId, name: a.name, status: a.status })) }
  } catch { agentsCache.at = Date.now() }
  return agentsCache.list
}

async function linkInfo() {
  if (!PASEO) return { paseo: false }
  const list = await agents()
  const cur = link && list.find(a => a.id === link.agentId || a.id.startsWith(link.agentId) || a.shortId === link.agentId)
  return { paseo: true, link: cur ? { ...cur } : null, agents: list }
}

function setLink(agentId, mode) {
  if (!agentId) return
  // auto(세션 시작): 연결이 없거나 연결된 세션이 사라졌을 때만. explicit(/playmaker)·user(화면에서 선택): 항상 바꾼다
  if (mode === 'auto' && link && agentsCache.list.some(a => a.id === link.agentId)) return
  link = { agentId, by: mode }
}

async function send(text, task, label) {
  const info = await linkInfo()
  if (!info.link) throw new Error('연결된 세션이 없습니다')
  await run(PASEO, ['send', info.link.id, '--no-wait', '--json', '--prompt', text], 15000)
  sent.unshift({ at: Date.now(), to: info.link.name, task, label, text })
  sent.length = Math.min(sent.length, 30)
  return info.link
}

function body(req) {
  return new Promise((ok, fail) => {
    let s = ''
    req.on('data', c => { s += c; if (s.length > 64 << 10) { fail(new Error('too large')); req.destroy() } })
    req.on('end', () => { try { ok(s ? JSON.parse(s) : {}) } catch (e) { fail(e) } })
  })
}

// 쓰기 요청 검사: 이 서버가 내준 토큰 + 같은 출처(다른 웹페이지가 몰래 보내는 것 차단)
function allowed(req) {
  const origin = req.headers.origin
  if (origin && origin !== `http://127.0.0.1:${port}`) return false
  return req.headers['x-playmaker-token'] === TOKEN
}

const LOGO = readFileSync(new URL('../assets/logo.svg', import.meta.url))

const PAGE = `<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>playmaker</title>
<link rel="icon" href="logo.svg" type="image/svg+xml">
<style>
:root{--bg:#0f1011;--bar:#0f1011;--lane:#141517;--card:#1b1c1f;--card-h:#212226;--line:#232428;--line2:#2e2f35;
--fg:#eeeff1;--fg2:#c4c6cc;--dim:#8a8f98;--faint:#5d6169;--todo:#8a8f98;--doing:#f2c94c;--wait:#f2994a;--done:#5e6ad2;--focus:#5e6ad2;
--font:"Inter Variable","Inter",-apple-system,BlinkMacSystemFont,"Pretendard","Apple SD Gothic Neo",system-ui,sans-serif}
:root.light{--bg:#fcfcfd;--bar:#fcfcfd;--lane:#f4f5f8;--card:#fff;--card-h:#fbfbfc;--line:#e6e7eb;--line2:#d9dbe0;--fg:#1b1c1f;--fg2:#3c3f45;--dim:#6b6f76;--faint:#a0a4ab;--todo:#a0a4ab;--doing:#e2b203;--wait:#e8790d}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--fg)}
body{font:13px/1.45 var(--font);-webkit-font-smoothing:antialiased;font-feature-settings:"cv11","ss01";display:flex;flex-direction:column}
button{font:inherit;color:inherit}
/* 상단 바 */
.hd{height:44px;flex:none;display:flex;align-items:center;gap:8px;padding:0 12px;border-bottom:1px solid var(--line);background:var(--bar)}
.hd .logo{width:20px;height:20px;flex:none}
.crumb{display:flex;align-items:center;gap:6px;min-width:0;color:var(--dim)}.crumb b{color:var(--fg);font-weight:500}.crumb .goal{color:var(--fg2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sp{flex:1}
.live{display:flex;align-items:center;gap:6px;color:var(--faint);font-size:12px;white-space:nowrap}.live i{width:6px;height:6px;border-radius:50%;background:#4cb782}.live.off i{background:#eb5757}.live.off{color:#eb5757}
.vs{display:inline-flex;border:1px solid var(--line2);border-radius:6px;overflow:hidden}
.vs button{all:unset;cursor:pointer;display:flex;align-items:center;gap:5px;height:24px;padding:0 8px;color:var(--dim);font-size:12px}.vs button+button{border-left:1px solid var(--line2)}
.vs button.on{background:var(--card-h);color:var(--fg)}.vs svg{width:14px;height:14px}
.ib{all:unset;cursor:pointer;height:26px;padding:0 8px;border-radius:6px;color:var(--dim);font-size:12px;display:flex;align-items:center;gap:6px;border:1px solid transparent}.ib:hover{background:var(--card-h);color:var(--fg)}.ib.on{color:var(--fg);border-color:var(--line2)}
kbd{font:10.5px var(--font);color:var(--faint);border:1px solid var(--line2);border-radius:4px;padding:0 4px;line-height:15px}
/* 마일스톤 탭 */
.tabs{flex:none;display:flex;align-items:center;gap:4px;padding:8px 12px;border-bottom:1px solid var(--line);overflow-x:auto;scrollbar-width:none}
.tab{all:unset;cursor:pointer;display:flex;align-items:center;gap:6px;height:26px;padding:0 9px;border-radius:6px;color:var(--dim);white-space:nowrap;border:1px solid transparent}
.tab:hover{background:var(--card-h);color:var(--fg2)}.tab.on{background:var(--card);border-color:var(--line2);color:var(--fg)}
.tab .p{color:var(--faint);font-variant-numeric:tabular-nums}.tab svg{flex:none}
.prog{margin-left:auto;display:flex;align-items:center;gap:7px;color:var(--dim);white-space:nowrap;font-variant-numeric:tabular-nums;padding-left:12px}
.warn{margin:8px 12px 0;padding:7px 10px;border-radius:6px;font-size:12px;color:var(--fg2);background:color-mix(in srgb,var(--wait) 10%,transparent);border:1px solid color-mix(in srgb,var(--wait) 28%,transparent)}
main{flex:1;overflow:auto}
/* 보드 */
.board{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;padding:10px 12px 16px;align-items:start}
@media (max-width:560px){.board{grid-template-columns:1fr}.lane.doing{order:-1}}
.lane{background:var(--lane);border-radius:8px;padding:0 6px 6px;min-width:0}
.lh{display:flex;align-items:center;gap:8px;height:36px;padding:0 6px;font-weight:500;color:var(--fg)}
.lh .c{color:var(--faint);font-weight:400;font-variant-numeric:tabular-nums}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:9px 11px 10px;margin-bottom:6px;box-shadow:0 1px 1px rgba(0,0,0,.12);transition:background .12s,border-color .12s}
.card:hover{background:var(--card-h);border-color:var(--line2)}
.r1{display:flex;align-items:center;gap:6px;color:var(--faint);font-size:12px;font-variant-numeric:tabular-nums;margin-bottom:4px}.r1 svg{margin-left:auto}
.ti{color:var(--fg);font-weight:500;line-height:1.4;word-break:keep-all;overflow-wrap:anywhere}
.card.done .ti{color:var(--dim)}.card.inferred{border-style:dashed}
.props{display:flex;flex-wrap:wrap;gap:4px;margin-top:8px}
.pill{display:inline-flex;align-items:center;gap:5px;height:20px;padding:0 7px;border:1px solid var(--line2);border-radius:999px;color:var(--dim);font-size:11.5px;white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
.pill.urgent{color:var(--wait);border-color:color-mix(in srgb,var(--wait) 40%,var(--line2))}
.empty{color:var(--faint);font-size:12px;padding:4px 6px 8px}
.fold{display:flex;align-items:center;gap:8px;height:32px;padding:0 6px;color:var(--fg2)}.fold .c{margin-left:auto;color:var(--faint)}
/* 리스트 */
.list{padding:6px 0 16px}
.gh{display:flex;align-items:center;gap:8px;height:36px;padding:0 14px;font-weight:500;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.gh .c{color:var(--faint);font-weight:400}.gh .pc{margin-left:auto;color:var(--dim);font-weight:400;font-variant-numeric:tabular-nums}
.row{display:flex;align-items:center;gap:10px;height:38px;padding:0 14px;border-bottom:1px solid var(--line);color:var(--fg2)}
.row:hover{background:var(--card-h)}.row .id{color:var(--faint);width:52px;flex:none;font-variant-numeric:tabular-nums}
.row .tx{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--fg)}.row.done .tx{color:var(--dim)}
.foot{flex:none;display:flex;gap:14px;align-items:center;height:30px;padding:0 12px;border-top:1px solid var(--line);color:var(--faint);font-size:11.5px;white-space:nowrap;overflow:hidden}
.foot .d{margin-left:auto;overflow:hidden;text-overflow:ellipsis}
.hidden{display:none!important}
.card{cursor:pointer}.card.sel{border-color:var(--focus);box-shadow:0 0 0 1px var(--focus)}.row{cursor:pointer}
/* 연결된 세션 */
.lk{position:relative}
.lkb{all:unset;cursor:pointer;display:flex;align-items:center;gap:6px;height:26px;padding:0 8px;border-radius:6px;border:1px solid var(--line2);color:var(--fg2);font-size:12px;max-width:220px}
.lkb:hover{background:var(--card-h)}.lkb .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dot{width:7px;height:7px;border-radius:50%;flex:none;background:var(--todo)}.dot.running{background:var(--doing);box-shadow:0 0 0 3px color-mix(in srgb,var(--doing) 25%,transparent)}.dot.idle{background:#4cb782}.dot.none{background:transparent;border:1px dashed var(--faint)}
.menu{position:absolute;right:0;top:32px;z-index:20;width:300px;max-height:360px;overflow:auto;background:var(--card);border:1px solid var(--line2);border-radius:8px;box-shadow:0 12px 32px rgba(0,0,0,.35);padding:4px}
.menu .mh{padding:6px 8px;color:var(--faint);font-size:11.5px}
.menu button{all:unset;cursor:pointer;display:flex;align-items:center;gap:8px;width:100%;box-sizing:border-box;padding:6px 8px;border-radius:5px;color:var(--fg2);font-size:12.5px}
.menu button:hover{background:var(--card-h);color:var(--fg)}.menu button .nm{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.menu button .ck{color:var(--focus)}
/* 상세 패널 (Linear 이슈 미리보기) */
.peek{position:fixed;top:0;right:0;bottom:0;width:min(400px,100%);z-index:30;background:var(--card);border-left:1px solid var(--line2);box-shadow:-16px 0 40px rgba(0,0,0,.35);display:flex;flex-direction:column;transform:translateX(100%);transition:transform .18s ease}
.peek.on{transform:none}
.ph{display:flex;align-items:center;gap:8px;height:44px;padding:0 12px;border-bottom:1px solid var(--line);color:var(--faint);font-size:12px}
.ph .x{all:unset;cursor:pointer;margin-left:auto;width:24px;height:24px;display:grid;place-items:center;border-radius:5px;color:var(--dim)}.ph .x:hover{background:var(--card-h);color:var(--fg)}
.pb{flex:1;overflow:auto;padding:14px 16px}
.pt{font-size:16px;font-weight:600;line-height:1.4;margin:0 0 12px;word-break:keep-all}
.kv{display:grid;grid-template-columns:72px 1fr;gap:8px 10px;align-items:center;font-size:12.5px;margin-bottom:16px}.kv span:nth-child(odd){color:var(--faint)}.kv .v{display:flex;align-items:center;gap:6px;color:var(--fg2)}
.sec{color:var(--faint);font-size:11.5px;font-weight:500;margin:14px 0 8px;text-transform:none}
.acts{display:flex;flex-direction:column;gap:6px}
.act{all:unset;cursor:pointer;display:flex;align-items:center;gap:8px;padding:8px 10px;border:1px solid var(--line2);border-radius:6px;color:var(--fg);font-size:12.5px}
.act:hover{background:var(--card-h);border-color:var(--faint)}.act.primary{border-color:color-mix(in srgb,var(--focus) 60%,var(--line2));background:color-mix(in srgb,var(--focus) 12%,transparent)}
.act small{margin-left:auto;color:var(--faint);font-size:11px}
.ta{width:100%;min-height:84px;resize:vertical;background:var(--bg);color:var(--fg);border:1px solid var(--line2);border-radius:6px;padding:8px 10px;font:13px/1.45 var(--font);outline:none}.ta:focus{border-color:var(--focus)}
.sendrow{display:flex;align-items:center;gap:8px;margin-top:6px}.sendrow .hint{color:var(--faint);font-size:11px}
.btn{all:unset;cursor:pointer;margin-left:auto;height:28px;padding:0 12px;border-radius:6px;background:var(--focus);color:#fff;font-size:12.5px;font-weight:500;display:flex;align-items:center}.btn[disabled]{opacity:.45;cursor:default}
.banner{display:flex;gap:8px;align-items:flex-start;padding:9px 10px;border-radius:6px;margin-bottom:12px;font-size:12px;color:var(--fg2);background:color-mix(in srgb,var(--focus) 10%,transparent);border:1px solid color-mix(in srgb,var(--focus) 35%,transparent)}.banner.busy{background:color-mix(in srgb,var(--doing) 9%,transparent);border-color:color-mix(in srgb,var(--doing) 30%,transparent)}.banner b{color:var(--fg);font-weight:500}
.act[disabled]{opacity:.45;cursor:default}.act .ok{margin-left:auto;color:var(--focus);font-size:11px}
.nolink{padding:10px;border:1px dashed var(--line2);border-radius:6px;color:var(--dim);font-size:12px}
.log{display:flex;flex-direction:column;gap:6px}.log div{border-left:2px solid var(--line2);padding:2px 0 2px 8px;color:var(--fg2);font-size:12px;white-space:pre-wrap;word-break:break-word}.log time{display:block;color:var(--faint);font-size:11px}
.toast{position:fixed;left:50%;bottom:44px;transform:translateX(-50%) translateY(20px);opacity:0;z-index:40;background:var(--card);border:1px solid var(--line2);border-radius:8px;padding:8px 12px;font-size:12.5px;box-shadow:0 8px 24px rgba(0,0,0,.35);transition:all .18s;pointer-events:none}.toast.on{opacity:1;transform:translateX(-50%)}.toast.err{border-color:#eb5757}
</style></head><body>
<header class="hd">
  <img class="logo" src="logo.svg" alt="">
  <div class="crumb"><b>playmaker</b><span>›</span><span class="goal" id="goal"></span></div>
  <span class="sp"></span>
  <span id="live" class="live"><i></i><span>실시간</span></span>
  <div class="lk hidden" id="lk"><button class="lkb" id="lkb" title="골 작업 세션 (메시지를 받을 세션)"><span class="dot none" id="lkd"></span><span class="nm" id="lkn">세션 연결</span><svg width="10" height="10" viewBox="0 0 10 10"><path d="M2.5 4l2.5 2.5L7.5 4" fill="none" stroke="currentColor" stroke-width="1.3"/></svg></button><div class="menu hidden" id="menu"></div></div>
  <button class="ib" id="vDone" title="완료 작업 펼치기 (D)">완료 펼치기 <kbd>D</kbd></button>
  <div class="vs"><button id="vBoard" class="on" title="보드 (1)"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="2" y="2.5" width="3.3" height="11" rx="1"/><rect x="6.35" y="2.5" width="3.3" height="7.5" rx="1"/><rect x="10.7" y="2.5" width="3.3" height="9.5" rx="1"/></svg>보드</button><button id="vList" title="리스트 (2)"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M5.5 4h8M5.5 8h8M5.5 12h8"/><circle cx="2.6" cy="4" r=".6" fill="currentColor"/><circle cx="2.6" cy="8" r=".6" fill="currentColor"/><circle cx="2.6" cy="12" r=".6" fill="currentColor"/></svg>리스트</button></div>
</header>
<nav class="tabs" id="tabs"></nav>
<div id="warn"></div>
<main><section class="board" id="board"></section><section class="list hidden" id="list"></section></main>
<footer class="foot" id="foot"></footer>
<aside class="peek" id="peek"><div class="ph"><span id="pid"></span><button class="x" id="px" title="닫기 (Esc)">✕</button></div><div class="pb" id="pb"></div></aside>
<div class="toast" id="toast"></div>
<script>
if(new URLSearchParams(location.search).get('theme')==='light')document.documentElement.classList.add('light')
const COLOR={todo:'var(--todo)',doing:'var(--doing)',waiting:'var(--wait)',done:'var(--done)'}
const LABEL={todo:'대기',doing:'진행',waiting:'사람 대기',done:'완료'}
const ICON={
todo:'<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="5.6" fill="none" stroke="var(--todo)" stroke-width="1.5"/></svg>',
doing:'<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="5.6" fill="none" stroke="var(--doing)" stroke-width="1.5"/><path d="M7 3.6A3.4 3.4 0 0 1 7 10.4Z" fill="var(--doing)"/></svg>',
waiting:'<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="5.6" fill="none" stroke="var(--wait)" stroke-width="1.5"/><rect x="4.9" y="4.4" width="1.5" height="5.2" rx=".5" fill="var(--wait)"/><rect x="7.6" y="4.4" width="1.5" height="5.2" rx=".5" fill="var(--wait)"/></svg>',
done:'<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6.3" fill="var(--done)"/><path d="M4.3 7.2l1.8 1.8 3.6-3.8" fill="none" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'}
const URGENT='<svg width="12" height="12" viewBox="0 0 12 12"><rect x=".5" y=".5" width="11" height="11" rx="3" fill="var(--wait)"/><path d="M6 3v3.6" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/><circle cx="6" cy="8.7" r=".85" fill="#fff"/></svg>'
const msState=m=>m.status==='done'?'done':m.status==='current'?(m.waiting?'waiting':'doing'):'todo'
let uid=0
function diamond(m,size){const s=size||12,st=msState(m),n=m.tasks.filter(t=>t.state==='done').length,p=m.tasks.length?n/m.tasks.length:0,id='dm'+(uid++),c=st==='todo'?'var(--todo)':COLOR[st]
  return '<svg width="'+s+'" height="'+s+'" viewBox="0 0 12 12"><defs><clipPath id="'+id+'"><rect x="0" y="'+(12-12*p)+'" width="12" height="12"/></clipPath></defs><path d="M6 1l5 5-5 5-5-5z" fill="none" stroke="'+c+'" stroke-width="1.4" stroke-linejoin="round"/><path d="M6 3.1L8.9 6 6 8.9 3.1 6z" fill="'+c+'" clip-path="url(#'+id+')"/></svg>'}
function ring(p){const r=6,c=2*Math.PI*r;return '<svg width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="'+r+'" fill="none" stroke="var(--line2)" stroke-width="2"/><circle cx="8" cy="8" r="'+r+'" fill="none" stroke="var(--done)" stroke-width="2" stroke-dasharray="'+(c*p)+' '+c+'" transform="rotate(-90 8 8)" stroke-linecap="round"/></svg>'}
const pct=m=>{const n=m.tasks.filter(t=>t.state==='done').length;return m.tasks.length?Math.round(n/m.tasks.length*100):0}
const TOKEN='__TOKEN__'
let view='board',open=false,filter='all',last='',cache=null,seen=0,sel=null,menuOn=false
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))
const $=id=>document.getElementById(id)
const tid=(m,t,i)=>t.id||('M'+m.id+'-'+(i+1))
function card(m,t,i){
  const k=m.id+':'+i
  return '<div class="card '+t.state+(t.inferred&&t.state!=='done'?' inferred':'')+(sel===k?' sel':'')+'" data-k="'+esc(k)+'"><div class="r1">'+esc(tid(m,t,i))+ICON[t.state]+'</div><div class="ti">'+esc(t.text)+'</div><div class="props">'
   +(t.state==='waiting'?'<span class="pill urgent">'+URGENT+'사람 확인 필요</span>':'')
   +'<span class="pill" title="M'+esc(m.id)+' '+esc(m.name)+'">'+diamond(m)+esc(m.name)+' · '+pct(m)+'%</span></div></div>'}
function tint(st){return 'background:color-mix(in srgb,'+COLOR[st]+' 9%,transparent)'}
function render(b){
  const ms=b.milestones,shown=filter==='all'?ms:ms.filter(m=>m.id===filter)
  $('goal').textContent=b.goal||'(골 문장 없음)';document.title=(b.goal?b.goal+' — ':'')+'playmaker'
  const allT=ms.flatMap(m=>m.tasks),doneN=allT.filter(t=>t.state==='done').length,p=allT.length?doneN/allT.length:0
  $('tabs').innerHTML='<button class="tab'+(filter==='all'?' on':'')+'" data-f="all">전체 <span class="p">'+allT.length+'</span></button>'
    +ms.map(m=>'<button class="tab'+(filter===m.id?' on':'')+'" data-f="'+esc(m.id)+'">'+diamond(m)+'M'+esc(m.id)+' '+esc(m.name)+' <span class="p">'+pct(m)+'%</span></button>').join('')
    +'<span class="prog">'+ring(p)+doneN+'/'+allT.length+' 완료 · '+Math.round(p*100)+'%</span>'
  $('tabs').querySelectorAll('.tab').forEach(el=>el.onclick=()=>{filter=el.dataset.f;render(cache)})
  $('warn').innerHTML=(b.mismatch||[]).map(x=>'<div class="warn">⚠ '+esc(x)+'</div>').join('')
  const all=shown.flatMap(m=>m.tasks.map((t,i)=>[m,t,i])),pick=s=>all.filter(([,t])=>s.includes(t.state))
  const todo=pick(['todo']),doing=pick(['doing','waiting']).sort((a,c)=>(c[1].state==='waiting')-(a[1].state==='waiting')),done=pick(['done'])
  const cards=l=>l.length?l.map(([m,t,i])=>card(m,t,i)).join(''):'<div class="empty">없음</div>'
  const doneBody=open?cards(done):(shown.map(m=>[m,m.tasks.filter(t=>t.state==='done').length]).filter(x=>x[1]).map(([m,n])=>'<div class="fold">'+diamond(m)+esc(m.name)+'<span class="c">'+n+'건</span></div>').join('')||'<div class="empty">아직 없음</div>')
  const lane=(k,l,body)=>'<div class="lane '+k+'"><div class="lh">'+ICON[k]+LABEL[k]+'<span class="c">'+l.length+'</span></div>'+body+'</div>'
  $('board').innerHTML=lane('todo',todo,cards(todo))+lane('doing',doing,cards(doing))+lane('done',done,doneBody)
  $('list').innerHTML=shown.map(m=>{const st=msState(m),n=m.tasks.filter(t=>t.state==='done').length
    const rows=m.status==='done'&&!open?'':m.tasks.map((t,i)=>'<div class="row '+t.state+'" data-k="'+esc(m.id+':'+i)+'">'+ICON[t.state]+'<span class="id">'+esc(tid(m,t,i))+'</span><span class="tx">'+esc(t.text)+'</span>'+(t.state==='waiting'?'<span class="pill urgent">'+URGENT+'사람 확인</span>':'<span class="pill">'+LABEL[t.state]+'</span>')+'</div>').join('')
    return '<div class="gh" style="'+tint(st)+'">'+diamond(m,13)+'M'+esc(m.id)+' '+esc(m.name)+'<span class="c">'+m.tasks.length+'</span><span class="pc">'+n+'/'+m.tasks.length+' · '+pct(m)+'%</span></div>'+rows}).join('')
  const legacy=ms.length&&ms.every(m=>m.source==='legacy')
  seen=b.touched
  $('foot').innerHTML=(legacy?'<span>점선 카드는 마일스톤 기록에서 추정한 작업</span>':'')+(b.lastValidation?'<span>최근 검증 · '+esc(b.lastValidation)+'</span>':'')+'<span id="ago"></span><span class="d">'+esc(b.dir)+'</span>'
  document.querySelectorAll('[data-k]').forEach(el=>el.onclick=()=>openPeek(el.dataset.k))
  renderLink(b);if(sel)renderPeek()
  ago()}
function findTask(k){if(!cache||!k)return null;const [mid,i]=k.split(':'),m=cache.milestones.find(x=>x.id===mid);return m&&m.tasks[+i]?{m,t:m.tasks[+i],i:+i}:null}
function renderLink(b){const on=!!b.paseo;$('lk').classList.toggle('hidden',!on);if(!on)return
  const l=b.link;$('lkd').className='dot '+(l?l.status:'none');$('lkn').textContent=l?l.name:'세션 연결 안 됨';$('lkb').title=l?'메시지를 받을 골 작업 세션: '+l.name+' ('+(l.status==='running'?'작업 중':'대기 중')+')':'메시지를 받을 세션을 고르세요'
  if(menuOn)renderMenu(b)}
function renderMenu(b){$('menu').innerHTML='<div class="mh">메시지를 받을 골 작업 세션</div>'+((b.agents||[]).map(a=>'<button data-a="'+esc(a.id)+'"><span class="dot '+esc(a.status)+'"></span><span class="nm">'+esc(a.name)+'</span>'+(b.link&&b.link.id===a.id?'<span class="ck">✓</span>':'')+'</button>').join('')||'<div class="mh">이 프로젝트에서 도는 Paseo 세션이 없습니다</div>')
  $('menu').querySelectorAll('[data-a]').forEach(el=>el.onclick=async()=>{menuOn=false;$('menu').classList.add('hidden');await post('api/link',{agentId:el.dataset.a,mode:'user'});last='';tick()})}
async function post(u,v){const r=await fetch(u,{method:'POST',headers:{'content-type':'application/json','x-playmaker-token':TOKEN},body:JSON.stringify(v)});return r.json()}
function toast(t,err){const el=$('toast');el.textContent=t;el.className='toast on'+(err?' err':'');clearTimeout(toast.h);toast.h=setTimeout(()=>el.className='toast',2600)}
const ACTS={
 waiting:[['승인하고 진행','이 작업은 승인합니다. 진행하고, 시작하면 PLAN.md의 이 작업 마커를 [>]로 바꿔 주세요.',1],['무엇을 확인해야 하나?','이 작업에서 제가 무엇을 확인하거나 결정해야 하는지, 선택지가 있으면 선택지와 추천을 짧게 알려 주세요.'],['보류','이 작업은 보류합니다. 다른 작업을 먼저 진행하고, 보류 사유를 PROGRESS.md에 남겨 주세요.']],
 doing:[['진행 상황 알려줘','이 작업을 지금 어디까지 했고 남은 게 무엇인지 짧게 알려 주세요.',1],['막힌 게 있나?','이 작업에서 막힌 부분이 있으면 무엇이 필요한지 알려 주세요. 없으면 계속 진행해 주세요.']],
 todo:[['이것부터 해','이 작업을 다음 작업으로 먼저 진행해 주세요.',1],['계획 설명해','이 작업을 어떻게 할 계획인지 짧게 설명해 주세요. 아직 시작하지는 마세요.']],
 done:[['결과 보여줘','이 작업의 결과물과 확인 방법을 짧게 알려 주세요.',1],['다시 검증해','이 작업이 실제로 끝났는지 다시 검증하고 결과를 알려 주세요. 문제가 있으면 마커를 [>]로 되돌려 주세요.']]}
function msgFor(x,body){return '[playmaker · '+tid(x.m,x.t,x.i)+'] '+x.t.text+'\\n(M'+x.m.id+' '+x.m.name+' · 지금 상태: '+LABEL[x.t.state]+')\\n\\n'+body}
function openPeek(k){sel=k;$('peek').classList.add('on');renderPeek(true);document.querySelectorAll('.card').forEach(el=>el.classList.toggle('sel',el.dataset.k===k))}
function closePeek(){sel=null;$('peek').classList.remove('on');document.querySelectorAll('.card.sel').forEach(el=>el.classList.remove('sel'))}
function renderPeek(fresh){const x=findTask(sel);if(!x){closePeek();return}
  const draft=fresh?'':($('ta')?$('ta').value:''),l=cache.link
  $('pid').textContent=tid(x.m,x.t,x.i)
  const id=tid(x.m,x.t,x.i),mine=(cache.sent||[]).filter(s=>s.task===id),lastS=mine[0]
  // 보낸 뒤 세션이 답을 마칠 때까지(작업 중 → 대기) 이 작업의 빠른 행동은 잠근다. 반대 지시가 연달아 들어가는 것 방지
  const pending=!!(lastS&&l&&(l.status==='running'||Date.now()-lastS.at<8000))
  const busy=!!(l&&l.status==='running'&&!pending)
  const acts=(ACTS[x.t.state]||[]).map(([label,body,pri],j)=>{const done=mine.some(s=>s.label===label);return '<button class="act'+(pri&&!done?' primary':'')+'" data-j="'+j+'"'+(l&&!pending?'':' disabled')+'>'+label+(done?'<span class="ok">✓ 보냄</span>':'<small>보내기</small>')+'</button>'}).join('')
  const banner=pending?'<div class="banner"><span class="dot running"></span><span><b>'+esc(lastS.label||'메시지')+'</b>를 보냈습니다 · '+new Date(lastS.at).toLocaleTimeString()+'<br>세션이 답하는 중입니다. 답이 끝나면 다시 보낼 수 있습니다.</span></div>'
    :busy?'<div class="banner busy"><span class="dot running"></span><span>연결된 세션이 지금 다른 작업 중입니다. 보내면 하던 일 사이에 끼어들 수 있습니다.</span></div>'
    :lastS?'<div class="banner"><span class="dot idle"></span><span>마지막으로 보낸 것: <b>'+esc(lastS.label||'메시지')+'</b> · '+new Date(lastS.at).toLocaleTimeString()+' · 세션 답변 끝남</span></div>':''
  $('pb').innerHTML='<h2 class="pt">'+esc(x.t.text)+'</h2>'
   +'<div class="kv"><span>상태</span><span class="v">'+ICON[x.t.state]+LABEL[x.t.state]+(x.t.inferred?' (추정)':'')+'</span><span>마일스톤</span><span class="v">'+diamond(x.m)+'M'+esc(x.m.id)+' '+esc(x.m.name)+' · '+pct(x.m)+'%</span>'
   +(cache.paseo?'<span>보낼 곳</span><span class="v"><span class="dot '+(l?esc(l.status):'none')+'"></span>'+(l?esc(l.name):'연결 안 됨')+'</span>':'')+'</div>'
   +(cache.paseo?(l?'':'<div class="nolink">위쪽 「세션 연결 안 됨」을 눌러 이 골을 작업하는 세션을 고르면 여기서 바로 지시를 보낼 수 있습니다.</div>')
     +'<div class="sec">빠른 행동</div>'+banner+'<div class="acts">'+acts+'</div>'
     +'<div class="sec">직접 쓰기</div><textarea class="ta" id="ta" placeholder="이 작업에 대해 세션에 보낼 말"></textarea><div class="sendrow"><span class="hint">⌘↵ 보내기 · 작업 ID와 맥락이 자동으로 붙습니다</span><button class="btn" id="sendb"'+(l&&!pending?'':' disabled')+'>보내기</button></div>'
     +(mine.length?'<div class="sec">보낸 메시지</div><div class="log">'+mine.map(s=>'<div><time>'+new Date(s.at).toLocaleTimeString()+' → '+esc(s.to)+'</time>'+esc(s.label?s.label:s.text.split('\\n\\n').slice(1).join('\\n\\n'))+'</div>').join('')+'</div>':'')
    :'<div class="nolink">세션 연결은 Paseo에서 쓸 수 있습니다. 터미널에서는 이 내용을 직접 세션에 입력하세요.</div>')
  if($('ta')){$('ta').value=draft;$('ta').onkeydown=e=>{if(e.key==='Enter'&&(e.metaKey||e.ctrlKey)){e.preventDefault();$('sendb').click()}}}
  $('pb').querySelectorAll('[data-j]').forEach(el=>el.onclick=()=>{if(el.disabled)return;const a=ACTS[x.t.state][+el.dataset.j];doSend(msgFor(x,a[1]),false,id,a[0])})
  if($('sendb'))$('sendb').onclick=()=>{const v=$('ta').value.trim();if(v&&!pending)doSend(msgFor(x,v),true,id,'')}}
let sending=false
async function doSend(text,clear,task,label){if(sending)return;sending=true;try{const r=await post('api/send',{text,task,label});if(r.error)return toast('보내지 못했습니다: '+r.error,true);toast(r.to+' 세션에 보냈습니다');if(clear&&$('ta'))$('ta').value='';last='';await tick()}catch(e){toast('보내지 못했습니다',true)}finally{sending=false}}
function ago(){const el=$('ago');if(!el||!seen)return;const s=Math.max(0,Math.round((Date.now()-seen)/1000));el.textContent='변경 '+(s<60?s+'초 전':s<3600?Math.floor(s/60)+'분 전':s<86400?Math.floor(s/3600)+'시간 전':new Date(seen).toLocaleDateString())}
function apply(){$('board').classList.toggle('hidden',view!=='board');$('list').classList.toggle('hidden',view!=='list');$('vBoard').classList.toggle('on',view==='board');$('vList').classList.toggle('on',view==='list');$('vDone').classList.toggle('on',open);$('vDone').firstChild.textContent=open?'완료 접기 ':'완료 펼치기 '}
async function tick(){try{const r=await fetch('api/board',{cache:'no-store'});const t=await r.text();$('live').className='live';$('live').lastChild.textContent='실시간'
  if(t!==last){last=t;cache=JSON.parse(t);if(cache.error){$('goal').textContent='읽기 실패: '+cache.error}else render(cache)}}
  catch(e){$('live').className='live off';$('live').lastChild.textContent='연결 끊김 · /playmaker 로 다시 켜기'}}
const rerender=()=>{apply();cache&&!cache.error&&render(cache)}
vBoard.onclick=()=>{view='board';rerender()};vList.onclick=()=>{view='list';rerender()};vDone.onclick=()=>{open=!open;rerender()}
$('px').onclick=closePeek
$('lkb').onclick=e=>{e.stopPropagation();menuOn=!menuOn;$('menu').classList.toggle('hidden',!menuOn);if(menuOn&&cache)renderMenu(cache)}
document.addEventListener('click',e=>{if(menuOn&&!$('lk').contains(e.target)){menuOn=false;$('menu').classList.add('hidden')}})
addEventListener('keydown',e=>{if(e.key==='Escape'){closePeek();return}if(/^(TEXTAREA|INPUT)$/.test(document.activeElement&&document.activeElement.tagName))return;if(e.metaKey||e.ctrlKey||e.altKey)return;if(e.key==='1'){view='board';rerender()}else if(e.key==='2'){view='list';rerender()}else if(e.key==='d'||e.key==='D'){open=!open;rerender()}})
apply();tick();setInterval(tick,2000);setInterval(()=>{ago();if(sel&&cache&&!cache.error&&!(document.activeElement&&document.activeElement.id==='ta'))renderPeek()},1000)
</script></body></html>`

const json = (res, code, v) => { res.writeHead(code, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }); res.end(JSON.stringify(v)) }

const server = createServer(async (req, res) => {
  lastHit = Date.now()
  const url = new URL(req.url ?? '/', 'http://x')
  try {
    if (url.pathname === '/api/health') return json(res, 200, { ok: true, app: 'playmaker', dir: DIR })
    if (url.pathname === '/api/board') {
      try { return json(res, 200, { ...board(), ...(await linkInfo()), sent }) } catch (e) { return json(res, 200, { error: String(e.message ?? e) }) }
    }
    if (req.method === 'POST' && (url.pathname === '/api/link' || url.pathname === '/api/send')) {
      if (!allowed(req)) return json(res, 403, { error: 'forbidden' })
      const b = await body(req)
      if (url.pathname === '/api/link') { await agents(); setLink(String(b.agentId ?? ''), b.mode === 'auto' ? 'auto' : b.mode === 'explicit' ? 'explicit' : 'user'); return json(res, 200, await linkInfo()) }
      const text = String(b.text ?? '').trim()
      if (!text) return json(res, 400, { error: '빈 메시지' })
      try { const to = await send(text.slice(0, 4000), String(b.task ?? '').slice(0, 40), String(b.label ?? '').slice(0, 60)); return json(res, 200, { ok: true, to: to.name }) } catch (e) { return json(res, 200, { error: String(e.message ?? e) }) }
    }
    if (url.pathname === '/logo.svg') {
      res.writeHead(200, { 'content-type': 'image/svg+xml', 'cache-control': 'max-age=3600' })
      return res.end(LOGO)
    }
    if (url.pathname === '/') {
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' })
      return res.end(PAGE.replace('__TOKEN__', TOKEN))
    }
    res.writeHead(404); res.end()
  } catch (e) {
    json(res, 500, { error: String(e?.message ?? e) })
  }
})

function listen(p, tries) {
  server.once('error', e => {
    if (e.code === 'EADDRINUSE' && tries > 0) return listen(p + 1, tries - 1)
    console.error(String(e)); process.exit(1)
  })
  server.listen(p, '127.0.0.1', () => {
    port = p
    const u = `http://127.0.0.1:${p}/`
    if (args['port-file']) {
      writeFileSync(`${args['port-file']}.token`, TOKEN, { mode: 0o600 })
      writeFileSync(args['port-file'], u)
    }
    console.log(`PLAYMAKER_URL ${u} dir=${DIR}`)
  })
}
listen(FIRST, 20)
setInterval(() => { if (Date.now() - lastHit > IDLE_MS) process.exit(0) }, 60_000).unref()
