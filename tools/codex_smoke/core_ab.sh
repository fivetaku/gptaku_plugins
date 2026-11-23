#!/bin/bash
# gptaku-core Codex 분기 A/B (AC-04.1). 같은 요청("레딧 인기글 가져와줘")을 Claude 설정이 없는 격리 Codex에서
#   A = origin/main에 게시된 gptaku-core(분기 전)   B = 이 작업 사본의 gptaku-core
# 로 한 번씩 돌린다. B에서 세션 안내 ≥1, 라우터 안내 ≥1, 라우터가 insane-search를 지목하면 종료 코드 0.
# A는 비교용으로 함께 보인다(분기 전에는 안내가 0이어야 정상).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
STATE=${CODEX_SMOKE_STATE:-$HOME/gptaku-codex-merge-state/smoke}
BASE=${CORE_AB_BASE:-origin/main}
AB="$STATE/core-ab-$(date +%Y%m%d-%H%M%S)-$$"
LINE=$(awk -F'\t' '$1=="gptaku-core"' "$HERE/prompts.tsv"); PROMPT=$(printf '%s' "$LINE" | cut -f4)
for side in A B; do
  M="$AB/$side/mkt"; mkdir -p "$M/plugins" "$M/.agents/plugins"
  if [ "$side" = A ]; then
    git -C "$ROOT" archive "$BASE" plugins/gptaku-core | tar -x -C "$M"
  else
    cp -R "$ROOT/plugins/gptaku-core" "$M/plugins/"
  fi
  rsync -a --exclude .git --exclude __pycache__ "$ROOT/plugins/insane-search" "$M/plugins/"
  cat > "$M/.agents/plugins/marketplace.json" <<'J'
{"name":"gptaku-plugins","plugins":[
 {"name":"gptaku-core","source":{"source":"local","path":"./plugins/gptaku-core"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Development"},
 {"name":"insane-search","source":{"source":"local","path":"./plugins/insane-search"},"policy":{"installation":"AVAILABLE","authentication":"ON_INSTALL"},"category":"Development"}]}
J
  bash "$HERE/one.sh" "$AB/$side" gptaku-core 0 insane-search:insane-search "$PROMPT" insane-search > /dev/null &
done
wait
for side in A B; do
  python3 - "$AB/$side/gptaku-core/row.json" "$side" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print(f"{sys.argv[2]}: 세션 안내 {r['session_rule']}  라우터 안내 {r['router']}  판정 {'PASS' if r['pass'] else 'FAIL'}  {'; '.join(r['reasons'])}")
print(f"   rollout {r['rollout']}")
PY
done
python3 -c "import json,sys;sys.exit(0 if json.load(open('$AB/B/gptaku-core/row.json'))['pass'] else 1)"
