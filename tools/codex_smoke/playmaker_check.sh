#!/bin/bash
# playmaker Codex 웹 보드 실측 (AC-07.1·07.2). 격리 Codex에서 playmaker 스킬로 데모 골(fixtures/playmaker) 보드를 띄우게 한 뒤
#  1) 응답에 나온 주소의 /api/board에 PLAN.md 작업 ID(M1-T2)가 보이는지
#  2) 페이지 토큰으로 /api/send(카드 행동)를 보내면 그 Codex 스레드 큐에 메시지가 들어가는지(codex queue → queue DB)
# 를 본다. 브라우저 창은 열지 않는다(HTTP로 확인). 둘 다 맞으면 종료 코드 0. 끝나면 보드 서버를 끈다.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
STATE=${CODEX_SMOKE_STATE:-$HOME/gptaku-codex-merge-state/smoke}
RUN="$STATE/playmaker-$(date +%Y%m%d-%H%M%S)-$$"; M="$RUN/mkt"; mkdir -p "$M/plugins" "$M/.agents/plugins"
for p in gptaku-core playmaker; do rsync -a --exclude .git --exclude __pycache__ --exclude node_modules "$ROOT/plugins/$p" "$M/plugins/"; done
cat > "$M/.agents/plugins/marketplace.json" <<'J'
{"name":"gptaku-plugins","plugins":[
 {"name":"gptaku-core","source":{"source":"local","path":"./plugins/gptaku-core"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Development"},
 {"name":"playmaker","source":{"source":"local","path":"./plugins/playmaker"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Development"}]}
J
LINE=$(awk -F'\t' '$1=="playmaker"' "$HERE/prompts.tsv")
# 보드는 Codex 세션 안에서 뜬 프로세스라 세션이 살아 있는 동안만 산다 — 검사 끝까지 세션을 유지한다(CODEX_SMOKE_KEEP)
# 카드 행동은 서버가 `codex queue`를 부르는데 샌드박스 안에서 띄운 서버는 EPERM으로 실패한다(2026-11-23 실측).
# 실제 사용에서는 스킬이 샌드박스 밖 권한을 요청하고 사용자가 승인한다 — 시험에서는 그 승인을 danger-full-access로 대신한다.
CODEX_SMOKE_SANDBOX=danger-full-access CODEX_SMOKE_KEEP=1 bash "$HERE/one.sh" "$RUN" playmaker 0 - "$(printf '%s' "$LINE" | cut -f4)" > /dev/null
D="$RUN/playmaker"; H="$D/home"
URL=$(grep -oE 'http://127\.0\.0\.1:[0-9]+' "$D/screen.txt" | tail -1)
echo "보드 주소: ${URL:-(없음)}"
TID=$(basename "$(python3 -c "import json;print(json.load(open('$D/row.json'))['rollout'])")" .jsonl | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
echo "Codex 스레드: $TID"
ok=1
if [ -z "$URL" ]; then echo "FAIL 응답에 보드 주소 없음"; ok=0
else
  B=$(curl -s --max-time 5 "$URL/api/board")
  if printf '%s' "$B" | grep -q "M1-T2"; then echo "OK   /api/board에 작업 카드(M1-T2) 있음"; else echo "FAIL /api/board에 M1-T2 없음: ${B:0:160}"; ok=0; fi
  TOKEN=$(curl -s --max-time 5 "$URL/" | grep -oE "TOKEN *= *['\"][0-9a-f]{32}['\"]" | grep -oE '[0-9a-f]{32}' | head -1)
  MARK="PMCHECK-$$-$(date +%s)"
  S=$(curl -s --max-time 20 -X POST "$URL/api/send" -H 'content-type: application/json' -H "x-playmaker-token: $TOKEN" -H "Origin: $URL" \
      --data "{\"text\":\"보드 시험 메시지 $MARK\",\"task\":\"M1-T2\",\"label\":\"test\"}")
  echo "/api/send 응답: $S"
  RO=$(python3 -c "import json;print(json.load(open('$D/row.json'))['rollout'])")
  got=""
  for _ in $(seq 1 24); do
    sleep 5
    if grep -q "$MARK" "$RO" 2>/dev/null; then got="rollout"; break; fi
    if grep -aq "$MARK" "$H"/queue_1.sqlite* 2>/dev/null; then got="queue"; fi
  done
  case "$got" in
    rollout) echo "OK   카드 메시지가 그 Codex 스레드에 사용자 메시지로 들어감(rollout)";;
    queue) echo "OK   카드 메시지가 그 Codex 스레드 큐(queue_1.sqlite)에 들어감(아직 처리 전)";;
    *) echo "FAIL 스레드 rollout·큐 어디에서도 카드 메시지를 못 찾음"; ok=0;;
  esac
fi
tmux kill-session -t "$(cat "$D/tmux-session" 2>/dev/null)" 2>/dev/null
# 보드 서버 정리: 이 실행 폴더를 --dir로 띄운 node 프로세스만 끈다
pgrep -f "web/server.mjs --dir $D/work" | xargs -r kill 2>/dev/null; pgrep -f "server.mjs.*$D/work" | xargs -r kill 2>/dev/null
[ $ok -eq 1 ] && echo "PASS 보드 표시 + 카드 행동 전달" && exit 0
exit 1
