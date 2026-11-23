#!/bin/bash
# Claude Code 대화형 실측(Claude 쪽 패리티). `claude -p`에는 AskUserQuestion 카드가 없어 판정할 수 없으므로
# 숨은 tmux에서 대화형 claude를 띄운다. 작업 사본 플러그인을 --plugin-dir로 싣고 설치본은 끈다.
# 사용: claude_run.sh [--all | <plugin>...] [--workers N]   (요청 문장·asks는 prompts.tsv)
# 결과: <state>/smoke/claude-<시각>/results.json + 표. 하나라도 FAIL이면 종료 코드 1.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
STATE=${CODEX_SMOKE_STATE:-$HOME/gptaku-codex-merge-state/smoke}
MODEL=${CLAUDE_SMOKE_MODEL:-}   # 비우면 claude 기본 모델
WAIT=${CLAUDE_SMOKE_WAIT:-600}
WORKERS=4; NAMES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --all) NAMES=($(grep -v '^#' "$HERE/prompts.tsv" | cut -f1)) ;;
    --workers) WORKERS="$2"; shift ;;
    *) NAMES+=("$1") ;;
  esac
  shift
done
[ ${#NAMES[@]} -gt 0 ] || { echo "usage: claude_run.sh [--all | plugin...] [--workers N]"; exit 2; }
RUN="$STATE/claude-$(date +%Y%m%d-%H%M%S)-$$"; mkdir -p "$RUN"
export RUN HERE ROOT MODEL WAIT

one() {
  p="$1"; line=$(awk -F'\t' -v n="$p" '$1==n' "$HERE/prompts.tsv")
  asks=$(printf '%s' "$line" | cut -f2); prompt=$(printf '%s' "$line" | cut -f4)
  D="$RUN/$p"; WK="$D/work"; mkdir -p "$WK"; SRC="$ROOT/plugins/$p"
  [ -d "$HERE/fixtures/$p" ] && cp -R "$HERE/fixtures/$p/." "$WK/"
  WK=$(cd "$WK" && pwd -P)
  S="cls-$(basename "$RUN")-$p"
  tmux kill-session -t "$S" 2>/dev/null
  tmux new-session -d -s "$S" -x 170 -y 50 -c "$WK" \
    "env -u CLAUDE_CODE_SESSION_ID -u CLAUDECODE claude ${MODEL:+--model '$MODEL'} --plugin-dir '$SRC' --settings '{\"enabledPlugins\":{\"$p@gptaku-plugins\":false}}'; sleep 600"
  for _ in $(seq 1 40); do
    s=$(tmux capture-pane -t "$S" -p)
    # 폴더 신뢰 확인: 기본 선택이 "No, exit"이므로 "Yes" 쪽으로 옮긴 뒤 확정한다
    if echo "$s" | grep -qE "Yes, I trust this folder|Yes, proceed"; then
      tmux send-keys -t "$S" Down; sleep 0.5; tmux send-keys -t "$S" Enter; sleep 3; continue
    fi
    echo "$s" | grep -qE "for shortcuts|^❯ |^│ >|^> " && break
    sleep 2
  done
  tmux send-keys -t "$S" -l "$prompt"; sleep 1; tmux send-keys -t "$S" Enter
  T=""; end=$(( $(date +%s) + WAIT ))
  while [ "$(date +%s)" -lt "$end" ]; do
    sleep 6
    [ -n "$T" ] || T=$(grep -l "\"cwd\":\"$WK\"" $(ls -t "$HOME"/.claude/projects/*/*.jsonl 2>/dev/null | head -60) 2>/dev/null | head -1)
    [ -n "$T" ] && [ "$(python3 -B "$HERE/claude_scan.py" "$p" "$asks" "$SRC" "$T" --wait-check)" = done ] && { sleep 4; break; }
  done
  tmux capture-pane -t "$S" -p -S -300 > "$D/screen.txt"
  tmux kill-session -t "$S" 2>/dev/null
  python3 -B "$HERE/claude_scan.py" "$p" "$asks" "$SRC" "${T:--}" > "$D/row.json"
  echo "$p done"
}
export -f one
printf '%s\n' "${NAMES[@]}" | xargs -P "$WORKERS" -I{} bash -c 'one "$1"' _ {} > "$RUN/progress.log" 2>&1

python3 - "$RUN" "${NAMES[@]}" <<'PY'
import json, os, sys
run, names = sys.argv[1], sys.argv[2:]
rows = {}
for n in names:
    try:
        rows[n] = json.load(open(os.path.join(run, n, "row.json")))
    except Exception:
        rows[n] = {"plugin": n, "pass": False, "reasons": ["row.json 없음"]}
json.dump(rows, open(os.path.join(run, "results.json"), "w"), ensure_ascii=False, indent=2)
print(f"{'plugin':18} {'판정':4} {'스킬':4} {'카드':4}  사유")
for n in names:
    r = rows[n]
    print(f"{n:18} {'PASS' if r['pass'] else 'FAIL':4} {r.get('skill_open', '-')!s:4} {'예' if r.get('card_seen') else '-':4}  "
          f"{'; '.join(r.get('reasons', []))}{' (첫 실행 설정 카드만 뜸)' if r.get('setup_card_only') else ''}")
bad = [n for n in names if not rows[n]["pass"]]
print(f"\nrun: {run}\n결과: PASS {len(names) - len(bad)} / {len(names)}")
sys.exit(1 if bad else 0)
PY
