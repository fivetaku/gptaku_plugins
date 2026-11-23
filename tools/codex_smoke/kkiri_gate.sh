#!/bin/bash
# kkirikkiri 게이트 Codex 실측 (AC-06.2). 격리 Codex에 작업 사본 kkirikkiri를 설치하고 "끼리끼리, …"로 시작하는 요청
# (gate-init 훅이 이 세션의 장부를 연다)으로 ① 경계 블록 없는 spawn_agent ② agents/*.md 카드 파일 apply_patch를 시킨다.
# (card-lint는 front matter에 archetype이 있는 kkirikkiri 카드만 검사한다 — 그래서 카드 모양으로 만든다)
# 판정: 가짜 HOME의 ~/.cache/kkirikkiri/hooks.log에 `gate-spawn block`과 `gate-card` 줄이 모두 있으면 종료 코드 0.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
STATE=${CODEX_SMOKE_STATE:-$HOME/gptaku-codex-merge-state/smoke}
RUN="$STATE/kkiri-gate-$(date +%Y%m%d-%H%M%S)-$$"; M="$RUN/mkt"; mkdir -p "$M/plugins" "$M/.agents/plugins"
for p in gptaku-core kkirikkiri; do rsync -a --exclude .git --exclude __pycache__ --exclude node_modules "$ROOT/plugins/$p" "$M/plugins/"; done
cat > "$M/.agents/plugins/marketplace.json" <<'J'
{"name":"gptaku-plugins","plugins":[
 {"name":"gptaku-core","source":{"source":"local","path":"./plugins/gptaku-core"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Development"},
 {"name":"kkirikkiri","source":{"source":"local","path":"./plugins/kkirikkiri"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Development"}]}
J
PROMPT='끼리끼리, 팀 구성 전에 게이트 점검만 해줘. 1) spawn_agent로 서브에이전트 하나를 메시지 "17 곱하기 23을 계산해서 결과만 알려줘" 그대로(다른 문장 추가 없이) 띄워 봐. 막히면 막힌 이유 문장을 그대로 보여줘. 2) 그다음 apply_patch로 ./team/agents/tester.md 팀원 카드 파일을 아래 네 줄 그대로 새로 만들어(다른 내용 추가 없이): "---" / "name: tester" / "archetype: verifier" / "---". 3) 두 결과만 짧게 보고하고 끝내. 다른 작업은 하지 마.'
bash "$HERE/one.sh" "$RUN" kkirikkiri 0 - "$PROMPT" > /dev/null
LOG="$RUN/kkirikkiri/fakehome/.cache/kkirikkiri/hooks.log"
echo "hooks.log: $LOG"
[ -f "$LOG" ] && cat "$LOG" || echo "(hooks.log 없음)"
R=$(python3 -c "import json;print(json.load(open('$RUN/kkirikkiri/row.json'))['rollout'])")
echo "rollout: $R"
grep -o '\[kkirikkiri gate-[a-z]*\][^"\\]\{0,120\}' "$R" 2>/dev/null | sort -u | head -5
ok=1
grep -q "gate-spawn block" "$LOG" 2>/dev/null || { echo "FAIL 경계 없는 spawn_agent 차단 기록 없음"; ok=0; }
grep -q "gate-card" "$LOG" 2>/dev/null || { echo "FAIL apply_patch 카드 수정에 card-lint 실행 기록 없음"; ok=0; }
[ $ok -eq 1 ] && echo "PASS spawn_agent 차단 + apply_patch card-lint 실행" && exit 0
exit 1
