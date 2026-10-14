#!/usr/bin/env python3
"""PostToolUse·PostToolUseFailure(WebFetch) — 페이지가 막혀 못 열렸으면 insane-search로 다시 열게 한다.

주소가 없거나(ENOTFOUND) 연결이 거부된 경우는 insane-search로도 못 여니 넘기지 않는다.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes import load_routes

SKILL = "insane-search:insane-search"
BLOCKED = re.compile(r"(unable to fetch|safety check for domain|unable to verify if domain|certificate|"
                     r"\b(403|429|451|503)\b|forbidden|access denied|too many requests|just a moment|"
                     r"enable javascript|captcha|cloudflare|blocked|timed? ?out|timeout)", re.I)
UNREACHABLE = re.compile(r"(enotfound|econnrefused|doesn't want to proceed|rejected)", re.I)

if os.environ.get("GPTAKU_ROUTER") == "off":
    sys.exit(0)
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if data.get("tool_name") != "WebFetch" or not any(r["skill"] == SKILL for r in load_routes()):
    sys.exit(0)

event = data.get("hook_event_name", "PostToolUse")
url = (data.get("tool_input") or {}).get("url", "")
if event == "PostToolUseFailure":
    text = str(data.get("error", ""))
else:
    resp = data.get("tool_response")
    code = resp.get("code") if isinstance(resp, dict) else None
    body = (resp.get("result", "") if isinstance(resp, dict) else str(resp or ""))[:800]
    # 정상 응답 본문에 'blocked' 같은 단어가 섞인 경우를 피하려고, 성공 코드면 차단 페이지 표지만 본다
    if isinstance(code, int) and code >= 400:
        text = f"{code} {body}"
    elif re.search(r"(just a moment|enable javascript|captcha|access denied)", body, re.I):
        text = body
    else:
        sys.exit(0)
if UNREACHABLE.search(text) or not BLOCKED.search(text):
    sys.exit(0)

msg = (f"[gptaku 폴백] WebFetch가 {url or '이 페이지'}를 열지 못했습니다(차단·접근 제한). "
       f"포기하거나 추측하지 말고 Skill 도구로 `{SKILL}`을 호출해 같은 URL을 다시 여세요.")
print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": msg}}, ensure_ascii=False))
