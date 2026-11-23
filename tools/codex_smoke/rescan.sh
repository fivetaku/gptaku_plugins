#!/bin/bash
# 이미 끝난 실행 폴더(run.sh 결과)를 현재 scan.py·main_rollout.py로 다시 판정한다. 판정기를 고친 뒤
# 같은 rollout을 재실행 없이 재평가할 때 쓴다. 첫 판정은 row.first.json으로 한 번만 보존한다.
# 사용: rescan.sh <run_dir>   결과: <run_dir>/results.json 갱신 + 표 출력. FAIL이 있으면 종료 코드 1.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); RUN="$1"; bad=0
for D in "$RUN"/*/; do
  D=${D%/}; P=$(basename "$D"); [ -f "$D/row.json" ] || continue
  line=$(awk -F'\t' -v n="$P" '$1==n' "$HERE/prompts.tsv"); [ -n "$line" ] || continue
  ASKS=$(printf '%s' "$line" | cut -f2); EXPECT=$(printf '%s' "$line" | cut -f3)
  [ -f "$D/row.first.json" ] || cp "$D/row.json" "$D/row.first.json"
  R=$(python3 -B "$HERE/main_rollout.py" "$D/home")
  python3 "$HERE/scan.py" "$P" "$ASKS" "$EXPECT" "$R" "$D/screen.txt" "$D/fakehome" "$D/seed.sha" > "$D/row.json"
done
python3 - "$RUN" <<'PY'
import json, os, sys
run = sys.argv[1]; rows = {}
for n in sorted(os.listdir(run)):
    f = os.path.join(run, n, "row.json")
    if os.path.isfile(f):
        rows[n] = json.load(open(f))
json.dump(rows, open(os.path.join(run, "results.json"), "w"), ensure_ascii=False, indent=2)
for n, r in rows.items():
    print(f"{n:16} {'PASS' if r['pass'] else 'FAIL'} skill={r.get('skill_open')} q={r.get('q_ok')}/{r.get('q_err')} {'; '.join(r.get('reasons', []))}")
sys.exit(1 if any(not r["pass"] for r in rows.values()) else 0)
PY
