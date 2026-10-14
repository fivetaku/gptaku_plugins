import type { Board, Milestone, Task, TaskState } from '../types'

// goaljaby canonical headings (templates.md §헤딩 맵): ko / en
const H = {
  milestone: /^##\s*(?:마일스톤|Milestone)\s*(\d+[a-z]?)\s*[:：.]\s*(.+?)\s*$/,
  // 비표준 PLAN: 표 행 `| M1a 이름 | 범위 | ...`, 헤딩 `### M2 이름`, 목록 `- M3: 이름`
  loose: [
    /^\|\s*\**M(\d+[a-z]?)\**\s+([^|]+?)\s*\|/,
    /^#{2,4}\s*M(\d+[a-z]?)[\s:：.\-—]+(.+?)\s*$/,
    /^\s*(?:[-*]|\d+\.)\s*\**M(\d+[a-z]?)\**[\s:：.\-—]+(.+?)\s*$/,
  ],
  goal: /^##\s*(?:현재 골|Current Goal)\s*$/,
  current: /^##\s*(?:현재 마일스톤|Current Milestone)\s*$/,
  done: /^##\s*(?:완료|Completed)\s*$/,
  failed: /^##\s*(?:실패 시도|Failed Attempts)\s*$/,
  validation: /^##\s*(?:마지막 검증 결과|Last Validation)\s*$/,
  scope: /^\s*[-*]\s*(?:범위(?:\s*\(Scope\))?|Scope)\s*[:：]\s*(.+)$/i,
  doneWhen: /^\s*[-*]\s*(?:완료 조건|Completion|Done when)\s*[:：]\s*(.+)$/i,
  checkbox: /^\s*[-*]\s*\[([ xX✓>!])\]\s*(?:\**(M\d+[a-z]?-T\d+)\**\s*[:：]\s*)?(.+?)\s*$/,
  waitWords: /대기|동석|사람\s*(?:측정|확인|판단|증거)|blocked|waiting|on hold|needs? (?:human|user)/i,
}

const MARK: Record<string, TaskState> = { ' ': 'todo', '>': 'doing', x: 'done', X: 'done', '✓': 'done', '!': 'waiting' }

function section(md: string, head: RegExp): string {
  const lines = md.split('\n')
  const i = lines.findIndex(l => head.test(l))
  if (i < 0) return ''
  const out: string[] = []
  for (const l of lines.slice(i + 1)) {
    if (/^##\s/.test(l)) break
    out.push(l)
  }
  return out.join('\n').trim()
}

function clean(s: string): string {
  return s.replace(/\{.*?\}/g, '').replace(/\*\*/g, '').replace(/`/g, '').trim()
}

// 명시 표기(M2, 마일스톤 2)만 인정한다
function mentionsId(text: string, id: string): boolean {
  return new RegExp(`(^|[^0-9A-Za-z])M${id}(?![0-9a-z])`).test(text)
    || new RegExp(`(마일스톤|Milestone)\\s*${id}(?![0-9a-z])`, 'i').test(text)
}

// 괄호 밖의 쉼표로만 자른다: "A(x, y), B" → ["A(x, y)", "B"]
function splitTopLevel(s: string): string[] {
  const out: string[] = []
  let depth = 0
  let cur = ''
  for (const ch of s) {
    if ('([{（「'.includes(ch)) depth++
    if (')]}）」'.includes(ch)) depth = Math.max(0, depth - 1)
    if ((ch === ',' || ch === '，') && depth === 0) { out.push(cur); cur = ''; continue }
    cur += ch
  }
  out.push(cur)
  return out.map(clean).filter(x => x.length > 0)
}

type Head = { id: string; name: string; line: number; kind: 'canonical' | 'loose'; tableScope?: string }

// 모든 줄에서 canonical·loose 마일스톤 헤딩을 함께 수집 (혼합형 PLAN 대응)
function collectHeads(lines: string[]): Head[] {
  const heads: Head[] = []
  lines.forEach((l, i) => {
    const c = l.match(H.milestone)
    if (c) { heads.push({ id: c[1], name: clean(c[2]), line: i, kind: 'canonical' }); return }
    if (H.checkbox.test(l)) return
    for (const re of H.loose) {
      const m = l.match(re)
      if (!m) continue
      const cells = l.trim().startsWith('|') ? l.split('|').map(x => x.trim()) : []
      heads.push({ id: m[1], name: clean(m[2]), line: i, kind: 'loose', tableScope: cells.length > 3 ? cells[2] : undefined })
      return
    }
  })
  // 같은 ID가 여러 번이면 canonical 우선, 그다음 먼저 나온 것
  const byId = new Map<string, Head>()
  for (const h of heads) {
    const prev = byId.get(h.id)
    if (!prev || (prev.kind === 'loose' && h.kind === 'canonical')) byId.set(h.id, h)
  }
  return [...byId.values()].sort((a, b) => a.line - b.line)
}

// 헤딩 다음 줄부터 다음 마일스톤 헤딩 또는 다음 ## 헤딩 직전까지
function bodyOf(lines: string[], h: Head, heads: Head[]): string[] {
  if (h.tableScope !== undefined) return []
  const starts = new Set(heads.map(x => x.line))
  const out: string[] = []
  for (let i = h.line + 1; i < lines.length; i++) {
    if (starts.has(i) || /^##\s/.test(lines[i])) break
    out.push(lines[i])
  }
  return out
}

// PROGRESS 완료 섹션에서 그 마일스톤을 가리키는 최상위 bullet과 하위 항목
function doneEntry(doneText: string, m: { id: string; name: string }): { hit: boolean; sub: string[] } {
  const lines = doneText.split('\n')
  const i = lines.findIndex(l => {
    if (!/^[-*]\s/.test(l)) return false
    if (mentionsId(l, m.id)) return true
    const head = clean(l.replace(/^[-*]\s+/, ''))
    return m.name.length >= 2 && head.startsWith(m.name)
  })
  if (i < 0) return { hit: false, sub: [] }
  const sub: string[] = []
  for (const l of lines.slice(i + 1)) {
    if (/^[-*]\s/.test(l)) break
    const s = l.match(/^\s{2,}[-*]\s+(.+)$/)
    if (s) sub.push(clean(s[1]))
  }
  return { hit: true, sub }
}

// "현재 마일스톤" 산문에서 그 마일스톤 ID가 나온 구간만 잘라 대기 여부를 본다
function currentClause(currentText: string, id: string): string {
  const parts = currentText.split(/(?=(?:^|[^0-9A-Za-z])M\d+[a-z]?(?![0-9a-z]))|[.。]\s/)
  return parts.filter(p => mentionsId(p, id)).join(' ')
}

function firstMeaningful(text: string): string {
  for (const raw of text.split('\n')) {
    const l = raw.trim()
    if (!l) continue
    if (/^(```|~~~)/.test(l)) continue
    if (/^\|?\s*:?-{3,}/.test(l)) continue
    return clean(l.replace(/^[-*]\s*/, ''))
  }
  return ''
}

export function parseBoard(dir: string, plan: string, progress: string, now: number): Board {
  const lines = plan.split('\n')
  const heads = collectHeads(lines)
  const doneText = section(progress, H.done)
  const currentText = section(progress, H.current)
  const saysAllDone = /전체 완료|모두 완료|all (?:milestones )?(?:complete|done)/i.test(currentText)
  const mismatch: string[] = []

  const milestones: Milestone[] = heads.map(h => {
    const body = bodyOf(lines, h, heads)
    const doneWhen = body.map(l => l.match(H.doneWhen)).find(Boolean)?.[1].trim() ?? ''
    const boxes = body.map(l => l.match(H.checkbox)).filter(Boolean) as RegExpMatchArray[]
    const entry = doneEntry(doneText, h)
    const progressDone = saysAllDone || entry.hit
    const progressCurrent = mentionsId(currentText, h.id)
    const clauseWaiting = progressCurrent && H.waitWords.test(currentClause(currentText, h.id))

    if (boxes.length) {
      const tasks: Task[] = boxes.map(b => ({ id: b[2], text: clean(b[3]), state: MARK[b[1]] ?? 'todo', inferred: false }))
      const all = tasks.every(t => t.state === 'done')
      const started = tasks.some(t => t.state !== 'todo')
      const status = all ? 'done' : started || progressCurrent ? 'current' : 'todo'
      if (progressDone && !all) mismatch.push(`M${h.id}: PROGRESS는 완료, PLAN 체크리스트에 남은 작업 ${tasks.filter(t => t.state !== 'done').length}건`)
      if (all && !progressDone && !saysAllDone && doneText) mismatch.push(`M${h.id}: 체크리스트는 모두 완료, PROGRESS 완료 기록 없음`)
      return { id: h.id, name: h.name, status, waiting: tasks.some(t => t.state === 'waiting'), tasks, doneWhen, source: 'checklist' }
    }

    const status = progressDone ? 'done' : progressCurrent ? 'current' : 'todo'
    const legacyState: TaskState = status === 'done' ? 'done' : status === 'current' ? (clauseWaiting ? 'waiting' : 'doing') : 'todo'
    const texts = status === 'done' && entry.sub.length
      ? entry.sub
      : splitTopLevel(body.map(l => l.match(H.scope)).find(Boolean)?.[1] ?? h.tableScope ?? '')
    const tasks: Task[] = texts.map(text => ({ text, state: legacyState, inferred: true }))
    return { id: h.id, name: h.name, status, waiting: legacyState === 'waiting', tasks, doneWhen, source: 'legacy' }
  })

  const failedText = section(progress, H.failed)
  const failed = failedText.split('\n').filter(l => /^\s*([-*]|\d+\.)\s+\S/.test(l) && !/^\s*[-*]\s*\(?없음\)?\s*$/.test(l)).length
  return {
    dir,
    goal: firstMeaningful(section(progress, H.goal)),
    milestones,
    failed,
    lastValidation: firstMeaningful(section(progress, H.validation)),
    allDone: milestones.length > 0 && milestones.every(m => m.status === 'done'),
    mismatch,
    updatedAt: now,
  }
}

export function counts(b: Board) {
  const tasks = b.milestones.flatMap(m => m.tasks)
  return {
    msDone: b.milestones.filter(m => m.status === 'done').length,
    current: b.milestones.filter(m => m.status === 'current'),
    taskDone: tasks.filter(t => t.state === 'done').length,
    taskTotal: tasks.length,
    waiting: tasks.filter(t => t.state === 'waiting').length,
  }
}

export function summaryLine(b: Board): string {
  const c = counts(b)
  const parts = [`골 ${c.msDone}/${b.milestones.length}`]
  if (c.current.length) parts.push(`진행 ${c.current.map(m => `M${m.id}`).join('·')}`)
  else if (b.allDone) parts.push('전체 완료')
  if (c.taskTotal) parts.push(`작업 ${c.taskDone}/${c.taskTotal}`)
  if (c.waiting) parts.push(`⏸ 사람 대기 ${c.waiting}`)
  return parts.join(' · ')
}

const MD_ICON: Record<TaskState, string> = { todo: '⬜', doing: '▶️', done: '✅', waiting: '⏸️' }

// 텍스트 요약: 마크다운. Paseo·채팅 화면에서 표와 목록으로 그려진다
export function summaryText(b: Board): string {
  const card = (t: Task, id: string) => `${MD_ICON[t.state]} [M${id}] ${t.text.replace(/\|/g, '/').slice(0, 60)}`
  const pick = (states: TaskState[]) => b.milestones.flatMap(m => m.tasks.filter(t => states.includes(t.state)).map(t => card(t, m.id)))
  const todo = pick(['todo'])
  const doing = pick(['doing', 'waiting'])
  const done = b.milestones.map(m => ({ m, n: m.tasks.filter(t => t.state === 'done').length })).filter(x => x.n).map(x => `✅ M${x.m.id} ${x.n}건`)
  const rows = Math.min(10, Math.max(todo.length, doing.length, done.length, 1))
  const table = [`| 대기 (${todo.length}) | 진행 (${doing.length}) | 완료 (${b.milestones.flatMap(m => m.tasks).filter(t => t.state === 'done').length}) |`, '|---|---|---|']
  for (let i = 0; i < rows; i++) table.push(`| ${todo[i] ?? ''} | ${doing[i] ?? ''} | ${done[i] ?? ''} |`)
  const ms = b.milestones.map(m => {
    const n = m.tasks.filter(t => t.state === 'done').length
    const head = m.status === 'done' ? '✅' : m.status === 'current' ? (m.waiting ? '⏸️' : '▶️') : '⬜'
    const lines = m.status === 'done' ? [] : m.tasks.map(t => `- ${MD_ICON[t.state]} ${t.id ? `${t.id}: ` : ''}${t.text}`)
    return [`**${head} M${m.id} ${m.name}** (${n}/${m.tasks.length})`, ...lines].join('\n')
  })
  return [
    `**${summaryLine(b)}**`,
    b.goal ? `> ${b.goal}` : '',
    table.join('\n'),
    ms.join('\n\n'),
    b.failed ? `실패 시도 ${b.failed}건` : '',
    ...b.mismatch.map(x => `⚠️ ${x}`),
    `\`${b.dir}\``,
  ].filter(Boolean).join('\n\n')
}

// 카드 행동: 상태별 빠른 지시. 웹 보기(web/server.mjs)의 ACTS와 같은 문구를 쓴다
export const ACTIONS: Record<TaskState, [label: string, body: string][]> = {
  waiting: [
    ['승인하고 진행', '이 작업은 승인합니다. 진행하고, 시작하면 PLAN.md의 이 작업 마커를 [>]로 바꿔 주세요.'],
    ['무엇을 확인해야 하나?', '이 작업에서 제가 무엇을 확인하거나 결정해야 하는지, 선택지가 있으면 선택지와 추천을 짧게 알려 주세요.'],
    ['보류', '이 작업은 보류합니다. 다른 작업을 먼저 진행하고, 보류 사유를 PROGRESS.md에 남겨 주세요.'],
  ],
  doing: [
    ['진행 상황 알려줘', '이 작업을 지금 어디까지 했고 남은 게 무엇인지 짧게 알려 주세요.'],
    ['막힌 게 있나?', '이 작업에서 막힌 부분이 있으면 무엇이 필요한지 알려 주세요. 없으면 계속 진행해 주세요.'],
  ],
  todo: [
    ['이것부터 해', '이 작업을 다음 작업으로 먼저 진행해 주세요.'],
    ['계획 설명해', '이 작업을 어떻게 할 계획인지 짧게 설명해 주세요. 아직 시작하지는 마세요.'],
  ],
  done: [
    ['결과 보여줘', '이 작업의 결과물과 확인 방법을 짧게 알려 주세요.'],
    ['다시 검증해', '이 작업이 실제로 끝났는지 다시 검증하고 결과를 알려 주세요. 문제가 있으면 마커를 [>]로 되돌려 주세요.'],
  ],
}

const STATE_LABEL: Record<TaskState, string> = { todo: '대기', doing: '진행', done: '완료', waiting: '사람 대기' }

export function taskId(m: Milestone, t: Task, i: number): string {
  return t.id ?? `M${m.id}-${i + 1}`
}

export function actionMessage(m: Milestone, t: Task, i: number, body: string): string {
  return `[playmaker · ${taskId(m, t, i)}] ${t.text}\n(M${m.id} ${m.name} · 지금 상태: ${STATE_LABEL[t.state]})\n\n${body}`
}
