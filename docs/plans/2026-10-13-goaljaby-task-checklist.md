# goaljaby 수정 계획: 세부 작업 체크리스트 기록 (v0.6.3에서 v0.7.0으로)

- 작성: 2026-10-13
- 근거: GPT Pro 리뷰 `.insane-review/response_goalboard-review_20261012_224606_31593_9bf1a0.md`(질문 2, 4), 실제 골 폴더 5곳 관찰
- 짝 작업: playmaker 플러그인(`docs/plans/2026-10-13-playmaker-plugin.md`). **playmaker가 새 형식을 읽을 수 있게 된 뒤에** 이 변경을 배포한다.

## 1. 왜 바꾸나

지금 goaljaby는 진행 상태를 **마일스톤 단위로만** 기록한다. 그래서 진행 중인 마일스톤 안에서 어느 작업이 끝났는지, 어느 작업이 사람을 기다리는지 알 수 없다. 실제로 tesladesk media-path-fix 골은 M4와 M5가 동시에 "사람 대기" 상태인데, 이 사실이 PROGRESS.md 산문 한 단락에만 적혀 있다.

playmaker 보드가 "지금 어떤 작업이 진행 중인가"를 보여 주려면 작업 단위 상태가 파일에 있어야 한다.

## 2. 결정 사항

| 항목 | 결정 | 이유 |
|---|---|---|
| 작업 상태의 정본 | PLAN.md 마일스톤별 체크리스트 | 사람도 읽을 수 있고, 줄 단위로 안정적으로 파싱되며, 산출물 5종 구조를 유지한다 |
| 상태 표시 | `[ ]` 대기 · `[>]` 진행 · `[x]` 완료 · `[!]` 사람 판단·외부 입력 대기 | 마커만 바꾸면 되므로 에이전트 부담이 가장 작다 |
| 작업 ID | `M{N}-T{K}` (예: `M2-T1`) | 문장이 비슷해도 작업을 구분할 수 있다 |
| progress.json | 만들지 않음 | 파일 세 개를 동시에 갱신하면 어긋난다. 필요하면 playmaker가 읽어서 만든다 |
| PROGRESS.md | 실행 로그로 역할을 바꿈 | 현재 작업·검증 결과·리스크·인수인계를 남긴다. 작업 상태를 재정의하지 않는다 |
| 기존 골 폴더 | 자동 마이그레이션 금지 | 이미 만든 PLAN과 사람이 손으로 쓴 PLAN은 그대로 둔다 |
| 보호 문구 P1~P5 | 그대로 유지 | 새 규칙은 `TASK_STATUS_RULE` 검사로 따로 추가한다 |

## 3. 변경 파일과 내용

### 3.1 `skills/goaljaby/references/templates.md`

**PLAN 마일스톤 형식** (현재 205줄 부근)

```diff
 ## 마일스톤 {N}: {MILESTONE_NAME}
 - 범위(Scope): {MILESTONE_SCOPE}
 - 완료 조건: {MILESTONE_COMPLETION}
 - 검증: {MILESTONE_VALIDATION}
+
+작업 (상태: `[ ]` 대기 · `[>]` 진행 · `[x]` 완료 · `[!]` 사람 대기)
+{MILESTONE_TASK_ROWS}
```

`{MILESTONE_TASK_ROWS}` 생성 규칙을 새로 추가한다.

- 범위·완료 조건·검증을 실행 가능한 작업 단위로 나눈다. 마일스톤마다 2~6개를 만든다.
- 각 행의 형식은 `- [ ] M{N}-T{K}: <동사로 끝나는 작업 한 문장>`이다.
- 마지막 작업은 그 마일스톤의 검증 실행으로 둔다(예: `M2-T4: 마일스톤 검증을 실행하고 결과를 기록한다`).
- 실행 중에는 마커만 바꾼다. 작업 문장, 범위, 완료 조건, 검증 문장은 수정하지 않는다.
- 작업을 새로 추가해야 하면 해당 마일스톤 맨 끝에 다음 번호로 덧붙인다. 기존 번호는 재사용하지 않는다.

영어 헤딩 맵(§헤딩 맵)에도 `작업` / `Tasks` 한 줄을 추가한다.

**PROGRESS 템플릿 머리말** (현재 213~255줄)

```diff
- 이 PROGRESS.md는 골잡이가 생성했다. 골 실행 중 매 체크포인트마다 갱신된다.
+ 이 PROGRESS.md는 골잡이가 생성한 실행 로그다.
+ 세부 작업 상태의 정본은 PLAN.md의 체크리스트다(`[ ]`/`[>]`/`[x]`/`[!]`).
+ 이 파일에는 현재 작업, 검증 결과, 리스크, 인수인계를 체크포인트마다 남긴다.
```

**`/goal` 본문 F-1~F-6 공통 한 줄** (현재 280, 294, 308, 322, 337, 351줄의 "PROGRESS.md를 업데이트한다" 바로 앞)

```diff
+작업을 시작하면 PLAN.md의 해당 줄을 `[>]`, 끝나면 `[x]`, 사람 판단이 필요하면 `[!]`로 바꾸고(마커만), 
 각 마일스톤이 끝나면 PROGRESS.md를 업데이트한다.
```

이 줄은 공백을 포함해 약 90자다. `output_lang`으로 번역하되 마커와 파일명은 그대로 둔다.

### 3.2 `skills/goaljaby/references/compact-strategy.md`

- **기존 버그 수정:** 단계 3의 약어 치환이 `PROGRESS.md`를 `PR.md`로 바꾸면 P5 정규식(`PROGRESS\.md[를을]?\s*업데이트`)이 매칭되지 않는다. P5 문장 안에서는 `PROGRESS.md`를 약어로 바꾸지 않는다는 예외를 명시한다. 같은 이유로 새 상태 규칙 문장의 `PLAN.md`도 약어 치환에서 제외한다.
- **새 검사:** 압축 후 자체 검증에 아래 검사를 추가한다. 생성된 PLAN에 체크리스트가 있을 때만 적용한다.

```python
def verify_task_rule(text: str, plan_has_tasks: bool) -> list[str]:
    if not plan_has_tasks:
        return []
    errs = []
    if not re.search(r"PLAN\.md", text):
        errs.append("TASK_STATUS_RULE: PLAN.md 언급 없음")
    for marker in ("[>]", "[x]", "[!]"):
        if marker not in text:
            errs.append(f"TASK_STATUS_RULE: 마커 {marker} 없음")
    return errs
```

- 압축 단계에서 이 문장이 빠졌으면 다시 넣는다. 그래도 4,000자를 넘으면 기존 오버플로 처리 규칙을 따른다.

### 3.3 `skills/goaljaby/SKILL.md`

| 위치 | 변경 |
|---|---|
| 출력 목록(43~47줄) | PLAN.md 설명에 "마일스톤별 세부 작업 체크리스트" 추가 |
| Step 5 슬롯 채움 | 새 PLAN의 각 마일스톤에 `M{N}-T{K}` 작업 행을 만든다. 기존 PLAN(이어가기 분기)에는 소급 삽입하지 않는다 |
| Step 7 자체 검증 | 새 PLAN은 마일스톤마다 작업 행 1개 이상, ID 중복 없음. `TASK_STATUS_RULE` 통과. 체크리스트가 없는 기존 PLAN은 검사를 생략한다 |
| Step 8 검토 요약 | 마일스톤 줄에 작업 수 표시 (예: `M2 인증 (작업 4)`) |
| 핵심 원칙 | "세부 작업의 정본은 PLAN.md다. PROGRESS.md는 작업 상태를 재정의하지 않는다." 추가 |

### 3.4 `.claude-plugin/plugin.json`, `CHANGELOG.md`, README

- 버전을 0.7.0으로 올린다(산출물 형식이 바뀌므로 마이너 버전).
- CHANGELOG에 "PLAN.md 작업 체크리스트 + 상태 마커, P5 약어 충돌 수정"을 적는다.
- README 5개 언어에 "playmaker를 함께 쓰면 진행 보드를 볼 수 있다"는 한 줄을 넣는다. playmaker 배포 뒤에 한다.

## 4. 하위호환

- 기존 골 폴더의 PLAN, PROGRESS, goal-command는 바꾸지 않는다. 체크리스트가 없어도 기존처럼 실행된다.
- "이어가기" 분기(기존 산출물이 있을 때)는 PLAN을 다시 쓰지 않는다.
- playmaker는 체크리스트가 없는 PLAN을 기존 방식(마일스톤 단위 + 범위 분해)으로 읽는다. 따라서 goaljaby 0.6.x로 만든 골도 계속 보드에 나온다.

## 5. 검증 계획

1. **템플릿 단위:** 새 PLAN 예시 1개를 손으로 채워 playmaker 파서에 넣고, 마커 4종이 상태 4종으로 읽히는지 확인한다(playmaker 테스트에 fixture로 추가).
2. **압축 회귀:** 기존 F-1~F-6 예시 6개로 compact 후 길이 4,000자 이하, P1~P5 통과, `TASK_STATUS_RULE` 통과를 확인한다.
3. **P5 버그:** 약어 치환을 강제로 적용한 본문에서 P5가 통과하는지 확인한다(수정 전 실패, 수정 후 통과).
4. **실전 1회:** 작은 PRD 하나로 새 goaljaby를 돌려 `/goal`을 실행한다. 에이전트가 `[>]`, `[x]`, `[!]`를 실제로 꾸준히 바꾸는지, playmaker 보드에서 카드가 옮겨지는지 본다. 갱신이 끊기면 `/goal` 문장 위치와 표현을 조정한다.
5. **gptaku doctor:** 배포 후 `python3 tools/gptaku_doctor.py goaljaby --all`.

## 구현 현황 (2026-10-13)

- 서브모듈 브랜치 `feat/task-checklist` 커밋 `b19c613` (로컬, push·릴리스 안 함). 변경: templates.md, compact-strategy.md, SKILL.md, plugin.json 0.7.0, CHANGELOG, `tests/verify_v070.py`, fixture `expected-outputs/PLAN.md`·`goal-command.md`.
- 5절 1~3 검증 완료: `verify_v070.py` 9/9 통과(P1~P5, TASK_STATUS_RULE, 4,000자, 작업 행·ID, P5 약어 충돌 재현, 기존 PLAN 면제, 마커 누락 감지). playmaker 파서가 새 PLAN의 마커 4종을 그대로 읽음. `claude plugin validate` 통과.
- P5 약어 충돌은 실제로 발생한 버그다: tesladesk sales-prep, handsup, bluemedison의 goal-command.md가 `PR.md를 업데이트`로 저장돼 있다.
- 남은 것: 5절 4(실전 1회), 배포.

## 6. 순서

1. playmaker v0.1.0 시험판을 완성한다(새 형식과 기존 형식을 모두 읽음). ← 지금 하는 일
2. 이 계획대로 goaljaby를 브랜치에서 수정하고 5절 1~3을 검증한다.
3. 5절 4(실전 1회)를 통과한다.
4. 오너 확인 후 goaljaby 0.7.0과 playmaker 0.1.0을 함께 릴리스한다(CLAUDE.md 배포 8단계).

## 7. 열린 문제

- 에이전트가 장시간 골에서 마커를 꾸준히 갱신할지는 실전에서만 확인할 수 있다. 갱신이 자주 빠지면 Stop 훅으로 "PLAN 마커 갱신 누락" 경고를 띄우는 방안을 검토한다. 이번 범위는 아니다.
- 마일스톤당 작업 수가 많으면 PLAN이 길어진다. 6개 상한으로 시작하고 실전 결과를 보고 조정한다.
