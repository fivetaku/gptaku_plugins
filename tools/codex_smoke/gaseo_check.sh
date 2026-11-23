#!/bin/bash
# gaseo Codex 등록 실측 (AC-08.1). 오너 Paseo 데몬·~/.codex를 건드리지 않도록 격리 Paseo 데몬(자기 home·포트, relay 끔)을
# 시험 Codex 홈(CODEX_HOME)으로 띄우고, 격리 Codex 세션에서 gaseo 스킬로 그 세션을 등록하게 한다.
# 판정: 격리 데몬 에이전트 목록에 provider codex 에이전트가 있고 제목이 "<대상> <한 일>" 꼴(두 단어 이상, main 아님)이면 종료 코드 0.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
STATE=${CODEX_SMOKE_STATE:-$HOME/gptaku-codex-merge-state/smoke}
RUN="$STATE/gaseo-$(date +%Y%m%d-%H%M%S)-$$"; M="$RUN/mkt"; mkdir -p "$M/plugins" "$M/.agents/plugins"
PH="$RUN/paseo-home"; CH="$RUN/gaseo/home"; mkdir -p "$PH" "$CH"
PORT=${GASEO_CHECK_PORT:-6799}
cat > "$PH/config.json" <<J
{"version":1,"daemon":{"listen":"127.0.0.1:$PORT","relay":{"enabled":false},"mcp":{"injectIntoAgents":false}}}
J
for p in gptaku-core gaseo; do rsync -a --exclude .git --exclude __pycache__ --exclude node_modules "$ROOT/plugins/$p" "$M/plugins/"; done
cat > "$M/.agents/plugins/marketplace.json" <<'J'
{"name":"gptaku-plugins","plugins":[
 {"name":"gptaku-core","source":{"source":"local","path":"./plugins/gptaku-core"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Development"},
 {"name":"gaseo","source":{"source":"local","path":"./plugins/gaseo"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Development"}]}
J
cleanup() { env PASEO_HOME="$PH" paseo daemon stop --home "$PH" >/dev/null 2>&1; }
trap cleanup EXIT
env PASEO_HOME="$PH" CODEX_HOME="$CH" paseo daemon start --home "$PH" --timeout 60 > "$RUN/daemon-start.log" 2>&1
env PASEO_HOME="$PH" paseo daemon status --home "$PH" 2>&1 | head -4
PROMPT='gaseo 스킬로 지금 이 세션을 Paseo에 등록해줘. 제목은 스킬의 제목 규칙대로 지어줘. 다른 작업은 하지 마.'
# paseo CLI는 Codex 기본 샌드박스에서 실행되지 않는다(uv_uptime EPERM, 2026-11-23 실측) — 실제 사용에서는 사용자가
# 권한 상승을 승인한다. 시험에서는 그 승인을 샌드박스 해제(danger-full-access)로 대신한다.
CODEX_SMOKE_SANDBOX=danger-full-access CODEX_SMOKE_EXTRA_ENV="PASEO_HOME=$PH" bash "$HERE/one.sh" "$RUN" gaseo 0 - "$PROMPT" > /dev/null
R=$(python3 -c "import json;print(json.load(open('$RUN/gaseo/row.json'))['rollout'])")
TID=$(basename "$R" .jsonl | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
echo "Codex 스레드: $TID"
grep -oE '(DETECTED|FORKED|REGISTERED|ALREADY_REGISTERED|NAMED|TITLED|ERROR)[^"\\]{0,140}' "$R" | sort -u | head -6
env PASEO_HOME="$PH" paseo ls --home "$PH" --json > "$RUN/agents.json" 2>&1
python3 - "$RUN/agents.json" "$TID" <<'PY'
import json, sys
raw = open(sys.argv[1]).read()
try:
    data = json.loads(raw)
except ValueError:
    print("FAIL paseo ls 출력이 JSON이 아님:", raw[:200]); sys.exit(1)
items = data if isinstance(data, list) else data.get("agents") or data.get("items") or []
hit = [a for a in items if "codex" in json.dumps(a).lower()]
for a in items:
    print("AGENT", json.dumps({k: a.get(k) for k in ("id", "provider", "name", "title", "cwd") if k in a}, ensure_ascii=False))
ok = False
for a in hit:
    t = (a.get("title") or a.get("name") or "").strip()
    if t and t != "main" and len(t.split()) >= 2 and sys.argv[2][:8] not in t:
        ok = True
print("PASS Codex 세션이 Paseo 에이전트로 등록됨(제목 규칙 충족)" if ok else "FAIL codex 에이전트 없음 또는 제목 규칙 미충족")
sys.exit(0 if ok else 1)
PY
