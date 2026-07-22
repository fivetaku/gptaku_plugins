# PLAN — insane-research v2.7 ULW 흡수 개선

## 목표

insane-research의 강점(validate_ledger.py 코드 게이트·eval_report.py 채점기·resume·Rate-Limit Guard)을 그대로 유지한 채, ulw-research에서 검증된 오케스트레이션 메커니즘(P1 5종)과 P2 보강(시간 유효성 필드·SKILL 계약 CI·리포트 시각화)을 흡수해 v2.7.0 커밋까지 완료한다. push·릴리즈·캐시 교체는 하지 않는다.

## 참조 문서

- 근거 보고서 1: RESEARCH/lazycodex_ulw_vs_insane_20260722_140015/outputs/00_comparison_report.md (§4 개선 로드맵)
- 근거 보고서 2: RESEARCH/lazycodex_ulw_vs_insane_20260722_140015/outputs/01_insane_research_vs_insane_search_integration.md (W1-W5 배선 설계)
- 근거 초안: RESEARCH/lazycodex_ulw_vs_insane_20260722_140015/artifacts/improvement_draft.md
- VALIDATION.md
- RECOVERY.md

작업 대상: `plugins/insane-research` 서브모듈(skills/insane-research-main/의 SKILL.md·references/·scripts/) + 루트 `tools/`(계약 CI). 그 외 서브모듈은 수정 금지.

## 마일스톤 1: P1-0 접근 레이어 위임 (W1-W5)

- 범위(Scope): SKILL.md Phase 3 접근 규칙을 3단 에스컬레이션(WebFetch 1회 → insane-search 위임 → 미설치 폴백)으로 교체(W1). tool_strategy.md에 엔진 탐지 계약 섹션 추가(W2: 캐시 글롭 → `python3 -m engine "<URL>" --json --trace`, exit code·⛔ NOT EXHAUSTED·untried_routes 해석, to_untrusted_text 사용 규칙), 플랫폼 스니펫 다이어트 + 죽은 경로 정정(W3: Reddit `.json`→`.rss`, Google Cache 제거). agent_prompts.md에 위임+R8(untrusted 데이터 취급) 지시 추가(W4). SKILL.md sources.jsonl 스키마에 `access` 메타(layer/verdict/profile_used/extraction_source/phase) 추가(W5).
- 완료 조건: 3단 에스컬레이션·엔진 탐지 계약·access 스키마가 문서에 존재하고, 죽은 경로 문자열이 skills/ 아래 0건.
- 검증: VALIDATION.md 마일스톤별 검증 M1 명령 전부 통과.

## 마일스톤 2: P1-1 EXPAND 리드 계약 + 수렴 규칙 + P2 시간 유효성 필드

- 범위(Scope): SKILL.md Phase 3에 EXPAND 계약(모든 리서치 에이전트 응답 꼬리 `## EXPAND` — LEAD/WHY/ANGLE | DEAD END | none)과 수렴 규칙(미확인 리드 0 / 2연속 웨이브 무신규 / depth 한도 도달 시 사용자 질의) 명문화 — 확장 웨이브는 기존 Rate-Limit Guard(2-3 동시 배치) 안에서만. `artifacts/expansion_log.md` 전수 dedup(거부 리드 포함) 규정. sources.jsonl·claim ledger 스키마에 `observed_at`/`valid_at` 필드 추가(문서), validate_ledger.py가 신규 필드를 하드 에러 없이 수용하는지 확인.
- 완료 조건: EXPAND 계약·수렴 규칙·시간 필드가 SKILL.md와 agent_prompts.md에 존재. Rate-Limit Guard 원문 무손상.
- 검증: M2 명령 전부 통과 + 기존 ledger 픽스처가 여전히 exit 0.

## 마일스톤 3: P1-2 executable 주장 실행 검증

- 범위(Scope): claim ledger 스키마에 `claim_type: "executable"` + `execution_proof`(스크립트·출력 요약·판정) 추가. validate_ledger.py 확장 — executable 주장에 execution_proof 부재 시 exit 1(프로세스 위반), 존재 시 검증 통과 로직. `plugins/insane-research/tests/test_validate_ledger.py` 신규 — 픽스처 세션으로 exit 0/1/2 시나리오(기존 동작 회귀 포함) 커버.
- 완료 조건: 확장된 게이트가 기존 시나리오를 깨지 않고(회귀 0) executable 시나리오를 강제한다.
- 검증: pytest 통과 (M3 명령).

## 마일스톤 4: P1-3 스폰 계약 + P1-4 검색 크래프트 + P2 SKILL 계약 CI

- 범위(Scope): agent_prompts.md에 스폰 메시지 3요소(예산 해제문·완료 정의·EXPAND 꼬리) 표준 템플릿화. tool_strategy.md에 검색 크래프트 섹션(연산자 변주 표 site:/filetype:/intitle:/inurl:/"exact"/-term/OR/before:/after:, 에이전트당 최소 8-10 상이 쿼리, 언어 정책 — 한국어 주제 Korean-first + English 2차, sitemap 발견 경로). 루트 `tools/validate_skill_contracts.py` 신규 — insane-research SKILL.md 불가침 문구(7-Phase·validate_ledger 게이트·Abstention·Rate-Limit Guard·EXPAND 계약) grep-assert, `.github/workflows/`에 연결. ⚠️ 루트 .gitignore가 `scripts/`를 막으므로 반드시 `tools/`에 둔다.
- 완료 조건: 3요소 템플릿·크래프트 섹션 존재, 계약 CI 스크립트가 로컬에서 통과하고 문구 삭제 시 실패한다(네거티브 확인 1회).
- 검증: M4 명령 전부 통과.

## 마일스톤 5: P2 리포트 시각화 + 통합 자가검증 + v2.7.0 bump

- 범위(Scope): 보고서 템플릿(assets/templates/)에 차트(정량 발견)·Mermaid(구조/인과) 기본 블록 추가, website_template.html 갱신. 통합 자검 — 픽스처 세션으로 validate_ledger→eval_report 체인 실행, 문서 버전 표기 일관성(README·CHANGELOG) 점검. plugin.json 2.6.1→2.7.0, CHANGELOG 갱신, 서브모듈 커밋(메시지에 "star" 계열 단어 금지). push·릴리즈·캐시 교체·installed_plugins 갱신은 하지 않는다.
- 완료 조건: 필수 검증 전부 통과 + 버전 bump 커밋 존재(로컬).
- 검증: VALIDATION.md 필수 검증 전체 + M5 명령.

## 최종 완료 기준

- [ ] 마일스톤 1~5 완료
- [ ] VALIDATION.md의 필수 검증 전부 통과
- [ ] scope 위반 없음 (RECOVERY.md scope 잠금 준수)
- [ ] PROGRESS.md 최신화
