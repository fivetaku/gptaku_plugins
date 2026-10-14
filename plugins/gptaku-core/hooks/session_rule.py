#!/usr/bin/env python3
"""SessionStart — 켜진 gptaku 스킬의 사용 규칙을 세션마다(압축 후 포함) 다시 넣는다."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes import load_routes

if os.environ.get("GPTAKU_ROUTER") == "off":
    sys.exit(0)
routes = load_routes()
if not routes:
    sys.exit(0)
# 명시 호출 전용 라우트(키워드·패턴 없음)는 규칙에 넣지 않는다
lines = "\n".join(f"- {r['when']} → `{r['skill']}`" for r in routes
                  if r.get("when") and (r.get("keywords") or r.get("patterns") or r.get("weak") or r.get("weak_patterns")))
if not lines:
    sys.exit(0)
rule = f"""<EXTREMELY_IMPORTANT>
gptaku 스킬 우선 규칙

아래 상황이 오면 직접 처리하거나 WebSearch·WebFetch·Bash 같은 기본 도구를 부르기 전에 해당 스킬을 Skill 도구로 먼저 호출한다. 직접 처리와 기본 도구는 스킬이 실패했을 때의 폴백이다.

{lines}

해당하지 않는 일(일반 코드 작성·수정, 로컬 파일 작업, 일반 지식 설명)에는 쓰지 않는다.

| 이런 생각이 들면 | 실제로는 |
|---|---|
| "이 정도는 내가 바로 하면 돼" | 사용자는 스킬이 주는 품질을 기대하고 설치했다. 스킬을 먼저 연다. |
| "간단한 검색이라 WebSearch면 충분" | 단순 의미·일반 검색은 WebSearch가 맞다. 특정 URL·플랫폼의 내용이나 주제 리서치는 스킬로 연다. |
| "일단 정보부터 조금 보고 나서" | 정보 수집이 바로 스킬이 하는 일이다. |
| "이 스킬은 너무 무거워" | 무게는 스킬 안에서 조절한다. 미리 판단하지 않는다. |
| "curl이나 WebFetch로 바로 열면 되는데" | 처음부터 스킬로 연다. |
</EXTREMELY_IMPORTANT>"""
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": rule}}, ensure_ascii=False))
