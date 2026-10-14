import { test, expect, describe } from 'claude-code/testing'
import { parseBoard, summaryLine } from './hooks/parse'

// ── fixtures ────────────────────────────────────────────────
// goaljaby 0.7+ 체크리스트 형식
const PLAN_NEW = `# PLAN
## 마일스톤 1: 스캐폴딩
- 범위(Scope): 프로젝트 생성, DB 스키마
- 완료 조건: 빌드 통과

작업 (상태: \`[ ]\` 대기 · \`[>]\` 진행 · \`[x]\` 완료 · \`[!]\` 사람 대기)
- [x] M1-T1: 프로젝트를 생성한다
- [x] M1-T2: DB 스키마를 만든다

## 마일스톤 2: 인증
- 범위(Scope): OAuth, 승인 게이트
- [>] M2-T1: OAuth 콜백을 연결한다
- [!] M2-T2: 운영자 승인 계정을 기다린다
- [ ] M2-T3: 마일스톤 검증을 실행한다

## 마일스톤 3: 배포
- [ ] M3-T1: 배포 설정을 만든다
`
const PROGRESS_NEW = `# PROGRESS
## 현재 골
인증까지 붙인 MVP를 배포한다.
## 현재 마일스톤
M2 인증
## 완료
- **M1 스캐폴딩** (2026-10-13)
## 마지막 검증 결과

\`\`\`text
2026-10-13 npm run build 통과
\`\`\`
## 실패 시도
- (없음)
`

// goaljaby 0.6 형식 (체크리스트 없음) + 병렬 진행·사람 대기 (tesladesk media-path-fix 패턴)
const PLAN_LEGACY = `# PLAN
## 마일스톤 1: 송신 위임
- 범위(Scope): 위임 로직, 후보 완화(prflx, 주소 없음)
- 완료 조건: 테스트 통과
## 마일스톤 2: 실차 기록
- 범위(Scope): 화면 표시 확인, 3초 측정
## 마일스톤 3: 네트워크 스파이크
- 범위(Scope): S1 인터넷 공유, S2 별칭 유지
## 마일스톤 4: 배포
- 범위(Scope): 서명, 설치
`
const PROGRESS_LEGACY = `# PROGRESS
## 현재 골
실차에서 3초 안에 화면이 뜬다.
## 현재 마일스톤
M2 실차 기록 — 화면 표시 확인 완료, 3초 기준은 사람 측정 대기. M3 — S1은 사용자 동석 대기.
## 완료
- **M1 송신 위임** (2026-09-14)
  - WebRTCTransport.swift 수정
  - 관련 테스트 추가
- 메모: 배포 체크리스트는 나중에 정리
## 실패 시도
- 1차: ICE 후보 누락
`

// 사람이 손으로 쓴 표 형식 PLAN (tesladesk PRD 패턴)
const PLAN_TABLE = `# PLAN
## 마일스톤과 통과 조건
| 단계 | 허용 범위 | 통과 조건 | 책임 |
|---|---|---|---|
| M1a 최소 진단 준비 | 설정 후보, 진단 페이지·타이머 | 테스트 | 에이전트 |
| M1b 사람 수행 실차 진단 | 핫스팟 확인 | 원자료 | 사람 |
`

// canonical + ### 헤딩 혼합
const PLAN_MIXED = `# PLAN
## 마일스톤 1: 기본
- [x] M1-T1: 기본 작업
### M2 추가 작업
- [>] M2-T1: 추가 작업을 한다
`

describe('parser', () => {
  test('체크리스트 마커 4종 → 상태 4종, 마일스톤 상태는 작업에서', () => {
    const b = parseBoard('/g', PLAN_NEW, PROGRESS_NEW, 0)
    expect(b.milestones.map(m => m.status)).toEqual(['done', 'current', 'todo'])
    expect(b.milestones[1].tasks.map(t => t.state)).toEqual(['doing', 'waiting', 'todo'])
    expect(b.milestones[1].tasks[0].id).toBe('M2-T1')
    expect(b.milestones[1].waiting).toBe(true)
    expect(b.milestones.every(m => m.source === 'checklist')).toBe(true)
    expect(b.mismatch).toEqual([])
    expect(summaryLine(b)).toBe('골 1/3 · 진행 M2 · 작업 2/6 · ⏸ 사람 대기 1')
  })

  test('최근 검증: 코드 펜스를 건너뛰고 실제 내용', () => {
    expect(parseBoard('/g', PLAN_NEW, PROGRESS_NEW, 0).lastValidation).toBe('2026-10-13 npm run build 통과')
  })

  test('실패 시도 "(없음)"은 0건', () => {
    expect(parseBoard('/g', PLAN_NEW, PROGRESS_NEW, 0).failed).toBe(0)
  })

  test('PROGRESS는 완료라는데 체크리스트가 남으면 불일치 표시', () => {
    const p = PROGRESS_NEW.replace('- **M1 스캐폴딩** (2026-10-13)', '- **M1 스캐폴딩** (2026-10-13)\n- **M2 인증** 완료')
    const b = parseBoard('/g', PLAN_NEW, p, 0)
    expect(b.milestones[1].status).toBe('current')
    expect(b.mismatch.join()).toContain('M2: PROGRESS는 완료')
  })

  test('기존 형식: 완료 하위 항목, 병렬 진행, 사람 대기 추정', () => {
    const b = parseBoard('/g', PLAN_LEGACY, PROGRESS_LEGACY, 0)
    expect(b.milestones.map(m => m.status)).toEqual(['done', 'current', 'current', 'todo'])
    expect(b.milestones[0].tasks.map(t => t.text)).toEqual(['WebRTCTransport.swift 수정', '관련 테스트 추가'])
    expect(b.milestones[1].tasks.map(t => t.state)).toEqual(['waiting', 'waiting'])
    expect(b.milestones[1].tasks[0].inferred).toBe(true)
    expect(b.milestones[3].tasks.map(t => t.text)).toEqual(['서명', '설치'])
    expect(b.failed).toBe(1)
    expect(summaryLine(b)).toContain('진행 M2·M3')
  })

  test('산문 속 마일스톤 이름만으로 완료 판정하지 않음', () => {
    // 완료 섹션 "- 메모: 배포 체크리스트는..."에 '배포'가 있지만 M4는 완료가 아님
    expect(parseBoard('/g', PLAN_LEGACY, PROGRESS_LEGACY, 0).milestones[3].status).toBe('todo')
  })

  test('범위의 괄호 안 쉼표는 자르지 않음', () => {
    expect(parseBoard('/g', PLAN_LEGACY, '', 0).milestones[0].tasks.map(t => t.text)).toEqual(['위임 로직', '후보 완화(prflx, 주소 없음)'])
  })

  test('표 형식 PLAN: 마일스톤과 허용 범위 열', () => {
    const b = parseBoard('/g', PLAN_TABLE, '', 0)
    expect(b.milestones.map(m => m.id)).toEqual(['1a', '1b'])
    expect(b.milestones[0].tasks.map(t => t.text)).toEqual(['설정 후보', '진단 페이지·타이머'])
  })

  test('canonical + ### 혼합: 둘 다 찾고 ### 아래 체크리스트도 읽음', () => {
    const b = parseBoard('/g', PLAN_MIXED, '', 0)
    expect(b.milestones.map(m => m.id)).toEqual(['1', '2'])
    expect(b.milestones[1].tasks[0].state).toBe('doing')
    expect(b.milestones[0].tasks.length).toBe(1)
  })
})

// ── engine mocks ────────────────────────────────────────────
function mockEngine(on: any, files: Record<string, string>, mtime = 100) {
  const opened: string[] = []
  on('session.cwd', () => ({ value: '/w' }))
  on('fs.exists', ($: any, e: any) => ({ value: e.path in files }))
  on('fs.read', ($: any, e: any) => ({ value: files[e.path] }))
  on('fs.stat', ($: any, e: any) => ({ value: { kind: 'file', size: (files[e.path] ?? '').length, mtimeMs: mtime, isLink: false } }))
  on('fs.list', ($: any, e: any) => ({ value: e.path === '/w' ? [{ name: 'node_modules', kind: 'dir', size: 0 }, { name: 'goal', kind: 'dir', size: 0 }] : [] }))
  on('clock.now', () => ({ value: 1 }))
  on('ui.open', ($: any, e: any) => { opened.push(e.id); return { value: { isPlaced: true } } })
  return opened
}

const NEW = { '/w/goal/PLAN.md': PLAN_NEW, '/w/goal/PROGRESS.md': PROGRESS_NEW }
const LEGACY = { '/w/goal/PLAN.md': PLAN_LEGACY, '/w/goal/PROGRESS.md': PROGRESS_LEGACY }
const RUN = { command: 'playmaker', args: '', origin: { kind: 'user' }, presentation: 'transcript' } as any
const pane = (surface: any, cols: number) => ({
  plugin: 'playmaker', surface, component: 'Pane', requestId: 'playmaker',
  props: { title: '골 진행', isFocused: false, bodyColumns: cols, placement: 'dock' } as any,
})

test('명령: 자동 탐색 + 작업 단위 요약', async ($, on) => {
  const opened = mockEngine(on, NEW)
  const r: any = await $.command.run(RUN)
  const text = JSON.stringify(r)
  expect(text).toContain('골 1/3 · 진행 M2')
  expect(text).toContain('▶️ M2-T1: OAuth 콜백을 연결한다')
  expect(text).toContain('⏸️ M2-T2')
  expect(text).toContain('| 대기 (2) | 진행 (2) | 완료 (2) |')
  expect(opened).toEqual(['playmaker'])
})

test('명령 web: 웹 보드 서버를 켜고 주소를 돌려줌 (pane은 안 엶)', async ($, on) => {
  const opened = mockEngine(on, NEW)
  const runs: any[] = []
  on('process.run', ($: any, e: any) => { runs.push(e.argv); return { value: { exitCode: 0, stdout: 'URL http://127.0.0.1:4778/ started\n', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } } })
  const text = JSON.stringify(await $.command.run({ ...RUN, args: 'web goal' }))
  expect(runs.length).toBe(1)
  expect(runs[0][0]).toBe('sh')
  expect(String(runs[0][1]).endsWith('/web/start.sh')).toBe(true)
  expect(runs[0][2]).toBe('/w/goal')
  expect(text).toContain('http://127.0.0.1:4778/')
  expect(opened).toEqual([])
})

test('Paseo 감지: /playmaker는 한 줄 요약 + 탭 열기 (표는 웹 탭이 대신)', async ($, on) => {
  mockEngine(on, NEW)
  const calls: string[] = []
  on('env.get', ($: any, e: any) => ({ value: e.name === 'PASEO_AGENT_ID' ? 'agent-1' : undefined }))
  on('process.run', () => ({ value: { exitCode: 0, stdout: 'URL http://127.0.0.1:4778/ started\n', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('mcp.call', ($: any, e: any) => {
    calls.push(`${e.server}/${e.tool}`)
    const text = e.tool === 'browser_list_tabs' ? JSON.stringify({ ok: true, result: { tabs: [] } }) : '{"ok":true}'
    return { value: { content: [{ type: 'text', text }], isError: false } }
  })
  const text = JSON.stringify(await $.command.run(RUN))
  expect(text).toContain('골 1/3 · 진행 M2')
  expect(text).toContain('playmaker 탭에 있습니다 (새로 열었음)')
  expect(text).not.toContain('| 대기 (')
  expect(calls).toEqual(['paseo/browser_list_tabs', 'paseo/browser_new_tab'])
})

test('Paseo 감지: 같은 주소 탭이 있으면 새로 열지 않음', async ($, on) => {
  mockEngine(on, NEW)
  const calls: string[] = []
  on('env.get', () => ({ value: 'agent-1' }))
  on('process.run', () => ({ value: { exitCode: 0, stdout: 'URL http://127.0.0.1:4778/ reused\n', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('mcp.call', ($: any, e: any) => {
    calls.push(e.tool)
    return { value: { content: [{ type: 'text', text: JSON.stringify({ result: { tabs: [{ browserId: 'b1', url: 'http://127.0.0.1:4778/', title: 'playmaker' }] } }) }], isError: false } }
  })
  const text = JSON.stringify(await $.command.run({ ...RUN, args: 'web' }))
  expect(text).toContain('이미 열려 있습니다')
  expect(calls).toEqual(['browser_list_tabs'])
})

test('명령 web: 서버 실패 시 원인 출력', async ($, on) => {
  mockEngine(on, NEW)
  on('process.run', () => ({ value: { exitCode: 1, stdout: 'ERR node를 찾지 못했습니다\n', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  const text = JSON.stringify(await $.command.run({ ...RUN, args: 'web' }))
  expect(text).toContain('웹 보기를 켜지 못했습니다')
  expect(text).toContain('node를 찾지 못했습니다')
})

test('명령: 골 폴더 없음', async ($, on) => {
  mockEngine(on, {})
  expect(JSON.stringify(await $.command.run(RUN))).toContain('골 폴더를 찾지 못했습니다')
})

for (const surface of ['terminal', 'desktop'] as const) {
  describe(surface, () => {
    test('넓은 폭: 대기 · 진행 · 완료 3열', async ($, on) => {
      mockEngine(on, NEW)
      await $.command.run(RUN)
      const ui: any = await $.ui.mount(pane(surface, 90))
      expect(await ui.find({ type: 'Text', text: /^대기 \(2\)$/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /^진행 \(2\)$/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /^완료 \(2\)$/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /▶ \[M2\] OAuth 콜백을 연결한다/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /⏸ \[M2\] 운영자 승인 계정을 기다린다/ })).toBeDefined()
      expect(JSON.stringify(await ui.drawn())).toContain('"flexDirection":"row"')
    })

    test('좁은 폭: 진행 → 대기 → 완료 세로 순서', async ($, on) => {
      mockEngine(on, NEW)
      await $.command.run(RUN)
      const ui: any = await $.ui.mount(pane(surface, 50))
      const tree = JSON.stringify(await ui.drawn())
      const i = (s: string) => tree.indexOf(s)
      // 열 제목은 자식 노드로 나뉘므로 정확히 일치하는 라벨 노드 위치를 비교
      expect(i('"진행"')).toBeGreaterThan(-1)
      expect(i('"진행"')).toBeLessThan(i('"대기"'))
      expect(i('"대기"')).toBeLessThan(i('"완료 ("')) // 접힌 완료 열 제목은 한 노드
      expect(tree).not.toContain('"flexDirection":"row","children":[{"type":"Box","props":{"flexDirection":"column","width":"33%"')
    })

    test('완료는 접혀 있다가 펼치기 버튼으로 카드 표시', async ($, on) => {
      mockEngine(on, NEW)
      await $.command.run(RUN)
      const ui: any = await $.ui.mount(pane(surface, 90))
      expect(await ui.find({ type: 'Text', text: /✓ M1 2건/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /DB 스키마를 만든다/ })).toBeUndefined()
      await ui.press({ key: 'done' })
      expect(await ui.find({ type: 'Text', text: /✓ \[M1\] DB 스키마를 만든다/ })).toBeDefined()
    })

    test('마일스톤별 보기: 체크리스트', async ($, on) => {
      mockEngine(on, NEW)
      await $.command.run(RUN)
      const ui: any = await $.ui.mount(pane(surface, 90))
      await ui.press({ key: 'view' })
      expect(await ui.find({ type: 'Text', text: /⏸ M2 인증 \(0\/3\)/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /\[>\] M2-T1: OAuth/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /\[!\] M2-T2/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /M1-T1/ })).toBeUndefined() // 완료 마일스톤은 접힘
    })

    test('기존 형식 골: 추정 표시 안내', async ($, on) => {
      mockEngine(on, LEGACY)
      await $.command.run(RUN)
      const ui: any = await $.ui.mount(pane(surface, 90))
      expect(await ui.find({ type: 'Text', text: /⏸ \[M2\] 3초 측정/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /추정했습니다/ })).toBeDefined()
    })

    test('band 한 줄 요약', async ($, on) => {
      mockEngine(on, NEW)
      on('ui.render', { component: 'AbovePrompt' }, ($: any, e: any) => { const { Text } = $.ui.resolve(e); return <Text>engine-base</Text> })
      await $.command.run(RUN)
      const ui: any = await $.ui.mount({ plugin: 'playmaker', surface, component: 'AbovePrompt', props: { hasSurvey: false, isWorking: true, maxRows: 3, bodyColumns: 80 } as any })
      expect(await ui.find({ type: 'Text', text: /골 1\/3 · 진행 M2 · 작업 2\/6 · ⏸ 사람 대기 1/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /engine-base/ })).toBeDefined()
    })
  })
}

test('band: 골이 없으면 엔진 기본만', async ($, on) => {
  on('ui.render', { component: 'AbovePrompt' }, ($: any, e: any) => { const { Text } = $.ui.resolve(e); return <Text>engine-base</Text> })
  const ui: any = await $.ui.mount({ plugin: 'playmaker', surface: 'terminal', component: 'AbovePrompt', props: { hasSurvey: false, isWorking: false, maxRows: 3, bodyColumns: 80 } as any })
  expect(await ui.find({ type: 'Text', text: /골 \d/ })).toBeUndefined()
})

const START = { cwd: '/w', surface: 'terminal', isInteractive: true } as any
const DONE_PLAN = PLAN_NEW.replace(/\[[ >!]\]/g, '[x]')
for (const c of [
  { name: '진행 중인 골', plan: PLAN_NEW, mtime: 100, opens: true },
  { name: '끝난 골', plan: DONE_PLAN, mtime: 100, opens: false },
  { name: '8일 묵은 골', plan: PLAN_NEW, mtime: -8 * 24 * 3600 * 1000, opens: false },
]) {
  test(`세션 시작 자동 열림: ${c.name} → ${c.opens ? '열림' : '안 열림'}`, async ($, on) => {
    const opened = mockEngine(on, { '/w/goal/PLAN.md': c.plan, '/w/goal/PROGRESS.md': PROGRESS_NEW }, c.mtime)
    on('command.register', () => ({ value: undefined }))
    on('clock.every', () => ({ value: { cancel() {} } }))
    on('session.start', ($: any, e: any) => e)
    on('ui.render', { component: 'AbovePrompt' }, ($: any, e: any) => { const { Text } = $.ui.resolve(e); return <Text>engine-base</Text> })
    await $.session.start(START)
    expect(opened.length).toBe(c.opens ? 1 : 0)
    const ui: any = await $.ui.mount({ plugin: 'playmaker', surface: 'terminal', component: 'AbovePrompt', props: { hasSurvey: false, isWorking: false, maxRows: 3, bodyColumns: 80 } as any })
    const band = await ui.find({ type: 'Text', text: /골 \d\/3/ })
    if (c.opens) expect(band).toBeDefined(); else expect(band).toBeUndefined()
  })
}

test('터미널 카드 누르기: 아래에 행동 줄이 펼쳐지고, 버튼으로 이 세션에 지시, 답이 끝날 때까지 잠금', async ($, on) => {
  mockEngine(on, NEW)
  const submitted: string[] = []
  const toasts: string[] = []
  let asked = 0
  on('tool.call', ($: any, e: any, next: any) => { if (e.tool === 'AskUserQuestion') asked++; return next(e) })
  on('prompt.submit', ($: any, e: any) => { submitted.push(e.text); return { text: e.text } })
  on('ui.toast', ($: any, e: any) => { toasts.push(JSON.stringify(e)); return { value: undefined } })
  await $.command.run(RUN)
  const ui: any = await $.ui.mount(pane('terminal', 90))
  await ui.press({ key: 't:2:1' })
  expect(await ui.find({ type: 'Button', key: 'a:2:1:0' })).toBeDefined()
  expect(JSON.stringify(await ui.drawn())).toContain('승인하고 진행')
  await ui.press({ key: 'a:2:1:0' })
  expect(asked).toBe(0)
  expect(submitted.length).toBe(1)
  expect(submitted[0]).toContain('[playmaker · M2-T2]')
  expect(submitted[0]).toContain('이 작업은 승인합니다')
  expect(await ui.find({ type: 'Button', key: 'a:2:1:0' })).toBeUndefined()
  await ui.press({ key: 't:2:0' })
  expect(await ui.find({ type: 'Button', key: 'a:2:0:0' })).toBeUndefined()
  expect(JSON.stringify(await ui.drawn())).toContain('답이 끝나면 보낼 수 있습니다')
})

test('터미널 직접 쓰기: 입력칸 Enter로 이 세션에 지시', async ($, on) => {
  mockEngine(on, NEW)
  const submitted: string[] = []
  on('prompt.submit', ($: any, e: any) => { submitted.push(e.text); return { text: e.text } })
  await $.command.run(RUN)
  const ui: any = await $.ui.mount(pane('terminal', 90))
  await ui.press({ key: 't:2:0' })
  await ui.press({ key: 'w:2:0' })
  expect(await ui.find({ type: 'Input', key: 'in:2:0' })).toBeDefined()
  await ui.input({ key: 'in:2:0', text: '콜백 URL은 /auth/cb로 해 주세요', kind: 'submit' })
  expect(submitted.length).toBe(1)
  expect(submitted[0]).toContain('[playmaker · M2-T1]')
  expect(submitted[0]).toContain('콜백 URL은 /auth/cb로 해 주세요')
})

test('터미널 패널: 브라우저로 열기는 웹 서버를 켜고 open으로 열며 링크를 보여 준다', async ($, on) => {
  mockEngine(on, NEW)
  const runs: string[][] = []
  on('process.run', ($: any, e: any) => {
    runs.push([...e.argv])
    const out = e.argv[0] === 'sh' ? 'URL http://127.0.0.1:4777/ started\n' : ''
    return { value: { exitCode: 0, stdout: out, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  await $.command.run(RUN)
  const ui: any = await $.ui.mount(pane('terminal', 90))
  await ui.press({ key: 'web' })
  expect(runs.some(a => a[0] === 'sh' && String(a[1]).endsWith('/web/start.sh'))).toBe(true)
  expect(runs.some(a => a[0] === 'open' && a[1] === 'http://127.0.0.1:4777/')).toBe(true)
  await ui.redraw()
  expect(JSON.stringify(await ui.drawn())).toContain('"type":"Link","props":{"href":"http://127.0.0.1:4777/"')
})

test('터미널 패널: 닫기는 pane을 닫고 입력창 위 요약 줄도 내린다', async ($, on) => {
  mockEngine(on, NEW)
  on('ui.render', { component: 'AbovePrompt' }, ($: any, e: any) => { const { Text } = $.ui.resolve(e); return <Text>engine-base</Text> })
  const closed: string[] = []
  on('ui.close', ($: any, e: any) => { closed.push(e.id); return { value: undefined } })
  await $.command.run(RUN)
  const ui: any = await $.ui.mount(pane('terminal', 90))
  await ui.press({ key: 'close' })
  expect(closed).toEqual(['playmaker'])
  const band: any = await $.ui.mount({ plugin: 'playmaker', surface: 'terminal', component: 'AbovePrompt', props: { hasSurvey: false, isWorking: true, maxRows: 3, bodyColumns: 80 } as any })
  expect(await band.find({ type: 'Text', text: /engine-base/ })).toBeDefined()
  expect(await band.find({ type: 'Text', text: /골 1\/3/ })).toBeUndefined()
})
