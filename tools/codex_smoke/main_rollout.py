#!/usr/bin/env python3
"""CODEX_HOME/sessions 아래 rollout 중 메인 스레드(서브에이전트가 아닌 것) 경로를 출력한다.
서브에이전트(spawn_agent) rollout은 session_meta에 parent_thread_id가, 포크(thread/fork, 예: gaseo) rollout은
forked_from_id가 있다 — 둘 다 메인이 아니다."""
import glob, json, os, sys

best = ""
for f in sorted(glob.glob(os.path.join(sys.argv[1], "sessions", "**", "*.jsonl"), recursive=True), key=os.path.getmtime):
    try:
        meta = json.loads(open(f, encoding="utf-8").readline()).get("payload") or {}
    except (OSError, ValueError):
        continue
    if not meta.get("parent_thread_id") and not meta.get("forked_from_id"):
        best = best or f  # 가장 먼저 시작한 메인 스레드
print(best)
