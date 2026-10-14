import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'
import type { Board, Milestone, Task, TaskState } from '../types'
import { ACTIONS, actionMessage, counts, parseBoard, summaryLine, summaryText, taskId } from './parse'

const PANE = 'playmaker'
const TITLE = '골 진행'
const SKIP = new Set(['node_modules', '.git', '.next', 'dist', 'build', '.venv', 'Library', 'Applications'])
const MAX_DIRS = 150 // 세션 시작 지연 방지: 탐색 폴더 수 상한
const ACTIVE_MS = 7 * 24 * 3600 * 1000
const POLL_MS = 3000
const WIDE = 72 // 이 폭 이상이면 상태 3열, 미만이면 세로 쌓기
const CAP = 10 // 열 하나에 보여 줄 카드 수

const board = atom({ plugin: 'playmaker', key: 'board' } as const, null as Board | null)
const view = atom({ plugin: 'playmaker', key: 'view' } as const, 'state' as 'state' | 'milestone')
const webUrl = atom({ plugin: 'playmaker', key: 'webUrl' } as const, null as string | null)
const expandDone = atom({ plugin: 'playmaker', key: 'expandDone' } as const, false)
const pending = atom({ plugin: 'playmaker', key: 'pending' } as const, null as { task: string; label: string; at: number; started: boolean } | null)

async function release($: any) {
  try { const p = await read($, pending); if (p?.started) await update($, pending, () => null) } catch { /* 잠금 표시만 영향 */ }
}

// 카드를 누르면 그 카드 아래에 행동 버튼 줄이 펼쳐진다(대화상자 없음). 고른 지시를 이 세션에 넣고,
// 그 턴이 끝날 때까지 다른 카드 행동은 잠근다(반대 지시가 연달아 들어가는 것 방지)
const selected = atom({ plugin: 'playmaker', key: 'selected' } as const, null as { key: string; compose: boolean } | null)

async function sendTask($: any, ms: Milestone, task: Task, i: number, label: string, body: string) {
  const id = taskId(ms, task, i)
  const busy = await read($, pending)
  if (busy) { $.ui.toast(`${busy.task} ${busy.label} — 세션이 답하는 중입니다`); return }
  if (!body.trim()) return
  await update($, pending, () => ({ task: id, label, at: Date.now(), started: false }))
  await update($, selected, () => null)
  try {
    await $.prompt.submit({ text: actionMessage(ms, task, i, body.trim()), asUser: true })
  } catch {
    await update($, pending, () => null)
    $.ui.toast('지시를 보내지 못했습니다')
  }
}

async function taskAt($: any, mid: string, i: number): Promise<{ ms: Milestone; task: Task } | null> {
  const b = await read($, board)
  const ms = b?.milestones.find(x => x.id === mid)
  const task = ms?.tasks[i]
  return ms && task ? { ms, task } : null
}

async function isGoalDir($: any, dir: string): Promise<boolean> {
  try {
    return (await $.fs.exists(`${dir}/PLAN.md`)) && (await $.fs.exists(`${dir}/PROGRESS.md`))
  } catch {
    return false
  }
}

async function touchedAt($: any, dir: string): Promise<number> {
  const a = await $.fs.stat(`${dir}/PLAN.md`)
  const b = await $.fs.stat(`${dir}/PROGRESS.md`)
  return Math.max(a.mtimeMs, b.mtimeMs)
}

// 작업 폴더 → 하위 2단계까지, 이름순(결정론적)으로 탐색. 가장 최근에 바뀐 골 폴더를 고른다
async function findGoalDir($: any, base: string): Promise<string | null> {
  const found: { dir: string; at: number }[] = []
  let seen = 0
  const visit = async (dir: string, depth: number) => {
    if (++seen > MAX_DIRS) return
    if (await isGoalDir($, dir)) {
      try { found.push({ dir, at: await touchedAt($, dir) }) } catch { /* 읽기 실패한 후보는 건너뜀 */ }
    }
    if (depth >= 2) return
    let entries: any[] = []
    try { entries = await $.fs.list(dir) } catch { return }
    const dirs = entries
      .filter(e => e.kind === 'dir' && !SKIP.has(e.name) && !e.name.startsWith('.'))
      .map(e => e.name as string)
      .sort()
    for (const name of dirs) {
      if (seen > MAX_DIRS) return
      await visit(`${dir}/${name}`, depth + 1)
    }
  }
  await visit(base, 0)
  found.sort((a, b) => b.at - a.at || a.dir.localeCompare(b.dir))
  return found[0]?.dir ?? null
}

async function stamp($: any, dir: string): Promise<string> {
  const a = await $.fs.stat(`${dir}/PLAN.md`)
  const b = await $.fs.stat(`${dir}/PROGRESS.md`)
  return `${a.mtimeMs}:${a.size}|${b.mtimeMs}:${b.size}`
}

async function refresh($: any, dir: string, show?: boolean): Promise<Board> {
  const plan = await $.fs.read(`${dir}/PLAN.md`)
  const progress = await $.fs.read(`${dir}/PROGRESS.md`)
  const now = await $.clock.now()
  const parsed = parseBoard(dir, plan, progress, now)
  const age = Math.max(0, now - (await touchedAt($, dir)))
  const active = !parsed.allDone && age < ACTIVE_MS
  const prev = await read($, board)
  const next = { ...parsed, active, show: show ?? (prev?.dir === dir ? prev.show : active) }
  await update($, board, () => next)
  return next
}

async function locate($: any, arg: string): Promise<string | null> {
  const cwd = await $.session.cwd()
  const want = arg.trim()
  if (want) {
    const dir = want.startsWith('/') ? want : `${cwd}/${want}`
    return (await isGoalDir($, dir)) ? dir : null
  }
  return findGoalDir($, cwd)
}

// 폴더 경로 → 짧은 키 (서버 주소 파일 이름용)
function keyOf(dir: string): string {
  let h = 5381
  for (const ch of dir) h = ((h * 33) ^ ch.charCodeAt(0)) >>> 0
  return h.toString(36)
}

type Web = { url: string; reused: boolean } | { error: string }

// 화면을 그리지 않는 호스트(Paseo 등)용: 같은 파서로 도는 로컬 웹 보드를 켜고 주소를 돌려준다
// mode: auto(세션 시작 — 기존 연결이 살아 있으면 유지) · explicit(/playmaker — 이 세션으로 연결)
async function startWeb($: any, dir: string, mode: 'auto' | 'explicit' = 'explicit'): Promise<Web> {
  const root = $.plugin.root
  const or = (p: Promise<string | undefined>) => p.then(v => v ?? '', () => '')
  const paseo = [await or($.env.get('PASEO_AGENT_ID')), await or($.env.get('PASEO_CLI')), await or($.env.get('PASEO_AGENT_CWD'))]
  const r = await $.process.run(['sh', `${root}/web/start.sh`, dir, root, keyOf(dir), ...paseo, mode], { timeoutMs: 15000 })
  const m = r.stdout.match(/^URL (\S+) (reused|started)/m)
  if (m) await update($, webUrl, () => m[1])
  return m ? { url: m[1], reused: m[2] === 'reused' } : { error: (r.stdout + r.stderr).trim().slice(0, 800) }
}

async function isPaseo($: any): Promise<boolean> {
  try { return !!(await $.env.get('PASEO_AGENT_ID')) } catch { return false }
}

// Paseo가 모든 에이전트에 붙이는 `paseo` MCP로 브라우저 탭을 연다. 같은 주소 탭이 있으면 그대로, 옛 playmaker 탭이면 주소만 옮긴다
async function openPaseoTab($: any, url: string): Promise<'opened' | 'moved' | 'exists' | 'failed'> {
  try {
    const listed = await $.mcp.call('paseo', 'browser_list_tabs', {})
    const text = listed.content.map((c: any) => (c.type === 'text' ? c.text : '')).join('')
    const tabs: any[] = (() => { try { return JSON.parse(text).result?.tabs ?? [] } catch { return [] } })()
    if (tabs.some(t => t.url === url)) return 'exists'
    const old = tabs.find(t => t.title === 'playmaker')
    if (old) {
      const r = await $.mcp.call('paseo', 'browser_navigate', { browserId: old.browserId, url })
      return r.isError ? 'failed' : 'moved'
    }
    const r = await $.mcp.call('paseo', 'browser_new_tab', { url })
    return r.isError ? 'failed' : 'opened'
  } catch {
    return 'failed'
  }
}

// Paseo 짧은 안내 한 줄. 서버나 탭을 못 열면 null
async function webLine($: any, dir: string): Promise<string | null> {
  const w = await startWeb($, dir, 'explicit')
  if ('error' in w) return null
  const tab = await openPaseoTab($, w.url)
  if (tab === 'failed') return `보드: [${w.url}](${w.url})`
  return `보드는 Paseo의 playmaker 탭에 있습니다 (${tab === 'opened' ? '새로 열었음' : tab === 'moved' ? '주소 갱신' : '실시간 갱신 중'}). [${w.url}](${w.url})`
}

async function webText($: any, dir: string, paseo: boolean, mode: 'auto' | 'explicit' = 'explicit'): Promise<string> {
  const w = await startWeb($, dir, mode)
  if ('error' in w) return `웹 보기를 켜지 못했습니다.\n\n\`\`\`\n${w.error}\n\`\`\``
  const tab = paseo ? await openPaseoTab($, w.url) : null
  const where = tab === 'opened' ? 'Paseo 브라우저 탭에 열었습니다.'
    : tab === 'moved' ? '기존 playmaker 탭을 이 주소로 옮겼습니다.'
    : tab === 'exists' ? 'Paseo 브라우저 탭에 이미 열려 있습니다.'
    : '이 주소를 브라우저 탭으로 열어 두세요.'
  return [
    `**playmaker 웹 보기${w.reused ? ' (이미 켜져 있음)' : ''}**`,
    `[${w.url}](${w.url}) — ${where}`,
    'PLAN.md·PROGRESS.md가 바뀌면 2초 안에 다시 그립니다. 6시간 동안 아무도 보지 않으면 서버는 저절로 꺼집니다.',
  ].join('\n\n')
}

const noop = () => {}

const ICON: Record<TaskState, string> = { todo: '·', doing: '▶', done: '✓', waiting: '⏸' }
const COLOR: Partial<Record<TaskState, string>> = { doing: 'yellow', done: 'green', waiting: 'magenta' }

type Card = { key: string; ms: Milestone; task: Task }

function cardsOf(b: Board, states: TaskState[]): Card[] {
  return b.milestones.flatMap(ms =>
    ms.tasks.map((task, i) => ({ key: `${ms.id}-${task.id ?? i}`, ms, task })).filter(c => states.includes(c.task.state)),
  )
}

export const register: Register = on => {
  let last = ''
  let timer: { cancel: () => void } | null = null

  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'playmaker', description: '골 진행 보드 열기 (인자: 골 폴더 경로 · web: 브라우저 보드)' })
    let dir: string | null = null
    try { dir = await locate($, '') } catch { dir = null }
    if (dir) {
      try {
        const b = await refresh($, dir)
        last = await stamp($, dir)
        if (b.active) void $.ui.open({ id: PANE, title: TITLE })
        // Paseo는 pane을 그리지 않으므로 진행 중인 골이면 웹 보드를 켜고 탭을 연다
        if (b.active && (await isPaseo($))) void webText($, dir, true, 'auto').catch(() => {})
      } catch { /* 첫 읽기 실패 시 보드 없이 시작 */ }
    }
    timer?.cancel()
    timer = $.clock.every(POLL_MS, async () => {
      try {
        const cur = await read($, board)
        if (!cur) return
        const s = await stamp($, cur.dir)
        if (s !== last) { last = s; await refresh($, cur.dir) }
      } catch { /* 이번 주기만 건너뜀 */ }
    })
    return next(e)
  })

  // 카드에서 보낸 지시의 턴: 시작을 확인한 뒤 끝나면 잠금을 푼다
  on('turn.start', async ($, e, next) => {
    try { const p = await read($, pending); if (p && !p.started) await update($, pending, () => ({ ...p, started: true })) } catch { /* 잠금 표시만 영향 */ }
    return next(e)
  })
  on('turn.complete', async ($, e, next) => { await release($); return next(e) })
  on('turn.abort', async ($, e, next) => { await release($); return next(e) })

  // 패널 누르기: t 카드 펼치기/접기 · a 빠른 행동 보내기 · w 직접 쓰기 열기 · x 닫기
  on('ui.press', async ($, e, next) => {
    const mine = e.plugin === 'playmaker' && e.requestId === PANE
    if (mine && e.element === 'close') {
      // 패널을 닫고 입력창 위 요약 줄도 내린다. /playmaker로 다시 연다
      const b = await read($, board)
      if (b) await update($, board, () => ({ ...b, show: false }))
      await update($, selected, () => null)
      await $.ui.close({ id: PANE })
      return { element: e.element }
    }
    if (mine && e.element === 'web') {
      const b = await read($, board)
      if (!b) return { element: e.element }
      const w = await startWeb($, b.dir, 'explicit')
      if ('error' in w) { $.ui.toast('웹 보기를 켜지 못했습니다'); return { element: e.element } }
      await update($, webUrl, () => w.url)
      try { await $.process.run(['open', w.url], { timeoutMs: 5000 }) } catch { $.ui.toast(`브라우저를 열지 못했습니다: ${w.url}`) }
      return { element: e.element }
    }
    const m = mine ? e.element.match(/^([tawx]):([^:]+):(\d+)(?::(\d+))?$/) : null
    if (!m) {
      // 다시 그리기 직전의 버튼이 눌리면 그 손잡이가 이미 사라져 있다: 무시하고 다음 그림을 기다린다
      try { return await next(e) } catch { return { element: e.element } }
    }
    const [, kind, mid, si, sj] = m
    const key = `${mid}:${si}`
    if (kind === 't') {
      const was = await read($, selected)
      await update($, selected, () => (was?.key === key ? null : { key, compose: false }))
      if (was?.key !== key && !(await read($, pending))) void $.ui.focus({ requestId: PANE, key: `a:${mid}:${si}:0` }).catch(noop)
      return
    }
    if (kind === 'x') { await update($, selected, () => null); return }
    if (kind === 'w') {
      await update($, selected, () => ({ key, compose: true }))
      // 입력칸으로 포커스를 옮긴다. 버튼에 남아 있으면 친 글자가 아래 입력창으로 간다
      void $.ui.focus({ requestId: PANE, key: `in:${key}` }).catch(noop)
      return
    }
    const hit = await taskAt($, mid, Number(si))
    const opt = hit && ACTIONS[hit.task.state][Number(sj)]
    if (hit && opt) await sendTask($, hit.ms, hit.task, Number(si), opt[0], opt[1])
  })

  // 직접 쓰기 입력칸에서 Enter
  on('ui.input', async ($, e, next) => {
    const m = e.plugin === 'playmaker' && e.requestId === PANE && e.kind === 'submit' ? e.element.match(/^in:([^:]+):(\d+)$/) : null
    if (!m) return next(e)
    const hit = await taskAt($, m[1], Number(m[2]))
    if (hit) await sendTask($, hit.ms, hit.task, Number(m[2]), '직접 쓴 지시', e.value)
    return { element: e.element, value: '' }
  })

  on('command.run', { command: 'playmaker' }, async ($, e) => {
    const web = /^web(\s|$)/.test(e.args.trim())
    const dir = await locate($, web ? e.args.trim().slice(3) : e.args)
    if (web) {
      if (!dir) return { text: '골 폴더를 찾지 못했습니다. /playmaker web <경로>' }
      return { text: await webText($, dir, await isPaseo($)) }
    }
    if (!dir) return { text: '골 폴더를 찾지 못했습니다. PLAN.md와 PROGRESS.md가 있는 폴더 경로를 인자로 주세요: /playmaker <경로>' }
    const b = await refresh($, dir, true)
    last = await stamp($, dir)
    await $.ui.open({ id: PANE, title: TITLE })
    // Paseo: 보드는 옆 웹 탭이 보여 주므로 채팅에는 한 줄 요약과 탭 상태만 남긴다. 웹을 못 켜면 마크다운 보드로 대신한다
    if (await isPaseo($)) {
      const w = await webLine($, dir)
      return { text: w ? `**${summaryLine(b)}**\n\n${w}` : summaryText(b) }
    }
    return { text: summaryText(b) }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button, Input, Link } = $.ui.resolve(e)
    const b = await read($, board)
    if (!b) return <Text dimColor>골 폴더를 찾지 못했습니다. /playmaker &lt;경로&gt;</Text>
    const mode = await read($, view)
    const open = await read($, expandDone)
    const cols = e.props.bodyColumns ?? 80
    const wide = cols >= WIDE
    const c = counts(b)

    const sent = await read($, pending)
    const sel = await read($, selected)
    const web = await read($, webUrl)
    const idx = (x: Card) => x.ms.tasks.indexOf(x.task)
    // 펼친 카드 아래 행동 줄
    const actionRow = (ms: Milestone, t: Task, i: number) => {
      if (sel?.key !== `${ms.id}:${i}`) return null
      if (sent) return <Text key="ar" color="cyan" wrap="truncate-end">{`   ↗ ${sent.task} ${sent.label} — 답이 끝나면 보낼 수 있습니다`}</Text>
      return (
        <Box key="ar" flexDirection="column" paddingLeft={3} marginBottom={1}>
          <Box key="arb" flexDirection="row" flexWrap="wrap">
            {ACTIONS[t.state].flatMap((o, j) => [<Button key={`a:${ms.id}:${i}:${j}`} label={o[0]} variant={j === 0 ? 'primary' : undefined} onPress={noop} />, <Text key={`sp${j}`}> </Text>])}
            <Button key={`w:${ms.id}:${i}`} label="직접 쓰기…" onPress={noop} />
            <Text key="spw"> </Text>
            <Button key={`x:${ms.id}:${i}`} label="닫기" dimColor onPress={noop} />
          </Box>
          {sel.compose ? <Input key={`in:${ms.id}:${i}`} placeholder="이 작업에 대해 세션에 보낼 말" submitLabel="보내기" autoFocus onSubmit={noop} /> : null}
        </Box>
      )
    }
    const card = (x: Card) => (
      <Box key={`cb-${x.key}`} flexDirection="column">
        <Button key={`t:${x.ms.id}:${idx(x)}`} plain onPress={noop}>
          <Text wrap="truncate-end" color={COLOR[x.task.state]} dimColor={x.task.inferred && x.task.state !== 'done'} bold={sel?.key === `${x.ms.id}:${idx(x)}`}>
            {ICON[x.task.state]} [M{x.ms.id}] {x.task.text}
          </Text>
        </Button>
        {actionRow(x.ms, x.task, idx(x))}
      </Box>
    )

    const column = (key: string, label: string, cards: Card[], width: string) => (
      <Box key={key} flexDirection="column" width={width} paddingRight={1} marginBottom={wide ? 0 : 1}>
        <Text bold>{label} ({cards.length})</Text>
        {cards.length === 0 ? <Text dimColor>없음</Text> : cards.slice(0, CAP).map(card)}
        {cards.length > CAP ? <Text dimColor>… 외 {cards.length - CAP}건</Text> : null}
      </Box>
    )

    const doneColumn = (width: string) => {
      const done = cardsOf(b, ['done'])
      if (open) return column('done', '완료', done, width)
      const per = b.milestones.map(ms => ({ ms, n: ms.tasks.filter(t => t.state === 'done').length })).filter(x => x.n > 0)
      return (
        <Box key="done" flexDirection="column" width={width}>
          <Text bold>완료 ({done.length})</Text>
          {per.length === 0 ? <Text dimColor>아직 없음</Text> : per.map(x => (
            <Text key={`dn-${x.ms.id}`} color="green">✓ M{x.ms.id} {x.n}건{x.ms.status === 'done' ? '' : ' (진행 중)'}</Text>
          ))}
        </Box>
      )
    }

    const doing = cardsOf(b, ['doing', 'waiting']).sort((x, y) => (x.task.state === 'waiting' ? 1 : 0) - (y.task.state === 'waiting' ? 1 : 0))
    const todo = cardsOf(b, ['todo'])

    const byState = wide ? (
      <Box key="cols" flexDirection="row">
        {column('todo', '대기', todo, '33%')}
        {column('doing', '진행', doing, '34%')}
        {doneColumn('33%')}
      </Box>
    ) : (
      <Box key="cols" flexDirection="column">
        {column('doing', '진행', doing, '100%')}
        {column('todo', '대기', todo, '100%')}
        {doneColumn('100%')}
      </Box>
    )

    const byMilestone = (
      <Box key="ms" flexDirection="column">
        {b.milestones.map(ms => {
          const n = ms.tasks.filter(t => t.state === 'done').length
          const head = ms.status === 'done' ? '✓' : ms.status === 'current' ? (ms.waiting ? '⏸' : '▶') : '·'
          const fold = ms.status === 'done' && !open
          return (
            <Box key={`m-${ms.id}`} flexDirection="column" marginBottom={1}>
              <Text bold color={ms.status === 'current' ? 'yellow' : ms.status === 'done' ? 'green' : undefined}>
                {head} M{ms.id} {ms.name} ({n}/{ms.tasks.length})
              </Text>
              {fold ? null : ms.tasks.map((t, i) => (
                <Box key={`mb-${ms.id}-${i}`} flexDirection="column">
                  <Button key={`t:${ms.id}:${i}`} plain onPress={noop}>
                    <Text wrap="truncate-end" color={COLOR[t.state]} dimColor={t.inferred && t.state !== 'done'} bold={sel?.key === `${ms.id}:${i}`}>
                      {'  '}{t.state === 'done' ? '[x]' : t.state === 'doing' ? '[>]' : t.state === 'waiting' ? '[!]' : '[ ]'} {t.id ? `${t.id}: ` : ''}{t.text}
                    </Text>
                  </Button>
                  {actionRow(ms, t, i)}
                </Box>
              ))}
            </Box>
          )
        })}
      </Box>
    )

    return (
      <Box flexDirection="column">
        {b.goal ? <Text bold wrap="truncate-end">{b.goal}</Text> : null}
        <Text dimColor>{summaryLine(b)}</Text>
        {b.mismatch.slice(0, 2).map((m, i) => <Text key={`mm-${i}`} color="yellow" wrap="truncate-end">⚠ {m}</Text>)}
        {sent ? <Text key="sent" color="cyan" wrap="truncate-end">{`↗ ${sent.task} ${sent.label} 보냄 · 세션이 답하는 중 (끝나면 다른 카드도 누를 수 있습니다)`}</Text> : null}
        <Box key="bar" flexDirection="row" marginY={1}>
          <Button key="view" label={mode === 'state' ? '마일스톤별 보기' : '상태별 보기'} onPress={() => update($, view, v => (v === 'state' ? 'milestone' : 'state'))} />
          <Text> </Text>
          <Button key="done" label={open ? '완료 접기' : '완료 펼치기'} onPress={() => update($, expandDone, v => !v)} />
          <Text> </Text>
          <Button key="web" label="브라우저로 열기" onPress={noop} />
          <Text> </Text>
          <Button key="close" label="✕ 닫기" dimColor role="dismiss" onPress={noop} />
        </Box>
        {mode === 'state' ? byState : byMilestone}
        {c.taskTotal > 0 && b.milestones.every(m => m.source === 'legacy') ? (
          <Text dimColor wrap="truncate-end">작업 상태는 마일스톤 기록에서 추정했습니다 (흐린 카드). goaljaby 0.7+는 작업별로 기록합니다.</Text>
        ) : null}
        {b.lastValidation ? <Text dimColor wrap="truncate-end">최근 검증: {b.lastValidation}</Text> : null}
        {web ? <Box key="weblink" flexDirection="row"><Text dimColor>웹 보드: </Text><Link key="wl" href={web} label={web} /></Box> : null}
        <Text dimColor wrap="truncate-end">카드를 누르면 아래에 행동 버튼이 펼쳐집니다 (마우스 또는 Ctrl+X Tab 뒤 화살표·Enter)</Text>
      </Box>
    )
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const b = await read($, board)
    if (!b || !b.show) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        <Text dimColor wrap="truncate-end">{summaryLine(b)}</Text>
        {await next(e)}
      </Box>
    )
  })
}
