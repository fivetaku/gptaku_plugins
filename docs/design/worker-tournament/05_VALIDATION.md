# 검증 계획

> 선택된 검증 수준: **실측 스모크 + A/B 벤치** (CI 자동 게이트는 범위 밖 — 가정 8)

원칙: **기억으로 상태를 보고하지 않는다.** 모든 완료 판정은 실제 명령 실행 결과로만 내린다. 아래 각 항목은 "돌려서 이 출력이 나와야 통과"로 적혀 있다.

---

## V1 — 품앗이 grok 워커 스모크 (Phase 1)

### V1-1. 단독 실행

```bash
export PATH="$HOME/.grok/bin:$PATH"
grok --version                      # → grok 1.0.x
grok models                         # → "You are logged in with grok.com."
```

**통과**: 버전 출력 + 로그인 상태 확인.
**실패 시**: `grok login`. 인증이 안 되면 이후 전부 무의미하므로 여기서 멈춘다.

### V1-2. 품앗이 워커로 1개 실행

`.pumasi/pumasi.config.yaml`에 grok command로 태스크 1개를 두고:

```bash
bash plugins/pumasi/skills/pumasi/scripts/pumasi-job.sh start "스모크"
bash plugins/pumasi/skills/pumasi/scripts/pumasi-job.sh wait <JOB_DIR>
bash plugins/pumasi/skills/pumasi/scripts/pumasi-job.sh gates --json <JOB_DIR>
```

**통과**: `state: "done"`, `exitCode: 0`, 게이트 전부 pass.
**확인할 것**: `output.txt`가 **비어 있지 않은지**. agy는 비-TTY에서 stdout이 누락되는 버그가 문서화돼 있다(`run-cli-worker.js:93`). grok은 단독 실행에서 정상이었지만, 품앗이 워커로 스폰됐을 때도 그런지는 여기서 처음 확인한다.

### V1-3. 병렬 3개 — 가정 4 해소

같은 instruction을 가진 grok 태스크 3개를 동시에 발사한다.

| 측정 항목 | 기록 위치 |
|---|---|
| 3개 전부 `exitCode: 0`인가 | `gates --json` |
| 레이트 리밋 에러가 `error.txt`에 있는가 | `members/*/error.txt` |
| 순차 실행 대비 총 소요 시간 | `startedAt`/`finishedAt` 차 |

**통과 기준**: 3개 전부 완료 + 레이트 리밋 에러 0건.
**부분 통과 시**: 동시 실행 상한을 찾아 문서에 기록하고, 그 값을 품앗이 설정 권장값으로 적는다. **가정 4를 "N개까지 안전"으로 갱신한다.**

---

## V2 — 끼리끼리 grok 프로바이더 (Phase 2)

### V2-1. 프로바이더 등록

```bash
bash plugins/kkirikkiri/scripts/run-cli.sh check grok
```

**통과**: `grok: found at ...`

### V2-2. PATH 폴백 — 비대화형 셸

check-env가 오판하지 않는지가 이 Phase의 핵심 리스크다.

```bash
env -i HOME="$HOME" /bin/sh -c 'node plugins/kkirikkiri/scripts/check-env.js' | grep -i grok
```

**통과**: PATH가 비어 있는 환경에서도 grok을 "설치됨"으로 감지.
**실패 시**: `~/.grok/bin/grok` 존재 확인 폴백을 `check-env.js`에 추가한다. 이 케이스를 안 잡으면 사용자에게 "grok 미설치"라고 잘못 안내하게 된다.

### V2-3. 실제 위임 1건

```bash
bash plugins/kkirikkiri/scripts/run-cli.sh start --provider grok --prompt-file /tmp/smoke.md
bash plugins/kkirikkiri/scripts/run-cli.sh wait <JOB_DIR>
bash plugins/kkirikkiri/scripts/run-cli.sh results <JOB_DIR>
```

**통과**: 결과 텍스트가 비어 있지 않고 프롬프트에 실제로 응답.

### V2-4. 회귀 — 기존 프로바이더

```bash
for p in codex antigravity gjc; do
  bash plugins/kkirikkiri/scripts/run-cli.sh check $p
done
```

**통과**: 3개 전부 이전과 동일한 결과. `PROVIDER_BINARIES`와 usage 문자열을 건드렸으므로 회귀 확인이 필요하다.

---

## V3 — 실행형태 5종 (Phase 3)

각 형태를 최소 예제로 1회씩 돌린다. **형태별로 "무엇이 증명돼야 하는가"가 다르다.**

| 형태 | 최소 예제 | 통과 기준 |
|---|---|---|
| `parallel` | 독립 태스크 3개 | 3개가 실제로 동시 실행 (타임스탬프 겹침) |
| `serial` | A→B→C | B의 `startedAt` > A의 `finishedAt` |
| `chain` | 플랜 A→B | A 스테이지 전원 종료 후 B 시작 |
| `fanout` | 부모 1 + 자식 3 | 자식 3개 완료 후에만 부모 완료 |
| `tournament` | 참가자 2 | V4로 |

**타임스탬프 대조가 유일한 증거다.** "직렬로 설정했으니 직렬로 돌았을 것"은 검증이 아니다 — 설정이 실제로 실행 순서를 바꿨는지 시각으로 확인한다.

---

## V4 — 토너먼트 (Phase 3, 핵심)

### V4-1. 격리 확인

```bash
ls .kkirikkiri/arena/<task>/
git -C .kkirikkiri/arena/<task>/codex rev-parse --show-toplevel
git -C .kkirikkiri/arena/<task>/grok  rev-parse --show-toplevel
```

**통과**: 참가자별로 **다른** 워크트리 경로. 같으면 서로 덮어쓰므로 즉시 중단.

### V4-2. 채점 결정론

같은 참가자 산출물로 채점을 **2회** 돌린다.

**통과**: `scorecard.json`의 `rank`가 두 번 동일. 다르면 채점에 모델 판단이 새어 들어간 것이므로 순위 규칙을 다시 본다 (게이트 수 → diff 크기 → 그다음에야 모델).

### V4-3. 가드 동작

`gates`가 빈 태스크로 토너먼트를 시도한다.

**통과**: 실행되지 않고 거부 메시지. 이게 통과 못 하면 채점 근거 없는 토너먼트가 돌아 재현성이 사라진다.

### V4-4. 탈락 규칙

한 참가자가 게이트 전패하도록 유도(예: 일부러 불가능한 게이트 하나 추가는 X — 전패 참가자가 나오는 실제 케이스를 기다리거나, 참가자 하나에 고의로 잘못된 instruction 주입).

**통과**: `gatesPassed === 0` 참가자가 `winner` 후보에서 제외되고 `adoption`에도 안 들어감.

---

## V5 — A/B 벤치 (Phase 3, 판정)

**이 항목이 토너먼트 기능의 존폐를 결정한다.** 다른 검증은 "동작하는가"를 보지만 이건 "값을 하는가"를 본다.

### 설계

| 조건 | 내용 |
|---|---|
| 대상 태스크 | 게이트가 명확한 코딩 태스크 **5개 이상** |
| A 조건 | codex 단독 |
| B 조건 | 토너먼트 (codex + grok, 승자 채택) |
| 측정 | 게이트 통과율, 소요 시간, 토큰/비용 |
| 반복 | 태스크당 최소 2회 (모델 출력 분산 때문) |

### 사전 등록 기준 — 실행 전에 확정한다

> 결과를 본 뒤에 기준을 정하면 검증이 아니라 사후 합리화가 된다. 아래를 **벤치 실행 전에** 고정한다.

| 판정 | 조건 | 조치 |
|---|---|---|
| **우위** | B의 게이트 통과율이 A보다 유의미하게 높음 | Phase 4(병합) 착수. 토너먼트를 어려운 태스크의 권장 기본값으로 |
| **동등** | 통과율 차이가 미미 | 기능 유지하되 **기본값 승격 안 함**. 옵트인 실험 기능 |
| **열위** | B가 A보다 낮음 | 토너먼트 동결. 원인 분석(채점 규칙? 프롬프트 분산?) 후 재설계 |

**비용 축을 반드시 같이 기록한다.** 토너먼트는 정의상 N배 비용이므로, 통과율이 소폭 올랐어도 비용이 2배면 "우위"가 아니다. 리포트에 통과율만 적고 비용을 빼면 안 된다.

### 산출물

`docs/reports/tournament-ab-2026-XX-XX.md` — 조건별 원시 수치, 사전 등록 기준, 판정, 그리고 **판정에 반하는 관찰도 함께** 기록한다.

---

## V6 — 배포 검증 (Phase 5)

```bash
# 캐시에 새 버전만 존재
ls ~/.claude/plugins/cache/gptaku-plugins/pumasi/
ls ~/.claude/plugins/cache/gptaku-plugins/kkirikkiri/

# 소스 대조 — 닷파일 누락 확인
diff -rq ~/.claude/plugins/marketplaces/gptaku-plugins/plugins/pumasi \
         ~/.claude/plugins/cache/gptaku-plugins/pumasi/<ver> --exclude=.git

# installed_plugins.json 3항목 일치
cat ~/.claude/plugins/installed_plugins.json | python3 -c "
import json,sys; d=json.load(sys.stdin)
for k in ['pumasi@gptaku-plugins','kkirikkiri@gptaku-plugins']:
    print(k, json.dumps(d['plugins'][k], indent=2))"
```

**통과**: 구버전 디렉토리 없음 + `diff` 차이 없음 + installPath/version/gitCommitSha 일치.
**특히 확인**: 캐시에 `.claude-plugin/` 디렉토리가 존재하는지. `cp -R staging/*` 글롭으로 복사하면 누락되는 실제 사고 이력이 있다.

---

## 검증 요약표

| ID | 대상 | Phase | 성공기준 매핑 |
|---|---|---|---|
| V1 | 품앗이 grok 워커 + 병렬 실측 | 1 | S1, 가정 4 |
| V2 | 끼리끼리 grok 프로바이더 + PATH 폴백 + 회귀 | 2 | S2 |
| V3 | 실행형태 5종 타임스탬프 대조 | 3 | S3 |
| V4 | 토너먼트 격리·채점 결정론·가드·탈락 | 3 | S4 |
| V5 | **A/B 벤치 (사전 등록 기준)** | 3 | S5 |
| V6 | 배포 대조 | 5 | — |

---

## 검증하지 않는 것 (명시적 제외)

| 항목 | 이유 |
|---|---|
| CI 자동 게이트 | grok 구독 세션이 CI에서 동작하지 않음. mock 설계가 별건 (가정 8) |
| grok API 키 경로 | 구독 세션으로 충분. 종량 과금이라 기본 경로가 아님 |
| Agent Teams 경로의 토너먼트 | 범위 밖 (가정 2) |
| agy/gjc 프로바이더 개선 | 이번 범위 밖. V2-4의 회귀 확인만 |
