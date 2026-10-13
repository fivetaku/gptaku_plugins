#!/usr/bin/env python3
"""UserPromptSubmit — 요청과 맞는 gptaku 스킬 하나를 단정 문구로 지목한다.

판단을 모델에 넘기는 후보 제시("맞으면 써라")는 2026-10-12 벤치에서 기준선과
같은 결과였으므로, 근거 키워드가 있을 때만 1개를 단정해서 붙인다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes import load_routes, match

if os.environ.get("GPTAKU_ROUTER") == "off":
    sys.exit(0)
try:
    prompt = json.load(sys.stdin).get("prompt", "")
except Exception:
    sys.exit(0)
r = match(prompt, load_routes())
if r:
    msg = (f"[gptaku 라우터] 이 요청은 `{r['skill']}` 스킬 대상입니다. "
           "직접 처리하거나 다른 도구를 부르기 전에 Skill 도구로 이 스킬을 먼저 호출하세요.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}, ensure_ascii=False))
