# 데이터 모델 — 선언 스키마와 산출물 구조

> 이 프로젝트는 DB가 없다. "데이터 모델" = **선언 스키마**(YAML/스크립트 계약)와 **잡 디렉토리 구조**다.

---

## 1. 관계도

```
                    ┌──────────────────┐
                    │  실행형태 (shape) │   5종
                    │  serial          │
                    │  parallel        │
                    │  chain           │
                    │  fanout          │
                    │  tournament      │
                    └────────┬─────────┘
                             │ 1:N
                             ▼
        ┌────────────────────────────────────┐
        │            Task                    │
        │  name / instruction / gates / cwd  │
        │  command | provider                │
        └───────┬────────────────────┬───────┘
                │ (tournament일 때만) │
                │ 1:N                 │
                ▼                     │
        ┌───────────────┐             │
        │  Contender    │             │
        │  provider     │             │
        │  worktree     │             │
        └───────┬───────┘             │
                │ 1:1                 │ 1:1
                ▼                     ▼
        ┌───────────────┐     ┌───────────────┐
        │  Scorecard    │     │  GateResult   │
        │  gatesPassed  │◄────┤  name/pass    │
        │  diffSize     │     │  command      │
        │  rank         │     └───────────────┘
        └───────┬───────┘
                │ N:1
                ▼
        ┌───────────────┐
        │   Adoption    │
        │  winner       │
        │  mode:        │
        │   winner|merge│
        │  transplants[]│
        └───────────────┘
```

---

## 2. 실행형태 (shape) — 5종

> ⚠️ 가정 6: 아래 키 이름은 **본 저장소 자체 정의**다. 원본 그림의 스펙 문서를 저장소에서 찾지 못했다 (`grep -rln "토너먼트\|tournament" plugins/ docs/` → 0건). 외부 스펙이 확인되면 키를 거기에 맞춘다.

| shape | 한글 라벨 | 의미 | 의존 선언 | 격리 |
|---|---|---|---|---|
| `serial` | 직렬 | 한 줄로 차례차례 | `depends_on: [이전]` | 불필요 |
| `parallel` | 병렬 | 안 부딪히는 묶음은 같이 | 없음 (기본) | 불필요 |
| `chain` | 플랜 뒤에 플랜 | 앞이 끝나야 뒤가 시작 | `depends_on: [플랜]` | 불필요 |
| `fanout` | 부모와 자식 | 자식이 다 끝나야 부모도 | `parent: <name>` | 불필요 |
| `tournament` | 토너먼트 | 여럿이 붙고 채점으로 고른다 | `contenders: [...]` | **워크트리 필수** |

`serial`과 `chain`은 둘 다 순서 의존이지만 단위가 다르다 — `serial`은 태스크 단위, `chain`은 스테이지(플랜) 단위다. 구현상 `serial`은 `depends_on` 그래프의 특수형이므로, **`depends_on` 하나로 `serial`·`chain`·`fanout`을 전부 표현하고** `parallel`은 의존 없음, `tournament`만 별도 키를 갖는다.

---

## 3. Task 스키마 (품앗이 YAML)

기존 필드는 그대로 두고 확장만 한다.

```yaml
pumasi:
  defaults:
    command: "codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check"

  tasks:
    - name: auth-token
      command: "grok --no-auto-update --no-alt-screen --sandbox workspace --always-approve -p"   # ← grok 추가
      cwd: null                     # 기존 필드 (pumasi-job.js:434)
      instruction: |
        ...
      gates:
        - name: "타입 체크"
          command: "npx tsc --noEmit src/auth/token.ts"
```

| 필드 | 타입 | 기존/신규 | 근거 |
|---|---|---|---|
| `name` | string | 기존 | — |
| `instruction` | string | 기존 | — |
| `gates[]` | `{name, command}` \| `{label, bash}` | 기존 | 두 형식 모두 저장소에 존재 |
| `command` | string | 기존 | `pumasi-job.js:434` — 태스크별 오버라이드 |
| `cwd` | string\|null | 기존 | `pumasi-job.js:457-458` (`task.cwd > job.cwd > process.cwd()`) |

**품앗이에는 신규 필드가 없다.** grok 추가는 `command` 문자열 값 하나이므로 스키마 변경이 아니다.

---

## 4. Tournament 스키마 (끼리끼리 Workflow)

토너먼트는 워크플로우 스크립트가 소비하는 **JS 객체**다. YAML이 아니다 — 끼리끼리 Workflow 경로는 인라인 스크립트를 생성하기 때문이다 (SKILL.md Step 4-W).

```javascript
const TOURNAMENT = {
  task: {
    name: 'auth-token',
    instruction: '...',           // 참가자 전원에게 동일하게 전달
    gates: [                      // 참가자 전원에게 동일하게 적용
      { name: 'tsc', command: 'npx tsc --noEmit src/auth/token.ts' },
    ],
  },
  contenders: [                   // 기본 2명 (가정 5)
    { provider: 'codex', worktree: '.kkirikkiri/arena/auth-token/codex' },
    { provider: 'grok',  worktree: '.kkirikkiri/arena/auth-token/grok'  },
  ],
  judge: 'gates',                 // 'gates' | 'model' — 기본 gates
  adopt: 'winner',                // 'winner' (기본) | 'merge' (옵트인, 가정 7)
}
```

### 필드 계약

| 필드 | 타입 | 기본값 | 제약 |
|---|---|---|---|
| `task.gates[]` | array | — | **비어 있으면 토너먼트 거부.** 채점 근거가 없으면 모델 판정만 남아 재현성이 사라진다 (01_PRD §7) |
| `contenders[]` | array | codex + grok | 2명. 3명 이상은 설정으로만 |
| `contenders[].provider` | enum | — | `run-cli-job.js`의 `PROVIDER_BINARIES` 키와 **반드시 일치** |
| `contenders[].worktree` | path | 자동 생성 | 참가자별로 달라야 함. 중복 시 거부 |
| `judge` | enum | `'gates'` | `'model'`은 게이트 동점일 때만 타이브레이커로 |
| `adopt` | enum | `'winner'` | `'merge'`는 명시적 옵트인 |

---

## 5. Scorecard — 채점 결과

```json
{
  "task": "auth-token",
  "contenders": [
    {
      "provider": "codex",
      "worktree": ".kkirikkiri/arena/auth-token/codex",
      "exitCode": 0,
      "gatesPassed": 3,
      "gatesTotal": 3,
      "diffSize": 142,
      "rank": 1
    },
    {
      "provider": "grok",
      "worktree": ".kkirikkiri/arena/auth-token/grok",
      "exitCode": 0,
      "gatesPassed": 2,
      "gatesTotal": 3,
      "diffSize": 98,
      "rank": 2
    }
  ],
  "winner": "codex",
  "tieBreaker": null
}
```

### 순위 규칙 (결정론 — 모델 판단 없음)

1. `gatesPassed` 내림차순
2. 동점이면 `diffSize` 오름차순 (작은 변경이 이김)
3. 그래도 동점이면 `judge: 'model'`로 타이브레이커 1회
4. **`gatesPassed === 0`인 참가자는 탈락** — 승자 후보에서도, 병합 후보에서도 제외

`diffSize`를 2순위로 둔 이유: 게이트를 똑같이 통과했다면 더 적게 건드린 쪽이 부작용이 적다. 모델 판정보다 재현성이 높다.

---

## 6. Adoption — 채택 결과

```json
{
  "mode": "winner",
  "winner": "codex",
  "transplants": []
}
```

`mode: "merge"`일 때만 `transplants[]`가 채워진다:

```json
{
  "mode": "merge",
  "winner": "codex",
  "transplants": [
    {
      "from": "grok",
      "description": "만료 토큰 처리에서 throw 대신 null 반환하는 방어 코드",
      "files": ["src/auth/token.ts"],
      "gatesAfter": { "passed": 3, "total": 3 },
      "kept": true
    }
  ]
}
```

### 병합 규칙 (가정 7 — 옵트인)

- **승자 코드가 베이스로 확정된다.** 패자 워크트리를 통째로 덮는 것은 금지.
- 이식 단위는 "이식 가능한 델타" — 파일 통째 교체 금지.
- **이식 1건마다 게이트 재실행.** `gatesAfter`가 이식 전보다 나빠지면 `kept: false`로 되돌린다.
- 참가자 간 diff를 입력으로 준다. 전체 파일 두 벌을 모델에게 읽히지 않는다.

---

## 7. 잡 디렉토리 구조

기존 구조를 확장한다.

```
.kkirikkiri/
  arena/
    auth-token/                    # 태스크명
      codex/                       # 참가자 워크트리 (git worktree)
      grok/
      scorecard.json               # §5
      adoption.json                # §6
      contenders/
        codex/
          job/                     # run-cli.sh JOB_DIR
            status.json
            output.txt
            error.txt
          gates.json
        grok/
          job/
          gates.json
```

품앗이 쪽은 기존 구조를 그대로 쓴다 (토너먼트 없음):

```
.pumasi/.jobs/pumasi-<날짜>-<해시>/
  job.json
  members/<task-name>/
    status.json
    output.txt
    report.json                    # codex는 --output-schema, grok은 --json-schema 언랩 (선택)
```

---

## 8. Grok 출력 언랩 계약

grok의 `--json-schema`는 스키마 준수 JSON을 **문자열로 중첩**해서 반환한다 (실측).

```
grok --json-schema '{"type":"object",...}' -p "..."
→ {"text": "{\"summary\":\"...\"}", "stopReason": "end_turn", "usage": {...}}
```

codex는 `-o <path>`로 파일에 직접 쓰므로 언랩이 없다. 따라서 `report.json` 생성 경로가 프로바이더별로 갈린다:

| 프로바이더 | 플래그 | report.json 생성 |
|---|---|---|
| codex | `--output-schema <schema> -o report.json` | CLI가 직접 씀 |
| grok | `--json-schema '<schema>' --output-format json` | 워커가 stdout의 `.text`를 파싱해서 씀 |
| agy / gjc | 없음 | 생성 안 함 (output.txt 기반 graceful) |

이 언랩은 **선택 사항**이다. 구현하지 않아도 grok 워커는 output.txt 경로로 정상 동작한다.
