#!/usr/bin/env python3
"""Codex rollout 한 개를 읽어 플러그인 실측 한 행을 판정한다(run.sh·core_ab.sh가 부른다).

사용: scan.py <plugin> <asks 0|1> <expect|-> <rollout.jsonl> <screen.txt> <fakehome> <seed.sha>
출력: 한 줄 JSON(행 판정). 종료 코드는 항상 0 — 판정은 JSON의 pass 필드다.

판정 기준(PASS = 아래 모두):
- finished: 화면에 'Worked for'가 떠 턴이 끝났다(시간 초과 아님).
- skill_open: 이 플러그인의 Codex 캐시 경로 아래 SKILL.md를 열었거나 스킬 본문이 주입됐다.
  gptaku-core 행은 대신 세션 안내 ≥1, 라우터 안내 ≥1, 라우터가 expect 스킬을 지목.
- 질문 도구: asks=1이면 request_user_input* 호출이 1회 이상 수락됐고(async는 {"accepted":true},
  Plan 도구는 답 반환) 파싱 오류 0. asks=0이어도 질문 도구 오류는 0이어야 한다.
- tool_errors 0: 도구 인자 파싱 실패("failed to parse", "unknown field", "missing field")와 훅 실행 실패.
  셸 명령의 0이 아닌 종료 코드(설치 여부 확인 등)는 스킬 동작이라 도구 오류로 세지 않는다.
- home_unchanged: 가짜 HOME(.claude·.gptaku-setup 포함) 파일 해시가 시작 때와 같다 — setup.sh 등이
  Codex에서 Claude 설정을 건드리지 않았다(AC-02.1의 실행 환경 판정).
"""
import hashlib, json, os, re, sys

PARSE_ERR = re.compile(r"failed to parse|unknown field|missing field|invalid type", re.I)


def home_digest(home):
    lines = []
    for d, _, files in os.walk(home):
        for f in files:
            p = os.path.join(d, f)
            try:
                h = hashlib.sha1(open(p, "rb").read()).hexdigest()
            except OSError:
                h = "unreadable"
            lines.append(f"{os.path.relpath(p, home)} {h}")
    return "\n".join(sorted(lines))


def main(argv):
    plugin, asks, expect, rollout, screen, fakehome, seed = argv[:7]
    asks = asks == "1"
    row = {"plugin": plugin, "rollout": rollout, "screen": screen, "reasons": []}
    screen_txt = open(screen, encoding="utf-8", errors="replace").read() if os.path.exists(screen) else ""
    row["finished"] = "Worked for" in screen_txt
    cache_mark = f"/plugins/cache/gptaku-plugins/{plugin}/"
    skill_open = session_rule = router = 0
    router_msgs, q_calls, q_ok, q_err, tool_err, setup_calls = [], {}, 0, 0, 0, 0
    if rollout and os.path.exists(rollout):
        for line in open(rollout, encoding="utf-8"):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            s = json.dumps(o, ensure_ascii=False)
            p = o.get("payload") if isinstance(o.get("payload"), dict) else {}
            t = p.get("type")
            if t == "message":
                text = json.dumps(p.get("content"), ensure_ascii=False)
                if "gptaku 스킬 안내" in text:
                    session_rule += 1
                if "[gptaku 라우터]" in text:
                    router += 1
                    router_msgs.append(text)
                if cache_mark in text and "SKILL.md" in text and p.get("role") in ("user", "developer"):
                    skill_open += 1  # 스킬 본문 주입
            if t in ("custom_tool_call", "function_call"):
                a = p.get("input") or p.get("arguments") or ""
                if cache_mark in a and "SKILL.md" in a:
                    skill_open += 1
                if "setup/setup.sh" in a:
                    setup_calls += 1
                if (p.get("name") or "").startswith("request_user_input"):
                    q_calls[p.get("call_id")] = p.get("name")
            if t in ("function_call_output", "custom_tool_call_output"):
                out = str(p.get("output"))
                if p.get("call_id") in q_calls:
                    if PARSE_ERR.search(out) or ("error" in out.lower() and "accepted" not in out):
                        q_err += 1
                    elif "accepted" in out or q_calls[p["call_id"]] == "request_user_input":
                        q_ok += 1
                    else:
                        q_err += 1
                elif PARSE_ERR.search(out) and "argument" in out.lower():
                    tool_err += 1
    else:
        row["reasons"].append("rollout 없음")
    # 훅 실패는 rollout에 따로 남지 않고 TUI 화면에만 뜬다
    tool_err += len(re.findall(r"(?i)hook[^\n]{0,80}(?:failed|error)", screen_txt))
    row.update(skill_open=skill_open, session_rule=session_rule, router=router, q_ok=q_ok, q_err=q_err,
               tool_errors=tool_err, setup_calls=setup_calls)
    row["home_unchanged"] = home_digest(fakehome) == open(seed, encoding="utf-8").read()

    if not row["finished"]:
        row["reasons"].append("턴 미종료(시간 초과)")
    if plugin == "gptaku-core":
        if session_rule < 1:
            row["reasons"].append("세션 안내 없음")
        if router < 1:
            row["reasons"].append("라우터 안내 없음")
        elif expect != "-" and not any(expect in m for m in router_msgs):
            row["reasons"].append(f"라우터가 {expect}를 지목하지 않음")
    elif skill_open < 1:
        row["reasons"].append("스킬 SKILL.md 열림 없음")
    if asks and q_ok < 1:
        row["reasons"].append("질문 도구 호출 수락 없음")
    if q_err:
        row["reasons"].append(f"질문 도구 오류 {q_err}")
    if tool_err:
        row["reasons"].append(f"도구 오류 {tool_err}")
    if not row["home_unchanged"]:
        row["reasons"].append("가짜 HOME(.claude·.gptaku-setup) 변경됨")
    row["pass"] = not row["reasons"]
    print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
