/goal PLAN.md의 마일스톤 5개가 모두 완료되고 VALIDATION.md의 필수 검증이 전부 통과될 때까지 멈추지 말고 insane-research v2.7 개선(ULW 흡수)을 구현한다.

먼저 docs/goals/insane-research-ulw-absorption/의 PLAN.md, VALIDATION.md, RECOVERY.md를 읽고, 근거 보고서(RESEARCH/lazycodex_ulw_vs_insane_20260722_140015/outputs/ 2편)를 참조한다.
작업 대상은 plugins/insane-research 서브모듈과 루트 tools/뿐이다. insane-search 등 다른 서브모듈은 수정하지 않는다.
마일스톤 순서대로 진행한다 (M1 접근 레이어 위임 → M2 EXPAND+시간 유효성 → M3 executable 실행 검증 → M4 문서 계약+CI → M5 시각화+통합 자검+v2.7.0 bump).
PLAN.md를 벗어나는 scope 확장은 금지한다. Non-goals(대량 동시발사 채용, 게이트 약화, push·릴리즈·배포)는 구현하지 않는다. 기존 불가침 계약(Rate-Limit Guard·validate_ledger 게이트·Abstention)은 삭제·약화하지 않는다.
각 마일스톤이 끝나면 VALIDATION.md의 해당 검증을 실행하고 PROGRESS.md를 업데이트한다.
요구사항이 충돌하거나 같은 검증이 3회(3 attempts) 실패하면 자체 수정을 멈추고 사람의 결정을 기다린다 (Claude Code는 /goal pause를 지원하지 않음).
버전 bump는 서브모듈 로컬 커밋까지만 하고 push·릴리즈·캐시 교체는 하지 않는다. 커밋 메시지에 "star" 계열 단어를 쓰지 않는다.
