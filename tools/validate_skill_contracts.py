#!/usr/bin/env python3
"""validate_skill_contracts.py — 스킬 불가침 계약 회귀 게이트.

플러그인 SKILL/reference 문서에서 실수로 지워지면 안 되는 계약 문구를
grep-assert 한다. 문구가 사라지면 exit 1로 CI를 실패시킨다.

사용: 레포 루트에서 `python3 tools/validate_skill_contracts.py`
(⚠️ 루트 .gitignore가 scripts/ 를 무시하므로 이 파일은 tools/ 에 둔다.)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (파일, [반드시 존재해야 하는 문구]) — 문구는 리터럴 부분 문자열 매칭
REQUIRED = {
    "plugins/insane-research/skills/insane-research-main/SKILL.md": [
        # 7-Phase 파이프라인 골격
        "The 7-Phase Insane Research Process",
        # 결정론 검증 게이트 (코드 강제)
        "validate_ledger.py",
        "verified_claims.json",
        "Abstention 강제 규칙",
        # 동시성 가드 (실측 실패에서 도출 — 약화 금지)
        "Rate-Limit & Reliability Guard",
        # v2.7 ULW 흡수 계약
        "접근 3단 에스컬레이션",
        "insane-search 위임",
        "## EXPAND",
        "수렴 규칙",
        "execution_proof",
        "observed_at",
        # v2.8 Workflow 팬아웃 계약
        "실행 모드 선택",
        "workflow_fanout",
    ],
    "plugins/insane-research/skills/insane-research-main/references/workflow_fanout.md": [
        "AGENT_RETURN_SCHEMA",
        "검색 예산 회계",
        "merge_agent_returns.py",
        "배치 모드로 보충",
    ],
    "plugins/insane-research/skills/insane-research-main/references/tool_strategy.md": [
        "insane-search 엔진 위임",
        "검색 크래프트",
        "to_untrusted_text",
        "세션당 200회 캡",
        "lossy",
        # v2.8.1 비동기 위임
        "비동기 위임",
        "수거 전 반환 금지",
    ],
    "plugins/insane-research/skills/insane-research-main/references/agent_prompts.md": [
        "스폰 메시지 표준 3요소",
        "## EXPAND",
        "R8",
    ],
}

# (파일, [존재하면 안 되는 문구]) — 죽은 경로·폐기된 안내 재유입 차단
FORBIDDEN = {
    "plugins/insane-research/skills/insane-research-main/references/tool_strategy.md": [
        "webcache.googleusercontent",  # Google Cache 2024-07 종료
    ],
}


def main() -> int:
    failures = []
    for rel, phrases in REQUIRED.items():
        path = ROOT / rel
        if not path.exists():
            failures.append(f"[누락 파일] {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                failures.append(f"[계약 문구 소실] {rel}: '{phrase}'")

    for rel, phrases in FORBIDDEN.items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase in text:
                failures.append(f"[금지 문구 재유입] {rel}: '{phrase}'")

    if failures:
        print("validate_skill_contracts: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    total = sum(len(v) for v in REQUIRED.values()) + sum(len(v) for v in FORBIDDEN.values())
    print(f"validate_skill_contracts: OK ({total} assertions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
