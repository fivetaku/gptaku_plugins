#!/bin/bash
# 플러그인 하나를 격리 Codex에서 한 번 실행하고 판정 행(row.json)을 남긴다. run.sh·core_ab.sh가 부른다.
# 사용: one.sh <run_dir> <plugin> <asks 0|1> <expect|-> <prompt> [같이 설치할 플러그인...]
#   <run_dir>/mkt 에 로컬 마켓(.agents/plugins/marketplace.json, 이름 gptaku-plugins)이 미리 있어야 한다.
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
  "env HOME='$F' CODEX_HOME='$H' codex -s workspace-write -c sandbox_workspace_write.network_access=true --dangerously-bypass-hook-trust; sleep 600"
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
tmux capture-pane -t "$S" -p -S -300 > "$D/screen.txt"
tmux kill-session -t "$S" 2>/dev/null
R=$(find "$H/sessions" -name '*.jsonl' 2>/dev/null | head -1)
python3 "$HERE/scan.py" "$P" "$ASKS" "$EXPECT" "$R" "$D/screen.txt" "$F" "$D/seed.sha" > "$D/row.json"
echo "$P $(python3 -c "import json;r=json.load(open('$D/row.json'));print('PASS' if r['pass'] else 'FAIL '+'; '.join(r['reasons']))")"
