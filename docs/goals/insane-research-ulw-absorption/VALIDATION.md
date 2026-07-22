# VALIDATION — insane-research v2.7 ULW 흡수 개선

## 필수 검증

골 완료로 마크하기 전 다음 명령을 반드시 실행한다. (실행 위치: `/Users/chulrolee/gptaku_plugins`)

```bash
# 1) 게이트 단위 테스트 (M3 신규 — 기존 회귀 포함)
cd plugins/insane-research && python3 -m pytest tests/ -q; cd ../..

# 2) SKILL 계약 CI (M4 신규 — 불가침 문구 grep-assert)
python3 tools/validate_skill_contracts.py

# 3) 죽은 접근 경로 0건
! grep -rn "webcache\.googleusercontent" plugins/insane-research/skills/
! grep -rnE "reddit.*\.json.*(모바일|Mobile) UA" plugins/insane-research/skills/insane-research-main/references/tool_strategy.md

# 4) 신규 계약 존재 확인
grep -q "## EXPAND" plugins/insane-research/skills/insane-research-main/SKILL.md
grep -qE "insane-search (위임|delegation)" plugins/insane-research/skills/insane-research-main/SKILL.md
grep -q "execution_proof" plugins/insane-research/skills/insane-research-main/scripts/validate_ledger.py

# 5) 기존 강점 무손상 (Rate-Limit Guard·게이트 문구 잔존)
grep -q "Rate-Limit & Reliability Guard" plugins/insane-research/skills/insane-research-main/SKILL.md
grep -q "validate_ledger.py" plugins/insane-research/skills/insane-research-main/SKILL.md
```

## 마일스톤별 검증

각 마일스톤 종료 시 실행한다.

```bash
# M1 — 접근 레이어 위임
grep -qE "3단 에스컬레이션|에스컬레이션" plugins/insane-research/skills/insane-research-main/SKILL.md
grep -q "python3 -m engine" plugins/insane-research/skills/insane-research-main/references/tool_strategy.md
grep -q "to_untrusted_text" plugins/insane-research/skills/insane-research-main/references/tool_strategy.md
grep -q '"access"' plugins/insane-research/skills/insane-research-main/SKILL.md
! grep -rn "webcache\.googleusercontent" plugins/insane-research/skills/

# M2 — EXPAND + 시간 유효성
grep -q "## EXPAND" plugins/insane-research/skills/insane-research-main/SKILL.md
grep -qE "수렴|convergence" plugins/insane-research/skills/insane-research-main/SKILL.md
grep -q "observed_at" plugins/insane-research/skills/insane-research-main/SKILL.md
grep -q "Rate-Limit & Reliability Guard" plugins/insane-research/skills/insane-research-main/SKILL.md

# M3 — executable 실행 검증
cd plugins/insane-research && python3 -m pytest tests/test_validate_ledger.py -q; cd ../..

# M4 — 스폰 계약 + 크래프트 + 계약 CI
grep -qE "예산 해제|budget" plugins/insane-research/skills/insane-research-main/references/agent_prompts.md
grep -q "filetype:" plugins/insane-research/skills/insane-research-main/references/tool_strategy.md
python3 tools/validate_skill_contracts.py

# M5 — 시각화 + bump
grep -qi "mermaid" plugins/insane-research/skills/insane-research-main/assets/templates/website_template.html
grep -q '"version": "2.7.0"' plugins/insane-research/.claude-plugin/plugin.json
cd plugins/insane-research && git log --oneline -1 | grep -qE "2\.7\.0|v2\.7" && cd ../..
```

## 수동 확인 절차

1. M1 후: 새 Claude Code 세션에서 SKILL.md를 읽혔을 때 3단 에스컬레이션 지시가 모순 없이 읽히는지 검토 (insane-search 설치 경로와 미설치 폴백 경로 각각 시나리오 리딩).
2. M3 후: 픽스처 ledger에 executable 주장을 넣고 validate_ledger.py를 직접 실행해 exit 1(증적 없음)→exit 0(증적 추가) 전이를 눈으로 확인.
3. M4 후: SKILL.md에서 불가침 문구 하나를 임시로 지워 계약 CI가 실패하는지 확인 후 원복 (네거티브 테스트).
4. M5 후: 갱신된 website_template.html을 브라우저로 열어 차트/Mermaid 블록이 렌더되는지 확인.

## 완료 기준 매핑

| PRD 완료 기준 (개선 백로그) | 검증 방식 | 상태 |
| --- | --- | --- |
| P1-0 W1: SKILL.md 3단 에스컬레이션 | M1 grep (에스컬레이션) | ☐ |
| P1-0 W2: 엔진 탐지 계약 + CLI 해석 규칙 | M1 grep (python3 -m engine, to_untrusted_text) | ☐ |
| P1-0 W3: tool_strategy 다이어트 + 죽은 경로 정정 | 필수 3) 죽은 경로 0건 | ☐ |
| P1-0 W4: 에이전트 위임+R8 지시 | M1 후 agent_prompts.md 리뷰 + 필수 4) | ☐ |
| P1-0 W5: sources.jsonl access 메타 | M1 grep ("access") | ☐ |
| P1-1: EXPAND 계약 + 수렴 규칙 (Guard 내 배치) | M2 grep (EXPAND, 수렴, Guard 잔존) | ☐ |
| P1-2: executable + execution_proof 게이트 | M3 pytest | ☐ |
| P1-3: 스폰 메시지 3요소 표준 | M4 grep (예산 해제) | ☐ |
| P1-4: 검색 크래프트 섹션 | M4 grep (filetype:) | ☐ |
| P2: observed_at/valid_at 시간 유효성 | M2 grep (observed_at) + 기존 픽스처 exit 0 | ☐ |
| P2: SKILL 계약 CI (tools/) | M4 계약 CI 통과 + 네거티브 확인 | ☐ |
| P2: 리포트 차트/Mermaid 기본화 | M5 grep (mermaid) + 수동 4 | ☐ |
| v2.7.0 bump 커밋 (push 없음) | M5 plugin.json + git log | ☐ |

## 완료로 보지 않는 조건

- 필수 검증 중 하나라도 실패
- PLAN.md 밖의 scope로 변경됨 (다른 서브모듈·릴리즈/배포 파이프라인 착수 포함)
- Rate-Limit Guard·validate_ledger 게이트·Abstention 등 기존 불가침 계약 문구가 삭제·약화됨
- 검증을 통과시키기 위해 테스트가 삭제·skip됨
- 진단 없이 에러가 침묵 처리됨
- 산출물이 생성됐지만 검토되지 않음
- 커밋 메시지·문서에 금지 단어("star" 계열)가 포함됨
