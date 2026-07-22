## 골 검토 요약 (Step 8 자동 생성)

- 목표: insane 강점(코드 게이트·resume·Rate-Limit Guard) 유지 + ulw 메커니즘 흡수(P1+P2) → v2.7.0 로컬 커밋
- 마일스톤: M1 접근레이어 위임 / M2 EXPAND+시간유효성 / M3 executable 검증 / M4 문서계약+CI / M5 시각화+자검+bump
- 필수 검증: pytest tests/ + tools/validate_skill_contracts.py + 죽은경로 0건 grep + 계약 존재 grep + Guard 잔존 grep
- scope 잠금: insane-research·tools/만 수정, 대량 동시발사·게이트 약화·push/릴리즈/배포·타 서브모듈 금지

---

# PROGRESS

## 현재 골

insane-research 강점 유지 + ulw-research 메커니즘 흡수(P1+P2) → v2.7.0 로컬 커밋까지

## 현재 마일스톤

전체 완료 (M1-M5)

## 완료

- M1 접근 레이어 위임 (W1-W5) — 검증 9/9 PASS.
- M2 EXPAND 계약+수렴 규칙+시간 유효성 — grep 4/4 + 신규 필드 픽스처 exit 0
- M3 executable 실행 검증 — validate_ledger.py 확장 + pytest 10/10
- M4 스폰 3요소+검색 크래프트+계약 CI(18 assertions, 네거티브 확인) — validate-commands.yml 연결
- M5 Mermaid 시각화(SRI 핀)+통합 자검 chain PASS+CHANGELOG+v2.7.0 커밋 3df1876 특이사항: tool_strategy.md에 7/20 omo 세션이 남긴 미커밋 SSOT 노트(ultimate-browsing을 SSOT로 선언)가 있었음 — 오늘 승인된 PLAN이 이를 대체(ultimate-browsing은 스테일 vendor로 판명)하므로 insane-search SSOT 선언으로 정정하고 취지(엔진 위임·드리프트 방지)는 계승

## 마지막 검증 결과

```text
필수 검증 전체 PASS (2026-07-22): pytest 10/10 · 계약 CI 18 assertions OK ·
죽은 경로 0건 · 계약 존재 3종 · 강점 무손상 2종 · mermaid 존재 · plugin.json 2.7.0 ·
커밋 3df1876 (로컬, push 안 함) · 통합 자검 chain: validate_ledger exit 0 → eval_report PASS
```

## 실패 시도

| 시도 | 변경 | 결과 | 배운 점 |
| --- | --- | --- | --- |

## 현재 가장 안정적인 상태

골 실행 전 — insane-research v2.6.1 (서브모듈 clean)

## 다음 단계

골 완료. 남은 것은 골 범위 밖: 서브모듈 push → v2.7.0 릴리즈 → 마켓 동기화 → 캐시 교체 → installed_plugins 갱신 (CLAUDE.md Step 2-8, 사용자 지시 대기). 부모 레포의 tools/validate_skill_contracts.py·워크플로우·docs/goals/ 커밋도 사용자 지시 대기.

## 리스크 / 블로커

- 병렬 세션이 insane-search 자체 개선(P0/P1) 작업 중 — 이 골은 insane-search 서브모듈을 건드리지 않으므로 충돌 없음(scope 잠금). 단, W2 엔진 탐지 계약은 insane-search 버전에 독립적으로(캐시 글롭) 작성할 것.
- insane-search 미설치 폴백 경로는 실환경 재현이 어려움 — 문서 계약 수준 검증 + 시나리오 리딩으로 갈음(VALIDATION 수동 1).
- SKILL.md 비대화 위험 — 신규 계약 추가로 로딩 크기 증가. 계약 CI(M4)에 크기 상한 추가 여부는 골 중 판단.

## 인수인계 메모

이 PROGRESS.md는 골잡이가 생성했다. 골 실행 중 매 체크포인트마다 갱신된다. 근거 보고서는 RESEARCH/lazycodex_ulw_vs_insane_20260722_140015/outputs/ 2편.

## 골 시작 기록
- 시작 시각: 2026-07-22T17:07:26+0900
- 사용 CLI: claude_code
- 컴팩트 후 본문 길이: 872자
