#!/bin/bash
# 플러그인 하나를 격리 Codex에서 한 번 실행하고 판정 행(row.json)을 남긴다. run.sh·core_ab.sh가 부른다.
# 사용: one.sh <run_dir> <plugin> <asks 0|1> <expect|-> <prompt> [같이 설치할 플러그인...]
#   <run_dir>/mkt 에 로컬 마켓(.agents/plugins/marketplace.json, 이름 gptaku-plugins)이 미리 있어야 한다.
# 선택 환경변수: CODEX_SMOKE_SANDBOX(기본 workspace-write), CODEX_SMOKE_KEEP(1=세션 유지), CODEX_SMOKE_EXTRA_ENV("K=V ...", Codex 프로세스에 추가), CODEX_SMOKE_CODEX_ARGS(codex 추가 인자), CODEX_SMOKE_FOLLOWUP(둘째 메시지)
# 격리: CODEX_HOME=<run_dir>/<plugin>/home (설정 템플릿 복사, 로그인 파일 없음 — 모델은 로컬 프록시 경유),
#       HOME=<run_dir>/<plugin>/fakehome (가짜 .claude·.gptaku-setup). 오너 ~/.codex·~/.claude는 쓰지 않는다.
set -u
RUN="$1"; P="$2"; ASKS="$3"; EXPECT="$4"; PROMPT="$5"; shift 5
HERE=$(cd "$(dirname "$0")" && pwd)
TMPL=${CODEX_SMOKE_TMPL:-$HOME/gptaku-codex-merge-state/smoke-tmpl}
WAIT=${CODEX_SMOKE_WAIT:-600}
D="$RUN/$P"; H="$D/home"; F="$D/fakehome"; WK="$D/work"
mkdir -p "$H" "$WK" "$F/.claude/plugins" "$F/.gptaku-setup"
cp "$TMPL/config.toml" "$H/config.toml"
echo '{}' > "$F/.claude/settings.json"
echo '{"version":2,"plugins":{}}' > "$F/.claude/plugins/installed_plugins.json"
echo '{"gptaku-plugins":{"source":{"source":"github","repo":"fivetaku/gptaku_plugins"},"autoUpdate":false}}' > "$F/.claude/plugins/known_marketplaces.json"
python3 -B -c "import sys;sys.path.insert(0,'$HERE');import scan;open('$D/seed.sha','w').write(scan.home_digest('$F'))"
[ -d "$HERE/fixtures/$P" ] && cp -R "$HERE/fixtures/$P/." "$WK/"

{
  CODEX_HOME="$H" codex plugin marketplace add "$RUN/mkt"
  for x in gptaku-core "$P" "$@"; do CODEX_HOME="$H" codex plugin add "$x@gptaku-plugins"; done
} > "$D/install.log" 2>&1

S="cxs-$(basename "$RUN")-$P"
tmux kill-session -t "$S" 2>/dev/null
tmux new-session -d -s "$S" -x 170 -y 50 -c "$WK" \
  "env -u CLAUDE_CODE_SESSION_ID -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT -u CLAUDE_PLUGIN_ROOT HOME='$F' CODEX_HOME='$H' ${CODEX_SMOKE_EXTRA_ENV:-} codex -s ${CODEX_SMOKE_SANDBOX:-workspace-write} -c sandbox_workspace_write.network_access=true --dangerously-bypass-hook-trust ${CODEX_SMOKE_CODEX_ARGS:-}; sleep 600"
for _ in $(seq 1 45); do
  s=$(tmux capture-pane -t "$S" -p)
  echo "$s" | grep -q "Trust this folder" && tmux send-keys -t "$S" Enter
  echo "$s" | grep -qE "Review hooks|need review" && tmux send-keys -t "$S" Escape
  echo "$s" | grep -q "Ask Codex to do anything" && break
  sleep 2
done
tmux send-keys -t "$S" -l "$PROMPT"; sleep 1; tmux send-keys -t "$S" Enter
end=$(( $(date +%s) + WAIT ))
while [ "$(date +%s)" -lt "$end" ]; do
  sleep 5
  tmux capture-pane -t "$S" -p | grep -q "Worked for" && break
done
# 선택: 첫 턴이 끝나면 후속 메시지 하나를 더 보낸다(예: 승인 답). CODEX_SMOKE_FOLLOWUP 환경변수
if [ -n "${CODEX_SMOKE_FOLLOWUP:-}" ]; then
  tmux capture-pane -t "$S" -p -S -300 > "$D/screen1.txt"
  n1=$(grep -c "Worked for" "$D/screen1.txt")
  tmux send-keys -t "$S" -l "$CODEX_SMOKE_FOLLOWUP"; sleep 1; tmux send-keys -t "$S" Enter
  end=$(( $(date +%s) + WAIT ))
  while [ "$(date +%s)" -lt "$end" ]; do
    sleep 5
    [ "$(tmux capture-pane -t "$S" -p -S -300 | grep -c "Worked for")" -gt "$n1" ] && break
  done
fi
tmux capture-pane -t "$S" -p -S -300 > "$D/screen.txt"
# CODEX_SMOKE_KEEP=1이면 세션을 살려 두고 이름만 남긴다(세션 안에서 띄운 프로세스를 확인하는 검사용 — 호출자가 끈다)
if [ "${CODEX_SMOKE_KEEP:-0}" = 1 ]; then echo "$S" > "$D/tmux-session"; else tmux kill-session -t "$S" 2>/dev/null; fi
R=$(python3 -B "$HERE/main_rollout.py" "$H")
python3 "$HERE/scan.py" "$P" "$ASKS" "$EXPECT" "$R" "$D/screen.txt" "$F" "$D/seed.sha" > "$D/row.json"
echo "$P $(python3 -c "import json;r=json.load(open('$D/row.json'));print('PASS' if r['pass'] else 'FAIL '+'; '.join(r['reasons']))")"
