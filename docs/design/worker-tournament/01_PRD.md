# Worker Tournament — PRD

> Show Me The PRD로 생성됨 (2026-08-23)
> 대상: `plugins/pumasi`, `plugins/kkirikkiri`

## 한 줄 요약

외부 코드 에이전트 워커에 **Grok CLI**를 추가하고, 끼리끼리 Workflow 경로에 **같은 과제를 여러 워커에게 시켜 채점·채택하는 토너먼트**를 포함한 5종 실행형태를 도입한다.

---

## 1. 문제

### 1-1. 현재 상태 (실측)

외부 코드 에이전트를 CLI로 호출하는 플러그인은 **2개뿐**이다.

| 플러그인 | 호출 방식 | 지원 프로바이더 | 근거 |
|---|---|---|---|
| **pumasi** | config의 command 문자열을 파싱해 spawn | `codex exec` / `gjc --print` / `agy -p` | `skills/pumasi/scripts/pumasi-job-worker.js:225,262` |
| **kkirikkiri** | 프로바이더별 if 분기 하드코딩 | `codex` / `antigravity(agy)` / `gjc` | `scripts/run-cli-worker.js:77-105`, `run-cli-job.js:25` |
| insane-review | CDP로 ChatGPT 웹 세션 구동 (CLI 아님) | GPT Pro 웹 전용 | `README.md:11` — 해당 없음 |

두 플러그인의 확장성이 구조적으로 다르다:

- **pumasi**는 프로바이더 개념 자체가 없다. `command` 문자열을 그대로 실행하고, codex일 때만 `--output-schema`를 주입한다 (`pumasi-job-worker.js:243` — `const isCodex = /(^|\/)codex$/.test(program)`). 따라서 **새 CLI 추가 = 설정 한 줄**.
- **kkirikkiri**는 `PROVIDER_BINARIES` 맵과 if 분기가 하드코딩돼 있어 **새 CLI 추가 = 코드 3곳 수정**.

### 1-2. 진짜 문제 두 가지

**(A) 워커 다양성이 없다.** 실질적으로 codex 단독이다. gjc·agy는 등록돼 있으나 agy는 비-TTY에서 stdout 누락 버그가 문서화돼 있고(`run-cli-worker.js:93`), 코딩 주력으로 쓰이지 않는다. 단일 모델에 의존하면 그 모델의 실패 모드가 그대로 산출물의 실패 모드가 된다.

**(B) 실행형태가 "병렬" 하나뿐이다.** 오너가 제시한 5종 실행형태 그림(직렬 / 병렬 / 플랜 뒤에 플랜 / 부모와 자식 / 토너먼트) 중 현재 구현된 것은 병렬 하나다.

| 실행형태 | 현재 상태 | 근거 |
|---|---|---|
| 직렬 | ❌ 없음 (태스크는 전부 동시 발사) | pumasi tasks 배열에 순서 의존 개념 없음 |
| **병렬** | ✅ 유일하게 구현됨 | pumasi tasks / 끼리끼리 `parallel()` |
| 플랜 뒤에 플랜 | ⚠️ 부분 (round/`maxRound` 배관만) | `pumasi-job.js:111-115` |
| 부모와 자식 | ❌ 없음 | — |
| **토너먼트** | ❌ 없음 | 이번 도입 대상 |

토너먼트가 가치 있다는 전제 — "같은 목표를 경쟁시키고 결과를 취합하면 더 나은 결과가 나온다" — 는 오너가 외부 벤치마크에서 관찰한 것으로, **본 저장소에서는 아직 실측되지 않았다.** 그래서 Phase 3의 A/B 벤치가 이 PRD의 핵심 산출물이다.

> ⚠️ 가정 1: 토너먼트가 단일 워커보다 나은 결과를 낸다 — 미검증. Phase 3에서 반증 가능하며, 값을 못 하면 기능을 접는다.

---

## 2. 왜 토너먼트는 품앗이가 아니라 끼리끼리인가

품앗이 SKILL.md가 스스로 토너먼트를 배제하고 있다. 문서에 명시된 전제 4개와 정면 충돌한다.

| 품앗이 문서의 전제 | 출처 | 토너먼트와의 충돌 |
|---|---|---|
| "품앗이의 존재 이유는 **Claude가 코드를 짜지 않는 것**" | SKILL.md 핵심 가치 | 토너먼트의 목적은 품질 향상 — 목적이 다름 |
| "독립 모듈 N개 동시 구현" — **분할**이 본질 | SKILL.md 개념 | 토너먼트는 **중복**. 정반대 |
| "**단일 파일 작업** — 병렬 이점 없음 → 사용 안 함" | SKILL.md 작업 규모별 분기 | 토너먼트는 정확히 단일 태스크를 N번 하는 것 |
| "격리: **동일 워킹 디렉토리**" | SKILL.md /batch 비교표 | 토너먼트는 워크트리 격리 필수 |

반면 끼리끼리에는 개념적 조상이 이미 있다:

- **핵심 운영 원칙 4번**: "**build ≠ review family** — 만든 모델과 검토하는 모델은 다른 family가 기본 (Codex → agy → Opus 적대 인스턴스 폴백)" (SKILL.md:83). 크로스모델 심사가 이미 원칙이다.
- **Workflow 경로**에 `adversarial-verify` 스테이지가 필수로 박혀 있다 (SKILL.md Step 4-W 규칙 4).
- Step 6-W가 **네이티브 Workflow 도구**를 호출하고, 그 도구는 `isolation: 'worktree'`와 judge panel 패턴을 지원한다.

**결론**: 품앗이는 grok 워커만 추가하고 토너먼트는 넣지 않는다. 토너먼트는 끼리끼리 **Workflow 경로 전용**으로 간다.

> ⚠️ 가정 2: Agent Teams 경로에는 토너먼트를 넣지 않는다 — 영속 팀·공유메모리 구조라 워크트리 격리가 불가능하고 Ralph 루프와 채점 노드가 기능적으로 겹친다. (오너 확인됨)

---

## 3. 설계상 가장 중요한 제약 — 발견 사항

끼리끼리의 **외부 CLI 러너와 Workflow 경로가 지금은 만나지 않는다.**

| 위치 | 경로 | 용도 |
|---|---|---|
| SKILL.md:1059 | **Agent Teams** (Step 6) | `run-cli.sh start --provider codex` — 본 작업 위임 |
| SKILL.md:1228 | **Workflow** (Step 7-W) | 워크플로우 *끝난 뒤* 선택적 사후 적대 검토 1회뿐 |

즉 Workflow 경로의 `agent()`는 **Claude 서브에이전트**(model: sonnet/opus)지 외부 CLI가 아니다. 그런데 토너먼트의 대진표는 codex vs grok이다.

**해결**: 토너먼트 참가자를 `agent()`로 감싸고, 그 서브에이전트가 Bash로 `run-cli.sh`를 호출하게 한다. 워크플로우 스크립트 자체에는 파일시스템·셸 접근이 없지만 `agent()`가 스폰하는 서브에이전트에는 있다.

```
Workflow 스크립트
  └─ agent("run-cli.sh로 codex 돌리고 결과 경로 반환", {schema})   ← 얇은 shim
       └─ Bash: run-cli.sh start --provider codex --prompt-file ...
```

비용: 참가자당 Claude 서브에이전트 1개가 shim으로 추가된다. 대안(스크립트에서 직접 셸 호출)은 Workflow 도구가 지원하지 않으므로 이 경로가 유일하다.

> ⚠️ 가정 3: shim 에이전트는 `model: "haiku"`로 충분하다 — 판단 없이 명령 실행·경로 반환만 하는 기계적 처리이므로 Step 4-W 모델 선택 기준표의 haiku 항목에 해당한다.

---

## 4. Grok CLI — 실측 결과

로컬에 이미 설치·로그인돼 있어 직접 실행해 확인했다.

```
grok --version   → grok 1.0.4 (d846eb93d94d) [stable]
grok models      → "You are logged in with grok.com."
                   default: grok-4.6 / available: grok-4.6, grok-4.5
grok -p "Reply with exactly: PONG"  → PONG  (exit 0, 비-TTY 파이프 정상)
```

헤드리스 인터페이스가 codex·agy보다 오히려 넓다.

| 기능 | 플래그 | 상태 |
|---|---|---|
| 원샷 프롬프트 | `-p, --single "<PROMPT>"` | 실측 확인 |
| 프롬프트 파일 | `--prompt-file <PATH>` | **codex·agy에 없는 기능** |
| 구조화 출력 | `--json-schema '<schema>'` | 실측 확인 (공식 문서에는 미기재) |
| 출력 포맷 | `--output-format plain\|json\|streaming-json\|streaming-messages-json` | 실측 확인 |
| 승인 우회 | `--always-approve` / `--permission-mode bypassPermissions` | help 확인 |
| 작업 디렉토리 | `--cwd <CWD>` | help 확인 |
| 세션 재개 | `-r/--resume`, `-c/--continue`, `--fork-session` | help 확인 — codex 수준 |
| 워크트리 | `-w/--worktree` | help 확인. **단 `-p` 헤드리스에서는 워크트리를 만들지 않음** |
| 샌드박스 | `--sandbox <PROFILE>` | **기본 off** — codex와 반대 |

### 주의점 5가지

1. **`--json-schema` 결과는 `.text`에 문자열로 중첩된다.** 실측 출력: `{"text":"{\"summary\":\"...\"}", "usage":{...}}`. codex의 `-o report.json`처럼 파일로 떨어지지 않으므로 언랩이 필요하다.
2. **샌드박스 기본 off.** codex는 기본 샌드박스인데 grok은 제약 없이 파일·네트워크에 접근한다. 프로바이더 기본값에 `--sandbox workspace`를 넣어야 한다.
3. **자동 업데이터가 백그라운드로 돈다** → 항상 `--no-auto-update --no-alt-screen`.
4. **PATH 함정**: `~/.grok/bin/grok`에 설치된다. 비대화형 셸에서 `command -v grok`이 실패할 수 있으므로 check-env에 경로 폴백이 필요하다.
5. **`grok-code-fast-1`은 2026-08-15 폐기됨.** 모델은 미지정(기본 grok-4.6)으로 둔다.

인증은 현재 **구독 세션**(grok.com 로그인)이라 `XAI_API_KEY` 없이 동작한다. API 키 경로도 있으나 종량 과금이므로 기본은 구독 세션을 유지한다.

> ⚠️ 가정 4: grok 구독 세션이 동시 병렬 호출에서 레이트 리밋에 걸리지 않는다 — 미검증. Phase 1의 첫 실측 대상.

---

## 5. 범위

### 포함

| 항목 | 대상 플러그인 |
|---|---|
| grok 워커 프로바이더 추가 | pumasi, kkirikkiri |
| 실행형태 5종 (직렬·병렬·플랜뒤플랜·부모자식·토너먼트) | kkirikkiri Workflow 경로 |
| 토너먼트 채점(게이트 기반) + 승자 채택 | kkirikkiri |
| 병합 채택 (옵트인) | kkirikkiri |
| 실측 스모크 + A/B 벤치 | 양쪽 |

### 제외

- 품앗이의 토너먼트 — §2 근거로 명시적 배제
- Agent Teams 경로의 토너먼트 — 가정 2
- CI 자동 게이트 — grok 구독 세션이 CI에서 동작하지 않아 mock 설계가 별도로 필요. 별건으로 분리
- 새 CLI(cursor-agent 등) 추가 — 이번 범위 밖

---

## 6. 성공 기준

| # | 기준 | 측정 방법 |
|---|---|---|
| S1 | grok이 품앗이 워커로 병렬 3개 이상 동시 실행되고 전부 게이트 통과 | `pumasi-job.sh gates --json` |
| S2 | grok이 끼리끼리 프로바이더로 등록되고 `check-env`가 감지 | `run-cli.sh check grok` |
| S3 | 5종 실행형태가 Step 4-W에서 선택 가능하고 각각 스크립트가 생성됨 | 형태별 1회 실행 |
| S4 | 토너먼트가 참가자를 격리 실행하고 게이트 기반으로 승자를 뽑음 | job 디렉토리 + 채점 로그 |
| S5 | **codex 단독 vs 토너먼트의 게이트 통과율 차이가 숫자로 남음** | Phase 3 A/B 벤치 리포트 |

S5가 미달(토너먼트가 단독보다 낫지 않음)이면 **토너먼트를 기본값으로 승격하지 않고 실험 기능으로 유지한다.** 기능을 넣는 것이 목표가 아니라 값을 하는지 확인하는 것이 목표다.

---

## 7. 비용 경고

토너먼트는 정의상 **토큰·시간이 N배**다. grok 구독 세션은 정액이라 부담이 적지만 codex는 아니다.

- 전체 태스크에 기본 적용 금지. **까다로운 단일 태스크에만 옵트인.**
- 게이트·테스트 같은 객관 지표가 없는 태스크(리서치·기획)에서는 채점도 모델 판정이라 신뢰도가 떨어진다 → **게이트가 있는 코딩 태스크에만 토너먼트를 허용하는 가드**를 건다.

> ⚠️ 가정 5: 토너먼트 참가자 수 기본값은 2명(codex, grok)이다 — 3명 이상은 비용 대비 이득이 불확실하므로 설정으로만 연다.

---

## 8. 가정 원장

| # | 가정 | 영향 문서 | 확인 |
|---|---|---|---|
| 1 | 토너먼트가 단일 워커보다 나은 결과를 낸다 | 01, 03, 05 | ⚠️ **반증됨(조건부)** — 2026-08-23 A/B 2라운드에서 게이트 통과율 차이 0. 잘 명세된 태스크 한정 판정. [리포트](../../reports/tournament-ab-2026-08-23.md) |
| 2 | Agent Teams 경로에는 토너먼트를 넣지 않는다 | 01, 04 | ✅ 오너 확인 |
| 3 | shim 에이전트는 `model: "haiku"`로 충분 | 01, 02 | ❌ 미확인 |
| 4 | grok 구독 세션이 병렬 호출에서 레이트 리밋에 안 걸린다 | 01, 03 | ✅ **해소** — 3개 동시 실행 전부 exit 0, 레이트리밋 에러 0건 (2026-08-23) |
| 5 | 토너먼트 기본 참가자는 2명 | 01, 02 | ❌ 미확인 |
| 6 | 5종 실행형태의 이름·선언 형식은 **본 저장소 자체 정의**를 쓴다 | 02, 04 | ❌ 원본 그림의 스펙 문서를 저장소에서 못 찾음 (`grep -rln "토너먼트\|tournament" plugins/ docs/` → 0건). 외부 스펙이 있으면 키 이름을 맞춰야 함 |
| 7 | 병합(merge) 채택은 옵트인, 기본은 승자 채택 | 01, 03 | ✅ 오너 확인. 단 A/B 동등 판정으로 **Phase 4 미착수** |
| 8 | CI 게이트는 이번 범위 밖 | 01, 05 | ❌ 미확인 — grok 로그인 세션이 CI에서 불가한 것이 이유 |

---

## FACT_GATE doc=6 run=14 unverifiable=8
