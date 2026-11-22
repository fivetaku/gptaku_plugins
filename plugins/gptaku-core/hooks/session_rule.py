#!/usr/bin/env python3
"""SessionStart — 켜진 gptaku 스킬의 사용 조건을 세션마다(압축 후 포함) 다시 넣는다.

사용자 라우트(~/.claude/gptaku-core/routes.json)는 여기 싣지 않는다 — 요청마다 router.py가
키워드 근거가 있을 때 하나를 지목한다. 강한 지시어(CRITICAL·MUST류)는 과잉 호출을 부르므로
조건문("이럴 때 이 스킬")으로만 쓴다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes import load_routes

if os.environ.get("GPTAKU_ROUTER") == "off":
    sys.exit(0)
routes = load_routes(include_user=False)
if not routes:
    sys.exit(0)
# 명시 호출 전용 라우트(키워드·패턴 없음)는 규칙에 넣지 않는다
lines = "\n".join(f"- {r['when']} → `{r['skill']}`"
                  + (f" 단, {r['skip_when']}" if isinstance(r.get('skip_when'), str) and r['skip_when'].strip() else "") for r in routes
                  if r.get("when") and (r.get("keywords") or r.get("patterns") or r.get("weak") or r.get("weak_patterns")))
if not lines:
    sys.exit(0)
rule = f"""gptaku 스킬 안내: 요청이 아래 상황에 맞으면 그 스킬을 먼저 여세요. 일반 코드 작성·수정, 로컬 파일 작업, 일반 지식 설명은 직접 처리합니다.

{lines}

페이지 읽기(글·댓글·자막·목록)는 `insane-search`, 브라우저 조작(폼·로그인·클릭·다운로드)은 `aside-browser` 같은 브라우저 스킬이 맞습니다."""
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": rule}}, ensure_ascii=False))
