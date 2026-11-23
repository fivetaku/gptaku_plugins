#!/bin/bash
# Codex 격리 실측 표 (F-11, AC-11.1). 플러그인마다 새 CODEX_HOME에 작업 사본을 로컬 마켓으로 설치하고
# prompts.tsv의 요청을 숨은 tmux TUI로 1회 보낸 뒤 rollout을 scan.py로 판정한다.
# 사용: run.sh [--all | <plugin>...] [--workers N] [--src <plugins 폴더>]
#   --src 기본값은 이 레포의 plugins/ (작업 사본). 결과: <state>/smoke/run-<시각>/results.json, 표는 표준 출력.
#   하나라도 FAIL이면 종료 코드 1.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
STATE=${CODEX_SMOKE_STATE:-$HOME/gptaku-codex-merge-state/smoke}
SRC="$ROOT/plugins"; WORKERS=8; NAMES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --all) NAMES=($(grep -v '^#' "$HERE/prompts.tsv" | cut -f1)) ;;
    --workers) WORKERS="$2"; shift ;;
    --src) SRC="$2"; shift ;;
    *) NAMES+=("$1") ;;
  esac
  shift
done
[ ${#NAMES[@]} -gt 0 ] || { echo "usage: run.sh [--all | plugin...] [--workers N] [--src dir]"; exit 2; }
RUN="$STATE/run-$(date +%Y%m%d-%H%M%S)-$$"; mkdir -p "$RUN/mkt/plugins" "$RUN/mkt/.agents/plugins"

# 로컬 마켓: 설치할 플러그인 전부(대상 + gptaku-core + 동반 설치)를 .git 없이 복사
NEED=$(printf '%s\n' gptaku-core insane-search "${NAMES[@]}" | sort -u)
python3 - "$RUN/mkt" "$SRC" $NEED <<'PY'
import json, os, shutil, sys
mkt, src, names = sys.argv[1], sys.argv[2], sys.argv[3:]
entries = []
for n in names:
    shutil.copytree(os.path.join(src, n), os.path.join(mkt, "plugins", n),
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
    entries.append({"name": n, "source": {"source": "local", "path": f"./plugins/{n}"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": "Development"})
json.dump({"name": "gptaku-plugins", "interface": {"displayName": "GPTaku smoke"}, "plugins": entries},
          open(os.path.join(mkt, ".agents", "plugins", "marketplace.json"), "w"), ensure_ascii=False, indent=2)
PY

: > "$RUN/jobs.tsv"
for n in "${NAMES[@]}"; do
  line=$(awk -F'\t' -v n="$n" '$1==n' "$HERE/prompts.tsv")
  [ -n "$line" ] || { echo "prompts.tsv에 없음: $n"; exit 2; }
  echo "$line" >> "$RUN/jobs.tsv"
done
export RUN HERE
tr '\n' '\0' < "$RUN/jobs.tsv" | xargs -0 -P "$WORKERS" -I{} bash -c '
  IFS=$(printf "\t") read -r p asks expect prompt <<< "$1"
  extra=""; [ "$p" = gptaku-core ] && extra="insane-search"
  bash "$HERE/one.sh" "$RUN" "$p" "$asks" "$expect" "$prompt" $extra' _ {} > "$RUN/progress.log" 2>&1

python3 - "$RUN" "${NAMES[@]}" <<'PY'
import json, os, sys
run, names = sys.argv[1], sys.argv[2:]
rows = {}
for n in names:
    f = os.path.join(run, n, "row.json")
    try:
        rows[n] = json.load(open(f))
    except Exception:
        rows[n] = {"plugin": n, "pass": False, "reasons": ["row.json 없음"]}
json.dump(rows, open(os.path.join(run, "results.json"), "w"), ensure_ascii=False, indent=2)
print(f"{'plugin':18} {'판정':4} {'스킬':4} {'질문ok/err':10} {'도구오류':6} {'setup':5} {'HOME':4}  사유")
for n in names:
    r = rows[n]
    print(f"{n:18} {'PASS' if r['pass'] else 'FAIL':4} {r.get('skill_open', '-')!s:4} "
          f"{str(r.get('q_ok', '-')) + '/' + str(r.get('q_err', '-')):10} {r.get('tool_errors', '-')!s:6} "
          f"{r.get('setup_calls', '-')!s:5} {'같음' if r.get('home_unchanged') else '바뀜':4}  {'; '.join(r.get('reasons', []))}")
bad = [n for n in names if not rows[n]["pass"]]
print(f"\nrun: {run}\n결과: PASS {len(names) - len(bad)} / {len(names)}")
sys.exit(1 if bad else 0)
PY
