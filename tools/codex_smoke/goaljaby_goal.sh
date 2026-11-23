#!/bin/bash
# goaljaby Codex 분기 실측: 격리 Codex에서 ./PRD 골 셋업 → 승인 답을 보내면 create_goal 도구가 호출되는지 본다.
# 판정: 메인 rollout에 create_goal 호출이 있으면 종료 코드 0.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
STATE=${CODEX_SMOKE_STATE:-$HOME/gptaku-codex-merge-state/smoke}
RUN="$STATE/goaljaby-goal-$(date +%Y%m%d-%H%M%S)-$$"; M="$RUN/mkt"; mkdir -p "$M/plugins" "$M/.agents/plugins"
for p in gptaku-core goaljaby; do rsync -a --exclude .git --exclude __pycache__ --exclude node_modules "$ROOT/plugins/$p" "$M/plugins/"; done
cat > "$M/.agents/plugins/marketplace.json" <<'J'
{"name":"gptaku-plugins","plugins":[
 {"name":"gptaku-core","source":{"source":"local","path":"./plugins/gptaku-core"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Development"},
 {"name":"goaljaby","source":{"source":"local","path":"./plugins/goaljaby"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Development"}]}
J
LINE=$(awk -F'\t' '$1=="goaljaby"' "$HERE/prompts.tsv")
CODEX_SMOKE_FOLLOWUP="승인 — 지금 골 작업 시작 (추천). 다른 질문 없이 바로 시작해줘." \
  bash "$HERE/one.sh" "$RUN" goaljaby "$(printf '%s' "$LINE" | cut -f2)" - "$(printf '%s' "$LINE" | cut -f4)" > /dev/null
R=$(python3 -c "import json;print(json.load(open('$RUN/goaljaby/row.json'))['rollout'])")
echo "rollout: $R"
python3 - "$R" <<'PY'
import json, sys
# Codex 코드 모드에서는 create_goal이 exec 스크립트 안 tools.create_goal(...)로 불린다 — 호출 본문 전체와 결과를 본다
called, created = [], []
for line in open(sys.argv[1], encoding="utf-8"):
    try:
        o = json.loads(line)
    except ValueError:
        continue
    p = o.get("payload") if isinstance(o.get("payload"), dict) else {}
    if p.get("type") in ("function_call", "custom_tool_call"):
        a = p.get("arguments") or p.get("input") or ""
        if p.get("name") == "create_goal" or "create_goal(" in a:
            called.append(p.get("call_id"))
            k = a.find("create_goal")
            print("CALL", p.get("name"), a[max(0, k - 40):k + 60].replace("\n", " "))
    if p.get("type") in ("function_call_output", "custom_tool_call_output") and p.get("call_id") in called:
        out = json.dumps(p.get("output"), ensure_ascii=False)
        if '\\"goal\\":{' in out or '"goal":{' in out or 'goal\\":{\\"threadId' in out:
            created.append(out[:160])
for c in created:
    print("RESULT", c)
ok = bool(called) and bool(created)
print("PASS create_goal 호출·골 생성 확인" if ok else ("FAIL create_goal 호출 없음" if not called else "FAIL create_goal 결과에 goal 없음"))
sys.exit(0 if ok else 1)
PY
