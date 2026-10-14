// 웹 보기 서버 테스트: node --test plugins/playmaker/web/server.test.mjs
// 가짜 paseo CLI로 세션 목록·전송을 흉내 내고, 읽기·연결·토큰·출처 검사를 확인한다.
import { test, before, after } from 'node:test'
import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { chmodSync, mkdtempSync, readFileSync, existsSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const PLAN = `# PLAN

## 마일스톤 1: 저장과 복원
- 완료 조건: 새로고침 뒤 값이 남는다
- [x] M1-T1: 토글 변경 시 저장한다
- [>] M1-T2: 로드 시 복원한다

## 마일스톤 2: 격리
- [!] M2-T1: 사용자 키만 저장하도록 제한한다
- [ ] M2-T2: 검증을 실행한다
`
const PROGRESS = `# PROGRESS

## 현재 골
설정 토글을 유지한다.

## 현재 마일스톤
M1 진행 중.

## 완료
(없음)
`

const tmp = mkdtempSync(join(tmpdir(), 'pm-web-test-'))
const goal = join(tmp, 'goal')
const sentLog = join(tmp, 'sent.log')
const fake = join(tmp, 'paseo')
const portFile = join(tmp, 'url')
let child, url, token

before(async () => {
  await import('node:fs').then(fs => fs.mkdirSync(goal))
  writeFileSync(join(goal, 'PLAN.md'), PLAN)
  writeFileSync(join(goal, 'PROGRESS.md'), PROGRESS)
  // 가짜 paseo: ls --json 은 이 골 폴더에서 도는 세션 둘을, send 는 인자를 기록
  writeFileSync(fake, `#!/bin/sh
case "$1" in
  ls) printf '[{"id":"aaaa1111-0000","shortId":"aaaa111","name":"골 작업 세션","status":"idle","cwd":"${tmp}"},{"id":"bbbb2222-0000","shortId":"bbbb222","name":"다른 세션","status":"running","cwd":"${tmp}"},{"id":"cccc3333-0000","shortId":"cccc333","name":"남의 폴더","status":"idle","cwd":"/elsewhere"}]' ;;
  send) shift; printf '%s\\n' "$@" >> "${sentLog}"; printf '{"status":"sent"}' ;;
esac
`)
  chmodSync(fake, 0o755)
  child = spawn(process.execPath, [new URL('./server.mjs', import.meta.url).pathname, '--dir', goal, '--port', '4890', '--port-file', portFile, '--paseo', fake, '--project', tmp, '--agent', 'aaaa1111-0000'], { stdio: 'ignore' })
  for (let i = 0; i < 50 && !existsSync(portFile + '.token'); i++) await new Promise(r => setTimeout(r, 100))
  for (let i = 0; i < 50 && !(existsSync(portFile) && readFileSync(portFile, 'utf8')); i++) await new Promise(r => setTimeout(r, 100))
  url = readFileSync(portFile, 'utf8')
  token = readFileSync(portFile + '.token', 'utf8')
})

after(() => child?.kill())

const post = (path, body, headers = {}) => fetch(url + path, {
  method: 'POST',
  headers: { 'content-type': 'application/json', 'x-playmaker-token': token, origin: url.replace(/\/$/, ''), ...headers },
  body: JSON.stringify(body),
})

test('health: 이 골 폴더를 알려 준다', async () => {
  const h = await (await fetch(url + 'api/health')).json()
  assert.equal(h.app, 'playmaker')
  assert.equal(h.dir, goal)
})

test('board: 마커 4종을 상태로 읽고, 같은 프로젝트 세션만 목록에 올린다', async () => {
  const b = await (await fetch(url + 'api/board')).json()
  assert.deepEqual(b.milestones[0].tasks.map(t => t.state), ['done', 'doing'])
  assert.deepEqual(b.milestones[1].tasks.map(t => t.state), ['waiting', 'todo'])
  assert.equal(b.paseo, true)
  assert.equal(b.link.name, '골 작업 세션')
  assert.deepEqual(b.agents.map(a => a.name), ['골 작업 세션', '다른 세션'])
})

test('페이지: 토큰이 심겨 있고 자리표시자는 남지 않는다', async () => {
  const html = await (await fetch(url)).text()
  assert.ok(html.includes(token))
  assert.ok(!html.includes('__TOKEN__'))
})

test('쓰기 요청: 토큰이 없거나 다른 출처면 403', async () => {
  assert.equal((await post('api/send', { text: 'x' }, { 'x-playmaker-token': 'wrong' })).status, 403)
  assert.equal((await post('api/send', { text: 'x' }, { origin: 'http://evil.example' })).status, 403)
  assert.equal((await post('api/link', { agentId: 'bbbb2222-0000' }, { 'x-playmaker-token': '' })).status, 403)
})

test('전송: 연결된 세션으로 paseo send, 보낸 기록에 작업·이름이 남는다', async () => {
  const r = await (await post('api/send', { text: '[playmaker · M2-T1] 확인', task: 'M2-T1', label: '승인하고 진행' })).json()
  assert.equal(r.ok, true)
  assert.equal(r.to, '골 작업 세션')
  const argv = readFileSync(sentLog, 'utf8').trim().split('\n')
  assert.equal(argv[0], 'aaaa1111-0000')
  assert.ok(argv.includes('--no-wait'))
  assert.ok(argv.includes('[playmaker · M2-T1] 확인'))
  const b = await (await fetch(url + 'api/board')).json()
  assert.equal(b.sent[0].task, 'M2-T1')
  assert.equal(b.sent[0].label, '승인하고 진행')
})

test('연결: auto는 살아 있는 연결을 바꾸지 않고, user는 바꾼다', async () => {
  let b = await (await post('api/link', { agentId: 'bbbb2222-0000', mode: 'auto' })).json()
  assert.equal(b.link.name, '골 작업 세션')
  b = await (await post('api/link', { agentId: 'bbbb2222-0000', mode: 'user' })).json()
  assert.equal(b.link.name, '다른 세션')
})

test('빈 메시지는 400', async () => {
  assert.equal((await post('api/send', { text: '   ' })).status, 400)
})
