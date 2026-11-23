#!/usr/bin/env python3
"""Claude Code 대화형 transcript 한 개로 플러그인 실측 한 행을 판정한다(claude_run.sh가 부른다).

사용: claude_scan.py <plugin> <asks 0|1> <plugin_src_dir> <transcript.jsonl|-> [--wait-check]
출력: 한 줄 JSON. --wait-check면 판정 대신 "done"/"running"만 출력(루프 종료 판단용).

판정(PASS = 모두):
- skill_open: 이 플러그인 스킬을 Skill 도구로 불렀거나 플러그인 폴더의 SKILL.md·명령 파일을 읽었다
  (Skill 호출 시 Claude가 넣는 "Base directory for this skill: <플러그인 폴더>" 포함).
- finished: 마지막 assistant 턴이 끝났거나(end_turn) 답을 기다리는 카드가 떠 있다.
- asks=1이면 card_seen: 첫 실행 설정용 카드(GitHub 별·자동 업데이트)가 아닌 AskUserQuestion이
  결과 없이 떠 있다(= 화면에 카드가 표시돼 답을 기다림). 훅이 막아 오류 결과가 붙은 호출은 세지 않는다.
"""
import json, os, re, sys

SETUP_CARD = re.compile(r"GitHub|⭐|star|auto-?update|자동 업데이트|스타", re.I)


def load(path):
    out = []
    if path and path != "-" and os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def main(argv):
    plugin, asks, src, transcript = argv[:4]
    wait_check = "--wait-check" in argv
    recs = load(transcript)
    uses, results, skill_open, last_stop = {}, {}, 0, None
    for o in recs:
        msg = o.get("message") or {}
        content = msg.get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        for c in content or []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use":
                uses[c.get("id")] = c
                inp = c.get("input") if isinstance(c.get("input"), dict) else {}
                if c.get("name") == "Skill" and str(inp.get("skill", "")).split(":")[0] == plugin:
                    skill_open += 1
                if c.get("name") == "Read" and str(inp.get("file_path", "")).startswith(src):
                    skill_open += 1
            elif c.get("type") == "tool_result":
                results[c.get("tool_use_id")] = c
            elif c.get("type") == "text" and f"Base directory for this skill: {src}" in str(c.get("text")):
                skill_open += 1
        if o.get("type") == "assistant":
            last_stop = msg.get("stop_reason")
    asks_calls = [u for u in uses.values() if u.get("name") == "AskUserQuestion"]
    pending = [u for u in asks_calls if u.get("id") not in results]
    target_pending = [u for u in pending if not SETUP_CARD.search(json.dumps(u.get("input"), ensure_ascii=False))]
    finished = bool(pending) or last_stop == "end_turn"
    if wait_check:
        print("done" if finished else "running")
        return 0
    row = {"plugin": plugin, "transcript": transcript, "skill_open": skill_open,
           "ask_calls": len(asks_calls), "card_seen": bool(target_pending), "finished": finished,
           "setup_card_only": bool(pending) and not target_pending, "reasons": []}
    if not finished:
        row["reasons"].append("턴 미종료(시간 초과)")
    if skill_open < 1:
        row["reasons"].append("스킬 열림 없음")
    if asks == "1" and not target_pending:
        row["reasons"].append("AskUserQuestion 카드 미표시")
    row["pass"] = not row["reasons"]
    if target_pending:
        q = target_pending[-1].get("input", {}).get("questions", [])
        row["card"] = [{"header": x.get("header"), "options": len(x.get("options", []))} for x in q]
    print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
