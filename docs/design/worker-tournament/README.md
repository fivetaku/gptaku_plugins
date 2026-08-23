# Worker Tournament — 디자인 문서

> Show Me The PRD로 생성됨 (2026-08-23)
> 대상: `plugins/pumasi`, `plugins/kkirikkiri`

## 무엇인가

외부 코드 에이전트 워커에 **Grok CLI**를 추가하고, 끼리끼리 Workflow 경로에 **토너먼트를 포함한 5종 실행형태**를 도입하는 작업의 설계 문서다.

두 가지 결론이 이 문서의 골격이다:

1. **토너먼트는 품앗이가 아니라 끼리끼리에 넣는다.** 품앗이의 정체성은 "분할"이고 토너먼트는 "중복"이라 문서에 적힌 전제 4개와 충돌한다.
2. **토너먼트가 값을 하는지는 아직 모른다.** A/B 벤치로 판정하고, 우위가 없으면 기본값으로 승격하지 않는다.

---

## 문서

| 문서 | 내용 |
|---|---|
| [01_PRD.md](01_PRD.md) | 문제 정의, 현재 상태 실측, 품앗이 vs 끼리끼리 판단 근거, Grok CLI 실측, 가정 원장 |
| [02_DATA_MODEL.md](02_DATA_MODEL.md) | 실행형태 5종 스키마, Task/Contender/Scorecard/Adoption 계약, 잡 디렉토리 구조 |
| [03_PHASES.md](03_PHASES.md) | Phase 1~5 분리 계획과 의존 관계 |
| [04_PROJECT_SPEC.md](04_PROJECT_SPEC.md) | AI 행동 규칙 — 절대 규칙, 코드 수정 규칙, 판정 규칙 |
| [05_VALIDATION.md](05_VALIDATION.md) | V1~V6 검증 계획, A/B 벤치 사전 등록 기준 |

---

## 빠른 요약

### 현재 상태

| 플러그인 | 프로바이더 | 확장 난이도 |
|---|---|---|
| pumasi | codex / gjc / agy (command 문자열) | **설정 한 줄** |
| kkirikkiri | codex / antigravity / gjc (하드코딩 분기) | 코드 3곳 |
| insane-review | ChatGPT 웹 (CDP) — CLI 아님 | 해당 없음 |

실행형태는 5종 중 **병렬 하나만** 구현돼 있다.

### 할 일

| Phase | 내용 | 산출물 |
|---|---|---|
| 1 | 품앗이 grok 워커 | 설정 + **grok 병렬 실측 데이터** |
| 2 | 끼리끼리 grok 프로바이더 | 코드 3곳 + PATH 폴백 |
| 3 | 실행형태 5종 + 토너먼트 + **A/B 벤치** | 기능 + 판정 리포트 |
| 4 | 병합 채택 *(A/B 우위일 때만)* | 옵트인 경로 |
| 5 | 배포 | 8단계 체크리스트 |

### Grok CLI 실측 (2026-08-23)

```
grok 1.0.4 (d846eb93d94d) [stable]
로그인: grok.com 구독 세션 (XAI_API_KEY 불필요)
모델: grok-4.6 (기본), grok-4.5
grok -p "..." → 비-TTY 파이프에서 정상 출력, exit 0
```

권장 command 문자열:
```
grok --no-auto-update --no-alt-screen --sandbox workspace --always-approve -p
```

주의: 샌드박스가 **기본 off**(codex와 반대), `~/.grok/bin`에 설치돼 비대화형 셸에서 PATH 누락 가능, `--json-schema` 결과는 `.text`에 문자열로 중첩.

---

## 미해결 가정

착수 전에 알고 있어야 할 것들. 전체 목록은 [01_PRD.md §8](01_PRD.md#8-가정-원장).

| # | 가정 | 해소 시점 |
|---|---|---|
| 1 | **토너먼트가 단일 워커보다 낫다** | Phase 3 A/B 벤치 — 반증되면 기능 동결 |
| 4 | grok 구독 세션이 병렬 호출에서 레이트 리밋에 안 걸린다 | Phase 1 실측 |
| 6 | 5종 형태의 키 이름은 자체 정의 | 원본 그림의 스펙 문서를 저장소에서 못 찾음 — 외부 스펙 확인 시 맞춰야 함 |

---

## 다음 단계

Phase 1부터 순서대로 간다. 골 기반 실행이 필요하면 `/goaljaby`로 이 폴더를 넘긴다 — 가정 원장이 골 컨텍스트로 승계된다.
