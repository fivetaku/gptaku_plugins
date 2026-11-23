#!/usr/bin/env python3
"""UserPromptSubmit — 요청과 맞는 gptaku 스킬 하나를 단정 문구로 지목한다.

판단을 모델에 넘기는 후보 제시("맞으면 써라")는 2026-10-12 벤치에서 기준선과
같은 결과였으므로, 근거 키워드가 있을 때만 1개를 단정해서 붙인다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes import load_routes, match, codex_install

if os.environ.get("GPTAKU_ROUTER") == "off":
    sys.exit(0)
try:
    prompt = json.load(sys.stdin).get("prompt", "")
except Exception:
    sys.exit(0)
r = match(prompt, load_routes())
if r:
    # Codex에는 Skill 도구가 없다 — 스킬은 SKILL.md를 열어 따른다
    how = ("이 스킬의 SKILL.md를 먼저 열어 그 절차를 따르세요" if codex_install()
           else "Skill 도구로 이 스킬을 먼저 호출하세요")
    msg = (f"[gptaku 라우터] 이 요청은 `{r['skill']}` 스킬 대상입니다. "
           f"직접 처리하거나 다른 도구를 부르기 전에 {how}.")
    if isinstance(r.get("skip_when"), str) and r["skip_when"].strip():
        msg = (f"[gptaku 라우터] 이 요청은 `{r['skill']}` 사용 범위입니다. "
               f"예외를 먼저 확인하세요: {r['skip_when']} "
               f"예외에 해당하지 않으면 다른 도구보다 먼저 {how}.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}, ensure_ascii=False))
