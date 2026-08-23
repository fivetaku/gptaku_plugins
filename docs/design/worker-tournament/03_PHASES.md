# Phase 분리 계획

각 Phase는 **다음 Phase의 설계 입력을 실측으로 만들어내는** 순서로 배열했다. Phase 1의 grok 병렬 실측이 없으면 Phase 2의 분기 주석을 쓸 수 없고, Phase 3의 A/B 결과가 없으면 Phase 4(병합)를 만들 근거가 없다.

---

## Phase 1 — 품앗이 grok 워커 (MVP)

**목표**: grok을 품앗이 워커로 쓸 수 있게 하고, **grok의 병렬 실행 특성을 실측한다.**

품앗이는 command 문자열 방식이라 코드 변경이 거의 없다. 이 Phase의 진짜 산출물은 코드가 아니라 **실측 데이터**다.

### 작업

| # | 대상 | 변경 |
|---|---|---|
| 1-1 | `.pumasi/pumasi.config.yaml`, `plugins/pumasi/pumasi.config.yaml` | 프로바이더 주석 블록에 grok 한 줄 추가 |
| 1-2 | `plugins/pumasi/README.md` ×5(ko/en/ja/zh/es) | 프로바이더 표에 grok 행 |
| 1-3 | `plugins/pumasi/CHANGELOG.md` | 항목 추가 |
| 1-4 | *(선택)* `pumasi-job-worker.js:243` | `isCodex` 옆에 `isGrok` — `--json-schema` + `.text` 언랩으로 report.json 생성 |

추가할 command 문자열:
```yaml
# grok : "grok --no-auto-update --no-alt-screen --sandbox workspace --always-approve -p"
```

1-4는 **하지 않아도 동작한다** (output.txt graceful 경로). Phase 1에서는 미루고, 게이트 품질이 실제로 아쉬울 때만 한다.

### 완료 조건

- S1: grok 워커 3개 이상 동시 실행 → 전부 게이트 통과
- 가정 4 해소: 병렬 호출에서 레이트 리밋 발생 여부가 기록됨

### 검증 → [05_VALIDATION.md](05_VALIDATION.md) V1

---

## Phase 2 — 끼리끼리 grok 프로바이더

**목표**: 끼리끼리에서도 grok을 워커로 쓸 수 있게 한다. 하드코딩 분기라 Phase 1과 달리 코드가 필수다.

### 작업

| # | 파일 | 변경 |
|---|---|---|
| 2-1 | `scripts/run-cli-job.js:25` | `PROVIDER_BINARIES`에 `grok: 'grok'` |
| 2-2 | `scripts/run-cli-job.js:6,104,110` | usage 문자열을 `codex\|antigravity\|gjc\|grok`로 갱신 |
| 2-3 | `scripts/run-cli-worker.js:105` 뒤 | `provider === 'grok'` 분기 추가 |
| 2-4 | `scripts/check-env.js:142` 근처 | grok 감지 + **`~/.grok/bin/grok` 경로 폴백** |
| 2-5 | `scripts/check-env.sh` | 동일 반영 |
| 2-6 | `skills/kkirikkiri/references/presets.md` | 역할 라우팅에 grok 슬롯 |
| 2-7 | README ×5, CHANGELOG | 문서 |

2-3 분기 초안 (Phase 1 실측을 주석에 반영해서 확정):
```js
} else if (provider === 'grok') {
  // xAI Grok Build CLI (바이너리: `grok`).
  // 원샷 헤드리스: `grok -p "<프롬프트>"`.
  // 실측(2026-08-23, grok 1.0.4): 비-TTY 파이프에서 stdout 정상 — agy의 누락 버그 없음.
  // 주의 1) 샌드박스가 기본 off라 workspace로 조인다 (codex와 반대).
  // 주의 2) 자동 업데이터가 백그라운드로 돌므로 --no-auto-update 필수.
  program = 'grok';
  args = ['--no-auto-update', '--no-alt-screen', '--sandbox', 'workspace', '--always-approve'];
  if (process.env.KKIRIKKIRI_GROK_MODEL) args.push('-m', process.env.KKIRIKKIRI_GROK_MODEL);
  args.push('-p', promptContent);
}
```

`KKIRIKKIRI_GROK_MODEL`은 기존 `KKIRIKKIRI_CODEX_MODEL` 패턴(`run-cli-worker.js:85`)을 그대로 따른다.

2-4의 PATH 폴백이 이 Phase에서 가장 놓치기 쉬운 지점이다. grok은 `~/.grok/bin`에 설치되고 셸 프로필을 통해서만 PATH에 들어가므로, 비대화형 셸에서 도는 check-env가 "미설치"로 오판한다.

### 완료 조건

- S2: `run-cli.sh check grok` → found
- Agent Teams 경로에서 grok에게 실제 작업 1건 위임 성공

### 검증 → [05_VALIDATION.md](05_VALIDATION.md) V2

---

## Phase 3 — 토너먼트 + A/B 벤치 (핵심)

**목표**: 끼리끼리 Workflow 경로에 토너먼트를 넣고, **토너먼트가 값을 하는지 숫자로 판정한다.**

이 Phase는 기능 구현과 가설 검증이 한 몸이다. 벤치 결과가 나쁘면 기능을 기본값으로 승격하지 않는다 (01_PRD §6).

### 작업

| # | 위치 | 변경 |
|---|---|---|
| 3-1 | `SKILL.md` Step 3.5 (:339) | Workflow 선택 후 **실행형태 재질문** 추가 |
| 3-2 | `SKILL.md` Step 4-W (:508) | 실행형태별 스크립트 템플릿 5종 |
| 3-3 | 신규 `references/execution-shapes.md` | 5종 형태 정의 + 스크립트 골격 (Step 4-W가 lazy-read) |
| 3-4 | Step 4-W | 토너먼트 참가자 shim (`agent` → Bash → `run-cli.sh`) |
| 3-5 | Step 4-W | 채점 스테이지 (게이트 기반, 결정론) |
| 3-6 | Step 4-W | 승자 채택 + `scorecard.json` / `adoption.json` 기록 |
| 3-7 | Step 4-W | **가드**: `gates`가 비면 토너먼트 거부 |

Step 4-W는 현재 **하나의 형태**(수집→검증→종합)만 하드코딩돼 있다. 5종은 이걸 템플릿 라이브러리로 승격하는 작업이다. Step 4-W의 기존 규칙(모델 핀 필수, adversarial-verify 필수, schema 강제)은 **모든 템플릿에 그대로 적용**한다.

토너먼트 참가자 shim이 이 Phase의 구조적 핵심이다 (01_PRD §3) — Workflow 스크립트에는 셸 접근이 없으므로 `agent()`가 스폰하는 서브에이전트를 통해서만 외부 CLI에 닿는다.

### 완료 조건

- S3: 5종 형태 각각 1회 실행 성공
- S4: 토너먼트가 참가자를 격리 실행하고 게이트 기반 승자 산출
- **S5: A/B 벤치 리포트 존재** — codex 단독 vs 토너먼트 게이트 통과율

### 검증 → [05_VALIDATION.md](05_VALIDATION.md) V3, V4

---

## Phase 4 — 병합 채택 (조건부)

**진입 조건**: Phase 3의 A/B 벤치에서 토너먼트가 단독보다 우위. 우위가 없으면 이 Phase는 **착수하지 않는다.**

> 🔴 **판정 결과 (2026-08-23): 동등 → 이 Phase는 착수하지 않는다.**
> A/B 2라운드에서 게이트 통과율 차이 0 (양쪽 6/6, 테스트 35/35). CLI 호출만 2배.
> 상세: [docs/reports/tournament-ab-2026-08-23.md](../../reports/tournament-ab-2026-08-23.md)
> 단, 판정은 **잘 명세된 태스크에 한정**된다 — 모호한 태스크에서의 재측정은 열려 있다.

### 작업

| # | 변경 |
|---|---|
| 4-1 | `adopt: 'merge'` 옵트인 경로 |
| 4-2 | 참가자 간 diff 생성 → 모델 입력 (전체 파일 금지) |
| 4-3 | 이식 1건마다 게이트 재실행 + 실패 시 롤백 |
| 4-4 | `adoption.transplants[]` 기록 |

병합은 잘못하면 양쪽 최악을 섞은 결과가 나온다. 그래서 §4-3의 이식별 게이트 재실행이 안전장치가 아니라 **기능의 본체**다.

### 검증 → [05_VALIDATION.md](05_VALIDATION.md) V5

---

## Phase 5 — 배포

두 플러그인 모두 CLAUDE.md의 8단계 배포 체크리스트를 따른다.

| # | 단계 |
|---|---|
| 5-1 | 서브모듈에서 `plugin.json` 버전 범프 + commit + push |
| 5-2 | 서브모듈에 `gh release create v<ver>` |
| 5-3 | 부모 저장소 서브모듈 포인터 업데이트 |
| 5-4 | 마켓플레이스 클론 `git pull` + `git submodule update` |
| 5-5 | 캐시 교체 — **`cp -R "$SRC/." "$DST/"`** (글롭 금지, 닷파일 누락 함정) |
| 5-6 | `installed_plugins.json` (installPath/version/gitCommitSha/lastUpdated) |
| 5-7 | `diff -rq "$SRC" "$DST" --exclude=.git` 대조 |
| 5-8 | Claude Code 재시작 |

5-5는 메모리에 기록된 실제 사고 이력이 있다 — `cp -R staging/*`는 `.claude-plugin/`을 누락시킨다.

### 검증 → [05_VALIDATION.md](05_VALIDATION.md) V6

---

## 의존 관계

```
Phase 1 ──(grok 병렬 실측)──▶ Phase 2 ──(프로바이더 등록)──▶ Phase 3
                                                                │
                                                    (A/B 우위?) │
                                                       ┌────────┴────────┐
                                                      YES               NO
                                                       │                 │
                                                       ▼                 ▼
                                                   Phase 4          기능 동결
                                                       │           (실험 유지)
                                                       └────────┬────────┘
                                                                ▼
                                                            Phase 5
```

Phase 1과 2는 서로 독립이라 병렬로 해도 되지만, **순서대로 하는 편이 낫다** — Phase 1에서 얻은 grok 실측(레이트 리밋·타임아웃·stdout 거동)을 Phase 2의 분기 주석에 그대로 적기 위해서다. 저장소의 기존 프로바이더 분기들도 전부 실측 날짜와 함께 주석이 달려 있다.
