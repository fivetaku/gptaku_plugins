#!/bin/sh
# playmaker 웹 보기 켜기: 같은 골 폴더 서버가 살아 있으면 그 주소를, 없으면 새로 띄워 주소를 출력한다.
# 사용: sh start.sh <골 폴더> <플러그인 루트> <키> [Paseo 에이전트 ID] [paseo CLI] [에이전트 cwd] [auto|explicit]
D="$1"; R="$2"; F="${TMPDIR:-/tmp}/playmaker-web-$3.url"
AGENT="$4"; CLI="$5"; PROJ="$6"; MODE="${7:-auto}"
command -v node >/dev/null 2>&1 || { echo "ERR node를 찾지 못했습니다 (Node 22.18 이상 필요)"; exit 1; }
if [ -s "$F" ]; then
  U=$(cat "$F")
  if curl -fsS --max-time 1 "${U}api/health" 2>/dev/null | grep -qF "\"dir\":\"$D\""; then
    # 살아 있는 서버: 이 세션으로 연결을 알린다 (auto면 기존 연결이 살아 있을 때 서버가 무시)
    if [ -n "$AGENT" ] && [ -s "$F.token" ]; then
      curl -fsS --max-time 2 -X POST -H "content-type: application/json" -H "x-playmaker-token: $(cat "$F.token")" \
        -d "{\"agentId\":\"$AGENT\",\"mode\":\"$MODE\"}" "${U}api/link" >/dev/null 2>&1
    fi
    echo "URL $U reused"; exit 0
  fi
fi
: > "$F"
set -- node "$R/web/server.mjs" --dir "$D" --port-file "$F"
[ -n "$CLI" ] && set -- "$@" --paseo "$CLI"
[ -n "$PROJ" ] && set -- "$@" --project "$PROJ"
[ -n "$AGENT" ] && set -- "$@" --agent "$AGENT"
nohup "$@" >"$F.log" 2>&1 </dev/null &
i=0
while [ $i -lt 50 ]; do
  [ -s "$F" ] && { echo "URL $(cat "$F") started"; exit 0; }
  sleep 0.1; i=$((i + 1))
done
echo "ERR 서버가 5초 안에 뜨지 않았습니다"; tail -5 "$F.log"; exit 1
