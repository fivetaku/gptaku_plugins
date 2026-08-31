# gptaku 플러그인 스킬 frontmatter 호출제어 정책

> 근거: cursor/plugins 구조 점검(2026-08-31) + Claude Code 공식 문서(code.claude.com/docs/en/skills) 실측.
> CC 2.1.251 바이너리에서 `disable-model-invocation` → `disableModelInvocation` 파싱 경로 확인됨.

---

## 0. 한 줄 원칙

**우리 마켓의 기본은 NL 트리거다** — 스킬 description의 한국어/영어 트리거 문구가 발동 표면이고, 이를 막는 키는 예외적으로만 쓴다.

## 1. 세 가지 상태 (공식 시맨틱)

| frontmatter | 모델 자동 발동 | 사용자 `/` 호출 | 용도 |
|---|---|---|---|
| (기본값) | O | O | NL 트리거 스킬 — **우리 마켓 표준** |
| `disable-model-invocation: true` | **X** | O | 부작용 있는 수동 워크플로우 (deploy/commit/발송류) |
| `user-invocable: false` | O | **X** (메뉴 숨김) | 순수 참고 지식 — 사용자가 칠 이유가 없는 스킬 |

주의사항 (공식 문서 명시):
- `disable-model-invocation: true`는 **서브에이전트 프리로드와 스케줄 태스크 발동까지 차단**한다 (v2.1.196+). 다른 스킬이 "이 스킬을 호출하라"고 지시해도 모델 호출이므로 차단됨 — **조합(서브스킬) 구조에 쓰면 깨진다.**
- description 자체가 컨텍스트에서 빠지므로 NL 트리거가 완전히 사라진다.

## 2. 적용 판정 (2026-08-31 전수 점검 결과)

- 마켓 등재 18종의 스킬 39개 전수 확인: `-knowledge` 계열 포함 전부 NL 트리거가 설계 핵심 → **적용 대상 0건**. 기존 스킬에 소급 적용하지 않는다.
- 프라이빗 insane-video는 이미 `disable-model-invocation: true` 사용 중 (올바른 용례).

## 3. 신규 스킬 작성 시 체크

1. 사용자가 자연어로 부를 스킬인가? → 기본값. description에 트리거 문구를 충실히.
2. 배포·발송·과금 등 **타이밍을 사용자가 통제해야 하는** 스킬인가? → `disable-model-invocation: true`. 단 다른 스킬/서브에이전트/스케줄이 이 스킬을 부르는 구조면 금지.
3. 순수 레퍼런스(사용자 명령으로서 무의미)인가? → `user-invocable: false`. 단 트리거 문구가 description에 있는 스킬은 해당 없음(그건 NL 스킬이다).
4. `allowed-tools`에 `AskUserQuestion` 금지 — 기존 CI 게이트(tools/validate_commands.py) 유지.
